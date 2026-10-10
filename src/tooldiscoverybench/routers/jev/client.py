"""HTTP client for TypeSafe Jev decision requests.

Dialects (all send TypeSafe's native request schema: ``model``, ``state``, ``questions``):

``typesafe``    POST ``https://api.typesafe.ai/v1/systemone`` with ``TYPESAFE_API_KEY``
``openrouter``  POST ``https://openrouter.ai/api/alpha/decisions`` with ``OPENROUTER_API_KEY``.
                Serves every decision model OpenRouter hosts, e.g. ``typesafe/jev-1.13``,
                ``~typesafe/jev-latest`` and ``openai/gpt-6-luna-decisions``. Model ids are
                sent verbatim and ``usage.cost`` (USD) is recorded.
``decisions``   POST ``{base_url}{path}`` on another ``/v1/decisions`` gateway such as
                Bifrost or NanoGPT (question key configurable, default ``kind``)
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

MAX_CHOICE_OPTIONS = 255

DIALECTS: dict[str, dict[str, str]] = {
    "typesafe": {
        "base_url": "https://api.typesafe.ai",
        "base_env": "TYPESAFE_BASE_URL",
        "path": "/v1/systemone",
        "qkey": "type",
        "key_env": "TYPESAFE_API_KEY",
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api",
        "base_env": "OPENROUTER_BASE_URL",
        "path": "/alpha/decisions",
        "qkey": "type",
        "key_env": "OPENROUTER_API_KEY",
    },
    "decisions": {
        "base_url": "http://localhost:8080",
        "base_env": "",
        "path": "/v1/decisions",
        "qkey": "kind",
        "key_env": "TYPESAFE_API_KEY",
    },
}

# kept for backwards compatibility with earlier imports
JevError = DecisionError
JevResponse = DecisionResponse


class JevClient:
    max_options = MAX_CHOICE_OPTIONS

    def __init__(
        self,
        *,
        dialect: str = "typesafe",
        model: str = "jev-latest",
        base_url: str | None = None,
        path: str | None = None,
        question_type_key: str | None = None,
        api_key: str | None = None,
        api_key_env: str | None = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        if dialect not in DIALECTS:
            raise ValueError(f"unknown dialect {dialect!r}; known: {sorted(DIALECTS)}")
        d = DIALECTS[dialect]
        self.dialect = dialect
        self.model = model
        env_base = os.environ.get(d["base_env"]) if d["base_env"] else None
        self.base_url = (base_url or env_base or d["base_url"]).rstrip("/")
        self.path = path or d["path"]
        self.question_type_key = question_type_key or d["qkey"]
        self.api_key_env = api_key_env or d["key_env"]
        extra = {}
        if dialect == "openrouter":
            # optional OpenRouter attribution headers
            extra = {
                "HTTP-Referer": os.environ.get("OPENROUTER_REFERER", ""),
                "X-Title": os.environ.get("OPENROUTER_TITLE", "ToolDiscoveryBench"),
            }
            extra = {k: v for k, v in extra.items() if v}
        self._http = BearerHTTP(
            api_key or os.environ.get(self.api_key_env, ""),
            self.api_key_env,
            timeout,
            max_retries,
            transport,
            extra,
        )

    @property
    def configured(self) -> bool:
        return self._http.configured

    @property
    def model_id(self) -> str:
        if self.dialect == "typesafe":
            return self.model.split("/", 1)[-1]  # native API takes bare ids
        if self.dialect == "openrouter":
            return self.model  # verbatim: typesafe/jev-1.13, ~typesafe/jev-latest, openai/...
        return self.model if "/" in self.model else f"typesafe/{self.model}"

    def build_body(self, state: str, questions: dict[str, ChoiceQuestion]) -> dict[str, Any]:
        return {
            "model": self.model_id,
            "state": state,
            "questions": {
                name: {
                    self.question_type_key: "choice",
                    "instructions": q.instructions,
                    "criteria": q.criteria,
                }
                for name, q in questions.items()
            },
        }

    async def ask(self, state: str, questions: dict[str, ChoiceQuestion]) -> DecisionResponse:
        """Send one decision request, retrying on 429 / 529 with backoff."""
        data, elapsed_ms = await self._http.post_json(
            self.base_url + self.path, self.build_body(state, questions)
        )
        usage = data.get("usage") or {}
        tokens = int(usage.get("input_tokens", usage.get("prompt_tokens", 0)) or 0)
        cost = usage.get("cost")
        return DecisionResponse(
            normalise_answers(data.get("answers", {})),
            tokens,
            elapsed_ms,
            data,
            cost_usd=float(cost) if cost is not None else None,
        )

    async def aclose(self) -> None:
        await self._http.aclose()


def normalise_answers(answers: Any) -> dict[str, dict[str, Any]]:
    """Accept TypeSafe's ``{name: answer}`` map or an OpenAI-style ``[answer, ...]`` list,
    and ``probabilities`` as either ``{value: p}`` or ``[{value, probability}, ...]``."""
    items = answers.items() if isinstance(answers, dict) else ((a.get("name"), a) for a in answers)
    out: dict[str, dict[str, Any]] = {}
    for name, answer in items:
        if answer.get("type") == "refusal":
            raise DecisionError(f"refusal on question {name!r}: {answer.get('refusal')}")
        probs = answer.get("probabilities")
        if isinstance(probs, list):
            probs = {str(p["value"]): float(p["probability"]) for p in probs if "value" in p}
        out[str(name)] = {**answer, "probabilities": probs or {}}
    return out
