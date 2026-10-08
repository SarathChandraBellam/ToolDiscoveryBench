"""Scoring. Every row in results.jsonl is one (router, catalog_size, question, repeat)."""

from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Iterable
from typing import Any

from tooldiscoverybench.core.models import GoldenItem, RouteResult


def score_row(item: GoldenItem, res: RouteResult) -> dict[str, Any]:
    ids = [tid for tid, _ in res.ranked]
    gold = set(item.gold)
    rank = next((i + 1 for i, tid in enumerate(ids) if tid in gold), None)
    top1 = ids[0] if ids else None
    return {
        "rank": rank,  # 1-based rank of first gold tool, None if absent
        "top1": top1,
        "correct@1": rank == 1,
        "correct@3": rank is not None and rank <= 3,
        "correct@5": rank is not None and rank <= 5,
        "rr": 1.0 / rank if rank else 0.0,
        "server_correct@1": top1 is not None and top1.split(".", 1)[0] in item.gold_servers,
        "p_top1": res.ranked[0][1] if res.ranked else None,
        "p_gold": max((p for tid, p in res.ranked if tid in gold), default=0.0),
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


def summarize(
    rows: Iterable[dict[str, Any]], price_per_m_input: dict[str, float] | None = None
) -> list[dict[str, Any]]:
    price_per_m_input = price_per_m_input or {}
    groups: dict[tuple[str, Any], list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        groups[(r["router"], r["catalog_size"])].append(r)
    out = []
    for (router, size), rs in sorted(
        groups.items(), key=lambda kv: (kv[0][0], _size_key(kv[0][1]))
    ):
        ok = [r for r in rs if not r["error"]]
        lat = [r["latency_ms"] for r in ok]
        calibrated = any(r["calibrated"] for r in ok)
        conf = [r["p_top1"] for r in ok if r["p_top1"] is not None]
        corr = [r["correct@1"] for r in ok if r["p_top1"] is not None]
        tok = [r["input_tokens"] for r in ok if r.get("input_tokens")]
        mean_tok = sum(tok) / len(tok) if tok else None
        price = price_per_m_input.get(router)
        n = max(1, len(ok))
        row = {
            "router": router,
            "catalog_size": size,
            "n": len(rs),
            "errors": len(rs) - len(ok),
            "top1": sum(r["correct@1"] for r in ok) / n,
            "top3": sum(r["correct@3"] for r in ok) / n,
            "top5": sum(r["correct@5"] for r in ok) / n,
            "mrr": sum(r["rr"] for r in ok) / n,
            "server_top1": sum(r["server_correct@1"] for r in ok) / n,
            "lat_p50_ms": pct(lat, 0.5),
            "lat_p95_ms": pct(lat, 0.95),
            "lat_mean_ms": sum(lat) / len(lat) if lat else None,
            "calls_mean": sum(r["calls"] for r in ok) / n,
            "in_tokens_mean": mean_tok,
            "usd_per_1k_q": (
                (mean_tok * price / 1e6 * 1000) if (mean_tok and price is not None) else None
            ),
            "ece": ece(conf, corr) if calibrated else None,
            "brier": (
                (sum((c - y) ** 2 for c, y in zip(conf, corr, strict=True)) / len(conf))
                if (calibrated and conf)
                else None
            ),
            "conf_right": (
                _mean([r["p_top1"] for r in ok if r["correct@1"] and r["p_top1"] is not None])
                if calibrated
                else None
            ),
            "conf_wrong": (
                _mean([r["p_top1"] for r in ok if not r["correct@1"] and r["p_top1"] is not None])
                if calibrated
                else None
            ),
        }
        out.append(row)
    return out


def by_tag(rows: Iterable[dict[str, Any]]) -> dict[str, dict[str, float]]:
    """top-1 accuracy per (router -> tag). Tags like `hard_negative:*` collapse to `hard_negative`."""
    acc: dict[tuple[str, str], list[bool]] = defaultdict(list)
    for r in rows:
        if r["error"]:
            continue
        for tag in r["tags"]:
            acc[(r["router"], tag.split(":", 1)[0])].append(r["correct@1"])
    out: dict[str, dict[str, float]] = defaultdict(dict)
    for (router, tag), ys in acc.items():
        out[router][tag] = sum(ys) / len(ys)
    return dict(out)


def _mean(xs: list[float]) -> float | None:
    return sum(xs) / len(xs) if xs else None


def _size_key(s: Any) -> float:
    return float("inf") if s == "all" else float(s)
