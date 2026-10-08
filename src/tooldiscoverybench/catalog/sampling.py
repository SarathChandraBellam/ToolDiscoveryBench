"""Build the per-question catalog a router sees at a given catalog size."""

from __future__ import annotations

import hashlib
import random

from tooldiscoverybench.core.models import GoldenItem, Tool

CatalogSize = int | str

#: catalog size label used for questions that carry their own fixed candidate catalog
FIXED = "fixed"


def sample_catalog(
    all_tools: list[Tool],
    item: GoldenItem,
    size: CatalogSize,
    seed: int = 0,
) -> list[Tool]:
    """The catalog a router sees for this question.

    If the question carries ``candidates``, exactly those tools are used (in a seeded
    shuffle, so position never leaks the answer). Otherwise: gold tool(s) plus seeded
    distractors, same-server ones first because they are the hard negatives.
    Deterministic for ``(item.id, size, seed)``, so every router sees the same catalog.
    """
    if item.candidates is not None:
        by_id = {t.id: t for t in all_tools}
        fixed = [by_id[c] for c in item.candidates if c in by_id]
        random.Random(int(hashlib.sha256(f"{item.id}|{seed}".encode()).hexdigest(), 16)).shuffle(
            fixed
        )
        return fixed
    if size in ("all", FIXED) or int(size) >= len(all_tools):
        return list(all_tools)
    n = int(size)
    gold = [t for t in all_tools if t.id in item.gold]
    rest = [t for t in all_tools if t.id not in item.gold]

    digest = hashlib.sha256(f"{item.id}|{n}|{seed}".encode()).hexdigest()
    rng = random.Random(int(digest, 16))
    same_server = [t for t in rest if t.server in item.gold_servers]
    others = [t for t in rest if t.server not in item.gold_servers]
    rng.shuffle(same_server)
    rng.shuffle(others)

    picked = gold + (same_server + others)[: max(0, n - len(gold))]
    rng.shuffle(picked)
    return picked
