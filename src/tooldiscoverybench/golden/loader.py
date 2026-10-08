"""Golden question sets (JSONL): load and validate against a pulled catalog."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from tooldiscoverybench.core.models import GoldenItem, Tool


def load_golden(path: str | Path) -> list[GoldenItem]:
    """One JSON object per line: ``{"id", "question", "gold": [...], "tags": [...]}``.

    Blank lines and lines starting with ``//`` are ignored.
    """
    items: list[GoldenItem] = []
    for raw_line in Path(path).read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("//"):
            continue
        data = json.loads(line)
        items.append(
            GoldenItem(
                id=data["id"],
                question=data["question"],
                gold=list(data["gold"]),
                tags=list(data.get("tags", [])),
                notes=data.get("notes", ""),
            )
        )
    dupes = [k for k, v in Counter(it.id for it in items).items() if v > 1]
    if dupes:
        raise ValueError(f"duplicate golden ids: {dupes}")
    return items


def validate_golden(items: list[GoldenItem], tools: list[Tool]) -> list[str]:
    """Problems found (empty means OK).

    Catches upstream renames, e.g. DeepWiki's ``ask_question`` became ``ask_wiki_question``.
    """
    known = {t.id for t in tools}
    problems = []
    for item in items:
        missing = [g for g in item.gold if g not in known]
        if missing:
            problems.append(f"{item.id}: gold tool(s) not in catalog: {missing}")
    return problems
