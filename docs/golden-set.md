# Golden set and catalogs

## Catalog

`configs/servers.yaml` lists the MCP servers. Values support `${VAR}` and `${VAR:-default}`.

- Servers with `enabled: false` (or an env var that resolves to `false`) are skipped.
- Headers whose value resolves to empty, such as `Bearer ` with no token, are dropped.
- `auth: true` servers without credentials are skipped rather than failing the pull.

The first pull (2026-10-08) found 31 tools across 10 no-auth servers: DeepWiki, Context7,
AWS Knowledge, Microsoft Learn, Hugging Face, Cloudflare Docs, GitMCP, Astro Docs, Svelte
and Kiwi. GitHub and a Microsoft 365 server are configured but off until tokens are set.

`scripts/make_distractors.py` writes 110 synthetic tools across 23 `syn-*` servers
(`synthetic: true`). Some deliberately overlap real intents, such as internal docs search,
code search and corporate flight booking.

Re-pull and validate whenever servers change:

```bash
uv run tdb pull
uv run tdb validate
```

`validate` fails if a gold label no longer exists, which catches upstream renames.

## Question format

`data/golden/<family>/golden_v2.jsonl` (see `data/golden/README.md`), one object per line:

```json
{"id": "aws-04", "question": "Is Amazon Bedrock AgentCore available in ap-south-1 (Mumbai)?",
 "gold": ["aws-knowledge.aws___get_regional_availability"],
 "tags": ["cloud-docs", "hard_negative:aws_list_regions"]}
```

- `gold` lists **every** tool that is a correct *first* call. Context7 questions accept both
  `resolve-library-id` and `query-docs` when a library id may already be known.
- Lines starting with `//` are comments.

For `datasets_v1`, the benchmark-ready files (shared `qid`, frozen `test` split, leak
rewrites, no-tool additions) come from `scripts/build_benchmark.py`; see
`data/golden/README.md`.

## Tags

| Tag | Meaning |
|---|---|
| `hard_negative:<x>` | A specific confusable tool or server exists in the catalog. |
| `intra_server` | The distinction is between tools on the same server (search vs read). |
| `implicit_vendor` | The vendor is implied, not named ("Durable Objects alarms"). |
| `url_given` | The request contains a URL, which should push toward fetch/read tools. |
| `multi_valid` | More than one first call is acceptable. |
| `cross_server_ambiguous` | Several servers could reasonably answer. |
| `paraphrase` | Indirect wording of a common intent. |

## Writing good questions

- Phrase them the way a user would, not by echoing tool descriptions. Never include the gold
  tool's name; `tests/unit/test_dataset_integrity.py` fails if a question does.
- Add at least one question per real tool. `tdb validate` lists uncovered tools.
- Prefer questions with a clear first call. When two are genuinely fine, list both in `gold`
  and tag `multi_valid`.
