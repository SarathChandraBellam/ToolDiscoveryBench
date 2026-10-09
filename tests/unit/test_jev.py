"""Jev router tests against a fake HTTP transport (no network, no key)."""

from __future__ import annotations

import json
from typing import Any

import httpx
import pytest

from tooldiscoverybench.core.models import Tool
from tooldiscoverybench.routers import build_router


def fake_jev(captured: list[dict[str, Any]]) -> httpx.MockTransport:
    """Puts 0.9 on the first option containing 'search' (or the 'aws' server), 0.1 spread."""

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        captured.append(
            {"url": str(request.url), "body": body, "auth": request.headers.get("authorization")}
        )
        answers = {}
        for qname, question in body["questions"].items():
            options = list(question["criteria"])
            best = next((o for o in options if "search" in o or o == "aws"), options[0])
            rest = [o for o in options if o != best]
            probs = {best: 0.9, **{o: 0.1 / len(rest) for o in rest}} if rest else {best: 1.0}
            answers[qname] = {
                "type": "choice",
                "choice": best,
                "confidence": 0.8,
                "probabilities": probs,
            }
        return httpx.Response(
            200,
            json={
                "model": "jev-1.13.0",
                "answers": answers,
                "usage": {"input_tokens": 123, "output_tokens": 0},
            },
        )

    return httpx.MockTransport(handler)


def jev(captured: list[dict[str, Any]], **cfg: Any) -> Any:
    return build_router(
        {"name": "j", "type": "jev", "api_key": "k", "_transport": fake_jev(captured), **cfg}
    )


async def test_flat_payload_and_parse(tools: list[Tool], server_desc: dict[str, str]) -> None:
    cap: list[dict[str, Any]] = []
    router = jev(cap, mode="flat")
    res = await router.route("how do I search aws docs", tools, server_desc)
    await router.aclose()

    assert res.error is None and res.calibrated
    assert res.top1 == "aws.search_docs"
    assert res.ranked[0][1] == pytest.approx(0.9)
    req = cap[0]
    assert req["url"] == "https://api.typesafe.ai/v1/systemone"
    assert req["auth"] == "Bearer k"
    question = req["body"]["questions"]["tool"]
    assert req["body"]["model"] == "jev-latest"
    assert question["type"] == "choice"
    assert set(question["criteria"]) == {t.id for t in tools} | {"__none__"}
    assert res.input_tokens == 123 and res.calls == 1


async def test_factored_is_one_request_with_joint_probs(
    tools: list[Tool], server_desc: dict[str, str]
) -> None:
    cap: list[dict[str, Any]] = []
    res = await jev(cap, mode="factored").route("aws docs", tools, server_desc)

    assert len(cap) == 1 and res.calls == 1
    questions = cap[0]["body"]["questions"]
    assert "server" in questions and len(questions) == 2  # server + the 2-tool aws server
    probs = dict(res.ranked)
    assert res.raw is not None
    assert sum(probs.values()) + res.raw["p_none"] == pytest.approx(1.0)
    assert "__none__" in questions["server"]["criteria"]
    assert res.top1 == "aws.search_docs"
    assert probs["aws.search_docs"] == pytest.approx(0.9 * 0.9)


async def test_hierarchical_makes_two_calls(tools: list[Tool], server_desc: dict[str, str]) -> None:
    cap: list[dict[str, Any]] = []
    res = await jev(cap, mode="hierarchical", top_servers=1).route("aws docs", tools, server_desc)

    assert len(cap) == 2 and res.calls == 2
    assert set(cap[1]["body"]["questions"]["tool"]["criteria"]) == {
        "aws.search_docs",
        "aws.list_regions",
    }
    assert {t for t, _ in res.ranked} == {t.id for t in tools}  # pruned tools kept at p=0


async def test_flat_tournament_above_255_options() -> None:
    many = [Tool(f"s{i // 50}", f"t{i}", "x") for i in range(600)] + [Tool("zz", "search_me", "x")]
    cap: list[dict[str, Any]] = []
    res = await jev(cap, mode="flat").route("q", many, {})

    assert all(len(c["body"]["questions"]["tool"]["criteria"]) <= 255 for c in cap)
    assert res.calls == 4  # 3 chunks + final
    assert res.top1 == "zz.search_me"


async def test_gateway_dialect(tools: list[Tool], server_desc: dict[str, str]) -> None:
    cap: list[dict[str, Any]] = []
    await jev(cap, dialect="decisions", base_url="https://gw.example").route(
        "q", tools, server_desc
    )

    assert cap[0]["url"] == "https://gw.example/v1/decisions"
    assert cap[0]["body"]["model"] == "typesafe/jev-latest"
    assert cap[0]["body"]["questions"]["tool"]["kind"] == "choice"


async def test_http_error_is_reported_not_raised(
    tools: list[Tool], server_desc: dict[str, str]
) -> None:
    transport = httpx.MockTransport(lambda _: httpx.Response(401, json={"detail": "bad key"}))
    router = build_router({"name": "j", "type": "jev", "api_key": "k", "_transport": transport})
    res = await router.route("q", tools, server_desc)

    assert res.error is not None and "401" in res.error
    assert res.ranked == []


def test_missing_key_marks_router_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    router = build_router({"name": "j", "type": "jev"})
    assert router.unavailable_reason() == "TYPESAFE_API_KEY not set"


async def test_abstains_when_none_option_wins(
    tools: list[Tool], server_desc: dict[str, str]
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        criteria = body["questions"]["tool"]["criteria"]
        assert "__none__" in criteria
        probs = {k: (0.7 if k == "__none__" else 0.3 / (len(criteria) - 1)) for k in criteria}
        return httpx.Response(
            200, json={"answers": {"tool": {"probabilities": probs}}, "usage": {"input_tokens": 5}}
        )

    router = build_router(
        {"name": "j", "type": "jev", "api_key": "k", "_transport": httpx.MockTransport(handler)}
    )
    res = await router.route("cancel my hotel booking", tools, server_desc)
    assert res.abstained and res.top1 is None
    assert res.raw is not None and res.raw["p_none"] == pytest.approx(0.7)
    assert "__none__" not in dict(res.ranked)


async def test_abstain_can_be_disabled(tools: list[Tool], server_desc: dict[str, str]) -> None:
    cap: list[dict[str, Any]] = []
    res = await jev(cap, mode="flat", allow_abstain=False).route("q", tools, server_desc)
    assert "__none__" not in cap[0]["body"]["questions"]["tool"]["criteria"]
    assert not res.abstained


async def test_openrouter_dialect_and_measured_cost(
    tools: list[Tool], server_desc: dict[str, str]
) -> None:
    cap: list[dict[str, Any]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        cap.append(
            {"url": str(request.url), "body": body, "auth": request.headers["authorization"]}
        )
        opts = list(body["questions"]["tool"]["criteria"])
        probs = {o: (0.9 if o == "aws.search_docs" else 0.1 / (len(opts) - 1)) for o in opts}
        return httpx.Response(
            200,
            json={
                "model": "typesafe/jev-1.13-20260901",
                "answers": {
                    "tool": {
                        "type": "choice",
                        "choice": "aws.search_docs",
                        "probabilities": probs,
                        "confidence": 0.8,
                    }
                },
                "usage": {"input_tokens": 400, "output_tokens": 0, "cost": 0.0000168},
            },
        )

    router = build_router(
        {
            "name": "or",
            "type": "openrouter",
            "model": "openai/gpt-6-luna-decisions",
            "api_key": "or-key",
            "_transport": httpx.MockTransport(handler),
        }
    )
    res = await router.route("aws docs", tools, server_desc)
    assert cap[0]["url"] == "https://openrouter.ai/api/alpha/decisions"
    assert cap[0]["auth"] == "Bearer or-key"
    assert cap[0]["body"]["model"] == "openai/gpt-6-luna-decisions"  # sent verbatim
    assert cap[0]["body"]["questions"]["tool"]["type"] == "choice"
    assert res.top1 == "aws.search_docs"
    assert res.cost_usd == pytest.approx(0.0000168) and res.input_tokens == 400


def test_openrouter_needs_its_own_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    router = build_router({"name": "or", "type": "openrouter", "model": "typesafe/jev-1.13"})
    assert router.unavailable_reason() == "OPENROUTER_API_KEY not set"


def test_list_shaped_answers_are_normalised() -> None:
    from tooldiscoverybench.routers.jev.client import normalise_answers

    out = normalise_answers(
        [
            {
                "type": "choice",
                "name": "tool",
                "choice": "a",
                "probabilities": [
                    {"value": "a", "probability": 0.7},
                    {"value": "b", "probability": 0.3},
                ],
            }
        ]
    )
    assert out["tool"]["probabilities"] == {"a": 0.7, "b": 0.3}


def scripted(server: dict[str, float], tool: dict[str, float] | None = None) -> httpx.MockTransport:
    """Fixed server-question probabilities; tool questions get ``tool`` or a uniform spread."""

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        answers = {}
        for qname, question in body["questions"].items():
            opts = list(question["criteria"])
            if qname == "server":
                probs = {o: server.get(o, 0.0) for o in opts}
            elif tool:
                probs = {o: tool.get(o, 0.0) for o in opts}
            else:
                probs = {o: 1 / len(opts) for o in opts}
            answers[qname] = {"probabilities": probs}
        usage = {"input_tokens": 1, "cost": 0.001}
        return httpx.Response(200, json={"answers": answers, "usage": usage})

    return httpx.MockTransport(handler)


def jev_with(transport: httpx.MockTransport, **cfg: Any) -> Any:
    return build_router(
        {"name": "j", "type": "jev", "api_key": "k", "_transport": transport, **cfg}
    )


async def test_factored_abstain_compares_none_with_best_server(
    tools: list[Tool], server_desc: dict[str, str]
) -> None:
    # aws 0.5 beats NONE 0.3, but the joint P(aws) * P(tool | aws) = 0.25 is below 0.3
    t = scripted({"aws": 0.5, "ms": 0.1, "kiwi": 0.1, "__none__": 0.3})
    res = await jev_with(t, mode="factored").route("aws docs", tools, server_desc)
    assert not res.abstained
    assert res.top1 in {"aws.search_docs", "aws.list_regions"}


async def test_hierarchical_abstain_compares_none_with_best_server(
    tools: list[Tool], server_desc: dict[str, str]
) -> None:
    # NONE wins the server question; a confident second-stage tool pick must not override it
    t = scripted(
        {"aws": 0.3, "ms": 0.1, "kiwi": 0.1, "__none__": 0.5},
        {"aws.search_docs": 0.9, "aws.list_regions": 0.1},
    )
    res = await jev_with(t, mode="hierarchical", top_servers=1).route("q", tools, server_desc)
    assert res.abstained and res.top1 is None


async def test_hierarchical_single_candidate_keeps_pruned_tools(
    tools: list[Tool], server_desc: dict[str, str]
) -> None:
    t = scripted({"kiwi": 0.8, "aws": 0.1, "ms": 0.05, "__none__": 0.05})
    res = await jev_with(t, mode="hierarchical", top_servers=1).route("flights", tools, server_desc)
    assert res.top1 == "kiwi.search-flight" and res.calls == 1
    assert {tid for tid, _ in res.ranked} == {tool.id for tool in tools}


async def test_flat_tournament_counts_cost_of_every_round() -> None:
    many = [Tool(f"s{i // 50}", f"t{i}", "x") for i in range(600)]
    res = await jev_with(scripted({}), mode="flat").route("q", many, {})
    assert res.calls == 4
    assert res.cost_usd == pytest.approx(0.004)
