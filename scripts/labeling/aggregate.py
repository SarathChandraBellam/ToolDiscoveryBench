"""Merge labeler votes, execution results, judge decisions and the drafter's intent into
`data/golden/<family>/golden_v2.jsonl` (accepted) and `review_v2.jsonl` (needs a human).

    uv run python scripts/labeling/aggregate.py --family claude

Gold rule
---------
gold = judge gold
     + any alternative that a majority of labelers named as acceptable AND the drafter
       also intended (two independent sources agreeing it is a valid first call)

A question goes to review when the judge marked it `review`, or when the final gold shares
no tool with the drafter's intended tools (labelers + judge disagree with the question's author).
"""

from __future__ import annotations

import json
from collections import Counter
from typing import Any

from _common import SHARED, family_dir, labeling_dir, parse_family_args, read_jsonl, write_jsonl


def main() -> None:
    args = parse_family_args(__doc__ or "")
    lab = labeling_dir(args.family)
    models = args.models
    majority = len(models) // 2 + 1
    cands = {c["id"]: c for c in read_jsonl(SHARED / "candidates.jsonl")}
    votes = {m: {v["id"]: v for v in read_jsonl(lab / f"votes_{m}.jsonl")} for m in models}
    judge = {j["id"]: j for j in read_jsonl(lab / "judgments.jsonl")}

    accepted: list[dict[str, Any]] = []
    review: list[dict[str, Any]] = []
    stats: Counter[str] = Counter()
    per_model_vs_final: Counter[str] = Counter()

    for qid, cand in cands.items():
        j = judge[qid]
        picks = {m: votes[m][qid]["tool_id"] for m in models}
        alt_counts = Counter(
            a for m in models for a in votes[m][qid].get("acceptable_alternatives", [])
        )
        intended = set(cand["intended"] or [])

        gold = list(j["gold"])
        for alt, n in alt_counts.items():
            if n >= majority and alt in intended and alt not in gold:
                gold.append(alt)

        agreement = Counter(picks.values()).most_common(1)[0][1]
        stats[f"agree_{agreement}of{len(models)}"] += 1
        for m in models:
            per_model_vs_final[m] += picks[m] in gold

        disagrees_with_drafter = not (set(gold) & intended)
        status = "review" if j["status"] == "review" or disagrees_with_drafter else "accept"
        stats[status] += 1
        stats["multi_gold"] += len(gold) > 1
        stats["drafter_disagreement"] += disagrees_with_drafter

        tags = list(cand["tags"])
        if len(gold) > 1 and "multi_valid" not in tags:
            tags.append("multi_valid")
        record = {
            "id": qid,
            "question": cand["question"],
            "gold": gold,
            "tags": tags,
            "provenance": {
                "source": cand["source"],
                "first_picks": picks,
                "agreement": f"{agreement}/{len(models)}",
                "drafter_intended": sorted(intended),
                "result_useful": j["result_useful"],
                "judge_status": j["status"],
            },
        }
        if j.get("question_issue"):
            record["provenance"]["question_issue"] = j["question_issue"]
        if j.get("notes"):
            record["notes"] = j["notes"]
        (review if status == "review" else accepted).append(record)

    out = family_dir(args.family)
    write_jsonl(out / "golden_v2.jsonl", accepted)
    write_jsonl(out / "review_v2.jsonl", review)

    n = len(cands)
    report = {
        "family": args.family,
        "labelers": models,
        "questions": n,
        "accepted": len(accepted),
        "review": len(review),
        "first_pick_agreement": {k: v for k, v in stats.items() if k.startswith("agree_")},
        "multi_gold": stats["multi_gold"],
        "final_gold_disagrees_with_drafter": stats["drafter_disagreement"],
        "labeler_first_pick_in_final_gold": {m: f"{per_model_vs_final[m]}/{n}" for m in models},
    }
    (out / "labeling_report_v2.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
