"""Summary table (markdown + csv) over COMPLETE (setup, model) cells only."""

from __future__ import annotations

import csv
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

from tooldiscoverybench.harness import SETUPS
from tooldiscoverybench.harness.runner import latest_rows, load_results

COLUMNS = [
    ("setup", "setup"),
    ("model", "model"),
    ("n", "n"),
    ("n_answerable", "answerable"),
    ("n_no_tool", "no-tool"),
    ("errors", "errors"),
    ("top1", "top-1 (all)"),
    ("top1_answerable", "top-1 answerable"),
    ("abstain_no_tool", "abstain on no-tool"),
    ("gold_ever", "gold ever called"),
    ("llm_calls", "LLM calls"),
    ("tool_search", "tool_search calls"),
    ("input_tokens", "input tok"),
    ("output_tokens", "output tok"),
    ("latency_s", "latency s (mean)"),
    ("latency_p50_s", "latency s (p50)"),
    ("fallback_rate", "router fallback"),
    ("router_hit", "router top-3 has gold"),
    ("step_cap", "hit 8-step cap"),
    ("skill_reads", "SKILL.md reads/q"),
]


def _rate(flags: list[bool]) -> str:
    return f"{sum(flags) / len(flags):.2f} ({sum(flags)}/{len(flags)})" if flags else "–"


def _mean(values: list[float], fmt: str = "{:.2f}") -> str:
    return fmt.format(statistics.fmean(values)) if values else "–"


def summarise(rows: list[dict[str, Any]], qids: list[str]) -> tuple[list[dict[str, str]], list[str]]:
    """Summary rows for complete cells, plus a note per incomplete cell."""
    latest = latest_rows(rows)
    cells: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for (setup, model, qid), r in latest.items():
        if qid in qids:
            cells[(setup, model)].append(r)
    order = {s: i for i, s in enumerate(SETUPS)}
    out, partial = [], []
    for (setup, model), rs in sorted(cells.items(), key=lambda kv: (kv[0][1], order.get(kv[0][0], 9))):
        if len(rs) < len(qids):
            partial.append(f"{setup} / {model}: {len(rs)}/{len(qids)} questions (excluded)")
            continue
        ok = [r for r in rs if not r.get("error")]
        ans = [r for r in rs if not r["no_tool"]]
        none = [r for r in rs if r["no_tool"]]
        lat = [r["latency_ms"] / 1000 for r in ok]
        out.append(
            {
                "setup": setup,
                "model": model,
                "n": str(len(rs)),
                "n_answerable": str(len(ans)),
                "n_no_tool": str(len(none)),
                "errors": str(len(rs) - len(ok)),
                "top1": _rate([bool(r["top1_correct"]) for r in rs]),
                "top1_answerable": _rate([bool(r["top1_correct"]) for r in ans]),
                "abstain_no_tool": _rate([bool(r["top1_correct"]) for r in none]),
                "gold_ever": _rate([bool(r["gold_ever_called"]) for r in ans]),
                "llm_calls": _mean([r["llm_calls"] for r in ok]),
                "tool_search": _mean([r["tool_search_calls"] for r in ok]),
                "input_tokens": _mean([r["input_tokens"] for r in ok], "{:,.0f}"),
                "output_tokens": _mean([r["output_tokens"] for r in ok], "{:,.0f}"),
                "latency_s": _mean(lat, "{:.1f}"),
                "latency_p50_s": f"{statistics.median(lat):.1f}" if lat else "–",
                "fallback_rate": _rate([bool(r.get("fallback_used")) for r in ok])
                if setup == "router_first" else "–",
                "router_hit": _rate([bool(r.get("router_hit")) for r in ans])
                if setup == "router_first" else "–",
                "step_cap": _rate([bool(r["hit_step_cap"]) for r in ok]),
                "skill_reads": _mean([len(r.get("skills_read") or []) for r in ok]),
            }
        )
    return out, partial


def write_summary(out_dir: Path, qids: list[str], meta: dict[str, Any]) -> str:
    rows = load_results(out_dir / "results.jsonl")
    table, partial = summarise(rows, qids)
    with (out_dir / "summary.csv").open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=[k for k, _ in COLUMNS])
        writer.writeheader()
        writer.writerows(table)
    lines = [
        "# deepagents harness: all_tools vs bm25_search vs router_first",
        "",
        f"Sample: {len(qids)} dev-split `datasets_v1` questions "
        f"({meta.get('n_answerable', '?')} answerable, {meta.get('n_no_tool', '?')} no-tool), "
        f"catalog of {meta.get('n_tools', '?')} real tools, stub execution, "
        f"max {meta.get('max_model_calls', 8)} agent model calls per run.",
        f"Router for `router_first`: {meta.get('router', '?')}.",
        "",
        "Rates are `mean (count/n)`. Accuracy columns count error rows as wrong; LLM calls, "
        "tokens and latency are means over non-error rows and include the router call for "
        "`router_first`. Only complete cells are shown.",
        "",
        "| " + " | ".join(h for _, h in COLUMNS) + " |",
        "|" + "---|" * len(COLUMNS),
    ]
    lines += ["| " + " | ".join(r[k] for k, _ in COLUMNS) + " |" for r in table]
    if partial:
        lines += ["", "Incomplete cells (not in the table):", *[f"- {p}" for p in partial]]
    text = "\n".join(lines) + "\n"
    (out_dir / "summary.md").write_text(text)
    return text
