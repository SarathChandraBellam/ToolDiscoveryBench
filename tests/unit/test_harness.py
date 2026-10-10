"""deepagents harness: offline tests with a scripted fake chat model (no network)."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("deepagents")

from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage

from tooldiscoverybench.harness.agent import run_agent
from tooldiscoverybench.harness.models import PaidModelError, assert_free
from tooldiscoverybench.harness.report import summarise
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


Q = {"qid": "q1", "question": "how do Astro content collections work?",
     "gold": ["astro-docs.search_astro_docs"], "no_tool": False}


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
    model = scripted(call("astro-docs__search_astro_docs", {"query": "content collections"}),
                     AIMessage("done"))
    run = run_agent(model, Q["question"], "all_tools", catalog)
    assert run.error is None
    row = score_row(Q, "all_tools", "fake:free", run, None)
    assert row["first_tool"] == "astro-docs.search_astro_docs"
    assert row["top1_correct"] and row["gold_ever_called"]
    assert row["llm_calls"] == 2 and row["tool_search_calls"] == 0
    assert row["input_tokens"] == 200


def test_bm25_search_then_call_tool(catalog: Any) -> None:
    model = scripted(
        call("tool_search", {"query": "astro docs content collections"}, 0),
        call("call_tool", {"name": "astro-docs__search_astro_docs",
                           "arguments": {"query": "content collections"}}, 1),
        AIMessage("done"),
    )
    run = run_agent(model, Q["question"], "bm25_search", catalog)
    row = score_row(Q, "bm25_search", "fake:free", run, None)
    assert row["tool_search_calls"] == 1
    assert "astro-docs.search_astro_docs" in row["search_hits"][0]
    assert row["first_tool"] == "astro-docs.search_astro_docs"
    assert row["first_tool_via"] == "call_tool"
    assert row["llm_calls"] == 3


def test_router_first_counts_router_and_fallback(catalog: Any) -> None:
    pick = RouterPick(["svelte.get-documentation", "kiwi.search-flight", "gitmcp.search_generic_code"],
                      5.0, "free-model router", "router:free", llm_calls=1,
                      input_tokens=50, output_tokens=5)
    model = scripted(
        call("tool_search", {"query": "astro docs"}, 0),
        call("call_tool", {"name": "astro-docs.search_astro_docs", "arguments": "{}"}, 1),
        AIMessage("done"),
    )
    run = run_agent(model, Q["question"], "router_first", catalog, pick)
    row = score_row(Q, "router_first", "fake:free", run, pick)
    assert row["bound_tools"] == pick.tool_ids
    assert row["fallback_used"] and row["router_hit"] is False
    assert row["top1_correct"]
    assert row["llm_calls"] == 4 and row["input_tokens"] == 350


def test_no_tool_question_abstains(catalog: Any) -> None:
    q = {**Q, "gold": [], "no_tool": True}
    run = run_agent(scripted(AIMessage("NO_TOOL")), q["question"], "all_tools", catalog)
    row = score_row(q, "all_tools", "fake:free", run, None)
    assert row["abstained"] and row["top1_correct"] and row["said_no_tool"]


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


def test_summary_excludes_partial_cells() -> None:
    base = {"no_tool": False, "top1_correct": True, "gold_ever_called": True, "llm_calls": 2,
            "tool_search_calls": 0, "input_tokens": 1, "output_tokens": 1, "latency_ms": 1000,
            "hit_step_cap": False, "error": None}
    rows = [{**base, "setup": "all_tools", "model": "m", "qid": q} for q in ("a", "b")]
    rows.append({**base, "setup": "bm25_search", "model": "m", "qid": "a"})
    table, partial = summarise(rows, ["a", "b"])
    assert [r["setup"] for r in table] == ["all_tools"]
    assert table[0]["top1"] == "1.00 (2/2)"
    assert partial and "bm25_search" in partial[0]
