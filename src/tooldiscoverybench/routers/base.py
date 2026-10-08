"""Router interface.

A router answers one question: given a user request and a tool catalog, which tool
should be called first? It returns a best-first ranking and how long that took.
"""

from __future__ import annotations

import abc
import re
from typing import Any

from tooldiscoverybench.core.models import RouteResult, Tool

Ranked = list[tuple[str, float]]

_UNSAFE_NAME_CHARS = re.compile(r"[^A-Za-z0-9_-]")


class Router(abc.ABC):
    #: set by the registry from the config entry's ``name``
    name: str = "router"
    #: True when ranking scores are real probabilities (enables calibration metrics)
    calibrated: bool = False

    def __init__(self, **cfg: Any) -> None:
        self.cfg = cfg

    def unavailable_reason(self) -> str | None:
        """Why this router can't run (e.g. missing API key), or None if usable."""
        return None

    async def setup(self, all_tools: list[Tool], server_desc: dict[str, str]) -> None:  # noqa: B027
        """Called once before a run with the full catalog (e.g. to build an index)."""

    @abc.abstractmethod
    async def route(
        self, question: str, tools: list[Tool], server_desc: dict[str, str]
    ) -> RouteResult: ...

    async def aclose(self) -> None:  # noqa: B027
        """Release network clients and other resources."""


def safe_tool_name(tool_id: str, max_len: int = 64) -> str:
    """Map ``server.tool`` to a provider-safe tool name.

    Bedrock, Anthropic and OpenAI restrict tool names to ``[A-Za-z0-9_-]{1,64}``.
    """
    return _UNSAFE_NAME_CHARS.sub("_", tool_id.replace(".", "__", 1))[:max_len]


def catalog_lines(tools: list[Tool], desc_chars: int) -> str:
    return "\n".join(f"- {t.id}: {t.short_desc(desc_chars)}" for t in tools)
