"""Option text for decision routers: plain (default, unchanged) vs rich (hand-written hints)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from tests.unit.test_jev import jev
from tooldiscoverybench.catalog import load_catalog
from tooldiscoverybench.catalog.option_text import (
    DEFAULT_HINTS_PATH,
    OptionHint,
    OptionTextBuilder,
    load_option_hints,
)
from tooldiscoverybench.core.models import Tool

ROOT = Path(__file__).resolve().parents[2]
HINTS = ROOT / DEFAULT_HINTS_PATH


def test_plain_text_is_the_original_format(tools: list[Tool]) -> None:
    build = OptionTextBuilder(desc_chars=10)
    t = tools[0]
    assert build(t) == f"[{t.server}] {t.name}: {t.short_desc(10)}"


def test_rich_text_uses_hints_and_falls_back(tools: list[Tool]) -> None:
    hint = OptionHint("Searches AWS docs", "a how-to question", "a URL is given", "query")
    build = OptionTextBuilder("rich", hints={"aws.search_docs": hint})
    assert build(tools[0]) == (
        "[aws] search_docs: Searches AWS docs. Use when: a how-to question. "
        "Not when: a URL is given. Key args: query."
    )
    assert build(tools[1]) == OptionTextBuilder()(tools[1])  # no hint -> plain


def test_unknown_mode_and_field_are_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="option_text"):
        OptionTextBuilder("fancy")
    bad = tmp_path / "hints.json"
    bad.write_text(json.dumps({"tools": {"a.b": {"use_whenn": "x"}}}))
    with pytest.raises(ValueError, match="unknown option hint"):
        load_option_hints(bad)


def test_hints_cover_every_real_tool_and_stay_short() -> None:
    tools, _ = load_catalog(ROOT / "data/catalog/public.json")
    hints = load_option_hints(HINTS)
    assert set(hints) == {t.id for t in tools}
    for tool_id, h in hints.items():
        assert h.summary and h.use_when and h.not_when and h.key_args, tool_id
        text = OptionTextBuilder("rich", hints=hints)(next(t for t in tools if t.id == tool_id))
        assert len(text) <= 700, (tool_id, len(text))


async def test_decision_router_default_is_plain_and_rich_is_opt_in(
    tools: list[Tool], server_desc: dict[str, str], tmp_path: Path
) -> None:
    plain_cap: list[dict[str, Any]] = []
    await jev(plain_cap, mode="flat").route("q", tools, server_desc)
    plain = plain_cap[0]["body"]["questions"]["tool"]["criteria"]
    assert plain["aws.search_docs"] == "[aws] search_docs: Search AWS documentation"

    path = tmp_path / "hints.json"
    path.write_text(json.dumps({"tools": {"aws.search_docs": {"use_when": "docs questions"}}}))
    rich_cap: list[dict[str, Any]] = []
    router = jev(rich_cap, mode="flat", option_text="rich", option_hints=str(path))
    await router.route("q", tools, server_desc)
    rich = rich_cap[0]["body"]["questions"]["tool"]["criteria"]

    assert rich["aws.search_docs"] == (
        "[aws] search_docs: Search AWS documentation Use when: docs questions."
    )
    assert rich["aws.list_regions"] == plain["aws.list_regions"]  # no hint -> plain
    assert rich["__none__"] == plain["__none__"]
