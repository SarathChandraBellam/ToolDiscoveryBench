"""deepagents harness: offline tests with a scripted fake chat model (no network)."""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("deepagents")

from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage

from tooldiscoverybench.harness.agent import run_agent
from tooldiscoverybench.harness.models import PaidModelError, assert_free
from tooldiscoverybench.harness.report import complete_cells
from tooldiscoverybench.harness.routing import JevDecisionRouter, RouterPick, parse_tool_ids
from tooldiscoverybench.harness.runner import (
    TEST_QIDS,
    load_harness_catalog,
    sample_questions,
    score_row,
)


class ScriptedModel(GenericFakeChatModel):
    """Replays AIMessages (with tool calls); bind_tools is a no-op."""

    def bind_tools(self, tools: Any, **kwargs: Any) -> Any:
        return self


def scripted(*messages: AIMessage) -> ScriptedModel:
    def gen() -> Iterator[AIMessage]:
        for m in messages:
            m.usage_metadata = {"input_tokens": 100, "output_tokens": 10, "total_tokens": 110}
            yield m

    return ScriptedModel(messages=gen())


def call(name: str, args: dict[str, Any], i: int = 0) -> AIMessage:
    return AIMessage("", tool_calls=[{"name": name, "args": args, "id": f"c{i}"}])


@pytest.fixture(scope="module")
def catalog() -> Any:
    return load_harness_catalog()


Q = {
    "qid": "q1",
    "question": "how do Astro content collections work?",
    "gold": ["astro-docs.search_astro_docs"],
    "no_tool": False,
}


def test_catalog_has_31_real_tools(catalog: Any) -> None:
    assert len(catalog.tools) == 31
    assert catalog.resolve("astro-docs__search_astro_docs").id == "astro-docs.search_astro_docs"


def test_sample_is_dev_only_and_balanced() -> None:
    qs = sample_questions()
    test = set(Path(TEST_QIDS).read_text().split())
    assert len(qs) == 48
    assert not {q["qid"] for q in qs} & test
    assert all(q["split"] == "dev" for q in qs)
    assert sum(q["no_tool"] for q in qs) == 8


def test_all_tools_direct_call(catalog: Any) -> None:
    model = scripted(
        call("astro-docs__search_astro_docs", {"query": "content collections"}), AIMessage("done")
    )
    run = run_agent(model, Q["question"], "all_tools", catalog)
    assert run.error is None
    row = score_row(Q, "all_tools", "fake:free", run)
    assert row["first_tool"] == "astro-docs.search_astro_docs"
    assert row["top1_correct"] and row["gold_ever_called"] and row["ended_with_gold"]
    assert row["llm_calls"] == 2 and row["tool_search_calls"] == 0
    assert row["calls_to_gold"] == 1 and row["wasted_real_calls"] == 0
    assert row["input_tokens"] == 200


@pytest.mark.parametrize(
    ("setup", "arg"),
    [
        ("bm25_search", {"query": "astro docs content collections"}),
        ("regex_search", {"pattern": "astro"}),
    ],
)
def test_search_loads_then_direct_call(catalog: Any, setup: str, arg: dict[str, Any]) -> None:
    model = scripted(
        call("tool_search", arg, 0),
        call("svelte__get-documentation", {"section": ["x"]}, 1),
        call("astro-docs__search_astro_docs", {"query": "content collections"}, 2),
        AIMessage("done"),
    )
    run = run_agent(model, Q["question"], setup, catalog)
    row = score_row(Q, setup, "fake:free", run)
    assert row["tool_search_calls"] == 1 and row["discovery_calls"] == 1
    assert "astro-docs.search_astro_docs" in row["search_hits"][0]
    assert "astro-docs__search_astro_docs" in row["loaded_at_end"]
    # svelte was never loaded: the call is refused and not executed
    assert row["unloaded_tool_calls"] == ["svelte__get-documentation"]
    assert row["first_tool"] == "astro-docs.search_astro_docs" and row["top1_correct"]
    assert row["wasted_real_calls"] == 0 and row["calls_to_gold"] == 2
    assert row["real_calls_to_gold"] == 1 and row["llm_calls"] == 4


def test_regex_and_bm25_search_semantics(catalog: Any) -> None:
    assert catalog.regex_search("astro")[0] == "astro-docs__search_astro_docs"
    assert len(catalog.regex_search(".*")) == 5  # default limit 5
    assert len(catalog.regex_search(".*", limit=10)) == 10
    assert catalog.regex_search("zzzz_no_match") == []
    with pytest.raises(ValueError):
        catalog.regex_search("a" * 201)
    # argument names are searchable (Anthropic matches argument names/descriptions too)
    assert catalog.bm25_search("cloudflare documentation")[0].startswith("cloudflare-docs__")
    assert catalog.bm25_search("qqqq zzzz") == []


def test_invalid_regex_is_a_tool_error(catalog: Any) -> None:
    from tooldiscoverybench.harness.tools import CallLog

    out = catalog.search_tool("regex", CallLog()).invoke({"pattern": "("})
    assert "invalid_tool_input" in out


def test_deferred_tools_hidden_until_discovered(catalog: Any) -> None:
    from langchain_core.messages import HumanMessage, ToolMessage

    from tooldiscoverybench.harness.middleware import DeferredToolsMiddleware

    mw = DeferredToolsMiddleware(catalog.names)
    ref = '{"tool_references": [{"type": "tool_reference", "tool_name": "kiwi__search-flight"}]}'
    msgs = [HumanMessage("x"), ToolMessage(ref, tool_call_id="1", name="tool_search")]
    mw._discover(msgs)
    assert mw.loaded == ["kiwi__search-flight"]


class _FixedRouter:
    kind = "fixed"
    model_id = "fixed"

    def __init__(self, ids: list[str]) -> None:
        self.ids = ids
        self.calls = 0

    def pick(self, question: str, tools: list[Any]) -> RouterPick:
        self.calls += 1
        return RouterPick(self.ids, 5.0, "test router", "fixed", llm_calls=0)


def test_router_first_picks_once_and_falls_back(catalog: Any) -> None:
    router = _FixedRouter(
        ["svelte.get-documentation", "kiwi.search-flight", "gitmcp.search_generic_code"]
    )
    model = scripted(
        call("tool_search", {"query": "astro docs"}, 0),
        call("astro-docs__search_astro_docs", {"query": "x"}, 1),
        AIMessage("done"),
    )
    run = run_agent(model, Q["question"], "router_first", catalog, router)
    row = score_row(Q, "router_first", "fake:free", run)
    assert router.calls == 1  # once per run, not per model call
    assert row["router_tools"] == router.ids
    assert row["initially_loaded"] == [
        "svelte__get-documentation",
        "kiwi__search-flight",
        "gitmcp__search_generic_code",
    ]
    assert row["fallback_used"] and row["router_hit"] is False
    assert row["top1_correct"] and row["llm_calls"] == 3


def test_no_tool_question_abstains(catalog: Any) -> None:
    q = {**Q, "gold": [], "no_tool": True}
    run = run_agent(scripted(AIMessage("NO_TOOL")), q["question"], "all_tools", catalog)
    row = score_row(q, "all_tools", "fake:free", run)
    assert row["abstained"] and row["top1_correct"] and row["said_no_tool"]
    assert row["wasted_real_calls"] == 0


def test_step_cap(catalog: Any) -> None:
    model = scripted(*[call("tool_search", {"query": f"x{i}"}, i) for i in range(20)])
    run = run_agent(model, Q["question"], "bm25_search", catalog, max_model_calls=3)
    assert run.usage.calls == 3 and run.hit_step_cap


def test_paid_models_refused() -> None:
    assert assert_free("a/b:free") == "a/b:free"
    with pytest.raises(PaidModelError):
        assert_free("anthropic/claude-sonnet-5.5")
    with pytest.raises(PermissionError):
        JevDecisionRouter({}, allow_paid=False)


def test_parse_tool_ids() -> None:
    known = {"a.x", "b.y", "c.z"}
    assert parse_tool_ids('{"tools": ["b.y", "nope", "a.x"]}', known, 3) == ["b.y", "a.x"]
    assert parse_tool_ids("I'd pick c.z then a.x", known, 3) == ["c.z", "a.x"]


def test_summary_excludes_partial_cells(tmp_path: Path) -> None:
    from tooldiscoverybench.harness.report import write_summary

    base = {
        "no_tool": False,
        "top1_correct": True,
        "gold_ever_called": True,
        "ended_with_gold": True,
        "llm_calls": 2,
        "tool_search_calls": 0,
        "input_tokens": 1,
        "output_tokens": 1,
        "latency_ms": 1000,
        "hit_step_cap": False,
        "error": None,
        "total_tool_calls": 1,
        "discovery_calls": 0,
        "real_tool_calls": 1,
        "wasted_real_calls": 0,
        "calls_to_gold": 1,
        "search_found_gold": None,
    }
    rows = [{**base, "setup": "all_tools", "model": "m", "qid": q} for q in ("a", "b")]
    rows.append({**base, "setup": "bm25_search", "model": "m", "qid": "a"})
    cells, partial = complete_cells(rows, ["a", "b"])
    assert list(cells) == [("all_tools", "m")]
    assert partial and "bm25_search" in partial[0]
    (tmp_path / "results.jsonl").write_text("\n".join(json.dumps(r) for r in rows))
    text = write_summary(tmp_path, ["a", "b"], {})
    assert "1.00 (2/2)" in text and "Incomplete cells" in text
