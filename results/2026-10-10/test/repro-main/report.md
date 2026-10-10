# ToolDiscoveryBench — repro-main

## Accuracy

| router | suite | tools | n | no-tool | err | **acc** | top-1 | lenient | top-3 | server@1 | abstain ✓ | false abstain | refused |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| bm25 | claude_v2 | 10 | 165 | 33 | 0 | **36.4%** | 45.5% | 45.5% | 84.1% | 79.5% | 0.0% | 0.0% | 0.0% |
| bm25 | claude_v2 | 30 | 165 | 33 | 0 | **29.1%** | 36.4% | 36.4% | 81.8% | 70.5% | 0.0% | 0.0% | 0.0% |
| bm25 | claude_v2 | 75 | 165 | 33 | 0 | **27.3%** | 34.1% | 34.1% | 61.4% | 59.1% | 0.0% | 0.0% | 0.0% |
| bm25 | claude_v2 | 150 | 165 | 33 | 0 | **25.5%** | 31.8% | 31.8% | 56.8% | 52.3% | 0.0% | 0.0% | 0.0% |
| bm25 | multi_confused | fixed | 393 | 87 | 0 | **42.0%** | 53.9% | 67.6% | 79.4% | 74.5% | 0.0% | 0.0% | 0.0% |
| bm25 | multi_server | fixed | 618 | 132 | 0 | **49.0%** | 62.3% | 69.8% | 87.7% | 82.1% | 0.0% | 0.0% | 0.0% |
| bm25 | one_server | fixed | 618 | 132 | 0 | **56.3%** | 71.6% | 82.7% | 94.4% | 100.0% | 0.0% | 0.0% | 0.0% |
| bm25-abstain | claude_v2 | 10 | 165 | 33 | 0 | **47.3%** | 43.2% | 43.2% | 79.5% | 77.3% | 63.6% | 9.1% | 0.0% |
| bm25-abstain | claude_v2 | 30 | 165 | 33 | 0 | **29.1%** | 36.4% | 36.4% | 79.5% | 70.5% | 0.0% | 4.5% | 0.0% |
| bm25-abstain | claude_v2 | 75 | 165 | 33 | 0 | **27.3%** | 34.1% | 34.1% | 61.4% | 59.1% | 0.0% | 2.3% | 0.0% |
| bm25-abstain | claude_v2 | 150 | 165 | 33 | 0 | **25.5%** | 31.8% | 31.8% | 56.8% | 52.3% | 0.0% | 2.3% | 0.0% |
| bm25-abstain | multi_confused | fixed | 393 | 87 | 0 | **42.7%** | 53.9% | 67.6% | 79.4% | 74.5% | 3.4% | 0.0% | 0.0% |
| bm25-abstain | multi_server | fixed | 618 | 132 | 0 | **50.0%** | 62.3% | 69.8% | 87.7% | 81.5% | 4.5% | 0.6% | 0.0% |
| bm25-abstain | one_server | fixed | 618 | 132 | 0 | **56.3%** | 59.9% | 68.5% | 79.0% | 80.9% | 43.2% | 19.1% | 0.0% |
| or-jev-factored | claude_v2 | 10 | 165 | 0 | 165 | **–** | – | – | – | – | – | – | – |
| or-jev-factored | claude_v2 | 30 | 165 | 0 | 165 | **–** | – | – | – | – | – | – | – |
| or-jev-factored | claude_v2 | 75 | 165 | 0 | 165 | **–** | – | – | – | – | – | – | – |
| or-jev-factored | claude_v2 | 150 | 165 | 0 | 165 | **–** | – | – | – | – | – | – | – |
| or-jev-factored | multi_confused | fixed | 393 | 46 | 41 | **83.0%** | 87.3% | 92.5% | 95.1% | 94.4% | 54.3% | 2.9% | 0.0% |
| or-jev-factored | multi_server | fixed | 618 | 132 | 0 | **83.2%** | 89.3% | 94.4% | 97.5% | 96.3% | 60.6% | 0.6% | 0.0% |
| or-jev-factored | one_server | fixed | 618 | 132 | 0 | **87.1%** | 90.7% | 96.3% | 98.8% | 98.8% | 73.5% | 1.2% | 0.0% |
| or-jev-flat | claude_v2 | 10 | 165 | 33 | 0 | **95.2%** | 95.5% | 95.5% | 100.0% | 100.0% | 93.9% | 0.0% | 0.0% |
| or-jev-flat | claude_v2 | 30 | 165 | 33 | 0 | **87.9%** | 93.9% | 93.9% | 100.0% | 97.0% | 63.6% | 0.0% | 0.0% |
| or-jev-flat | claude_v2 | 75 | 165 | 33 | 0 | **78.2%** | 86.4% | 86.4% | 98.5% | 93.2% | 45.5% | 0.0% | 0.0% |
| or-jev-flat | claude_v2 | 150 | 165 | 33 | 0 | **75.2%** | 82.6% | 82.6% | 98.5% | 91.7% | 45.5% | 0.0% | 0.0% |
| or-jev-flat | multi_confused | fixed | 393 | 87 | 0 | **84.5%** | 85.6% | 95.1% | 98.0% | 98.0% | 80.5% | 0.0% | 0.0% |
| or-jev-flat | multi_server | fixed | 618 | 132 | 0 | **88.5%** | 90.5% | 95.7% | 97.7% | 98.1% | 81.1% | 0.6% | 0.0% |
| or-jev-flat | one_server | fixed | 618 | 132 | 0 | **91.3%** | 91.6% | 96.9% | 99.4% | 99.4% | 90.2% | 0.6% | 0.0% |
| or-luna-factored | claude_v2 | 10 | 165 | 0 | 165 | **–** | – | – | – | – | – | – | – |
| or-luna-factored | claude_v2 | 30 | 165 | 0 | 165 | **–** | – | – | – | – | – | – | – |
| or-luna-factored | claude_v2 | 75 | 165 | 0 | 165 | **–** | – | – | – | – | – | – | – |
| or-luna-factored | claude_v2 | 150 | 165 | 0 | 165 | **–** | – | – | – | – | – | – | – |
| or-luna-factored | multi_confused | fixed | 393 | 0 | 393 | **–** | – | – | – | – | – | – | – |
| or-luna-factored | multi_server | fixed | 618 | 0 | 618 | **–** | – | – | – | – | – | – | – |
| or-luna-factored | one_server | fixed | 618 | 0 | 618 | **–** | – | – | – | – | – | – | – |
| or-luna-flat | claude_v2 | 10 | 165 | 0 | 165 | **–** | – | – | – | – | – | – | – |
| or-luna-flat | claude_v2 | 30 | 165 | 0 | 165 | **–** | – | – | – | – | – | – | – |
| or-luna-flat | claude_v2 | 75 | 165 | 0 | 165 | **–** | – | – | – | – | – | – | – |
| or-luna-flat | claude_v2 | 150 | 165 | 0 | 165 | **–** | – | – | – | – | – | – | – |
| or-luna-flat | multi_confused | fixed | 393 | 0 | 393 | **–** | – | – | – | – | – | – | – |
| or-luna-flat | multi_server | fixed | 618 | 0 | 618 | **–** | – | – | – | – | – | – | – |
| or-luna-flat | one_server | fixed | 618 | 0 | 618 | **–** | – | – | – | – | – | – | – |

*acc: answerable questions need the gold tool first, no-tool questions need an abstain. top-1 / lenient / top-3 / server@1 are over answerable questions only; lenient also accepts tools labelled acceptable. abstain ✓: share of no-tool questions where the router abstained. false abstain: share of answerable ones where it did. refused: share of questions where the backend refused a per-server sub-question (scored as P = 0 for that server, which can flatter accuracy).*

## Speed, cost and calibration

| router | suite | tools | p50 ms | p95 ms | calls | in-tok | $/1k q | ECE | Brier | conf ✓ | conf ✗ |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| bm25 | claude_v2 | 10 | 0 | 0 | 0.000 | – | – | – | – | – | – |
| bm25 | claude_v2 | 30 | 1 | 1 | 0.000 | – | – | – | – | – | – |
| bm25 | claude_v2 | 75 | 1 | 1 | 0.000 | – | – | – | – | – | – |
| bm25 | claude_v2 | 150 | 2 | 2 | 0.000 | – | – | – | – | – | – |
| bm25 | multi_confused | fixed | 1 | 1 | 0.000 | – | – | – | – | – | – |
| bm25 | multi_server | fixed | 1 | 1 | 0.000 | – | – | – | – | – | – |
| bm25 | one_server | fixed | 0 | 0 | 0.000 | – | – | – | – | – | – |
| bm25-abstain | claude_v2 | 10 | 0 | 0 | 0.000 | – | – | – | – | – | – |
| bm25-abstain | claude_v2 | 30 | 1 | 1 | 0.000 | – | – | – | – | – | – |
| bm25-abstain | claude_v2 | 75 | 1 | 1 | 0.000 | – | – | – | – | – | – |
| bm25-abstain | claude_v2 | 150 | 2 | 2 | 0.000 | – | – | – | – | – | – |
| bm25-abstain | multi_confused | fixed | 1 | 1 | 0.000 | – | – | – | – | – | – |
| bm25-abstain | multi_server | fixed | 1 | 1 | 0.000 | – | – | – | – | – | – |
| bm25-abstain | one_server | fixed | 0 | 0 | 0.000 | – | – | – | – | – | – |
| or-jev-factored | claude_v2 | 10 | – | – | – | – | – | – | – | – | – |
| or-jev-factored | claude_v2 | 30 | – | – | – | – | – | – | – | – | – |
| or-jev-factored | claude_v2 | 75 | – | – | – | – | – | – | – | – | – |
| or-jev-factored | claude_v2 | 150 | – | – | – | – | – | – | – | – | – |
| or-jev-factored | multi_confused | fixed | 161 | 233 | 1.000 | 1,830 | 0.077 | 0.051 | 0.100 | 0.895 | 0.621 |
| or-jev-factored | multi_server | fixed | 161 | 230 | 1.000 | 1,674 | 0.070 | 0.067 | 0.090 | 0.922 | 0.580 |
| or-jev-factored | one_server | fixed | 171 | 262 | 1.000 | 715 | 0.030 | 0.054 | 0.075 | 0.930 | 0.611 |
| or-jev-flat | claude_v2 | 10 | 201 | 262 | 1.000 | 850 | 0.036 | 0.052 | 0.035 | 0.949 | 0.642 |
| or-jev-flat | claude_v2 | 30 | 206 | 293 | 1.000 | 1,640 | 0.069 | 0.085 | 0.062 | 0.916 | 0.540 |
| or-jev-flat | claude_v2 | 75 | 215 | 327 | 1.000 | 3,407 | 0.143 | 0.103 | 0.118 | 0.904 | 0.576 |
| or-jev-flat | claude_v2 | 150 | 223 | 274 | 1.000 | 6,047 | 0.254 | 0.096 | 0.108 | 0.908 | 0.535 |
| or-jev-flat | multi_confused | fixed | 202 | 271 | 1.000 | 1,360 | 0.057 | 0.044 | 0.100 | 0.910 | 0.596 |
| or-jev-flat | multi_server | fixed | 206 | 274 | 1.000 | 1,246 | 0.052 | 0.046 | 0.075 | 0.934 | 0.639 |
| or-jev-flat | one_server | fixed | 206 | 283 | 1.000 | 619 | 0.026 | 0.031 | 0.071 | 0.946 | 0.724 |
| or-luna-factored | claude_v2 | 10 | – | – | – | – | – | – | – | – | – |
| or-luna-factored | claude_v2 | 30 | – | – | – | – | – | – | – | – | – |
| or-luna-factored | claude_v2 | 75 | – | – | – | – | – | – | – | – | – |
| or-luna-factored | claude_v2 | 150 | – | – | – | – | – | – | – | – | – |
| or-luna-factored | multi_confused | fixed | – | – | – | – | – | – | – | – | – |
| or-luna-factored | multi_server | fixed | – | – | – | – | – | – | – | – | – |
| or-luna-factored | one_server | fixed | – | – | – | – | – | – | – | – | – |
| or-luna-flat | claude_v2 | 10 | – | – | – | – | – | – | – | – | – |
| or-luna-flat | claude_v2 | 30 | – | – | – | – | – | – | – | – | – |
| or-luna-flat | claude_v2 | 75 | – | – | – | – | – | – | – | – | – |
| or-luna-flat | claude_v2 | 150 | – | – | – | – | – | – | – | – | – |
| or-luna-flat | multi_confused | fixed | – | – | – | – | – | – | – | – | – |
| or-luna-flat | multi_server | fixed | – | – | – | – | – | – | – | – | – |
| or-luna-flat | one_server | fixed | – | – | – | – | – | – | – | – | – |

*Calibration columns are filled only for calibrated routers (Jev). conf ✓ / ✗ is the mean top-1 probability when right vs wrong; a big gap lets you set an abstain threshold.*

## Top-1 with 95% bootstrap confidence intervals

| router | suite | tools | n | top-1 | 95% CI | test n | test top-1 | test 95% CI |
|---|---|---:|---:|---:|---|---:|---:|---|
| bm25 | claude_v2 | 10 | 44 | 45.5% | 31.8%–59.1% | 44 | 45.5% | 31.8%–59.1% |
| bm25 | claude_v2 | 30 | 44 | 36.4% | 22.7%–50.0% | 44 | 36.4% | 22.7%–50.0% |
| bm25 | claude_v2 | 75 | 44 | 34.1% | 20.5%–47.7% | 44 | 34.1% | 20.5%–47.7% |
| bm25 | claude_v2 | 150 | 44 | 31.8% | 18.2%–45.5% | 44 | 31.8% | 18.2%–45.5% |
| bm25 | multi_confused | fixed | 102 | 53.9% | 43.1%–63.7% | 102 | 53.9% | 43.1%–63.7% |
| bm25 | multi_server | fixed | 162 | 62.3% | 54.3%–69.8% | 162 | 62.3% | 54.3%–69.8% |
| bm25 | one_server | fixed | 162 | 71.6% | 63.6%–77.8% | 162 | 71.6% | 63.6%–77.8% |
| bm25-abstain | claude_v2 | 10 | 44 | 43.2% | 29.5%–56.8% | 44 | 43.2% | 29.5%–56.8% |
| bm25-abstain | claude_v2 | 30 | 44 | 36.4% | 22.7%–50.0% | 44 | 36.4% | 22.7%–50.0% |
| bm25-abstain | claude_v2 | 75 | 44 | 34.1% | 20.5%–47.7% | 44 | 34.1% | 20.5%–47.7% |
| bm25-abstain | claude_v2 | 150 | 44 | 31.8% | 18.2%–45.5% | 44 | 31.8% | 18.2%–45.5% |
| bm25-abstain | multi_confused | fixed | 102 | 53.9% | 43.1%–63.7% | 102 | 53.9% | 43.1%–63.7% |
| bm25-abstain | multi_server | fixed | 162 | 62.3% | 54.3%–69.8% | 162 | 62.3% | 54.3%–69.8% |
| bm25-abstain | one_server | fixed | 162 | 59.9% | 51.9%–67.3% | 162 | 59.9% | 51.9%–67.3% |
| or-jev-factored | claude_v2 | 10 | 0 | – | – | 0 | – | – |
| or-jev-factored | claude_v2 | 30 | 0 | – | – | 0 | – | – |
| or-jev-factored | claude_v2 | 75 | 0 | – | – | 0 | – | – |
| or-jev-factored | claude_v2 | 150 | 0 | – | – | 0 | – | – |
| or-jev-factored | multi_confused | fixed | 102 | 87.3% | 80.1%–93.1% | 102 | 87.3% | 80.1%–93.1% |
| or-jev-factored | multi_server | fixed | 162 | 89.3% | 84.2%–93.6% | 162 | 89.3% | 84.2%–93.6% |
| or-jev-factored | one_server | fixed | 162 | 90.7% | 86.0%–94.9% | 162 | 90.7% | 86.0%–94.9% |
| or-jev-flat | claude_v2 | 10 | 44 | 95.5% | 88.6%–100.0% | 44 | 95.5% | 88.6%–100.0% |
| or-jev-flat | claude_v2 | 30 | 44 | 93.9% | 86.4%–99.2% | 44 | 93.9% | 86.4%–99.2% |
| or-jev-flat | claude_v2 | 75 | 44 | 86.4% | 75.8%–95.5% | 44 | 86.4% | 75.8%–95.5% |
| or-jev-flat | claude_v2 | 150 | 44 | 82.6% | 70.5%–93.2% | 44 | 82.6% | 70.5%–93.2% |
| or-jev-flat | multi_confused | fixed | 102 | 85.6% | 79.1%–91.8% | 102 | 85.6% | 79.1%–91.8% |
| or-jev-flat | multi_server | fixed | 162 | 90.5% | 85.6%–94.4% | 162 | 90.5% | 85.6%–94.4% |
| or-jev-flat | one_server | fixed | 162 | 91.6% | 87.0%–95.3% | 162 | 91.6% | 87.0%–95.3% |
| or-luna-factored | claude_v2 | 10 | 0 | – | – | 0 | – | – |
| or-luna-factored | claude_v2 | 30 | 0 | – | – | 0 | – | – |
| or-luna-factored | claude_v2 | 75 | 0 | – | – | 0 | – | – |
| or-luna-factored | claude_v2 | 150 | 0 | – | – | 0 | – | – |
| or-luna-factored | multi_confused | fixed | 0 | – | – | 0 | – | – |
| or-luna-factored | multi_server | fixed | 0 | – | – | 0 | – | – |
| or-luna-factored | one_server | fixed | 0 | – | – | 0 | – | – |
| or-luna-flat | claude_v2 | 10 | 0 | – | – | 0 | – | – |
| or-luna-flat | claude_v2 | 30 | 0 | – | – | 0 | – | – |
| or-luna-flat | claude_v2 | 75 | 0 | – | – | 0 | – | – |
| or-luna-flat | claude_v2 | 150 | 0 | – | – | 0 | – | – |
| or-luna-flat | multi_confused | fixed | 0 | – | – | 0 | – | – |
| or-luna-flat | multi_server | fixed | 0 | – | – | 0 | – | – |
| or-luna-flat | one_server | fixed | 0 | – | – | 0 | – | – |

*Answerable questions only; 1000 seeded resamples over questions (repeats averaged per question). *test* is the frozen held-out split (`data/golden/splits/test_qids.txt`); publish numbers from it with repeats ≥ 3.*

## Accuracy by question tag (all suites and sizes pooled)

| router | cloud-docs | code | confusable | generator:claude | generator:cursor-bot | generator:openai | hard_negative | id_given | implicit_vendor | intra_server | judges_split | lib-docs | ml-hub | multi_server | multi_server_confused | multi_valid | needs_human_review | no_tool | one_server | paraphrase | relabelled | repo-qa | rewritten | split:test | travel | url_given |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| bm25 | 36.8% | 33.3% | 54.9% | 46.9% | 0.0% | 69.9% | 50.0% | 0.0% | 35.0% | 82.1% | 16.7% | 25.0% | 30.0% | 49.0% | 42.0% | 0.0% | 0.0% | 0.0% | 56.3% | 12.5% | 7.4% | 50.0% | 66.7% | 44.2% | 58.3% | 66.7% |
| bm25-abstain | 36.8% | 33.3% | 51.9% | 45.5% | 16.4% | 66.7% | 50.0% | 0.0% | 35.0% | 82.1% | 19.4% | 25.0% | 30.0% | 50.0% | 42.7% | 0.0% | 16.4% | 18.0% | 56.3% | 12.5% | 7.4% | 50.0% | 66.7% | 45.3% | 50.0% | 66.7% |
| or-jev-flat | 94.1% | 100.0% | 85.4% | 84.0% | 79.2% | 92.7% | 90.9% | 16.7% | 100.0% | 100.0% | 56.5% | 83.3% | 100.0% | 88.5% | 84.5% | 81.2% | 79.2% | 78.3% | 91.3% | 100.0% | 53.1% | 80.6% | 100.0% | 87.3% | 100.0% | 83.3% |
| or-jev-factored | – | – | 83.5% | 82.2% | 61.6% | 93.4% | – | – | – | – | 55.6% | – | – | 83.2% | 83.0% | – | 61.6% | 65.2% | 87.1% | – | 51.9% | – | 100.0% | 84.6% | – | – |

## Accuracy by question author (model family that wrote the question)

| router | claude | cursor | gpt |
|---|---:|---:|---:|
| bm25 | 46.9% | 0.0% | 69.9% |
| bm25-abstain | 45.5% | 16.4% | 66.7% |
| or-jev-factored | 82.2% | 61.6% | 93.4% |
| or-jev-flat | 84.0% | 79.2% | 92.7% |

## Accuracy by question author (exact model)

| router | claude-fable-5-1 | claude-haiku-4-5 | claude-opus-5-5 | claude-sonnet-5-5 | cursor-bot | gpt-5.5 | gpt-5.6-luna | gpt-5.6-sol | gpt-5.6-terra | gpt-6-astra |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| bm25 | 60.3% | 33.3% | 74.4% | 17.1% | 0.0% | 75.0% | 72.6% | 56.1% | 78.5% | 56.7% |
| bm25-abstain | 57.5% | 33.3% | 76.9% | 12.2% | 16.4% | 72.9% | 69.4% | 53.7% | 73.8% | 53.3% |
| or-jev-factored | 82.2% | 83.3% | 85.5% | 77.2% | 61.6% | 95.8% | 91.9% | 91.9% | 95.4% | 90.0% |
| or-jev-flat | 82.2% | 83.9% | 96.6% | 75.6% | 79.2% | 95.8% | 95.7% | 87.0% | 90.8% | 93.3% |

## Accuracy without possibly contaminated questions

| router | suite | tools | n | acc | top-1 | n kept | acc kept | top-1 kept |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| bm25 | claude_v2 | 10 | 165 | 36.4% | 45.5% | 165 | 36.4% | 45.5% |
| bm25 | claude_v2 | 30 | 165 | 29.1% | 36.4% | 165 | 29.1% | 36.4% |
| bm25 | claude_v2 | 75 | 165 | 27.3% | 34.1% | 165 | 27.3% | 34.1% |
| bm25 | claude_v2 | 150 | 165 | 25.5% | 31.8% | 165 | 25.5% | 31.8% |
| bm25 | multi_confused | fixed | 393 | 42.0% | 53.9% | 303 | 32.7% | 45.8% |
| bm25 | multi_server | fixed | 618 | 49.0% | 62.3% | 450 | 43.3% | 58.0% |
| bm25 | one_server | fixed | 618 | 56.3% | 71.6% | 450 | 51.3% | 68.8% |
| bm25-abstain | claude_v2 | 10 | 165 | 47.3% | 43.2% | 165 | 47.3% | 43.2% |
| bm25-abstain | claude_v2 | 30 | 165 | 29.1% | 36.4% | 165 | 29.1% | 36.4% |
| bm25-abstain | claude_v2 | 75 | 165 | 27.3% | 34.1% | 165 | 27.3% | 34.1% |
| bm25-abstain | claude_v2 | 150 | 165 | 25.5% | 31.8% | 165 | 25.5% | 31.8% |
| bm25-abstain | multi_confused | fixed | 393 | 42.7% | 53.9% | 303 | 33.7% | 45.8% |
| bm25-abstain | multi_server | fixed | 618 | 50.0% | 62.3% | 450 | 44.7% | 58.0% |
| bm25-abstain | one_server | fixed | 618 | 56.3% | 59.9% | 450 | 52.7% | 56.2% |
| or-jev-factored | claude_v2 | 10 | 165 | – | – | 165 | – | – |
| or-jev-factored | claude_v2 | 30 | 165 | – | – | 165 | – | – |
| or-jev-factored | claude_v2 | 75 | 165 | – | – | 165 | – | – |
| or-jev-factored | claude_v2 | 150 | 165 | – | – | 165 | – | – |
| or-jev-factored | multi_confused | fixed | 393 | 83.0% | 87.3% | 303 | 79.4% | 84.7% |
| or-jev-factored | multi_server | fixed | 618 | 83.2% | 89.3% | 450 | 81.1% | 89.3% |
| or-jev-factored | one_server | fixed | 618 | 87.1% | 90.7% | 450 | 86.0% | 90.8% |
| or-jev-flat | claude_v2 | 10 | 165 | 95.2% | 95.5% | 165 | 95.2% | 95.5% |
| or-jev-flat | claude_v2 | 30 | 165 | 87.9% | 93.9% | 165 | 87.9% | 93.9% |
| or-jev-flat | claude_v2 | 75 | 165 | 78.2% | 86.4% | 165 | 78.2% | 86.4% |
| or-jev-flat | claude_v2 | 150 | 165 | 75.2% | 82.6% | 165 | 75.2% | 82.6% |
| or-jev-flat | multi_confused | fixed | 393 | 84.5% | 85.6% | 303 | 82.2% | 82.9% |
| or-jev-flat | multi_server | fixed | 618 | 88.5% | 90.5% | 450 | 86.9% | 89.0% |
| or-jev-flat | one_server | fixed | 618 | 91.3% | 91.6% | 450 | 90.0% | 90.2% |
| or-luna-factored | claude_v2 | 10 | 165 | – | – | 165 | – | – |
| or-luna-factored | claude_v2 | 30 | 165 | – | – | 165 | – | – |
| or-luna-factored | claude_v2 | 75 | 165 | – | – | 165 | – | – |
| or-luna-factored | claude_v2 | 150 | 165 | – | – | 165 | – | – |
| or-luna-factored | multi_confused | fixed | 393 | – | – | 303 | – | – |
| or-luna-factored | multi_server | fixed | 618 | – | – | 450 | – | – |
| or-luna-factored | one_server | fixed | 618 | – | – | 450 | – | – |
| or-luna-flat | claude_v2 | 10 | 165 | – | – | 165 | – | – |
| or-luna-flat | claude_v2 | 30 | 165 | – | – | 165 | – | – |
| or-luna-flat | claude_v2 | 75 | 165 | – | – | 165 | – | – |
| or-luna-flat | claude_v2 | 150 | 165 | – | – | 165 | – | – |
| or-luna-flat | multi_confused | fixed | 393 | – | – | 303 | – | – |
| or-luna-flat | multi_server | fixed | 618 | – | – | 450 | – | – |
| or-luna-flat | one_server | fixed | 618 | – | – | 450 | – | – |

*kept: questions not written by `gpt-5.6-sol`, `claude-opus-5-5`, `gpt-5.6-luna` (judges of the labels, or the same model line as a router under test).*

## Misses (repeat 0, first 200)

| router | suite | tools | item | picked | p | gold |
|---|---|---:|---|---|---:|---|
| bm25 | claude_v2 | 10 | c7-03 | `context7.query-docs` | 4.664 | `context7.resolve-library-id` |
| bm25 | claude_v2 | 10 | c7-04 | `context7.query-docs` | 3.019 | `context7.resolve-library-id` |
| bm25 | claude_v2 | 10 | cf-01 | `cloudflare-docs.migrate_pages_to_workers_guide` | 3.640 | `cloudflare-docs.search_cloudflare_documentation` |
| bm25 | claude_v2 | 10 | cf-03 | `syn-storage.search_files` | 3.867 | `cloudflare-docs.search_cloudflare_documentation` |
| bm25 | claude_v2 | 10 | cursor-bot-002 | `huggingface.hf_fs` | 0.935 | *abstain* |
| bm25 | claude_v2 | 10 | cursor-bot-004 | `svelte.list-sections` | 0.710 | *abstain* |
| bm25 | claude_v2 | 10 | cursor-bot-013 | `microsoft-learn.microsoft_docs_search` | 0.811 | *abstain* |
| bm25 | claude_v2 | 10 | cursor-bot-026 | `syn-ml-registry.promote_model` | 5.936 | *abstain* |
| bm25 | claude_v2 | 10 | cursor-bot-033 | `huggingface.hub_repo_search` | 3.228 | *abstain* |
| bm25 | claude_v2 | 10 | cursor-bot-036 | `syn-wiki.search_pages` | 0.000 | *abstain* |
| bm25 | claude_v2 | 10 | cursor-bot-054 | `deepwiki.read_wiki_structure` | 0.000 | *abstain* |
| bm25 | claude_v2 | 10 | cursor-bot-055 | `syn-ml-registry.promote_model` | 3.531 | *abstain* |
| bm25 | claude_v2 | 10 | cursor-bot-075 | `context7.query-docs` | 1.785 | *abstain* |
| bm25 | claude_v2 | 10 | cursor-bot-076 | `huggingface.hub_repo_search` | 0.000 | *abstain* |
| bm25 | claude_v2 | 10 | cursor-bot-078 | `syn-mail.search_mail` | 0.000 | *abstain* |
| bm25 | claude_v2 | 10 | d-aws-avail-04 | `aws-knowledge.aws___read_documentation` | 3.277 | `aws-knowledge.aws___get_regional_availability` |
| bm25 | claude_v2 | 10 | d-aws-search-02 | `syn-chat.post_message` | 4.159 | `aws-knowledge.aws___search_documentation` |
| bm25 | claude_v2 | 10 | d-aws-skill-01 | `aws-knowledge.aws___retrieve_skill` | 10.298 | `aws-knowledge.aws___search_documentation` |
| bm25 | claude_v2 | 10 | d-aws-skill-02 | `aws-knowledge.aws___retrieve_skill` | 4.602 | `aws-knowledge.aws___search_documentation` |
| bm25 | claude_v2 | 10 | d-c7-either-03 | `context7.query-docs` | 3.988 | `context7.resolve-library-id` |
| bm25 | claude_v2 | 10 | d-c7-query-03 | `context7.resolve-library-id` | 1.241 | `context7.query-docs` |
| bm25 | claude_v2 | 10 | d-dw-ask-03 | `svelte.list-sections` | 0.747 | `deepwiki.ask_wiki_question` |
| bm25 | claude_v2 | 10 | d-dw-read-02 | `deepwiki.read_wiki_structure` | 3.583 | `deepwiki.read_wiki_contents` |
| bm25 | claude_v2 | 10 | d-gm-searchdoc-03 | `aws-knowledge.aws___get_regional_availability` | 1.305 | `gitmcp.search_generic_documentation` |
| bm25 | claude_v2 | 10 | d-gm-url-01 | `gitmcp.fetch_generic_documentation` | 2.667 | `gitmcp.fetch_generic_url_content` |
| bm25 | claude_v2 | 10 | d-hf-details-01 | `aws-knowledge.aws___get_regional_availability` | 3.004 | `huggingface.hub_repo_details` |
| bm25 | claude_v2 | 10 | d-hf-fs-02 | `huggingface.hub_repo_details` | 4.615 | `huggingface.hf_fs` |
| bm25 | claude_v2 | 10 | d-ms-code-02 | `aws-knowledge.aws___get_regional_availability` | 5.786 | `microsoft-learn.microsoft_code_sample_search` |
| bm25 | claude_v2 | 10 | d-sv-doc-02 | `svelte.svelte-autofixer` | 3.669 | `svelte.list-sections`, `svelte.get-documentation` |
| bm25 | claude_v2 | 10 | d-sv-doc-03 | `syn-incident.get_oncall` | 0.000 | `svelte.list-sections`, `svelte.get-documentation` |
| bm25 | claude_v2 | 10 | d-sv-fix-03 | `svelte.playground-link` | 2.374 | `svelte.svelte-autofixer` |
| bm25 | claude_v2 | 10 | d-x-06 | `aws-knowledge.aws___get_regional_availability` | 1.471 | `microsoft-learn.microsoft_docs_search` |
| bm25 | claude_v2 | 10 | gm-03 | `gitmcp.match_common_libs_owner_repo_mapping` | 3.493 | `gitmcp.fetch_generic_documentation` |
| bm25 | claude_v2 | 10 | ms-04 | `microsoft-learn.microsoft_code_sample_search` | 1.587 | `microsoft-learn.microsoft_docs_search` |
| bm25 | claude_v2 | 10 | x-05 | `syn-wiki.search_pages` | 0.000 | `huggingface.hub_repo_search` |
| bm25 | claude_v2 | 150 | aws-05 | `aws-knowledge.aws___list_regions` | 14.306 | `aws-knowledge.aws___get_regional_availability` |
| bm25 | claude_v2 | 150 | c7-03 | `context7.query-docs` | 9.030 | `context7.resolve-library-id` |
| bm25 | claude_v2 | 150 | c7-04 | `syn-weather.current_weather` | 6.908 | `context7.resolve-library-id` |
| bm25 | claude_v2 | 150 | cf-01 | `cloudflare-docs.migrate_pages_to_workers_guide` | 10.488 | `cloudflare-docs.search_cloudflare_documentation` |
| bm25 | claude_v2 | 150 | cf-03 | `syn-calendar.find_free_slots` | 8.843 | `cloudflare-docs.search_cloudflare_documentation` |
| bm25 | claude_v2 | 150 | cursor-bot-002 | `astro-docs.search_astro_docs` | 9.467 | *abstain* |
| bm25 | claude_v2 | 150 | cursor-bot-004 | `astro-docs.search_astro_docs` | 9.467 | *abstain* |
| bm25 | claude_v2 | 150 | cursor-bot-013 | `syn-crm.list_contacts` | 4.736 | *abstain* |
| bm25 | claude_v2 | 150 | cursor-bot-026 | `syn-ml-registry.get_model_version` | 11.739 | *abstain* |
| bm25 | claude_v2 | 150 | cursor-bot-033 | `deepwiki.ask_wiki_question` | 18.932 | *abstain* |
| bm25 | claude_v2 | 150 | cursor-bot-036 | `deepwiki.read_wiki_contents` | 8.439 | *abstain* |
| bm25 | claude_v2 | 150 | cursor-bot-054 | `syn-wiki.create_page` | 5.124 | *abstain* |
| bm25 | claude_v2 | 150 | cursor-bot-055 | `syn-ml-registry.get_model_version` | 6.589 | *abstain* |
| bm25 | claude_v2 | 150 | cursor-bot-075 | `svelte.playground-link` | 10.320 | *abstain* |
| bm25 | claude_v2 | 150 | cursor-bot-076 | `svelte.svelte-autofixer` | 14.289 | *abstain* |
| bm25 | claude_v2 | 150 | cursor-bot-078 | `svelte.svelte-autofixer` | 10.670 | *abstain* |
| bm25 | claude_v2 | 150 | d-aws-avail-04 | `syn-cloudops.deploy_stack` | 8.758 | `aws-knowledge.aws___get_regional_availability` |
| bm25 | claude_v2 | 150 | d-aws-search-02 | `syn-mail.get_message` | 6.908 | `aws-knowledge.aws___search_documentation` |
| bm25 | claude_v2 | 150 | d-aws-skill-01 | `aws-knowledge.aws___retrieve_skill` | 24.841 | `aws-knowledge.aws___search_documentation` |
| bm25 | claude_v2 | 150 | d-aws-skill-02 | `aws-knowledge.aws___retrieve_skill` | 13.774 | `aws-knowledge.aws___search_documentation` |
| bm25 | claude_v2 | 150 | d-c7-either-03 | `context7.query-docs` | 7.097 | `context7.resolve-library-id` |
| bm25 | claude_v2 | 150 | d-c7-query-03 | `syn-cloudops.list_instances` | 9.763 | `context7.query-docs` |
| bm25 | claude_v2 | 150 | d-dw-ask-03 | `syn-cloudops.list_instances` | 8.758 | `deepwiki.ask_wiki_question` |
| bm25 | claude_v2 | 150 | d-dw-read-02 | `deepwiki.ask_wiki_question` | 9.803 | `deepwiki.read_wiki_contents` |
| bm25 | claude_v2 | 150 | d-gm-searchdoc-03 | `microsoft-learn.microsoft_docs_search` | 9.818 | `gitmcp.search_generic_documentation` |
| bm25 | claude_v2 | 150 | d-gm-url-01 | `syn-web.fetch_url` | 4.792 | `gitmcp.fetch_generic_url_content` |
| bm25 | claude_v2 | 150 | d-hf-details-01 | `context7.resolve-library-id` | 3.477 | `huggingface.hub_repo_details` |
| bm25 | claude_v2 | 150 | d-hf-fs-02 | `syn-storage.read_file` | 9.819 | `huggingface.hf_fs` |
| bm25 | claude_v2 | 150 | d-hf-search-01 | `syn-ml-registry.search_models` | 6.083 | `huggingface.hub_repo_search` |
| bm25 | claude_v2 | 150 | d-kw-03 | `syn-travel.get_itinerary` | 5.543 | `kiwi.search-flight` |
| bm25 | claude_v2 | 150 | d-ms-code-02 | `aws-knowledge.aws___list_regions` | 6.146 | `microsoft-learn.microsoft_code_sample_search` |
| bm25 | claude_v2 | 150 | d-sv-doc-02 | `svelte.svelte-autofixer` | 11.877 | `svelte.list-sections`, `svelte.get-documentation` |
| bm25 | claude_v2 | 150 | d-sv-doc-03 | `huggingface.hf_fs` | 0.724 | `svelte.list-sections`, `svelte.get-documentation` |
| bm25 | claude_v2 | 150 | d-x-06 | `syn-warehouse.explain_query` | 7.855 | `microsoft-learn.microsoft_docs_search` |
| bm25 | claude_v2 | 150 | dw-01 | `gitmcp.match_common_libs_owner_repo_mapping` | 5.447 | `deepwiki.ask_wiki_question` |
| bm25 | claude_v2 | 150 | gm-03 | `gitmcp.match_common_libs_owner_repo_mapping` | 6.845 | `gitmcp.fetch_generic_documentation` |
| bm25 | claude_v2 | 150 | ms-02 | `syn-calendar.list_events` | 17.763 | `microsoft-learn.microsoft_code_sample_search` |
| bm25 | claude_v2 | 150 | ms-04 | `syn-incident.list_incidents` | 5.081 | `microsoft-learn.microsoft_docs_search` |
| bm25 | claude_v2 | 150 | x-02 | `syn-finance.currency_convert` | 8.054 | `aws-knowledge.aws___search_documentation` |
| bm25 | claude_v2 | 150 | x-05 | `microsoft-learn.microsoft_docs_search` | 2.280 | `huggingface.hub_repo_search` |
| bm25 | claude_v2 | 150 | x-07 | `syn-hr.request_leave` | 7.927 | `kiwi.search-flight` |
| bm25 | claude_v2 | 30 | aws-05 | `aws-knowledge.aws___list_regions` | 8.528 | `aws-knowledge.aws___get_regional_availability` |
| bm25 | claude_v2 | 30 | c7-03 | `context7.query-docs` | 6.992 | `context7.resolve-library-id` |
| bm25 | claude_v2 | 30 | c7-04 | `context7.query-docs` | 4.575 | `context7.resolve-library-id` |
| bm25 | claude_v2 | 30 | cf-01 | `cloudflare-docs.migrate_pages_to_workers_guide` | 7.001 | `cloudflare-docs.search_cloudflare_documentation` |
| bm25 | claude_v2 | 30 | cf-03 | `syn-cloudops.list_buckets` | 3.864 | `cloudflare-docs.search_cloudflare_documentation` |
| bm25 | claude_v2 | 30 | cursor-bot-002 | `astro-docs.search_astro_docs` | 6.570 | *abstain* |
| bm25 | claude_v2 | 30 | cursor-bot-004 | `syn-warehouse.run_sql` | 4.030 | *abstain* |
| bm25 | claude_v2 | 30 | cursor-bot-013 | `syn-crm.update_opportunity_stage` | 3.746 | *abstain* |
| bm25 | claude_v2 | 30 | cursor-bot-026 | `syn-ml-registry.list_experiments` | 4.859 | *abstain* |
| bm25 | claude_v2 | 30 | cursor-bot-033 | `deepwiki.ask_wiki_question` | 11.973 | *abstain* |
| bm25 | claude_v2 | 30 | cursor-bot-036 | `gitmcp.fetch_generic_documentation` | 6.914 | *abstain* |
| bm25 | claude_v2 | 30 | cursor-bot-054 | `aws-knowledge.aws___get_regional_availability` | 1.194 | *abstain* |
| bm25 | claude_v2 | 30 | cursor-bot-055 | `syn-ml-registry.search_models` | 3.459 | *abstain* |
| bm25 | claude_v2 | 30 | cursor-bot-075 | `svelte.playground-link` | 9.744 | *abstain* |
| bm25 | claude_v2 | 30 | cursor-bot-076 | `svelte.list-sections` | 4.936 | *abstain* |
| bm25 | claude_v2 | 30 | cursor-bot-078 | `svelte.get-documentation` | 4.773 | *abstain* |
| bm25 | claude_v2 | 30 | d-aws-avail-04 | `aws-knowledge.aws___read_documentation` | 4.172 | `aws-knowledge.aws___get_regional_availability` |
| bm25 | claude_v2 | 30 | d-aws-search-02 | `aws-knowledge.aws___read_documentation` | 4.509 | `aws-knowledge.aws___search_documentation` |
| bm25 | claude_v2 | 30 | d-aws-skill-01 | `aws-knowledge.aws___retrieve_skill` | 16.329 | `aws-knowledge.aws___search_documentation` |
| bm25 | claude_v2 | 30 | d-aws-skill-02 | `aws-knowledge.aws___retrieve_skill` | 8.802 | `aws-knowledge.aws___search_documentation` |
| bm25 | claude_v2 | 30 | d-c7-either-03 | `context7.query-docs` | 4.769 | `context7.resolve-library-id` |
| bm25 | claude_v2 | 30 | d-c7-query-03 | `syn-cloudops.list_instances` | 7.159 | `context7.query-docs` |
| bm25 | claude_v2 | 30 | d-dw-ask-03 | `huggingface.hub_repo_details` | 1.663 | `deepwiki.ask_wiki_question` |
| bm25 | claude_v2 | 30 | d-dw-read-02 | `deepwiki.ask_wiki_question` | 7.916 | `deepwiki.read_wiki_contents` |
| bm25 | claude_v2 | 30 | d-gm-searchdoc-03 | `microsoft-learn.microsoft_code_sample_search` | 5.517 | `gitmcp.search_generic_documentation` |
| bm25 | claude_v2 | 30 | d-gm-url-01 | `gitmcp.fetch_generic_documentation` | 4.202 | `gitmcp.fetch_generic_url_content` |
| bm25 | claude_v2 | 30 | d-hf-details-01 | `syn-crm.update_opportunity_stage` | 3.354 | `huggingface.hub_repo_details` |
| bm25 | claude_v2 | 30 | d-hf-fs-02 | `huggingface.hub_repo_details` | 6.781 | `huggingface.hf_fs` |
| bm25 | claude_v2 | 30 | d-kw-03 | `syn-travel.get_itinerary` | 3.700 | `kiwi.search-flight` |
| bm25 | claude_v2 | 30 | d-ms-code-02 | `aws-knowledge.aws___get_regional_availability` | 4.928 | `microsoft-learn.microsoft_code_sample_search` |
| bm25 | claude_v2 | 30 | d-sv-doc-02 | `svelte.svelte-autofixer` | 7.461 | `svelte.list-sections`, `svelte.get-documentation` |
| bm25 | claude_v2 | 30 | d-sv-doc-03 | `gitmcp.search_generic_code` | 0.000 | `svelte.list-sections`, `svelte.get-documentation` |
| bm25 | claude_v2 | 30 | d-sv-fix-03 | `svelte.playground-link` | 4.751 | `svelte.svelte-autofixer` |
| bm25 | claude_v2 | 30 | d-x-06 | `svelte.get-documentation` | 3.529 | `microsoft-learn.microsoft_docs_search` |
| bm25 | claude_v2 | 30 | dw-01 | `gitmcp.match_common_libs_owner_repo_mapping` | 4.396 | `deepwiki.ask_wiki_question` |
| bm25 | claude_v2 | 30 | ms-04 | `microsoft-learn.microsoft_code_sample_search` | 2.618 | `microsoft-learn.microsoft_docs_search` |
| bm25 | claude_v2 | 30 | x-02 | `syn-hr.get_employee` | 3.208 | `aws-knowledge.aws___search_documentation` |
| bm25 | claude_v2 | 30 | x-05 | `syn-market.earnings_calendar` | 0.000 | `huggingface.hub_repo_search` |
| bm25 | claude_v2 | 30 | x-07 | `syn-travel.search_flights` | 4.788 | `kiwi.search-flight` |
| bm25 | claude_v2 | 75 | aws-05 | `aws-knowledge.aws___list_regions` | 11.820 | `aws-knowledge.aws___get_regional_availability` |
| bm25 | claude_v2 | 75 | c7-03 | `context7.query-docs` | 7.756 | `context7.resolve-library-id` |
| bm25 | claude_v2 | 75 | c7-04 | `syn-calendar.create_event` | 5.944 | `context7.resolve-library-id` |
| bm25 | claude_v2 | 75 | cf-01 | `cloudflare-docs.migrate_pages_to_workers_guide` | 8.383 | `cloudflare-docs.search_cloudflare_documentation` |
| bm25 | claude_v2 | 75 | cf-03 | `syn-calendar.find_free_slots` | 7.587 | `cloudflare-docs.search_cloudflare_documentation` |
| bm25 | claude_v2 | 75 | cursor-bot-002 | `gitmcp.search_generic_code` | 3.673 | *abstain* |
| bm25 | claude_v2 | 75 | cursor-bot-004 | `huggingface.hub_repo_details` | 6.400 | *abstain* |
| bm25 | claude_v2 | 75 | cursor-bot-013 | `syn-crm.list_contacts` | 4.269 | *abstain* |
| bm25 | claude_v2 | 75 | cursor-bot-026 | `syn-ml-registry.get_model_version` | 11.156 | *abstain* |
| bm25 | claude_v2 | 75 | cursor-bot-033 | `deepwiki.read_wiki_structure` | 6.890 | *abstain* |
| bm25 | claude_v2 | 75 | cursor-bot-036 | `deepwiki.read_wiki_structure` | 7.523 | *abstain* |
| bm25 | claude_v2 | 75 | cursor-bot-054 | `syn-hr.get_employee` | 3.297 | *abstain* |
| bm25 | claude_v2 | 75 | cursor-bot-055 | `syn-ml-registry.get_model_version` | 5.763 | *abstain* |
| bm25 | claude_v2 | 75 | cursor-bot-075 | `svelte.playground-link` | 9.558 | *abstain* |
| bm25 | claude_v2 | 75 | cursor-bot-076 | `svelte.playground-link` | 9.902 | *abstain* |
| bm25 | claude_v2 | 75 | cursor-bot-078 | `svelte.svelte-autofixer` | 10.219 | *abstain* |
| bm25 | claude_v2 | 75 | d-aws-avail-04 | `syn-cloudops.deploy_stack` | 7.516 | `aws-knowledge.aws___get_regional_availability` |
| bm25 | claude_v2 | 75 | d-aws-search-02 | `syn-mail.get_message` | 6.971 | `aws-knowledge.aws___search_documentation` |
| bm25 | claude_v2 | 75 | d-aws-skill-01 | `aws-knowledge.aws___retrieve_skill` | 20.979 | `aws-knowledge.aws___search_documentation` |
| bm25 | claude_v2 | 75 | d-aws-skill-02 | `aws-knowledge.aws___retrieve_skill` | 11.758 | `aws-knowledge.aws___search_documentation` |
| bm25 | claude_v2 | 75 | d-c7-either-03 | `context7.query-docs` | 6.371 | `context7.resolve-library-id` |
| bm25 | claude_v2 | 75 | d-c7-query-03 | `syn-cloudops.list_instances` | 8.432 | `context7.query-docs` |
| bm25 | claude_v2 | 75 | d-dw-ask-03 | `context7.query-docs` | 2.035 | `deepwiki.ask_wiki_question` |
| bm25 | claude_v2 | 75 | d-dw-read-02 | `deepwiki.ask_wiki_question` | 8.841 | `deepwiki.read_wiki_contents` |
| bm25 | claude_v2 | 75 | d-gm-searchdoc-03 | `syn-hr.get_employee` | 7.745 | `gitmcp.search_generic_documentation` |
| bm25 | claude_v2 | 75 | d-gm-url-01 | `syn-web.fetch_url` | 4.453 | `gitmcp.fetch_generic_url_content` |
| bm25 | claude_v2 | 75 | d-hf-details-01 | `syn-hr.get_employee` | 3.032 | `huggingface.hub_repo_details` |
| bm25 | claude_v2 | 75 | d-hf-fs-02 | `huggingface.hub_repo_details` | 7.638 | `huggingface.hf_fs` |
| bm25 | claude_v2 | 75 | d-hf-search-01 | `syn-incident.list_incidents` | 4.388 | `huggingface.hub_repo_search` |
| bm25 | claude_v2 | 75 | d-ms-code-02 | `aws-knowledge.aws___list_regions` | 6.058 | `microsoft-learn.microsoft_code_sample_search` |
| bm25 | claude_v2 | 75 | d-sv-doc-02 | `svelte.svelte-autofixer` | 9.639 | `svelte.list-sections`, `svelte.get-documentation` |
| bm25 | claude_v2 | 75 | d-sv-doc-03 | `huggingface.hf_fs` | 0.682 | `svelte.list-sections`, `svelte.get-documentation` |
| bm25 | claude_v2 | 75 | d-sv-fix-03 | `svelte.playground-link` | 5.951 | `svelte.svelte-autofixer` |
| bm25 | claude_v2 | 75 | d-x-06 | `svelte.get-documentation` | 3.902 | `microsoft-learn.microsoft_docs_search` |
| bm25 | claude_v2 | 75 | dw-01 | `huggingface.hub_repo_search` | 5.427 | `deepwiki.ask_wiki_question` |
| bm25 | claude_v2 | 75 | gm-03 | `gitmcp.match_common_libs_owner_repo_mapping` | 7.293 | `gitmcp.fetch_generic_documentation` |
| bm25 | claude_v2 | 75 | ms-04 | `syn-codehost.create_pull_request` | 4.511 | `microsoft-learn.microsoft_docs_search` |
| bm25 | claude_v2 | 75 | x-02 | `syn-market.fx_rate` | 7.637 | `aws-knowledge.aws___search_documentation` |
| bm25 | claude_v2 | 75 | x-05 | `microsoft-learn.microsoft_docs_search` | 2.039 | `huggingface.hub_repo_search` |
| bm25 | claude_v2 | 75 | x-07 | `syn-hr.request_leave` | 7.572 | `kiwi.search-flight` |
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

## Errors (5279)

- or-jev-factored / cursor-bot-054@multi_server_confused: DecisionError: HTTP 402: {"error":{"message":"Insufficient credits. Add more using https://openrouter.ai/settings/credits","code":402,"metadata":{"limit_source":"openrouter_credits","remedy_hint":"Add
- or-jev-factored / cursor-bot-054@multi_server_confused: DecisionError: HTTP 402: {"error":{"message":"Insufficient credits. Add more using https://openrouter.ai/settings/credits","code":402,"metadata":{"limit_source":"openrouter_credits","remedy_hint":"Add
- or-jev-factored / cursor-bot-054@multi_server_confused: DecisionError: HTTP 402: {"error":{"message":"Insufficient credits. Add more using https://openrouter.ai/settings/credits","code":402,"metadata":{"limit_source":"openrouter_credits","remedy_hint":"Add
- or-jev-factored / cursor-bot-055@multi_server_confused: DecisionError: HTTP 402: {"error":{"message":"Insufficient credits. Add more using https://openrouter.ai/settings/credits","code":402,"metadata":{"limit_source":"openrouter_credits","remedy_hint":"Add
- or-jev-factored / cursor-bot-055@multi_server_confused: DecisionError: HTTP 402: {"error":{"message":"Insufficient credits. Add more using https://openrouter.ai/settings/credits","code":402,"metadata":{"limit_source":"openrouter_credits","remedy_hint":"Add
- or-jev-factored / cursor-bot-056@multi_server_confused: DecisionError: HTTP 402: {"error":{"message":"Insufficient credits. Add more using https://openrouter.ai/settings/credits","code":402,"metadata":{"limit_source":"openrouter_credits","remedy_hint":"Add
- or-jev-factored / cursor-bot-056@multi_server_confused: DecisionError: HTTP 402: {"error":{"message":"Insufficient credits. Add more using https://openrouter.ai/settings/credits","code":402,"metadata":{"limit_source":"openrouter_credits","remedy_hint":"Add
- or-jev-factored / cursor-bot-056@multi_server_confused: DecisionError: HTTP 402: {"error":{"message":"Insufficient credits. Add more using https://openrouter.ai/settings/credits","code":402,"metadata":{"limit_source":"openrouter_credits","remedy_hint":"Add
- or-jev-factored / cursor-bot-057@multi_server_confused: DecisionError: HTTP 402: {"error":{"message":"Insufficient credits. Add more using https://openrouter.ai/settings/credits","code":402,"metadata":{"limit_source":"openrouter_credits","remedy_hint":"Add
- or-jev-factored / cursor-bot-057@multi_server_confused: DecisionError: HTTP 402: {"error":{"message":"Insufficient credits. Add more using https://openrouter.ai/settings/credits","code":402,"metadata":{"limit_source":"openrouter_credits","remedy_hint":"Add
- or-jev-factored / cursor-bot-057@multi_server_confused: DecisionError: HTTP 402: {"error":{"message":"Insufficient credits. Add more using https://openrouter.ai/settings/credits","code":402,"metadata":{"limit_source":"openrouter_credits","remedy_hint":"Add
- or-jev-factored / cursor-bot-058@multi_server_confused: DecisionError: HTTP 402: {"error":{"message":"Insufficient credits. Add more using https://openrouter.ai/settings/credits","code":402,"metadata":{"limit_source":"openrouter_credits","remedy_hint":"Add
- or-jev-factored / cursor-bot-058@multi_server_confused: DecisionError: HTTP 402: {"error":{"message":"Insufficient credits. Add more using https://openrouter.ai/settings/credits","code":402,"metadata":{"limit_source":"openrouter_credits","remedy_hint":"Add
- or-jev-factored / cursor-bot-058@multi_server_confused: DecisionError: HTTP 402: {"error":{"message":"Insufficient credits. Add more using https://openrouter.ai/settings/credits","code":402,"metadata":{"limit_source":"openrouter_credits","remedy_hint":"Add
- or-jev-factored / cursor-bot-064@multi_server_confused: DecisionError: HTTP 402: {"error":{"message":"Insufficient credits. Add more using https://openrouter.ai/settings/credits","code":402,"metadata":{"limit_source":"openrouter_credits","remedy_hint":"Add
- or-jev-factored / cursor-bot-064@multi_server_confused: DecisionError: HTTP 402: {"error":{"message":"Insufficient credits. Add more using https://openrouter.ai/settings/credits","code":402,"metadata":{"limit_source":"openrouter_credits","remedy_hint":"Add
- or-jev-factored / cursor-bot-064@multi_server_confused: DecisionError: HTTP 402: {"error":{"message":"Insufficient credits. Add more using https://openrouter.ai/settings/credits","code":402,"metadata":{"limit_source":"openrouter_credits","remedy_hint":"Add
- or-jev-factored / cursor-bot-068@multi_server_confused: DecisionError: HTTP 402: {"error":{"message":"Insufficient credits. Add more using https://openrouter.ai/settings/credits","code":402,"metadata":{"limit_source":"openrouter_credits","remedy_hint":"Add
- or-jev-factored / cursor-bot-068@multi_server_confused: DecisionError: HTTP 402: {"error":{"message":"Insufficient credits. Add more using https://openrouter.ai/settings/credits","code":402,"metadata":{"limit_source":"openrouter_credits","remedy_hint":"Add
- or-jev-factored / cursor-bot-068@multi_server_confused: DecisionError: HTTP 402: {"error":{"message":"Insufficient credits. Add more using https://openrouter.ai/settings/credits","code":402,"metadata":{"limit_source":"openrouter_credits","remedy_hint":"Add
