"""Sample questions, run (setup x model x question) cells, write ``results.jsonl``."""

from __future__ import annotations

import itertools
import json
import random
import time
from collections import defaultdict
from collections.abc import Callable
from pathlib import Path
from typing import Any

from tooldiscoverybench.catalog.store import load_catalog
from tooldiscoverybench.harness.agent import (
    NO_TOOL,
    AgentRun,
    RouterOptions,
    run_agent,
    run_conversation,
)
from tooldiscoverybench.harness.routing import BudgetExhaustedError
from tooldiscoverybench.harness.tools import Catalog

ROOT = Path(__file__).resolve().parents[3]
QUESTIONS = ROOT / "data/golden/questions.jsonl"
TEST_QIDS = ROOT / "data/golden/splits/test_qids.txt"
CATALOG = ROOT / "data/catalog/public.json"


def load_harness_catalog(path: Path = CATALOG) -> Catalog:
    tools, server_desc = load_catalog(path)
    return Catalog([t for t in tools if not t.synthetic], server_desc)


def sample_questions(
    n_per_server: int = 4,
    n_no_tool: int = 8,
    seed: int = 20261010,
    questions_path: Path = QUESTIONS,
    test_qids_path: Path = TEST_QIDS,
) -> list[dict[str, Any]]:
    """Dev-split ``datasets_v1`` questions, stratified by the gold tool's server.

    Never returns a qid listed in the frozen test split (checked twice: the ``split`` field
    and ``test_qids.txt``).
    """
    test = set(test_qids_path.read_text().split())
    rows = [json.loads(line) for line in questions_path.read_text().splitlines() if line.strip()]
    dev = [
        r
        for r in rows
        if r["source"] == "datasets_v1" and r["split"] == "dev" and r["qid"] not in test
    ]
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in dev:
        groups[r["gold"][0].split(".", 1)[0] if r["gold"] else NO_TOOL].append(r)
    rng = random.Random(seed)
    strata: list[list[dict[str, Any]]] = []
    for key in sorted(groups):
        pool = sorted(groups[key], key=lambda r: r["qid"])
        rng.shuffle(pool)
        strata.append(pool[: n_no_tool if key == NO_TOOL else n_per_server])
    # round-robin across strata so any prefix (--limit) is also roughly balanced
    picked = [s[i] for i in range(max(map(len, strata))) for s in strata if i < len(s)]
    assert not {r["qid"] for r in picked} & test, "test-split question leaked into the sample"
    return picked


def score_row(q: dict[str, Any], setup: str, model_id: str, run: AgentRun) -> dict[str, Any]:
    """One results.jsonl row. Totals (LLM calls, tokens, latency) include the router call."""
    gold = list(q["gold"])
    real = run.log.real_calls()
    first = real[0].tool_id if real else None
    searches = [c for c in run.log.calls if c.via == "search"]
    no_tool = not gold
    u = run.usage
    events = run.router_events
    routed = [e for e in events if e["source"] == "user_message"]
    router_llm = sum(int(e.get("llm_calls") or 0) for e in events)
    router_in = sum(int(e.get("input_tokens") or 0) for e in events)
    router_out = sum(int(e.get("output_tokens") or 0) for e in events)
    costs = [e["cost_usd"] for e in events if e.get("cost_usd") is not None]
    # tool-call efficiency: positions are 1-based over ALL tool calls (discovery + real)
    all_calls = run.log.calls
    gold_pos = next(
        (i for i, c in enumerate(all_calls, 1) if c.via != "search" and c.tool_id in gold), None
    )
    gold_real_pos = next((i for i, c in enumerate(real, 1) if c.tool_id in gold), None)
    # wrong real calls before the first gold call; for no-tool questions every real call
    wasted = (gold_real_pos - 1) if gold_real_pos else len(real)
    row: dict[str, Any] = {
        "setup": setup,
        "model": model_id,
        "qid": q["qid"],
        "question": q["question"],
        "gold": gold,
        "no_tool": no_tool,
        "gold_server": gold[0].split(".", 1)[0] if gold else NO_TOOL,
        "first_tool": first,
        "tools_called": [c.tool_id for c in real],
        "top1_correct": (first is None) if no_tool else (first in gold),
        "gold_ever_called": None if no_tool else gold_real_pos is not None,
        "abstained": first is None,
        "said_no_tool": NO_TOOL in (run.final_text or ""),
        # efficiency
        "total_tool_calls": len(all_calls),
        "discovery_calls": len(searches),
        "real_tool_calls": len(real),
        "wasted_real_calls": wasted,
        "calls_to_gold": gold_pos,
        "real_calls_to_gold": gold_real_pos,
        "ended_with_gold": None if no_tool else bool(real) and real[-1].tool_id in gold,
        # cost: totals include the router; router also reported on its own
        "llm_calls": u.calls + router_llm,
        "agent_llm_calls": u.calls,
        "router_llm_calls": router_llm,
        "input_tokens": u.input_tokens + router_in,
        "output_tokens": u.output_tokens + router_out,
        "router_input_tokens": router_in,
        "router_output_tokens": router_out,
        "latency_ms": round(run.latency_ms, 1),  # wall time of the turn, router included
        "router_latency_ms": round(sum(e["latency_ms"] for e in events), 1),
        # one entry per router call (new user message or request_tools)
        "router_calls": len(events),
        "router_call_latencies_ms": [e["latency_ms"] for e in events],
        "request_tools_calls": sum(e["source"] == "request_tools" for e in events),
        "router_cost_usd": round(sum(costs), 8) if costs else None,
        "tool_search_calls": len(searches),
        "search_inputs": [s["input"] for s in run.log.searches],
        "search_hits": [s["hits"] for s in run.log.searches],
        "search_errors": [s["error"] for s in run.log.searches if s["error"]],
        "search_found_gold": (
            None if no_tool else any(g in s["hits"] for s in run.log.searches for g in gold)
        ),
        "initially_loaded": run.initially_loaded if setup != "all_tools" else "ALL",
        "loaded_at_end": run.loaded_at_end,
        "unloaded_tool_calls": run.unloaded_calls,
        "hit_step_cap": run.hit_step_cap,
        "skills_read": run.skills_read,
        "builtin_calls": run.builtin_calls,
        "final_text": run.final_text,
        "trace": run.trace,
        "error": run.error,
        "llm_errors": u.errors,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    if events:
        picked = [t for e in routed for t in e["tool_ids"]]
        row.update(
            router_label=events[0]["label"],
            router_model=events[0]["model"],
            router_tools=picked,
            router_hit=None if no_tool else any(g in picked for g in gold),
            router_error=next((e["error"] for e in events if e.get("error")), None),
            fallback_used=len(searches) > 0,
            router_events=events,
        )
    return row


# ------------------------------------------------------------------ multi-turn suite
def build_conversations(
    n_same_server: int = 5,
    n_cross_server: int = 5,
    n_ends_no_tool: int = 3,
    n_three_turn: int = 2,
    seed: int = 20261011,
    exclude_qids: set[str] | None = None,
    questions_path: Path = QUESTIONS,
    test_qids_path: Path = TEST_QIDS,
) -> list[dict[str, Any]]:
    """Short conversations whose every follow-up needs a DIFFERENT tool than the turn before.

    Each turn is a dev-split ``datasets_v1`` question with its own gold, so gold per turn is
    the harness-grounded label. Kinds: ``same_server`` (follow-up on another tool of the
    same server), ``cross_server``, ``ends_no_tool`` (follow-up no tool can do) and
    ``three_turn``. No question is used twice and none is in the frozen test split.
    """
    test = set(test_qids_path.read_text().split())
    skip = test | (exclude_qids or set())
    rows = [json.loads(line) for line in questions_path.read_text().splitlines() if line.strip()]
    rng = random.Random(seed)
    by_tool: dict[str, list[dict[str, Any]]] = defaultdict(list)
    none: list[dict[str, Any]] = []
    for r in sorted(rows, key=lambda r: r["qid"]):
        if r["source"] != "datasets_v1" or r["split"] != "dev" or r["qid"] in skip:
            continue
        (by_tool[r["gold"][0]] if r["gold"] else none).append(r)
    for pool in [*by_tool.values(), none]:
        rng.shuffle(pool)
    by_server: dict[str, list[str]] = defaultdict(list)
    for tool in sorted(by_tool):
        by_server[tool.split(".", 1)[0]].append(tool)

    def take(tool: str | None) -> dict[str, Any] | None:
        pool = none if tool is None else by_tool[tool]
        return pool.pop() if pool else None

    def pick_tools(kind: str, i: int) -> list[str | None]:
        servers = sorted(s for s in by_server if any(by_tool[t] for t in by_server[s]))
        rng.shuffle(servers)
        multi = [s for s in servers if sum(bool(by_tool[t]) for t in by_server[s]) >= 2]

        def tools_of(server: str, n: int) -> list[str | None]:
            live = [t for t in by_server[server] if by_tool[t]]
            return list(rng.sample(live, n))

        if kind == "same_server":
            return tools_of(multi[i % len(multi)], 2)
        if kind == "cross_server":
            return [*tools_of(servers[0], 1), *tools_of(servers[1], 1)]
        if kind == "ends_no_tool":
            return [*tools_of(servers[0], 1), None]
        return [*tools_of(multi[i % len(multi)], 2), *tools_of(servers[-1], 1)][:3]

    plan = (
        ["same_server"] * n_same_server
        + ["cross_server"] * n_cross_server
        + ["ends_no_tool"] * n_ends_no_tool
        + ["three_turn"] * n_three_turn
    )
    out: list[dict[str, Any]] = []
    for i, kind in enumerate(plan):
        turns = [take(t) for t in pick_tools(kind, i)]
        if any(t is None for t in turns):
            raise ValueError(f"not enough dev questions for a {kind} conversation")
        qs = [t for t in turns if t is not None]
        for a, b in itertools.pairwise(qs):
            assert not set(a["gold"]) & set(b["gold"]), "follow-up must need a different tool"
        out.append(
            {
                "conv_id": f"mt-{i + 1:02d}",
                "kind": kind,
                "turns": [
                    {
                        "qid": q["qid"],
                        "question": q["question"],
                        "gold": list(q["gold"]),
                        "no_tool": not q["gold"],
                    }
                    for q in qs
                ],
            }
        )
    assert not {t["qid"] for c in out for t in c["turns"]} & test, "test-split question leaked"
    return out


def run_conversation_cell(
    setup: str,
    model_id: str,
    model: Any,
    conversations: list[dict[str, Any]],
    catalog: Catalog,
    out_path: Path,
    *,
    router: Any = None,
    max_model_calls: int = 8,
    options: RouterOptions | None = None,
    budget_left: Callable[[], int] | None = None,
    reserve_per_turn: int = 12,
    log: Callable[[str], None] = print,
) -> int:
    """Run every conversation of one (setup, model) cell; one row per turn, written per
    conversation so a conversation is never half recorded. Returns rows written."""
    done = latest_rows(load_results(out_path))
    written = 0
    for i, conv in enumerate(conversations, 1):
        n = len(conv["turns"])
        keys = [f"{conv['conv_id']}#t{t}" for t in range(1, n + 1)]
        if all((setup, model_id, k) in done for k in keys):
            continue
        if budget_left is not None and budget_left() < reserve_per_turn * n:
            raise BudgetExhaustedError(
                f"stopping before {setup}/{model_id}/{conv['conv_id']}: budget low"
            )
        runs = run_conversation(
            model,
            [t["question"] for t in conv["turns"]],
            setup,
            catalog,
            router,
            max_model_calls,
            options=options,
        )
        rows = []
        for t, (turn, run) in enumerate(zip(conv["turns"], runs, strict=True), 1):
            row = score_row({**turn, "qid": keys[t - 1]}, setup, model_id, run)
            row.update(
                conv_id=conv["conv_id"],
                conv_kind=conv["kind"],
                turn=t,
                n_turns=n,
                source_qid=turn["qid"],
            )
            rows.append(row)
        with out_path.open("a") as fh:
            fh.writelines(json.dumps(r) + "\n" for r in rows)
        written += len(rows)
        log(
            f"[mt {setup} {model_id}] {i}/{len(conversations)} {conv['conv_id']} "
            f"ok={[r['top1_correct'] for r in rows]} llm={sum(r['llm_calls'] for r in rows)} "
            f"router={sum(r['router_calls'] for r in rows)} "
            f"search={sum(r['tool_search_calls'] for r in rows)} "
            f"err={next((r['error'][:60] for r in rows if r['error']), '')}"
        )
    return written


def load_results(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def latest_rows(rows: list[dict[str, Any]]) -> dict[tuple[str, str, str], dict[str, Any]]:
    """Last row per (setup, model, qid): reruns of error rows replace the earlier row."""
    out: dict[tuple[str, str, str], dict[str, Any]] = {}
    for r in rows:
        out[(r["setup"], r["model"], r["qid"])] = r
    return out


def run_cell(
    setup: str,
    model_id: str,
    model: Any,
    questions: list[dict[str, Any]],
    catalog: Catalog,
    out_path: Path,
    *,
    router: Any = None,
    selector_model: Any = None,
    max_model_calls: int = 8,
    options: RouterOptions | None = None,
    retry_errors: bool = False,
    budget_left: Callable[[], int] | None = None,
    reserve_per_question: int = 12,
    log: Callable[[str], None] = print,
) -> int:
    """Run every question of one (setup, model) cell, appending rows. Returns rows written."""
    done = latest_rows(load_results(out_path))
    written = 0
    for i, q in enumerate(questions, 1):
        prev = done.get((setup, model_id, q["qid"]))
        if prev and not (retry_errors and (prev.get("error") or prev.get("router_error"))):
            continue
        if budget_left is not None and budget_left() < reserve_per_question:
            raise BudgetExhaustedError(f"stopping before {setup}/{model_id}/{q['qid']}: budget low")
        run = run_agent(
            model, q["question"], setup, catalog, router, max_model_calls, selector_model, options
        )
        row = score_row(q, setup, model_id, run)
        with out_path.open("a") as fh:
            fh.write(json.dumps(row) + "\n")
        written += 1
        log(
            f"[{setup} {model_id}] {i}/{len(questions)} {q['qid']} first={row['first_tool']} "
            f"ok={row['top1_correct']} llm={row['llm_calls']} search={row['tool_search_calls']} "
            f"err={(row['error'] or '')[:80]}"
        )
    return written
