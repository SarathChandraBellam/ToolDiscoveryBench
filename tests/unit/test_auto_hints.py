"""Auto option hints: mechanical key args, LLM lines from catalog data only, per-catalog cache."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import httpx
import pytest

from tests.unit.test_jev import jev
from tooldiscoverybench.catalog.auto_hints import (
    AutoHint,
    auto_option_text,
    key_args_from_schema,
    load_or_generate,
    parse_reply,
    user_message,
)
from tooldiscoverybench.core.models import Tool


def fake_llm(calls: list[dict[str, Any]]) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        calls.append(body)
        target = body["messages"][1]["content"].split("Target tool: ", 1)[1].split("\n", 1)[0]
        reply = {"use_when": f"asked about {target}", "not_when": "something else"}
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": "```json\n" + json.dumps(reply) + "\n```"}}],
                "usage": {"cost": 0.001},
            },
        )

    return httpx.MockTransport(handler)


def test_key_args_are_mechanical() -> None:
    schema = {
        "properties": {"b": {"type": "integer"}, "a": {"type": "string"}, "c": {}},
        "required": ["a"],
    }
    assert key_args_from_schema(schema) == "a (string, required), b (integer), c"
    assert key_args_from_schema({}) == "none"
    many = {"properties": {f"p{i}": {"type": "string"} for i in range(8)}}
    assert key_args_from_schema(many, limit=2).endswith("+6 more")


def test_parse_reply() -> None:
    assert parse_reply('```json\n{"use_when": " a  b ", "not_when": "c"}\n```') == AutoHint(
        "a b", "c"
    )
    with pytest.raises(ValueError):
        parse_reply('{"use_when": "a"}')
    with pytest.raises(ValueError):
        parse_reply("sorry")


def test_option_text_keeps_description_verbatim() -> None:
    tool = Tool("aws", "search_docs", "Search AWS documentation", {"properties": {"q": {}}})
    plain = "[aws] search_docs: Search AWS documentation"
    assert auto_option_text(tool, None, 240) == plain
    assert auto_option_text(tool, AutoHint("docs questions", "a URL is given"), 240) == (
        plain + " Use when: docs questions. Not when: a URL is given. Key args: q."
    )


def test_prompt_uses_catalog_data_only(tools: list[Tool]) -> None:
    msg = user_message(tools[0], tools, {"aws": "AWS docs"})
    assert "Target tool: aws.search_docs" in msg
    assert "- aws.list_regions: List AWS regions" in msg  # sibling with description
    assert "ms.docs_search" in msg and "Search Microsoft Learn docs" not in msg  # ids only


async def test_generates_once_then_uses_cache(
    tools: list[Tool], server_desc: dict[str, str], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[dict[str, Any]] = []
    logs: list[str] = []
    monkeypatch.setenv("TDB_TEST_KEY", "k")
    hints, meta = await load_or_generate(
        tools,
        server_desc,
        cache_dir=tmp_path,
        api_key_env="TDB_TEST_KEY",
        transport=fake_llm(calls),
        log=logs.append,
    )
    assert len(calls) == len(tools) and set(hints) == {t.id for t in tools}
    assert all(c["temperature"] == 0 for c in calls)
    assert meta["cost_usd"] == pytest.approx(0.004) and not meta["cached"]
    assert hints["aws.search_docs"].use_when == "asked about aws.search_docs"

    again, meta2 = await load_or_generate(tools, server_desc, cache_dir=tmp_path, log=logs.append)
    assert again == hints and meta2["cached"] and len(calls) == len(tools)  # no new calls


async def test_router_default_plain_and_auto_opt_in(
    tools: list[Tool], server_desc: dict[str, str], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plain_cap: list[dict[str, Any]] = []
    plain_router = jev(plain_cap, mode="flat")
    await plain_router.setup(tools, server_desc)
    await plain_router.route("q", tools, server_desc)
    plain = plain_cap[0]["body"]["questions"]["tool"]["criteria"]
    assert plain["aws.search_docs"] == "[aws] search_docs: Search AWS documentation"

    monkeypatch.setenv("OPENROUTER_API_KEY", "k")
    calls: list[dict[str, Any]] = []
    auto_cap: list[dict[str, Any]] = []
    router = jev(
        auto_cap,
        mode="flat",
        option_text="auto",
        auto_hints_cache=str(tmp_path),
        _auto_hints_transport=fake_llm(calls),
    )
    await router.setup(tools, server_desc)
    await router.route("q", tools, server_desc)
    auto = auto_cap[0]["body"]["questions"]["tool"]["criteria"]
    assert auto["aws.search_docs"].startswith(plain["aws.search_docs"] + " Use when: ")
    assert auto["__none__"] == plain["__none__"]
    assert router.auto_hints_meta["n_tools"] == len(tools)

    with pytest.raises(ValueError, match="option_text"):
        jev([], option_text="fancy")
