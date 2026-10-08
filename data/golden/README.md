# Golden datasets

## Which set to use

| Suite | File | Questions | Catalog | Notes |
|---|---|---:|---|---|
| `one_server` | `datasets_v1/one_server.jsonl` | 616 (67 no-tool) | fixed: tools of 1 connected server (1–5) | easiest; tests tool choice within one server |
| `multi_server` | `datasets_v1/multi_server.jsonl` | 616 (67 no-tool) | fixed: tools of 4 connected servers (7–18) | same questions, more servers |
| `multi_confused` | `datasets_v1/multi_server_confused.jsonl` | 325 | fixed, 9–18 tools | multi_server subset with confusable tools |
| `claude_v2` | `claude/golden_v2.jsonl` | 151 | sampled at 10/30/75/150 with synthetic distractors | earlier Claude-only labelling |

`datasets_v1` is the main set. Questions were written by 9 models (4 Claude, 5 GPT, about 70
each) and judged by two judges from different families (gpt-5.6-sol and claude-opus-5-5);
585/616 judge pairs agree. Raw files are kept unchanged in `data/raw/datasets_v1/` and
converted with `scripts/import_datasets.py`. Each record has:

- `gold`: the right first tool, or `[]` when no connected tool can do it (e.g. "cancel my
  Kiwi booking"); the right behaviour then is to abstain
- `acceptable`: reasonable but not ideal first calls, counted only by the *lenient* metric
- `candidates`: the exact catalog shown for that question
- `meta`: generator model, both judges' picks, agreement, connected servers
- tags: scenario, `generator:<family>`, `no_tool`, `confusable`, `judges_split`, `relabelled`

`data/raw/datasets_v1/review.jsonl` holds 3 questions the judges disagreed on that were left
out of the set.

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
