"""Running only one split of the golden set."""

from __future__ import annotations

import json
from pathlib import Path

from tooldiscoverybench.core.models import Tool
from tooldiscoverybench.evaluation.runner import load_suites


def test_split_keeps_only_tagged_questions(tmp_path: Path, tools: list[Tool]) -> None:
    golden = tmp_path / "g.jsonl"
    rows = [
        {"id": "a", "question": "?", "gold": ["aws.search_docs"], "tags": ["split:test"]},
        {"id": "b", "question": "?", "gold": ["aws.search_docs"], "tags": ["split:dev"]},
        {"id": "c", "question": "?", "gold": [], "tags": []},
    ]
    golden.write_text("\n".join(json.dumps(r) for r in rows))
    cfg = {"suites": [{"name": "s", "golden": str(golden)}]}

    assert [it.id for it in load_suites(cfg, tools, None)[0].items] == ["a", "b", "c"]
    assert [it.id for it in load_suites(cfg, tools, None, split="test")[0].items] == ["a"]
    assert [it.id for it in load_suites({**cfg, "split": "test"}, tools, None)[0].items] == ["a"]
    assert load_suites(cfg, tools, None, split="nope") == []
