"""Report extras: bootstrap CI, per-split and per-author tables."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tooldiscoverybench.evaluation.report import bootstrap_ci, write_report


def test_bootstrap_ci_brackets_the_mean_and_is_seeded() -> None:
    xs = [1.0] * 70 + [0.0] * 30
    lo, hi = bootstrap_ci(xs) or (0.0, 0.0)
    assert lo < 0.7 < hi
    assert lo > 0.55 and hi < 0.85
    assert bootstrap_ci(xs) == bootstrap_ci(xs)  # deterministic
    assert bootstrap_ci([1.0, 1.0, 1.0]) == (1.0, 1.0)
    assert bootstrap_ci([]) is None


def _row(item: str, correct: bool, generator: str, split: str) -> dict[str, object]:
    return {
        "router": "bm25",
        "suite": "s",
        "catalog_size": "fixed",
        "item": item,
        "repeat": 0,
        "error": None,
        "answerable": True,
        "correct": correct,
        "correct@1": correct,
        "abstained": False,
        "top1": "a.x" if correct else "a.y",
        "p_top1": None,
        "gold": ["a.x"],
        "tags": [f"split:{split}"],
        "generator": generator,
    }


def test_report_has_ci_split_and_contamination_tables(tmp_path: Path) -> None:
    rows = [
        _row("q1", True, "gpt-5.6-sol", "test"),
        _row("q2", False, "claude-haiku-4-5", "dev"),
        _row("q3", True, "claude-haiku-4-5", "test"),
        _row("q4", True, "gpt-5.5", "dev"),
    ]
    (tmp_path / "results.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    (tmp_path / "summary.json").write_text(json.dumps({"summary": [], "by_tag": {}}))

    text = write_report(tmp_path).read_text()

    assert "95% bootstrap confidence intervals" in text
    ci_line = next(line for line in text.splitlines() if line.startswith("| bm25 | s | fixed | 4"))
    assert "75.0%" in ci_line and "| 2 | 100.0% |" in ci_line  # all 4, then test split only
    assert "Accuracy by question author (exact model)" in text
    kept = next(ln for ln in text.splitlines() if "| 4 | 75.0% | 75.0% | 3 |" in ln)
    assert "66.7%" in kept  # gpt-5.6-sol's question dropped


@pytest.mark.parametrize("exclude", [(), ("nobody",)])
def test_contamination_table_skipped_when_nothing_excluded(
    tmp_path: Path, exclude: tuple[str, ...]
) -> None:
    (tmp_path / "results.jsonl").write_text(json.dumps(_row("q1", True, "gpt-5.5", "dev")) + "\n")
    (tmp_path / "summary.json").write_text(json.dumps({"summary": [], "by_tag": {}}))
    assert "contaminated" not in write_report(tmp_path, exclude).read_text()
