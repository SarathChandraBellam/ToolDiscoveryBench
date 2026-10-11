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
from tooldiscoverybench.harness.report import write_multiturn_summary, write_summary
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
    "suite": "single",  # single | multiturn
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
    p.add_argument("--suite", choices=["single", "multiturn"])
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


def paid_spend(out: Path, since: str = "", models: Any = None) -> float:
    """Recorded paid spend (agent + router) in this out dir, optionally only rows from
    ``since`` on and only for ``models`` (so parallel runs of different models each keep
    their own share of a budget)."""
    rows = load_results(out / "results.jsonl") + load_results(out / "multiturn_results.jsonl")
    return sum(
        float(r.get("cost_usd", r.get("router_cost_usd")) or 0)
        for r in rows
        if r.get("ts", "") >= since and (models is None or r["model"] in models)
    )


def jev_spend(out: Path) -> float:
    """Jev cost already recorded in this out dir (every row ever written, reruns included)."""
    rows = load_results(out / "results.jsonl") + load_results(out / "multiturn_results.jsonl")
    return sum(float(r.get("router_cost_usd") or 0) for r in rows)


def main(argv: list[str] | None = None) -> int:  # noqa: PLR0912, PLR0915 - linear CLI entry point
    cfg = parse_args(argv)
    out = Path(cfg["out"])
    out.mkdir(parents=True, exist_ok=True)
    catalog = load_harness_catalog()
    multi = cfg["suite"] == "multiturn"
    mt = cfg["multiturn"]
    questions = sample_questions(cfg["n_per_server"], cfg["n_no_tool"], cfg["seed"])
    conversations: list[dict[str, Any]] = []
    if multi:
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
    elif cfg.get("limit"):
        questions = questions[: cfg["limit"]]
    qids = [q["qid"] for q in questions]
    options = RouterOptions(
        request_tools=bool(mt["request_tools"] if multi else cfg["request_tools"]),
        search_fallback=bool(cfg["search_fallback"]),
        carry=str(cfg["carry"]),
        carry_cap=int(cfg["carry_cap"]),
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
    }
    turn_keys = [
        f"{c['conv_id']}#t{t}" for c in conversations for t in range(1, len(c["turns"]) + 1)
    ]
    kinds = sorted({c["kind"] for c in conversations})
    mt_meta = {
        **meta,
        "n_conversations": len(conversations),
        "kinds": ", ".join(f"{sum(c['kind'] == k for c in conversations)} {k}" for k in kinds),
        "router_options": f"a router call on every new user message, request_tools "
        f"{'on' if options.request_tools else 'off'}, tool_search fallback "
        f"{'on' if options.search_fallback else 'off'}, carry={options.carry}"
        + (f" (last {options.carry_cap})" if options.carry == "cap" else ""),
    }

    def summary() -> str:
        if multi:
            return write_multiturn_summary(out, turn_keys, mt_meta)
        return write_summary(out, qids, meta)

    if multi:
        (out / "multiturn_sample.json").write_text(
            json.dumps({**mt_meta, "conversations": conversations}, indent=1)
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
        float(cfg["max_spend_usd"]), paid_spend(out, str(cfg["spend_since"]), set(cfg["models"]))
    )
    print(
        f"paid spend recorded so far for {cfg['models']}: ${spend.spent:.4f} "
        f"(cap ${spend.max_usd})",
        flush=True,
    )
    call_timeout, task_timeout = float(cfg["call_timeout_s"]), float(cfg["task_timeout_s"])
    quota = free_quota()
    print(f"free-model quota at start: {quota}", flush=True)
    state = {"remaining": int(quota.get("remaining") or 0), "at": 0}

    def refresh_quota() -> None:
        q = free_quota()
        state["remaining"], state["at"] = int(q.get("remaining") or 0), counter.count
        print(f"free-model quota: {q}", flush=True)

    def budget_left() -> int:
        # OpenRouter's count may lag; subtract every request we sent since the last check
        return state["remaining"] - (counter.count - state["at"]) - int(cfg["quota_reserve"])

    rpm = float(cfg["requests_per_minute"])
    selector_model = None
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
    router: Any
    if cfg["router"] == "jev":
        router = jev
    elif cfg["router"] == "bm25":
        router = BM25ShortlistRouter(catalog.server_desc, int(cfg["router_k"]))
    else:
        selector_model = build_chat_model(
            cfg["router_model"],
            counter,
            requests_per_minute=rpm,
            max_tokens=1024,
            timeout=min(60.0, call_timeout),
            max_retries=2,
        )
        router = FreeLLMRouter(selector_model, cfg["router_model"], k=int(cfg["router_k"]))
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
                refresh_quota()
                t0 = time.perf_counter()
                before = counter.count
                setup_router = jev if setup == "router_first_jev" else router
                if multi:
                    n = run_conversation_cell(
                        setup,
                        model_id,
                        model,
                        conversations,
                        catalog,
                        out / "multiturn_results.jsonl",
                        router=setup_router,
                        max_model_calls=int(cfg["max_model_calls"]),
                        options=options,
                        task_timeout=task_timeout,
                        spend=spend,
                        budget_left=budget_left,
                        log=lambda s: print(s, flush=True),
                    )
                else:
                    n = run_cell(
                        setup,
                        model_id,
                        model,
                        questions,
                        catalog,
                        out / "results.jsonl",
                        router=setup_router,
                        selector_model=selector_model,
                        max_model_calls=int(cfg["max_model_calls"]),
                        options=options,
                        retry_errors=bool(cfg.get("retry_errors")),
                        task_timeout=task_timeout,
                        spend=spend,
                        budget_left=budget_left,
                        log=lambda s: print(s, flush=True),
                    )
                print(
                    f"== cell {setup}/{model_id}: {n} rows, {counter.count - before} requests, "
                    f"{time.perf_counter() - t0:.0f}s; free requests {counter.count}, paid "
                    f"requests {paid_counter.count}, paid spend ${spend.spent:.4f}"
                    + (f"; Jev spend ${jev.spent_usd:.6f} over {jev.calls} calls" if jev else ""),
                    flush=True,
                )
    except BudgetExhaustedError as exc:
        print(f"STOP: {exc}", flush=True)
        status = 2
    print(
        f"free requests this run: {counter.count}, paid requests: {paid_counter.count}, "
        f"recorded paid spend: ${spend.spent:.4f}; quota now: {free_quota()}",
        flush=True,
    )
    if jev:
        print(f"Jev spend recorded in {out}: ${jev_spend(out):.6f}", flush=True)
    print(summary())
    return status


if __name__ == "__main__":
    sys.exit(main())
