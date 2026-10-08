"""Core data types shared by every part of the bench."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class Tool:
    server: str
    name: str
    description: str = ""
    input_schema: dict[str, Any] = field(default_factory=dict, hash=False, compare=False)
    synthetic: bool = False  # True for distractor-pack tools that don't exist on a real server

    @property
    def id(self) -> str:
        """Canonical id used everywhere in gold labels and results: `server.tool`."""
        return f"{self.server}.{self.name}"

    def short_desc(self, max_chars: int = 300) -> str:
        d = " ".join((self.description or "").split())
        return d if len(d) <= max_chars else d[: max_chars - 1] + "…"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GoldenItem:
    """One benchmark question.

    gold        tool ids that are the right first call. EMPTY means no tool in the
                catalog fits, and the correct behaviour is to abstain.
    acceptable  tool ids that are a reasonable but not ideal first call (counted by the
                lenient metric only).
    candidates  when set, the exact catalog this question must be shown (e.g. the tools
                of the servers "connected" in that scenario). When None, the runner
                samples a catalog of each configured size.
    """

    id: str
    question: str
    gold: list[str]
    tags: list[str] = field(default_factory=list)
    notes: str = ""
    acceptable: list[str] = field(default_factory=list)
    candidates: list[str] | None = None
    meta: dict[str, Any] = field(default_factory=dict)

    @property
    def gold_servers(self) -> set[str]:
        return {g.split(".", 1)[0] for g in self.gold}

    @property
    def expects_abstain(self) -> bool:
        return not self.gold


@dataclass
class RouteResult:
    """What a router returns for one question.

    ranked: best-first list of (tool_id, score). Scores are probabilities when the
    router is calibrated (Jev), otherwise whatever the router produces (BM25 scores,
    cosine sims, self-reported LLM confidence). `calibrated` tells metrics which.
    abstained: the router decided no tool fits (ranked may still hold its scores).
    """

    ranked: list[tuple[str, float]]
    latency_ms: float
    calibrated: bool = False
    input_tokens: int | None = None
    output_tokens: int | None = None
    calls: int = 1  # upstream API calls made for this question
    error: str | None = None
    raw: dict[str, Any] | None = None
    abstained: bool = False
    cost_usd: float | None = None  # provider-reported cost, when the API returns one

    @property
    def top1(self) -> str | None:
        """The tool the router would call, or None when it abstains."""
        if self.abstained:
            return None
        return self.ranked[0][0] if self.ranked else None
