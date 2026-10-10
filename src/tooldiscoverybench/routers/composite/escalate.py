"""Cascade router: a cheap calibrated primary answers when it is confident, a stronger
fallback answers the rest.

The primary's *decision confidence* is the probability of what it decided: its top tool's
probability when it picks a tool, or its NONE probability when it abstains (decision
routers report it as ``raw["p_none"]``). Below ``escalate_below`` the question goes to the
fallback and the fallback's answer is used. Latency is the sum of both calls (they run in
sequence) and cost is the sum of both.

Config::

    - name: escalate-jev-sonnet
      type: escalate
      escalate_below: 0.8
      primary:  {type: openrouter, model: typesafe/jev-1.13, mode: flat}
      fallback: {type: strands, provider: huggingface, base_url: https://openrouter.ai/api/v1,
                 api_key_env: OPENROUTER_API_KEY, model_id: anthropic/claude-sonnet-5.5,
                 mode: structured}

Every row records ``escalated``, the primary's confidence and pick, and both costs and
latencies, so a lower threshold can be replayed offline from one run at a high threshold
(see ``scripts/escalation_curve.py``).
"""

from __future__ import annotations

from typing import Any

from tooldiscoverybench.core.models import RouteResult, Tool
from tooldiscoverybench.routers.base import Router
from tooldiscoverybench.routers.composite.common import build_child

DEFAULT_PRIMARY: dict[str, Any] = {
    "type": "openrouter",
    "model": "typesafe/jev-1.13",
    "mode": "flat",
}


def decision_confidence(res: RouteResult) -> float:
    """Probability of the primary's own decision (tool pick or abstain); 0 on error."""
    if res.error:
        return 0.0
    if res.abstained:
        p_none = (res.raw or {}).get("p_none")
        return float(p_none) if p_none is not None else 0.0
    return float(res.ranked[0][1]) if res.ranked else 0.0


class EscalateRouter(Router):
    #: mixes calibrated primary probabilities with the fallback's self-reported confidence
    calibrated = False

    def __init__(self, **cfg: Any) -> None:
        super().__init__(**cfg)
        self.escalate_below = float(cfg.get("escalate_below", 0.8))
        self.primary = build_child(cfg.get("primary") or DEFAULT_PRIMARY, "primary")
        if not cfg.get("fallback"):
            raise ValueError("escalate router needs a 'fallback' router config")
        self.fallback = build_child(cfg["fallback"], "fallback")

    def unavailable_reason(self) -> str | None:
        for role, child in (("primary", self.primary), ("fallback", self.fallback)):
            reason = child.unavailable_reason()
            if reason:
                return f"{role}: {reason}"
        return None

    async def setup(self, all_tools: list[Tool], server_desc: dict[str, str]) -> None:
        await self.primary.setup(all_tools, server_desc)
        await self.fallback.setup(all_tools, server_desc)

    async def aclose(self) -> None:
        await self.primary.aclose()
        await self.fallback.aclose()

    async def route(
        self, question: str, tools: list[Tool], server_desc: dict[str, str]
    ) -> RouteResult:
        first = await self.primary.route(question, tools, server_desc)
        conf = decision_confidence(first)
        extra: dict[str, Any] = {
            "escalated": False,
            "primary_conf": conf,
            "primary_top1": first.top1,
            "primary_abstained": first.abstained,
            "primary_error": first.error,
            "primary_cost_usd": first.cost_usd,
            "primary_latency_ms": first.latency_ms,
            "fallback_cost_usd": None,
            "fallback_latency_ms": None,
            "fallback_top1": None,
            "fallback_abstained": None,
            "fallback_error": None,
        }
        if conf >= self.escalate_below:
            return _with(first, first, None, extra)

        second = await self.fallback.route(question, tools, server_desc)
        extra.update(
            escalated=True,
            fallback_cost_usd=second.cost_usd,
            fallback_latency_ms=second.latency_ms,
            fallback_top1=second.top1,
            fallback_abstained=second.abstained,
            fallback_error=second.error,
        )
        # a failed fallback keeps the primary's answer (and its error, if it had one)
        answer = first if second.error else second
        return _with(answer, first, second, extra)


def _sum(*values: float | None) -> float | None:
    present = [v for v in values if v is not None]
    return sum(present) if present else None


def _with(
    answer: RouteResult, first: RouteResult, second: RouteResult | None, extra: dict[str, Any]
) -> RouteResult:
    calls = [first] + ([second] if second else [])
    raw = dict(answer.raw or {})
    # p_none in results.jsonl stays the primary's (the calibrated NONE probability)
    raw["p_none"] = (first.raw or {}).get("p_none")
    return RouteResult(
        ranked=answer.ranked,
        latency_ms=sum(c.latency_ms for c in calls),
        calibrated=False,
        input_tokens=_sum(*(c.input_tokens for c in calls)),  # type: ignore[arg-type]
        output_tokens=_sum(*(c.output_tokens for c in calls)),  # type: ignore[arg-type]
        calls=sum(c.calls for c in calls),
        error=answer.error,
        raw=raw,
        abstained=answer.abstained,
        cost_usd=_sum(*(c.cost_usd for c in calls)),
        extra=extra,
    )
