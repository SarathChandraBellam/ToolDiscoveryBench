"""Types shared by every decision-model backend (TypeSafe Jev, OpenAI Decisions, ...)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


class DecisionError(RuntimeError):
    """A decision request failed (HTTP error, refusal, retries exhausted)."""


@dataclass
class ChoiceQuestion:
    """A single-choice question: ``criteria`` maps option value -> description."""

    instructions: str
    criteria: dict[str, str]


@dataclass
class DecisionResponse:
    """Answers normalised to ``{question_name: {"probabilities": {value: p}, ...}}``."""

    answers: dict[str, dict[str, Any]]
    input_tokens: int
    latency_ms: float
    raw: dict[str, Any] = field(default_factory=dict)

    def probabilities(self, question: str) -> dict[str, float]:
        """Probability per option for one question (falls back to the pick alone)."""
        answer = self.answers.get(question, {})
        probs = {k: float(v) for k, v in (answer.get("probabilities") or {}).items()}
        if not probs:
            pick = answer.get("choice", answer.get("value"))
            if pick is not None:
                probs = {str(pick): float(answer.get("confidence", 1.0))}
        return probs


class DecisionClient(Protocol):
    """What a decision router needs from a backend."""

    api_key_env: str
    max_options: int

    @property
    def configured(self) -> bool: ...

    async def ask(self, state: str, questions: dict[str, ChoiceQuestion]) -> DecisionResponse: ...

    async def aclose(self) -> None: ...
