# Metrics

Each row in `runs/<ts>/results.jsonl` is one (router, catalog size, question, repeat).
`summary.json` aggregates rows per (router, catalog size).

| Metric | Definition |
|---|---|
| `top1`, `top3`, `top5` | Share of questions where a gold tool is ranked within the first 1, 3 or 5. Any tool in `gold` counts. |
| `mrr` | Mean reciprocal rank of the first gold tool (0 when absent). |
| `server_top1` | Top-1 tool is on a gold tool's server, even if it's the wrong tool there. |
| `lat_p50_ms`, `lat_p95_ms` | Wall-clock per question, including every upstream call and retry. One warm-up call per router is excluded. |
| `calls_mean` | Upstream API calls per question. BM25 and embeddings are 0. |
| `in_tokens_mean` | Input tokens reported by the provider. |
| `usd_per_1k_q` | `in_tokens_mean × usd_per_m_input / 1e6 × 1000`. Input tokens only, since Jev bills input only. |
| `ece` | Expected calibration error of the top-1 probability over 10 bins. Calibrated routers only. |
| `brier` | Mean squared error between top-1 probability and correctness. Calibrated routers only. |
| `conf_right`, `conf_wrong` | Mean top-1 probability when right vs wrong. A wide gap supports an abstain threshold. |

The report also breaks top-1 accuracy down by question tag. Tags of the form
`hard_negative:<x>` are pooled as `hard_negative`.

## Reading the results

- Compare routers **at the same catalog size**; accuracy always falls as size grows.
- Use `top3` when the router feeds an agent a shortlist, and `top1` when it picks one tool.
- For Jev, look at `conf_wrong`. If wrong answers come with low probability, a threshold can
  route only uncertain questions to a slower model.
- Small golden sets are noisy. With 50 questions, one question is 2 points of accuracy.
