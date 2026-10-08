"""Small shared HTTP helper: bearer auth, lazy client, retry on 429/529 with backoff."""

from __future__ import annotations

import asyncio
import time
from typing import Any

import httpx

from tooldiscoverybench.routers.decisions.types import DecisionError


class BearerHTTP:
    def __init__(
        self,
        api_key: str,
        api_key_env: str,
        timeout: float,
        max_retries: int,
        transport: httpx.AsyncBaseTransport | None,
        extra_headers: dict[str, str] | None = None,
    ) -> None:
        self.api_key = api_key
        self.api_key_env = api_key_env
        self.timeout = timeout
        self.max_retries = max_retries
        self._transport = transport
        self._extra = extra_headers or {}
        self._http: httpx.AsyncClient | None = None

    @property
    def configured(self) -> bool:
        return bool(self.api_key) or self._transport is not None

    def _client(self) -> httpx.AsyncClient:
        if self._http is None:
            if not self.configured:
                raise DecisionError(f"no API key: set {self.api_key_env}")
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                **self._extra,
            }
            self._http = httpx.AsyncClient(
                timeout=self.timeout, headers=headers, transport=self._transport
            )
        return self._http

    async def post_json(self, url: str, body: dict[str, Any]) -> tuple[dict[str, Any], float]:
        """POST and return ``(json, latency_ms of the successful attempt)``."""
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
                raise DecisionError(f"HTTP {resp.status_code}: {resp.text[:300]}")
            data: dict[str, Any] = resp.json()
            return data, elapsed_ms
        raise DecisionError("retries exhausted")

    async def aclose(self) -> None:
        if self._http is not None:
            await self._http.aclose()
            self._http = None
