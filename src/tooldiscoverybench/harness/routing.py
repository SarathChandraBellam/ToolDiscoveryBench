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
import json
import re
import time
from dataclasses import dataclass, field
from typing import Any

from tooldiscoverybench.core.models import Tool
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
            raw={"text": text[:400]},
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

    def pick(self, question: str, tools: list[Tool]) -> RouterPick:
        res = asyncio.run(self.router.route(question, tools, self.server_desc))
        return RouterPick(
            [tid for tid, _ in res.ranked[: self.k]],
            res.latency_ms,
            ROUTER_LABELS[self.kind],
            self.model_id,
            llm_calls=res.calls,
            input_tokens=res.input_tokens or 0,
            output_tokens=res.output_tokens or 0,
            error=res.error,
            raw={"cost_usd": res.cost_usd},
        )
