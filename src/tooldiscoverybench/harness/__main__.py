"""CLI: ``uv run --extra deepagents python -m tooldiscoverybench.harness --config configs/harness.yaml``."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

import yaml

from tooldiscoverybench.harness import DEFAULT_SETUPS, SETUPS
from tooldiscoverybench.harness.agent import RouterOptions
from tooldiscoverybench.harness.models import (
    RequestCounter,
    assert_allowed,
    build_chat_model,
    free_quota,
)
from tooldiscoverybench.harness.multistep import multistep_tasks
from tooldiscoverybench.harness.report import (
    write_multistep_summary,
    write_multiturn_summary,
    write_summary,
)
from tooldiscoverybench.harness.routing import (
    BM25ShortlistRouter,
    BudgetExhaustedError,
    FreeLLMRouter,
    JevDecisionRouter,
)
from tooldiscoverybench.harness.runner import (
    SpendCap,
    build_conversations,
    load_harness_catalog,
    load_results,
    run_cell,
    run_conversation_cell,
    sample_questions,
    score_multistep,
)

DEFAULTS: dict[str, Any] = {
    "models": ["nvidia/nemotron-3-super-120b-a12b:free"],
    "setups": list(DEFAULT_SETUPS),
    "router": "free_llm",  # free_llm | bm25 | jev (jev is PAID: also needs allow_paid_router)
    "router_model": "apodex/apodex-1.1-mini:free",
    "jev_model": "typesafe/jev-1.13",
    "allow_paid_router": False,
    # paid AGENT models: refused unless listed here and the run passes --allow-paid-models
    "paid_models": [],
    "allow_paid_models": False,
    "max_spend_usd": 3.0,  # hard cap on recorded paid spend (agent + router) since spend_since
    "spend_since": "",  # only rows with ts >= this count towards max_spend_usd ("" = all)
    "call_timeout_s": 90,  # hard limit per model / router request
    "task_timeout_s": 300,  # wall-clock cap per task (turn); recorded as a TaskTimeout error
    "paid_requests_per_minute": 120,
    "jev_max_spend_usd": 1.0,  # hard cap on Jev spend across runs into the same out dir
    "router_k": 3,
    # ToolRouterMiddleware options, per suite (single-turn keeps the PR's first configuration)
    "request_tools": False,
    "search_fallback": True,
    "carry": "cap",  # tools loaded in earlier turns: cap | keep | replace
    "carry_cap": 5,
    "suite": "single",  # single | multiturn | multistep
    "max_own_spend_usd": None,  # paid allowance of one process when several run in parallel
    "multiturn": {
        "request_tools": True,
        "n_same_server": 5,
        "n_cross_server": 5,
        "n_ends_no_tool": 3,
        "n_three_turn": 2,
        "seed": 20261011,
    },
    "n_per_server": 4,
    "n_no_tool": 8,
    "seed": 20261010,
    "max_model_calls": 8,
    "requests_per_minute": 15,
    "quota_reserve": 25,
    "out": "/workspace/tdb-runs/harness-deepagents",
}


def parse_args(argv: list[str] | None) -> dict[str, Any]:
    p = argparse.ArgumentParser(prog="python -m tooldiscoverybench.harness", description=__doc__)
    p.add_argument("--config", type=Path, help="YAML with any of the options below")
    p.add_argument("--models", nargs="+", help="free OpenRouter model ids (must end with :free)")
    p.add_argument("--setups", nargs="+", choices=SETUPS)
    p.add_argument("--router", choices=["free_llm", "bm25", "jev"])
    p.add_argument("--router-model")
    p.add_argument(
        "--allow-paid-router",
        action="store_true",
        default=None,
        help="permit router=jev (paid). Needs the owner's approval.",
    )
    p.add_argument("--suite", choices=["single", "multiturn", "multistep"])
    p.add_argument("--max-own-spend-usd", type=float, help="paid allowance of this process")
    p.add_argument("--request-tools", action="store_true", default=None)
    p.add_argument(
        "--allow-paid-models",
        action="store_true",
        default=None,
        help="permit agent models listed in `paid_models`. Needs the owner's approval.",
    )
    p.add_argument("--max-spend-usd", type=float, help="hard cap on recorded paid spend")
    p.add_argument("--spend-since", help="count only rows with ts >= this towards the cap")
    p.add_argument("--task-timeout-s", type=float)
    p.add_argument("--call-timeout-s", type=float)
    p.add_argument("--jev-max-spend-usd", type=float, help="stop before Jev spend passes this")
    p.add_argument("--carry", choices=["cap", "keep", "replace"])
    p.add_argument("--n-per-server", type=int)
    p.add_argument("--n-no-tool", type=int)
    p.add_argument("--limit", type=int, help="only the first N sampled questions (smoke runs)")
    p.add_argument("--max-model-calls", type=int)
    p.add_argument("--requests-per-minute", type=float)
    p.add_argument("--quota-reserve", type=int, help="stop when this few free requests remain")
    p.add_argument("--retry-errors", action="store_true", help="rerun rows that errored")
    p.add_argument("--summary-only", action="store_true")
    p.add_argument("--out")
    ns = p.parse_args(argv)
    cfg = dict(DEFAULTS)
    if ns.config:
        loaded = yaml.safe_load(ns.config.read_text()) or {}
        loaded["multiturn"] = {**cfg["multiturn"], **(loaded.get("multiturn") or {})}
        cfg.update(loaded)
    for key, value in vars(ns).items():
        if value is not None and key != "config":
            cfg[key] = value
    return cfg


RESULT_FILES = {
    "single": "results.jsonl",
    "multiturn": "multiturn_results.jsonl",
    "multistep": "multistep_results.jsonl",
}


def all_rows(out: Path) -> list[dict[str, Any]]:
    return [r for name in RESULT_FILES.values() for r in load_results(out / name)]


def paid_spend(out: Path, since: str = "") -> float:
    """Recorded paid spend (agent + router/selector) in this out dir from ``since`` on."""
    return sum(
        float(r.get("cost_usd", r.get("router_cost_usd")) or 0)
        for r in all_rows(out)
        if r.get("ts", "") >= since
    )


def jev_spend(out: Path) -> float:
    """Jev cost already recorded in this out dir (every row ever written, reruns included)."""
    return sum(
        float(r.get("router_cost_usd") or 0)
        for r in all_rows(out)
        if str(r.get("router_label", "")).startswith("Jev")
    )


def main(argv: list[str] | None = None) -> int:  # noqa: PLR0912, PLR0915 - linear CLI entry
    cfg = parse_args(argv)
    out = Path(cfg["out"])
    out.mkdir(parents=True, exist_ok=True)
    catalog = load_harness_catalog()
    suite = cfg["suite"]
    mt = cfg["multiturn"]
    questions = sample_questions(cfg["n_per_server"], cfg["n_no_tool"], cfg["seed"])
    conversations: list[dict[str, Any]] = []
    if suite == "multiturn":
        # questions of the single-turn sample are not reused
        conversations = build_conversations(
            mt["n_same_server"],
            mt["n_cross_server"],
            mt["n_ends_no_tool"],
            mt["n_three_turn"],
            mt["seed"],
            exclude_qids={q["qid"] for q in questions},
        )
        if cfg.get("limit"):
            conversations = conversations[: cfg["limit"]]
    else:
        if suite == "multistep":
            questions = multistep_tasks()
        if cfg.get("limit"):
            questions = questions[: cfg["limit"]]
    qids = [q["qid"] for q in questions]
    options = RouterOptions(
        request_tools=bool(mt["request_tools"] if suite == "multiturn" else cfg["request_tools"]),
        search_fallback=bool(cfg["search_fallback"]),
        carry=str(cfg["carry"]),
        carry_cap=int(cfg["carry_cap"]),
        multi_step=suite == "multistep",
    )
    router_label = {
        "free_llm": f"free-model router ({cfg['router_model']}), top-{cfg['router_k']}",
        "bm25": f"BM25 shortlist, top-{cfg['router_k']} (no LLM call)",
        "jev": f"Jev ({cfg['jev_model']}, PAID), top-{cfg['router_k']}",
    }[cfg["router"]]
    meta = {
        "n_questions": len(qids),
        "n_answerable": sum(not q["no_tool"] for q in questions),
        "n_no_tool": sum(q["no_tool"] for q in questions),
        "n_tools": len(catalog.tools),
        "max_model_calls": cfg["max_model_calls"],
        "router": router_label,
        "jev_router": f"Jev ({cfg['jev_model']}, PAID, via /api/alpha/decisions), "
        f"top-{cfg['router_k']}",
        "models": cfg["models"],
        "setups": cfg["setups"],
        "router_options": f"a router call on every new user message, request_tools "
        f"{'on' if options.request_tools else 'off'}, tool_search fallback "
        f"{'on' if options.search_fallback else 'off'}, carry={options.carry}"
        + (f" (last {options.carry_cap})" if options.carry == "cap" else ""),
    }
    turn_keys = [
        f"{c['conv_id']}#t{t}" for c in conversations for t in range(1, len(c["turns"]) + 1)
    ]
    kinds = sorted({c["kind"] for c in conversations})
    meta["n_conversations"] = len(conversations)
    meta["kinds"] = ", ".join(f"{sum(c['kind'] == k for c in conversations)} {k}" for k in kinds)

    def summary() -> str:
        if suite == "multiturn":
            return write_multiturn_summary(out, turn_keys, meta)
        if suite == "multistep":
            return write_multistep_summary(out, qids, meta)
        return write_summary(out, qids, meta)

    if suite == "multiturn":
        (out / "multiturn_sample.json").write_text(
            json.dumps({**meta, "conversations": conversations}, indent=1)
        )
    elif suite == "multistep":
        (out / "multistep_sample.json").write_text(
            json.dumps({**meta, "tasks": questions}, indent=1)
        )
    else:
        (out / "sample.json").write_text(json.dumps({"qids": qids, **meta}, indent=1))
    if cfg.get("summary_only"):
        print(summary())
        return 0

    for m in cfg["models"]:
        assert_allowed(m, cfg["paid_models"], bool(cfg["allow_paid_models"]))
    counter = RequestCounter()  # requests to FREE models only: they draw on the daily quota
    paid_counter = RequestCounter()
    spend = SpendCap(
        float(cfg["max_spend_usd"]),
        paid_spend(out, str(cfg["spend_since"])),
        cfg["max_own_spend_usd"],
    )
    print(
        f"paid spend recorded since {cfg['spend_since'] or 'the start'}: ${spend.spent:.4f} "
        f"(cap ${spend.max_usd}, this run's allowance {spend.max_own_usd})",
        flush=True,
    )
    call_timeout, task_timeout = float(cfg["call_timeout_s"]), float(cfg["task_timeout_s"])
    uses_free = any(m.endswith(":free") for m in cfg["models"]) or (
        cfg["router"] == "free_llm" and "router_first" in cfg["setups"]
    )
    state = {"remaining": 0, "at": 0}

    def refresh_quota() -> None:
        q = free_quota()
        state["remaining"], state["at"] = int(q.get("remaining") or 0), counter.count
        print(f"free-model quota: {q}", flush=True)

    def budget_left() -> int:
        # OpenRouter's count may lag; subtract every request we sent since the last check
        return state["remaining"] - (counter.count - state["at"]) - int(cfg["quota_reserve"])

    rpm = float(cfg["requests_per_minute"])
    jev: JevDecisionRouter | None = None
    if cfg["router"] == "jev" or "router_first_jev" in cfg["setups"]:
        jev = JevDecisionRouter(
            catalog.server_desc,
            cfg["router_k"],
            cfg["jev_model"],
            bool(cfg["allow_paid_router"]),
            max_spend_usd=float(cfg["jev_max_spend_usd"]),
            spent_usd=jev_spend(out),
            timeout=call_timeout,
        )
        print(f"Jev spend so far in {out}: ${jev.spent_usd:.6f} (cap ${jev.max_spend_usd})")
    router: Any = None
    if cfg["router"] == "jev":
        router = jev
    elif cfg["router"] == "bm25":
        router = BM25ShortlistRouter(catalog.server_desc, int(cfg["router_k"]))
    elif "router_first" in cfg["setups"]:
        router_model = build_chat_model(
            cfg["router_model"],
            counter,
            requests_per_minute=rpm,
            max_tokens=1024,
            timeout=min(60.0, call_timeout),
        )
        router = FreeLLMRouter(router_model, cfg["router_model"], k=int(cfg["router_k"]))
    status = 0
    try:
        for model_id in cfg["models"]:  # one model across every setup before the next
            free = model_id.endswith(":free")
            model = build_chat_model(
                model_id,
                counter if free else paid_counter,
                requests_per_minute=rpm if free else float(cfg["paid_requests_per_minute"]),
                timeout=call_timeout,
                paid_ok=not free,
            )
            for setup in cfg["setups"]:
                if uses_free:
                    refresh_quota()
                t0 = time.perf_counter()
                common: dict[str, Any] = {
                    "router": jev if setup == "router_first_jev" else router,
                    "max_model_calls": int(cfg["max_model_calls"]),
                    "options": options,
                    "task_timeout": task_timeout,
                    "spend": spend,
                    "budget_left": budget_left if uses_free else None,
                    "log": lambda s: print(s, flush=True),
                }
                if suite == "multiturn":
                    n = run_conversation_cell(
                        setup,
                        model_id,
                        model,
                        conversations,
                        catalog,
                        out / RESULT_FILES[suite],
                        selector_model=model,
                        **common,
                    )
                else:
                    n = run_cell(
                        setup,
                        model_id,
                        model,
                        questions,
                        catalog,
                        out / RESULT_FILES[suite],
                        selector_model=model,  # langchain_selector: the agent model selects
                        retry_errors=bool(cfg.get("retry_errors")),
                        scorer=score_multistep if suite == "multistep" else None,
                        **common,
                    )
                print(
                    f"== cell {suite}/{setup}/{model_id}: {n} rows, "
                    f"{time.perf_counter() - t0:.0f}s; free requests {counter.count}, paid "
                    f"requests {paid_counter.count}, paid spend ${spend.spent:.4f} "
                    f"(this run ${spend.own:.4f})"
                    + (f"; Jev spend ${jev.spent_usd:.6f} over {jev.calls} calls" if jev else ""),
                    flush=True,
                )
    except BudgetExhaustedError as exc:
        print(f"STOP: {exc}", flush=True)
        status = 2
    print(
        f"free requests this run: {counter.count}, paid requests: {paid_counter.count}, "
        f"recorded paid spend: ${spend.spent:.4f} (this run ${spend.own:.4f})",
        flush=True,
    )
    print(summary())
    return status


if __name__ == "__main__":
    sys.exit(main())
