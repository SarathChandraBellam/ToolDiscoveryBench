"""Agent middleware for tool discovery, on LangChain v1's ``AgentMiddleware`` interface.

Both classes narrow the tools sent to the model the way LangChain's own
``LLMToolSelectorMiddleware`` does (``wrap_model_call`` + ``request.override(tools=...)``).
Every catalog tool stays registered with the agent (so the tool node can execute it), but
only *loaded* tools are sent to the model on each call.

``DeferredToolsMiddleware``  Anthropic-style deferred loading: a catalog tool becomes loaded
                             once a ``tool_search`` result references it, like the API
                             expanding ``tool_reference`` blocks. The loaded set is derived
                             from the message history, so it is per-thread and survives a
                             checkpointer.
``ToolRouterMiddleware``     Routing as part of the agent. A pluggable router (BM25
                             shortlist, free-model router, Jev) picks k tools

                             * before the first model call after every NEW user message
                               (``before_model``; the router sees the new message plus a
                               short summary of the recent conversation), and
                             * mid-task whenever the agent calls ``request_tools(need)``
                               (optional).

                             ``tool_search`` can stay as the last-resort fallback. Routing
                             state (last routed message, picks of the turn, tools carried
                             over, one event per router call) lives in the agent graph state
                             (``state_schema``), not on the instance. Unlike
                             ``LLMToolSelectorMiddleware`` it does not re-select before every
                             model call and it accepts any router, not only a chat model.

Tools loaded in earlier turns (``carry``):

``"cap"`` (default)  keep the ``carry_cap`` most recently loaded tools (default 5), then add
                     the new picks. Follow-ups that reuse a tool need no new routing and
                     the loaded set cannot grow without bound.
``"keep"``           keep everything ever loaded on the thread.
``"replace"``        drop everything; only the new turn's picks are loaded.
"""

from __future__ import annotations

import asyncio
import json
import operator
from collections.abc import Awaitable, Callable, Iterable
from typing import Annotated, Any, Literal, NotRequired, Protocol

from langchain.agents.middleware import AgentMiddleware, AgentState, ModelRequest, ModelResponse
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.tools import BaseTool, StructuredTool
from langgraph.types import Command

from tooldiscoverybench.core.models import Tool
from tooldiscoverybench.harness.routing import RouterPick
from tooldiscoverybench.harness.tools import REQUEST_TOOL, SEARCH_TOOL, referenced_tools
from tooldiscoverybench.routers.base import safe_tool_name


class ToolRouter(Protocol):
    kind: str
    model_id: str

    def pick(self, question: str, tools: list[Tool]) -> RouterPick: ...


def _tool_name(tool: Any) -> str | None:
    if isinstance(tool, dict):
        return tool.get("name") or (tool.get("function") or {}).get("name")
    return getattr(tool, "name", None)


def _text(msg: Any) -> str:
    return msg.content if isinstance(msg.content, str) else str(msg.content)


def discovered(messages: Iterable[Any], deferred: set[str]) -> list[str]:
    """Deferred tools referenced by ``tool_search`` / ``request_tools`` results, in order."""
    out: list[str] = []
    for msg in messages:
        if isinstance(msg, ToolMessage) and msg.name in {SEARCH_TOOL, REQUEST_TOOL}:
            for name in referenced_tools(msg.content):
                if name in deferred and name not in out:
                    out.append(name)
    return out


class DeferredToolsMiddleware(AgentMiddleware):  # type: ignore[type-arg]
    """Hide deferred catalog tools from the model until discovered by ``tool_search``."""

    def __init__(self, deferred: Iterable[str]) -> None:
        super().__init__()
        self.deferred = set(deferred)

    def loaded(self, state: Any) -> list[str]:
        """Loaded tool names for this thread: every tool a search result referenced."""
        return discovered((state or {}).get("messages", []), self.deferred)

    def _filter(self, request: ModelRequest) -> ModelRequest:  # type: ignore[type-arg]
        state = {**(request.state or {}), "messages": request.messages}
        visible = set(self.loaded(state))
        tools = [
            t
            for t in request.tools
            if _tool_name(t) not in self.deferred or _tool_name(t) in visible
        ]
        return request.override(tools=tools)

    def _refusal(self, request: Any) -> ToolMessage | None:
        """Refuse calls to deferred tools that are not loaded (as the API would)."""
        name = (request.tool_call or {}).get("name", "")
        if name in self.deferred and name not in self.loaded(request.state):
            return ToolMessage(
                f"Error: tool {name!r} is not loaded. Use {SEARCH_TOOL} to load it first.",
                tool_call_id=request.tool_call.get("id", ""),
                name=name,
                status="error",
            )
        return None

    def wrap_tool_call(self, request: Any, handler: Callable[[Any], Any]) -> Any:
        return self._refusal(request) or handler(request)

    async def awrap_tool_call(self, request: Any, handler: Callable[[Any], Awaitable[Any]]) -> Any:
        return self._refusal(request) or await handler(request)

    def wrap_model_call(
        self,
        request: ModelRequest,  # type: ignore[type-arg]
        handler: Callable[[ModelRequest], ModelResponse],  # type: ignore[type-arg]
    ) -> Any:
        return handler(self._filter(request))

    async def awrap_model_call(
        self,
        request: ModelRequest,  # type: ignore[type-arg]
        handler: Callable[[ModelRequest], Awaitable[ModelResponse]],  # type: ignore[type-arg]
    ) -> Any:
        return await handler(self._filter(request))


class ToolRoutingState(AgentState):  # type: ignore[type-arg]
    """Routing state kept in the agent graph state (per thread, checkpointed)."""

    tdb_routed_message: NotRequired[str]  # key of the last user message that was routed
    tdb_turn_picks: NotRequired[list[str]]  # router picks for the current turn
    tdb_carry: NotRequired[list[str]]  # tools kept from earlier turns (see ``carry``)
    tdb_router_events: NotRequired[Annotated[list[dict[str, Any]], operator.add]]


def _request_tools_stub(need: str) -> str:
    return "request_tools is handled by ToolRouterMiddleware; add it to the agent."


class ToolRouterMiddleware(DeferredToolsMiddleware):
    """Route on every new user message and on ``request_tools``; see the module docstring."""

    state_schema = ToolRoutingState  # type: ignore[assignment]

    def __init__(
        self,
        router: ToolRouter,
        catalog_tools: list[Tool],
        *,
        request_tools: bool = False,
        carry: Literal["cap", "keep", "replace"] = "cap",
        carry_cap: int = 5,
        context_turns: int = 2,
        context_chars: int = 200,
    ) -> None:
        super().__init__([safe_tool_name(t.id) for t in catalog_tools])
        if carry not in {"cap", "keep", "replace"}:
            raise ValueError(f"unknown carry policy {carry!r}")
        self.router = router
        self.catalog_tools = catalog_tools
        self.carry = carry
        self.carry_cap = carry_cap
        self.context_turns = context_turns
        self.context_chars = context_chars
        self.tools: list[BaseTool] = []
        if request_tools:
            self.tools = [
                StructuredTool.from_function(
                    func=_request_tools_stub,
                    name=REQUEST_TOOL,
                    description=(
                        "Ask the tool router for integration tools when none of the loaded "
                        "tools can do what you need. `need` is one sentence describing the "
                        "capability (e.g. 'search flights between two cities'). The router "
                        "loads its best matches; call them directly afterwards."
                    ),
                )
            ]

    # ------------------------------------------------------------------ state
    @staticmethod
    def _message_key(messages: list[Any], index: int) -> str:
        msg_id = getattr(messages[index], "id", None)
        n = sum(isinstance(m, HumanMessage) for m in messages[: index + 1])
        return str(msg_id) if msg_id else f"human#{n}"

    @staticmethod
    def _last_human(messages: list[Any]) -> int | None:
        return next(
            (i for i in range(len(messages) - 1, -1, -1) if isinstance(messages[i], HumanMessage)),
            None,
        )

    def loaded(self, state: Any) -> list[str]:
        """Carried tools, then this turn's router picks, then this turn's discoveries."""
        state = state or {}
        messages = list(state.get("messages", []))
        start = self._last_human(messages)
        turn = discovered(messages[start:] if start is not None else messages, self.deferred)
        out: list[str] = []
        for name in [*state.get("tdb_carry", []), *state.get("tdb_turn_picks", []), *turn]:
            if name not in out:
                out.append(name)
        return out

    def _carry_over(self, previously_loaded: list[str]) -> list[str]:
        if self.carry == "replace":
            return []
        if self.carry == "cap":
            return previously_loaded[-self.carry_cap :] if self.carry_cap > 0 else []
        return previously_loaded

    def route_text(self, messages: list[Any], index: int, need: str | None = None) -> str:
        """The current user message, preceded by a short summary of recent turns."""
        current = _text(messages[index])
        context: list[str] = []
        humans = [i for i in range(index) if isinstance(messages[i], HumanMessage)]
        for i in humans[-self.context_turns :]:
            called = [
                c.get("name", "")
                for m in messages[i:index]
                if isinstance(m, AIMessage)
                for c in m.tool_calls or []
                if c.get("name") in self.deferred
            ]
            line = f"- user: {_text(messages[i])[: self.context_chars]}"
            if called:
                line += f" (tools used: {', '.join(dict.fromkeys(called))})"
            context.append(line)
        text = current
        if context:
            text = "Earlier in this conversation:\n" + "\n".join(context)
            text += f"\n\nCurrent request: {current}"
        if need:
            text += f"\n\nThe agent is missing a tool for: {need}"
        return text

    def _event(self, pick: RouterPick, source: str, key: str) -> dict[str, Any]:
        return {
            "source": source,  # "user_message" or "request_tools"
            "message": key,
            "tools": [safe_tool_name(t) for t in pick.tool_ids],
            "tool_ids": list(pick.tool_ids),
            "label": pick.label,
            "model": pick.model,
            "latency_ms": round(pick.latency_ms, 1),
            "llm_calls": pick.llm_calls,
            "input_tokens": pick.input_tokens,
            "output_tokens": pick.output_tokens,
            "cost_usd": (pick.raw or {}).get("cost_usd"),
            "error": pick.error,
        }

    # ---------------------------------------------------- route on a new user message
    def _pending(self, state: Any) -> tuple[list[Any], int, str] | None:
        messages = list((state or {}).get("messages", []))
        index = self._last_human(messages)
        if index is None:
            return None
        key = self._message_key(messages, index)
        if state.get("tdb_routed_message") == key:
            return None
        return messages, index, key

    def _routed(self, state: Any, pending: tuple[list[Any], int, str], pick: RouterPick) -> Any:
        messages, index, key = pending
        before = {**state, "messages": messages[:index]}
        names = [n for n in (safe_tool_name(t) for t in pick.tool_ids) if n in self.deferred]
        return {
            "tdb_routed_message": key,
            "tdb_carry": self._carry_over(self.loaded(before)),
            "tdb_turn_picks": names,
            "tdb_router_events": [self._event(pick, "user_message", key)],
        }

    def before_model(self, state: Any, runtime: Any) -> dict[str, Any] | None:
        pending = self._pending(state)
        if pending is None:
            return None
        pick = self.router.pick(self.route_text(pending[0], pending[1]), self.catalog_tools)
        return self._routed(state, pending, pick)  # type: ignore[no-any-return]

    async def abefore_model(self, state: Any, runtime: Any) -> dict[str, Any] | None:
        pending = self._pending(state)
        if pending is None:
            return None
        text = self.route_text(pending[0], pending[1])
        pick = await asyncio.to_thread(self.router.pick, text, self.catalog_tools)
        return self._routed(state, pending, pick)  # type: ignore[no-any-return]

    # -------------------------------------------------------- route on request_tools
    def _request_text(self, request: Any) -> tuple[str, str]:
        messages = list((request.state or {}).get("messages", []))
        index = self._last_human(messages)
        need = str((request.tool_call.get("args") or {}).get("need", ""))
        if index is None:
            return need, "human#0"
        return self.route_text(messages, index, need), self._message_key(messages, index)

    def _requested(self, request: Any, key: str, pick: RouterPick) -> Command[Any]:
        names = [n for n in (safe_tool_name(t) for t in pick.tool_ids) if n in self.deferred]
        content = json.dumps(
            {
                "type": "tool_search_tool_search_result",
                "tool_references": [{"type": "tool_reference", "tool_name": n} for n in names],
                "note": (
                    "Referenced tools are now loaded; call them directly by name."
                    if names
                    else "The router found no matching tool."
                ),
            }
        )
        message = ToolMessage(
            content, tool_call_id=request.tool_call.get("id", ""), name=REQUEST_TOOL
        )
        return Command(
            update={
                "messages": [message],
                "tdb_router_events": [self._event(pick, "request_tools", key)],
            }
        )

    def wrap_tool_call(self, request: Any, handler: Callable[[Any], Any]) -> Any:
        if (request.tool_call or {}).get("name") == REQUEST_TOOL and self.tools:
            text, key = self._request_text(request)
            return self._requested(request, key, self.router.pick(text, self.catalog_tools))
        return super().wrap_tool_call(request, handler)

    async def awrap_tool_call(self, request: Any, handler: Callable[[Any], Awaitable[Any]]) -> Any:
        if (request.tool_call or {}).get("name") == REQUEST_TOOL and self.tools:
            text, key = self._request_text(request)
            pick = await asyncio.to_thread(self.router.pick, text, self.catalog_tools)
            return self._requested(request, key, pick)
        return await super().awrap_tool_call(request, handler)
