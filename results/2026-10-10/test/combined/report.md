# ToolDiscoveryBench — combined test-split snapshot (2026-10-10)

## Accuracy

| router | suite | tools | n | no-tool | err | **acc** | top-1 | lenient | top-3 | server@1 | abstain ✓ | false abstain | refused |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| bm25 | multi_confused | fixed | 393 | 87 | 0 | **42.0%** | 53.9% | 67.6% | 79.4% | 74.5% | 0.0% | 0.0% | 0.0% |
| bm25 | multi_server | fixed | 618 | 132 | 0 | **49.0%** | 62.3% | 69.8% | 87.7% | 82.1% | 0.0% | 0.0% | 0.0% |
| bm25 | one_server | fixed | 618 | 132 | 0 | **56.3%** | 71.6% | 82.7% | 94.4% | 100.0% | 0.0% | 0.0% | 0.0% |
| bm25-abstain | multi_confused | fixed | 393 | 87 | 0 | **42.7%** | 53.9% | 67.6% | 79.4% | 74.5% | 3.4% | 0.0% | 0.0% |
| bm25-abstain | multi_server | fixed | 618 | 132 | 0 | **50.0%** | 62.3% | 69.8% | 87.7% | 81.5% | 4.5% | 0.6% | 0.0% |
| bm25-abstain | one_server | fixed | 618 | 132 | 0 | **56.3%** | 59.9% | 68.5% | 79.0% | 80.9% | 43.2% | 19.1% | 0.0% |
| embed-bge-small | multi_confused | fixed | 393 | 87 | 0 | **47.3%** | 60.8% | 66.7% | 82.4% | 78.4% | 0.0% | 0.0% | 0.0% |
| embed-bge-small | multi_server | fixed | 618 | 132 | 0 | **51.5%** | 65.4% | 69.8% | 89.5% | 84.6% | 0.0% | 0.0% | 0.0% |
| embed-bge-small | one_server | fixed | 618 | 132 | 0 | **58.3%** | 74.1% | 81.5% | 98.1% | 100.0% | 0.0% | 0.0% | 0.0% |
| or-jev-factored | multi_confused | fixed | 393 | 87 | 0 | **80.4%** | 87.9% | 93.5% | 95.8% | 95.4% | 54.0% | 2.3% | 0.0% |
| or-jev-factored | multi_server | fixed | 618 | 132 | 0 | **83.2%** | 89.1% | 94.4% | 97.5% | 96.3% | 61.4% | 0.6% | 0.0% |
| or-jev-factored | one_server | fixed | 618 | 132 | 0 | **88.0%** | 91.8% | 97.1% | 99.4% | 99.4% | 74.2% | 0.6% | 0.0% |
| or-jev-factored-fitq | multi_confused | fixed | 393 | 87 | 0 | **88.0%** | 88.6% | 96.1% | 98.0% | 98.0% | 86.2% | 0.0% | 0.0% |
| or-jev-factored-fitq | multi_server | fixed | 618 | 132 | 0 | **89.6%** | 88.5% | 94.0% | 96.7% | 95.7% | 93.9% | 1.4% | 0.0% |
| or-jev-factored-fitq | one_server | fixed | 618 | 132 | 0 | **92.4%** | 90.9% | 96.5% | 98.8% | 98.8% | 97.7% | 1.2% | 0.0% |
| or-jev-flat | multi_confused | fixed | 393 | 87 | 0 | **84.5%** | 85.6% | 94.8% | 97.7% | 98.0% | 80.5% | 0.0% | 0.0% |
| or-jev-flat | multi_server | fixed | 618 | 132 | 0 | **90.0%** | 91.6% | 95.5% | 97.5% | 97.9% | 84.1% | 0.6% | 0.0% |
| or-jev-flat | one_server | fixed | 618 | 132 | 0 | **91.3%** | 91.4% | 96.9% | 99.4% | 99.4% | 90.9% | 0.6% | 0.0% |
| or-luna-factored | multi_confused | fixed | 393 | 87 | 0 | **80.9%** | 81.4% | 95.1% | 97.1% | 96.1% | 79.3% | 1.0% | 23.7% |
| or-luna-factored | multi_server | fixed | 618 | 132 | 0 | **85.9%** | 87.0% | 94.4% | 95.1% | 96.3% | 81.8% | 2.5% | 20.9% |
| or-luna-factored | one_server | fixed | 618 | 132 | 0 | **87.9%** | 88.9% | 96.9% | 99.4% | 100.0% | 84.1% | 0.0% | 1.0% |
| or-luna-flat | multi_confused | fixed | 393 | 87 | 0 | **80.9%** | 76.5% | 93.1% | 98.0% | 98.0% | 96.6% | 0.0% | 0.0% |
| or-luna-flat | multi_server | fixed | 618 | 132 | 0 | **89.8%** | 87.7% | 95.7% | 95.7% | 98.1% | 97.7% | 1.2% | 0.0% |
| or-luna-flat | one_server | fixed | 618 | 132 | 0 | **90.3%** | 88.9% | 96.9% | 99.4% | 99.4% | 95.5% | 0.6% | 0.0% |

*acc: answerable questions need the gold tool first, no-tool questions need an abstain. top-1 / lenient / top-3 / server@1 are over answerable questions only; lenient also accepts tools labelled acceptable. abstain ✓: share of no-tool questions where the router abstained. false abstain: share of answerable ones where it did. refused: share of questions where the backend refused a per-server sub-question (scored as P = 0 for that server, which can flatter accuracy).*

## Speed, cost and calibration

| router | suite | tools | p50 ms | p95 ms | calls | in-tok | $/1k q | ECE | Brier | conf ✓ | conf ✗ |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| bm25 | multi_confused | fixed | 1 | 1 | 0.000 | – | – | – | – | – | – |
| bm25 | multi_server | fixed | 1 | 1 | 0.000 | – | – | – | – | – | – |
| bm25 | one_server | fixed | 0 | 0 | 0.000 | – | – | – | – | – | – |
| bm25-abstain | multi_confused | fixed | 1 | 1 | 0.000 | – | – | – | – | – | – |
| bm25-abstain | multi_server | fixed | 1 | 1 | 0.000 | – | – | – | – | – | – |
| bm25-abstain | one_server | fixed | 0 | 0 | 0.000 | – | – | – | – | – | – |
| embed-bge-small | multi_confused | fixed | 4 | 8 | 0.000 | – | – | – | – | – | – |
| embed-bge-small | multi_server | fixed | 5 | 8 | 0.000 | – | – | – | – | – | – |
| embed-bge-small | one_server | fixed | 5 | 10 | 0.000 | – | – | – | – | – | – |
| or-jev-factored | multi_confused | fixed | 221 | 312 | 1.000 | 1,827 | 0.077 | 0.056 | 0.111 | 0.888 | 0.588 |
| or-jev-factored | multi_server | fixed | 220 | 291 | 1.000 | 1,674 | 0.070 | 0.057 | 0.089 | 0.924 | 0.579 |
| or-jev-factored | one_server | fixed | 217 | 299 | 1.000 | 715 | 0.030 | 0.048 | 0.076 | 0.925 | 0.616 |
| or-jev-factored-fitq | multi_confused | fixed | 163 | 223 | 1.000 | 2,688 | 0.113 | 0.062 | 0.114 | 0.899 | 0.744 |
| or-jev-factored-fitq | multi_server | fixed | 161 | 218 | 1.000 | 2,440 | 0.102 | 0.053 | 0.072 | 0.934 | 0.663 |
| or-jev-factored-fitq | one_server | fixed | 156 | 218 | 1.000 | 906 | 0.038 | 0.046 | 0.062 | 0.952 | 0.742 |
| or-jev-flat | multi_confused | fixed | 230 | 314 | 1.000 | 1,360 | 0.057 | 0.040 | 0.100 | 0.910 | 0.597 |
| or-jev-flat | multi_server | fixed | 225 | 308 | 1.000 | 1,246 | 0.052 | 0.034 | 0.072 | 0.929 | 0.648 |
| or-jev-flat | one_server | fixed | 221 | 299 | 1.000 | 619 | 0.026 | 0.030 | 0.070 | 0.947 | 0.718 |
| or-luna-factored | multi_confused | fixed | 190 | 395 | 1.000 | 1,660 | 0.166 | 0.106 | 0.154 | 0.890 | 0.715 |
| or-luna-factored | multi_server | fixed | 188 | 420 | 1.000 | 1,504 | 0.150 | 0.050 | 0.088 | 0.914 | 0.647 |
| or-luna-factored | one_server | fixed | 171 | 246 | 1.000 | 540 | 0.054 | 0.050 | 0.089 | 0.932 | 0.663 |
| or-luna-flat | multi_confused | fixed | 196 | 268 | 1.000 | 1,021 | 0.102 | 0.141 | 0.165 | 0.908 | 0.742 |
| or-luna-flat | multi_server | fixed | 196 | 270 | 1.000 | 920 | 0.092 | 0.075 | 0.099 | 0.903 | 0.743 |
| or-luna-flat | one_server | fixed | 194 | 274 | 1.000 | 389 | 0.039 | 0.071 | 0.099 | 0.936 | 0.833 |

*Calibration columns are filled only for calibrated routers (Jev). conf ✓ / ✗ is the mean top-1 probability when right vs wrong; a big gap lets you set an abstain threshold.*

## Top-1 with 95% bootstrap confidence intervals

| router | suite | tools | n | top-1 | 95% CI | test n | test top-1 | test 95% CI |
|---|---|---:|---:|---:|---|---:|---:|---|
| bm25 | multi_confused | fixed | 102 | 53.9% | 43.1%–63.7% | 102 | 53.9% | 43.1%–63.7% |
| bm25 | multi_server | fixed | 162 | 62.3% | 54.3%–69.8% | 162 | 62.3% | 54.3%–69.8% |
| bm25 | one_server | fixed | 162 | 71.6% | 63.6%–77.8% | 162 | 71.6% | 63.6%–77.8% |
| bm25-abstain | multi_confused | fixed | 102 | 53.9% | 43.1%–63.7% | 102 | 53.9% | 43.1%–63.7% |
| bm25-abstain | multi_server | fixed | 162 | 62.3% | 54.3%–69.8% | 162 | 62.3% | 54.3%–69.8% |
| bm25-abstain | one_server | fixed | 162 | 59.9% | 51.9%–67.3% | 162 | 59.9% | 51.9%–67.3% |
| embed-bge-small | multi_confused | fixed | 102 | 60.8% | 51.0%–69.6% | 102 | 60.8% | 51.0%–69.6% |
| embed-bge-small | multi_server | fixed | 162 | 65.4% | 57.4%–72.8% | 162 | 65.4% | 57.4%–72.8% |
| embed-bge-small | one_server | fixed | 162 | 74.1% | 66.7%–80.9% | 162 | 74.1% | 66.7%–80.9% |
| or-jev-factored | multi_confused | fixed | 102 | 87.9% | 80.7%–93.8% | 102 | 87.9% | 80.7%–93.8% |
| or-jev-factored | multi_server | fixed | 162 | 89.1% | 84.2%–93.4% | 162 | 89.1% | 84.2%–93.4% |
| or-jev-factored | one_server | fixed | 162 | 91.8% | 87.4%–95.7% | 162 | 91.8% | 87.4%–95.7% |
| or-jev-factored-fitq | multi_confused | fixed | 102 | 88.6% | 81.7%–94.1% | 102 | 88.6% | 81.7%–94.1% |
| or-jev-factored-fitq | multi_server | fixed | 162 | 88.5% | 83.1%–93.0% | 162 | 88.5% | 83.1%–93.0% |
| or-jev-factored-fitq | one_server | fixed | 162 | 90.9% | 86.4%–94.9% | 162 | 90.9% | 86.4%–94.9% |
| or-jev-flat | multi_confused | fixed | 102 | 85.6% | 79.1%–91.8% | 102 | 85.6% | 79.1%–91.8% |
| or-jev-flat | multi_server | fixed | 162 | 91.6% | 87.2%–95.5% | 162 | 91.6% | 87.2%–95.5% |
| or-jev-flat | one_server | fixed | 162 | 91.4% | 87.0%–95.1% | 162 | 91.4% | 87.0%–95.1% |
| or-luna-factored | multi_confused | fixed | 102 | 81.4% | 73.5%–88.2% | 102 | 81.4% | 73.5%–88.2% |
| or-luna-factored | multi_server | fixed | 162 | 87.0% | 81.5%–92.0% | 162 | 87.0% | 81.5%–92.0% |
| or-luna-factored | one_server | fixed | 162 | 88.9% | 84.0%–93.2% | 162 | 88.9% | 84.0%–93.2% |
| or-luna-flat | multi_confused | fixed | 102 | 76.5% | 68.6%–84.3% | 102 | 76.5% | 68.6%–84.3% |
| or-luna-flat | multi_server | fixed | 162 | 87.7% | 82.1%–92.0% | 162 | 87.7% | 82.1%–92.0% |
| or-luna-flat | one_server | fixed | 162 | 88.9% | 84.0%–93.2% | 162 | 88.9% | 84.0%–93.2% |

*Answerable questions only; 1000 seeded resamples over questions (repeats averaged per question). *test* is the frozen held-out split (`data/golden/splits/test_qids.txt`); publish numbers from it with repeats ≥ 3.*

## Accuracy by question tag (all suites and sizes pooled)

| router | confusable | generator:claude | generator:cursor-bot | generator:openai | judges_split | multi_server | multi_server_confused | needs_human_review | no_tool | one_server | relabelled | rewritten | split:test |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| or-jev-flat | 85.8% | 84.7% | 89.7% | 92.8% | 56.5% | 90.0% | 84.5% | 89.7% | 85.8% | 91.3% | 53.1% | 100.0% | 89.1% |
| or-jev-factored | 82.9% | 83.3% | 60.7% | 93.4% | 56.5% | 83.2% | 80.4% | 60.7% | 64.4% | 88.0% | 53.1% | 100.0% | 84.3% |
| or-jev-factored-fitq | 86.2% | 86.1% | 94.8% | 92.4% | 53.7% | 89.6% | 88.0% | 94.8% | 93.4% | 92.4% | 53.1% | 100.0% | 90.3% |
| or-luna-flat | 81.9% | 78.4% | 98.8% | 92.3% | 30.6% | 89.8% | 80.9% | 98.8% | 96.6% | 90.3% | 29.6% | 100.0% | 87.8% |
| or-luna-factored | 81.9% | 77.5% | 84.5% | 92.7% | 38.9% | 85.9% | 80.9% | 84.5% | 82.1% | 87.9% | 33.3% | 100.0% | 85.5% |
| embed-bge-small | 59.3% | 53.5% | 0.0% | 70.7% | 13.9% | 51.5% | 47.3% | 0.0% | 0.0% | 58.3% | 0.0% | 100.0% | 53.0% |
| bm25 | 54.9% | 46.9% | 0.0% | 69.9% | 16.7% | 49.0% | 42.0% | 0.0% | 0.0% | 56.3% | 7.4% | 66.7% | 50.1% |
| bm25-abstain | 51.9% | 45.5% | 16.7% | 66.7% | 19.4% | 50.0% | 42.7% | 16.7% | 18.8% | 56.3% | 7.4% | 66.7% | 50.6% |

## Accuracy by question author (model family that wrote the question)

| router | claude | cursor | gpt |
|---|---:|---:|---:|
| bm25 | 46.9% | 0.0% | 69.9% |
| bm25-abstain | 45.5% | 16.7% | 66.7% |
| embed-bge-small | 53.5% | 0.0% | 70.7% |
| or-jev-factored | 83.3% | 60.7% | 93.4% |
| or-jev-factored-fitq | 86.1% | 94.8% | 92.4% |
| or-jev-flat | 84.7% | 89.7% | 92.8% |
| or-luna-factored | 77.5% | 84.5% | 92.7% |
| or-luna-flat | 78.4% | 98.8% | 92.3% |

## Accuracy by question author (exact model)

| router | claude-fable-5-1 | claude-haiku-4-5 | claude-opus-5-5 | claude-sonnet-5-5 | cursor-bot | gpt-5.5 | gpt-5.6-luna | gpt-5.6-sol | gpt-5.6-terra | gpt-6-astra |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| bm25 | 60.3% | 33.3% | 74.4% | 17.1% | 0.0% | 75.0% | 72.6% | 56.1% | 78.5% | 56.7% |
| bm25-abstain | 57.5% | 33.3% | 76.9% | 12.2% | 16.7% | 72.9% | 69.4% | 53.7% | 73.8% | 53.3% |
| embed-bge-small | 52.1% | 45.0% | 66.7% | 56.1% | 0.0% | 64.6% | 79.0% | 65.9% | 69.2% | 73.3% |
| or-jev-factored | 83.1% | 83.9% | 87.2% | 78.9% | 60.7% | 95.8% | 92.5% | 91.1% | 95.4% | 90.0% |
| or-jev-factored-fitq | 84.0% | 82.2% | 99.1% | 82.9% | 94.8% | 100.0% | 91.9% | 90.2% | 89.2% | 91.1% |
| or-jev-flat | 83.1% | 83.9% | 97.4% | 76.4% | 89.7% | 95.8% | 96.2% | 86.2% | 91.3% | 93.3% |
| or-luna-factored | 82.2% | 70.0% | 89.7% | 68.3% | 84.5% | 93.8% | 93.5% | 90.2% | 95.4% | 86.7% |
| or-luna-flat | 83.6% | 63.3% | 97.4% | 73.2% | 98.8% | 97.9% | 91.9% | 92.7% | 89.2% | 90.0% |

## Accuracy without possibly contaminated questions

| router | suite | tools | n | acc | top-1 | n kept | acc kept | top-1 kept |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| bm25 | multi_confused | fixed | 393 | 42.0% | 53.9% | 303 | 32.7% | 45.8% |
| bm25 | multi_server | fixed | 618 | 49.0% | 62.3% | 450 | 43.3% | 58.0% |
| bm25 | one_server | fixed | 618 | 56.3% | 71.6% | 450 | 51.3% | 68.8% |
| bm25-abstain | multi_confused | fixed | 393 | 42.7% | 53.9% | 303 | 33.7% | 45.8% |
| bm25-abstain | multi_server | fixed | 618 | 50.0% | 62.3% | 450 | 44.7% | 58.0% |
| bm25-abstain | one_server | fixed | 618 | 56.3% | 59.9% | 450 | 52.7% | 56.2% |
| embed-bge-small | multi_confused | fixed | 393 | 47.3% | 60.8% | 303 | 38.6% | 54.2% |
| embed-bge-small | multi_server | fixed | 618 | 51.5% | 65.4% | 450 | 46.0% | 61.6% |
| embed-bge-small | one_server | fixed | 618 | 58.3% | 74.1% | 450 | 52.0% | 69.6% |
| or-jev-factored | multi_confused | fixed | 393 | 80.4% | 87.9% | 303 | 76.6% | 85.6% |
| or-jev-factored | multi_server | fixed | 618 | 83.2% | 89.1% | 450 | 81.3% | 89.3% |
| or-jev-factored | one_server | fixed | 618 | 88.0% | 91.8% | 450 | 86.7% | 91.4% |
| or-jev-factored-fitq | multi_confused | fixed | 393 | 88.0% | 88.6% | 303 | 85.5% | 85.2% |
| or-jev-factored-fitq | multi_server | fixed | 618 | 89.6% | 88.5% | 450 | 89.3% | 87.8% |
| or-jev-factored-fitq | one_server | fixed | 618 | 92.4% | 90.9% | 450 | 91.6% | 89.6% |
| or-jev-flat | multi_confused | fixed | 393 | 84.5% | 85.6% | 303 | 82.5% | 83.3% |
| or-jev-flat | multi_server | fixed | 618 | 90.0% | 91.6% | 450 | 88.4% | 89.9% |
| or-jev-flat | one_server | fixed | 618 | 91.3% | 91.4% | 450 | 90.0% | 90.2% |
| or-luna-factored | multi_confused | fixed | 393 | 80.9% | 81.4% | 303 | 78.2% | 77.8% |
| or-luna-factored | multi_server | fixed | 618 | 85.9% | 87.0% | 450 | 84.0% | 84.8% |
| or-luna-factored | one_server | fixed | 618 | 87.9% | 88.9% | 450 | 86.0% | 87.5% |
| or-luna-flat | multi_confused | fixed | 393 | 80.9% | 76.5% | 303 | 79.2% | 72.2% |
| or-luna-flat | multi_server | fixed | 618 | 89.8% | 87.7% | 450 | 87.3% | 83.9% |
| or-luna-flat | one_server | fixed | 618 | 90.3% | 88.9% | 450 | 88.7% | 86.6% |

*kept: questions not written by `gpt-5.6-sol`, `claude-opus-5-5`, `gpt-5.6-luna` (judges of the labels, or the same model line as a router under test).*

## Misses (repeat 0, first 200)

| router | suite | tools | item | picked | p | gold |
|---|---|---:|---|---|---:|---|
| bm25 | multi_confused | fixed | claude-fable-5-1-006@multi_server_confused | `kiwi.feedback-to-devs` | 3.714 | `aws-knowledge.aws___search_documentation` |
| bm25 | multi_confused | fixed | claude-fable-5-1-020@multi_server_confused | `svelte.playground-link` | 2.790 | `context7.query-docs` |
| bm25 | multi_confused | fixed | claude-fable-5-1-022@multi_server_confused | `context7.resolve-library-id` | 4.620 | `deepwiki.ask_wiki_question` |
| bm25 | multi_confused | fixed | claude-fable-5-1-024@multi_server_confused | `deepwiki.ask_wiki_question` | 6.461 | `deepwiki.read_wiki_contents` |
| bm25 | multi_confused | fixed | claude-fable-5-1-026@multi_server_confused | `deepwiki.read_wiki_contents` | 6.511 | `deepwiki.read_wiki_structure` |
| bm25 | multi_confused | fixed | claude-fable-5-1-030@multi_server_confused | `gitmcp.fetch_generic_url_content` | 3.135 | `gitmcp.fetch_generic_documentation` |
| bm25 | multi_confused | fixed | claude-fable-5-1-055@multi_server_confused | `svelte.get-documentation` | 12.717 | `svelte.list-sections` |
| bm25 | multi_confused | fixed | claude-fable-5-1-061@multi_server_confused | `kiwi.search-flight` | 9.522 | `svelte.svelte-autofixer` |
| bm25 | multi_confused | fixed | claude-haiku-4-5-002@multi_server_confused | `context7.query-docs` | 4.115 | *abstain* |
| bm25 | multi_confused | fixed | claude-haiku-4-5-010@multi_server_confused | `aws-knowledge.aws___list_regions` | 4.032 | `aws-knowledge.aws___get_regional_availability` |
| bm25 | multi_confused | fixed | claude-haiku-4-5-019@multi_server_confused | `svelte.get-documentation` | 3.055 | `context7.resolve-library-id` |
| bm25 | multi_confused | fixed | claude-haiku-4-5-020@multi_server_confused | `context7.query-docs` | 4.371 | `context7.resolve-library-id` |
| bm25 | multi_confused | fixed | claude-haiku-4-5-030@multi_server_confused | `gitmcp.fetch_generic_documentation` | 2.099 | `gitmcp.match_common_libs_owner_repo_mapping` |
| bm25 | multi_confused | fixed | claude-haiku-4-5-031@multi_server_confused | `huggingface.hub_repo_search` | 3.587 | `gitmcp.search_generic_documentation` |
| bm25 | multi_confused | fixed | claude-haiku-4-5-033@multi_server_confused | `kiwi.feedback-to-devs` | 3.586 | `gitmcp.match_common_libs_owner_repo_mapping` |
| bm25 | multi_confused | fixed | claude-haiku-4-5-034@multi_server_confused | `deepwiki.ask_wiki_question` | 3.144 | `gitmcp.match_common_libs_owner_repo_mapping` |
| bm25 | multi_confused | fixed | claude-haiku-4-5-035@multi_server_confused | `aws-knowledge.aws___read_documentation` | 7.554 | `gitmcp.fetch_generic_url_content` |
| bm25 | multi_confused | fixed | claude-haiku-4-5-036@multi_server_confused | `svelte.playground-link` | 4.911 | `gitmcp.fetch_generic_url_content` |
| bm25 | multi_confused | fixed | claude-haiku-4-5-044@multi_server_confused | `huggingface.hub_repo_search` | 4.800 | `huggingface.hf_fs` |
| bm25 | multi_confused | fixed | claude-haiku-4-5-050@multi_server_confused | `kiwi.feedback-to-devs` | 2.545 | `microsoft-learn.microsoft_docs_search` |
| bm25 | multi_confused | fixed | claude-haiku-4-5-053@multi_server_confused | `microsoft-learn.microsoft_docs_fetch` | 8.159 | `microsoft-learn.microsoft_docs_search` |
| bm25 | multi_confused | fixed | claude-haiku-4-5-056@multi_server_confused | `svelte.get-documentation` | 6.920 | `svelte.list-sections` |
| bm25 | multi_confused | fixed | claude-opus-5-5-031@multi_server_confused | `gitmcp.match_common_libs_owner_repo_mapping` | 4.791 | `gitmcp.search_generic_documentation` |
| bm25 | multi_confused | fixed | claude-sonnet-5-5-012@multi_server_confused | `aws-knowledge.aws___search_documentation` | 10.347 | `aws-knowledge.aws___retrieve_skill` |
| bm25 | multi_confused | fixed | claude-sonnet-5-5-013@multi_server_confused | `huggingface.hf_fs` | 3.604 | `cloudflare-docs.search_cloudflare_documentation` |
| bm25 | multi_confused | fixed | claude-sonnet-5-5-023@multi_server_confused | `deepwiki.read_wiki_structure` | 4.213 | `deepwiki.read_wiki_contents` |
| bm25 | multi_confused | fixed | claude-sonnet-5-5-024@multi_server_confused | `svelte.playground-link` | 5.171 | `deepwiki.read_wiki_contents` |
| bm25 | multi_confused | fixed | claude-sonnet-5-5-035@multi_server_confused | `aws-knowledge.aws___read_documentation` | 6.081 | `gitmcp.fetch_generic_url_content` |
| bm25 | multi_confused | fixed | claude-sonnet-5-5-040@multi_server_confused | `deepwiki.ask_wiki_question` | 2.776 | `huggingface.hub_repo_search` |
| bm25 | multi_confused | fixed | claude-sonnet-5-5-052@multi_server_confused | `context7.resolve-library-id` | 4.856 | `microsoft-learn.microsoft_code_sample_search` |
| bm25 | multi_confused | fixed | claude-sonnet-5-5-055@multi_server_confused | `svelte.get-documentation` | 10.208 | `svelte.list-sections` |
| bm25 | multi_confused | fixed | cursor-bot-001@multi_server_confused | `astro-docs.search_astro_docs` | 4.690 | *abstain* |
| bm25 | multi_confused | fixed | cursor-bot-002@multi_server_confused | `astro-docs.search_astro_docs` | 4.623 | *abstain* |
| bm25 | multi_confused | fixed | cursor-bot-004@multi_server_confused | `astro-docs.search_astro_docs` | 4.623 | *abstain* |
| bm25 | multi_confused | fixed | cursor-bot-006@multi_server_confused | `astro-docs.search_astro_docs` | 4.822 | *abstain* |
| bm25 | multi_confused | fixed | cursor-bot-011@multi_server_confused | `kiwi.feedback-to-devs` | 2.740 | *abstain* |
| bm25 | multi_confused | fixed | cursor-bot-013@multi_server_confused | `aws-knowledge.aws___read_documentation` | 2.010 | *abstain* |
| bm25 | multi_confused | fixed | cursor-bot-014@multi_server_confused | `kiwi.feedback-to-devs` | 2.740 | *abstain* |
| bm25 | multi_confused | fixed | cursor-bot-024@multi_server_confused | `deepwiki.read_wiki_structure` | 0.000 | *abstain* |
| bm25 | multi_confused | fixed | cursor-bot-026@multi_server_confused | `context7.resolve-library-id` | 9.016 | *abstain* |
| bm25 | multi_confused | fixed | cursor-bot-033@multi_server_confused | `deepwiki.ask_wiki_question` | 11.841 | *abstain* |
| bm25 | multi_confused | fixed | cursor-bot-036@multi_server_confused | `deepwiki.read_wiki_structure` | 5.541 | *abstain* |
| bm25 | multi_confused | fixed | cursor-bot-043@multi_server_confused | `gitmcp.match_common_libs_owner_repo_mapping` | 4.698 | *abstain* |
| bm25 | multi_confused | fixed | cursor-bot-047@multi_server_confused | `gitmcp.match_common_libs_owner_repo_mapping` | 7.056 | *abstain* |
| bm25 | multi_confused | fixed | cursor-bot-048@multi_server_confused | `gitmcp.match_common_libs_owner_repo_mapping` | 4.698 | *abstain* |
| bm25 | multi_confused | fixed | cursor-bot-054@multi_server_confused | `huggingface.hub_repo_details` | 3.022 | *abstain* |
| bm25 | multi_confused | fixed | cursor-bot-055@multi_server_confused | `huggingface.hub_repo_details` | 5.415 | *abstain* |
| bm25 | multi_confused | fixed | cursor-bot-056@multi_server_confused | `huggingface.hub_repo_details` | 3.036 | *abstain* |
| bm25 | multi_confused | fixed | cursor-bot-057@multi_server_confused | `kiwi.feedback-to-devs` | 4.970 | *abstain* |
| bm25 | multi_confused | fixed | cursor-bot-058@multi_server_confused | `kiwi.search-flight` | 6.629 | *abstain* |
| bm25 | multi_confused | fixed | cursor-bot-064@multi_server_confused | `kiwi.feedback-to-devs` | 8.435 | *abstain* |
| bm25 | multi_confused | fixed | cursor-bot-068@multi_server_confused | `microsoft-learn.microsoft_code_sample_search` | 2.448 | *abstain* |
| bm25 | multi_confused | fixed | cursor-bot-069@multi_server_confused | `svelte.playground-link` | 2.195 | *abstain* |
| bm25 | multi_confused | fixed | cursor-bot-074@multi_server_confused | `svelte.svelte-autofixer` | 3.660 | *abstain* |
| bm25 | multi_confused | fixed | cursor-bot-075@multi_server_confused | `svelte.playground-link` | 7.249 | *abstain* |
| bm25 | multi_confused | fixed | cursor-bot-076@multi_server_confused | `svelte.svelte-autofixer` | 8.317 | *abstain* |
| bm25 | multi_confused | fixed | cursor-bot-078@multi_server_confused | `svelte.svelte-autofixer` | 5.568 | *abstain* |
| bm25 | multi_confused | fixed | cursor-bot-079@multi_server_confused | `svelte.get-documentation` | 4.847 | *abstain* |
| bm25 | multi_confused | fixed | cursor-bot-080@multi_server_confused | `svelte.playground-link` | 6.297 | *abstain* |
| bm25 | multi_confused | fixed | gpt-5.5-026@multi_server_confused | `deepwiki.ask_wiki_question` | 5.818 | `deepwiki.read_wiki_structure` |
| bm25 | multi_confused | fixed | gpt-5.5-030@multi_server_confused | `aws-knowledge.aws___read_documentation` | 7.996 | `gitmcp.fetch_generic_documentation` |
| bm25 | multi_confused | fixed | gpt-5.5-031@multi_server_confused | `astro-docs.search_astro_docs` | 1.137 | `gitmcp.search_generic_documentation` |
| bm25 | multi_confused | fixed | gpt-5.6-luna-007@multi_server_confused | `aws-knowledge.aws___get_regional_availability` | 8.893 | `aws-knowledge.aws___list_regions` |
| bm25 | multi_confused | fixed | gpt-5.6-luna-009@multi_server_confused | `context7.resolve-library-id` | 5.859 | `aws-knowledge.aws___get_regional_availability` |
| bm25 | multi_confused | fixed | gpt-5.6-luna-021@multi_server_confused | `kiwi.search-flight` | 6.053 | `deepwiki.ask_wiki_question` |
| bm25 | multi_confused | fixed | gpt-5.6-luna-026@multi_server_confused | `microsoft-learn.microsoft_code_sample_search` | 4.174 | `deepwiki.read_wiki_structure` |
| bm25 | multi_confused | fixed | gpt-5.6-sol-024@multi_server_confused | `deepwiki.ask_wiki_question` | 7.910 | `deepwiki.read_wiki_contents` |
| bm25 | multi_confused | fixed | gpt-5.6-sol-042@multi_server_confused | `huggingface.hf_whoami` | 3.164 | `huggingface.hub_repo_details` |
| bm25 | multi_confused | fixed | gpt-5.6-sol-049@multi_server_confused | `microsoft-learn.microsoft_code_sample_search` | 5.683 | `microsoft-learn.microsoft_docs_search` |
| bm25 | multi_confused | fixed | gpt-5.6-terra-006@multi_server_confused | `context7.resolve-library-id` | 6.228 | `aws-knowledge.aws___search_documentation` |
| bm25 | multi_confused | fixed | gpt-5.6-terra-031@multi_server_confused | `astro-docs.search_astro_docs` | 1.137 | `gitmcp.search_generic_documentation` |
| bm25 | multi_confused | fixed | gpt-5.6-terra-052@multi_server_confused | `aws-knowledge.aws___get_regional_availability` | 2.852 | `microsoft-learn.microsoft_code_sample_search` |
| bm25 | multi_confused | fixed | gpt-6-astra-009@multi_server_confused | `aws-knowledge.aws___read_documentation` | 4.664 | `aws-knowledge.aws___get_regional_availability` |
| bm25 | multi_confused | fixed | gpt-6-astra-014@multi_server_confused | `kiwi.feedback-to-devs` | 2.373 | `cloudflare-docs.search_cloudflare_documentation` |
| bm25 | multi_confused | fixed | gpt-6-astra-023@multi_server_confused | `deepwiki.ask_wiki_question` | 6.377 | `deepwiki.read_wiki_contents` |
| bm25 | multi_confused | fixed | gpt-6-astra-032@multi_server_confused | `svelte.list-sections` | 3.080 | `gitmcp.search_generic_documentation` |
| bm25 | multi_server | fixed | claude-fable-5-1-006@multi_server | `cloudflare-docs.search_cloudflare_documentation` | 4.624 | `aws-knowledge.aws___search_documentation` |
| bm25 | multi_server | fixed | claude-fable-5-1-020@multi_server | `aws-knowledge.aws___get_regional_availability` | 2.344 | `context7.query-docs` |
| bm25 | multi_server | fixed | claude-fable-5-1-022@multi_server | `context7.resolve-library-id` | 4.602 | `deepwiki.ask_wiki_question` |
| bm25 | multi_server | fixed | claude-fable-5-1-024@multi_server | `deepwiki.ask_wiki_question` | 8.019 | `deepwiki.read_wiki_contents` |
| bm25 | multi_server | fixed | claude-fable-5-1-026@multi_server | `deepwiki.read_wiki_contents` | 7.895 | `deepwiki.read_wiki_structure` |
| bm25 | multi_server | fixed | claude-fable-5-1-030@multi_server | `gitmcp.fetch_generic_url_content` | 3.173 | `gitmcp.fetch_generic_documentation` |
| bm25 | multi_server | fixed | claude-fable-5-1-033@multi_server | `huggingface.hf_fs` | 9.172 | `gitmcp.search_generic_code` |
| bm25 | multi_server | fixed | claude-fable-5-1-038@multi_server | `huggingface.hf_fs` | 5.115 | `huggingface.hf_whoami` |
| bm25 | multi_server | fixed | claude-fable-5-1-046@multi_server | `svelte.get-documentation` | 3.399 | `kiwi.search-flight` |
| bm25 | multi_server | fixed | claude-fable-5-1-055@multi_server | `svelte.get-documentation` | 15.088 | `svelte.list-sections` |
| bm25 | multi_server | fixed | claude-fable-5-1-061@multi_server | `huggingface.hf_fs` | 8.450 | `svelte.svelte-autofixer` |
| bm25 | multi_server | fixed | claude-fable-5-1-065@multi_server | `huggingface.hub_repo_details` | 0.000 | *abstain* |
| bm25 | multi_server | fixed | claude-fable-5-1-066@multi_server | `aws-knowledge.aws___get_regional_availability` | 2.074 | *abstain* |
| bm25 | multi_server | fixed | claude-haiku-4-5-002@multi_server | `astro-docs.search_astro_docs` | 3.932 | *abstain* |
| bm25 | multi_server | fixed | claude-haiku-4-5-010@multi_server | `aws-knowledge.aws___list_regions` | 3.689 | `aws-knowledge.aws___get_regional_availability` |
| bm25 | multi_server | fixed | claude-haiku-4-5-019@multi_server | `aws-knowledge.aws___get_regional_availability` | 2.595 | `context7.resolve-library-id` |
| bm25 | multi_server | fixed | claude-haiku-4-5-020@multi_server | `context7.query-docs` | 5.523 | `context7.resolve-library-id` |
| bm25 | multi_server | fixed | claude-haiku-4-5-030@multi_server | `gitmcp.fetch_generic_documentation` | 2.369 | `gitmcp.match_common_libs_owner_repo_mapping` |
| bm25 | multi_server | fixed | claude-haiku-4-5-031@multi_server | `gitmcp.match_common_libs_owner_repo_mapping` | 4.780 | `gitmcp.search_generic_documentation` |
| bm25 | multi_server | fixed | claude-haiku-4-5-034@multi_server | `gitmcp.fetch_generic_url_content` | 0.000 | `gitmcp.match_common_libs_owner_repo_mapping` |
| bm25 | multi_server | fixed | claude-haiku-4-5-035@multi_server | `aws-knowledge.aws___read_documentation` | 7.445 | `gitmcp.fetch_generic_url_content` |
| bm25 | multi_server | fixed | claude-haiku-4-5-036@multi_server | `deepwiki.read_wiki_structure` | 2.466 | `gitmcp.fetch_generic_url_content` |
| bm25 | multi_server | fixed | claude-haiku-4-5-038@multi_server | `svelte.get-documentation` | 2.266 | `huggingface.hf_whoami` |
| bm25 | multi_server | fixed | claude-haiku-4-5-046@multi_server | `aws-knowledge.aws___get_regional_availability` | 2.340 | `kiwi.search-flight` |
| bm25 | multi_server | fixed | claude-haiku-4-5-050@multi_server | `kiwi.feedback-to-devs` | 2.169 | `microsoft-learn.microsoft_docs_search` |
| bm25 | multi_server | fixed | claude-haiku-4-5-053@multi_server | `microsoft-learn.microsoft_docs_fetch` | 8.216 | `microsoft-learn.microsoft_docs_search` |
| bm25 | multi_server | fixed | claude-haiku-4-5-056@multi_server | `svelte.get-documentation` | 6.353 | `svelte.list-sections` |
| bm25 | multi_server | fixed | claude-haiku-4-5-069@multi_server | `aws-knowledge.aws___search_documentation` | 1.423 | *abstain* |
| bm25 | multi_server | fixed | claude-opus-5-5-031@multi_server | `gitmcp.match_common_libs_owner_repo_mapping` | 4.882 | `gitmcp.search_generic_documentation` |
| bm25 | multi_server | fixed | claude-opus-5-5-034@multi_server | `context7.resolve-library-id` | 3.268 | `gitmcp.search_generic_code` |
| bm25 | multi_server | fixed | claude-opus-5-5-046@multi_server | `svelte.svelte-autofixer` | 3.293 | `kiwi.search-flight` |
| bm25 | multi_server | fixed | claude-opus-5-5-065@multi_server | `cloudflare-docs.search_cloudflare_documentation` | 3.248 | *abstain* |
| bm25 | multi_server | fixed | claude-opus-5-5-066@multi_server | `deepwiki.ask_wiki_question` | 1.900 | *abstain* |
| bm25 | multi_server | fixed | claude-opus-5-5-067@multi_server | `kiwi.search-flight` | 4.783 | *abstain* |
| bm25 | multi_server | fixed | claude-sonnet-5-5-005@multi_server | `gitmcp.fetch_generic_url_content` | 3.198 | `aws-knowledge.aws___search_documentation` |
| bm25 | multi_server | fixed | claude-sonnet-5-5-012@multi_server | `aws-knowledge.aws___search_documentation` | 9.319 | `aws-knowledge.aws___retrieve_skill` |
| bm25 | multi_server | fixed | claude-sonnet-5-5-013@multi_server | `cloudflare-docs.migrate_pages_to_workers_guide` | 1.791 | `cloudflare-docs.search_cloudflare_documentation` |
| bm25 | multi_server | fixed | claude-sonnet-5-5-023@multi_server | `gitmcp.match_common_libs_owner_repo_mapping` | 4.791 | `deepwiki.read_wiki_contents` |
| bm25 | multi_server | fixed | claude-sonnet-5-5-024@multi_server | `deepwiki.ask_wiki_question` | 4.635 | `deepwiki.read_wiki_contents` |
| bm25 | multi_server | fixed | claude-sonnet-5-5-035@multi_server | `kiwi.search-flight` | 2.793 | `gitmcp.fetch_generic_url_content` |
| bm25 | multi_server | fixed | claude-sonnet-5-5-036@multi_server | `microsoft-learn.microsoft_docs_fetch` | 4.421 | `gitmcp.fetch_generic_url_content` |
| bm25 | multi_server | fixed | claude-sonnet-5-5-046@multi_server | `huggingface.hf_fs` | 3.801 | `kiwi.search-flight` |
| bm25 | multi_server | fixed | claude-sonnet-5-5-052@multi_server | `microsoft-learn.microsoft_docs_search` | 5.301 | `microsoft-learn.microsoft_code_sample_search` |
| bm25 | multi_server | fixed | claude-sonnet-5-5-055@multi_server | `svelte.get-documentation` | 7.007 | `svelte.list-sections` |
| bm25 | multi_server | fixed | claude-sonnet-5-5-058@multi_server | `svelte.get-documentation` | 6.373 | `svelte.list-sections` |
| bm25 | multi_server | fixed | claude-sonnet-5-5-060@multi_server | `cloudflare-docs.search_cloudflare_documentation` | 4.782 | `svelte.playground-link` |
| bm25 | multi_server | fixed | claude-sonnet-5-5-068@multi_server | `microsoft-learn.microsoft_docs_search` | 3.556 | *abstain* |
| bm25 | multi_server | fixed | claude-sonnet-5-5-070@multi_server | `huggingface.hf_whoami` | 6.644 | *abstain* |
| bm25 | multi_server | fixed | cursor-bot-001@multi_server | `astro-docs.search_astro_docs` | 4.480 | *abstain* |
| bm25 | multi_server | fixed | cursor-bot-002@multi_server | `astro-docs.search_astro_docs` | 4.623 | *abstain* |
| bm25 | multi_server | fixed | cursor-bot-004@multi_server | `astro-docs.search_astro_docs` | 4.876 | *abstain* |
| bm25 | multi_server | fixed | cursor-bot-006@multi_server | `astro-docs.search_astro_docs` | 4.698 | *abstain* |
| bm25 | multi_server | fixed | cursor-bot-011@multi_server | `context7.resolve-library-id` | 1.845 | *abstain* |
| bm25 | multi_server | fixed | cursor-bot-013@multi_server | `kiwi.feedback-to-devs` | 2.341 | *abstain* |
| bm25 | multi_server | fixed | cursor-bot-014@multi_server | `kiwi.feedback-to-devs` | 2.427 | *abstain* |
| bm25 | multi_server | fixed | cursor-bot-024@multi_server | `context7.query-docs` | 0.000 | *abstain* |
| bm25 | multi_server | fixed | cursor-bot-026@multi_server | `context7.resolve-library-id` | 6.877 | *abstain* |
| bm25 | multi_server | fixed | cursor-bot-033@multi_server | `deepwiki.ask_wiki_question` | 9.454 | *abstain* |
| bm25 | multi_server | fixed | cursor-bot-036@multi_server | `kiwi.feedback-to-devs` | 2.505 | *abstain* |
| bm25 | multi_server | fixed | cursor-bot-043@multi_server | `huggingface.hub_repo_details` | 5.252 | *abstain* |
| bm25 | multi_server | fixed | cursor-bot-047@multi_server | `gitmcp.match_common_libs_owner_repo_mapping` | 7.469 | *abstain* |
| bm25 | multi_server | fixed | cursor-bot-048@multi_server | `gitmcp.match_common_libs_owner_repo_mapping` | 4.467 | *abstain* |
| bm25 | multi_server | fixed | cursor-bot-054@multi_server | `huggingface.hub_repo_details` | 2.732 | *abstain* |
| bm25 | multi_server | fixed | cursor-bot-055@multi_server | `huggingface.hub_repo_details` | 4.905 | *abstain* |
| bm25 | multi_server | fixed | cursor-bot-056@multi_server | `huggingface.hub_repo_details` | 2.408 | *abstain* |
| bm25 | multi_server | fixed | cursor-bot-057@multi_server | `kiwi.feedback-to-devs` | 4.879 | *abstain* |
| bm25 | multi_server | fixed | cursor-bot-058@multi_server | `kiwi.search-flight` | 5.876 | *abstain* |
| bm25 | multi_server | fixed | cursor-bot-064@multi_server | `kiwi.feedback-to-devs` | 8.138 | *abstain* |
| bm25 | multi_server | fixed | cursor-bot-068@multi_server | `microsoft-learn.microsoft_code_sample_search` | 2.317 | *abstain* |
| bm25 | multi_server | fixed | cursor-bot-069@multi_server | `svelte.playground-link` | 2.195 | *abstain* |
| bm25 | multi_server | fixed | cursor-bot-074@multi_server | `svelte.svelte-autofixer` | 3.565 | *abstain* |
| bm25 | multi_server | fixed | cursor-bot-075@multi_server | `svelte.playground-link` | 6.492 | *abstain* |
| bm25 | multi_server | fixed | cursor-bot-076@multi_server | `svelte.svelte-autofixer` | 7.390 | *abstain* |
| bm25 | multi_server | fixed | cursor-bot-078@multi_server | `svelte.svelte-autofixer` | 5.253 | *abstain* |
| bm25 | multi_server | fixed | cursor-bot-079@multi_server | `svelte.svelte-autofixer` | 5.002 | *abstain* |
| bm25 | multi_server | fixed | cursor-bot-080@multi_server | `svelte.playground-link` | 5.669 | *abstain* |
| bm25 | multi_server | fixed | gpt-5.5-017@multi_server | `context7.query-docs` | 12.889 | `context7.resolve-library-id` |
| bm25 | multi_server | fixed | gpt-5.5-025@multi_server | `deepwiki.ask_wiki_question` | 5.537 | `deepwiki.read_wiki_structure` |
| bm25 | multi_server | fixed | gpt-5.5-030@multi_server | `microsoft-learn.microsoft_docs_fetch` | 3.382 | `gitmcp.fetch_generic_documentation` |
| bm25 | multi_server | fixed | gpt-5.5-063@multi_server | `aws-knowledge.aws___get_regional_availability` | 2.551 | *abstain* |
| bm25 | multi_server | fixed | gpt-5.5-065@multi_server | `huggingface.hub_repo_details` | 6.963 | *abstain* |
| bm25 | multi_server | fixed | gpt-5.6-luna-005@multi_server | `aws-knowledge.aws___read_documentation` | 5.755 | `aws-knowledge.aws___search_documentation` |
| bm25 | multi_server | fixed | gpt-5.6-luna-007@multi_server | `aws-knowledge.aws___get_regional_availability` | 10.118 | `aws-knowledge.aws___list_regions` |
| bm25 | multi_server | fixed | gpt-5.6-luna-009@multi_server | `aws-knowledge.aws___read_documentation` | 4.124 | `aws-knowledge.aws___get_regional_availability` |
| bm25 | multi_server | fixed | gpt-5.6-luna-021@multi_server | `microsoft-learn.microsoft_docs_fetch` | 1.385 | `deepwiki.ask_wiki_question` |
| bm25 | multi_server | fixed | gpt-5.6-luna-026@multi_server | `microsoft-learn.microsoft_code_sample_search` | 4.051 | `deepwiki.read_wiki_structure` |
| bm25 | multi_server | fixed | gpt-5.6-luna-034@multi_server | `context7.resolve-library-id` | 2.775 | `gitmcp.search_generic_code` |
| bm25 | multi_server | fixed | gpt-5.6-luna-063@multi_server | `aws-knowledge.aws___get_regional_availability` | 2.340 | *abstain* |
| bm25 | multi_server | fixed | gpt-5.6-sol-005@multi_server | `aws-knowledge.aws___read_documentation` | 4.664 | `aws-knowledge.aws___search_documentation` |
| bm25 | multi_server | fixed | gpt-5.6-sol-024@multi_server | `deepwiki.ask_wiki_question` | 10.407 | `deepwiki.read_wiki_contents` |
| bm25 | multi_server | fixed | gpt-5.6-sol-042@multi_server | `huggingface.hf_whoami` | 2.766 | `huggingface.hub_repo_details` |
| bm25 | multi_server | fixed | gpt-5.6-sol-049@multi_server | `microsoft-learn.microsoft_code_sample_search` | 4.258 | `microsoft-learn.microsoft_docs_search` |
| bm25 | multi_server | fixed | gpt-5.6-sol-061@multi_server | `svelte.playground-link` | 9.443 | `svelte.svelte-autofixer` |
| bm25 | multi_server | fixed | gpt-5.6-sol-067@multi_server | `svelte.list-sections` | 1.357 | *abstain* |
| bm25 | multi_server | fixed | gpt-5.6-sol-070@multi_server | `kiwi.feedback-to-devs` | 4.889 | *abstain* |
| bm25 | multi_server | fixed | gpt-5.6-terra-006@multi_server | `kiwi.search-flight` | 6.303 | `aws-knowledge.aws___search_documentation` |
| bm25 | multi_server | fixed | gpt-5.6-terra-030@multi_server | `aws-knowledge.aws___search_documentation` | 3.300 | `gitmcp.fetch_generic_documentation` |
| bm25 | multi_server | fixed | gpt-5.6-terra-031@multi_server | `astro-docs.search_astro_docs` | 1.359 | `gitmcp.search_generic_documentation` |
| bm25 | multi_server | fixed | gpt-5.6-terra-052@multi_server | `aws-knowledge.aws___get_regional_availability` | 3.181 | `microsoft-learn.microsoft_code_sample_search` |
| bm25 | multi_server | fixed | gpt-5.6-terra-064@multi_server | `deepwiki.ask_wiki_question` | 1.545 | *abstain* |
| bm25 | multi_server | fixed | gpt-5.6-terra-068@multi_server | `microsoft-learn.microsoft_docs_fetch` | 4.444 | *abstain* |
| bm25 | multi_server | fixed | gpt-6-astra-005@multi_server | `aws-knowledge.aws___retrieve_skill` | 12.874 | `aws-knowledge.aws___search_documentation` |
| bm25 | multi_server | fixed | gpt-6-astra-009@multi_server | `aws-knowledge.aws___read_documentation` | 4.739 | `aws-knowledge.aws___get_regional_availability` |
| bm25 | multi_server | fixed | gpt-6-astra-032@multi_server | `huggingface.hf_fs` | 2.212 | `gitmcp.search_generic_documentation` |
| bm25 | multi_server | fixed | gpt-6-astra-035@multi_server | `gitmcp.fetch_generic_documentation` | 5.046 | `gitmcp.fetch_generic_url_content` |
| bm25 | one_server | fixed | claude-fable-5-1-024@one_server | `deepwiki.ask_wiki_question` | 2.641 | `deepwiki.read_wiki_contents` |
| bm25 | one_server | fixed | claude-fable-5-1-026@one_server | `deepwiki.read_wiki_contents` | 1.696 | `deepwiki.read_wiki_structure` |
| bm25 | one_server | fixed | claude-fable-5-1-030@one_server | `gitmcp.fetch_generic_url_content` | 1.373 | `gitmcp.fetch_generic_documentation` |
| bm25 | one_server | fixed | claude-fable-5-1-038@one_server | `huggingface.hf_fs` | 2.505 | `huggingface.hf_whoami` |
| bm25 | one_server | fixed | claude-fable-5-1-055@one_server | `svelte.get-documentation` | 6.702 | `svelte.list-sections` |
| bm25 | one_server | fixed | claude-fable-5-1-061@one_server | `svelte.list-sections` | 3.994 | `svelte.svelte-autofixer` |
| bm25 | one_server | fixed | claude-fable-5-1-065@one_server | `huggingface.hub_repo_search` | 0.000 | *abstain* |
| bm25 | one_server | fixed | claude-fable-5-1-066@one_server | `aws-knowledge.aws___get_regional_availability` | 1.508 | *abstain* |
| bm25 | one_server | fixed | claude-haiku-4-5-002@one_server | `astro-docs.search_astro_docs` | 0.411 | *abstain* |
| bm25 | one_server | fixed | claude-haiku-4-5-010@one_server | `aws-knowledge.aws___list_regions` | 1.847 | `aws-knowledge.aws___get_regional_availability` |
| bm25 | one_server | fixed | claude-haiku-4-5-019@one_server | `context7.query-docs` | 0.677 | `context7.resolve-library-id` |
| bm25 | one_server | fixed | claude-haiku-4-5-020@one_server | `context7.query-docs` | 1.787 | `context7.resolve-library-id` |
| bm25 | one_server | fixed | claude-haiku-4-5-030@one_server | `gitmcp.fetch_generic_documentation` | 0.241 | `gitmcp.match_common_libs_owner_repo_mapping` |
| bm25 | one_server | fixed | claude-haiku-4-5-034@one_server | `gitmcp.fetch_generic_url_content` | 0.000 | `gitmcp.match_common_libs_owner_repo_mapping` |
| bm25 | one_server | fixed | claude-haiku-4-5-036@one_server | `gitmcp.fetch_generic_documentation` | 0.102 | `gitmcp.fetch_generic_url_content` |
| bm25 | one_server | fixed | claude-haiku-4-5-038@one_server | `huggingface.hub_repo_search` | 0.662 | `huggingface.hf_whoami` |
| bm25 | one_server | fixed | claude-haiku-4-5-053@one_server | `microsoft-learn.microsoft_docs_fetch` | 3.829 | `microsoft-learn.microsoft_docs_search` |
| bm25 | one_server | fixed | claude-haiku-4-5-056@one_server | `svelte.get-documentation` | 1.518 | `svelte.list-sections` |
| bm25 | one_server | fixed | claude-haiku-4-5-069@one_server | `kiwi.search-flight` | 0.551 | *abstain* |
