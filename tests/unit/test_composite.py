"""escalate and shortlist routers, with scripted child routers (no network)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, ClassVar

import pytest

from tooldiscoverybench.core.models import RouteResult, Tool
from tooldiscoverybench.evaluation.metrics import summarize
from tooldiscoverybench.routers import Router, build_router, register
from tooldiscoverybench.routers.composite import decision_confidence


class Scripted(Router):
    """Ranks tools by the order of ``prefer``; optional abstain, p_none, cost, error."""

    calibrated = True
    seen: ClassVar[list[list[str]]] = []

    async def route(
        self, question: str, tools: list[Tool], server_desc: dict[str, str]
    ) -> RouteResult:
        Scripted.seen.append([t.id for t in tools])
        if self.cfg.get("error"):
            return RouteResult([], 5.0, error="boom")
        prefer: list[str] = self.cfg.get("prefer", [])
        ids = sorted((t.id for t in tools), key=lambda i: prefer.index(i) if i in prefer else 99)
        p_top = float(self.cfg.get("p_top", 0.9))
        rest = (1 - p_top) / max(1, len(ids) - 1)
        ranked = [(tid, p_top if i == 0 else rest) for i, tid in enumerate(ids)]
        return RouteResult(
            ranked,
            float(self.cfg.get("latency", 10.0)),
            True,
            input_tokens=100,
            raw={"p_none": self.cfg.get("p_none", 0.01)},
            abstained=bool(self.cfg.get("abstain")),
            cost_usd=self.cfg.get("cost"),
        )


register("scripted", f"{__name__}:Scripted")


def cascade(primary: dict[str, Any], fallback: dict[str, Any], below: float = 0.8) -> Any:
    return build_router(
        {
            "name": "esc",
            "type": "escalate",
            "escalate_below": below,
            "primary": {"type": "scripted", **primary},
            "fallback": {"type": "scripted", **fallback},
        }
    )


async def test_confident_primary_is_not_escalated(
    tools: list[Tool], server_desc: dict[str, str]
) -> None:
    router = cascade(
        {"prefer": ["aws.search_docs"], "p_top": 0.9, "cost": 0.001},
        {"prefer": ["ms.docs_search"], "cost": 0.01},
    )
    res = await router.route("q", tools, server_desc)
    assert res.top1 == "aws.search_docs"
    assert res.extra is not None and res.extra["escalated"] is False
    assert res.cost_usd == pytest.approx(0.001) and res.latency_ms == pytest.approx(10.0)
    assert res.extra["fallback_cost_usd"] is None


async def test_unsure_primary_escalates_and_sums_cost_and_latency(
    tools: list[Tool], server_desc: dict[str, str]
) -> None:
    router = cascade(
        {"prefer": ["aws.search_docs"], "p_top": 0.5, "cost": 0.001, "latency": 10},
        {"prefer": ["ms.docs_search"], "cost": 0.01, "latency": 500},
    )
    res = await router.route("q", tools, server_desc)
    assert res.top1 == "ms.docs_search"
    assert res.extra is not None and res.extra["escalated"] is True
    assert res.extra["primary_top1"] == "aws.search_docs"
    assert res.extra["primary_conf"] == pytest.approx(0.5)
    assert res.cost_usd == pytest.approx(0.011)
    assert res.latency_ms == pytest.approx(510.0)
    assert res.calls == 2 and not res.calibrated


async def test_abstain_uses_none_probability(
    tools: list[Tool], server_desc: dict[str, str]
) -> None:
    sure = cascade({"abstain": True, "p_none": 0.95}, {"prefer": ["ms.docs_search"]})
    res = await sure.route("q", tools, server_desc)
    assert res.abstained and res.extra is not None and not res.extra["escalated"]

    unsure = cascade({"abstain": True, "p_none": 0.55}, {"prefer": ["ms.docs_search"]})
    res = await unsure.route("q", tools, server_desc)
    assert not res.abstained and res.top1 == "ms.docs_search"
    assert res.raw is not None and res.raw["p_none"] == pytest.approx(0.55)


async def test_failed_fallback_keeps_primary(
    tools: list[Tool], server_desc: dict[str, str]
) -> None:
    router = cascade({"prefer": ["aws.list_regions"], "p_top": 0.4}, {"error": True})
    res = await router.route("q", tools, server_desc)
    assert res.error is None and res.top1 == "aws.list_regions"
    assert res.extra is not None and res.extra["fallback_error"] == "boom"


def test_decision_confidence_on_error() -> None:
    assert decision_confidence(RouteResult([], 1.0, error="x")) == 0.0
    assert decision_confidence(RouteResult([("a.b", 0.7)], 1.0)) == pytest.approx(0.7)


def test_escalate_needs_fallback() -> None:
    with pytest.raises(ValueError):
        build_router({"name": "e", "type": "escalate", "primary": {"type": "scripted"}})


def test_escalation_rate_in_summary() -> None:
    base = {
        "router": "esc",
        "suite": "s",
        "catalog_size": "fixed",
        "error": None,
        "answerable": True,
        "latency_ms": 1.0,
        "calls": 1,
        "calibrated": False,
        "input_tokens": 1,
        "cost_usd": 0.001,
        "abstained": False,
        "correct": True,
        "correct@1": True,
        "lenient@1": True,
        "correct@3": True,
        "rr": 1.0,
        "server_correct@1": True,
        "p_top1": 0.9,
        "refused": 0,
    }
    rows = [{**base, "escalated": True}, {**base, "escalated": False}]
    assert summarize(rows)[0]["escalation_rate"] == pytest.approx(0.5)
    assert summarize([base])[0]["escalation_rate"] is None


async def test_shortlist_keeps_top_k_and_zero_fills(
    tools: list[Tool], server_desc: dict[str, str]
) -> None:
    Scripted.seen = []
    router = build_router(
        {
            "name": "sl",
            "type": "shortlist",
            "k": 2,
            "retriever": {"type": "scripted", "prefer": ["kiwi.search-flight", "aws.search_docs"]},
            "decider": {"type": "scripted", "prefer": ["aws.search_docs"], "cost": 0.0001},
        }
    )
    res = await router.route("q", tools, server_desc)
    # the decider only saw the two shortlisted tools, in catalog order
    assert Scripted.seen[-1] == ["aws.search_docs", "kiwi.search-flight"]
    assert res.top1 == "aws.search_docs"
    assert [tid for tid, _ in res.ranked][:2] == ["aws.search_docs", "kiwi.search-flight"]
    assert {tid for tid, _ in res.ranked} == {t.id for t in tools}
    assert all(p == 0.0 for _, p in res.ranked[2:])
    assert res.cost_usd == pytest.approx(0.0001)
    assert res.extra is not None and res.extra["shortlist_k"] == 2


async def test_shortlist_skips_retriever_for_small_catalogs(
    tools: list[Tool], server_desc: dict[str, str]
) -> None:
    Scripted.seen = []
    router = build_router(
        {
            "name": "sl",
            "type": "shortlist",
            "k": 8,
            "retriever": {"type": "scripted"},
            "decider": {"type": "scripted", "prefer": ["ms.docs_search"], "abstain": True},
        }
    )
    res = await router.route("q", tools, server_desc)
    assert len(Scripted.seen) == 1 and res.abstained


def test_shortlist_rejects_bad_k() -> None:
    with pytest.raises(ValueError):
        build_router({"name": "sl", "type": "shortlist", "k": 0})


def test_escalation_curve_replay(tmp_path: Path) -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "escalation_curve", Path(__file__).parents[2] / "scripts" / "escalation_curve.py"
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    def row(conf: float, primary: str | None, fallback: str | None, gold: list[str]) -> dict:
        return {
            "item": "x",
            "gold": gold,
            "primary_conf": conf,
            "primary_top1": primary,
            "primary_abstained": primary is None,
            "escalated": fallback is not None or conf < 0.9,
            "fallback_top1": fallback,
            "fallback_abstained": fallback is None,
            "fallback_error": None,
            "primary_cost_usd": 0.0001,
            "fallback_cost_usd": 0.005 if conf < 0.9 else None,
        }

    rows = [
        row(0.95, "a.x", None, ["a.x"]),  # confident, right
        row(0.6, "a.y", "a.x", ["a.x"]),  # unsure, fallback fixes it
        row(0.85, "a.y", "a.y", ["a.x"]),  # unsure, both wrong
        row(0.4, "a.x", None, []),  # unsure on a no-tool question, fallback abstains
    ]
    at0, at07, at09 = mod.curve(rows, [0.0, 0.7, 0.9])
    assert at0["escalation_rate"] == 0 and at0["accuracy"] == pytest.approx(0.25)
    assert at07["escalation_rate"] == pytest.approx(0.5) and at07["accuracy"] == pytest.approx(0.75)
    assert at09["escalation_rate"] == pytest.approx(0.75)
    assert mod.pick([at0, at07, at09], 0.5) == at07
    with pytest.raises(ValueError):
        mod.curve(rows, [0.99])
    json.dumps(at09)


def test_strands_cost_from_token_prices() -> None:
    from tooldiscoverybench.routers.strands.router import StrandsRouter

    priced = StrandsRouter(price_input_per_m="2.0", price_output_per_m=10)
    assert priced._cost(1000, 100) == pytest.approx(0.003)
    assert StrandsRouter()._cost(1000, 100) is None
