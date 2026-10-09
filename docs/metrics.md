# Metrics

Each row in `runs/<ts>/results.jsonl` is one (router, suite, catalog size, question, repeat).
`summary.json` aggregates rows per (router, suite, catalog size). Suites with per-question
catalogs report size `fixed`.

Questions are either **answerable** (`gold` lists the right first tool) or **no-tool**
(`gold` is empty: nothing in the catalog fits, so the right behaviour is to abstain).

| Metric | Definition |
|---|---|
| `accuracy` | Over all questions: answerable ones need the gold tool picked first, no-tool ones need an abstain. |
| `top1` | Answerable only: not abstained and the pick is a gold tool. |
| `lenient1` | Like `top1`, but tools judged *acceptable* also count. |
| `top3` | Answerable only: a gold tool is in the first 3 of the ranking. |
| `abstain_recall` | No-tool questions where the router abstained. |
| `false_abstain` | Answerable questions where the router abstained. |
| `mrr` | Mean reciprocal rank of the first gold tool (0 when absent). |
| `server_top1` | Top-1 tool is on a gold tool's server, even if it's the wrong tool there. |
| `lat_p50_ms`, `lat_p95_ms` | Wall-clock per question, including every upstream call and retry. One warm-up call per router is excluded. |
| `calls_mean` | Upstream API calls per question. BM25 and embeddings are 0. |
| `in_tokens_mean` | Input tokens reported by the provider. |
| `usd_per_1k_q` | `in_tokens_mean × usd_per_m_input / 1e6 × 1000`. Input tokens only: Jev and OpenAI Decisions bill input only. |
| `ece` | Expected calibration error of the top-1 probability over 10 bins. Calibrated routers only. |
| `brier` | Mean squared error between top-1 probability and correctness. Calibrated routers only. |
| `conf_right`, `conf_wrong` | Mean top-1 probability when right vs wrong. A wide gap supports an abstain threshold. |

The report also breaks accuracy down by question tag (`confusable`, `judges_split`,
`no_tool`, `generator:<family>`, ...; `hard_negative:<x>` pools as `hard_negative`) and by
the model family and exact model that wrote the question. It also has:

- **Top-1 with 95% bootstrap confidence intervals** (1,000 seeded resamples over questions,
  repeats averaged per question), for all answerable questions and for the frozen `test`
  split (`data/golden/splits/test_qids.txt`).
- **Accuracy without possibly contaminated questions**: the same groups with questions by the
  label judges (gpt-5.6-sol, claude-opus-5-5) and gpt-5.6-luna removed. Change the list with
  `tdb report <run_dir> --exclude-generators a,b` (`''` for none).

## Reading the results

- Compare routers **at the same catalog size**; accuracy always falls as size grows.
- Use `top3` when the router feeds an agent a shortlist, and `top1` when it picks one tool.
- For decision models, look at `conf_wrong` and `abstain_recall`. If wrong answers come with low probability, a threshold can
  route only uncertain questions to a slower model.
- Small golden sets are noisy. With 50 questions, one question is 2 points of accuracy. Read
  the bootstrap intervals before calling a difference real.
- Published numbers should come from the `test` split with `repeats: 3` or more, and with
  pinned model versions (`jev-1.13`, not `jev-latest`).
