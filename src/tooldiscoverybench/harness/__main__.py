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
from tooldiscoverybench.harness.models import (
    RequestCounter,
    assert_free,
    build_chat_model,
    free_quota,
)
from tooldiscoverybench.harness.report import write_summary
from tooldiscoverybench.harness.routing import BM25ShortlistRouter, FreeLLMRouter, JevDecisionRouter
from tooldiscoverybench.harness.runner import (
    BudgetExhaustedError,
    load_harness_catalog,
    run_cell,
    sample_questions,
)

DEFAULTS: dict[str, Any] = {
    "models": ["nvidia/nemotron-3-super-120b-a12b:free"],
    "setups": list(DEFAULT_SETUPS),
    "router": "free_llm",  # free_llm | bm25 | jev (jev is PAID: also needs allow_paid_router)
    "router_model": "nvidia/nemotron-3.5-lightning:free",
    "jev_model": "typesafe/jev-1.13",
    "allow_paid_router": False,
    "router_k": 3,
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
        cfg.update(yaml.safe_load(ns.config.read_text()) or {})
    for key, value in vars(ns).items():
        if value is not None and key != "config":
            cfg[key] = value
    return cfg


def main(argv: list[str] | None = None) -> int:
    cfg = parse_args(argv)
    out = Path(cfg["out"])
    out.mkdir(parents=True, exist_ok=True)
    catalog = load_harness_catalog()
    questions = sample_questions(cfg["n_per_server"], cfg["n_no_tool"], cfg["seed"])
    if cfg.get("limit"):
        questions = questions[: cfg["limit"]]
    qids = [q["qid"] for q in questions]
    router_label = {
        "free_llm": f"free-model router ({cfg['router_model']}), top-{cfg['router_k']}, "
        "one call per task via ToolRouterMiddleware",
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
        "models": cfg["models"],
        "setups": cfg["setups"],
    }
    (out / "sample.json").write_text(json.dumps({"qids": qids, **meta}, indent=1))
    if cfg.get("summary_only"):
        print(write_summary(out, qids, meta))
        return 0

    for m in cfg["models"]:
        assert_free(m)
    counter = RequestCounter()
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
    router: Any
    selector_model = None
    if cfg["router"] == "jev":
        router = JevDecisionRouter(
            catalog.server_desc, cfg["router_k"], cfg["jev_model"], bool(cfg["allow_paid_router"])
        )
    elif cfg["router"] == "bm25":
        router = BM25ShortlistRouter(catalog.server_desc, int(cfg["router_k"]))
    else:
        selector_model = build_chat_model(
            cfg["router_model"], counter, requests_per_minute=rpm, max_tokens=1024
        )
        router = FreeLLMRouter(selector_model, cfg["router_model"], k=int(cfg["router_k"]))
    status = 0
    try:
        for model_id in cfg["models"]:  # one model across every setup before the next
            model = build_chat_model(model_id, counter, requests_per_minute=rpm)
            for setup in cfg["setups"]:
                refresh_quota()
                t0 = time.perf_counter()
                before = counter.count
                n = run_cell(
                    setup,
                    model_id,
                    model,
                    questions,
                    catalog,
                    out / "results.jsonl",
                    router=router,
                    selector_model=selector_model,
                    max_model_calls=int(cfg["max_model_calls"]),
                    retry_errors=bool(cfg.get("retry_errors")),
                    budget_left=budget_left,
                    log=lambda s: print(s, flush=True),
                )
                print(
                    f"== cell {setup}/{model_id}: {n} rows, {counter.count - before} requests, "
                    f"{time.perf_counter() - t0:.0f}s; total requests {counter.count}",
                    flush=True,
                )
    except BudgetExhaustedError as exc:
        print(f"STOP: {exc}", flush=True)
        status = 2
    print(f"requests sent this run: {counter.count}; quota now: {free_quota()}", flush=True)
    print(write_summary(out, qids, meta))
    return status


if __name__ == "__main__":
    sys.exit(main())
