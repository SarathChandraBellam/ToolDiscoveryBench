# Changelog

## v0.1.0 (2026-10-10)

The first public release.

### Added

- **Decision-model routers** (#2). An `openrouter` router for TypeSafe Jev (`typesafe/jev-1.13`) and
  GPT-6 Luna Decisions, with cost measured from `usage.cost`. Direct `jev` and
  `openai_decisions` routers. A shared `DecisionRouter` with `flat`, `factored` and
  `hierarchical` modes and a "none of these tools" option for abstention.
- **Strands Hugging Face provider** (#2) for open-weight models through HF Inference Providers.
- **`datasets_v1` golden suites** (#2). `one_server`, `multi_server` and `multi_confused`
  share 696 unique questions: 616 written by nine models and labelled from the first tool
  that Claude Code and Codex called, plus 80 synthetic near-miss no-tool questions marked
  for human review. Stable `qid`s, a frozen 30% test split and `data/golden/questions.jsonl`
  are included.
- **Evaluation** (#2). `tdb run --split test --repeats N`, abstention metrics (no-tool
  caught, false abstain), per-router refusal rate, bootstrap 95% CIs on top-1, per-author
  and contamination tables (`tdb report --exclude-generators`).
- **`escalate` router** (#4). Jev flat answers when confident; otherwise a frontier LLM
  (Strands via OpenRouter) answers. Defaults to `escalate_below=0.85`, tuned on dev with
  `scripts/escalation_curve.py`.
- **`shortlist` router** (#4). A retriever keeps the top `k` tools and Jev flat decides.
  Defaults to `k=10`, chosen on dev with `scripts/shortlist_recall.py`.
- **Fit question** (#5). `abstain_question: true` for `factored` mode asks a separate
  "does any listed tool fit?" question in the same request. On the test split it lifts Jev
  factored's no-tool catches from 74 / 61 / 54% to 98 / 94 / 86%. It is opt-in, and the
  default behaviour is unchanged.
- **Launch docs.** README results from the frozen test split, a results snapshot in
  `results/2026-10-10/`, `scripts/combine_runs.py`, `CITATION.cff` and this changelog.

### Fixed

- Factored mode survives per-server refusals from the backend, and refusals are reported (#2).
- Abstention is scored on the same scale for every router, and an abstention counts as a
  miss at every cutoff (#2).
