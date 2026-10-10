"""Scoring. Every row in results.jsonl is one (router, suite, catalog_size, question, repeat).

Two kinds of question:
  answerable  gold is non-empty. Correct (strict) = the router did not abstain and its top
              pick is a gold tool. Lenient also accepts tools labelled ``acceptable``.
  no-tool     gold is empty (nothing in the catalog fits). Correct = the router abstained.

An abstention on an answerable question is a miss at every cutoff: rank, @3, @5 and MRR
ignore the ranking a router may still report after abstaining, so they agree with @1.

Calibration (ECE, Brier) covers every question where the router made a pick, including
no-tool questions, where any pick is wrong.
"""

from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Iterable
from typing import Any

from tooldiscoverybench.core.models import GoldenItem, RouteResult


def score_row(item: GoldenItem, res: RouteResult) -> dict[str, Any]:
    ids = [tid for tid, _ in res.ranked]
    gold = set(item.gold)
    ok_lenient = gold | set(item.acceptable)
    pick = res.top1  # None when abstained
    answerable = not item.expects_abstain
    rank = (
        None if res.abstained else next((i + 1 for i, tid in enumerate(ids) if tid in gold), None)
    )

    strict = answerable and pick is not None and pick in gold
    lenient = answerable and pick is not None and pick in ok_lenient
    return {
        "answerable": answerable,
        "rank": rank,  # 1-based rank of first gold tool in the ranking, None if absent
        "top1": pick,
        "correct": strict if answerable else res.abstained,
        "correct@1": strict,
        "lenient@1": lenient,
        "correct@3": answerable and rank is not None and rank <= 3,
        "correct@5": answerable and rank is not None and rank <= 5,
        "rr": 1.0 / rank if rank else 0.0,
        "server_correct@1": answerable
        and pick is not None
        and pick.split(".", 1)[0] in item.gold_servers,
        "p_top1": res.ranked[0][1] if res.ranked else None,
        "p_gold": max((p for tid, p in res.ranked if tid in gold), default=0.0),
        "p_none": (res.raw or {}).get("p_none"),
    }


def pct(xs: list[float], q: float) -> float | None:
    if not xs:
        return None
    xs = sorted(xs)
    k = (len(xs) - 1) * q
    lo, hi = math.floor(k), math.ceil(k)
    return xs[lo] if lo == hi else xs[lo] + (xs[hi] - xs[lo]) * (k - lo)


def ece(conf: list[float], correct: list[bool], bins: int = 10) -> float | None:
    """Expected calibration error of the top-1 probability."""
    if not conf:
        return None
    buckets: dict[int, list[tuple[float, bool]]] = defaultdict(list)
    for c, y in zip(conf, correct, strict=True):
        buckets[min(bins - 1, int(c * bins))].append((c, y))
    n = len(conf)
    return sum(
        len(b) / n * abs(sum(c for c, _ in b) / len(b) - sum(y for _, y in b) / len(b))
        for b in buckets.values()
    )


def _rate(rows: list[dict[str, Any]], key: str) -> float | None:
    return sum(bool(r.get(key)) for r in rows) / len(rows) if rows else None


def _mean(xs: list[float]) -> float | None:
    return sum(xs) / len(xs) if xs else None


def summarize(
    rows: Iterable[dict[str, Any]], price_per_m_input: dict[str, float] | None = None
) -> list[dict[str, Any]]:
    price_per_m_input = price_per_m_input or {}
    groups: dict[tuple[str, str, Any], list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        groups[(r["router"], r.get("suite", "default"), r["catalog_size"])].append(r)

    out = []
    for (router, suite, size), rs in sorted(
        groups.items(), key=lambda kv: (kv[0][0], kv[0][1], _size_key(kv[0][2]))
    ):
        ok = [r for r in rs if not r["error"]]
        ans = [r for r in ok if r.get("answerable", True)]
        none = [r for r in ok if not r.get("answerable", True)]
        lat = [r["latency_ms"] for r in ok]
        calibrated = any(r["calibrated"] for r in ok)
        # every pick the router actually made; a pick on a no-tool question is wrong
        scored = [r for r in ok if r["p_top1"] is not None and not r.get("abstained")]
        conf = [r["p_top1"] for r in scored]
        corr = [r["correct@1"] for r in scored]
        tok = [r["input_tokens"] for r in ok if r.get("input_tokens")]
        mean_tok = _mean(tok)
        price = price_per_m_input.get(router)
        out.append(
            {
                "router": router,
                "suite": suite,
                "catalog_size": size,
                "n": len(rs),
                "n_no_tool": len(none),
                "errors": len(rs) - len(ok),
                "accuracy": _rate(ok, "correct"),
                "top1": _rate(ans, "correct@1"),
                "lenient1": _rate(ans, "lenient@1"),
                "top3": _rate(ans, "correct@3"),
                "mrr": _mean([r["rr"] for r in ans]),
                "server_top1": _rate(ans, "server_correct@1"),
                "abstain_recall": _rate(none, "abstained"),
                "false_abstain": _rate(ans, "abstained"),
                # share of questions where the backend refused at least one sub-question
                "refusal_rate": _rate(ok, "refused"),
                "lat_p50_ms": pct(lat, 0.5),
                "lat_p95_ms": pct(lat, 0.95),
                "lat_mean_ms": _mean(lat),
                "calls_mean": _mean([r["calls"] for r in ok]),
                "in_tokens_mean": mean_tok,
                "usd_per_1k_q": _usd_per_1k(ok, mean_tok, price),
                "cost_source": (
                    "measured" if any(r.get("cost_usd") is not None for r in ok) else "estimated"
                ),
                "ece": ece(conf, corr) if calibrated else None,
                "brier": (
                    sum((c - y) ** 2 for c, y in zip(conf, corr, strict=True)) / len(conf)
                    if (calibrated and conf)
                    else None
                ),
                "conf_right": (
                    _mean([c for c, y in zip(conf, corr, strict=True) if y]) if calibrated else None
                ),
                "conf_wrong": (
                    _mean([c for c, y in zip(conf, corr, strict=True) if not y])
                    if calibrated
                    else None
                ),
            }
        )
    return out


def _usd_per_1k(
    rows: list[dict[str, Any]], mean_tok: float | None, price: float | None
) -> float | None:
    """Measured provider cost when reported (OpenRouter usage.cost), else tokens x config price."""
    measured = [float(r["cost_usd"]) for r in rows if r.get("cost_usd") is not None]
    if measured:
        return sum(measured) / len(measured) * 1000
    if mean_tok and price is not None:
        return mean_tok * price / 1e6 * 1000
    return None


def by_tag(rows: Iterable[dict[str, Any]]) -> dict[str, dict[str, float]]:
    """Accuracy per (router -> tag). ``hard_negative:*`` style tags collapse to the prefix."""
    acc: dict[tuple[str, str], list[bool]] = defaultdict(list)
    for r in rows:
        if r["error"]:
            continue
        for tag in r["tags"]:
            acc[
                (r["router"], tag.split(":", 1)[0] if tag.startswith("hard_negative") else tag)
            ].append(r["correct"])
    out: dict[str, dict[str, float]] = defaultdict(dict)
    for (router, tag), ys in acc.items():
        out[router][tag] = sum(ys) / len(ys)
    return dict(out)


def _size_key(s: Any) -> float:
    if s in ("all", "fixed"):
        return float("inf")
    return float(s)
