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
        "## Accuracy",
        "",
        "| router | suite | tools | n | no-tool | err | **acc** | top-1 | lenient | top-3 "
        "| server@1 | abstain ✓ | false abstain |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
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
        ]
        lines.append("| " + " | ".join(str(c) for c in cells) + " |")
    lines += [
        "",
        "*acc: answerable questions need the gold tool first, no-tool questions need an "
        "abstain. top-1 / lenient / top-3 / server@1 are over answerable questions only; "
        "lenient also accepts tools labelled acceptable. abstain ✓: share of no-tool questions "
        "where the router abstained. false abstain: share of answerable ones where it did.*",
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
    lines += _by_generator(rows)
    lines += _misses(rows)
    lines += _errors(rows)

    path = run / "report.md"
    path.write_text("\n".join(lines) + "\n")
    return path
