"""HTTP client for TypeSafe Jev decision requests.

Two dialects:

``typesafe``   POST ``{base_url}/v1/systemone`` (native API, questions use ``type``)
``decisions``  POST ``{base_url}{path}`` on a ``/v1/decisions`` gateway such as
               Bifrost or NanoGPT (question key configurable, default ``kind``)
"""

from __future__ import annotations

import asyncio
import os
import time
from dataclasses import dataclass, field
from typing import Any

import httpx

MAX_CHOICE_OPTIONS = 255


class JevError(RuntimeError):
    """A Jev request failed (HTTP error, bad payload, retries exhausted)."""


@dataclass
class ChoiceQuestion:
    instructions: str
    criteria: dict[str, str]


@dataclass
class JevResponse:
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


class JevClient:
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
        self.api_key = api_key or os.environ.get(api_key_env, "")
        self.timeout = timeout
        self.max_retries = max_retries
        self._transport = transport
        self._http: httpx.AsyncClient | None = None

    @property
    def configured(self) -> bool:
        return bool(self.api_key) or self._transport is not None

    @property
    def model_id(self) -> str:
        if self.dialect == "typesafe":
            return self.model.split("/", 1)[-1]  # native API takes bare ids
        return self.model if "/" in self.model else f"typesafe/{self.model}"

    def _client(self) -> httpx.AsyncClient:
        if self._http is None:
            if not self.configured:
                raise JevError(f"no API key: set {self.api_key_env}")
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            self._http = httpx.AsyncClient(
                timeout=self.timeout, headers=headers, transport=self._transport
            )
        return self._http

    async def aclose(self) -> None:
        if self._http is not None:
            await self._http.aclose()
            self._http = None

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

    async def ask(self, state: str, questions: dict[str, ChoiceQuestion]) -> JevResponse:
        """Send one decision request, retrying on 429 / 529 with backoff."""
        body = self.build_body(state, questions)
        url = self.base_url + self.path
        delay = 0.5
        for attempt in range(self.max_retries + 1):
            started = time.perf_counter()
            resp = await self._client().post(url, json=body)
            elapsed_ms = (time.perf_counter() - started) * 1000
            if resp.status_code in (429, 529) and attempt < self.max_retries:
                await asyncio.sleep(delay)
                delay *= 2
                continue
            if resp.status_code >= 400:
                raise JevError(f"HTTP {resp.status_code}: {resp.text[:300]}")
            data: dict[str, Any] = resp.json()
            usage = data.get("usage", {})
            tokens = int(usage.get("input_tokens", usage.get("prompt_tokens", 0)) or 0)
            return JevResponse(data.get("answers", {}), tokens, elapsed_ms, data)
        raise JevError("retries exhausted")
