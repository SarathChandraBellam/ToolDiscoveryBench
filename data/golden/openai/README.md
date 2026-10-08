# OpenAI-labeled golden set (not run yet)

Same questions and catalog as every family (`../shared/`), labeled by OpenAI models.

Planned outputs, mirroring `../claude/`:

- `labeling/votes_<model>.jsonl` for each labeler (e.g. a small, a mid and a reasoning model)
- `labeling/executions.jsonl`, `labeling/judge_pack.jsonl`, `labeling/judgments.jsonl`
- `golden_v2.jsonl`, `review_v2.jsonl`, `labeling_report_v2.json`

Run with `--family openai --models <name1>,<name2>,<name3>`; see `../README.md`.
