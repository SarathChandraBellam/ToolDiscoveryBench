"""Catalog sampling, storage and golden-set validation."""

from __future__ import annotations

from pathlib import Path

from tooldiscoverybench.catalog import load_catalog, sample_catalog, save_catalog
from tooldiscoverybench.catalog.pull import _has_value, _truthy
from tooldiscoverybench.core.models import GoldenItem, Tool
from tooldiscoverybench.golden import validate_golden


def test_sample_contains_gold_and_is_deterministic() -> None:
    tools = [Tool(f"s{i % 7}", f"t{i}", "d") for i in range(100)]
    item = GoldenItem("q1", "?", ["s3.t3"])
    first = sample_catalog(tools, item, 20, seed=1)
    second = sample_catalog(tools, item, 20, seed=1)

    assert [t.id for t in first] == [t.id for t in second]
    assert len(first) == 20
    assert "s3.t3" in {t.id for t in first}
    # same-server hard negatives are added before anything else
    assert sum(t.server == "s3" for t in first) == sum(t.server == "s3" for t in tools)


def test_sample_all_returns_full_catalog() -> None:
    tools = [Tool("s", f"t{i}") for i in range(5)]
    assert len(sample_catalog(tools, GoldenItem("q", "?", []), "all")) == 5


def test_store_round_trip_merges_and_flags_synthetic(tmp_path: Path) -> None:
    real = {"servers": {"a": {"description": "A", "tools": [{"name": "x"}]}}}
    synth = {"synthetic": True, "servers": {"b": {"tools": [{"name": "y"}]}}}
    save_catalog(real, tmp_path / "real.json")
    save_catalog(synth, tmp_path / "synth.json")

    tools, desc = load_catalog(tmp_path / "real.json", tmp_path / "synth.json")

    assert [(t.id, t.synthetic) for t in tools] == [("a.x", False), ("b.y", True)]
    assert desc["a"] == "A"


def test_validate_golden_flags_renamed_tools() -> None:
    tools = [Tool("deepwiki", "ask_wiki_question")]
    items = [GoldenItem("q", "?", ["deepwiki.ask_question"])]
    assert validate_golden(items, tools) == ["q: tool(s) not in catalog: ['deepwiki.ask_question']"]


def test_env_driven_flags() -> None:
    assert not _truthy("false") and not _truthy("") and _truthy("true")
    assert not _has_value("Bearer ") and _has_value("Bearer abc")


def test_fixed_candidates_are_used_exactly() -> None:
    tools = [Tool(f"s{i % 3}", f"t{i}") for i in range(30)]
    item = GoldenItem("q", "?", ["s0.t0"], candidates=["s0.t0", "s1.t1", "s2.t2"])
    got = sample_catalog(tools, item, "fixed")
    assert sorted(t.id for t in got) == ["s0.t0", "s1.t1", "s2.t2"]
    assert [t.id for t in got] == [t.id for t in sample_catalog(tools, item, 150)]


def test_validate_flags_gold_outside_candidates() -> None:
    tools = [Tool("a", "x"), Tool("a", "y")]
    items = [GoldenItem("q", "?", ["a.x"], candidates=["a.y"])]
    assert validate_golden(items, tools) == ["q: gold not in its candidate catalog: ['a.x']"]
