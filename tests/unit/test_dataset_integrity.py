"""Golden data integrity: no answer leaks, stable question ids, frozen split, abstention share."""

from __future__ import annotations

import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import pytest
import yaml

from tooldiscoverybench.golden import leaked_gold_names, question_id

ROOT = Path(__file__).resolve().parents[2]
SUITES = {
    s["name"]: ROOT / s["golden"]
    for s in yaml.safe_load((ROOT / "configs/bench.yaml").read_text())["suites"]
}


def rows(name: str) -> list[dict[str, Any]]:
    return [json.loads(line) for line in SUITES[name].read_text().splitlines() if line.strip()]


def test_leak_detector() -> None:
    gold = ["svelte.playground-link"]
    assert leaked_gold_names("make a Playground link for this", gold) == gold
    assert leaked_gold_names("make a playground_link", gold) == gold
    assert leaked_gold_names("share it in the online REPL", gold) == []
    assert leaked_gold_names("whoami", ["huggingface.fs"]) == []  # too short to count
    assert question_id("gpt-5.5-013@multi_server") == "gpt-5.5-013"


@pytest.mark.parametrize("suite", sorted(SUITES))
def test_no_gold_tool_name_in_question(suite: str) -> None:
    leaks = [
        (r["id"], hit) for r in rows(suite) if (hit := leaked_gold_names(r["question"], r["gold"]))
    ]
    assert not leaks, f"gold tool name appears verbatim in the question: {leaks}"


def test_qid_is_shared_and_consistent_across_suites() -> None:
    seen: dict[str, tuple[str, list[str], str]] = {}
    per_suite: dict[str, set[str]] = defaultdict(set)
    for suite in SUITES:
        for r in rows(suite):
            assert r["qid"] == question_id(r["id"])
            per_suite[suite].add(r["qid"])
            key = (r["question"], r["gold"], r["split"])
            assert seen.setdefault(r["qid"], key) == key, f"{r['qid']} differs in {suite}"
    assert per_suite["one_server"] == per_suite["multi_server"]
    assert per_suite["multi_confused"] <= per_suite["multi_server"]


def test_split_is_frozen_and_about_30_percent() -> None:
    test_ids = set((ROOT / "data/golden/splits/test_qids.txt").read_text().split())
    canon = [json.loads(line) for line in (ROOT / "data/golden/questions.jsonl").open()]
    assert {c["qid"] for c in canon if c["split"] == "test"} == test_ids
    assert 0.27 <= len(test_ids) / len(canon) <= 0.33
    for suite in SUITES:
        for r in rows(suite):
            assert (r["qid"] in test_ids) == (r["split"] == "test")
            assert f"split:{r['split']}" in r["tags"]


def test_rewritten_rows_keep_original_text() -> None:
    for suite in SUITES:
        for r in rows(suite):
            if "rewritten" in r["tags"]:
                assert r["meta"]["original_question"] != r["question"]


def test_build_script_outputs_are_up_to_date() -> None:
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts/build_benchmark.py"), "--check"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
