"""Sample questions, run (setup x model x question) cells, write ``results.jsonl``."""

from __future__ import annotations

import json
import random
import time
from collections import defaultdict
from collections.abc import Callable
from pathlib import Path
from typing import Any

from tooldiscoverybench.catalog.store import load_catalog
from tooldiscoverybench.harness.agent import NO_TOOL, AgentRun, run_agent
from tooldiscoverybench.harness.routing import RouterPick
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
    pick: RouterPick | None = run.router_pick
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
        "llm_calls": u.calls + u.router_calls,
        "agent_llm_calls": u.calls,
        "router_llm_calls": u.router_calls,
        "input_tokens": u.input_tokens + u.router_input_tokens,
        "output_tokens": u.output_tokens + u.router_output_tokens,
        "router_input_tokens": u.router_input_tokens,
        "router_output_tokens": u.router_output_tokens,
        "latency_ms": round(run.latency_ms, 1),
        "router_latency_ms": round(pick.latency_ms, 1) if pick else 0.0,
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
    if pick is not None:
        row.update(
            router_label=pick.label,
            router_model=pick.model,
            router_tools=pick.tool_ids,
            router_hit=None if no_tool else any(g in pick.tool_ids for g in gold),
            router_error=pick.error,
            fallback_used=len(searches) > 0,
        )
    return row


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


class BudgetExhaustedError(RuntimeError):
    pass


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
            model, q["question"], setup, catalog, router, max_model_calls, selector_model
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
