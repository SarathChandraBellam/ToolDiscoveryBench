"""Summary tables (markdown + csv) over COMPLETE (setup, model) cells only.

Tables: a comparison across setups (accuracy, calls, tokens, router latency per call,
task latency, router cost), accuracy (answerable questions), tool-call efficiency
(answerable), no-tool questions (abstention), plus a short generated readout comparing
discovery setups with ``all_tools``. ``write_multiturn_summary`` does the same per turn and
per conversation for the multi-turn suite.
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
COMPARISON = [
    ("setup", "setup"),
    ("model", "model"),
    ("n", "tasks"),
    ("errors", "errors"),
    ("top1", "first call correct"),
    ("gold_ever", "gold reached"),
    ("abstain", "correct abstention"),
    ("tool_calls", "tool calls/task"),
    ("llm_calls", "LLM calls/task"),
    ("in_tok", "input tok/task"),
    ("router_calls", "router calls/task"),
    ("router_tok", "router input tok/task"),
    ("router_lat", "router latency per call s (mean / p50 / p90)"),
    ("latency", "task latency s (mean / p50 / p90)"),
    ("router_cost", "router cost $/task"),
    ("cost", "total cost $/task (agent + router)"),
]
PER_TURN = [
    ("setup", "setup"),
    ("model", "model"),
    ("turn", "turn"),
    ("n", "n"),
    ("top1", "first call correct (answerable)"),
    ("abstain", "correct abstention"),
    ("router_calls", "router calls"),
    ("request_tools", "request_tools calls"),
    ("searches", "tool_search calls"),
    ("llm_calls", "LLM calls"),
    ("in_tok", "input tok"),
    ("latency", "latency s (mean / p50 / p90)"),
]
PER_CONVERSATION = [
    ("setup", "setup"),
    ("model", "model"),
    ("n", "conversations"),
    ("errors", "with an error"),
    ("all_correct", "every turn's first call correct"),
    ("turns_correct", "turns correct"),
    ("router_calls", "router calls"),
    ("request_tools", "request_tools calls"),
    ("searches", "fallback / tool_search calls"),
    ("llm_calls", "LLM calls"),
    ("in_tok", "input tok"),
    ("out_tok", "output tok"),
    ("latency", "latency s (mean / p50 / p90)"),
    ("router_lat", "router s"),
    ("cost", "router cost $"),
    ("total_cost", "total cost $"),
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


def _pct(values: list[float], q: float) -> float:
    """Nearest-rank percentile (q in 0..100)."""
    ordered = sorted(values)
    return ordered[max(0, min(len(ordered) - 1, round(q / 100 * len(ordered) + 0.5) - 1))]


def _dist(values: list[float], fmt: str = "{:.1f}") -> str:
    """``mean / p50 / p90``."""
    if not values:
        return "–"
    return " / ".join(
        fmt.format(v) for v in (statistics.fmean(values), _pct(values, 50), _pct(values, 90))
    )


def _cost(rows: list[dict[str, Any]]) -> str:
    """Mean router cost per row over rows that made a paid router call; ``0`` if none did."""
    if not any(r.get("router_calls") for r in rows):
        return "–"
    costs = [r["router_cost_usd"] for r in rows if r.get("router_cost_usd") is not None]
    if not costs:
        return "0 (free)"
    return f"{sum(costs) / len(rows):.6f}"


def _router_calls(r: dict[str, Any]) -> int:
    # rows written before router events existed made exactly router_llm_calls router calls
    return int(r.get("router_calls", r.get("router_llm_calls", 0)) or 0)


def _router_latencies(rows: list[dict[str, Any]]) -> list[float]:
    out: list[float] = []
    for r in rows:
        if "router_call_latencies_ms" in r:
            out += [ms / 1000 for ms in r["router_call_latencies_ms"]]
        elif _router_calls(r):
            out.append(r.get("router_latency_ms", 0) / 1000)
    return out


def _comparison(setup: str, model: str, rs: list[dict[str, Any]]) -> dict[str, str]:
    """One row of the headline table. Accuracy counts error rows as wrong; cost columns are
    means over non-error rows and include router calls."""
    ok = [r for r in rs if not r.get("error")]
    ans = [r for r in rs if not r["no_tool"]]
    nt = [r for r in rs if r["no_tool"]]
    return {
        "setup": setup,
        "model": model,
        "n": str(len(rs)),
        "errors": str(len(rs) - len(ok)),
        "top1": _rate([bool(r["top1_correct"]) for r in ans]),
        "gold_ever": _rate([bool(r["gold_ever_called"]) for r in ans]),
        "abstain": _rate([bool(r["top1_correct"]) for r in nt]),
        "tool_calls": _mean([r["total_tool_calls"] for r in ok]),
        "llm_calls": _mean([r["llm_calls"] for r in ok]),
        "in_tok": _mean([r["input_tokens"] for r in ok], "{:,.0f}"),
        "router_calls": _mean([_router_calls(r) for r in ok]),
        "router_tok": _mean([r.get("router_input_tokens", 0) for r in ok], "{:,.0f}"),
        "router_lat": _dist(_router_latencies(ok), "{:.2f}"),
        "latency": _dist([r["latency_ms"] / 1000 for r in ok]),
        "router_cost": _cost(ok),
        "cost": _mean(
            [float(r.get("cost_usd", r.get("router_cost_usd")) or 0) for r in ok], "{:.6f}"
        ),
    }


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
    router = setup.startswith("router_first")
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
    comp = [_comparison(s, m, rs) for (s, m), rs in cells.items()]
    acc = [_accuracy(s, m, rs) for (s, m), rs in cells.items()]
    eff = [_efficiency(s, m, rs) for (s, m), rs in cells.items()]
    nt = [_no_tool(s, m, rs) for (s, m), rs in cells.items()]
    for name, cols, table in (
        ("comparison", COMPARISON, comp),
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
        f"{meta.get('router', '?')}. Router for `router_first_jev`: "
        f"{meta.get('jev_router', 'Jev (paid)')}. Skills: the same 4 SKILL.md files in "
        "every setup.",
        "",
        "Rates are `mean (count/n)`. Accuracy counts error rows as wrong. Efficiency and "
        "no-tool cost columns are means over non-error rows. LLM calls, tokens and latency "
        "INCLUDE the router call for `router_first` (also shown on its own). Only complete "
        "(setup, model) cells are shown.",
        "",
        "## Comparison (all questions)",
        "",
        "First call correct and gold reached are over answerable questions, correct "
        "abstention over no-tool questions; the other columns are means over all non-error "
        "tasks. Router latency is per router call; task latency is end to end and includes "
        "it. Router cost is what OpenRouter reported for the paid Jev calls.",
        "",
        *_md(COMPARISON, comp),
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


# ------------------------------------------------------------------ multi-turn suite
def _per_turn(setup: str, model: str, rs: list[dict[str, Any]]) -> list[dict[str, str]]:
    out = []
    for turn in sorted({r["turn"] for r in rs}):
        t = [r for r in rs if r["turn"] == turn]
        ok = [r for r in t if not r.get("error")]
        out.append(
            {
                "setup": setup,
                "model": model,
                "turn": str(turn),
                "n": str(len(t)),
                "top1": _rate([bool(r["top1_correct"]) for r in t if not r["no_tool"]]),
                "abstain": _rate([bool(r["top1_correct"]) for r in t if r["no_tool"]]),
                "router_calls": _mean([_router_calls(r) for r in ok]),
                "request_tools": _mean([r.get("request_tools_calls", 0) for r in ok]),
                "searches": _mean([r["tool_search_calls"] for r in ok]),
                "llm_calls": _mean([r["llm_calls"] for r in ok]),
                "in_tok": _mean([r["input_tokens"] for r in ok], "{:,.0f}"),
                "latency": _dist([r["latency_ms"] / 1000 for r in ok]),
            }
        )
    return out


def _per_conversation(setup: str, model: str, rs: list[dict[str, Any]]) -> dict[str, str]:
    convs: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in rs:
        convs[r["conv_id"]].append(r)
    groups = list(convs.values())
    ok = [g for g in groups if not any(r.get("error") for r in g)]

    def total(key: str) -> list[float]:
        return [sum(float(r.get(key) or 0) for r in g) for g in ok]

    costs = [r["router_cost_usd"] for g in ok for r in g if r.get("router_cost_usd") is not None]
    routed = any(_router_calls(r) for g in ok for r in g)
    return {
        "setup": setup,
        "model": model,
        "n": str(len(groups)),
        "errors": str(len(groups) - len(ok)),
        "all_correct": _rate([all(r["top1_correct"] for r in g) for g in groups]),
        "turns_correct": _rate([bool(r["top1_correct"]) for g in groups for r in g]),
        "router_calls": _mean([sum(_router_calls(r) for r in g) for g in ok]),
        "request_tools": _mean(total("request_tools_calls")),
        "searches": _mean(total("tool_search_calls")),
        "llm_calls": _mean(total("llm_calls")),
        "in_tok": _mean(total("input_tokens"), "{:,.0f}"),
        "out_tok": _mean(total("output_tokens"), "{:,.0f}"),
        "latency": _dist([v / 1000 for v in total("latency_ms")]),
        "router_lat": _mean([v / 1000 for v in total("router_latency_ms")], "{:.2f}"),
        "total_cost": _mean(
            [sum(float(r.get("cost_usd", r.get("router_cost_usd")) or 0) for r in g) for g in ok],
            "{:.6f}",
        ),
        "cost": (
            "–" if not routed else f"{sum(costs) / len(ok):.6f}" if costs and ok else "0 (free)"
        ),
    }


def write_multiturn_summary(out_dir: Path, turn_keys: list[str], meta: dict[str, Any]) -> str:
    """``multiturn_summary.md`` + csvs over complete (setup, model) cells of the suite."""
    rows = load_results(out_dir / "multiturn_results.jsonl")
    cells, partial = complete_cells(rows, turn_keys)
    comp = [_comparison(s, m, rs) for (s, m), rs in cells.items()]
    turns = [row for (s, m), rs in cells.items() for row in _per_turn(s, m, rs)]
    convs = [_per_conversation(s, m, rs) for (s, m), rs in cells.items()]
    for name, cols, table in (
        ("multiturn_comparison", COMPARISON, comp),
        ("multiturn_per_turn", PER_TURN, turns),
        ("multiturn_per_conversation", PER_CONVERSATION, convs),
    ):
        with (out_dir / f"{name}.csv").open("w", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=[k for k, _ in cols], extrasaction="ignore")
            writer.writeheader()
            writer.writerows(table)
    lines = [
        "# deepagents harness: multi-turn suite",
        "",
        f"{meta.get('n_conversations', '?')} conversations, {len(turn_keys)} turns "
        f"({meta.get('kinds', '')}), built from dev-split `datasets_v1` questions; every "
        "follow-up needs a different tool than the turn before, gold per turn. One agent "
        f"thread per conversation (checkpointer); step cap {meta.get('max_model_calls', 8)} "
        f"model calls per turn. Router setups: {meta.get('router_options', '')}. Router for "
        f"`router_first`: {meta.get('router', '?')}; for `router_first_jev`: "
        f"{meta.get('jev_router', 'Jev (paid)')}.",
        "",
        "Rates are `mean (count/n)`; error rows count as wrong and are left out of cost "
        "means. Only complete (setup, model) cells are shown.",
        "",
        "## Comparison (per turn)",
        "",
        "A task is one turn. Router latency is per router call; task latency is end to end "
        "and includes it.",
        "",
        *_md(COMPARISON, comp),
        "",
        "## By turn position",
        "",
        *_md(PER_TURN, turns),
        "",
        "## Per conversation (sums over a conversation's turns, then mean)",
        "",
        *_md(PER_CONVERSATION, convs),
    ]
    if partial:
        lines += ["", "Incomplete cells (not in the tables):", *[f"- {p}" for p in partial]]
    text = "\n".join(lines) + "\n"
    (out_dir / "multiturn_summary.md").write_text(text)
    return text
