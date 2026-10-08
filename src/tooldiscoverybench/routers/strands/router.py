"""Strands Agents as a tool router.

Modes
-----
``native``      Every catalog tool is registered as a stub Strands tool with its real
                MCP input schema. The model emits a tool call and we record which tool
                it picked first. This is what an agent actually does.
``structured``  The catalog goes in the system prompt and the model returns a pydantic
                object ``{tool_id, alternatives, confidence}``. Confidence is
                self-reported, not calibrated.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Callable
from typing import Any

from tooldiscoverybench.core.models import RouteResult, Tool
from tooldiscoverybench.routers.base import Ranked, Router, catalog_lines, safe_tool_name
from tooldiscoverybench.routers.strands.models import build_model, provider_unavailable_reason

NATIVE_SYSTEM = (
    "You are an agent with access to the tools provided. For the user's request, call the "
    "single most appropriate tool FIRST. Do not answer from your own knowledge; always call a tool."
)
STRUCTURED_SYSTEM = (
    "You route user requests to tools. Available tools (id: description):\n{catalog}\n\n"
    "Return the id of the tool an agent should call FIRST, up to 4 alternative ids in order "
    "of preference, and your confidence (0-1) that the first choice is correct. Only use ids "
    "from the list."
)

_ModeResult = tuple[Ranked, dict[str, Any], dict[str, Any]]


class StrandsRouter(Router):
    calibrated = False

    def __init__(self, **cfg: Any) -> None:
        super().__init__(**cfg)
        self.mode: str = cfg.get("mode", "native")
        self.desc_chars = int(cfg.get("desc_chars", 1024))
        # tests inject a fake model factory
        self._model_factory: Callable[[], Any] = cfg.get("_model_factory") or (
            lambda: build_model(cfg)
        )

    def unavailable_reason(self) -> str | None:
        if "_model_factory" in self.cfg:
            return None
        try:
            import strands  # noqa: F401
        except ImportError:
            return "strands-agents not installed (uv sync --extra strands)"
        return provider_unavailable_reason(self.cfg)

    async def route(
        self, question: str, tools: list[Tool], server_desc: dict[str, str]
    ) -> RouteResult:
        fn = self._native if self.mode == "native" else self._structured
        started = time.perf_counter()
        try:
            # Agent.__call__ is synchronous; run it off the loop so questions run concurrently
            ranked, usage, raw = await asyncio.to_thread(fn, question, tools)
        except Exception as exc:  # noqa: BLE001 - surfaced as a scored error row
            elapsed = (time.perf_counter() - started) * 1000
            return RouteResult([], elapsed, False, error=f"{type(exc).__name__}: {exc}")
        return RouteResult(
            ranked,
            (time.perf_counter() - started) * 1000,
            False,
            input_tokens=usage.get("inputTokens"),
            output_tokens=usage.get("outputTokens"),
            calls=1,
            raw=raw,
        )

    # ------------------------------------------------------------------- native
    def _native(self, question: str, tools: list[Tool]) -> _ModeResult:
        from strands import Agent
        from strands.hooks import BeforeToolCallEvent
        from strands.tools.tools import PythonAgentTool

        name_to_id: dict[str, str] = {}

        def stub(tool_use: Any, **_: Any) -> Any:
            return {
                "toolUseId": tool_use["toolUseId"],
                "status": "success",
                "content": [{"text": "ok (routing benchmark stub)"}],
            }

        stubs: list[Any] = []
        for t in tools:
            name = safe_tool_name(t.id)
            name_to_id[name] = t.id
            schema = t.input_schema if t.input_schema.get("type") == "object" else None
            spec: Any = {
                "name": name,
                "description": f"[{t.server}] {t.short_desc(self.desc_chars)}",
                "inputSchema": {"json": schema or {"type": "object", "properties": {}}},
            }
            stubs.append(PythonAgentTool(name, spec, stub))

        agent = Agent(
            model=self._model_factory(),
            tools=stubs,
            system_prompt=NATIVE_SYSTEM,
            callback_handler=None,
        )
        picked: list[str] = []

        def capture(event: BeforeToolCallEvent) -> None:
            picked.append(event.tool_use["name"])
            event.cancel_tool = "routing captured; stop here"

        agent.hooks.add_callback(BeforeToolCallEvent, capture)
        try:
            from strands.types.agent import Limits

            result = agent(question, limits=Limits(turns=1))
        except ImportError:  # older strands without turn limits
            result = agent(question)

        if not picked:  # fall back to scanning the transcript
            for message in agent.messages:
                for block in message.get("content", []):
                    if "toolUse" in block:
                        picked.append(block["toolUse"]["name"])

        ranked: Ranked = []
        seen: set[str] = set()
        for i, name in enumerate(picked):
            tool_id = name_to_id.get(name)
            if tool_id and tool_id not in seen:
                seen.add(tool_id)
                ranked.append((tool_id, 1.0 / (i + 1)))
        usage = dict(getattr(result.metrics, "accumulated_usage", {}) or {})
        return ranked, usage, {"picked": picked}

    # --------------------------------------------------------------- structured
    def _structured(self, question: str, tools: list[Tool]) -> _ModeResult:
        from pydantic import BaseModel, Field
        from strands import Agent

        class ToolPick(BaseModel):
            tool_id: str = Field(description="id of the tool to call first, exactly as listed")
            alternatives: list[str] = Field(
                default_factory=list, description="other plausible ids, best first"
            )
            confidence: float = Field(ge=0, le=1)

        system = STRUCTURED_SYSTEM.format(catalog=catalog_lines(tools, self.desc_chars))
        agent = Agent(model=self._model_factory(), system_prompt=system, callback_handler=None)
        result = agent(question, structured_output_model=ToolPick)
        pick = result.structured_output
        if not isinstance(pick, ToolPick):
            raise TypeError(f"expected ToolPick, got {type(pick).__name__}")

        valid = {t.id for t in tools}
        ranked: Ranked = []
        seen: set[str] = set()
        for i, tool_id in enumerate([pick.tool_id, *pick.alternatives]):
            if tool_id in valid and tool_id not in seen:
                seen.add(tool_id)
                score = pick.confidence if i == 0 else (1 - pick.confidence) / (i + 1)
                ranked.append((tool_id, score))
        usage = dict(getattr(result.metrics, "accumulated_usage", {}) or {})
        return ranked, usage, {"pick": pick.model_dump()}
