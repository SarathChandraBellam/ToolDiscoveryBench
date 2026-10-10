"""Merge chosen routers from several run directories into one run directory (offline).

Each spec is ``RUN_DIR:ROUTER[:SUITE,SUITE...]``. Rows are copied verbatim from each run's
``results.jsonl``; ``summary.json`` is recomputed, so render the report afterwards::

    uv run python scripts/combine_runs.py runs/combined \\
        runs/test-a:or-jev-flat runs/test-b:or-jev-factored:one_server,multi_server
    uv run tdb report runs/combined

``--require-tag split:test`` refuses to merge any row without that tag, so a published
table cannot silently mix dev and test questions. No network calls are made.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from tooldiscoverybench.evaluation.metrics import by_tag, summarize


def parse_spec(spec: str) -> tuple[Path, str, set[str] | None]:
    parts = spec.split(":")
    if len(parts) not in (2, 3) or not parts[0] or not parts[1]:
        raise SystemExit(f"bad spec {spec!r}; expected RUN_DIR:ROUTER[:SUITES]")
    suites = {s for s in parts[2].split(",") if s} if len(parts) == 3 else None
    return Path(parts[0]), parts[1], suites


def select_rows(
    run_dir: Path, router: str, suites: set[str] | None, require_tag: str | None
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in (run_dir / "results.jsonl").read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row["router"] != router or (suites is not None and row.get("suite") not in suites):
            continue
        if require_tag and require_tag not in row.get("tags", []):
            raise SystemExit(f"{run_dir}: row {row['item']} lacks tag {require_tag!r}")
        rows.append(row)
    if not rows:
        raise SystemExit(f"{run_dir}: no rows for router {router!r}")
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("out")
    parser.add_argument("specs", nargs="+", help="RUN_DIR:ROUTER[:SUITE,SUITE...]")
    parser.add_argument("--require-tag", default=None, help="e.g. split:test")
    args = parser.parse_args()

    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for spec in args.specs:
        run_dir, router, suites = parse_spec(spec)
        if router in seen:
            raise SystemExit(f"router {router!r} given twice; pick one source run")
        seen.add(router)
        picked = select_rows(run_dir, router, suites, args.require_tag)
        print(f"{run_dir} {router}: {len(picked)} rows")
        rows += picked

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "results.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    summary = {"summary": summarize(rows), "by_tag": by_tag(rows)}
    (out / "summary.json").write_text(json.dumps(summary, indent=2))
    print(f"wrote {len(rows)} rows -> {out}; render with: uv run tdb report {out}")


if __name__ == "__main__":
    main()
