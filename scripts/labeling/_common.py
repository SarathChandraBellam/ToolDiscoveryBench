"""Paths and CLI arguments shared by the labeling scripts.

Layout::

    data/golden/
      shared/                    model-agnostic inputs
        candidates.jsonl         every question + the drafter's intended tools (hidden from labelers)
        questions_blind.jsonl    id + question only, shuffled (what labelers see)
        catalog_for_labelers.json
        drafted_questions_v2.jsonl
        prompts/labeler.md, prompts/judge.md
      <family>/                  one folder per labeling model family (claude, openai, ...)
        golden_v2.jsonl          accepted questions
        review_v2.jsonl          questions a human must look at
        labeling_report_v2.json
        labeling/                votes_<model>.jsonl, executions.jsonl, judge_pack.jsonl, judgments.jsonl
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
GOLDEN = ROOT / "data" / "golden"
SHARED = GOLDEN / "shared"

# Labeler names per family, weakest first. Other families must pass --models.
DEFAULT_MODELS = {
    "claude": ["haiku", "sonnet", "opus"],
}


def family_dir(family: str) -> Path:
    return GOLDEN / family


def labeling_dir(family: str) -> Path:
    return family_dir(family) / "labeling"


def parse_family_args(description: str) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--family", default="claude", help="model family folder under data/golden")
    parser.add_argument(
        "--models",
        default=None,
        help="comma-separated labeler names (files are votes_<name>.jsonl); " "defaults per family",
    )
    args = parser.parse_args()
    args.models = args.models.split(",") if args.models else DEFAULT_MODELS.get(args.family, [])
    if not args.models:
        parser.error(f"no default labelers for family {args.family!r}; pass --models")
    return args


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.open() if line.strip()]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))
