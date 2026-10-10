"""Stub catalog tools and Anthropic-style tool search (regex and BM25 variants).

Every catalog tool is a LangChain tool with the server's real name, description and input
schema. Calling it only records the call in a :class:`CallLog` and returns a short canned
result, so runs never touch a real service.

Tool search mirrors Anthropic's Tool Search Tool
(https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool):

* ``regex`` variant: the model writes a Python ``re.search`` pattern (case-insensitive,
  max 200 chars) matched against tool names, descriptions, argument names and argument
  descriptions.
* ``bm25`` variant: the model writes a natural-language query (max 500 chars) scored with
  the repo's BM25 over the same fields.
* Both return up to 5 tool references by default; the model may pass ``limit``. The
  referenced tools are then *loaded*: :class:`~tooldiscoverybench.harness.middleware.
  DeferredToolsMiddleware` adds their full definitions to the next model call, the way the
  API expands ``tool_reference`` blocks. A search that matches nothing returns an empty list;
  an invalid regex returns an ``invalid_tool_input`` error.
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from typing import Any

from langchain_core.tools import BaseTool, StructuredTool

from tooldiscoverybench.core.models import Tool
from tooldiscoverybench.routers.base import safe_tool_name
from tooldiscoverybench.routers.baselines.bm25 import bm25_rank

SEARCH_TOOL = "tool_search"
DEFAULT_LIMIT = 5
MAX_REGEX_CHARS = 200
MAX_QUERY_CHARS = 500
STUB_RESULT = (
    "[stub] {tool_id} executed. This benchmark does not run real tools; assume the call "
    "succeeded and returned the information requested. Give your final answer now."
)


@dataclass
class ToolCall:
    tool_id: str  # canonical ``server.tool``; ``tool_search`` for searches
    via: str  # "direct" (catalog tool) or "search"
    args: dict[str, Any]
    t: float = field(default_factory=time.perf_counter)


@dataclass
class CallLog:
    """Every catalog-tool execution and every search during one agent run, in order."""

    calls: list[ToolCall] = field(default_factory=list)
    searches: list[dict[str, Any]] = field(default_factory=list)

    def real_calls(self) -> list[ToolCall]:
        return [c for c in self.calls if c.via != "search"]


def object_schema(tool: Tool) -> dict[str, Any]:
    schema = dict(tool.input_schema or {})
    if schema.get("type") != "object":
        schema = {"type": "object", "properties": {}}
    schema.pop("$schema", None)
    schema.setdefault("properties", {})
    return schema


def searchable_fields(tool: Tool) -> list[str]:
    """Name, description, argument names and argument descriptions (Anthropic's fields)."""
    fields = [safe_tool_name(tool.id), tool.description or ""]
    for arg, spec in (object_schema(tool).get("properties") or {}).items():
        fields.append(str(arg))
        if isinstance(spec, dict) and spec.get("description"):
            fields.append(str(spec["description"]))
    return fields


def _search_text(tool: Tool, _server_desc: dict[str, str]) -> str:
    return " ".join(searchable_fields(tool))


class Catalog:
    """The tool catalog an agent run can see, with id <-> provider-safe-name lookup."""

    def __init__(self, tools: list[Tool], server_desc: dict[str, str]) -> None:
        self.tools = tools
        self.server_desc = server_desc
        self.by_id = {t.id: t for t in tools}
        self.by_name = {safe_tool_name(t.id): t for t in tools}
        self.names = list(self.by_name)

    def resolve(self, name: str) -> Tool | None:
        """Accept the safe name (``deepwiki__ask_wiki_question``) or the id."""
        name = (name or "").strip()
        return self.by_name.get(name) or self.by_id.get(name)

    # ------------------------------------------------------------------ stubs
    def stub(self, tool: Tool, log: CallLog) -> BaseTool:
        def run(**kwargs: Any) -> str:
            log.calls.append(ToolCall(tool.id, "direct", kwargs))
            return STUB_RESULT.format(tool_id=tool.id)

        return StructuredTool.from_function(
            func=run,
            name=safe_tool_name(tool.id),
            description=f"[{tool.server}] {tool.description or tool.name}",
            args_schema=object_schema(tool),
            infer_schema=False,
        )

    def stubs(self, log: CallLog) -> list[BaseTool]:
        return [self.stub(t, log) for t in self.tools]

    # ----------------------------------------------------------------- search
    def regex_search(self, pattern: str, limit: int = DEFAULT_LIMIT) -> list[str]:
        """Tool names whose searchable fields match ``pattern`` (re.search, IGNORECASE).

        Ordered by how many fields match (name matches first), then catalog order.
        """
        if len(pattern) > MAX_REGEX_CHARS:
            raise ValueError(f"pattern longer than {MAX_REGEX_CHARS} characters")
        rx = re.compile(pattern, re.IGNORECASE)
        scored = []
        for i, tool in enumerate(self.tools):
            fields = searchable_fields(tool)
            hits = [bool(rx.search(f)) for f in fields]
            if any(hits):
                scored.append((-(2 * hits[0] + sum(hits)), i, safe_tool_name(tool.id)))
        return [name for *_, name in sorted(scored)[:limit]]

    def bm25_search(self, query: str, limit: int = DEFAULT_LIMIT) -> list[str]:
        """Tool names ranked by BM25 over the same fields; zero-score tools are dropped."""
        ranked = bm25_rank(
            query[:MAX_QUERY_CHARS], self.tools, self.server_desc, text_fn=_search_text
        )
        return [safe_tool_name(tid) for tid, score in ranked if score > 0][:limit]

    def search_tool(self, variant: str, log: CallLog) -> BaseTool:
        """The ``tool_search`` tool for ``variant`` (``regex`` or ``bm25``)."""

        def record(arg: str, names: list[str], error: str | None = None) -> str:
            log.calls.append(ToolCall(SEARCH_TOOL, "search", {"variant": variant, "input": arg}))
            ids = [self.by_name[n].id for n in names]
            log.searches.append({"variant": variant, "input": arg, "hits": ids, "error": error})
            if error:
                return json.dumps(
                    {
                        "type": "tool_search_tool_result_error",
                        "error_code": "invalid_tool_input",
                        "error_message": error,
                    }
                )
            return json.dumps(
                {
                    "type": "tool_search_tool_search_result",
                    "tool_references": [{"type": "tool_reference", "tool_name": n} for n in names],
                    "note": (
                        "Referenced tools are now loaded; call them directly by name."
                        if names
                        else "No tools matched."
                    ),
                }
            )

        def clamp(limit: int | None) -> int:
            return max(1, min(int(limit or DEFAULT_LIMIT), len(self.tools)))

        if variant == "regex":

            def tool_search(pattern: str, limit: int | None = None) -> str:
                try:
                    names = self.regex_search(pattern, clamp(limit))
                except (re.error, ValueError) as exc:
                    return record(pattern, [], f"Invalid regular expression pattern: {exc}")
                return record(pattern, names)

            description = (
                "Search for deferred tools (documentation services, code search, Hugging Face "
                "Hub, flight search, ...) with a Python regex `pattern` (re.search, "
                f"case-insensitive, max {MAX_REGEX_CHARS} chars) matched against tool names, "
                "descriptions, argument names and argument descriptions, e.g. 'weather', "
                "'get_.*_data', 'database.*query|query.*database'. Returns up to "
                f"{DEFAULT_LIMIT} tool references (set `limit` for more); the referenced tools "
                "are then loaded and can be called directly. You may search again."
            )
        elif variant == "bm25":

            def tool_search(query: str, limit: int | None = None) -> str:  # type: ignore[misc]
                return record(query, self.bm25_search(query, clamp(limit)))

            description = (
                "Search for deferred tools (documentation services, code search, Hugging Face "
                "Hub, flight search, ...) with a natural-language `query` (max "
                f"{MAX_QUERY_CHARS} chars) describing the capability you need. Matches tool "
                f"names, descriptions and argument names/descriptions. Returns up to "
                f"{DEFAULT_LIMIT} tool references (set `limit` for more); the referenced tools "
                "are then loaded and can be called directly. You may search again."
            )
        else:
            raise ValueError(f"unknown search variant {variant!r}")
        return StructuredTool.from_function(
            func=tool_search, name=SEARCH_TOOL, description=description
        )


def referenced_tools(content: Any) -> list[str]:
    """Tool names referenced by one ``tool_search`` result message."""
    try:
        data = json.loads(content if isinstance(content, str) else json.dumps(content))
    except (json.JSONDecodeError, TypeError):
        return []
    refs = data.get("tool_references", []) if isinstance(data, dict) else []
    return [r["tool_name"] for r in refs if isinstance(r, dict) and "tool_name" in r]
