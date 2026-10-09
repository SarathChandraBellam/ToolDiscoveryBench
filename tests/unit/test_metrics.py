"""Scoring and summary metrics."""

from __future__ import annotations

import pytest

from tooldiscoverybench.core.models import GoldenItem, RouteResult
from tooldiscoverybench.evaluation.metrics import ece, pct, score_row, summarize


def test_score_row_ranks_first_gold_hit() -> None:
    item = GoldenItem("q", "?", ["a.x", "a.y"])
    score = score_row(item, RouteResult([("b.z", 0.6), ("a.y", 0.3)], 10, True))

    assert score["rank"] == 2
    assert not score["correct@1"] and score["correct@3"]
    assert score["rr"] == 0.5
    assert not score["server_correct@1"]


def test_ece_and_percentiles() -> None:
    assert ece([0.9, 0.9], [True, True]) == pytest.approx(0.1)
    assert ece([], []) is None
    assert pct([1.0, 2.0, 3.0, 4.0], 0.5) == pytest.approx(2.5)


def test_summary_cost_and_calibration() -> None:
    item = GoldenItem("q", "?", ["a.y"])
    score = score_row(item, RouteResult([("a.y", 0.8)], 5.0, True))
    rows = [
        {
            "router": "r",
            "catalog_size": 10,
            "error": None,
            "latency_ms": 5.0,
            "calls": 1,
            "calibrated": True,
            "input_tokens": 100,
            **score,
        }
    ]
    summary = summarize(rows, {"r": 0.042})[0]

    assert summary["top1"] == 1.0
    assert summary["usd_per_1k_q"] == pytest.approx(0.0042)
    assert summary["ece"] == pytest.approx(0.2)


def test_no_tool_question_scored_on_abstention() -> None:
    item = GoldenItem("q", "cancel my booking", [])
    assert score_row(item, RouteResult([("a.x", 0.9)], 1.0, abstained=True))["correct"]
    missed = score_row(item, RouteResult([("a.x", 0.9)], 1.0))
    assert not missed["correct"] and not missed["answerable"]


def test_lenient_accepts_acceptable_and_abstain_is_wrong_for_answerable() -> None:
    item = GoldenItem("q", "?", ["a.read"], acceptable=["a.search"])
    picked_acceptable = score_row(item, RouteResult([("a.search", 0.6), ("a.read", 0.4)], 1.0))
    assert not picked_acceptable["correct@1"] and picked_acceptable["lenient@1"]
    abstained = score_row(item, RouteResult([("a.read", 0.6)], 1.0, abstained=True))
    assert not abstained["correct"] and abstained["top1"] is None


def test_abstention_on_answerable_is_a_miss_at_every_cutoff() -> None:
    item = GoldenItem("q", "?", ["a.read"])
    score = score_row(item, RouteResult([("a.read", 0.6)], 1.0, True, abstained=True))
    assert score["rank"] is None and score["rr"] == 0.0
    assert not score["correct@3"] and not score["correct@5"]


def test_calibration_includes_picks_on_no_tool_questions() -> None:
    def row(item: GoldenItem, res: RouteResult) -> dict:
        return {
            "router": "r",
            "catalog_size": 10,
            "error": None,
            "latency_ms": 1.0,
            "calls": 1,
            "calibrated": True,
            "abstained": res.abstained,
            **score_row(item, res),
        }

    rows = [
        row(GoldenItem("a", "?", ["a.y"]), RouteResult([("a.y", 0.9)], 1.0, True)),
        # confident pick on a question where nothing fits: must count as a wrong pick
        row(GoldenItem("n", "?", []), RouteResult([("a.y", 0.9)], 1.0, True)),
    ]
    summary = summarize(rows)[0]
    assert summary["ece"] == pytest.approx(0.4)  # mean conf 0.9, accuracy 0.5
    assert summary["conf_wrong"] == pytest.approx(0.9)
