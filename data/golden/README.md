# Golden datasets

## Which set to use

| Suite | File | Questions | Catalog | Notes |
|---|---|---:|---|---|
| `one_server` | `datasets_v1/one_server.jsonl` | 696 (147 no-tool, 21%) | fixed: tools of 1 connected server (1–5) | easiest; tests tool choice within one server |
| `multi_server` | `datasets_v1/multi_server.jsonl` | 696 (147 no-tool, 21%) | fixed: tools of 4 connected servers (7–18) | same questions, more servers |
| `multi_confused` | `datasets_v1/multi_server_confused.jsonl` | 405 (81 no-tool, 20%) | fixed, 9–18 tools | multi_server subset with confusable tools |
| `claude_v2` | `claude/golden_v2.jsonl` | 190 (39 no-tool, 21%) | sampled at 10/30/75/150 with synthetic distractors | earlier Claude-only labelling |

`datasets_v1` is the main set: **696 unique questions over 31 tools from 10 servers**, of
which 549 are answerable and 147 are no-tool. The three suites show the *same* questions
with different catalogs, so they are not independent samples; count questions by `qid`.
616 questions were written by 9 models (4 Claude, 5 GPT, about 70 each) and judged by two
judges from different families (gpt-5.6-sol and claude-opus-5-5); 585/616 judge pairs agree.
The other 80 are no-tool questions added by `cursor-bot` (see *Curation* below). Raw files
are kept unchanged in `data/raw/datasets_v1/`, converted with `scripts/import_datasets.py`
and then finalised with `scripts/build_benchmark.py`. Each record has:

- `gold`: the right first tool, or `[]` when no connected tool can do it (e.g. "cancel my
  Kiwi booking"); the right behaviour then is to abstain
- `acceptable`: reasonable but not ideal first calls, counted only by the *lenient* metric
- `candidates`: the exact catalog shown for that question
- `qid`: suite-independent question id (`id` without the `@suite` suffix), shared by every
  suite that contains the question
- `split`: `dev` or `test` (also as tag `split:<name>`), see *Held-out test split*
- `meta`: generator model, both judges' picks, agreement, connected servers; plus
  `original_question` on rewritten rows and `near_miss_server` on added no-tool rows
- tags: scenario, `generator:<family>`, `no_tool`, `confusable`, `judges_split`, `relabelled`
  (gold differs from the writer's intent), `rewritten` (wording changed, gold unchanged),
  `needs_human_review`, `split:dev` / `split:test`

`data/raw/datasets_v1/review.jsonl` holds 3 questions the judges disagreed on that were left
out of the set.

## Canonical question file

`questions.jsonl` lists every unique question once: `qid`, `source` (`datasets_v1` or
`claude_v2`), `question`, `gold`, `no_tool`, `generator`, `split`, the `suites` it appears in
and its non-suite tags. `acceptable` is per suite (the catalog differs), so it stays in the
suite files. Totals: 696 `datasets_v1` + 151 `claude_v2` = 847 unique questions (the 39
no-tool rows in `claude_v2` reuse `datasets_v1` qids).

## Held-out test split

`splits/test_qids.txt` freezes a **30% test split** (206 `datasets_v1` + 44 `claude_v2`
qids), drawn with a fixed seed (`SPLIT_SEED = 20261010` in `scripts/build_benchmark.py`)
and stratified by (source, first gold tool or `no_tool`), so every tool and the abstention
case are represented in proportion. A question has the same split in every suite. Tune
prompts, thresholds and router settings on `dev`; report `test`. The report adds a test-split
column with bootstrap 95% intervals.

**Not yet human-verified**: the split inherits the model-judged labels, and 28 of its
`datasets_v1` questions are unreviewed `cursor-bot` no-tool items. Do not change the seed or
the file once results are published; add questions to `dev` instead.

## Curation (`scripts/build_benchmark.py`)

Run it after `scripts/import_datasets.py`; it is deterministic and idempotent, and
`--check` (also run by the unit tests) fails if any output is stale. Inputs live in
`curation/`:

- `rewrites.jsonl`: 14 questions (13 in `datasets_v1`, 10 of which are also in
  `multi_confused`, and 1 in `claude_v2`) contained the gold tool's name verbatim, e.g.
  "make a playground link" for `svelte.playground-link`. They were reworded with the same
  intent and gold; the original is kept in `meta.original_question` and the row is tagged
  `rewritten`. `tests/unit/test_dataset_integrity.py` fails if any gold tool name (tool part,
  `_`/`-` read as spaces, ≥ 5 chars) appears in its question again.
- `no_tool_additions.jsonl`: 80 near-miss no-tool questions (8 per server): realistic dev
  requests that sound like a connected server's domain but need an action or private data no
  connected tool provides (deploys, account changes, local builds, booking changes). Each
  suite gets them in its own format: one server (`one_server`); the near-miss server plus 3
  seeded others (`multi_server`); the near-miss server plus 3 of the servers it is most often
  confused with (`multi_confused`). The 39 that also stay clear of every synthetic-distractor
  domain go into `claude_v2`, whose catalogs include those tools. All are tagged
  `generator:cursor-bot` and `needs_human_review`.

## Contamination

gpt-5.6-sol and claude-opus-5-5 both wrote questions **and** judged every label, and
gpt-5.6-luna wrote 69 questions while `openai/gpt-6-luna-decisions` is a router under test.
Every row keeps `meta.generator`, and the report shows accuracy per exact author model plus a
table with and without these three authors (`tdb report <run> --exclude-generators a,b` to
change the list). Prefer the "kept" columns when comparing routers from those families.

## Remaining work

- Human review of labels: nothing has been verified by a person yet, including the test
  split, the 80 `needs_human_review` no-tool questions, the 14 rewrites and the 11 questions
  in `claude/review_v2.jsonl`.
- Realistic scale: catalogs top out at the 31 real tools; the 75/150 sizes are padded with
  synthetic distractors. Pulling the authenticated servers (GitHub, Microsoft 365, ...) needs
  the owner's credentials and would give a 150+ real-tool tier.
- Coverage: `multi_confused` has no question for `huggingface.hf_whoami`, `kiwi.search-flight`
  or `kiwi.feedback-to-devs`, and `claude_v2` none for `aws-knowledge.aws___retrieve_skill`.

Gold labels are produced per **model family**, so results can be compared across labelers and
no single vendor's preferences define "correct".

```
data/golden/
  shared/                          model-agnostic inputs, identical for every family
    drafted_questions_v2.jsonl     drafted questions with the drafter's intended tools
    candidates.jsonl               every question + intended tools (never shown to labelers)
    questions_blind.jsonl          id + question only, shuffled (what labelers see)
    catalog_for_labelers.json      the 31 real tools with descriptions and input schemas
    prompts/labeler.md             instructions for labeler models
    prompts/judge.md               instructions for the judge model
  claude/                          labeled by Claude models
    golden_v1.jsonl                50 hand-labeled seed questions
    golden_v2.jsonl                151 accepted questions (Haiku, Sonnet, Opus + Opus judge)
    review_v2.jsonl                11 questions a human must decide
    labeling_report_v2.json        agreement statistics
    labeling/                      votes_<model>.jsonl, executions.jsonl, judge_pack.jsonl, judgments.jsonl
  openai/                          labeled by OpenAI models (not run yet)
```

## How a family is labeled

1. `scripts/labeling/build_pack.py` builds `shared/` from the seed and drafted questions.
2. Each labeler model reads `shared/prompts/labeler.md` and writes
   `<family>/labeling/votes_<model>.jsonl`: its first tool call, with arguments, per question.
3. `scripts/labeling/execute_calls.py --family <family>` runs every distinct proposed call
   against the live MCP servers. Tools with third-party side effects are skipped.
4. `scripts/labeling/build_judge_pack.py --family <family>` merges votes and results.
5. A judge model reads `shared/prompts/judge.md` and writes `<family>/labeling/judgments.jsonl`.
6. `scripts/labeling/aggregate.py --family <family>` writes `golden_v2.jsonl`, `review_v2.jsonl`
   and the report.

For families other than `claude`, pass the labeler names: `--models gpt-4.1-mini,gpt-4.1,o3`.

## Record format

```json
{"id": "d-aws-avail-01", "question": "Can I use Amazon Bedrock in ap-south-2?",
 "gold": ["aws-knowledge.aws___get_regional_availability"],
 "tags": ["cloud-docs", "hard_negative:aws_list_regions"],
 "provenance": {"source": "drafted", "first_picks": {"haiku": "...", "sonnet": "...", "opus": "..."},
                "agreement": "3/3", "drafter_intended": ["..."], "result_useful": "yes",
                "judge_status": "accept"}}
```

`gold` lists every tool that is a correct first call. The benchmark reads `id`, `question`,
`gold` and `tags`; `provenance` documents how the label was reached.

## Choosing a set

Point `golden:` in `configs/bench.yaml` at one family's file. When benchmarking a router built
on one vendor's models, prefer gold labels from a different family, or report both, so the
router isn't graded against its own family's preferences.
