"""OpenAI Decisions API router against a fake transport."""

from __future__ import annotations

import json
from typing import Any

import httpx
import pytest

from tooldiscoverybench.core.models import Tool
from tooldiscoverybench.routers import build_router


def fake_openai(captured: list[dict[str, Any]], refuse: bool = False) -> httpx.MockTransport:
    """Answers in the documented shape: answers[] with choice/probabilities[]/confidence."""

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        captured.append({"url": str(request.url), "body": body, "headers": dict(request.headers)})
        answers = []
        for q in body["questions"]:
            if refuse:
                answers.append({"type": "refusal", "name": q["name"], "refusal": "nope"})
                continue
            values = [c["value"] for c in q["choices"]]
            best = next((v for v in values if "search" in v or v == "aws"), values[0])
            rest = [v for v in values if v != best]
            probs = [{"value": best, "probability": 0.8}] + [
                {"value": v, "probability": 0.2 / len(rest)} for v in rest
            ]
            answers.append(
                {
                    "type": "choice",
                    "name": q["name"],
                    "choice": best,
                    "probabilities": probs,
                    "confidence": 0.8,
                }
            )
        return httpx.Response(200, json={"id": "dec_1", "answers": answers})

    return httpx.MockTransport(handler)


def router(cap: list[dict[str, Any]], **cfg: Any) -> Any:
    return build_router(
        {
            "name": "o",
            "type": "openai_decisions",
            "api_key": "sk-test",
            "_transport": fake_openai(cap, cfg.pop("refuse", False)),
            **cfg,
        }
    )


async def test_request_shape_and_ranking(tools: list[Tool], server_desc: dict[str, str]) -> None:
    cap: list[dict[str, Any]] = []
    res = await router(cap, project="proj_1").route("search aws docs", tools, server_desc)

    req = cap[0]
    assert req["url"] == "https://api.openai.com/v1/decisions"
    assert req["headers"]["authorization"] == "Bearer sk-test"
    assert req["headers"]["openai-project"] == "proj_1"
    body = req["body"]
    assert body["model"] == "gpt-6-luna"
    assert body["input"] == "search aws docs"
    q = body["questions"][0]
    assert q["type"] == "choice" and q["name"] == "tool"
    values = {c["value"] for c in q["choices"]}
    assert values == {t.id for t in tools} | {"__none__"}
    assert all(c["description"] for c in q["choices"])

    assert res.error is None and res.calibrated and not res.abstained
    assert res.top1 == "aws.search_docs"
    assert res.ranked[0][1] == pytest.approx(0.8)


async def test_factored_uses_one_request(tools: list[Tool], server_desc: dict[str, str]) -> None:
    cap: list[dict[str, Any]] = []
    res = await router(cap, mode="factored").route("aws docs", tools, server_desc)
    assert len(cap) == 1 and res.calls == 1
    names = [q["name"] for q in cap[0]["body"]["questions"]]
    assert names[0] == "server" and len(names) == 2
    assert res.top1 == "aws.search_docs"


async def test_refusal_is_an_error_row(tools: list[Tool], server_desc: dict[str, str]) -> None:
    res = await router([], refuse=True).route("q", tools, server_desc)
    assert res.error is not None and "refusal" in res.error


def test_missing_key_marks_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    r = build_router({"name": "o", "type": "openai_decisions"})
    assert r.unavailable_reason() == "OPENAI_API_KEY not set"
