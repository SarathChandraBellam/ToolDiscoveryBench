# Dataset card: ToolDiscoveryBench golden sets

## Summary

ToolDiscoveryBench measures whether a router can name the right **first** MCP tool for a
user request, and whether it **abstains** when no listed tool fits. The data is a set of
English questions about developer tasks, each labelled with the gold first tool(s) from a
catalog of **31 real tools on 10 public MCP servers** (DeepWiki, Context7, AWS Knowledge,
Microsoft Learn, Hugging Face, Cloudflare Docs, GitMCP, Astro Docs, Svelte, Kiwi). Another
110 synthetic tools on 23 `syn-*` servers pad catalogs to larger sizes.

There are **847 unique questions**: 696 in `datasets_v1` and 151 in `claude_v2`. **147** of
them are **no-tool** questions, where the right answer is to call nothing. All 147 are in
`datasets_v1`; `claude_v2`'s 39 no-tool rows reuse 39 of them. The 616 original `datasets_v1` labels
are **harness first-call labels**, and `claude_v2` labels come from model votes; **no human
has reviewed any label yet.**

## Intended use

- **Production target:** evaluating a drop-in replacement for tool search in agent harnesses.
  Instead of loading every tool definition, a harness can optionally use keyword search such
  as BM25 to decide which tools to load; a router evaluated here would take that place.
  Given a request and a catalog, it must rank the right tool first, or say that none fits.
- Comparing tool routers (decision models, LLM agents, retrieval baselines) on first-tool
  accuracy, abstention, latency and cost, using `tdb run`.
- **Report results on the frozen test split** (`tdb run --split test`) with `repeats >= 3`,
  and tune prompts, thresholds and hints on `dev` only.
- Not for training tool-use models, not a measure of end-to-end task success (only the first
  call is scored), and not representative of private or authenticated tool catalogs.

## Structure

Files (all JSONL, one question per line):

| Suite (`configs/bench.yaml`) | File | Rows | No-tool | Answerable | Test rows | Catalog per question |
|---|---|---:|---:|---:|---:|---|
| `one_server` | `golden/datasets_v1/one_server.jsonl` | 696 | 147 (21.1%) | 549 | 206 (44 no-tool) | fixed: tools of 1 connected server (1–5 tools) |
| `multi_server` | `golden/datasets_v1/multi_server.jsonl` | 696 | 147 (21.1%) | 549 | 206 (44 no-tool) | fixed: tools of 4 connected servers (7–18 tools) |
| `multi_confused` | `golden/datasets_v1/multi_server_confused.jsonl` | 405 | 81 (20.0%) | 324 | 131 (29 no-tool) | fixed: 4 servers chosen to contain confusable tools (9–18 tools) |
| `claude_v2` | `golden/claude/golden_v2.jsonl` | 190 | 39 (20.5%) | 151 | 55 (11 no-tool) | sampled per question at 10 / 30 / 75 / 150 tools |

- **The three `datasets_v1` suites are the same questions shown with different catalogs.**
  `one_server` and `multi_server` hold the same 696 questions (616 harness-labelled:
  549 answerable + 67 no-tool, plus 80 bot-written no-tool questions), and `multi_confused`
  holds 405 of them. Count by `qid`, not by row.
- `golden/questions.jsonl` lists each of the 847 unique questions once, with `qid`, `source`,
  `question`, `gold`, `no_tool`, `generator`, `split`, `suites` and tags.
- `golden/splits/test_qids.txt` holds the 250 test question ids.
- Catalogs: `catalog/public.json` (31 real tools, pulled 2026-10-08) and
  `catalog/distractors_synthetic.json` (110 synthetic tools).
- **claude_v2 catalog sizes:** each catalog is the gold tool(s) plus seeded distractors,
  same-server first. There are only 31 real tools, so **75- and 150-tool catalogs are mostly
  synthetic**. On average a catalog holds 5.6 / 21.6 / 57.5 / 110 synthetic tools at sizes
  10 / 30 / 75 / 150. "150" is the full 141-tool catalog.

Row fields:

| Field | Meaning |
|---|---|
| `id` | row id, `<qid>@<suite>` in `datasets_v1` |
| `qid` | question id shared by every suite that contains the question |
| `question` | the user request |
| `gold` | tool ids (`server.tool`) that are a correct first call; `[]` = no-tool, the router should abstain. Single-gold in `datasets_v1`; 10 `claude_v2` rows have 2+ gold tools. |
| `acceptable` | reasonable but not ideal first calls (lenient metric only; `datasets_v1`) |
| `candidates` | the fixed catalog shown for this question (`datasets_v1`); absent in `claude_v2` |
| `tags` | suite, `generator:<family>`, `no_tool`, `confusable`, `judges_split`, `relabelled`, `rewritten`, `needs_human_review`, `split:dev`/`split:test`, plus topic tags in `claude_v2` |
| `split` | `dev` or `test` |
| `meta` | `generator` (writer model), `generator_tool_id` (writer's intended tool), `judge_picks` (harness first calls: Codex/gpt-5.6-sol and Claude Code/claude-opus-5-5), `agreement`, `connected_servers`; `original_question` on rewritten rows; `near_miss_server` on added no-tool rows |
| `provenance` | `claude_v2` only: labeler first picks, agreement, judge status |

## Sources and generation

**datasets_v1 (616 model-written + 80 bot-written).** Nine models each wrote about 70
questions against the same 70 intent "slots". Each slot was written by 8–9 generators, and in
63 of the 70 slots every writer intended the same tool. Count per writer (identical in
`one_server` and `multi_server`):

| Writer | Questions | Writer | Questions |
|---|---:|---|---:|
| claude-fable-5-1 | 70 | gpt-5.5 | 69 |
| claude-haiku-4-5 | 68 | gpt-5.6-luna | 69 |
| claude-opus-5-5 | 66 | gpt-5.6-sol | 70 |
| claude-sonnet-5-5 | 68 | gpt-5.6-terra | 67 |
| | | gpt-6-astra | 69 |
| | | **cursor-bot** (added no-tool) | 80 |

Raw drops are in `raw/datasets_v1/` and are converted by `scripts/import_datasets.py`.
`scripts/build_benchmark.py` then adds `qid`s, the leak rewrites, the added no-tool questions
and the split; it is deterministic, and its `--check` mode is run by the tests.

**claude_v2 (151 + 39).** 48 seed questions (`claude/golden_v1.jsonl`) and 103 drafted
questions, all written and labelled by Claude-family models. The 39 no-tool rows are
`datasets_v1` cursor-bot questions, reused with the same `qid`.

## Labeling and judging

- **datasets_v1: harness first-call labels.** Each of the 616 model-written questions was run
  through two agent harnesses, **Claude Code (claude-opus-5-5)** and **Codex (gpt-5.6-sol)**,
  and the tool each harness actually called first was logged.
  - The harnesses loaded **every tool definition**: all 31 real tools, with no tool search.
    So the gold label is the agent's first call when it could see the whole catalog.
  - Those first calls were then cross-checked against the tool the question's writer
    intended.
  - The raw files store the two first calls as `judge_picks` (`null` = the harness made no
    call) and the writer's intent as `generator_tool_id` (`null` = writer intended no tool).
  - **Answerable vs no-tool:** **549** answerable, **67** no-tool.
  - **All three agree on 585** (`agreement: unanimous`): 519 answerable, plus 66 no-tool where
    neither harness made a call and the writer intended none.
  - **Majority on 31** (tag `judges_split`):
    - 23 where both harnesses agree against the writer. 21 of these are answerable and
      tagged `relabelled`; 1 has the writer intending no tool while both harnesses called
      `svelte.svelte-autofixer`; 1 has the writer intending `astro-docs.search_astro_docs`
      while neither harness made a call, so it is no-tool.
    - 8 where the writer and one harness agree: 5 with Claude Code, 3 with Codex.
  - **All 67 original no-tool questions went through both harnesses, and neither made a call
    on any of them.** In 66 the writer also intended no tool.
  - The gold tool is not always unanimous among the agents. On 8 answerable questions only
    one harness agrees with the gold tool, and on 1 of them (`claude-haiku-4-5-060`) Codex
    made no call.
  - 3 questions with no majority were dropped (`raw/datasets_v1/review.jsonl`).
  - The **80 added no-tool questions** (`generator:cursor-bot`) were **never run through a
    harness**. Their label is the writer's intent only, so they carry `needs_human_review`.
- **claude_v2:** Haiku, Sonnet and Opus each proposed a first call, the calls were executed
  against the live servers, and an Opus judge decided.
  - All 151 accepted questions are 3/3 agreement.
  - 11 more need a human decision (`claude/review_v2.jsonl`) and are not in the suite.
- **No human has reviewed any label yet.**

## Test split

- **What it is:** a frozen, seeded 30% test split (`SPLIT_SEED = 20261010` in
  `scripts/build_benchmark.py`). It is stratified by source and first gold tool, with no-tool
  as its own stratum.
- **Size:** 250 question ids (206 `datasets_v1` + 44 `claude_v2`). A question has the same split in
  every suite.
- **Not human-verified:** it inherits the harness and model-vote labels. 28 of its 44 `datasets_v1`
  no-tool questions are unreviewed cursor-bot questions, and all 11 `claude_v2` test no-tool
  rows are.
- **Use it with** `tdb run --split test`. The report adds bootstrap 95% CIs for the test split.

## Known biases and limitations

- **Paraphrase leakage between dev and test.** Questions in the same writer slot are
  near-paraphrases of one intent, and the split is stratified by tool, not by slot. 69 of the
  70 slots have questions in both dev and test, so anything tuned on dev (prompts, hints,
  thresholds) has seen paraphrases of most test questions. Treat dev-tuned gains as
  optimistic. A slot-grouped split is planned for the next version.
- **Routers get an easier catalog than the labelling agents had.** The harnesses chose from
  all 31 tools at once. Routers are scored on a narrower per-question catalog, which always
  contains the gold tool: 1–5 tools in `one_server`, 7–18 in `multi_server`, 9–18 in
  `multi_confused`. Accuracy here is therefore an upper bound on routing over the full
  catalog. The closest full-catalog setting is `claude_v2` at size 150, which is 141 tools
  but mostly synthetic distractors.
- **Small, docs-heavy catalog.** 31 real tools, mostly documentation search/read tools. Larger
  `claude_v2` sizes rely on synthetic distractors, and no authenticated servers (GitHub,
  Microsoft 365, ...) are included yet.
- **No-tool questions are mostly bot-written and templated.**
  - 80 of the 147 `datasets_v1` no-tool questions, 80 of the 81 in `multi_confused`, and all
    39 in `claude_v2` were written by cursor-bot (tags `generator:cursor-bot`,
    `needs_human_review`).
  - The 67 model-written no-tool questions repeat a few templates (cancel a booking, book a
    hotel, weather, deploy a Worker).
- **Unreviewed edits.** The 80 added no-tool questions and the 14 leak rewrites (13 in
  `datasets_v1`, 10 of which are also in `multi_confused`, and 1 in `claude_v2`; tag
  `rewritten`, original text in `meta.original_question`) have not been checked by a human.
- **Coverage gaps.**
  - `multi_confused` has no answerable questions for `huggingface.hf_whoami`,
    `kiwi.search-flight` or `kiwi.feedback-to-devs`, so it has nothing for the Kiwi server.
  - `claude_v2` has none for `aws-knowledge.aws___retrieve_skill`.
  - In `datasets_v1`, the number of questions per tool ranges from 10 (`svelte.get-documentation`) to 25
    (`svelte.list-sections`).
- **Disputed labels are concentrated in the hard suite.** All 31 `judges_split` and all 21
  `relabelled` questions are in `multi_confused`.
- English only; single first call; the tools' descriptions are as published on 2026-10-08 and
  may drift (`tdb validate` catches renames).

## Contamination notes

- gpt-5.6-sol and claude-opus-5-5 both **wrote questions and, via their harnesses (Codex,
  Claude Code), produced every `datasets_v1` label**. Their own questions are therefore
  labelled partly by themselves.
- gpt-5.6-luna wrote 69 questions, and `openai/gpt-6-luna-decisions` (the same model line)
  is one of the evaluated routers.
- `claude_v2` is entirely written and labelled by Claude-family models; prefer `datasets_v1`
  when evaluating Claude-based routers.
- The report shows accuracy per writer model and a table without these writers. Change the
  excluded writers with `tdb report <run_dir> --exclude-generators gpt-5.6-sol,claude-opus-5-5,gpt-5.6-luna`
  (`''` for none).

## Maintenance and versioning

- **Version:** `datasets_v1` as of this card (696 questions, test split frozen 2026-10-10).
- **Do not edit the split.** Add new questions to `dev`, or release a new version with its own
  split. Changing `SPLIT_SEED` or `splits/test_qids.txt` invalidates published numbers.
- **After any data change:** run `scripts/import_datasets.py`, then
  `scripts/build_benchmark.py`, `tdb validate` and `uv run pytest`. The tests fail on gold
  tool names leaking into questions, on qid or split inconsistencies, and on stale build
  outputs.
- **Re-pull catalogs** with `tdb pull` when servers change.
- **Planned work:**
  - human review of all labels, including the test split, the 80 bot-written no-tool
    questions and the 14 rewrites;
  - a slot-grouped split;
  - authenticated servers for a 150+ real-tool tier;
  - closing the coverage gaps above.

## License

MIT (see `LICENSE`), copyright 2026 Sarath Chandra Bellam. Questions were generated with
third-party models, and tool descriptions come from the public MCP servers listed above;
check those providers' terms before redistributing outputs commercially.

## Citation

No paper yet. Cite the repository using `CITATION.cff` (GitHub's "Cite this repository"):
Bellam, S. C. *ToolDiscoveryBench: benchmarking routers that pick the right MCP tool*,
v0.1.0, 2026. https://github.com/SarathChandraBellam/ToolDiscoveryBench
