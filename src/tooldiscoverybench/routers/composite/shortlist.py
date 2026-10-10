"""Shortlist router: a retriever narrows the catalog to its top ``k`` tools, then a decision
router chooses among them (keeping its NONE option, so it can still abstain).

Tools the retriever dropped are appended after the decider's ranking with probability 0, in
retriever order, so every catalog tool stays ranked and top-k metrics stay comparable. When
the catalog has ``k`` tools or fewer the retriever is skipped.

Config::

    - name: shortlist-bge-jev
      type: shortlist
      k: 8
      retriever: {type: embedding, model: BAAI/bge-small-en-v1.5}   # or {type: bm25}
      decider:   {type: openrouter, model: typesafe/jev-1.13, mode: flat}
"""

from __future__ import annotations

import time
from dataclasses import replace
from typing import Any

from tooldiscoverybench.core.models import RouteResult, Tool
from tooldiscoverybench.routers.base import Router
from tooldiscoverybench.routers.composite.common import build_child

DEFAULT_RETRIEVER: dict[str, Any] = {"type": "embedding", "model": "BAAI/bge-small-en-v1.5"}
DEFAULT_DECIDER: dict[str, Any] = {
    "type": "openrouter",
    "model": "typesafe/jev-1.13",
    "mode": "flat",
}


class ShortlistRouter(Router):
    calibrated = True

    def __init__(self, **cfg: Any) -> None:
        super().__init__(**cfg)
        self.k = int(cfg.get("k", 8))
        if self.k < 1:
            raise ValueError("shortlist: k must be >= 1")
        self.retriever = build_child(cfg.get("retriever") or DEFAULT_RETRIEVER, "retriever")
        self.decider = build_child(cfg.get("decider") or DEFAULT_DECIDER, "decider")
        self.calibrated = bool(getattr(self.decider, "calibrated", True))

    def unavailable_reason(self) -> str | None:
        for role, child in (("retriever", self.retriever), ("decider", self.decider)):
            reason = child.unavailable_reason()
            if reason:
                return f"{role}: {reason}"
        return None

    async def setup(self, all_tools: list[Tool], server_desc: dict[str, str]) -> None:
        await self.retriever.setup(all_tools, server_desc)
        await self.decider.setup(all_tools, server_desc)

    async def aclose(self) -> None:
        await self.retriever.aclose()
        await self.decider.aclose()

    async def route(
        self, question: str, tools: list[Tool], server_desc: dict[str, str]
    ) -> RouteResult:
        started = time.perf_counter()
        if len(tools) <= self.k:
            res = await self.decider.route(question, tools, server_desc)
            return replace(
                res, extra={"shortlist_k": len(tools), "shortlist_ids": sorted(t.id for t in tools)}
            )

        retrieved = await self.retriever.route(question, tools, server_desc)
        if retrieved.error:
            return replace(retrieved, latency_ms=(time.perf_counter() - started) * 1000)
        by_id = {t.id: t for t in tools}
        order = [tid for tid, _ in retrieved.ranked if tid in by_id]
        order += [t.id for t in tools if t.id not in set(order)]
        keep = set(order[: self.k])
        # keep the catalog's own order for the decider (no position hint from the retriever)
        short = [t for t in tools if t.id in keep]

        res = await self.decider.route(question, short, server_desc)
        decided = {tid for tid, _ in res.ranked}
        tail = [(tid, 0.0) for tid in order if tid not in decided]
        extra = {"shortlist_k": len(short), "shortlist_ids": sorted(keep)}
        return replace(
            res,
            ranked=list(res.ranked) + tail if not res.error else res.ranked,
            latency_ms=(time.perf_counter() - started) * 1000,
            calls=res.calls + retrieved.calls,
            extra=extra,
        )
