"""HTTP client for TypeSafe Jev decision requests.

Two dialects:

``typesafe``   POST ``{base_url}/v1/systemone`` (native API, questions use ``type``)
``decisions``  POST ``{base_url}{path}`` on a ``/v1/decisions`` gateway such as
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
        api_key_env: str = "TYPESAFE_API_KEY",
        timeout: float = 30.0,
        max_retries: int = 3,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        native = dialect == "typesafe"
        default_base = "https://api.typesafe.ai" if native else "http://localhost:8080"
        self.dialect = dialect
        self.model = model
        self.base_url = (base_url or os.environ.get("TYPESAFE_BASE_URL") or default_base).rstrip(
            "/"
        )
        self.path = path or ("/v1/systemone" if native else "/v1/decisions")
        self.question_type_key = question_type_key or ("type" if native else "kind")
        self.api_key_env = api_key_env
        self._http = BearerHTTP(
            api_key or os.environ.get(api_key_env, ""), api_key_env, timeout, max_retries, transport
        )

    @property
    def configured(self) -> bool:
        return self._http.configured

    @property
    def model_id(self) -> str:
        if self.dialect == "typesafe":
            return self.model.split("/", 1)[-1]  # native API takes bare ids
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
        usage = data.get("usage", {})
        tokens = int(usage.get("input_tokens", usage.get("prompt_tokens", 0)) or 0)
        return DecisionResponse(data.get("answers", {}), tokens, elapsed_ms, data)

    async def aclose(self) -> None:
        await self._http.aclose()
