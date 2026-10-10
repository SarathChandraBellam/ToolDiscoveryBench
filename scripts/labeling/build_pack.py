"""Build the shared, model-agnostic labeling pack.

Writes to ``data/golden/shared/``:
  candidates.jsonl          every question with the drafter's intended tools (never shown to labelers)
  questions_blind.jsonl     id + question only, shuffled
  catalog_for_labelers.json the real tools with descriptions and input schemas

    uv run python scripts/labeling/build_pack.py
"""

from __future__ import annotations

import json
import random

from _common import GOLDEN, ROOT, SHARED, read_jsonl, write_jsonl

SOURCES = (
    (GOLDEN / "claude" / "golden_v1.jsonl", "v1"),
    (SHARED / "drafted_questions_v2.jsonl", "drafted"),
)


def main() -> None:
    items = []
    for path, source in SOURCES:
        for d in read_jsonl(path):
            items.append(
                {
                    "id": d["id"],
                    "question": d["question"],
                    "intended": d.get("gold") or d.get("intended"),
                    "tags": d.get("tags", []),
                    "source": source,
                }
            )

    catalog = json.loads((ROOT / "data" / "catalog" / "public.json").read_text())
    tools = [
        {
            "tool_id": f"{server}.{t['name']}",
            "server": server,
            "server_description": spec.get("description", ""),
            "description": t["description"],
            "input_schema": t["input_schema"],
        }
        for server, spec in catalog["servers"].items()
        for t in spec["tools"]
    ]

    blind = [{"id": i["id"], "question": i["question"]} for i in items]
    random.Random(7).shuffle(blind)
    write_jsonl(SHARED / "candidates.jsonl", items)
    write_jsonl(SHARED / "questions_blind.jsonl", blind)
    (SHARED / "catalog_for_labelers.json").write_text(json.dumps(tools, indent=1))
    print(f"{len(items)} questions, {len(tools)} tools -> {SHARED}")


if __name__ == "__main__":
    main()
