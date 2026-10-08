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
