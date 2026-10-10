"""Stub catalog tools plus the ``tool_search`` / ``call_tool`` pair for deferred loading.

Every catalog tool is a LangChain tool with the server's real name, description and input
schema. Calling it only records the call in a :class:`CallLog` and returns a short canned
result, so runs are free, deterministic on the tool side and never touch a real service.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any

from langchain_core.tools import BaseTool, StructuredTool

from tooldiscoverybench.core.models import Tool
from tooldiscoverybench.routers.base import safe_tool_name
from tooldiscoverybench.routers.baselines.bm25 import bm25_rank

SEARCH_TOOL = "tool_search"
CALL_TOOL = "call_tool"
STUB_RESULT = (
    "[stub] {tool_id} executed. This benchmark does not run real tools; assume the call "
    "succeeded and returned the information requested. Give your final answer now."
)


@dataclass
class ToolCall:
    tool_id: str  # canonical ``server.tool``; ``tool_search`` for searches
    via: str  # "direct" (bound tool), "call_tool" (proxy) or "search"
    args: dict[str, Any]
    t: float = field(default_factory=time.perf_counter)


@dataclass
class CallLog:
    """Every catalog-tool execution and every search during one agent run, in order."""

    calls: list[ToolCall] = field(default_factory=list)
    searches: list[dict[str, Any]] = field(default_factory=list)

    def real_calls(self) -> list[ToolCall]:
        return [c for c in self.calls if c.via != "search"]


def _object_schema(tool: Tool) -> dict[str, Any]:
    schema = dict(tool.input_schema or {})
    if schema.get("type") != "object":
        schema = {"type": "object", "properties": {}}
    schema.pop("$schema", None)
    schema.setdefault("properties", {})
    return schema


def tool_card(tool: Tool, desc_chars: int = 600) -> dict[str, Any]:
    """What ``tool_search`` returns per hit: callable name, id, description and schema."""
    return {
        "name": safe_tool_name(tool.id),
        "id": tool.id,
        "description": tool.short_desc(desc_chars),
        "input_schema": _object_schema(tool),
    }


class Catalog:
    """The tool catalog an agent run can see, with id <-> provider-safe-name lookup."""

    def __init__(self, tools: list[Tool], server_desc: dict[str, str]) -> None:
        self.tools = tools
        self.server_desc = server_desc
        self.by_id = {t.id: t for t in tools}
        self.by_name = {safe_tool_name(t.id): t for t in tools}

    def resolve(self, name: str) -> Tool | None:
        """Accept the safe name (``deepwiki__ask_wiki_question``) or the id."""
        name = (name or "").strip()
        return self.by_name.get(name) or self.by_id.get(name)

    def id_of_tool_name(self, name: str) -> str | None:
        tool = self.by_name.get(name)
        return tool.id if tool else None

    # ------------------------------------------------------------------ stubs
    def stub(self, tool: Tool, log: CallLog) -> BaseTool:
        def run(**kwargs: Any) -> str:
            log.calls.append(ToolCall(tool.id, "direct", kwargs))
            return STUB_RESULT.format(tool_id=tool.id)

        return StructuredTool.from_function(
            func=run,
            name=safe_tool_name(tool.id),
            description=f"[{tool.server}] {tool.description or tool.name}",
            args_schema=_object_schema(tool),
            infer_schema=False,
        )

    def stubs(self, tool_ids: list[str], log: CallLog) -> list[BaseTool]:
        return [self.stub(self.by_id[tid], log) for tid in tool_ids if tid in self.by_id]

    # ------------------------------------------------------------- deferred
    def search_tools(self, log: CallLog, top_k: int = 5) -> list[BaseTool]:
        """``tool_search`` (BM25 over every catalog tool) and the ``call_tool`` proxy."""

        def tool_search(query: str) -> str:
            ranked = bm25_rank(query, self.tools, self.server_desc)[:top_k]
            hits = [tool_card(self.by_id[tid]) for tid, _ in ranked]
            log.calls.append(ToolCall(SEARCH_TOOL, "search", {"query": query}))
            log.searches.append({"query": query, "hits": [h["id"] for h in hits]})
            return json.dumps({"results": hits}, indent=1)

        def call_tool(name: str, arguments: dict[str, Any] | str | None = None) -> str:
            tool = self.resolve(name)
            if tool is None:
                return (
                    f"Error: unknown tool {name!r}. Use {SEARCH_TOOL} to find tools and pass "
                    "the exact 'name' it returns."
                )
            args = arguments
            if isinstance(args, str):
                try:
                    args = json.loads(args) if args.strip() else {}
                except json.JSONDecodeError:
                    args = {"_raw": args}
            log.calls.append(ToolCall(tool.id, CALL_TOOL, dict(args or {})))
            return STUB_RESULT.format(tool_id=tool.id)

        search = StructuredTool.from_function(
            func=tool_search,
            name=SEARCH_TOOL,
            description=(
                "Search the catalog of integration tools (documentation services, code search, "
                "Hugging Face Hub, flight search, ...) that are NOT loaded yet. Pass a short "
                f"keyword query describing the capability you need. Returns up to {top_k} "
                "matching tools with their name, description and input schema. You may search "
                "again with a different query."
            ),
        )
        call = StructuredTool.from_function(
            func=call_tool,
            name=CALL_TOOL,
            description=(
                f"Invoke a tool found with {SEARCH_TOOL}. `name` is the exact tool name from the "
                "search results; `arguments` is a JSON object matching that tool's input_schema."
            ),
        )
        return [search, call]
