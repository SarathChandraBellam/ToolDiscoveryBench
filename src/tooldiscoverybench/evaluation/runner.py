"""Benchmark runner: suites x catalog sizes x routers x repeats.

A *suite* is one golden file. Questions that carry a fixed ``candidates`` catalog run once
at size ``fixed``; others run at every configured catalog size.
"""

from __future__ import annotations

import asyncio
import json
import time
from collections.abc import Callable
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from tooldiscoverybench.catalog import CatalogSize, load_catalog, sample_catalog
from tooldiscoverybench.catalog.sampling import FIXED
from tooldiscoverybench.core.models import GoldenItem, RouteResult, Tool
from tooldiscoverybench.evaluation.metrics import by_tag, score_row, summarize
from tooldiscoverybench.evaluation.report import write_report
from tooldiscoverybench.golden import load_golden, validate_golden
from tooldiscoverybench.routers import Router, build_router

Logger = Callable[[str], None]


@dataclass
class Suite:
    name: str
    items: list[GoldenItem]
    sizes: list[CatalogSize]


def catalog_paths(cfg: dict[str, Any]) -> list[str]:
    raw = cfg["catalog"]
    return list(raw) if isinstance(raw, list) else [raw]


def suite_specs(cfg: dict[str, Any]) -> list[dict[str, Any]]:
    """``suites: [{name, golden, catalog_sizes?}]``, or a single legacy ``golden:`` path."""
    if cfg.get("suites"):
        return [dict(s) for s in cfg["suites"] if _enabled(s)]
    return [{"name": "default", "golden": cfg["golden"]}]


def load_suites(
    cfg: dict[str, Any], tools: list[Tool], limit: int | None, only: list[str] | None = None
) -> list[Suite]:
    default_sizes = list(cfg.get("catalog_sizes", ["all"]))
    suites = []
    for spec in suite_specs(cfg):
        if only and spec["name"] not in only:
            continue
        items = load_golden(spec["golden"])[: limit or None]
        problems = validate_golden(items, tools)
        if problems:
            raise SystemExit(
                f"suite {spec['name']}: golden set doesn't match catalog:\n  "
                + "\n  ".join(problems[:20])
            )
        fixed = all(it.candidates is not None for it in items)
        sizes = [FIXED] if fixed else list(spec.get("catalog_sizes", default_sizes))
        suites.append(Suite(spec["name"], items, sizes))
    return suites


def _enabled(cfg: dict[str, Any]) -> bool:
    value = cfg.get("enabled", True)
    if isinstance(value, str):
        return value.strip().lower() not in ("", "0", "false", "no", "off")
    return bool(value)


def build_routers(
    cfg: dict[str, Any], only: list[str] | None, log: Logger
) -> list[tuple[Router, dict[str, Any]]]:
    """Instantiate enabled routers, skipping (with a message) any that lack credentials."""
    selected = [r for r in cfg["routers"] if _enabled(r) and (not only or r["name"] in only)]
    routers: list[tuple[Router, dict[str, Any]]] = []
    for router_cfg in selected:
        clean = {k: v for k, v in router_cfg.items() if k not in _RUNNER_KEYS}
        router = build_router(clean)
        reason = router.unavailable_reason()
        if reason:
            log(f"  skipping {router.name}: {reason}")
            continue
        routers.append((router, router_cfg))
    return routers


# router config keys consumed by the runner, not passed to the router
_RUNNER_KEYS = {"concurrency", "usd_per_m_input", "abstain_threshold"}


def apply_threshold(res: RouteResult, threshold: float | None) -> RouteResult:
    """Abstain when the top score is below ``threshold`` (for routers without a NONE option)."""
    if threshold is None or res.abstained or res.error:
        return res
    if not res.ranked or res.ranked[0][1] < threshold:
        return replace(res, abstained=True)
    return res


class _Run:
    """Holds the state of one benchmark run and streams rows to results.jsonl."""

    def __init__(self, tools: list[Tool], server_desc: dict[str, str], seed: int, out: Path):
        self.tools = tools
        self.server_desc = server_desc
        self.seed = seed
        self.rows: list[dict[str, Any]] = []
        self._file = (out / "results.jsonl").open("w")

    async def one(
        self,
        router: Router,
        threshold: float | None,
        suite: str,
        item: GoldenItem,
        size: CatalogSize,
        repeat: int,
        sem: asyncio.Semaphore,
    ) -> None:
        catalog = sample_catalog(self.tools, item, size, self.seed)
        async with sem:
            res = apply_threshold(
                await router.route(item.question, catalog, self.server_desc), threshold
            )
        row = {
            "router": router.name,
            "suite": suite,
            "catalog_size": size,
            "n_tools": len(catalog),
            "item": item.id,
            "repeat": repeat,
            "question": item.question,
            "gold": item.gold,
            "acceptable": item.acceptable,
            "tags": item.tags,
            "generator": item.meta.get("generator"),
            "latency_ms": res.latency_ms,
            "calls": res.calls,
            "calibrated": res.calibrated,
            "input_tokens": res.input_tokens,
            "output_tokens": res.output_tokens,
            "error": res.error,
            "abstained": res.abstained,
            "ranked_top5": res.ranked[:5],
            **score_row(item, res),
        }
        self.rows.append(row)
        self._file.write(json.dumps(row) + "\n")
        self._file.flush()

    def close(self) -> None:
        self._file.close()


async def run_bench(
    cfg: dict[str, Any],
    out_dir: str | Path | None = None,
    log: Logger = print,
    only_routers: list[str] | None = None,
    limit: int | None = None,
    only_suites: list[str] | None = None,
) -> Path:
    tools, server_desc = load_catalog(*catalog_paths(cfg))
    suites = load_suites(cfg, tools, limit, only_suites)
    repeats = int(cfg.get("repeats", 1))
    routers = build_routers(cfg, only_routers, log)
    if not routers:
        raise SystemExit("no usable routers (check API keys / credentials)")
    prices = {r.name: float(rc["usd_per_m_input"]) for r, rc in routers if "usd_per_m_input" in rc}

    out = Path(out_dir or f"runs/{time.strftime('%Y%m%d-%H%M%S')}")
    out.mkdir(parents=True, exist_ok=True)
    (out / "config.json").write_text(json.dumps(cfg, indent=2, default=str))
    log(
        f"{len(tools)} tools · suites "
        + ", ".join(f"{s.name}({len(s.items)}q, sizes {s.sizes})" for s in suites)
        + f" · routers {[r.name for r, _ in routers]} · repeats {repeats}"
    )

    for router, _ in routers:
        await router.setup(tools, server_desc)

    run = _Run(tools, server_desc, int(cfg.get("seed", 0)), out)
    try:
        for router, router_cfg in routers:
            sem = asyncio.Semaphore(int(router_cfg.get("concurrency", cfg.get("concurrency", 4))))
            threshold = router_cfg.get("abstain_threshold")
            threshold = float(threshold) if threshold not in (None, "") else None
            first = suites[0]
            if cfg.get("warmup", True) and first.items:
                # connection / model warm-up is not scored
                warm = sample_catalog(tools, first.items[0], first.sizes[0], run.seed)
                await router.route(first.items[0].question, warm, server_desc)
            for suite in suites:
                for size in suite.sizes:
                    started = time.perf_counter()
                    await asyncio.gather(
                        *[
                            run.one(router, threshold, suite.name, it, size, rep, sem)
                            for it in suite.items
                            for rep in range(repeats)
                        ]
                    )
                    _log_size(
                        log, router.name, suite.name, size, run.rows, time.perf_counter() - started
                    )
    finally:
        run.close()
        for router, _ in routers:
            await router.aclose()

    (out / "summary.json").write_text(
        json.dumps({"summary": summarize(run.rows, prices), "by_tag": by_tag(run.rows)}, indent=2)
    )
    write_report(out)
    return out


def _log_size(
    log: Logger,
    name: str,
    suite: str,
    size: CatalogSize,
    rows: list[dict[str, Any]],
    seconds: float,
) -> None:
    mine = [
        r for r in rows if r["router"] == name and r["suite"] == suite and r["catalog_size"] == size
    ]
    errors = [r for r in mine if r["error"]]
    ok = [r for r in mine if not r["error"]]
    acc = sum(r["correct"] for r in ok) / max(1, len(ok))
    log(
        f"  {name:<22} {suite:<22} size={size!s:<5} acc={acc:6.1%}  "
        f"errors={len(errors)}  ({seconds:.1f}s)"
    )
    if errors:
        log(f"      first error: {str(errors[0]['error'])[:200]}")
