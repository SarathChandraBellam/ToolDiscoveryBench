"""Summary tables (markdown + csv) over COMPLETE (setup, model) cells only.

Tables: accuracy (answerable questions), tool-call efficiency (answerable), no-tool
questions (abstention), plus a short generated readout comparing discovery setups with
``all_tools``.
"""

from __future__ import annotations

import csv
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

from tooldiscoverybench.harness import SETUPS
from tooldiscoverybench.harness.runner import latest_rows, load_results

ACCURACY = [
    ("setup", "setup"),
    ("model", "model"),
    ("n", "n"),
    ("errors", "errors"),
    ("top1", "top-1 first real call = gold"),
    ("gold_ever", "gold reached"),
    ("ended_gold", "ended with gold"),
    ("search_found_gold", "a search returned gold"),
    ("router_hit", "router top-3 has gold"),
    ("fallback", "router fallback (searched)"),
    ("step_cap", "hit step cap"),
    ("skill_reads", "SKILL.md reads/task"),
]
EFFICIENCY = [
    ("setup", "setup"),
    ("model", "model"),
    ("n", "n"),
    ("tool_calls", "tool calls/task"),
    ("discovery", "discovery (tool_search)"),
    ("real", "real tool calls"),
    ("wasted", "wasted before gold"),
    ("calls_to_gold", "calls-to-gold (reached)"),
    ("never", "gold never reached"),
    ("llm_calls", "LLM calls (total)"),
    ("router_llm", "of which router"),
    ("in_tok", "input tok (total)"),
    ("router_in_tok", "of which router"),
    ("out_tok", "output tok"),
    ("latency", "latency s mean"),
    ("latency_p50", "p50"),
    ("router_lat", "router s"),
]
NO_TOOL = [
    ("setup", "setup"),
    ("model", "model"),
    ("n", "n"),
    ("errors", "errors"),
    ("abstain", "correct abstention"),
    ("wasted", "wasted real calls/task"),
    ("any_wasted", "tasks with a real call"),
    ("discovery", "tool_search/task"),
    ("llm_calls", "LLM calls"),
    ("in_tok", "input tok"),
    ("latency", "latency s"),
]


def _rate(flags: list[bool]) -> str:
    return f"{sum(flags) / len(flags):.2f} ({sum(flags)}/{len(flags)})" if flags else "–"


def _mean(values: list[float], fmt: str = "{:.2f}") -> str:
    return fmt.format(statistics.fmean(values)) if values else "–"


def complete_cells(
    rows: list[dict[str, Any]], qids: list[str]
) -> tuple[dict[tuple[str, str], list[dict[str, Any]]], list[str]]:
    latest = latest_rows(rows)
    cells: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    wanted = set(qids)
    for (setup, model, qid), r in latest.items():
        if qid in wanted:
            cells[(setup, model)].append(r)
    order = {s: i for i, s in enumerate(SETUPS)}
    full, partial = {}, []
    for key in sorted(cells, key=lambda k: (k[1], order.get(k[0], 9))):
        rs = cells[key]
        if len(rs) < len(qids):
            partial.append(f"{key[0]} / {key[1]}: {len(rs)}/{len(qids)} questions (excluded)")
        else:
            full[key] = rs
    return full, partial


def _accuracy(setup: str, model: str, rs: list[dict[str, Any]]) -> dict[str, str]:
    ans = [r for r in rs if not r["no_tool"]]
    ok = [r for r in ans if not r.get("error")]
    router = setup == "router_first"
    return {
        "setup": setup,
        "model": model,
        "n": str(len(ans)),
        "errors": str(len(ans) - len(ok)),
        "top1": _rate([bool(r["top1_correct"]) for r in ans]),
        "gold_ever": _rate([bool(r["gold_ever_called"]) for r in ans]),
        "ended_gold": _rate([bool(r["ended_with_gold"]) for r in ans]),
        "search_found_gold": _rate(
            [bool(r["search_found_gold"]) for r in ans if r["tool_search_calls"]]
        ),
        "router_hit": _rate([bool(r.get("router_hit")) for r in ans]) if router else "–",
        "fallback": _rate([bool(r.get("fallback_used")) for r in ans]) if router else "–",
        "step_cap": _rate([bool(r["hit_step_cap"]) for r in ans]),
        "skill_reads": _mean([len(r.get("skills_read") or []) for r in ans]),
    }


def _efficiency(setup: str, model: str, rs: list[dict[str, Any]]) -> dict[str, Any]:
    ans = [r for r in rs if not r["no_tool"] and not r.get("error")]
    reached = [r["calls_to_gold"] for r in ans if r["calls_to_gold"]]
    lat = [r["latency_ms"] / 1000 for r in ans]
    return {
        "setup": setup,
        "model": model,
        "n": str(len(ans)),
        "tool_calls": _mean([r["total_tool_calls"] for r in ans]),
        "discovery": _mean([r["discovery_calls"] for r in ans]),
        "real": _mean([r["real_tool_calls"] for r in ans]),
        "wasted": _mean([r["wasted_real_calls"] for r in ans]),
        "calls_to_gold": _mean(reached) + f" (n={len(reached)})",
        "never": _rate([not r["calls_to_gold"] for r in ans]),
        "llm_calls": _mean([r["llm_calls"] for r in ans]),
        "router_llm": _mean([r.get("router_llm_calls", 0) for r in ans]),
        "in_tok": _mean([r["input_tokens"] for r in ans], "{:,.0f}"),
        "router_in_tok": _mean([r.get("router_input_tokens", 0) for r in ans], "{:,.0f}"),
        "out_tok": _mean([r["output_tokens"] for r in ans], "{:,.0f}"),
        "latency": _mean(lat, "{:.1f}"),
        "latency_p50": f"{statistics.median(lat):.1f}" if lat else "–",
        "router_lat": _mean([r.get("router_latency_ms", 0) / 1000 for r in ans], "{:.1f}"),
        "_raw": {
            "llm": statistics.fmean([r["llm_calls"] for r in ans]) if ans else 0.0,
            "tok": statistics.fmean([r["input_tokens"] for r in ans]) if ans else 0.0,
            "lat": statistics.fmean(lat) if lat else 0.0,
            "tools": statistics.fmean([r["total_tool_calls"] for r in ans]) if ans else 0.0,
            "top1": statistics.fmean([bool(r["top1_correct"]) for r in ans]) if ans else 0.0,
        },
    }


def _no_tool(setup: str, model: str, rs: list[dict[str, Any]]) -> dict[str, str]:
    nt = [r for r in rs if r["no_tool"]]
    ok = [r for r in nt if not r.get("error")]
    return {
        "setup": setup,
        "model": model,
        "n": str(len(nt)),
        "errors": str(len(nt) - len(ok)),
        "abstain": _rate([bool(r["top1_correct"]) for r in nt]),
        "wasted": _mean([r["wasted_real_calls"] for r in ok]),
        "any_wasted": _rate([r["real_tool_calls"] > 0 for r in ok]),
        "discovery": _mean([r["discovery_calls"] for r in ok]),
        "llm_calls": _mean([r["llm_calls"] for r in ok]),
        "in_tok": _mean([r["input_tokens"] for r in ok], "{:,.0f}"),
        "latency": _mean([r["latency_ms"] / 1000 for r in ok], "{:.1f}"),
    }


def _md(cols: list[tuple[str, str]], rows: list[dict[str, Any]]) -> list[str]:
    out = ["| " + " | ".join(h for _, h in cols) + " |", "|" + "---|" * len(cols)]
    return out + ["| " + " | ".join(str(r[k]) for k, _ in cols) + " |" for r in rows]


def readout(eff: list[dict[str, Any]]) -> list[str]:
    """Plain-language comparison of each discovery setup against all_tools (same model)."""
    lines: list[str] = []
    base = {r["model"]: r["_raw"] for r in eff if r["setup"] == "all_tools"}
    for r in eff:
        if r["setup"] == "all_tools" or r["model"] not in base:
            continue
        b, x = base[r["model"]], r["_raw"]

        def pct(new: float, old: float) -> str:
            return f"{(new - old) / old * 100:+.0f}%" if old else "n/a"

        lines.append(
            f"- **{r['setup']}** vs all_tools ({r['model']}): "
            f"{x['llm'] - b['llm']:+.2f} LLM calls/task ({pct(x['llm'], b['llm'])}), "
            f"{x['tools'] - b['tools']:+.2f} tool calls/task, "
            f"input tokens {pct(x['tok'], b['tok'])}, latency {pct(x['lat'], b['lat'])}, "
            f"top-1 {x['top1'] - b['top1']:+.2f} (non-error answerable rows)."
        )
    return lines


def write_summary(out_dir: Path, qids: list[str], meta: dict[str, Any]) -> str:
    rows = load_results(out_dir / "results.jsonl")
    cells, partial = complete_cells(rows, qids)
    acc = [_accuracy(s, m, rs) for (s, m), rs in cells.items()]
    eff = [_efficiency(s, m, rs) for (s, m), rs in cells.items()]
    nt = [_no_tool(s, m, rs) for (s, m), rs in cells.items()]
    for name, cols, table in (
        ("summary", ACCURACY, acc),
        ("efficiency", EFFICIENCY, eff),
        ("no_tool", NO_TOOL, nt),
    ):
        with (out_dir / f"{name}.csv").open("w", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=[k for k, _ in cols], extrasaction="ignore")
            writer.writeheader()
            writer.writerows(table)
    lines = [
        "# deepagents harness: tool discovery inside an agent loop",
        "",
        f"Sample: {len(qids)} dev-split `datasets_v1` questions "
        f"({meta.get('n_answerable', '?')} answerable, {meta.get('n_no_tool', '?')} no-tool); "
        f"catalog of {meta.get('n_tools', '?')} real tools executed by stubs; agent step cap "
        f"{meta.get('max_model_calls', 8)} model calls. Router for `router_first`: "
        f"{meta.get('router', '?')}. Skills: the same 4 SKILL.md files in every setup.",
        "",
        "Rates are `mean (count/n)`. Accuracy counts error rows as wrong. Efficiency and "
        "no-tool cost columns are means over non-error rows. LLM calls, tokens and latency "
        "INCLUDE the router call for `router_first` (also shown on its own). Only complete "
        "(setup, model) cells are shown.",
        "",
        "## Accuracy (answerable questions)",
        "",
        *_md(ACCURACY, acc),
        "",
        "## Tool-call efficiency per task (answerable questions)",
        "",
        "`wasted before gold` = wrong real-tool calls before the first gold call (all real "
        "calls if gold was never reached). `calls-to-gold` = 1-based position of the first "
        "gold call among ALL tool calls (searches included), over tasks that reached gold.",
        "",
        *_md(EFFICIENCY, eff),
        "",
        "## No-tool questions (correct behaviour: abstain)",
        "",
        "Any real tool call on these is wasted.",
        "",
        *_md(NO_TOOL, nt),
        "",
        "## Readout",
        "",
        *(readout(eff) or ["- (needs all_tools and a discovery setup for the same model)"]),
    ]
    if partial:
        lines += ["", "Incomplete cells (not in the tables):", *[f"- {p}" for p in partial]]
    text = "\n".join(lines) + "\n"
    (out_dir / "summary.md").write_text(text)
    return text
