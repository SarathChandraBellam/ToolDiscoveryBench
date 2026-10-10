"""Import a browser agent's raw chat replies as labeler votes.

Paste everything the agent replied (all batches, notes included) into one text file, then:

    uv run python scripts/labeling/import_votes.py --family cross --agent chatgpt --input chatgpt_raw.txt

Extracts every ```jsonl / ```json code block, validates ids and tool_ids against the shared
pack, and writes data/golden/<family>/labeling/votes_<agent>.jsonl. Reports missing,
duplicate and invalid entries instead of silently dropping them.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from _common import SHARED, labeling_dir, read_jsonl, write_jsonl

BLOCK = re.compile(r"```(?:jsonl|json)?\s*\n(.*?)```", re.S)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--family", default="cross")
    parser.add_argument("--agent", required=True, help="e.g. claude, chatgpt, grok")
    parser.add_argument("--input", required=True, type=Path)
    args = parser.parse_args()

    valid_ids = {q["id"] for q in read_jsonl(SHARED / "questions_blind.jsonl")}
    valid_tools = {
        t["tool_id"] for t in json.loads((SHARED / "catalog_for_labelers.json").read_text())
    }

    votes: dict[str, dict] = {}
    problems: list[str] = []
    for block in BLOCK.findall(args.input.read_text()):
        for raw_line in block.splitlines():
            line = raw_line.strip()
            if not line.startswith("{"):
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                problems.append(f"bad JSON ({exc.msg}): {line[:80]}")
                continue
            qid, tool = row.get("id"), row.get("tool_id")
            if qid not in valid_ids:
                problems.append(f"unknown id: {qid}")
                continue
            if tool is not None and tool not in valid_tools:
                problems.append(f"{qid}: unknown tool_id {tool!r}")
                continue
            if qid in votes:
                problems.append(f"{qid}: duplicate, keeping the first")
                continue
            row["acceptable_alternatives"] = [
                a for a in row.get("acceptable_alternatives") or [] if a in valid_tools
            ]
            row.setdefault("arguments", {})
            row.setdefault("confidence", 0.5)
            votes[qid] = row

    missing = sorted(valid_ids - set(votes))
    out = labeling_dir(args.family) / f"votes_{args.agent}.jsonl"
    write_jsonl(out, [votes[q] for q in sorted(votes)])
    print(f"{len(votes)}/{len(valid_ids)} votes -> {out}")
    for p in problems:
        print("  !", p)
    if missing:
        print(
            f"  missing {len(missing)}: {', '.join(missing[:15])}{' ...' if len(missing) > 15 else ''}"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
