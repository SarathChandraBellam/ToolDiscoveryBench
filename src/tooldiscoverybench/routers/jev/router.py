"""TypeSafe Jev as a tool router.

Jev answers typed questions with calibrated probabilities instead of generated text,
so a ``choice`` over tool ids yields a ranked, calibrated distribution.

Modes
-----
``flat``          One ``choice`` over every tool. Above the 255-option limit the
                  catalog is split into chunks and run as a tournament.
``factored``      ONE request with a "which server?" question plus a "which tool on
                  server S?" question per server, combined as P(server) * P(tool | server).
``hierarchical``  Two sequential calls: pick server(s), then a tool among the top-m
                  servers' tools.
"""

from __future__ import annotations

import asyncio
import time
from collections import defaultdict
from typing import Any

from tooldiscoverybench.core.models import RouteResult, Tool
from tooldiscoverybench.routers.base import Ranked, Router
from tooldiscoverybench.routers.jev.client import (
    MAX_CHOICE_OPTIONS,
    ChoiceQuestion,
    JevClient,
)

DEFAULT_INSTRUCTIONS = (
    "The state is a user's request to an AI agent. Pick the tool the agent should call FIRST "
    "to make progress on this request. Prefer the tool whose described purpose matches the "
    "request most specifically."
)
SERVER_INSTRUCTIONS = (
    "The state is a user's request to an AI agent. Pick the tool server (integration) the "
    "agent should use first for this request."
)

# (ranked, input_tokens, upstream_calls, raw)
_ModeResult = tuple[Ranked, int, int, dict[str, Any] | None]


def _sorted(probs: dict[str, float]) -> Ranked:
    return sorted(probs.items(), key=lambda kv: -kv[1])


class JevRouter(Router):
    calibrated = True

    def __init__(self, **cfg: Any) -> None:
        super().__init__(**cfg)
        self.mode: str = cfg.get("mode", "flat")
        self.desc_chars = int(cfg.get("desc_chars", 240))
        self.instructions: str = cfg.get("instructions", DEFAULT_INSTRUCTIONS)
        self.top_servers = int(cfg.get("top_servers", 2))
        self.chunk_keep = int(cfg.get("chunk_keep", 5))
        self.client = JevClient(
            dialect=cfg.get("dialect", "typesafe"),
            model=cfg.get("model", "jev-latest"),
            base_url=cfg.get("base_url"),
            path=cfg.get("path"),
            question_type_key=cfg.get("question_type_key"),
            api_key=cfg.get("api_key"),
            api_key_env=cfg.get("api_key_env", "TYPESAFE_API_KEY"),
            timeout=float(cfg.get("timeout", 30)),
            max_retries=int(cfg.get("max_retries", 3)),
            transport=cfg.get("_transport"),
        )

    def unavailable_reason(self) -> str | None:
        return None if self.client.configured else f"{self.client.api_key_env} not set"

    async def aclose(self) -> None:
        await self.client.aclose()

    # ----------------------------------------------------------------- criteria
    def _tool_question(self, tools: list[Tool], extra: str = "") -> ChoiceQuestion:
        criteria = {t.id: f"[{t.server}] {t.name}: {t.short_desc(self.desc_chars)}" for t in tools}
        return ChoiceQuestion(f"{self.instructions}{extra}", criteria)

    @staticmethod
    def _server_question(tools: list[Tool], server_desc: dict[str, str]) -> ChoiceQuestion:
        by_server: dict[str, list[str]] = defaultdict(list)
        for t in tools:
            by_server[t.server].append(t.name)
        criteria = {
            s: f"{server_desc.get(s, '')} Tools: {', '.join(names[:12])}".strip()
            for s, names in by_server.items()
        }
        return ChoiceQuestion(SERVER_INSTRUCTIONS, criteria)

    # -------------------------------------------------------------------- route
    async def route(
        self, question: str, tools: list[Tool], server_desc: dict[str, str]
    ) -> RouteResult:
        started = time.perf_counter()
        try:
            if self.mode == "flat":
                ranked, tokens, calls, raw = await self._flat(question, tools)
            elif self.mode == "factored":
                ranked, tokens, calls, raw = await self._factored(question, tools, server_desc)
            elif self.mode == "hierarchical":
                ranked, tokens, calls, raw = await self._hierarchical(question, tools, server_desc)
            else:
                raise ValueError(f"unknown jev mode {self.mode!r}")
        except Exception as exc:  # noqa: BLE001 - surfaced as a scored error row
            elapsed = (time.perf_counter() - started) * 1000
            return RouteResult([], elapsed, True, error=f"{type(exc).__name__}: {exc}")
        elapsed = (time.perf_counter() - started) * 1000
        return RouteResult(
            ranked,
            elapsed,
            True,
            input_tokens=tokens,
            output_tokens=0,
            calls=calls,
            raw=raw,
        )

    async def _flat(self, q: str, tools: list[Tool]) -> _ModeResult:
        if len(tools) <= MAX_CHOICE_OPTIONS:
            resp = await self.client.ask(q, {"tool": self._tool_question(tools)})
            return _sorted(resp.probabilities("tool")), resp.input_tokens, 1, resp.answers

        chunks = [
            tools[i : i + MAX_CHOICE_OPTIONS] for i in range(0, len(tools), MAX_CHOICE_OPTIONS)
        ]
        rounds = await asyncio.gather(
            *[self.client.ask(q, {"tool": self._tool_question(c)}) for c in chunks]
        )
        survivors: set[str] = set()
        for resp in rounds:
            survivors.update(
                tid for tid, _ in _sorted(resp.probabilities("tool"))[: self.chunk_keep]
            )
        finalists = [t for t in tools if t.id in survivors]
        final = await self.client.ask(q, {"tool": self._tool_question(finalists)})
        tokens = sum(r.input_tokens for r in rounds) + final.input_tokens
        return _sorted(final.probabilities("tool")), tokens, len(chunks) + 1, None

    async def _factored(
        self, q: str, tools: list[Tool], server_desc: dict[str, str]
    ) -> _ModeResult:
        by_server: dict[str, list[Tool]] = defaultdict(list)
        for t in tools:
            by_server[t.server].append(t)

        questions: dict[str, ChoiceQuestion] = {}
        if len(by_server) > 1:
            questions["server"] = self._server_question(tools, server_desc)
        qname_for: dict[str, str] = {}
        for i, (server, server_tools) in enumerate(by_server.items()):
            if len(server_tools) > 1:
                qname_for[server] = f"tool_{i}"
                questions[f"tool_{i}"] = self._tool_question(
                    server_tools[:MAX_CHOICE_OPTIONS],
                    f" Assume the agent will use the '{server}' server.",
                )

        resp = await self.client.ask(q, questions)
        p_server = (
            resp.probabilities("server") if "server" in questions else {next(iter(by_server)): 1.0}
        )
        joint: dict[str, float] = {}
        for server, server_tools in by_server.items():
            ps = p_server.get(server, 0.0)
            if server in qname_for:
                pt = resp.probabilities(qname_for[server])
                for t in server_tools:
                    joint[t.id] = ps * pt.get(t.id, 0.0)
            else:
                joint[server_tools[0].id] = ps
        return _sorted(joint), resp.input_tokens, 1, {"server": resp.answers.get("server")}

    async def _hierarchical(
        self, q: str, tools: list[Tool], server_desc: dict[str, str]
    ) -> _ModeResult:
        server_q = self._server_question(tools, server_desc)
        tokens, calls = 0, 0
        if len(server_q.criteria) > 1:
            resp = await self.client.ask(q, {"server": server_q})
            tokens, calls = resp.input_tokens, 1
            p_server = resp.probabilities("server")
        else:
            p_server = {next(iter(server_q.criteria)): 1.0}

        top = {s for s, _ in _sorted(p_server)[: self.top_servers]}
        candidates = [t for t in tools if t.server in top]
        if len(candidates) == 1:
            only = candidates[0]
            return [(only.id, p_server.get(only.server, 1.0))], tokens, calls, {"server": p_server}

        resp = await self.client.ask(q, {"tool": self._tool_question(candidates)})
        ranked = _sorted(resp.probabilities("tool"))
        seen = {tid for tid, _ in ranked}
        # tools on pruned servers stay listed at p=0 so recall@k is defined
        ranked += [(t.id, 0.0) for t in tools if t.id not in seen]
        return ranked, tokens + resp.input_tokens, calls + 1, {"server": p_server}
