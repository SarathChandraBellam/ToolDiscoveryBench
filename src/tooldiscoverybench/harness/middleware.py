"""Agent middleware for tool discovery, on LangChain v1's ``AgentMiddleware`` interface.

Both classes use the hook LangChain's own ``LLMToolSelectorMiddleware`` uses:
``wrap_model_call`` + ``request.override(tools=...)``. Every catalog tool stays registered
with the agent (so the tool node can execute it), but only *loaded* tools are sent to the
model on each call.

``DeferredToolsMiddleware``  Anthropic-style deferred loading: catalog tools start
                             unloaded (or with an initial set) and a tool becomes loaded
                             once a ``tool_search`` result references it, like the API
                             expanding ``tool_reference`` blocks.
``ToolRouterMiddleware``     The one-upfront-pick pattern: before the FIRST model call of a
                             run, a pluggable router (BM25 shortlist, free-model router,
                             Jev) picks k tools; those are loaded for the whole run. Unlike
                             ``LLMToolSelectorMiddleware``, which re-selects before EVERY
                             model call, the pick happens once per run. ``tool_search`` stays
                             available as the fallback.

A middleware instance holds per-run state: build one per agent run (the harness does).
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any, Protocol

from langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse
from langchain_core.messages import HumanMessage, ToolMessage

from tooldiscoverybench.core.models import Tool
from tooldiscoverybench.harness.routing import RouterPick
from tooldiscoverybench.harness.tools import SEARCH_TOOL, referenced_tools
from tooldiscoverybench.routers.base import safe_tool_name


class ToolRouter(Protocol):
    kind: str
    model_id: str

    def pick(self, question: str, tools: list[Tool]) -> RouterPick: ...


def _tool_name(tool: Any) -> str | None:
    if isinstance(tool, dict):
        return tool.get("name") or (tool.get("function") or {}).get("name")
    return getattr(tool, "name", None)


def _first_user_text(messages: Iterable[Any]) -> str:
    for msg in messages:
        if isinstance(msg, HumanMessage):
            return msg.content if isinstance(msg.content, str) else str(msg.content)
    return ""


class DeferredToolsMiddleware(AgentMiddleware):  # type: ignore[type-arg]
    """Hide deferred catalog tools from the model until discovered by ``tool_search``."""

    def __init__(self, deferred: Iterable[str], initially_loaded: Iterable[str] = ()) -> None:
        super().__init__()
        self.deferred = set(deferred)
        self.loaded: list[str] = [n for n in initially_loaded if n in self.deferred]
        self.load_events: list[dict[str, Any]] = []
        self.rejected: list[str] = []  # calls to deferred tools that were never loaded

    def _discover(self, messages: Iterable[Any]) -> None:
        for msg in messages:
            if isinstance(msg, ToolMessage) and msg.name == SEARCH_TOOL:
                for name in referenced_tools(msg.content):
                    if name in self.deferred and name not in self.loaded:
                        self.loaded.append(name)
                        self.load_events.append({"tool": name, "via": SEARCH_TOOL})

    def _filter(self, request: ModelRequest) -> ModelRequest:  # type: ignore[type-arg]
        self._discover(request.messages)
        visible = set(self.loaded)
        tools = [
            t
            for t in request.tools
            if _tool_name(t) not in self.deferred or _tool_name(t) in visible
        ]
        return request.override(tools=tools)

    def wrap_tool_call(
        self,
        request: Any,
        handler: Callable[[Any], Any],
    ) -> Any:
        """Refuse calls to deferred tools that were never loaded (as the API would)."""
        name = (request.tool_call or {}).get("name", "")
        if name in self.deferred and name not in self.loaded:
            self.rejected.append(name)
            return ToolMessage(
                f"Error: tool {name!r} is not loaded. Use {SEARCH_TOOL} to load it first.",
                tool_call_id=request.tool_call.get("id", ""),
                name=name,
                status="error",
            )
        return handler(request)

    def wrap_model_call(
        self,
        request: ModelRequest,  # type: ignore[type-arg]
        handler: Callable[[ModelRequest], ModelResponse],  # type: ignore[type-arg]
    ) -> Any:
        return handler(self._filter(request))


class ToolRouterMiddleware(DeferredToolsMiddleware):
    """Pick k tools ONCE before the first model call with a pluggable router."""

    def __init__(self, router: ToolRouter, catalog_tools: list[Tool]) -> None:
        super().__init__([safe_tool_name(t.id) for t in catalog_tools])
        self.router = router
        self.catalog_tools = catalog_tools
        self.pick: RouterPick | None = None

    def _filter(self, request: ModelRequest) -> ModelRequest:  # type: ignore[type-arg]
        if self.pick is None:
            self.pick = self.router.pick(_first_user_text(request.messages), self.catalog_tools)
            for tid in self.pick.tool_ids:
                name = safe_tool_name(tid)
                if name in self.deferred and name not in self.loaded:
                    self.loaded.append(name)
                    self.load_events.append({"tool": name, "via": "router"})
        return super()._filter(request)
