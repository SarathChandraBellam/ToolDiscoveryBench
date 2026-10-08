"""BM25 baseline and router registry."""

from __future__ import annotations

import pytest

from tooldiscoverybench.core.models import Tool
from tooldiscoverybench.routers import available_types, build_router, safe_tool_name
from tooldiscoverybench.routers.baselines.bm25 import tokenize


async def test_bm25_ranks_obvious_tool(tools: list[Tool], server_desc: dict[str, str]) -> None:
    router = build_router({"name": "bm25", "type": "bm25"})
    res = await router.route("list all AWS regions", tools, server_desc)
    assert res.top1 == "aws.list_regions"
    assert res.calls == 0


def test_tokenize_splits_tool_name_styles() -> None:
    assert tokenize("aws___get_regional_availability") == ["aws", "regional", "availability"]
    assert tokenize("resolve-library-id") == ["resolve", "library", "id"]
    assert tokenize("searchFlights") == ["search", "flights"]


def test_registry_rejects_unknown_type() -> None:
    assert {"bm25", "embedding", "jev", "strands"} <= set(available_types())
    with pytest.raises(ValueError, match="unknown router type"):
        build_router({"name": "x", "type": "nope"})


def test_safe_tool_name() -> None:
    assert safe_tool_name("context7.resolve-library-id") == "context7__resolve-library-id"
    assert safe_tool_name("a.b.c d") == "a__b_c_d"
    assert len(safe_tool_name("s." + "x" * 100)) == 64
