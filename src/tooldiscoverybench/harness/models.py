"""OpenRouter chat models for the harness: FREE models only, paced, counted.

Every model id must end with ``:free``; anything else raises before a request is made.
Requests are paced by a shared rate limiter, 429s are retried with exponential backoff by
the OpenAI client (which honours ``Retry-After``), and every HTTP request sent to OpenRouter
is counted so a run can stop before the daily free-model quota.
"""

from __future__ import annotations

import os
import threading
from typing import Any

import httpx

OPENROUTER_BASE = "https://openrouter.ai/api/v1"
KEY_ENV = "OPENROUTER_API_KEY"


class PaidModelError(ValueError):
    """Raised when a non-free model id reaches the harness."""


def assert_free(model_id: str) -> str:
    if not model_id.endswith(":free"):
        raise PaidModelError(
            f"{model_id!r} is not a free OpenRouter model (id must end with ':free'); "
            "the harness refuses to call paid models"
        )
    return model_id


class RequestCounter:
    """Thread-safe count of HTTP requests sent to OpenRouter (retries included)."""

    def __init__(self, start: int = 0) -> None:
        self._n = start
        self._lock = threading.Lock()

    def hook(self, request: httpx.Request) -> None:
        if "openrouter.ai" in request.url.host:
            with self._lock:
                self._n += 1

    @property
    def count(self) -> int:
        return self._n


_RATE_LIMITERS: dict[float, Any] = {}


def rate_limiter(requests_per_minute: float) -> Any:
    """One shared limiter per rate, so the agent and router models share the pace."""
    from langchain_core.rate_limiters import InMemoryRateLimiter

    if requests_per_minute not in _RATE_LIMITERS:
        _RATE_LIMITERS[requests_per_minute] = InMemoryRateLimiter(
            requests_per_second=requests_per_minute / 60.0,
            check_every_n_seconds=0.2,
            max_bucket_size=1,
        )
    return _RATE_LIMITERS[requests_per_minute]


def build_chat_model(
    model_id: str,
    counter: RequestCounter,
    *,
    requests_per_minute: float = 15.0,
    max_retries: int = 6,
    timeout: float = 180.0,
    max_tokens: int = 4096,
    temperature: float = 0.0,
) -> Any:
    from langchain_openai import ChatOpenAI

    assert_free(model_id)
    api_key = os.environ.get(KEY_ENV)
    if not api_key:
        raise RuntimeError(f"{KEY_ENV} is not set")
    http_client = httpx.Client(timeout=timeout, event_hooks={"request": [counter.hook]})
    return ChatOpenAI(
        model=model_id,
        base_url=OPENROUTER_BASE,
        api_key=api_key,  # type: ignore[arg-type]
        temperature=temperature,
        max_tokens=max_tokens,  # type: ignore[call-arg]
        max_retries=max_retries,
        timeout=timeout,
        http_client=http_client,
        rate_limiter=rate_limiter(requests_per_minute),
        default_headers={"X-Title": "ToolDiscoveryBench harness"},
    )


def free_quota(timeout: float = 20.0) -> dict[str, Any]:
    """``free_model_daily_requests`` from OpenRouter's ``/key`` endpoint (does not count)."""
    resp = httpx.get(
        f"{OPENROUTER_BASE}/key",
        headers={"Authorization": f"Bearer {os.environ.get(KEY_ENV, '')}"},
        timeout=timeout,
    )
    resp.raise_for_status()
    data = resp.json().get("data", {})
    quota = data.get("free_model_daily_requests") or {}
    return {
        "used": quota.get("used"),
        "limit": quota.get("limit"),
        "remaining": quota.get("remaining"),
    }
