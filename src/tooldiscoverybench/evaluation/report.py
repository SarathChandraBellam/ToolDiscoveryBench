"""Render a run directory into ``report.md`` and ``summary.csv``."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

MAX_MISSES = 200
MAX_ERRORS = 20


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
        "## Accuracy and latency",
        "",
        "| router | tools | n | err | top-1 | top-3 | MRR | server@1 | p50 ms | p95 ms "
        "| calls | in-tok | $/1k q | ECE | conf ✓ | conf ✗ |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for s in summary:
        cells = [
            s["router"],
            s["catalog_size"],
            s["n"],
            s["errors"],
            _fmt(s["top1"], "pct"),
            _fmt(s["top3"], "pct"),
            _fmt(s["mrr"]),
            _fmt(s["server_top1"], "pct"),
            _fmt(s["lat_p50_ms"], "int"),
            _fmt(s["lat_p95_ms"], "int"),
            _fmt(s["calls_mean"]),
            _fmt(s["in_tokens_mean"], "int"),
            _fmt(s["usd_per_1k_q"]),
            _fmt(s["ece"]),
            _fmt(s["conf_right"]),
            _fmt(s["conf_wrong"]),
        ]
        lines.append("| " + " | ".join(str(c) for c in cells) + " |")
    lines += [
        "",
        "*ECE and conf columns are filled only for calibrated routers (Jev). conf ✓ / ✗ is the "
        "mean top-1 probability when right vs wrong; a big gap lets you set an abstain threshold.*",
        "",
    ]
    return lines


def _tag_table(tags: dict[str, dict[str, float]]) -> list[str]:
    all_tags = sorted({t for per_router in tags.values() for t in per_router})
    if not all_tags:
        return []
    lines = [
        "## Top-1 by question tag (all catalog sizes pooled)",
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


def _misses(rows: list[dict[str, Any]]) -> list[str]:
    misses = [r for r in rows if not r["error"] and not r["correct@1"] and r["repeat"] == 0]
    if not misses:
        return []
    lines = [
        "## Misses (repeat 0)",
        "",
        "| router | tools | item | picked | p | gold |",
        "|---|---:|---|---|---:|---|",
    ]
    ordered = sorted(misses, key=lambda r: (r["router"], str(r["catalog_size"]), r["item"]))
    for r in ordered[:MAX_MISSES]:
        gold = ", ".join(f"`{g}`" for g in r["gold"])
        lines.append(
            f"| {r['router']} | {r['catalog_size']} | {r['item']} | `{r['top1']}` "
            f"| {_fmt(r['p_top1'])} | {gold} |"
        )
    return lines


def _errors(rows: list[dict[str, Any]]) -> list[str]:
    errors = [r for r in rows if r["error"]]
    if not errors:
        return []
    lines = ["", f"## Errors ({len(errors)})", ""]
    lines += [f"- {r['router']} / {r['item']}: {r['error'][:200]}" for r in errors[:MAX_ERRORS]]
    return lines


def write_report(run_dir: str | Path) -> Path:
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
    lines += _tag_table(data["by_tag"])
    lines += _misses(rows)
    lines += _errors(rows)

    path = run / "report.md"
    path.write_text("\n".join(lines) + "\n")
    return path
