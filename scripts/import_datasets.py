"""Convert the raw `datasets_v1` drop into the benchmark's golden format.

    uv run python scripts/import_datasets.py [--raw data/raw/datasets_v1] [--out data/golden/datasets_v1]

Raw layout (one folder per scenario, one file per generator model plus all.jsonl):
  one_server/             each question is shown only the tools of 1 connected server
  multi_server/           the same questions, with 4 connected servers
  multi_server_confused/  the multi_server subset whose catalogs contain confusable tools

Raw record -> golden record:
  tool_id (or null)          -> gold ([] means no connected tool fits: correct answer is abstain)
  candidates[label=right]    -> gold (same as tool_id; asserted)
  candidates[label=acceptable] -> acceptable
  candidates[*].tool_id      -> candidates (the fixed catalog for that question)
  model, generator_tool_id, judge_picks, agreement, connected_servers -> meta
Server names are mapped onto the pulled catalog (aws_knowledge -> aws-knowledge, astro -> astro-docs).
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = ("one_server", "multi_server", "multi_server_confused")
SERVER_MAP = {
    "aws_knowledge": "aws-knowledge",
    "cloudflare_docs": "cloudflare-docs",
    "microsoft_learn": "microsoft-learn",
    "astro": "astro-docs",
}


def map_tool(tool_id: str | None) -> str | None:
    if tool_id is None:
        return None
    server, name = tool_id.split(".", 1)
    return f"{SERVER_MAP.get(server, server)}.{name}"


def family(model: str) -> str:
    return (
        "claude" if model.startswith("claude") else "openai" if model.startswith("gpt") else "other"
    )


def convert(raw: dict[str, Any], scenario: str) -> dict[str, Any]:
    gold_tool = map_tool(raw["tool_id"])
    right = [map_tool(c["tool_id"]) for c in raw["candidates"] if c["label"] == "right"]
    if gold_tool is not None and right != [gold_tool]:
        raise ValueError(f"{raw['id']}: tool_id {gold_tool} but right-labelled {right}")
    if gold_tool is None and right:
        raise ValueError(f"{raw['id']}: no tool_id but right-labelled {right}")

    tags = [scenario, f"generator:{family(raw['model'])}"]
    if gold_tool is None:
        tags.append("no_tool")
    if raw.get("confused"):
        tags.append("confusable")
    if raw.get("agreement") != "unanimous":
        tags.append("judges_split")
    if (
        gold_tool
        and raw.get("generator_tool_id")
        and map_tool(raw["generator_tool_id"]) != gold_tool
    ):
        tags.append("relabelled")

    return {
        "id": raw["id"],
        "question": raw["question"],
        "gold": [gold_tool] if gold_tool else [],
        "acceptable": [
            map_tool(c["tool_id"]) for c in raw["candidates"] if c["label"] == "acceptable"
        ],
        "candidates": [map_tool(c["tool_id"]) for c in raw["candidates"]],
        "tags": tags,
        "meta": {
            "generator": raw["model"],
            "generator_tool_id": map_tool(raw.get("generator_tool_id")),
            "judge_picks": {k: map_tool(v) for k, v in (raw.get("judge_picks") or {}).items()},
            "agreement": raw.get("agreement"),
            "connected_servers": [SERVER_MAP.get(s, s) for s in raw["connected_servers"]],
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=ROOT / "data/raw/datasets_v1")
    parser.add_argument("--out", type=Path, default=ROOT / "data/golden/datasets_v1")
    args = parser.parse_args()

    catalog = json.loads((ROOT / "data/catalog/public.json").read_text())
    known = {f"{s}.{t['name']}" for s, v in catalog["servers"].items() for t in v["tools"]}

    args.out.mkdir(parents=True, exist_ok=True)
    summary: dict[str, Any] = {}
    for scenario in SCENARIOS:
        rows = [
            convert(json.loads(line), scenario)
            for line in (args.raw / scenario / "all.jsonl").open()
            if line.strip()
        ]
        unknown = sorted(
            {t for r in rows for t in r["gold"] + r["acceptable"] + r["candidates"]} - known
        )
        if unknown:
            raise SystemExit(f"{scenario}: tools not in data/catalog/public.json: {unknown}")
        (args.out / f"{scenario}.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
        summary[scenario] = {
            "questions": len(rows),
            "no_tool": sum(not r["gold"] for r in rows),
            "with_acceptable": sum(bool(r["acceptable"]) for r in rows),
            "judges_split": sum("judges_split" in r["tags"] for r in rows),
            "catalog_size": dict(sorted(Counter(len(r["candidates"]) for r in rows).items())),
            "generators": dict(Counter(r["meta"]["generator"] for r in rows)),
            "gold_tools_covered": len({g for r in rows for g in r["gold"]}),
        }
    (args.out / "summary.json").write_text(json.dumps(summary, indent=2))
    print(
        json.dumps(
            {
                k: {
                    kk: v[kk]
                    for kk in (
                        "questions",
                        "no_tool",
                        "with_acceptable",
                        "judges_split",
                        "gold_tools_covered",
                    )
                }
                for k, v in summary.items()
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
