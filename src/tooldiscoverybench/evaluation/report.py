"""Render a run directory into ``report.md`` and ``summary.csv``."""

from __future__ import annotations

import csv
import json
import random
from collections import defaultdict
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any

MAX_MISSES = 200
MAX_ERRORS = 20
BOOTSTRAP_RESAMPLES = 1000

#: Question authors that also judged the labels (gpt-5.6-sol, claude-opus-5-5) or that share a
#: model line with a router under test (gpt-5.6-luna vs openai/gpt-6-luna-decisions). The
#: report shows accuracy with and without their questions; override with
#: ``tdb report --exclude-generators``.
DEFAULT_EXCLUDE_GENERATORS: tuple[str, ...] = ("gpt-5.6-sol", "claude-opus-5-5", "gpt-5.6-luna")


def _fmt(value: Any, kind: str = "") -> str:
    if value is None:
        return "–"
    if kind == "pct":
        return f"{value:.1%}"
    if kind == "int":
        return f"{value:,.0f}"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def _summary_table(summary: list[dict[str, Any]]) -> list[str]:
    lines = [
        "## Accuracy",
        "",
        "| router | suite | tools | n | no-tool | err | **acc** | top-1 | lenient | top-3 "
        "| server@1 | abstain ✓ | false abstain | refused |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for s in summary:
        cells = [
            s["router"],
            s["suite"],
            s["catalog_size"],
            s["n"],
            s["n_no_tool"],
            s["errors"],
            f"**{_fmt(s['accuracy'], 'pct')}**",
            _fmt(s["top1"], "pct"),
            _fmt(s["lenient1"], "pct"),
            _fmt(s["top3"], "pct"),
            _fmt(s["server_top1"], "pct"),
            _fmt(s["abstain_recall"], "pct"),
            _fmt(s["false_abstain"], "pct"),
            _fmt(s.get("refusal_rate"), "pct"),
        ]
        lines.append("| " + " | ".join(str(c) for c in cells) + " |")
    lines += [
        "",
        "*acc: answerable questions need the gold tool first, no-tool questions need an "
        "abstain. top-1 / lenient / top-3 / server@1 are over answerable questions only; "
        "lenient also accepts tools labelled acceptable. abstain ✓: share of no-tool questions "
        "where the router abstained. false abstain: share of answerable ones where it did. "
        "refused: share of questions where the backend refused a per-server sub-question "
        "(scored as P = 0 for that server, which can flatter accuracy).*",
        "",
        "## Speed, cost and calibration",
        "",
        "| router | suite | tools | p50 ms | p95 ms | calls | in-tok | $/1k q | ECE | Brier "
        "| conf ✓ | conf ✗ |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for s in summary:
        cells = [
            s["router"],
            s["suite"],
            s["catalog_size"],
            _fmt(s["lat_p50_ms"], "int"),
            _fmt(s["lat_p95_ms"], "int"),
            _fmt(s["calls_mean"]),
            _fmt(s["in_tokens_mean"], "int"),
            _fmt(s["usd_per_1k_q"]),
            _fmt(s["ece"]),
            _fmt(s["brier"]),
            _fmt(s["conf_right"]),
            _fmt(s["conf_wrong"]),
        ]
        lines.append("| " + " | ".join(str(c) for c in cells) + " |")
    lines += [
        "",
        "*Calibration columns are filled only for calibrated routers (Jev). conf ✓ / ✗ is the "
        "mean top-1 probability when right vs wrong; a big gap lets you set an abstain threshold.*",
        "",
    ]
    return lines


def _tag_table(tags: dict[str, dict[str, float]]) -> list[str]:
    all_tags = sorted({t for per_router in tags.values() for t in per_router})
    if not all_tags:
        return []
    lines = [
        "## Accuracy by question tag (all suites and sizes pooled)",
        "",
        "| router | " + " | ".join(all_tags) + " |",
        "|---|" + "---:|" * len(all_tags),
    ]
    for router, acc in tags.items():
        lines.append(
            f"| {router} | " + " | ".join(_fmt(acc.get(t), "pct") for t in all_tags) + " |"
        )
    lines.append("")
    return lines


def _by_generator(rows: list[dict[str, Any]]) -> list[str]:
    """Accuracy per router split by which model family wrote the question."""
    cells: dict[tuple[str, str], list[bool]] = {}
    for r in rows:
        if r["error"] or not r.get("generator"):
            continue
        fam = str(r["generator"]).split("-", 1)[0]
        cells.setdefault((r["router"], fam), []).append(r["correct"])
    if not cells:
        return []
    fams = sorted({f for _, f in cells})
    routers = sorted({rt for rt, _ in cells})
    lines = [
        "## Accuracy by question author (model family that wrote the question)",
        "",
        "| router | " + " | ".join(fams) + " |",
        "|---|" + "---:|" * len(fams),
    ]
    for rt in routers:
        vals = [cells.get((rt, f)) for f in fams]
        lines.append(
            f"| {rt} | "
            + " | ".join(_fmt(sum(v) / len(v), "pct") if v else "–" for v in vals)
            + " |"
        )
    lines.append("")
    return lines


def bootstrap_ci(
    per_item: Sequence[float], resamples: int = BOOTSTRAP_RESAMPLES, seed: int = 0
) -> tuple[float, float] | None:
    """Percentile 95% CI of the mean, resampling questions with replacement (seeded)."""
    n = len(per_item)
    if n == 0:
        return None
    rng = random.Random(seed)
    means = sorted(sum(rng.choices(per_item, k=n)) / n for _ in range(resamples))
    return means[int(0.025 * (resamples - 1))], means[round(0.975 * (resamples - 1))]


def _per_item_top1(rows: Iterable[dict[str, Any]]) -> list[float]:
    """Top-1 per answerable question, averaged over repeats so the question is the unit."""
    by_item: dict[str, list[bool]] = defaultdict(list)
    for r in rows:
        if not r["error"] and r.get("answerable", True):
            by_item[r["item"]].append(bool(r["correct@1"]))
    return [sum(v) / len(v) for _, v in sorted(by_item.items())]


def _group(rows: list[dict[str, Any]]) -> dict[tuple[str, str, str], list[dict[str, Any]]]:
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        groups[(r["router"], r.get("suite", ""), str(r["catalog_size"]))].append(r)
    return dict(
        sorted(
            groups.items(),
            key=lambda kv: (kv[0][0], kv[0][1], int(kv[0][2]) if kv[0][2].isdigit() else 1 << 30),
        )
    )


def _ci_cells(per_item: list[float]) -> list[str]:
    ci = bootstrap_ci(per_item)
    if ci is None:
        return ["0", "–", "–"]
    mean = sum(per_item) / len(per_item)
    return [str(len(per_item)), _fmt(mean, "pct"), f"{ci[0]:.1%}–{ci[1]:.1%}"]


def _top1_ci(rows: list[dict[str, Any]]) -> list[str]:
    groups = _group(rows)
    if not groups:
        return []
    lines = [
        "## Top-1 with 95% bootstrap confidence intervals",
        "",
        "| router | suite | tools | n | top-1 | 95% CI | test n | test top-1 | test 95% CI |",
        "|---|---|---:|---:|---:|---|---:|---:|---|",
    ]
    for (router, suite, size), rs in groups.items():
        test = [r for r in rs if "split:test" in r.get("tags", [])]
        cells = [router, suite, size, *_ci_cells(_per_item_top1(rs))]
        cells += _ci_cells(_per_item_top1(test))
        lines.append("| " + " | ".join(cells) + " |")
    lines += [
        "",
        f"*Answerable questions only; {BOOTSTRAP_RESAMPLES} seeded resamples over questions "
        "(repeats averaged per question). *test* is the frozen held-out split "
        "(`data/golden/splits/test_qids.txt`); publish numbers from it with repeats ≥ 3.*",
        "",
    ]
    return lines


def _by_generator_model(rows: list[dict[str, Any]]) -> list[str]:
    """Accuracy per router split by the exact model that wrote the question."""
    cells: dict[tuple[str, str], list[bool]] = defaultdict(list)
    for r in rows:
        if not r["error"] and r.get("generator"):
            cells[(r["router"], str(r["generator"]))].append(bool(r["correct"]))
    if not cells:
        return []
    gens = sorted({g for _, g in cells})
    lines = [
        "## Accuracy by question author (exact model)",
        "",
        "| router | " + " | ".join(gens) + " |",
        "|---|" + "---:|" * len(gens),
    ]
    for rt in sorted({rt for rt, _ in cells}):
        vals = [cells.get((rt, g)) for g in gens]
        lines.append(
            f"| {rt} | "
            + " | ".join(_fmt(sum(v) / len(v), "pct") if v else "–" for v in vals)
            + " |"
        )
    lines.append("")
    return lines


def _excluding(rows: list[dict[str, Any]], exclude: Sequence[str]) -> list[str]:
    if not exclude or not any(r.get("generator") in exclude for r in rows):
        return []
    lines = [
        "## Accuracy without possibly contaminated questions",
        "",
        "| router | suite | tools | n | acc | top-1 | n kept | acc kept | top-1 kept |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]

    def stats(rs: list[dict[str, Any]]) -> list[str]:
        ok = [r for r in rs if not r["error"]]
        ans = [r for r in ok if r.get("answerable", True)]
        acc = sum(bool(r["correct"]) for r in ok) / len(ok) if ok else None
        top1 = sum(bool(r["correct@1"]) for r in ans) / len(ans) if ans else None
        return [str(len(rs)), _fmt(acc, "pct"), _fmt(top1, "pct")]

    for (router, suite, size), rs in _group(rows).items():
        kept = [r for r in rs if r.get("generator") not in exclude]
        lines.append("| " + " | ".join([router, suite, size, *stats(rs), *stats(kept)]) + " |")
    lines += [
        "",
        "*kept: questions not written by " + ", ".join(f"`{g}`" for g in exclude) + " (judges "
        "of the labels, or the same model line as a router under test).*",
        "",
    ]
    return lines


def _misses(rows: list[dict[str, Any]]) -> list[str]:
    misses = [r for r in rows if not r["error"] and not r["correct"] and r["repeat"] == 0]
    if not misses:
        return []
    lines = [
        f"## Misses (repeat 0, first {MAX_MISSES})",
        "",
        "| router | suite | tools | item | picked | p | gold |",
        "|---|---|---:|---|---|---:|---|",
    ]
    ordered = sorted(
        misses, key=lambda r: (r["router"], r.get("suite", ""), str(r["catalog_size"]), r["item"])
    )
    for r in ordered[:MAX_MISSES]:
        gold = ", ".join(f"`{g}`" for g in r["gold"]) or "*abstain*"
        picked = "*abstained*" if r.get("abstained") else f"`{r['top1']}`"
        lines.append(
            f"| {r['router']} | {r.get('suite', '')} | {r['catalog_size']} | {r['item']} "
            f"| {picked} | {_fmt(r['p_top1'])} | {gold} |"
        )
    return lines


def _errors(rows: list[dict[str, Any]]) -> list[str]:
    errors = [r for r in rows if r["error"]]
    if not errors:
        return []
    lines = ["", f"## Errors ({len(errors)})", ""]
    lines += [f"- {r['router']} / {r['item']}: {r['error'][:200]}" for r in errors[:MAX_ERRORS]]
    return lines


def write_report(
    run_dir: str | Path, exclude_generators: Sequence[str] = DEFAULT_EXCLUDE_GENERATORS
) -> Path:
    run = Path(run_dir)
    data = json.loads((run / "summary.json").read_text())
    rows = [
        json.loads(line)
        for line in (run / "results.jsonl").read_text().splitlines()
        if line.strip()
    ]
    summary: list[dict[str, Any]] = data["summary"]

    with (run / "summary.csv").open("w", newline="") as fh:
        if summary:
            writer = csv.DictWriter(fh, fieldnames=list(summary[0]))
            writer.writeheader()
            writer.writerows(summary)

    lines = [f"# ToolDiscoveryBench — {run.name}", ""]
    lines += _summary_table(summary)
    lines += _top1_ci(rows)
    lines += _tag_table(data["by_tag"])
    lines += _by_generator(rows)
    lines += _by_generator_model(rows)
    lines += _excluding(rows, list(exclude_generators))
    lines += _misses(rows)
    lines += _errors(rows)

    path = run / "report.md"
    path.write_text("\n".join(lines) + "\n")
    return path
