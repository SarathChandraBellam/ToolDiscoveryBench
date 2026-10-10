"""Make the golden suites benchmark-ready, deterministically.

    uv run python scripts/build_benchmark.py            # rewrite the suite files in place
    uv run python scripts/build_benchmark.py --check    # exit 1 if any output is stale

Run it after ``scripts/import_datasets.py`` (which regenerates ``datasets_v1`` from the raw
drop). It is idempotent: it first undoes its own previous edits, then re-applies them.

What it does, in order:

1. ``qid``: every row gets a suite-independent question id (``id`` before the ``@``), so a
   question shared by ``one_server`` / ``multi_server`` / ``multi_confused`` counts once.
2. Leak rewrites: questions listed in ``data/golden/curation/rewrites.jsonl`` get the new
   wording in every suite; the old text goes to ``meta.original_question`` and the row is
   tagged ``rewritten``. Gold labels are untouched.
3. No-tool additions from ``data/golden/curation/no_tool_additions.jsonl`` are appended to
   every ``datasets_v1`` suite (and to ``claude_v2`` when flagged), in each suite's existing
   no-tool format, with catalogs built the same way as the suite's other rows. They are tagged
   ``generator:cursor-bot`` and ``needs_human_review``.
4. Split: a frozen, seeded 30 % held-out ``test`` split of the canonical questions,
   stratified by (source, first gold tool or ``no_tool``). Rows get ``split`` and a
   ``split:<name>`` tag; the test ids go to ``data/golden/splits/test_qids.txt``.
5. Leak check: fails if any gold tool name still appears verbatim in its question.
6. Writes the canonical ``data/golden/questions.jsonl`` (one row per question) and
   ``data/golden/datasets_v1/summary.json``.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from tooldiscoverybench.golden.integrity import leaked_gold_names, question_id, stable_rank

ROOT = Path(__file__).resolve().parents[1]
GOLDEN = ROOT / "data/golden"
CURATION = GOLDEN / "curation"
DV1 = GOLDEN / "datasets_v1"
SUITES = {
    "one_server": DV1 / "one_server.jsonl",
    "multi_server": DV1 / "multi_server.jsonl",
    "multi_server_confused": DV1 / "multi_server_confused.jsonl",
    "claude_v2": GOLDEN / "claude/golden_v2.jsonl",
}
DV1_SUITES = ("one_server", "multi_server", "multi_server_confused")
SPLIT_SEED = 20261010
TEST_FRACTION = 0.30
ADDED_BY = "cursor-bot"

Row = dict[str, Any]


def read_jsonl(path: Path) -> list[Row]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def dump_jsonl(rows: list[Row]) -> str:
    return "".join(json.dumps(r) + "\n" for r in rows)


def source_of(suite: str) -> str:
    return "datasets_v1" if suite in DV1_SUITES else suite


# ------------------------------------------------------------------------- 0. reset
def reset(row: Row) -> Row | None:
    """Undo this script's previous edits so every run starts from the imported data."""
    meta = row.get("meta") or {}
    if meta.get("generator") == ADDED_BY:
        return None
    row = dict(row)
    row.pop("qid", None)
    row.pop("split", None)
    row["tags"] = [
        t for t in row.get("tags", []) if t != "rewritten" and not t.startswith("split:")
    ]
    if "original_question" in meta:
        meta = dict(meta)
        row["question"] = meta.pop("original_question")
        row["meta"] = meta
        if not meta and "provenance" in row:  # claude_v2 rows had no meta before
            del row["meta"]
    return row


def with_qid(row: Row) -> Row:
    """Put ``qid`` right after ``id`` so files stay readable."""
    out: Row = {"id": row["id"], "qid": question_id(row["id"])}
    out.update({k: v for k, v in row.items() if k not in out})
    return out


# ---------------------------------------------------------------------- 2. rewrites
def apply_rewrites(suites: dict[str, list[Row]], rewrites: list[Row]) -> None:
    for rw in rewrites:
        hits = 0
        for suite, rows in suites.items():
            if source_of(suite) != rw["source"]:
                continue
            for row in rows:
                if row["qid"] != rw["qid"]:
                    continue
                meta = dict(row.get("meta") or {})
                meta["original_question"] = row["question"]
                row["meta"] = meta
                row["question"] = rw["question"]
                row["tags"] = [*row["tags"], "rewritten"]
                hits += 1
        if not hits:
            raise SystemExit(f"rewrite {rw['source']}/{rw['qid']} matched no row")


# ---------------------------------------------------------------------- 3. no-tool
def server_tools(catalog_path: Path) -> dict[str, list[str]]:
    cat = json.loads(catalog_path.read_text())
    return {s: [f"{s}.{t['name']}" for t in v["tools"]] for s, v in cat["servers"].items()}


def confusable_peers(rows: list[Row]) -> dict[str, list[str]]:
    """For each server, the 5 servers it is most often connected with in multi_confused."""
    co: dict[str, Counter[str]] = defaultdict(Counter)
    for r in rows:
        servers = r["meta"]["connected_servers"]
        for a in servers:
            co[a].update(b for b in servers if b != a)
    return {
        a: [b for b, _ in sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))[:5]]
        for a, c in co.items()
    }


def added_rows(
    additions: list[Row], suite: str, tools: dict[str, list[str]], peers: dict[str, list[str]]
) -> list[Row]:
    out = []
    for add in additions:
        qid, home = add["qid"], add["near_miss_server"]
        if suite == "claude_v2":
            if not add.get("claude_v2"):
                continue
            out.append(
                {
                    "id": qid,
                    "qid": qid,
                    "question": add["question"],
                    "gold": [],
                    "tags": ["no_tool", f"generator:{ADDED_BY}", "needs_human_review"],
                    "provenance": {"source": ADDED_BY, "judge_status": "unreviewed"},
                    "meta": {"generator": ADDED_BY, "near_miss_server": home},
                }
            )
            continue
        rng = random.Random(stable_rank(suite, qid))
        if suite == "one_server":
            connected = [home]
        elif suite == "multi_server":
            connected = [home, *rng.sample(sorted(s for s in tools if s != home), 3)]
        else:  # multi_server_confused: the servers most often confused with the near-miss one
            connected = [home, *rng.sample(peers[home], 3)]
        connected = sorted(connected)
        tags = [suite, f"generator:{ADDED_BY}", "no_tool"]
        if suite == "multi_server_confused":
            tags.append("confusable")
        tags.append("needs_human_review")
        out.append(
            {
                "id": f"{qid}@{suite}",
                "qid": qid,
                "question": add["question"],
                "gold": [],
                "acceptable": [],
                "candidates": [t for s in connected for t in tools[s]],
                "tags": tags,
                "meta": {
                    "generator": ADDED_BY,
                    "generator_tool_id": None,
                    "judge_picks": {},
                    "agreement": None,
                    "connected_servers": connected,
                    "near_miss_server": home,
                },
            }
        )
    return out


# ------------------------------------------------------------------------- 4. split
def assign_splits(suites: dict[str, list[Row]]) -> dict[str, str]:
    canon: dict[str, tuple[str, str]] = {}  # qid -> (source, stratum)
    for suite, rows in suites.items():
        for r in rows:
            src = (
                "datasets_v1"
                if (r.get("meta") or {}).get("generator") == ADDED_BY
                else source_of(suite)
            )
            canon.setdefault(r["qid"], (src, r["gold"][0] if r["gold"] else "no_tool"))
    strata: dict[tuple[str, str], list[str]] = defaultdict(list)
    for qid, key in canon.items():
        strata[key].append(qid)
    split = {}
    for qids in strata.values():
        ordered = sorted(qids, key=lambda q: stable_rank(SPLIT_SEED, q))
        n_test = round(len(ordered) * TEST_FRACTION)
        for i, q in enumerate(ordered):
            split[q] = "test" if i < n_test else "dev"
    for rows in suites.values():
        for r in rows:
            r["split"] = split[r["qid"]]
            r["tags"] = [*r["tags"], f"split:{r['split']}"]
    return split


# ---------------------------------------------------------------------- 6. outputs
def canonical(suites: dict[str, list[Row]]) -> list[Row]:
    out: dict[str, Row] = {}
    suite_tags = set(SUITES)
    for suite, rows in suites.items():
        for r in rows:
            meta = r.get("meta") or {}
            c = out.get(r["qid"])
            if c is None:
                c = out[r["qid"]] = {
                    "qid": r["qid"],
                    "source": (
                        "datasets_v1" if meta.get("generator") == ADDED_BY else source_of(suite)
                    ),
                    "question": r["question"],
                    "gold": r["gold"],
                    "no_tool": not r["gold"],
                    "generator": meta.get("generator") or "claude-labelled",
                    "split": r["split"],
                    "suites": [],
                    "tags": [],
                }
                for key in ("original_question", "near_miss_server"):
                    if key in meta:
                        c[key] = meta[key]
            elif c["question"] != r["question"] or c["gold"] != r["gold"]:
                raise SystemExit(f"{r['qid']}: question or gold differs between suites")
            c["suites"].append(suite)
            c["tags"] = sorted(
                {
                    *c["tags"],
                    *(t for t in r["tags"] if t not in suite_tags and not t.startswith("split:")),
                }
            )
    return list(out.values())


def summary(suites: dict[str, list[Row]], canon: list[Row]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for suite in DV1_SUITES:
        rows = suites[suite]
        n_nt = sum(not r["gold"] for r in rows)
        out[suite] = {
            "questions": len(rows),
            "no_tool": n_nt,
            "no_tool_pct": round(100 * n_nt / len(rows), 1),
            "with_acceptable": sum(bool(r["acceptable"]) for r in rows),
            "judges_split": sum("judges_split" in r["tags"] for r in rows),
            "rewritten": sum("rewritten" in r["tags"] for r in rows),
            "needs_human_review": sum("needs_human_review" in r["tags"] for r in rows),
            "test_split": sum(r["split"] == "test" for r in rows),
            "catalog_size": dict(sorted(Counter(len(r["candidates"]) for r in rows).items())),
            "generators": dict(sorted(Counter(r["meta"]["generator"] for r in rows).items())),
            "gold_tools_covered": len({g for r in rows for g in r["gold"]}),
        }
    dv1 = [c for c in canon if c["source"] == "datasets_v1"]
    out["canonical_datasets_v1"] = {
        "unique_questions": len(dv1),
        "no_tool": sum(c["no_tool"] for c in dv1),
        "gold_tools": len({g for c in dv1 for g in c["gold"]}),
        "servers": len({g.split(".", 1)[0] for c in dv1 for g in c["gold"]}),
        "test_split": sum(c["split"] == "test" for c in dv1),
        "added_by_cursor_bot": sum(c["generator"] == ADDED_BY for c in dv1),
    }
    return out


def build() -> dict[Path, str]:
    """Every output file and its content. Pure: reads inputs, writes nothing."""
    suites = {}
    for name, path in SUITES.items():
        suites[name] = [with_qid(r) for r in (reset(x) for x in read_jsonl(path)) if r is not None]

    apply_rewrites(suites, read_jsonl(CURATION / "rewrites.jsonl"))
    additions = read_jsonl(CURATION / "no_tool_additions.jsonl")
    tools = server_tools(ROOT / "data/catalog/public.json")
    peers = confusable_peers(suites["multi_server_confused"])
    for name in SUITES:
        suites[name] += added_rows(additions, name, tools, peers)

    assign_splits(suites)

    leaks = [
        f"{suite}/{r['id']}: {leaked}"
        for suite, rows in suites.items()
        for r in rows
        if (leaked := leaked_gold_names(r["question"], r["gold"]))
    ]
    if leaks:
        raise SystemExit("gold tool name leaks into question:\n  " + "\n  ".join(leaks))

    canon = canonical(suites)
    test_ids = sorted(c["qid"] for c in canon if c["split"] == "test")
    files = {path: dump_jsonl(suites[name]) for name, path in SUITES.items()}
    files[GOLDEN / "questions.jsonl"] = dump_jsonl(canon)
    files[GOLDEN / "splits/test_qids.txt"] = "".join(q + "\n" for q in test_ids)
    files[DV1 / "summary.json"] = json.dumps(summary(suites, canon), indent=2) + "\n"
    return files


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--check", action="store_true", help="fail if any output is out of date")
    args = parser.parse_args()
    files = build()
    stale = [p for p, text in files.items() if not p.exists() or p.read_text() != text]
    if args.check:
        if stale:
            print("stale:", *(str(p.relative_to(ROOT)) for p in stale), sep="\n  ")
            sys.exit(1)
        print("up to date")
        return
    for path in stale:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(files[path])
    print(json.dumps(json.loads(files[DV1 / "summary.json"])["canonical_datasets_v1"], indent=2))
    print(f"wrote {len(stale)} file(s)")


if __name__ == "__main__":
    main()
