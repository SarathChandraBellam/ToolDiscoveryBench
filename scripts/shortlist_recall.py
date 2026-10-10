"""Shortlist recall@k for a retriever on one split (free: runs locally, no API calls).

Tune the ``shortlist`` router's ``k`` on the dev split only::

    uv run python scripts/shortlist_recall.py --split dev --ks 3,4,5,6,8,10,12

Recall@k is the share of answerable questions whose gold tool survives the shortlist; the
decider can never recover a tool the retriever dropped, so it caps shortlist top-1.
"""

from __future__ import annotations

import argparse
import asyncio
import json
from typing import Any

from tooldiscoverybench.catalog import load_catalog, sample_catalog
from tooldiscoverybench.catalog.sampling import FIXED
from tooldiscoverybench.core.config import load_yaml
from tooldiscoverybench.evaluation.runner import catalog_paths, load_suites
from tooldiscoverybench.routers import build_router


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/bench.yaml")
    ap.add_argument("--split", default="dev")
    ap.add_argument("--suites", default="one_server,multi_server,multi_confused")
    ap.add_argument("--ks", default="3,4,5,6,8,10,12")
    ap.add_argument("--retriever", default='{"type": "embedding"}')
    args = ap.parse_args()
    if args.split == "test":
        raise SystemExit("tune k on dev, not on the frozen test split")

    cfg = load_yaml(args.config)
    tools, server_desc = load_catalog(*catalog_paths(cfg))
    suites = load_suites(cfg, tools, None, args.suites.split(","), args.split)
    ks = [int(k) for k in args.ks.split(",")]
    spec: dict[str, Any] = {"name": "retriever", **json.loads(args.retriever)}
    router = build_router(spec)
    await router.setup(tools, server_desc)
    out: dict[str, dict[str, Any]] = {}
    for suite in suites:
        hits = dict.fromkeys(ks, 0)
        n = 0
        sizes = []
        for item in suite.items:
            if item.expects_abstain:
                continue
            catalog = sample_catalog(tools, item, FIXED, 0)
            res = await router.route(item.question, catalog, server_desc)
            ids = [tid for tid, _ in res.ranked]
            n += 1
            sizes.append(len(catalog))
            for k in ks:
                hits[k] += any(t in item.gold for t in ids[:k])
        out[suite.name] = {
            "n_answerable": n,
            "max_tools": max(sizes, default=0),
            **{f"recall@{k}": hits[k] / max(1, n) for k in ks},
        }
    await router.aclose()
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
