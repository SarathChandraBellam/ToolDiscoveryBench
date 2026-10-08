"""Shared fixtures: a tiny catalog used across unit tests."""

from __future__ import annotations

import pytest

from tooldiscoverybench.core.models import Tool


@pytest.fixture
def tools() -> list[Tool]:
    return [
        Tool("aws", "search_docs", "Search AWS documentation"),
        Tool("aws", "list_regions", "List AWS regions"),
        Tool("ms", "docs_search", "Search Microsoft Learn docs"),
        Tool("kiwi", "search-flight", "Search flights"),
    ]


@pytest.fixture
def server_desc() -> dict[str, str]:
    return {"aws": "AWS docs", "ms": "Microsoft docs", "kiwi": "flights"}
