"""Benchmark runner: golden set x catalog sizes x routers x repeats."""

from __future__ import annotations

import asyncio
import json
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from tooldiscoverybench.catalog import CatalogSize, load_catalog, sample_catalog
from tooldiscoverybench.core.models import GoldenItem, Tool
from tooldiscoverybench.evaluation.metrics import by_tag, score_row, summarize
from tooldiscoverybench.evaluation.report import write_report
from tooldiscoverybench.golden import load_golden, validate_golden
from tooldiscoverybench.routers import Router, build_router

Logger = Callable[[str], None]


def catalog_paths(cfg: dict[str, Any]) -> list[str]:
    raw = cfg["catalog"]
    return list(raw) if isinstance(raw, list) else [raw]


def _enabled(router_cfg: dict[str, Any]) -> bool:
    value = router_cfg.get("enabled", True)
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
        router = build_router(router_cfg)
        reason = router.unavailable_reason()
        if reason:
            log(f"  skipping {router.name}: {reason}")
            continue
        routers.append((router, router_cfg))
    return routers


class _Run:
    """Holds the state of one benchmark run and streams rows to results.jsonl."""

    def __init__(
        self,
        tools: list[Tool],
        server_desc: dict[str, str],
        seed: int,
        out_dir: Path,
    ) -> None:
        self.tools = tools
        self.server_desc = server_desc
        self.seed = seed
        self.rows: list[dict[str, Any]] = []
        self._file = (out_dir / "results.jsonl").open("w")

    async def one(
        self,
        router: Router,
        item: GoldenItem,
        size: CatalogSize,
        repeat: int,
        sem: asyncio.Semaphore,
    ) -> None:
        catalog = sample_catalog(self.tools, item, size, self.seed)
        async with sem:
            res = await router.route(item.question, catalog, self.server_desc)
        row = {
            "router": router.name,
            "catalog_size": size,
            "n_tools": len(catalog),
            "item": item.id,
            "repeat": repeat,
            "question": item.question,
            "gold": item.gold,
            "tags": item.tags,
            "latency_ms": res.latency_ms,
            "calls": res.calls,
            "calibrated": res.calibrated,
            "input_tokens": res.input_tokens,
            "output_tokens": res.output_tokens,
            "error": res.error,
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
) -> Path:
    tools, server_desc = load_catalog(*catalog_paths(cfg))
    items = load_golden(cfg["golden"])[: limit or None]
    problems = validate_golden(items, tools)
    if problems:
        raise SystemExit(
            "golden set doesn't match catalog (re-pull or fix labels):\n  " + "\n  ".join(problems)
        )

    sizes: list[CatalogSize] = list(cfg.get("catalog_sizes", ["all"]))
    repeats = int(cfg.get("repeats", 1))
    routers = build_routers(cfg, only_routers, log)
    if not routers:
        raise SystemExit("no usable routers (check API keys / credentials)")
    prices = {r.name: float(rc["usd_per_m_input"]) for r, rc in routers if "usd_per_m_input" in rc}

    out = Path(out_dir or f"runs/{time.strftime('%Y%m%d-%H%M%S')}")
    out.mkdir(parents=True, exist_ok=True)
    (out / "config.json").write_text(json.dumps(cfg, indent=2, default=str))
    n_synth = sum(t.synthetic for t in tools)
    log(
        f"{len(items)} questions · {len(tools)} tools ({n_synth} synthetic) · sizes {sizes} · "
        f"routers {[r.name for r, _ in routers]} · repeats {repeats}"
    )

    for router, _ in routers:
        await router.setup(tools, server_desc)

    run = _Run(tools, server_desc, int(cfg.get("seed", 0)), out)
    try:
        for router, router_cfg in routers:
            sem = asyncio.Semaphore(int(router_cfg.get("concurrency", cfg.get("concurrency", 4))))
            if cfg.get("warmup", True) and items:
                # connection / model warm-up is not scored
                warm_catalog = sample_catalog(tools, items[0], sizes[0], run.seed)
                await router.route(items[0].question, warm_catalog, server_desc)
            for size in sizes:
                started = time.perf_counter()
                await asyncio.gather(
                    *[run.one(router, it, size, rep, sem) for it in items for rep in range(repeats)]
                )
                _log_size(log, router.name, size, run.rows, time.perf_counter() - started)
    finally:
        run.close()
        for router, _ in routers:
            await router.aclose()

    summary = summarize(run.rows, prices)
    (out / "summary.json").write_text(
        json.dumps({"summary": summary, "by_tag": by_tag(run.rows)}, indent=2)
    )
    write_report(out)
    return out


def _log_size(
    log: Logger, name: str, size: CatalogSize, rows: list[dict[str, Any]], seconds: float
) -> None:
    mine = [r for r in rows if r["router"] == name and r["catalog_size"] == size]
    errors = [r for r in mine if r["error"]]
    ok = len(mine) - len(errors)
    acc = sum(r["correct@1"] for r in mine if not r["error"]) / max(1, ok)
    log(f"  {name:<24} size={size!s:<4} top1={acc:6.1%}  errors={len(errors)}  ({seconds:.1f}s)")
    if errors:
        log(f"      first error: {str(errors[0]['error'])[:200]}")
