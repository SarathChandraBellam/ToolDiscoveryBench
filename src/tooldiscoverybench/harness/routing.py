"""The upfront router for the ``router_first`` setup.

``bm25``                The repo's BM25 baseline as a shortlist: top-k by BM25 over the question.
                        No model call (0 LLM calls, 0 tokens).
``free_llm`` (default)  ONE chat call to a free OpenRouter model that returns the top-k tool
                        ids as JSON. Labelled "free-model router" in results. The repo's
                        decision-router path (``/api/alpha/decisions``) only serves decision
                        models (Jev, GPT-6 Luna Decisions); it rejects free chat models, so
                        the free router is a plain chat completion.
``jev``                 The real TypeSafe Jev router via the repo's ``OpenRouterDecisionsRouter``
                        (flat mode). It is PAID: it only runs with ``allow_paid=True``
                        (``--allow-paid-router``), which needs the owner's approval.
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import json
import re
import threading
import time
from dataclasses import dataclass, field
from typing import Any

from tooldiscoverybench.core.models import Tool
from tooldiscoverybench.harness.models import call_cost
from tooldiscoverybench.routers.base import catalog_lines

ROUTER_PROMPT = (
    "You route a user's request to the tools an AI agent should have loaded. Available tools "
    "(id: description):\n{catalog}\n\nReturn the ids of the {k} tools most likely to be the "
    "right FIRST call for the request, best first. Use only ids from the list. Reply with JSON "
    'only, exactly: {{"tools": ["<id>", ...]}}'
)

ROUTER_LABELS = {"free_llm": "free-model router", "jev": "Jev (paid)", "bm25": "BM25 shortlist"}
#: ``metadata.lc_source`` of router model calls, so usage counters can split them out
ROUTER_SOURCE = "tdb_router"
#: charged against the Jev spend cap when OpenRouter reports no cost for a call
UNREPORTED_COST_USD = 0.001


class BudgetExhaustedError(RuntimeError):
    """A run must stop cleanly: free-model quota or the paid-router spend cap is used up."""


@dataclass
class RouterPick:
    tool_ids: list[str]
    latency_ms: float
    label: str
    model: str
    llm_calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    error: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)


def parse_tool_ids(text: str, known: set[str], k: int) -> list[str]:
    """Pull tool ids from a model reply: JSON first, then any known id mentioned."""
    picked: list[str] = []
    match = re.search(r"\{.*\}", text or "", re.DOTALL)
    if match:
        try:
            data = json.loads(match.group(0))
            values = data.get("tools", []) if isinstance(data, dict) else []
            picked = [str(v).strip() for v in values if isinstance(v, str)]
        except json.JSONDecodeError:
            picked = []
    if not picked:
        positions = sorted((text.find(tid), tid) for tid in known if tid in (text or ""))
        picked = [tid for _, tid in positions]
    out: list[str] = []
    for tid in picked:
        if tid in known and tid not in out:
            out.append(tid)
    return out[:k]


class BM25ShortlistRouter:
    kind = "bm25"

    def __init__(self, server_desc: dict[str, str], k: int = 3) -> None:
        self.server_desc = server_desc
        self.k = k
        self.model_id = "bm25"

    def pick(self, question: str, tools: list[Tool]) -> RouterPick:
        from tooldiscoverybench.routers.baselines.bm25 import bm25_rank

        started = time.perf_counter()
        ranked = bm25_rank(question, tools, self.server_desc)[: self.k]
        return RouterPick(
            [tid for tid, _ in ranked],
            (time.perf_counter() - started) * 1000,
            ROUTER_LABELS[self.kind],
            self.model_id,
            llm_calls=0,
        )


class FreeLLMRouter:
    kind = "free_llm"

    def __init__(self, model: Any, model_id: str, k: int = 3, desc_chars: int = 300) -> None:
        self.model = model
        self.model_id = model_id
        self.k = k
        self.desc_chars = desc_chars

    def pick(self, question: str, tools: list[Tool]) -> RouterPick:
        from langchain_core.messages import HumanMessage, SystemMessage

        known = {t.id for t in tools}
        started = time.perf_counter()
        prompt = ROUTER_PROMPT.format(catalog=catalog_lines(tools, self.desc_chars), k=self.k)
        try:
            msg = self.model.invoke(
                [SystemMessage(prompt), HumanMessage(question)],
                config={"metadata": {"lc_source": ROUTER_SOURCE}},
            )
        except Exception as exc:  # noqa: BLE001 - recorded on the row, agent still runs
            return RouterPick(
                [],
                (time.perf_counter() - started) * 1000,
                ROUTER_LABELS[self.kind],
                self.model_id,
                llm_calls=1,
                error=f"{type(exc).__name__}: {exc}"[:500],
            )
        usage = getattr(msg, "usage_metadata", None) or {}
        text = msg.content if isinstance(msg.content, str) else json.dumps(msg.content)
        ids = parse_tool_ids(text, known, self.k)
        return RouterPick(
            ids,
            (time.perf_counter() - started) * 1000,
            ROUTER_LABELS[self.kind],
            self.model_id,
            llm_calls=1,
            input_tokens=int(usage.get("input_tokens", 0) or 0),
            output_tokens=int(usage.get("output_tokens", 0) or 0),
            error=None if ids else "router returned no valid tool ids",
            raw={"text": text[:400], "cost_usd": call_cost(msg)},
        )


class JevDecisionRouter:
    """Real Jev via the repo's decision-router code path. Costs money: gated."""

    kind = "jev"

    def __init__(
        self,
        server_desc: dict[str, str],
        k: int = 3,
        model: str = "typesafe/jev-1.13",
        allow_paid: bool = False,
        max_spend_usd: float = 1.0,
        spent_usd: float = 0.0,
        timeout: float = 90.0,
    ) -> None:
        if not allow_paid:
            raise PermissionError(
                "router=jev calls the paid Jev decision model; pass --allow-paid-router only "
                "with the owner's approval"
            )
        from tooldiscoverybench.routers.registry import build_router

        self.router = build_router(
            {
                "type": "openrouter",
                "name": "jev-harness",
                "model": model,
                "mode": "flat",
                "allow_abstain": False,
            }
        )
        self.server_desc = server_desc
        self.k = k
        self.model_id = model
        self.max_spend_usd = max_spend_usd
        self.timeout = timeout  # hard limit per Jev call
        self.spent_usd = spent_usd  # spend so far, including earlier runs (from result files)
        self.calls = 0
        self._worst_call_usd = UNREPORTED_COST_USD

    def _run(self, coro: Any) -> Any:
        """Run on one long-lived event loop: the decisions client is bound to its loop, so
        ``asyncio.run`` per call breaks the second call. Also safe from a running loop."""
        loop = getattr(self, "_loop", None)
        if loop is None:
            loop = self._loop = asyncio.new_event_loop()
            threading.Thread(target=loop.run_forever, daemon=True, name="jev-router").start()
        future = asyncio.run_coroutine_threadsafe(coro, loop)
        try:
            return future.result(timeout=self.timeout)
        except concurrent.futures.TimeoutError:
            future.cancel()
            raise TimeoutError(f"Jev call exceeded {self.timeout:.0f}s") from None

    def pick(self, question: str, tools: list[Tool]) -> RouterPick:
        if self.spent_usd + self._worst_call_usd > self.max_spend_usd:
            raise BudgetExhaustedError(
                f"Jev spend cap: ${self.spent_usd:.4f} spent, next call could exceed "
                f"${self.max_spend_usd:.2f}"
            )
        started = time.perf_counter()
        try:
            res = self._run(self.router.route(question, tools, self.server_desc))
        except TimeoutError as exc:  # recorded on the row; the agent still runs
            self.calls += 1
            return RouterPick(
                [],
                (time.perf_counter() - started) * 1000,
                ROUTER_LABELS[self.kind],
                self.model_id,
                llm_calls=1,
                error=f"TimeoutError: {exc}",
                raw={"cost_usd": None},
            )
        # a successful call with no reported cost is charged a conservative estimate
        cost = res.cost_usd
        if cost is None:
            cost = 0.0 if res.error else UNREPORTED_COST_USD * res.calls
        self.spent_usd += cost
        self.calls += res.calls
        self._worst_call_usd = max(self._worst_call_usd, cost)
        return RouterPick(
            [tid for tid, _ in res.ranked[: self.k]],
            res.latency_ms,
            ROUTER_LABELS[self.kind],
            self.model_id,
            llm_calls=res.calls,
            input_tokens=res.input_tokens or 0,
            output_tokens=res.output_tokens or 0,
            error=res.error,
            raw={"cost_usd": res.cost_usd, "spent_usd": round(self.spent_usd, 6)},
        )
