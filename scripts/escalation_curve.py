"""Replay an ``escalate`` run at lower thresholds to pick ``escalate_below`` (dev split only).

Run the cascade once on dev with a high threshold, so every question that any lower
threshold would escalate already has a fallback answer::

    TDB_ESCALATE_BELOW=0.95 uv run tdb run --routers escalate-jev-sonnet --split dev \\
        --suites one_server,multi_server,multi_confused --out runs/dev-escalate
    uv run python scripts/escalation_curve.py runs/dev-escalate/results.jsonl --max-rate 0.25

For each threshold t <= the run's threshold, a row escalates iff primary_conf < t; it then
takes the fallback's answer (or keeps the primary's when the fallback failed). Prints the
curve (threshold, accuracy, top-1, escalation rate, $/1k) and the threshold with the best
accuracy whose escalation rate stays within ``--max-rate``.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Iterable
from typing import Any


def replay(row: dict[str, Any], threshold: float) -> tuple[bool, bool, bool, float]:
    """(escalated, correct, correct@1, cost) for one row at ``threshold``."""
    gold = set(row["gold"])
    escalate = float(row["primary_conf"]) < threshold
    use_fallback = escalate and row.get("escalated") and not row.get("fallback_error")
    if escalate and not row.get("escalated"):
        raise ValueError(f"row {row['item']} was not escalated in the run; lower the threshold")
    pick = row["fallback_top1"] if use_fallback else row["primary_top1"]
    abstained = bool(row["fallback_abstained"] if use_fallback else row["primary_abstained"])
    answerable = bool(gold)
    strict = answerable and not abstained and pick in gold
    correct = strict if answerable else abstained
    cost = float(row.get("primary_cost_usd") or 0.0)
    if escalate:
        cost += float(row.get("fallback_cost_usd") or 0.0)
    return escalate, correct, strict, cost


def curve(rows: list[dict[str, Any]], thresholds: Iterable[float]) -> list[dict[str, float]]:
    out = []
    ans = [r for r in rows if r["gold"]]
    for t in thresholds:
        res = [replay(r, t) for r in rows]
        res_ans = [replay(r, t) for r in ans]
        out.append(
            {
                "threshold": t,
                "accuracy": sum(c for _, c, _, _ in res) / len(res),
                "top1": sum(s for _, _, s, _ in res_ans) / max(1, len(res_ans)),
                "escalation_rate": sum(e for e, _, _, _ in res) / len(res),
                "usd_per_1k_q": sum(c for _, _, _, c in res) / len(res) * 1000,
            }
        )
    return out


def pick(points: list[dict[str, float]], max_rate: float) -> dict[str, float] | None:
    ok = [p for p in points if p["escalation_rate"] <= max_rate]
    return max(ok, key=lambda p: (p["accuracy"], -p["threshold"])) if ok else None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("results")
    ap.add_argument("--max-rate", type=float, default=0.25)
    ap.add_argument("--thresholds", default="0,0.3,0.4,0.5,0.6,0.7,0.75,0.8,0.85,0.9,0.95")
    args = ap.parse_args()
    with open(args.results) as fh:
        rows = [json.loads(line) for line in fh if line.strip()]
    rows = [r for r in rows if "primary_conf" in r and not r.get("primary_error")]
    if any("split:test" in r.get("tags", []) for r in rows):
        raise SystemExit("refusing to tune on split:test rows; run the cascade with --split dev")
    points = []
    for t in (float(x) for x in args.thresholds.split(",")):
        try:
            points += curve(rows, [t])
        except ValueError:  # above the run's own threshold: no fallback answer to replay
            break
    print("threshold  accuracy  top-1  escalated  $/1k")
    for p in points:
        print(
            f"{p['threshold']:>9.2f}  {p['accuracy']:8.1%}  {p['top1']:5.1%}  "
            f"{p['escalation_rate']:9.1%}  {p['usd_per_1k_q']:.3f}"
        )
    best = pick(points, args.max_rate)
    print("best within max rate:", json.dumps(best))


if __name__ == "__main__":
    main()
