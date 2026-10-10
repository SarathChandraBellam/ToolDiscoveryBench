"""Decision-model router, shared by every backend that answers typed ``choice`` questions
with probabilities (TypeSafe Jev, OpenAI Decisions API, ...).

A ``choice`` over tool ids yields a ranked, probability-weighted distribution.

Modes
-----
``flat``          One ``choice`` over every tool. Above the 255-option limit the
                  catalog is split into chunks and run as a tournament.
``factored``      ONE request with a "which server?" question plus a "which tool on
                  server S?" question per server, combined as P(server) * P(tool | server).
``hierarchical``  Two sequential calls: pick server(s), then a tool among the top-m
                  servers' tools.

Abstention (``allow_abstain``, default on): a ``NONE`` option ("no listed tool can handle
this") is added to the top-level question. When it wins, the router abstains. Its
probability is reported as ``raw["p_none"]``. NONE is compared only against options of the
same question: the best tool in ``flat`` mode, the best server in ``factored`` and
``hierarchical`` mode (a joint P(server) * P(tool | server) is not on the same scale).
"""

from __future__ import annotations

import asyncio
import contextvars
import re
import time
from collections import defaultdict
from typing import Any

from tooldiscoverybench.catalog.option_text import OptionTextBuilder
from tooldiscoverybench.core.models import RouteResult, Tool
from tooldiscoverybench.routers.base import Ranked, Router
from tooldiscoverybench.routers.decisions.types import (
    ChoiceQuestion,
    DecisionClient,
    DecisionError,
    DecisionResponse,
)

# provider-reported USD cost of every request made while routing one question
_COSTS: contextvars.ContextVar[list[float] | None] = contextvars.ContextVar("costs", default=None)

DEFAULT_INSTRUCTIONS = (
    "The state is a user's request to an AI agent. Pick the tool the agent should call FIRST "
    "to make progress on this request. Prefer the tool whose described purpose matches the "
    "request most specifically."
)
NONE = "__none__"
NONE_TOOL_TEXT = (
    "None of the listed tools can handle this request: it needs an action, account or "
    "service that no listed tool provides."
)
NONE_SERVER_TEXT = "None of these servers can handle this request."

# Per-server sub-question in factored mode. "Assume the agent will use server S" made some
# backends (GPT-6 Luna) refuse when nothing on S fits; asking for the closest tool does not.
FACTORED_TOOL_HINT = (
    " Suppose the agent is restricted to the '{server}' server's tools; pick the closest one "
    "even if none fits well."
)
_TOOL_Q = re.compile(r"\btool_\d+\b")

SERVER_INSTRUCTIONS = (
    "The state is a user's request to an AI agent. Pick the tool server (integration) the "
    "agent should use first for this request."
)

# (ranked, input_tokens, upstream_calls, raw, p_none, p_rival)
# p_rival is the best non-NONE option of the question NONE was asked in, so the abstain
# decision compares probabilities on the same scale.
_ModeResult = tuple[Ranked, int, int, dict[str, Any] | None, float, float]


def _sorted(probs: dict[str, float]) -> Ranked:
    return sorted(probs.items(), key=lambda kv: -kv[1])


def _split_none(probs: dict[str, float]) -> tuple[dict[str, float], float]:
    rest = dict(probs)
    return rest, rest.pop(NONE, 0.0)


def _best(probs: dict[str, float]) -> float:
    return max(probs.values(), default=0.0)


class DecisionRouter(Router):
    """Modes and abstention on top of any ``DecisionClient``. Subclasses build the client."""

    calibrated = True

    def __init__(self, **cfg: Any) -> None:
        super().__init__(**cfg)
        self.mode: str = cfg.get("mode", "flat")
        self.desc_chars = int(cfg.get("desc_chars", 240))
        self.instructions: str = cfg.get("instructions", DEFAULT_INSTRUCTIONS)
        self.top_servers = int(cfg.get("top_servers", 2))
        self.chunk_keep = int(cfg.get("chunk_keep", 5))
        self.allow_abstain = bool(cfg.get("allow_abstain", True))
        # how each tool option is described: plain (upstream description) or rich (hints)
        self.option_text = OptionTextBuilder(
            mode=cfg.get("option_text", "plain"),
            desc_chars=self.desc_chars,
            hints_path=cfg.get("option_hints"),
        )
        self.client: DecisionClient = self.build_client(cfg)

    def build_client(self, cfg: dict[str, Any]) -> DecisionClient:
        raise NotImplementedError

    async def _ask(self, state: str, questions: dict[str, ChoiceQuestion]) -> DecisionResponse:
        resp = await self.client.ask(state, questions)
        costs = _COSTS.get()
        if costs is not None and resp.cost_usd is not None:
            costs.append(resp.cost_usd)
        return resp

    def unavailable_reason(self) -> str | None:
        return None if self.client.configured else f"{self.client.api_key_env} not set"

    async def aclose(self) -> None:
        await self.client.aclose()

    # ----------------------------------------------------------------- criteria
    def _tool_question(
        self, tools: list[Tool], extra: str = "", with_none: bool = False
    ) -> ChoiceQuestion:
        criteria = {t.id: self.option_text(t) for t in tools}
        if with_none:
            criteria[NONE] = NONE_TOOL_TEXT
        return ChoiceQuestion(f"{self.instructions}{extra}", criteria)

    @staticmethod
    def _server_question(
        tools: list[Tool], server_desc: dict[str, str], with_none: bool = False
    ) -> ChoiceQuestion:
        by_server: dict[str, list[str]] = defaultdict(list)
        for t in tools:
            by_server[t.server].append(t.name)
        criteria = {
            s: f"{server_desc.get(s, '')} Tools: {', '.join(names[:12])}".strip()
            for s, names in by_server.items()
        }
        if with_none:
            criteria[NONE] = NONE_SERVER_TEXT
        return ChoiceQuestion(SERVER_INSTRUCTIONS, criteria)

    # -------------------------------------------------------------------- route
    async def route(
        self, question: str, tools: list[Tool], server_desc: dict[str, str]
    ) -> RouteResult:
        started = time.perf_counter()
        costs: list[float] = []
        _COSTS.set(costs)
        try:
            if self.mode == "flat":
                ranked, tokens, calls, raw, p_none, p_rival = await self._flat(question, tools)
            elif self.mode == "factored":
                ranked, tokens, calls, raw, p_none, p_rival = await self._factored(
                    question, tools, server_desc
                )
            elif self.mode == "hierarchical":
                ranked, tokens, calls, raw, p_none, p_rival = await self._hierarchical(
                    question, tools, server_desc
                )
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
            raw={**(raw or {}), "p_none": p_none},
            cost_usd=sum(costs) if costs else None,
            abstained=self.allow_abstain and p_none > p_rival,
        )

    async def _flat(self, q: str, tools: list[Tool]) -> _ModeResult:
        abstain = self.allow_abstain
        if len(tools) + abstain <= self.client.max_options:
            resp = await self._ask(q, {"tool": self._tool_question(tools, with_none=abstain)})
            probs, p_none = _split_none(resp.probabilities("tool"))
            return _sorted(probs), resp.input_tokens, 1, None, p_none, _best(probs)

        chunks = [
            tools[i : i + self.client.max_options]
            for i in range(0, len(tools), self.client.max_options)
        ]
        rounds = await asyncio.gather(
            *[self._ask(q, {"tool": self._tool_question(c)}) for c in chunks]
        )
        survivors: set[str] = set()
        for resp in rounds:
            survivors.update(
                tid for tid, _ in _sorted(resp.probabilities("tool"))[: self.chunk_keep]
            )
        finalists = [t for t in tools if t.id in survivors]
        final = await self._ask(q, {"tool": self._tool_question(finalists, with_none=abstain)})
        tokens = sum(r.input_tokens for r in rounds) + final.input_tokens
        probs, p_none = _split_none(final.probabilities("tool"))
        return _sorted(probs), tokens, len(chunks) + 1, None, p_none, _best(probs)

    async def _factored(
        self, q: str, tools: list[Tool], server_desc: dict[str, str]
    ) -> _ModeResult:
        by_server: dict[str, list[Tool]] = defaultdict(list)
        for t in tools:
            by_server[t.server].append(t)

        abstain = self.allow_abstain
        questions: dict[str, ChoiceQuestion] = {}
        if len(by_server) > 1 or abstain:
            questions["server"] = self._server_question(tools, server_desc, with_none=abstain)
        qname_for: dict[str, str] = {}
        for i, (server, server_tools) in enumerate(by_server.items()):
            if len(server_tools) > 1:
                qname_for[server] = f"tool_{i}"
                questions[f"tool_{i}"] = self._tool_question(
                    server_tools[: self.client.max_options],
                    FACTORED_TOOL_HINT.format(server=server),
                )

        resp, refused = await self._ask_dropping_refusals(q, questions)
        p_server, p_none = (
            _split_none(resp.probabilities("server"))
            if "server" in questions
            else ({next(iter(by_server)): 1.0}, 0.0)
        )
        joint: dict[str, float] = {}
        for server, server_tools in by_server.items():
            ps = p_server.get(server, 0.0)
            if server in qname_for:
                # a refused sub-question means P(tool | server) = 0 for that server's tools
                pt = {} if qname_for[server] in refused else resp.probabilities(qname_for[server])
                for t in server_tools:
                    joint[t.id] = ps * pt.get(t.id, 0.0)
            else:
                joint[server_tools[0].id] = ps
        raw: dict[str, Any] = {"server": resp.answers.get("server")}
        if refused:
            raw["refused"] = sorted(refused)
        return _sorted(joint), resp.input_tokens, 1, raw, p_none, _best(p_server)

    async def _ask_dropping_refusals(
        self, q: str, questions: dict[str, ChoiceQuestion]
    ) -> tuple[DecisionResponse, set[str]]:
        """Ask; when the backend refuses a per-server ``tool_N`` sub-question (which fails the
        whole request), drop that sub-question and ask again. Other errors propagate."""
        pending = dict(questions)
        refused: set[str] = set()
        while True:
            try:
                return await self._ask(q, pending), refused
            except DecisionError as exc:
                names = {n for n in _TOOL_Q.findall(str(exc)) if n in pending}
                if not names or "refus" not in str(exc).lower():
                    raise
                refused |= names
                for name in names:
                    pending.pop(name)
                if not pending:
                    raise

    async def _hierarchical(
        self, q: str, tools: list[Tool], server_desc: dict[str, str]
    ) -> _ModeResult:
        server_q = self._server_question(tools, server_desc, with_none=self.allow_abstain)
        tokens, calls, p_none = 0, 0, 0.0
        if len(server_q.criteria) > 1:
            resp = await self._ask(q, {"server": server_q})
            tokens, calls = resp.input_tokens, 1
            p_server, p_none = _split_none(resp.probabilities("server"))
        else:
            p_server = {next(iter(server_q.criteria)): 1.0}

        top = {s for s, _ in _sorted(p_server)[: self.top_servers]}
        candidates = [t for t in tools if t.server in top]
        p_rival = _best(p_server)
        if len(candidates) == 1:
            only = candidates[0]
            ranked = [(only.id, p_server.get(only.server, 1.0))]
        else:
            resp = await self._ask(q, {"tool": self._tool_question(candidates)})
            ranked = _sorted(resp.probabilities("tool"))
            tokens, calls = tokens + resp.input_tokens, calls + 1
        seen = {tid for tid, _ in ranked}
        # tools on pruned servers stay listed at p=0 so recall@k is defined
        ranked += [(t.id, 0.0) for t in tools if t.id not in seen]
        return ranked, tokens, calls, {"server": p_server}, p_none, p_rival
