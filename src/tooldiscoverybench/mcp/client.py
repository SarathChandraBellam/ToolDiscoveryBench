"""Minimal MCP Streamable-HTTP client: initialize + tools/list (with pagination).

Kept dependency-light on purpose (just httpx) so catalog pulls don't break when the
official SDK changes its transport API, and so we can time each round-trip precisely.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any

import httpx

PROTOCOL_VERSION = "2025-06-18"


class MCPError(RuntimeError):
    pass


def _parse_body(resp: httpx.Response) -> dict[str, Any]:
    """Servers may answer with plain JSON or a one-shot SSE stream."""
    ctype = resp.headers.get("content-type", "")
    text = resp.text
    if "text/event-stream" in ctype:
        last: dict[str, Any] | None = None
        for line in text.splitlines():
            if line.startswith("data:"):
                payload = line[5:].strip()
                if not payload:
                    continue
                try:
                    msg = json.loads(payload)
                except json.JSONDecodeError:
                    continue
                if "result" in msg or "error" in msg:
                    last = msg
        if last is None:
            raise MCPError(f"no JSON-RPC response in SSE stream: {text[:200]!r}")
        return last
    data: dict[str, Any] = resp.json()
    return data


@dataclass
class MCPHttpClient:
    url: str
    headers: dict[str, str] = field(default_factory=dict)
    timeout: float = 30.0
    session_id: str | None = None
    server_info: dict[str, Any] = field(default_factory=dict)
    instructions: str | None = None
    timings_ms: dict[str, float] = field(default_factory=dict)
    _id: int = 0

    def _headers(self) -> dict[str, str]:
        h = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "MCP-Protocol-Version": PROTOCOL_VERSION,
            **self.headers,
        }
        if self.session_id:
            h["Mcp-Session-Id"] = self.session_id
        return h

    def _rpc(
        self, client: httpx.Client, method: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        self._id += 1
        body = {"jsonrpc": "2.0", "id": self._id, "method": method, "params": params or {}}
        resp = client.post(self.url, json=body, headers=self._headers())
        if resp.status_code in (401, 403):
            raise MCPError(f"{method}: HTTP {resp.status_code} (auth required or rejected)")
        resp.raise_for_status()
        sid = resp.headers.get("mcp-session-id")
        if sid:
            self.session_id = sid
        msg = _parse_body(resp)
        if "error" in msg:
            raise MCPError(f"{method}: {msg['error']}")
        result: dict[str, Any] = msg["result"]
        return result

    def _notify(self, client: httpx.Client, method: str) -> None:
        body = {"jsonrpc": "2.0", "method": method}
        client.post(self.url, json=body, headers=self._headers())

    def list_tools(self) -> list[dict[str, Any]]:
        with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
            t0 = time.perf_counter()
            init = self._rpc(
                client,
                "initialize",
                {
                    "protocolVersion": PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {"name": "tooldiscoverybench", "version": "0.1.0"},
                },
            )
            self.timings_ms["initialize"] = (time.perf_counter() - t0) * 1000
            self.server_info = init.get("serverInfo", {})
            self.instructions = init.get("instructions")
            self._notify(client, "notifications/initialized")

            tools: list[dict[str, Any]] = []
            cursor: str | None = None
            t1 = time.perf_counter()
            while True:
                params = {"cursor": cursor} if cursor else {}
                result = self._rpc(client, "tools/list", params)
                tools.extend(result.get("tools", []))
                cursor = result.get("nextCursor")
                if not cursor:
                    break
            self.timings_ms["tools_list"] = (time.perf_counter() - t1) * 1000
            return tools
