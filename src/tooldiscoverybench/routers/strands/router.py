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
    "single most appropriate tool FIRST. Do not answer from your own knowledge. If none of the "
    "tools can handle the request (it needs an action, account or service they don't provide), "
    "call no tool and reply exactly NO_TOOL."
)
STRUCTURED_SYSTEM = (
    "You route user requests to tools. Available tools (id: description):\n{catalog}\n\n"
    "Return the id of the tool an agent should call FIRST, up to 4 alternative ids in order "
    "of preference, and your confidence (0-1) that the first choice is correct. Only use ids "
    'from the list. If none of the tools can handle the request, return tool_id "none".'
)

_ModeResult = tuple[Ranked, dict[str, Any], dict[str, Any]]


def _price(value: Any) -> float | None:
    return None if value in (None, "") else float(value)


class StrandsRouter(Router):
    calibrated = False

    def __init__(self, **cfg: Any) -> None:
        super().__init__(**cfg)
        self.mode: str = cfg.get("mode", "native")
        self.desc_chars = int(cfg.get("desc_chars", 1024))
        # optional token prices (USD per 1M) so LLM rows carry an input + output cost
        self.price_in = _price(cfg.get("price_input_per_m"))
        self.price_out = _price(cfg.get("price_output_per_m"))
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
        in_tok, out_tok = usage.get("inputTokens"), usage.get("outputTokens")
        return RouteResult(
            ranked,
            (time.perf_counter() - started) * 1000,
            False,
            input_tokens=in_tok,
            output_tokens=out_tok,
            calls=1,
            raw=raw,
            abstained=bool(raw.get("abstained")),
            cost_usd=self._cost(in_tok, out_tok),
        )

    def _cost(self, in_tok: int | None, out_tok: int | None) -> float | None:
        if self.price_in is None and self.price_out is None:
            return None
        return (
            (in_tok or 0) * (self.price_in or 0.0) + (out_tok or 0) * (self.price_out or 0.0)
        ) / 1e6

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
        # Only an explicit NO_TOOL reply is an abstention. A call to an unknown tool name, or a
        # reply with neither a tool call nor NO_TOOL, is a miss, not an abstention.
        said_no_tool = "NO_TOOL" in str(result)
        abstained = not picked and said_no_tool
        raw = {"picked": picked, "abstained": abstained}
        if picked and not ranked:
            raw["unknown_tool"] = True
        return ranked, usage, raw

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
        abstained = pick.tool_id.strip().lower() in ("none", "null", "")
        ranked: Ranked = []
        seen: set[str] = set()
        if not abstained and pick.tool_id not in valid:
            # keep an invalid first pick as the (wrong) top-1 instead of silently promoting
            # the first alternative
            ranked.append((pick.tool_id, pick.confidence))
            seen.add(pick.tool_id)
        for i, tool_id in enumerate([pick.tool_id, *pick.alternatives]):
            if tool_id in valid and tool_id not in seen:
                seen.add(tool_id)
                score = pick.confidence if i == 0 else (1 - pick.confidence) / (i + 1)
                ranked.append((tool_id, score))
        usage = dict(getattr(result.metrics, "accumulated_usage", {}) or {})
        return ranked, usage, {"pick": pick.model_dump(), "abstained": abstained}
