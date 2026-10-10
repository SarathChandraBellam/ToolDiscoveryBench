"""How a tool is described to a decision router as one ``choice`` option.

``plain`` (default) is the original text: ``[server] name: <upstream description>`` cut to
``desc_chars``. ``rich`` uses hand-written hints from ``data/catalog/option_hints.json`` so
look-alike tools (search vs read, list vs get, resolve vs query) are told apart::

    [server] name: <summary> Use when: <...>. Not when: <...>. Key args: <...>.

Tools without a hint (e.g. synthetic distractors) fall back to the plain text.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tooldiscoverybench.core.models import Tool

DEFAULT_HINTS_PATH = "data/catalog/option_hints.json"
OPTION_TEXT_MODES = ("plain", "rich")


@dataclass(frozen=True)
class OptionHint:
    summary: str = ""
    use_when: str = ""
    not_when: str = ""
    key_args: str = ""


def load_option_hints(path: str | Path = DEFAULT_HINTS_PATH) -> dict[str, OptionHint]:
    """``{"tools": {tool_id: {summary, use_when, not_when, key_args}}}`` -> hints by tool id."""
    data: dict[str, Any] = json.loads(Path(path).read_text())
    fields = set(OptionHint.__dataclass_fields__)
    out = {}
    for tool_id, raw in data["tools"].items():
        unknown = set(raw) - fields
        if unknown:
            raise ValueError(f"{tool_id}: unknown option hint field(s) {sorted(unknown)}")
        out[tool_id] = OptionHint(**raw)
    return out


def _sentence(text: str) -> str:
    text = " ".join(text.split()).rstrip()
    return text if not text or text.endswith((".", "!", "?")) else text + "."


def plain_option_text(tool: Tool, desc_chars: int) -> str:
    return f"[{tool.server}] {tool.name}: {tool.short_desc(desc_chars)}"


def rich_option_text(tool: Tool, hint: OptionHint | None, desc_chars: int) -> str:
    if hint is None:
        return plain_option_text(tool, desc_chars)
    parts = [_sentence(hint.summary) if hint.summary else tool.short_desc(desc_chars)]
    if hint.use_when:
        parts.append("Use when: " + _sentence(hint.use_when))
    if hint.not_when:
        parts.append("Not when: " + _sentence(hint.not_when))
    if hint.key_args:
        parts.append("Key args: " + _sentence(hint.key_args))
    return f"[{tool.server}] {tool.name}: " + " ".join(parts)


class OptionTextBuilder:
    """Builds option descriptions for one router; ``mode`` is ``plain`` or ``rich``."""

    def __init__(
        self,
        mode: str = "plain",
        desc_chars: int = 240,
        hints: dict[str, OptionHint] | None = None,
        hints_path: str | Path | None = None,
    ) -> None:
        if mode not in OPTION_TEXT_MODES:
            raise ValueError(f"option_text must be one of {OPTION_TEXT_MODES}, got {mode!r}")
        self.mode = mode
        self.desc_chars = desc_chars
        if mode == "rich" and hints is None:
            hints = load_option_hints(hints_path or DEFAULT_HINTS_PATH)
        self.hints = hints or {}

    def __call__(self, tool: Tool) -> str:
        if self.mode == "rich":
            return rich_option_text(tool, self.hints.get(tool.id), self.desc_chars)
        return plain_option_text(tool, self.desc_chars)
