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

from tooldiscoverybench.harness.agent import RouterOptions, run_agent, run_conversation
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
    assert mw.loaded({"messages": msgs[:1]}) == []
    assert mw.loaded({"messages": msgs}) == ["kiwi__search-flight"]


class _FixedRouter:
    kind = "fixed"
    model_id = "fixed"

    def __init__(self, ids: list[str], *more: list[str]) -> None:
        self.ids = ids
        self.script = [ids, *more]  # picks per call; the last one repeats
        self.calls = 0
        self.questions: list[str] = []

    def pick(self, question: str, tools: list[Any]) -> RouterPick:
        ids = self.script[min(self.calls, len(self.script) - 1)]
        self.calls += 1
        self.questions.append(question)
        return RouterPick(ids, 5.0, "test router", "fixed", llm_calls=0, raw={"cost_usd": 0.001})


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


# ------------------------------------------------------------------ routing across turns
TURNS = ["how do Astro content collections work?", "now find me a flight from Prague to Oslo"]
ASTRO, FLIGHT = "astro-docs.search_astro_docs", "kiwi.search-flight"


def test_router_reroutes_on_every_new_user_message(catalog: Any) -> None:
    router = _FixedRouter([ASTRO], [FLIGHT])
    model = scripted(
        call("astro-docs__search_astro_docs", {"query": "x"}, 0),
        AIMessage("done"),
        call("kiwi__search-flight", {}, 1),
        AIMessage("done"),
    )
    runs = run_conversation(model, TURNS, "router_first", catalog, router)
    assert router.calls == 2  # once per user message, not per model call
    assert router.questions[0] == TURNS[0]
    # the second call sees the new message plus a short summary of the earlier turn
    assert TURNS[0] in router.questions[1] and f"Current request: {TURNS[1]}" in router.questions[1]
    assert "astro-docs__search_astro_docs" in router.questions[1]
    rows = [
        score_row(
            {"qid": f"c#t{i}", "question": t, "gold": [g], "no_tool": False},
            "router_first",
            "fake:free",
            run,
        )
        for i, (t, g, run) in enumerate(zip(TURNS, [ASTRO, FLIGHT], runs, strict=True), 1)
    ]
    assert [r["top1_correct"] for r in rows] == [True, True]
    assert [r["router_calls"] for r in rows] == [1, 1]
    assert rows[1]["router_tools"] == [FLIGHT] and rows[1]["router_cost_usd"] == 0.001
    # default carry policy keeps the earlier turn's tool loaded next to the new pick
    assert runs[1].initially_loaded == ["astro-docs__search_astro_docs", "kiwi__search-flight"]
    assert rows[1]["llm_calls"] == 2 and rows[1]["input_tokens"] == 200  # per turn, not summed


@pytest.mark.parametrize(
    ("carry", "cap", "expected"),
    [
        (
            "keep",
            5,
            ["astro-docs__search_astro_docs", "svelte__list-sections", "kiwi__search-flight"],
        ),
        ("cap", 1, ["svelte__list-sections", "kiwi__search-flight"]),
        ("replace", 5, ["kiwi__search-flight"]),
    ],
)
def test_carry_policy_for_tools_loaded_in_earlier_turns(
    catalog: Any, carry: str, cap: int, expected: list[str]
) -> None:
    router = _FixedRouter([ASTRO, "svelte.list-sections"], [FLIGHT])
    model = scripted(AIMessage("a"), AIMessage("b"))
    options = RouterOptions(carry=carry, carry_cap=cap)
    runs = run_conversation(model, TURNS, "router_first", catalog, router, options=options)
    assert runs[1].initially_loaded == expected


def test_request_tools_reroutes_mid_task(catalog: Any) -> None:
    router = _FixedRouter(["svelte.list-sections"], [ASTRO])
    model = scripted(
        call("request_tools", {"need": "search the Astro documentation"}, 0),
        call("astro-docs__search_astro_docs", {"query": "x"}, 1),
        AIMessage("done"),
    )
    options = RouterOptions(request_tools=True, search_fallback=False)
    run = run_agent(model, Q["question"], "router_first", catalog, router, options=options)
    row = score_row(Q, "router_first", "fake:free", run)
    assert router.calls == 2 and "search the Astro documentation" in router.questions[1]
    assert row["router_calls"] == 2 and row["request_tools_calls"] == 1
    assert [e["source"] for e in row["router_events"]] == ["user_message", "request_tools"]
    assert row["top1_correct"] and row["unloaded_tool_calls"] == []
    assert row["tool_search_calls"] == 0  # search fallback was switched off
    assert row["router_latency_ms"] == 10.0 and row["router_call_latencies_ms"] == [5.0, 5.0]
    assert row["router_hit"] is False  # the upfront pick missed; request_tools fixed it


def test_request_tools_is_optional(catalog: Any) -> None:
    router = _FixedRouter(["svelte.list-sections"])
    model = scripted(call("astro-docs__search_astro_docs", {"query": "x"}, 0), AIMessage("done"))
    run = run_agent(model, Q["question"], "router_first", catalog, router)
    row = score_row(Q, "router_first", "fake:free", run)
    # not loaded and not requested: the call is refused, like the API would
    assert row["unloaded_tool_calls"] == ["astro-docs__search_astro_docs"]
    assert row["first_tool"] is None and router.calls == 1


def _router_agent(catalog: Any, router: Any, model: Any, checkpointer: Any) -> Any:
    from tooldiscoverybench.harness.agent import build_agent
    from tooldiscoverybench.harness.middleware import ToolRouterMiddleware
    from tooldiscoverybench.harness.tools import CallLog

    mw = ToolRouterMiddleware(router, catalog.tools, request_tools=True)
    agent = build_agent(
        model, catalog.stubs(CallLog()), "router_first", 8, mw, checkpointer=checkpointer
    )
    return agent, mw


def test_routing_state_lives_in_graph_state_per_thread(catalog: Any) -> None:
    from langchain_core.messages import HumanMessage
    from langgraph.checkpoint.memory import InMemorySaver

    saver = InMemorySaver()
    router = _FixedRouter([ASTRO], [FLIGHT])
    agent, _ = _router_agent(catalog, router, scripted(AIMessage("a")), saver)
    one = {"configurable": {"thread_id": "one"}}
    agent.invoke({"messages": [HumanMessage(TURNS[0])]}, one)
    # a NEW agent and middleware instance on the same checkpointer picks the thread up
    agent2, mw2 = _router_agent(catalog, router, scripted(AIMessage("b"), AIMessage("c")), saver)
    state = agent2.get_state(one).values
    assert state["tdb_turn_picks"] == ["astro-docs__search_astro_docs"]
    assert mw2.loaded(state) == ["astro-docs__search_astro_docs"]
    agent2.invoke({"messages": [HumanMessage(TURNS[1])]}, one)
    state = agent2.get_state(one).values
    assert [e["source"] for e in state["tdb_router_events"]] == ["user_message"] * 2
    assert state["tdb_carry"] == ["astro-docs__search_astro_docs"]
    assert state["tdb_turn_picks"] == ["kiwi__search-flight"]
    # another thread has its own routing state
    two = {"configurable": {"thread_id": "two"}}
    agent2.invoke({"messages": [HumanMessage("unrelated")]}, two)
    assert len(agent2.get_state(two).values["tdb_router_events"]) == 1
    assert router.calls == 3


async def test_async_invocation_routes_too(catalog: Any) -> None:
    from langchain_core.messages import HumanMessage

    router = _FixedRouter(["svelte.list-sections"], [ASTRO])
    model = scripted(
        call("request_tools", {"need": "astro docs"}, 0),
        call("astro-docs__search_astro_docs", {"query": "x"}, 1),
        AIMessage("done"),
    )
    agent, mw = _router_agent(catalog, router, model, None)
    state = await agent.ainvoke({"messages": [HumanMessage(Q["question"])]})
    assert router.calls == 2
    assert [e["source"] for e in state["tdb_router_events"]] == ["user_message", "request_tools"]
    assert mw.loaded(state) == ["svelte__list-sections", "astro-docs__search_astro_docs"]
    assert "[stub] astro-docs.search_astro_docs" in state["messages"][-2].content


def test_jev_spend_cap_stops_before_overspending(catalog: Any) -> None:
    from tooldiscoverybench.core.models import RouteResult
    from tooldiscoverybench.harness.routing import BudgetExhaustedError

    class FakeDecisions:
        async def route(self, question: str, tools: Any, server_desc: Any) -> RouteResult:
            return RouteResult([(ASTRO, 0.9), (FLIGHT, 0.1)], 12.0, cost_usd=0.4)

    jev = JevDecisionRouter.__new__(JevDecisionRouter)
    jev.router, jev.server_desc, jev.k, jev.model_id = FakeDecisions(), {}, 1, "jev"
    jev.max_spend_usd, jev.spent_usd, jev.calls, jev._worst_call_usd = 1.0, 0.0, 0, 0.001
    jev.timeout = 5.0
    for _ in range(2):
        pick = jev.pick("q", catalog.tools)
    assert pick.tool_ids == [ASTRO] and pick.raw["cost_usd"] == 0.4
    assert jev.spent_usd == pytest.approx(0.8)
    with pytest.raises(BudgetExhaustedError):  # 0.8 + another 0.4 would pass the $1 cap
        jev.pick("q", catalog.tools)
    assert jev.calls == 2


def test_conversations_are_dev_only_and_follow_ups_need_another_tool() -> None:
    from tooldiscoverybench.harness.runner import build_conversations

    single = {q["qid"] for q in sample_questions()}
    convs = build_conversations(exclude_qids=single)
    assert convs == build_conversations(exclude_qids=single)  # deterministic
    test = set(Path(TEST_QIDS).read_text().split())
    qids = [t["qid"] for c in convs for t in c["turns"]]
    assert len(convs) == 15 and len(qids) == 32 == len(set(qids))
    assert not set(qids) & test and not set(qids) & single
    assert {len(c["turns"]) for c in convs} == {2, 3}
    for c in convs:
        for a, b in zip(c["turns"], c["turns"][1:], strict=False):
            assert not set(a["gold"]) & set(b["gold"])
        if c["kind"] == "same_server":
            assert len({t["gold"][0].split(".")[0] for t in c["turns"]}) == 1
        if c["kind"] == "ends_no_tool":
            assert c["turns"][-1]["no_tool"]


def test_multiturn_summary_reports_complete_cells_only(tmp_path: Path) -> None:
    import json

    from tooldiscoverybench.harness.report import _dist, write_multiturn_summary

    assert _dist([1.0, 2.0, 3.0, 4.0, 10.0]) == "4.0 / 3.0 / 10.0"
    base = {
        "no_tool": False,
        "top1_correct": True,
        "gold_ever_called": True,
        "llm_calls": 3,
        "total_tool_calls": 1,
        "tool_search_calls": 0,
        "input_tokens": 100,
        "output_tokens": 5,
        "latency_ms": 2000.0,
        "error": None,
        "model": "m",
        "router_calls": 1,
        "router_call_latencies_ms": [250.0],
        "router_latency_ms": 250.0,
        "router_input_tokens": 40,
        "request_tools_calls": 0,
        "router_cost_usd": 0.0002,
    }
    keys = ["mt-01#t1", "mt-01#t2"]
    rows = [
        {**base, "setup": "router_first_jev", "qid": k, "conv_id": "mt-01", "turn": i}
        for i, k in enumerate(keys, 1)
    ]
    rows.append({**base, "setup": "all_tools", "qid": keys[0], "conv_id": "mt-01", "turn": 1})
    (tmp_path / "multiturn_results.jsonl").write_text("\n".join(json.dumps(r) for r in rows))
    text = write_multiturn_summary(tmp_path, keys, {"n_conversations": 1})
    assert "| router_first_jev | m | 2 | 0 | 1.00 (2/2) |" in text
    assert "0.25 / 0.25 / 0.25" in text and "0.000200" in text  # router latency, cost per turn
    assert "| router_first_jev | m | 1 | 0 | 1.00 (1/1) | 1.00 (2/2) | 2.00 |" in text
    assert "all_tools / m: 1/2 questions (excluded)" in text


# ------------------------------------------------------------ timeouts, paid models, spend
def test_task_timeout_is_recorded_as_an_error_row(catalog: Any) -> None:
    import time

    class StuckModel(ScriptedModel):
        def _generate(self, *args: Any, **kwargs: Any) -> Any:
            time.sleep(5)  # a call that never comes back in time
            return super()._generate(*args, **kwargs)

    model = StuckModel(messages=iter([AIMessage("late")]))
    started = time.perf_counter()
    runs = run_conversation(model, TURNS, "all_tools", catalog, task_timeout=0.3)
    assert time.perf_counter() - started < 3  # the run moved on instead of waiting
    assert runs[0].error and runs[0].error.startswith("TaskTimeout")
    assert runs[1].error and runs[1].error.startswith("skipped")  # conversation abandoned
    row = score_row(Q, "all_tools", "fake:free", runs[0])
    assert row["error"].startswith("TaskTimeout") and not row["top1_correct"]


def test_jev_call_timeout_returns_an_error_pick(catalog: Any) -> None:
    import asyncio

    class SlowDecisions:
        async def route(self, question: str, tools: Any, server_desc: Any) -> Any:
            await asyncio.sleep(5)

    jev = JevDecisionRouter.__new__(JevDecisionRouter)
    jev.router, jev.server_desc, jev.k, jev.model_id = SlowDecisions(), {}, 3, "jev"
    jev.max_spend_usd, jev.spent_usd, jev.calls, jev._worst_call_usd = 1.0, 0.0, 0, 0.001
    jev.timeout = 0.2
    pick = jev.pick("q", catalog.tools)
    assert pick.tool_ids == [] and pick.error and "TimeoutError" in pick.error
    assert jev.spent_usd == 0.0  # nothing charged for a call that never answered


def test_paid_agent_models_need_allowlist_and_flag() -> None:
    from tooldiscoverybench.harness.models import assert_allowed

    paid = ["openai/gpt-6-luna"]
    assert assert_allowed("a/b:free") == "a/b:free"
    assert assert_allowed("openai/gpt-6-luna", paid, True) == "openai/gpt-6-luna"
    with pytest.raises(PaidModelError):
        assert_allowed("openai/gpt-6-luna", paid, False)  # listed, but paid runs are off
    with pytest.raises(PaidModelError):
        assert_allowed("anthropic/claude-opus-5.5", paid, True)  # not on the allowlist


def test_spend_cap_and_billed_cost(catalog: Any) -> None:
    from tooldiscoverybench.harness.routing import BudgetExhaustedError
    from tooldiscoverybench.harness.runner import SpendCap

    cap = SpendCap(3.0, spent=2.0)
    cap.check("first task")  # nothing seen yet: allowed
    cap.add(0.6)
    with pytest.raises(BudgetExhaustedError):
        cap.check("next task")  # 2.6 + another 0.6 would pass $3
    cap = SpendCap(3.0, spent=2.0)
    cap.add(0.3)
    cap.check("one task")
    with pytest.raises(BudgetExhaustedError):
        cap.check("a 3-turn conversation", tasks=3)

    # the cost OpenRouter reports on each call ends up on the row
    msgs = [call("astro-docs__search_astro_docs", {"query": "x"}), AIMessage("done")]
    for m in msgs:
        m.response_metadata = {"token_usage": {"cost": 0.002}}
    run = run_agent(scripted(*msgs), Q["question"], "all_tools", catalog)
    row = score_row(Q, "all_tools", "paid/model", run)
    assert row["agent_cost_usd"] == pytest.approx(0.004) == row["cost_usd"]
    assert row["router_cost_usd"] is None
