"""Combine votes + execution results into one record per question for the judge.

uv run python scripts/labeling/build_judge_pack.py --family claude
"""

from __future__ import annotations

from collections import Counter

from _common import SHARED, labeling_dir, parse_family_args, read_jsonl, write_jsonl

SNIPPET = 700


def main() -> None:
    args = parse_family_args(__doc__ or "")
    lab = labeling_dir(args.family)
    models = args.models
    votes = {m: {v["id"]: v for v in read_jsonl(lab / f"votes_{m}.jsonl")} for m in models}
    execs = {(r["id"], r["tool_id"]): r for r in read_jsonl(lab / "executions.jsonl")}
    blind = read_jsonl(SHARED / "questions_blind.jsonl")
    out = []
    for q in blind:
        qid = q["id"]
        firsts = Counter(votes[m][qid]["tool_id"] for m in models)
        alts = Counter(a for m in models for a in votes[m][qid].get("acceptable_alternatives", []))
        calls = []
        for tool_id, n in firsts.most_common():
            ex = execs.get((qid, tool_id), {})
            calls.append(
                {
                    "tool_id": tool_id,
                    "first_pick_votes": n,
                    "arguments": ex.get("arguments"),
                    "status": ex.get("status"),
                    "result_snippet": (
                        ex.get("snippet") or ex.get("error") or ex.get("reason") or ""
                    )[:SNIPPET],
                }
            )
        out.append(
            {
                "id": qid,
                "question": q["question"],
                "executed_first_calls": calls,
                "alternatives_mentioned": dict(alts.most_common()),
                "mean_confidence": round(
                    sum(votes[m][qid]["confidence"] for m in models) / len(models), 2
                ),
            }
        )
    write_jsonl(lab / "judge_pack.jsonl", out)
    print(len(out), "records ->", lab / "judge_pack.jsonl")


if __name__ == "__main__":
    main()
