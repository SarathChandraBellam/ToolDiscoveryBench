"""HTTP client for the OpenAI Decisions API (public beta).

    POST https://api.openai.com/v1/decisions
    {"model": "gpt-6-luna",
     "input": "<user request>",
     "questions": [{"type": "choice", "name": "tool", "instructions": "...",
                    "choices": [{"value": "aws-knowledge.aws___list_regions", "description": "..."}]}]}

The response has ``answers`` in question order. A choice answer carries ``choice``,
``probabilities`` (a list of ``{value, probability}``) and ``confidence``; a model may also
return ``{"type": "refusal", ...}`` instead of an answer. Answers are normalised to the same
``DecisionResponse`` shape the Jev client returns, so both share one router.

Plain httpx is used (no SDK dependency); the official SDK equivalent is
``OpenAI().decisions.create(model=..., input=..., questions=[...])``.
"""

from __future__ import annotations

import os
from typing import Any

import httpx

from tooldiscoverybench.routers.decisions.http import BearerHTTP
from tooldiscoverybench.routers.decisions.types import (
    ChoiceQuestion,
    DecisionError,
    DecisionResponse,
)

DEFAULT_MODEL = "gpt-6-luna"


class OpenAIDecisionsClient:
    def __init__(
        self,
        *,
        model: str = DEFAULT_MODEL,
        base_url: str | None = None,
        api_key: str | None = None,
        api_key_env: str = "OPENAI_API_KEY",
        organization: str | None = None,
        project: str | None = None,
        max_options: int = 255,
        timeout: float = 30.0,
        max_retries: int = 3,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.model = model
        self.base_url = (
            base_url or os.environ.get("OPENAI_BASE_URL") or "https://api.openai.com/v1"
        ).rstrip("/")
        self.api_key_env = api_key_env
        self.max_options = max_options
        headers = {}
        org = organization or os.environ.get("OPENAI_ORG_ID")
        proj = project or os.environ.get("OPENAI_PROJECT_ID")
        if org:
            headers["OpenAI-Organization"] = org
        if proj:
            headers["OpenAI-Project"] = proj
        self._http = BearerHTTP(
            api_key or os.environ.get(api_key_env, ""),
            api_key_env,
            timeout,
            max_retries,
            transport,
            headers,
        )

    @property
    def configured(self) -> bool:
        return self._http.configured

    def build_body(self, state: str, questions: dict[str, ChoiceQuestion]) -> dict[str, Any]:
        return {
            "model": self.model,
            "input": state,
            "questions": [
                {
                    "type": "choice",
                    "name": name,
                    "instructions": q.instructions,
                    "choices": [{"value": v, "description": d} for v, d in q.criteria.items()],
                }
                for name, q in questions.items()
            ],
        }

    @staticmethod
    def normalise(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
        answers: dict[str, dict[str, Any]] = {}
        for answer in data.get("answers", []):
            name = answer.get("name")
            if answer.get("type") == "refusal":
                raise DecisionError(f"refusal on question {name!r}: {answer.get('refusal')}")
            probs = answer.get("probabilities") or []
            answers[name] = {
                "choice": answer.get("choice"),
                "confidence": answer.get("confidence"),
                "probabilities": {
                    str(p["value"]): float(p["probability"]) for p in probs if "value" in p
                },
            }
        return answers

    async def ask(self, state: str, questions: dict[str, ChoiceQuestion]) -> DecisionResponse:
        data, elapsed_ms = await self._http.post_json(
            f"{self.base_url}/decisions", self.build_body(state, questions)
        )
        usage = data.get("usage") or {}
        tokens = int(usage.get("input_tokens", usage.get("prompt_tokens", 0)) or 0)
        return DecisionResponse(self.normalise(data), tokens, elapsed_ms, data)

    async def aclose(self) -> None:
        await self._http.aclose()
