# ToolDiscoveryBench — luna-factored-v2

## Accuracy

| router | suite | tools | n | no-tool | err | **acc** | top-1 | lenient | top-3 | server@1 | abstain ✓ | false abstain | refused |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| or-jev-factored | multi_confused | fixed | 393 | 87 | 0 | **80.4%** | 87.9% | 93.5% | 95.8% | 95.4% | 54.0% | 2.3% | 0.0% |
| or-jev-factored | multi_server | fixed | 618 | 132 | 0 | **83.2%** | 89.1% | 94.4% | 97.5% | 96.3% | 61.4% | 0.6% | 0.0% |
| or-jev-factored | one_server | fixed | 618 | 132 | 0 | **88.0%** | 91.8% | 97.1% | 99.4% | 99.4% | 74.2% | 0.6% | 0.0% |
| or-luna-factored | multi_confused | fixed | 393 | 87 | 0 | **80.9%** | 81.4% | 95.1% | 97.1% | 96.1% | 79.3% | 1.0% | 23.7% |
| or-luna-factored | multi_server | fixed | 618 | 132 | 0 | **85.9%** | 87.0% | 94.4% | 95.1% | 96.3% | 81.8% | 2.5% | 20.9% |
| or-luna-factored | one_server | fixed | 618 | 132 | 0 | **87.9%** | 88.9% | 96.9% | 99.4% | 100.0% | 84.1% | 0.0% | 1.0% |

*acc: answerable questions need the gold tool first, no-tool questions need an abstain. top-1 / lenient / top-3 / server@1 are over answerable questions only; lenient also accepts tools labelled acceptable. abstain ✓: share of no-tool questions where the router abstained. false abstain: share of answerable ones where it did. refused: share of questions where the backend refused a per-server sub-question (scored as P = 0 for that server, which can flatter accuracy).*

## Speed, cost and calibration

| router | suite | tools | p50 ms | p95 ms | calls | in-tok | $/1k q | ECE | Brier | conf ✓ | conf ✗ |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| or-jev-factored | multi_confused | fixed | 221 | 312 | 1.000 | 1,827 | 0.077 | 0.056 | 0.111 | 0.888 | 0.588 |
| or-jev-factored | multi_server | fixed | 220 | 291 | 1.000 | 1,674 | 0.070 | 0.057 | 0.089 | 0.924 | 0.579 |
| or-jev-factored | one_server | fixed | 217 | 299 | 1.000 | 715 | 0.030 | 0.048 | 0.076 | 0.925 | 0.616 |
| or-luna-factored | multi_confused | fixed | 190 | 395 | 1.000 | 1,660 | 0.166 | 0.106 | 0.154 | 0.890 | 0.715 |
| or-luna-factored | multi_server | fixed | 188 | 420 | 1.000 | 1,504 | 0.150 | 0.050 | 0.088 | 0.914 | 0.647 |
| or-luna-factored | one_server | fixed | 171 | 246 | 1.000 | 540 | 0.054 | 0.050 | 0.089 | 0.932 | 0.663 |

*Calibration columns are filled only for calibrated routers (Jev). conf ✓ / ✗ is the mean top-1 probability when right vs wrong; a big gap lets you set an abstain threshold.*

## Top-1 with 95% bootstrap confidence intervals

| router | suite | tools | n | top-1 | 95% CI | test n | test top-1 | test 95% CI |
|---|---|---:|---:|---:|---|---:|---:|---|
| or-jev-factored | multi_confused | fixed | 102 | 87.9% | 80.7%–93.8% | 102 | 87.9% | 80.7%–93.8% |
| or-jev-factored | multi_server | fixed | 162 | 89.1% | 84.2%–93.4% | 162 | 89.1% | 84.2%–93.4% |
| or-jev-factored | one_server | fixed | 162 | 91.8% | 87.4%–95.7% | 162 | 91.8% | 87.4%–95.7% |
| or-luna-factored | multi_confused | fixed | 102 | 81.4% | 73.5%–88.2% | 102 | 81.4% | 73.5%–88.2% |
| or-luna-factored | multi_server | fixed | 162 | 87.0% | 81.5%–92.0% | 162 | 87.0% | 81.5%–92.0% |
| or-luna-factored | one_server | fixed | 162 | 88.9% | 84.0%–93.2% | 162 | 88.9% | 84.0%–93.2% |

*Answerable questions only; 1000 seeded resamples over questions (repeats averaged per question). *test* is the frozen held-out split (`data/golden/splits/test_qids.txt`); publish numbers from it with repeats ≥ 3.*

## Accuracy by question tag (all suites and sizes pooled)

| router | confusable | generator:claude | generator:cursor-bot | generator:openai | judges_split | multi_server | multi_server_confused | needs_human_review | no_tool | one_server | relabelled | rewritten | split:test |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| or-jev-factored | 82.9% | 83.3% | 60.7% | 93.4% | 56.5% | 83.2% | 80.4% | 60.7% | 64.4% | 88.0% | 53.1% | 100.0% | 84.3% |
| or-luna-factored | 81.9% | 77.5% | 84.5% | 92.7% | 38.9% | 85.9% | 80.9% | 84.5% | 82.1% | 87.9% | 33.3% | 100.0% | 85.5% |

## Accuracy by question author (model family that wrote the question)

| router | claude | cursor | gpt |
|---|---:|---:|---:|
| or-jev-factored | 83.3% | 60.7% | 93.4% |
| or-luna-factored | 77.5% | 84.5% | 92.7% |

## Accuracy by question author (exact model)

| router | claude-fable-5-1 | claude-haiku-4-5 | claude-opus-5-5 | claude-sonnet-5-5 | cursor-bot | gpt-5.5 | gpt-5.6-luna | gpt-5.6-sol | gpt-5.6-terra | gpt-6-astra |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| or-jev-factored | 83.1% | 83.9% | 87.2% | 78.9% | 60.7% | 95.8% | 92.5% | 91.1% | 95.4% | 90.0% |
| or-luna-factored | 82.2% | 70.0% | 89.7% | 68.3% | 84.5% | 93.8% | 93.5% | 90.2% | 95.4% | 86.7% |

## Accuracy without possibly contaminated questions

| router | suite | tools | n | acc | top-1 | n kept | acc kept | top-1 kept |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| or-jev-factored | multi_confused | fixed | 393 | 80.4% | 87.9% | 303 | 76.6% | 85.6% |
| or-jev-factored | multi_server | fixed | 618 | 83.2% | 89.1% | 450 | 81.3% | 89.3% |
| or-jev-factored | one_server | fixed | 618 | 88.0% | 91.8% | 450 | 86.7% | 91.4% |
| or-luna-factored | multi_confused | fixed | 393 | 80.9% | 81.4% | 303 | 78.2% | 77.8% |
| or-luna-factored | multi_server | fixed | 618 | 85.9% | 87.0% | 450 | 84.0% | 84.8% |
| or-luna-factored | one_server | fixed | 618 | 87.9% | 88.9% | 450 | 86.0% | 87.5% |

*kept: questions not written by `gpt-5.6-sol`, `claude-opus-5-5`, `gpt-5.6-luna` (judges of the labels, or the same model line as a router under test).*

## Misses (repeat 0, first 200)

| router | suite | tools | item | picked | p | gold |
|---|---|---:|---|---|---:|---|
| or-jev-factored | multi_confused | fixed | claude-fable-5-1-020@multi_server_confused | `context7.resolve-library-id` | 0.420 | `context7.query-docs` |
| or-jev-factored | multi_confused | fixed | claude-fable-5-1-021@multi_server_confused | `gitmcp.search_generic_code` | 0.488 | `deepwiki.ask_wiki_question` |
| or-jev-factored | multi_confused | fixed | claude-fable-5-1-022@multi_server_confused | `context7.resolve-library-id` | 0.666 | `deepwiki.ask_wiki_question` |
| or-jev-factored | multi_confused | fixed | claude-fable-5-1-055@multi_server_confused | `svelte.get-documentation` | 1.000 | `svelte.list-sections` |
| or-jev-factored | multi_confused | fixed | claude-haiku-4-5-002@multi_server_confused | `context7.resolve-library-id` | 0.562 | *abstain* |
| or-jev-factored | multi_confused | fixed | claude-haiku-4-5-053@multi_server_confused | `microsoft-learn.microsoft_docs_fetch` | 0.882 | `microsoft-learn.microsoft_docs_search` |
| or-jev-factored | multi_confused | fixed | claude-haiku-4-5-056@multi_server_confused | `svelte.get-documentation` | 0.810 | `svelte.list-sections` |
| or-jev-factored | multi_confused | fixed | claude-opus-5-5-004@multi_server_confused | *abstained* | 0.343 | `aws-knowledge.aws___read_documentation` |
| or-jev-factored | multi_confused | fixed | claude-sonnet-5-5-024@multi_server_confused | *abstained* | 0.247 | `deepwiki.read_wiki_contents` |
| or-jev-factored | multi_confused | fixed | claude-sonnet-5-5-055@multi_server_confused | `svelte.get-documentation` | 1.000 | `svelte.list-sections` |
| or-jev-factored | multi_confused | fixed | cursor-bot-002@multi_server_confused | `astro-docs.search_astro_docs` | 0.770 | *abstain* |
| or-jev-factored | multi_confused | fixed | cursor-bot-004@multi_server_confused | `gitmcp.search_generic_code` | 0.320 | *abstain* |
| or-jev-factored | multi_confused | fixed | cursor-bot-013@multi_server_confused | `aws-knowledge.aws___search_documentation` | 0.585 | *abstain* |
| or-jev-factored | multi_confused | fixed | cursor-bot-033@multi_server_confused | `deepwiki.read_wiki_structure` | 0.390 | *abstain* |
| or-jev-factored | multi_confused | fixed | cursor-bot-043@multi_server_confused | `gitmcp.search_generic_code` | 0.328 | *abstain* |
| or-jev-factored | multi_confused | fixed | cursor-bot-054@multi_server_confused | `huggingface.hf_whoami` | 0.394 | *abstain* |
| or-jev-factored | multi_confused | fixed | cursor-bot-055@multi_server_confused | `huggingface.hf_whoami` | 0.423 | *abstain* |
| or-jev-factored | multi_confused | fixed | cursor-bot-056@multi_server_confused | `huggingface.hf_whoami` | 0.473 | *abstain* |
| or-jev-factored | multi_confused | fixed | cursor-bot-074@multi_server_confused | `svelte.get-documentation` | 0.486 | *abstain* |
| or-jev-factored | multi_confused | fixed | cursor-bot-075@multi_server_confused | `svelte.get-documentation` | 0.739 | *abstain* |
| or-jev-factored | multi_confused | fixed | cursor-bot-076@multi_server_confused | `svelte.get-documentation` | 0.476 | *abstain* |
| or-jev-factored | multi_confused | fixed | cursor-bot-078@multi_server_confused | `svelte.get-documentation` | 0.489 | *abstain* |
| or-jev-factored | multi_confused | fixed | gpt-5.6-luna-004@multi_server_confused | `aws-knowledge.aws___search_documentation` | 0.750 | `aws-knowledge.aws___read_documentation` |
| or-jev-factored | multi_confused | fixed | gpt-5.6-terra-020@multi_server_confused | `context7.resolve-library-id` | 0.710 | `context7.query-docs` |
| or-jev-factored | multi_confused | fixed | gpt-6-astra-032@multi_server_confused | `gitmcp.match_common_libs_owner_repo_mapping` | 0.348 | `gitmcp.search_generic_documentation` |
| or-jev-factored | multi_server | fixed | claude-fable-5-1-020@multi_server | `context7.resolve-library-id` | 0.425 | `context7.query-docs` |
| or-jev-factored | multi_server | fixed | claude-fable-5-1-021@multi_server | `gitmcp.search_generic_code` | 0.360 | `deepwiki.ask_wiki_question` |
| or-jev-factored | multi_server | fixed | claude-fable-5-1-022@multi_server | `context7.resolve-library-id` | 0.695 | `deepwiki.ask_wiki_question` |
| or-jev-factored | multi_server | fixed | claude-fable-5-1-024@multi_server | `deepwiki.read_wiki_structure` | 0.473 | `deepwiki.read_wiki_contents` |
| or-jev-factored | multi_server | fixed | claude-fable-5-1-055@multi_server | `svelte.get-documentation` | 1.000 | `svelte.list-sections` |
| or-jev-factored | multi_server | fixed | claude-haiku-4-5-002@multi_server | `astro-docs.search_astro_docs` | 0.260 | *abstain* |
| or-jev-factored | multi_server | fixed | claude-haiku-4-5-031@multi_server | `gitmcp.match_common_libs_owner_repo_mapping` | 0.490 | `gitmcp.search_generic_documentation` |
| or-jev-factored | multi_server | fixed | claude-haiku-4-5-053@multi_server | `microsoft-learn.microsoft_docs_fetch` | 0.960 | `microsoft-learn.microsoft_docs_search` |
| or-jev-factored | multi_server | fixed | claude-haiku-4-5-056@multi_server | `svelte.get-documentation` | 0.780 | `svelte.list-sections` |
| or-jev-factored | multi_server | fixed | claude-opus-5-5-004@multi_server | *abstained* | 0.224 | `aws-knowledge.aws___read_documentation` |
| or-jev-factored | multi_server | fixed | claude-opus-5-5-065@multi_server | `cloudflare-docs.search_cloudflare_documentation` | 0.950 | *abstain* |
| or-jev-factored | multi_server | fixed | claude-sonnet-5-5-024@multi_server | `gitmcp.fetch_generic_documentation` | 0.556 | `deepwiki.read_wiki_contents` |
| or-jev-factored | multi_server | fixed | claude-sonnet-5-5-055@multi_server | `svelte.get-documentation` | 0.940 | `svelte.list-sections` |
| or-jev-factored | multi_server | fixed | claude-sonnet-5-5-068@multi_server | `aws-knowledge.aws___search_documentation` | 0.281 | *abstain* |
| or-jev-factored | multi_server | fixed | claude-sonnet-5-5-070@multi_server | `huggingface.hf_whoami` | 0.823 | *abstain* |
| or-jev-factored | multi_server | fixed | cursor-bot-002@multi_server | `astro-docs.search_astro_docs` | 0.870 | *abstain* |
| or-jev-factored | multi_server | fixed | cursor-bot-033@multi_server | `deepwiki.ask_wiki_question` | 0.262 | *abstain* |
| or-jev-factored | multi_server | fixed | cursor-bot-036@multi_server | `gitmcp.match_common_libs_owner_repo_mapping` | 0.546 | *abstain* |
| or-jev-factored | multi_server | fixed | cursor-bot-043@multi_server | `gitmcp.match_common_libs_owner_repo_mapping` | 0.195 | *abstain* |
| or-jev-factored | multi_server | fixed | cursor-bot-047@multi_server | `gitmcp.fetch_generic_documentation` | 0.555 | *abstain* |
| or-jev-factored | multi_server | fixed | cursor-bot-055@multi_server | `huggingface.hf_whoami` | 0.576 | *abstain* |
| or-jev-factored | multi_server | fixed | cursor-bot-056@multi_server | `huggingface.hf_whoami` | 0.429 | *abstain* |
| or-jev-factored | multi_server | fixed | cursor-bot-057@multi_server | `kiwi.search-flight` | 0.650 | *abstain* |
| or-jev-factored | multi_server | fixed | cursor-bot-064@multi_server | `kiwi.search-flight` | 0.360 | *abstain* |
| or-jev-factored | multi_server | fixed | cursor-bot-074@multi_server | `svelte.get-documentation` | 0.439 | *abstain* |
| or-jev-factored | multi_server | fixed | cursor-bot-075@multi_server | `svelte.get-documentation` | 0.747 | *abstain* |
| or-jev-factored | multi_server | fixed | cursor-bot-076@multi_server | `svelte.get-documentation` | 0.477 | *abstain* |
| or-jev-factored | multi_server | fixed | cursor-bot-078@multi_server | `svelte.get-documentation` | 0.480 | *abstain* |
| or-jev-factored | multi_server | fixed | gpt-5.5-065@multi_server | `huggingface.hf_whoami` | 0.714 | *abstain* |
| or-jev-factored | multi_server | fixed | gpt-5.6-luna-021@multi_server | `gitmcp.search_generic_code` | 0.792 | `deepwiki.ask_wiki_question` |
| or-jev-factored | multi_server | fixed | gpt-5.6-luna-026@multi_server | `gitmcp.fetch_generic_documentation` | 0.522 | `deepwiki.read_wiki_structure` |
| or-jev-factored | multi_server | fixed | gpt-5.6-sol-024@multi_server | `deepwiki.read_wiki_structure` | 0.301 | `deepwiki.read_wiki_contents` |
| or-jev-factored | multi_server | fixed | gpt-5.6-sol-029@multi_server | `gitmcp.match_common_libs_owner_repo_mapping` | 0.570 | `gitmcp.fetch_generic_documentation` |
| or-jev-factored | multi_server | fixed | gpt-5.6-terra-020@multi_server | `context7.resolve-library-id` | 0.640 | `context7.query-docs` |
| or-jev-factored | multi_server | fixed | gpt-6-astra-032@multi_server | `gitmcp.match_common_libs_owner_repo_mapping` | 0.309 | `gitmcp.search_generic_documentation` |
| or-jev-factored | one_server | fixed | claude-fable-5-1-020@one_server | `context7.resolve-library-id` | 0.671 | `context7.query-docs` |
| or-jev-factored | one_server | fixed | claude-fable-5-1-024@one_server | `deepwiki.read_wiki_structure` | 0.487 | `deepwiki.read_wiki_contents` |
| or-jev-factored | one_server | fixed | claude-fable-5-1-055@one_server | `svelte.get-documentation` | 1.000 | `svelte.list-sections` |
| or-jev-factored | one_server | fixed | claude-haiku-4-5-034@one_server | `gitmcp.search_generic_code` | 0.544 | `gitmcp.match_common_libs_owner_repo_mapping` |
| or-jev-factored | one_server | fixed | claude-haiku-4-5-053@one_server | `microsoft-learn.microsoft_docs_fetch` | 0.950 | `microsoft-learn.microsoft_docs_search` |
| or-jev-factored | one_server | fixed | claude-haiku-4-5-056@one_server | `svelte.get-documentation` | 0.960 | `svelte.list-sections` |
| or-jev-factored | one_server | fixed | claude-opus-5-5-004@one_server | *abstained* | 0.259 | `aws-knowledge.aws___read_documentation` |
| or-jev-factored | one_server | fixed | claude-opus-5-5-065@one_server | `cloudflare-docs.search_cloudflare_documentation` | 0.790 | *abstain* |
| or-jev-factored | one_server | fixed | claude-sonnet-5-5-024@one_server | `deepwiki.read_wiki_structure` | 0.518 | `deepwiki.read_wiki_contents` |
| or-jev-factored | one_server | fixed | claude-sonnet-5-5-055@one_server | `svelte.get-documentation` | 1.000 | `svelte.list-sections` |
| or-jev-factored | one_server | fixed | claude-sonnet-5-5-070@one_server | `huggingface.hf_whoami` | 0.722 | *abstain* |
| or-jev-factored | one_server | fixed | cursor-bot-002@one_server | `astro-docs.search_astro_docs` | 0.620 | *abstain* |
| or-jev-factored | one_server | fixed | cursor-bot-047@one_server | `gitmcp.fetch_generic_documentation` | 0.380 | *abstain* |
| or-jev-factored | one_server | fixed | cursor-bot-055@one_server | `huggingface.hf_whoami` | 0.461 | *abstain* |
| or-jev-factored | one_server | fixed | cursor-bot-056@one_server | `huggingface.hf_whoami` | 0.428 | *abstain* |
| or-jev-factored | one_server | fixed | cursor-bot-074@one_server | `svelte.get-documentation` | 0.469 | *abstain* |
| or-jev-factored | one_server | fixed | cursor-bot-075@one_server | `svelte.get-documentation` | 0.639 | *abstain* |
| or-jev-factored | one_server | fixed | cursor-bot-076@one_server | `svelte.get-documentation` | 0.527 | *abstain* |
| or-jev-factored | one_server | fixed | cursor-bot-078@one_server | `svelte.get-documentation` | 0.469 | *abstain* |
| or-jev-factored | one_server | fixed | gpt-5.5-065@one_server | `huggingface.hf_whoami` | 0.689 | *abstain* |
| or-jev-factored | one_server | fixed | gpt-5.6-luna-004@one_server | `aws-knowledge.aws___search_documentation` | 0.540 | `aws-knowledge.aws___read_documentation` |
| or-jev-factored | one_server | fixed | gpt-5.6-sol-024@one_server | `deepwiki.read_wiki_structure` | 0.473 | `deepwiki.read_wiki_contents` |
| or-jev-factored | one_server | fixed | gpt-5.6-sol-029@one_server | `gitmcp.match_common_libs_owner_repo_mapping` | 0.554 | `gitmcp.fetch_generic_documentation` |
| or-jev-factored | one_server | fixed | gpt-5.6-terra-020@one_server | `context7.resolve-library-id` | 0.590 | `context7.query-docs` |
| or-jev-factored | one_server | fixed | gpt-6-astra-032@one_server | `gitmcp.match_common_libs_owner_repo_mapping` | 0.362 | `gitmcp.search_generic_documentation` |
| or-luna-factored | multi_confused | fixed | claude-fable-5-1-004@multi_server_confused | `aws-knowledge.aws___search_documentation` | 0.920 | `aws-knowledge.aws___read_documentation` |
| or-luna-factored | multi_confused | fixed | claude-fable-5-1-020@multi_server_confused | `context7.resolve-library-id` | 0.640 | `context7.query-docs` |
| or-luna-factored | multi_confused | fixed | claude-fable-5-1-022@multi_server_confused | `context7.resolve-library-id` | 0.890 | `deepwiki.ask_wiki_question` |
| or-luna-factored | multi_confused | fixed | claude-fable-5-1-024@multi_server_confused | `deepwiki.read_wiki_structure` | 0.682 | `deepwiki.read_wiki_contents` |
| or-luna-factored | multi_confused | fixed | claude-fable-5-1-055@multi_server_confused | `svelte.get-documentation` | 0.874 | `svelte.list-sections` |
| or-luna-factored | multi_confused | fixed | claude-haiku-4-5-002@multi_server_confused | `context7.resolve-library-id` | 0.921 | *abstain* |
| or-luna-factored | multi_confused | fixed | claude-haiku-4-5-010@multi_server_confused | `aws-knowledge.aws___search_documentation` | 0.800 | `aws-knowledge.aws___get_regional_availability` |
| or-luna-factored | multi_confused | fixed | claude-haiku-4-5-030@multi_server_confused | `deepwiki.read_wiki_structure` | 0.400 | `gitmcp.match_common_libs_owner_repo_mapping` |
| or-luna-factored | multi_confused | fixed | claude-haiku-4-5-033@multi_server_confused | `gitmcp.search_generic_code` | 0.564 | `gitmcp.match_common_libs_owner_repo_mapping` |
| or-luna-factored | multi_confused | fixed | claude-haiku-4-5-034@multi_server_confused | `gitmcp.search_generic_code` | 0.854 | `gitmcp.match_common_libs_owner_repo_mapping` |
| or-luna-factored | multi_confused | fixed | claude-haiku-4-5-053@multi_server_confused | `microsoft-learn.microsoft_docs_fetch` | 0.773 | `microsoft-learn.microsoft_docs_search` |
| or-luna-factored | multi_confused | fixed | claude-opus-5-5-003@multi_server_confused | `aws-knowledge.aws___search_documentation` | 0.980 | `aws-knowledge.aws___read_documentation` |
| or-luna-factored | multi_confused | fixed | claude-opus-5-5-031@multi_server_confused | `deepwiki.ask_wiki_question` | 0.629 | `gitmcp.search_generic_documentation` |
| or-luna-factored | multi_confused | fixed | claude-sonnet-5-5-012@multi_server_confused | `aws-knowledge.aws___search_documentation` | 0.640 | `aws-knowledge.aws___retrieve_skill` |
| or-luna-factored | multi_confused | fixed | claude-sonnet-5-5-023@multi_server_confused | `deepwiki.read_wiki_structure` | 0.630 | `deepwiki.read_wiki_contents` |
| or-luna-factored | multi_confused | fixed | claude-sonnet-5-5-055@multi_server_confused | `svelte.get-documentation` | 1.000 | `svelte.list-sections` |
| or-luna-factored | multi_confused | fixed | cursor-bot-002@multi_server_confused | `astro-docs.search_astro_docs` | 0.580 | *abstain* |
| or-luna-factored | multi_confused | fixed | cursor-bot-013@multi_server_confused | `aws-knowledge.aws___search_documentation` | 0.874 | *abstain* |
| or-luna-factored | multi_confused | fixed | cursor-bot-054@multi_server_confused | `huggingface.hub_repo_details` | 0.312 | *abstain* |
| or-luna-factored | multi_confused | fixed | cursor-bot-055@multi_server_confused | `huggingface.hub_repo_details` | 0.442 | *abstain* |
| or-luna-factored | multi_confused | fixed | cursor-bot-076@multi_server_confused | `svelte.list-sections` | 0.462 | *abstain* |
| or-luna-factored | multi_confused | fixed | gpt-5.6-luna-058@multi_server_confused | `svelte.list-sections` | 0.807 | `svelte.get-documentation` |
| or-luna-factored | multi_confused | fixed | gpt-5.6-terra-008@multi_server_confused | `aws-knowledge.aws___search_documentation` | 0.485 | `aws-knowledge.aws___list_regions` |
| or-luna-factored | multi_confused | fixed | gpt-5.6-terra-020@multi_server_confused | `context7.resolve-library-id` | 1.000 | `context7.query-docs` |
| or-luna-factored | multi_confused | fixed | gpt-6-astra-023@multi_server_confused | *abstained* | 0.216 | `deepwiki.read_wiki_contents` |
| or-luna-factored | multi_server | fixed | claude-fable-5-1-004@multi_server | `aws-knowledge.aws___search_documentation` | 0.747 | `aws-knowledge.aws___read_documentation` |
| or-luna-factored | multi_server | fixed | claude-fable-5-1-020@multi_server | `context7.resolve-library-id` | 0.733 | `context7.query-docs` |
| or-luna-factored | multi_server | fixed | claude-fable-5-1-024@multi_server | `deepwiki.read_wiki_structure` | 0.792 | `deepwiki.read_wiki_contents` |
| or-luna-factored | multi_server | fixed | claude-fable-5-1-055@multi_server | `svelte.get-documentation` | 0.990 | `svelte.list-sections` |
| or-luna-factored | multi_server | fixed | claude-haiku-4-5-010@multi_server | `aws-knowledge.aws___search_documentation` | 0.630 | `aws-knowledge.aws___get_regional_availability` |
| or-luna-factored | multi_server | fixed | claude-haiku-4-5-030@multi_server | `gitmcp.fetch_generic_documentation` | 0.595 | `gitmcp.match_common_libs_owner_repo_mapping` |
| or-luna-factored | multi_server | fixed | claude-haiku-4-5-033@multi_server | `gitmcp.search_generic_code` | 0.594 | `gitmcp.match_common_libs_owner_repo_mapping` |
| or-luna-factored | multi_server | fixed | claude-haiku-4-5-034@multi_server | `gitmcp.search_generic_code` | 0.862 | `gitmcp.match_common_libs_owner_repo_mapping` |
| or-luna-factored | multi_server | fixed | claude-haiku-4-5-036@multi_server | *abstained* | 0.179 | `gitmcp.fetch_generic_url_content` |
| or-luna-factored | multi_server | fixed | claude-haiku-4-5-053@multi_server | `microsoft-learn.microsoft_docs_fetch` | 0.799 | `microsoft-learn.microsoft_docs_search` |
| or-luna-factored | multi_server | fixed | claude-opus-5-5-003@multi_server | `aws-knowledge.aws___search_documentation` | 0.550 | `aws-knowledge.aws___read_documentation` |
| or-luna-factored | multi_server | fixed | claude-opus-5-5-065@multi_server | `cloudflare-docs.search_cloudflare_documentation` | 0.990 | *abstain* |
| or-luna-factored | multi_server | fixed | claude-sonnet-5-5-024@multi_server | `deepwiki.read_wiki_structure` | 0.488 | `deepwiki.read_wiki_contents` |
| or-luna-factored | multi_server | fixed | claude-sonnet-5-5-036@multi_server | *abstained* | 0.390 | `gitmcp.fetch_generic_url_content` |
| or-luna-factored | multi_server | fixed | claude-sonnet-5-5-055@multi_server | `svelte.get-documentation` | 0.980 | `svelte.list-sections` |
| or-luna-factored | multi_server | fixed | claude-sonnet-5-5-068@multi_server | `aws-knowledge.aws___retrieve_skill` | 0.801 | *abstain* |
| or-luna-factored | multi_server | fixed | claude-sonnet-5-5-070@multi_server | `huggingface.hf_whoami` | 0.451 | *abstain* |
| or-luna-factored | multi_server | fixed | cursor-bot-011@multi_server | `aws-knowledge.aws___search_documentation` | 0.504 | *abstain* |
| or-luna-factored | multi_server | fixed | cursor-bot-024@multi_server | `cloudflare-docs.search_cloudflare_documentation` | 0.790 | *abstain* |
| or-luna-factored | multi_server | fixed | cursor-bot-054@multi_server | `huggingface.hf_fs` | 0.340 | *abstain* |
| or-luna-factored | multi_server | fixed | cursor-bot-055@multi_server | `huggingface.hub_repo_details` | 0.426 | *abstain* |
| or-luna-factored | multi_server | fixed | gpt-5.5-012@multi_server | *abstained* | 0.323 | `aws-knowledge.aws___retrieve_skill` |
| or-luna-factored | multi_server | fixed | gpt-5.5-065@multi_server | `huggingface.hf_fs` | 0.530 | *abstain* |
| or-luna-factored | multi_server | fixed | gpt-5.6-luna-004@multi_server | `aws-knowledge.aws___search_documentation` | 0.451 | `aws-knowledge.aws___read_documentation` |
| or-luna-factored | multi_server | fixed | gpt-5.6-luna-021@multi_server | `gitmcp.search_generic_code` | 0.445 | `deepwiki.ask_wiki_question` |
| or-luna-factored | multi_server | fixed | gpt-5.6-sol-024@multi_server | `deepwiki.read_wiki_structure` | 0.524 | `deepwiki.read_wiki_contents` |
| or-luna-factored | multi_server | fixed | gpt-5.6-terra-030@multi_server | `deepwiki.read_wiki_structure` | 0.805 | `gitmcp.fetch_generic_documentation` |
| or-luna-factored | multi_server | fixed | gpt-6-astra-023@multi_server | *abstained* | 0.226 | `deepwiki.read_wiki_contents` |
| or-luna-factored | multi_server | fixed | gpt-6-astra-032@multi_server | `gitmcp.match_common_libs_owner_repo_mapping` | 0.347 | `gitmcp.search_generic_documentation` |
| or-luna-factored | one_server | fixed | claude-fable-5-1-004@one_server | `aws-knowledge.aws___search_documentation` | 0.500 | `aws-knowledge.aws___read_documentation` |
| or-luna-factored | one_server | fixed | claude-fable-5-1-020@one_server | `context7.resolve-library-id` | 0.810 | `context7.query-docs` |
| or-luna-factored | one_server | fixed | claude-fable-5-1-024@one_server | `deepwiki.read_wiki_structure` | 0.800 | `deepwiki.read_wiki_contents` |
| or-luna-factored | one_server | fixed | claude-fable-5-1-055@one_server | `svelte.get-documentation` | 0.910 | `svelte.list-sections` |
| or-luna-factored | one_server | fixed | claude-haiku-4-5-002@one_server | `astro-docs.search_astro_docs` | 0.600 | *abstain* |
| or-luna-factored | one_server | fixed | claude-haiku-4-5-010@one_server | `aws-knowledge.aws___search_documentation` | 0.830 | `aws-knowledge.aws___get_regional_availability` |
| or-luna-factored | one_server | fixed | claude-haiku-4-5-030@one_server | `gitmcp.fetch_generic_documentation` | 0.941 | `gitmcp.match_common_libs_owner_repo_mapping` |
| or-luna-factored | one_server | fixed | claude-haiku-4-5-033@one_server | `gitmcp.search_generic_code` | 0.892 | `gitmcp.match_common_libs_owner_repo_mapping` |
| or-luna-factored | one_server | fixed | claude-haiku-4-5-053@one_server | `microsoft-learn.microsoft_docs_fetch` | 0.911 | `microsoft-learn.microsoft_docs_search` |
| or-luna-factored | one_server | fixed | claude-haiku-4-5-056@one_server | `svelte.get-documentation` | 0.910 | `svelte.list-sections` |
| or-luna-factored | one_server | fixed | claude-sonnet-5-5-012@one_server | `aws-knowledge.aws___search_documentation` | 0.460 | `aws-knowledge.aws___retrieve_skill` |
| or-luna-factored | one_server | fixed | claude-sonnet-5-5-023@one_server | `deepwiki.read_wiki_structure` | 0.610 | `deepwiki.read_wiki_contents` |
| or-luna-factored | one_server | fixed | claude-sonnet-5-5-024@one_server | `deepwiki.read_wiki_structure` | 0.519 | `deepwiki.read_wiki_contents` |
| or-luna-factored | one_server | fixed | claude-sonnet-5-5-055@one_server | `svelte.get-documentation` | 1.000 | `svelte.list-sections` |
| or-luna-factored | one_server | fixed | claude-sonnet-5-5-070@one_server | `huggingface.hf_whoami` | 0.573 | *abstain* |
| or-luna-factored | one_server | fixed | cursor-bot-011@one_server | `aws-knowledge.aws___search_documentation` | 0.244 | *abstain* |
| or-luna-factored | one_server | fixed | cursor-bot-054@one_server | `huggingface.hf_fs` | 0.266 | *abstain* |
| or-luna-factored | one_server | fixed | cursor-bot-055@one_server | `huggingface.hf_whoami` | 0.405 | *abstain* |
| or-luna-factored | one_server | fixed | cursor-bot-056@one_server | `huggingface.hf_fs` | 0.275 | *abstain* |
| or-luna-factored | one_server | fixed | gpt-5.5-065@one_server | `huggingface.hf_fs` | 0.621 | *abstain* |
| or-luna-factored | one_server | fixed | gpt-5.6-luna-058@one_server | `svelte.list-sections` | 0.770 | `svelte.get-documentation` |
| or-luna-factored | one_server | fixed | gpt-5.6-sol-019@one_server | `context7.resolve-library-id` | 0.740 | `context7.query-docs` |
| or-luna-factored | one_server | fixed | gpt-5.6-sol-024@one_server | `deepwiki.read_wiki_structure` | 0.863 | `deepwiki.read_wiki_contents` |
| or-luna-factored | one_server | fixed | gpt-5.6-sol-042@one_server | `huggingface.hub_repo_search` | 0.490 | `huggingface.hub_repo_details` |
| or-luna-factored | one_server | fixed | gpt-6-astra-032@one_server | `gitmcp.match_common_libs_owner_repo_mapping` | 0.647 | `gitmcp.search_generic_documentation` |
