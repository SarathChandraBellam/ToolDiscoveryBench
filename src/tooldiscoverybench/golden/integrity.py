"""Dataset integrity helpers shared by ``scripts/build_benchmark.py`` and the tests.

Pure data checks: nothing here touches routing or scoring.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable

#: tool names shorter than this are too generic to count as a leak (e.g. ``fs``)
MIN_LEAK_LEN = 5


def normalize(text: str) -> str:
    """Lowercase and treat ``_`` / ``-`` as spaces, so ``playground-link`` == ``playground link``."""
    return text.lower().replace("_", " ").replace("-", " ")


def tool_phrase(tool_id: str) -> str:
    """The tool part of ``server.tool``, normalized (``svelte.playground-link`` -> ``playground link``)."""
    return " ".join(normalize(tool_id.split(".", 1)[-1]).split())


def leaked_gold_names(question: str, gold: Iterable[str]) -> list[str]:
    """Gold tool ids whose tool name appears verbatim in the question (gives the answer away)."""
    q = normalize(question)
    return [g for g in gold if len(phrase := tool_phrase(g)) >= MIN_LEAK_LEN and phrase in q]


def question_id(item_id: str) -> str:
    """Suite-independent question id: ``gpt-5.5-013@multi_server`` -> ``gpt-5.5-013``."""
    return item_id.split("@", 1)[0]


def stable_rank(seed: int | str, key: str) -> int:
    """Deterministic, platform-independent sort key for seeded selection."""
    return int(hashlib.sha256(f"{seed}|{key}".encode()).hexdigest(), 16)
