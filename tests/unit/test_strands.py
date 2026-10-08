"""Strands router tests with a scripted streaming model (no network, no key)."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Callable
from typing import Any

import pytest

from tooldiscoverybench.core.models import Tool
from tooldiscoverybench.routers import build_router

strands_model = pytest.importorskip("strands.models.model")

# (tool_specs, call_number) -> (tool_name or None for a text reply, tool input)
Script = Callable[[list[dict[str, Any]], int], tuple[str | None, dict[str, Any]]]


class ScriptedModel(strands_model.Model):  # type: ignore[misc]
    """Minimal Strands model that streams whatever the script decides."""

    def __init__(self, script: Script) -> None:
        self.script = script
        self.config: dict[str, Any] = {}
        self.calls = 0

    def update_config(self, **kwargs: Any) -> None:
        self.config.update(kwargs)

    def get_config(self) -> dict[str, Any]:
        return self.config

    async def structured_output(self, *args: Any, **kwargs: Any) -> Any:  # pragma: no cover
        raise NotImplementedError

    async def stream(
        self,
        messages: Any,
        tool_specs: list[dict[str, Any]] | None = None,
        system_prompt: str | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[dict[str, Any]]:
        self.calls += 1
        name, args = self.script(tool_specs or [], self.calls)
        yield {"messageStart": {"role": "assistant"}}
        if name is None:
            yield {"contentBlockDelta": {"delta": {"text": "done"}}}
            yield {"contentBlockStop": {}}
            yield {"messageStop": {"stopReason": "end_turn"}}
        else:
            tool_use = {"toolUseId": f"t{self.calls}", "name": name}
            yield {"contentBlockStart": {"start": {"toolUse": tool_use}}}
            yield {"contentBlockDelta": {"delta": {"toolUse": {"input": json.dumps(args)}}}}
            yield {"contentBlockStop": {}}
            yield {"messageStop": {"stopReason": "tool_use"}}
        usage = {"inputTokens": 100, "outputTokens": 10, "totalTokens": 110}
        yield {"metadata": {"usage": usage, "metrics": {"latencyMs": 1}}}


async def test_native_captures_first_tool_call(
    tools: list[Tool], server_desc: dict[str, str]
) -> None:
    model = ScriptedModel(lambda specs, n: ("ms__docs_search", {}) if n == 1 else (None, {}))
    router = build_router(
        {"name": "s", "type": "strands", "mode": "native", "_model_factory": lambda: model}
    )
    res = await router.route("entra on-behalf-of flow", tools, server_desc)

    assert res.error is None, res.error
    assert res.top1 == "ms.docs_search"
    assert res.input_tokens is not None and res.input_tokens >= 100
    assert model.calls <= 2  # turn limit + cancel stop the loop quickly


async def test_structured_output_drops_unknown_ids(
    tools: list[Tool], server_desc: dict[str, str]
) -> None:
    def pick(specs: list[dict[str, Any]], _: int) -> tuple[str | None, dict[str, Any]]:
        name = specs[0]["name"] if specs else "ToolPick"
        return name, {
            "tool_id": "kiwi.search-flight",
            "alternatives": ["aws.search_docs", "bogus.x"],
            "confidence": 0.7,
        }

    router = build_router(
        {
            "name": "s",
            "type": "strands",
            "mode": "structured",
            "_model_factory": lambda: ScriptedModel(pick),
        }
    )
    res = await router.route("flights to Bangkok", tools, server_desc)

    assert res.error is None, res.error
    assert [t for t, _ in res.ranked] == ["kiwi.search-flight", "aws.search_docs"]
    assert res.ranked[0][1] == pytest.approx(0.7)
