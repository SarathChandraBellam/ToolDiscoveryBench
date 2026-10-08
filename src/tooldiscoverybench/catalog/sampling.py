"""Build the per-question catalog a router sees at a given catalog size."""

from __future__ import annotations

import hashlib
import random

from tooldiscoverybench.core.models import GoldenItem, Tool

CatalogSize = int | str


def sample_catalog(
    all_tools: list[Tool],
    item: GoldenItem,
    size: CatalogSize,
    seed: int = 0,
) -> list[Tool]:
    """Gold tool(s) plus seeded distractors.

    Same-server distractors are added first because they are the hard negatives.
    The result is deterministic for ``(item.id, size, seed)``, so every router sees
    the identical catalog, and it is shuffled so position never leaks the answer.
    """
    if size == "all" or int(size) >= len(all_tools):
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
