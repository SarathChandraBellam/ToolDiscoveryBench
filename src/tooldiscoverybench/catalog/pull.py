"""Snapshot `tools/list` from every MCP server listed in a servers config."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

from tooldiscoverybench.mcp.client import MCPHttpClient

Logger = Callable[[str], None]


def _truthy(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() not in ("", "0", "false", "no", "off")
    return bool(value)


def _has_value(value: Any) -> bool:
    """Drop headers whose env var was empty, e.g. ``Bearer `` with no token."""
    text = str(value or "").strip()
    return bool(text) and text.lower() not in ("bearer", "basic")


def pull_catalog(
    servers_cfg: dict[str, Any],
    only: list[str] | None = None,
    log: Logger = print,
) -> dict[str, Any]:
    """Connect to every enabled server and return a catalog snapshot dict."""
    out: dict[str, Any] = {"pulled_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "servers": {}}
    for name, cfg in servers_cfg.get("servers", {}).items():
        if only and name not in only:
            continue
        if not _truthy(cfg.get("enabled", True)):
            log(f"  - {name}: disabled, skipping")
            continue
        headers = {k: str(v) for k, v in (cfg.get("headers") or {}).items() if _has_value(v)}
        if _truthy(cfg.get("auth", False)) and not headers:
            log(f"  - {name}: needs auth but no credentials in env, skipping")
            continue

        client = MCPHttpClient(cfg["url"], headers=headers, timeout=float(cfg.get("timeout", 30)))
        try:
            tools = client.list_tools()
        except Exception as exc:  # noqa: BLE001 - report and keep pulling the rest
            log(f"  x {name}: {exc}")
            out["servers"][name] = {"url": cfg["url"], "error": str(exc), "tools": []}
            continue

        log(
            f"  ok {name}: {len(tools)} tools "
            f"(init {client.timings_ms.get('initialize', 0):.0f} ms, "
            f"list {client.timings_ms.get('tools_list', 0):.0f} ms)"
        )
        out["servers"][name] = {
            "url": cfg["url"],
            "auth": _truthy(cfg.get("auth", False)),
            "description": cfg.get("description", ""),
            "server_info": client.server_info,
            "instructions": client.instructions,
            "timings_ms": client.timings_ms,
            "tools": [
                {
                    "name": t["name"],
                    "description": t.get("description", ""),
                    "input_schema": t.get("inputSchema", {}),
                }
                for t in tools
            ],
        }
    return out
