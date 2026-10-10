# Results snapshot, 2026-10-10

Summaries, configs and rendered reports for every run behind the numbers in the top-level
README. Raw `results.jsonl` files (2–15 MB each) are not committed. Rerun with the commands
in the README's "Reproduce" section.

All test runs use plain MCP descriptions, the frozen test split (`data/golden/splits/test_qids.txt`;
206 / 206 / 131 / 55 questions per repeat for one_server / multi_server / multi_confused /
claude_v2) and 3 repeats. Decision models ran through OpenRouter (`/api/alpha/decisions`)
with cost from the reported `usage.cost`. Times are IST.

## Test split (published)

| Folder | Run | What it supplies |
|---|---|---|
| `test/combined/` | merged with `scripts/combine_runs.py` (below) | **the README tables**: one report with every published router |
| `test/claude_v2-scaling/` | merged from `repro-main` | Jev flat and BM25 at 10 / 30 / 75 / 150 tools |
| `test/openrouter-test/` | 01:56, PR #2 branch | `or-jev-flat`, `or-luna-flat`, `embed-bge-small`, `bm25` (its `or-jev-factored` predates the factored refusal fix, and its `or-luna-factored` rows errored; both are superseded) |
| `test/luna-factored-v2/` | 02:06, PR #2 branch after the refusal fix | `or-jev-factored`, `or-luna-factored` (with refusal rate) |
| `test/jev-factored-fitq/` | 08:16, PR #5 branch | `or-jev-factored-fitq` |
| `test/luna-flat-recheck/` | PR #4 branch | `or-luna-flat` recheck: identical accuracy, lower latency |
| `test/repro-main/` | 08:06, `main` | reproduction: `or-jev-flat` (all suites incl. claude_v2), `bm25`, `bm25-abstain`. Luna and Jev factored rows hit `HTTP 402` (out of credits) and are not used |
| `test/repro-main-embed/` | `main` | `embed-bge-small` reproduction (identical accuracy) |

`openrouter-test/config.json` points at pre-filtered copies of the test split (made before
`tdb run --split test` existed). They hold the same questions as `--split test`.

Rebuild the combined report from the raw run directories (offline, no API calls):

```bash
F=one_server,multi_server,multi_confused
uv run python scripts/combine_runs.py runs/combined --require-tag split:test \
  runs/openrouter-test:or-jev-flat:$F  runs/luna-factored-v2:or-jev-factored:$F \
  runs/test-fitq:or-jev-factored-fitq:$F  runs/openrouter-test:or-luna-flat:$F \
  runs/luna-factored-v2:or-luna-factored:$F  runs/openrouter-test:embed-bge-small:$F \
  runs/openrouter-test:bm25:$F  runs/repro-main:bm25-abstain:$F
uv run tdb report runs/combined            # default --exclude-generators: the two harness models + gpt-5.6-luna
uv run python scripts/combine_runs.py runs/claude_v2-scaling --require-tag split:test \
  runs/repro-main:or-jev-flat:claude_v2 runs/repro-main:bm25:claude_v2
uv run tdb report runs/claude_v2-scaling
```

## Dev split (preliminary, 1 repeat, never test)

| Folder / file | What |
|---|---|
| `dev/escalate-jev-sonnet-t0.95/` | one `escalate-jev-sonnet` run at `escalate_below=0.95` (Sonnet cost estimated from list price) |
| `dev/escalation_curve.txt` | `scripts/escalation_curve.py` replay at lower thresholds; 0.85 picked |
| `dev/jev-flat/` | Jev flat on dev, the baseline for both |
| `dev/shortlist-k8/`, `shortlist-k10/`, `shortlist-k12/` | `shortlist-bge-jev` at k = 8 / 10 / 12 |
| `dev/shortlist_recall_bge.json`, `shortlist_recall_bm25.json` | `scripts/shortlist_recall.py` recall@k |

The test-split runs of `escalate` and `shortlist` were stopped before finishing and are not included.
