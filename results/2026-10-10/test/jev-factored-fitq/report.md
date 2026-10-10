# ToolDiscoveryBench — test-fitq

## Accuracy

| router | suite | tools | n | no-tool | err | **acc** | top-1 | lenient | top-3 | server@1 | abstain ✓ | false abstain | refused |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| or-jev-factored-fitq | multi_confused | fixed | 393 | 87 | 0 | **88.0%** | 88.6% | 96.1% | 98.0% | 98.0% | 86.2% | 0.0% | 0.0% |
| or-jev-factored-fitq | multi_server | fixed | 618 | 132 | 0 | **89.6%** | 88.5% | 94.0% | 96.7% | 95.7% | 93.9% | 1.4% | 0.0% |
| or-jev-factored-fitq | one_server | fixed | 618 | 132 | 0 | **92.4%** | 90.9% | 96.5% | 98.8% | 98.8% | 97.7% | 1.2% | 0.0% |

*acc: answerable questions need the gold tool first, no-tool questions need an abstain. top-1 / lenient / top-3 / server@1 are over answerable questions only; lenient also accepts tools labelled acceptable. abstain ✓: share of no-tool questions where the router abstained. false abstain: share of answerable ones where it did. refused: share of questions where the backend refused a per-server sub-question (scored as P = 0 for that server, which can flatter accuracy).*

## Speed, cost and calibration

| router | suite | tools | p50 ms | p95 ms | calls | in-tok | $/1k q | ECE | Brier | conf ✓ | conf ✗ |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| or-jev-factored-fitq | multi_confused | fixed | 163 | 223 | 1.000 | 2,688 | 0.113 | 0.062 | 0.114 | 0.899 | 0.744 |
| or-jev-factored-fitq | multi_server | fixed | 161 | 218 | 1.000 | 2,440 | 0.102 | 0.053 | 0.072 | 0.934 | 0.663 |
| or-jev-factored-fitq | one_server | fixed | 156 | 218 | 1.000 | 906 | 0.038 | 0.046 | 0.062 | 0.952 | 0.742 |

*Calibration columns are filled only for calibrated routers (Jev). conf ✓ / ✗ is the mean top-1 probability when right vs wrong; a big gap lets you set an abstain threshold.*

## Top-1 with 95% bootstrap confidence intervals

| router | suite | tools | n | top-1 | 95% CI | test n | test top-1 | test 95% CI |
|---|---|---:|---:|---:|---|---:|---:|---|
| or-jev-factored-fitq | multi_confused | fixed | 102 | 88.6% | 81.7%–94.1% | 102 | 88.6% | 81.7%–94.1% |
| or-jev-factored-fitq | multi_server | fixed | 162 | 88.5% | 83.1%–93.0% | 162 | 88.5% | 83.1%–93.0% |
| or-jev-factored-fitq | one_server | fixed | 162 | 90.9% | 86.4%–94.9% | 162 | 90.9% | 86.4%–94.9% |

*Answerable questions only; 1000 seeded resamples over questions (repeats averaged per question). *test* is the frozen held-out split (`data/golden/splits/test_qids.txt`); publish numbers from it with repeats ≥ 3.*

## Accuracy by question tag (all suites and sizes pooled)

| router | confusable | generator:claude | generator:cursor-bot | generator:openai | judges_split | multi_server | multi_server_confused | needs_human_review | no_tool | one_server | relabelled | rewritten | split:test |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| or-jev-factored-fitq | 86.2% | 86.1% | 94.8% | 92.4% | 53.7% | 89.6% | 88.0% | 94.8% | 93.4% | 92.4% | 53.1% | 100.0% | 90.3% |

## Accuracy by question author (model family that wrote the question)

| router | claude | cursor | gpt |
|---|---:|---:|---:|
| or-jev-factored-fitq | 86.1% | 94.8% | 92.4% |

## Accuracy by question author (exact model)

| router | claude-fable-5-1 | claude-haiku-4-5 | claude-opus-5-5 | claude-sonnet-5-5 | cursor-bot | gpt-5.5 | gpt-5.6-luna | gpt-5.6-sol | gpt-5.6-terra | gpt-6-astra |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| or-jev-factored-fitq | 84.0% | 82.2% | 99.1% | 82.9% | 94.8% | 100.0% | 91.9% | 90.2% | 89.2% | 91.1% |

## Accuracy without possibly contaminated questions

| router | suite | tools | n | acc | top-1 | n kept | acc kept | top-1 kept |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| or-jev-factored-fitq | multi_confused | fixed | 393 | 88.0% | 88.6% | 303 | 85.5% | 85.2% |
| or-jev-factored-fitq | multi_server | fixed | 618 | 89.6% | 88.5% | 450 | 89.3% | 87.8% |
| or-jev-factored-fitq | one_server | fixed | 618 | 92.4% | 90.9% | 450 | 91.6% | 89.6% |

*kept: questions not written by `gpt-5.6-sol`, `claude-opus-5-5`, `gpt-5.6-luna` (judges of the labels, or the same model line as a router under test).*

## Misses (repeat 0, first 200)

| router | suite | tools | item | picked | p | gold |
|---|---|---:|---|---|---:|---|
| or-jev-factored-fitq | multi_confused | fixed | claude-fable-5-1-020@multi_server_confused | `context7.resolve-library-id` | 0.840 | `context7.query-docs` |
| or-jev-factored-fitq | multi_confused | fixed | claude-fable-5-1-021@multi_server_confused | `gitmcp.search_generic_code` | 0.502 | `deepwiki.ask_wiki_question` |
| or-jev-factored-fitq | multi_confused | fixed | claude-fable-5-1-022@multi_server_confused | `context7.resolve-library-id` | 0.753 | `deepwiki.ask_wiki_question` |
| or-jev-factored-fitq | multi_confused | fixed | claude-fable-5-1-055@multi_server_confused | `svelte.get-documentation` | 1.000 | `svelte.list-sections` |
| or-jev-factored-fitq | multi_confused | fixed | claude-haiku-4-5-002@multi_server_confused | `context7.resolve-library-id` | 0.697 | *abstain* |
| or-jev-factored-fitq | multi_confused | fixed | claude-haiku-4-5-053@multi_server_confused | `microsoft-learn.microsoft_docs_fetch` | 0.893 | `microsoft-learn.microsoft_docs_search` |
| or-jev-factored-fitq | multi_confused | fixed | claude-haiku-4-5-056@multi_server_confused | `svelte.get-documentation` | 0.810 | `svelte.list-sections` |
| or-jev-factored-fitq | multi_confused | fixed | claude-sonnet-5-5-023@multi_server_confused | `deepwiki.read_wiki_structure` | 0.449 | `deepwiki.read_wiki_contents` |
| or-jev-factored-fitq | multi_confused | fixed | claude-sonnet-5-5-024@multi_server_confused | `deepwiki.read_wiki_structure` | 0.614 | `deepwiki.read_wiki_contents` |
| or-jev-factored-fitq | multi_confused | fixed | claude-sonnet-5-5-055@multi_server_confused | `svelte.get-documentation` | 1.000 | `svelte.list-sections` |
| or-jev-factored-fitq | multi_confused | fixed | cursor-bot-002@multi_server_confused | `astro-docs.search_astro_docs` | 0.780 | *abstain* |
| or-jev-factored-fitq | multi_confused | fixed | cursor-bot-075@multi_server_confused | `svelte.get-documentation` | 0.870 | *abstain* |
| or-jev-factored-fitq | multi_confused | fixed | cursor-bot-076@multi_server_confused | `svelte.get-documentation` | 0.549 | *abstain* |
| or-jev-factored-fitq | multi_confused | fixed | gpt-5.6-luna-004@multi_server_confused | `aws-knowledge.aws___search_documentation` | 0.780 | `aws-knowledge.aws___read_documentation` |
| or-jev-factored-fitq | multi_confused | fixed | gpt-5.6-terra-020@multi_server_confused | `context7.resolve-library-id` | 0.760 | `context7.query-docs` |
| or-jev-factored-fitq | multi_confused | fixed | gpt-6-astra-032@multi_server_confused | `gitmcp.match_common_libs_owner_repo_mapping` | 0.541 | `gitmcp.search_generic_documentation` |
| or-jev-factored-fitq | multi_server | fixed | claude-fable-5-1-020@multi_server | `context7.resolve-library-id` | 0.710 | `context7.query-docs` |
| or-jev-factored-fitq | multi_server | fixed | claude-fable-5-1-022@multi_server | `context7.resolve-library-id` | 0.719 | `deepwiki.ask_wiki_question` |
| or-jev-factored-fitq | multi_server | fixed | claude-fable-5-1-024@multi_server | `deepwiki.read_wiki_structure` | 0.540 | `deepwiki.read_wiki_contents` |
| or-jev-factored-fitq | multi_server | fixed | claude-fable-5-1-055@multi_server | `svelte.get-documentation` | 1.000 | `svelte.list-sections` |
| or-jev-factored-fitq | multi_server | fixed | claude-haiku-4-5-002@multi_server | `astro-docs.search_astro_docs` | 0.510 | *abstain* |
| or-jev-factored-fitq | multi_server | fixed | claude-haiku-4-5-031@multi_server | `gitmcp.match_common_libs_owner_repo_mapping` | 0.486 | `gitmcp.search_generic_documentation` |
| or-jev-factored-fitq | multi_server | fixed | claude-haiku-4-5-053@multi_server | `microsoft-learn.microsoft_docs_fetch` | 0.970 | `microsoft-learn.microsoft_docs_search` |
| or-jev-factored-fitq | multi_server | fixed | claude-haiku-4-5-056@multi_server | `svelte.get-documentation` | 0.780 | `svelte.list-sections` |
| or-jev-factored-fitq | multi_server | fixed | claude-sonnet-5-5-024@multi_server | `gitmcp.fetch_generic_documentation` | 0.580 | `deepwiki.read_wiki_contents` |
| or-jev-factored-fitq | multi_server | fixed | claude-sonnet-5-5-055@multi_server | `svelte.get-documentation` | 0.950 | `svelte.list-sections` |
| or-jev-factored-fitq | multi_server | fixed | cursor-bot-076@multi_server | `svelte.get-documentation` | 0.640 | *abstain* |
| or-jev-factored-fitq | multi_server | fixed | gpt-5.6-luna-004@multi_server | `aws-knowledge.aws___search_documentation` | 0.530 | `aws-knowledge.aws___read_documentation` |
| or-jev-factored-fitq | multi_server | fixed | gpt-5.6-luna-021@multi_server | `gitmcp.search_generic_code` | 0.792 | `deepwiki.ask_wiki_question` |
| or-jev-factored-fitq | multi_server | fixed | gpt-5.6-luna-026@multi_server | `gitmcp.fetch_generic_documentation` | 0.561 | `deepwiki.read_wiki_structure` |
| or-jev-factored-fitq | multi_server | fixed | gpt-5.6-sol-019@multi_server | `context7.resolve-library-id` | 0.500 | `context7.query-docs` |
| or-jev-factored-fitq | multi_server | fixed | gpt-5.6-sol-024@multi_server | `deepwiki.read_wiki_structure` | 0.515 | `deepwiki.read_wiki_contents` |
| or-jev-factored-fitq | multi_server | fixed | gpt-5.6-sol-029@multi_server | `gitmcp.match_common_libs_owner_repo_mapping` | 0.610 | `gitmcp.fetch_generic_documentation` |
| or-jev-factored-fitq | multi_server | fixed | gpt-5.6-terra-004@multi_server | *abstained* | 0.750 | `aws-knowledge.aws___read_documentation` |
| or-jev-factored-fitq | multi_server | fixed | gpt-5.6-terra-020@multi_server | `context7.resolve-library-id` | 0.620 | `context7.query-docs` |
| or-jev-factored-fitq | multi_server | fixed | gpt-5.6-terra-060@multi_server | *abstained* | 0.822 | `svelte.playground-link` |
| or-jev-factored-fitq | multi_server | fixed | gpt-6-astra-032@multi_server | `gitmcp.match_common_libs_owner_repo_mapping` | 0.413 | `gitmcp.search_generic_documentation` |
| or-jev-factored-fitq | one_server | fixed | claude-fable-5-1-020@one_server | `context7.resolve-library-id` | 0.820 | `context7.query-docs` |
| or-jev-factored-fitq | one_server | fixed | claude-fable-5-1-024@one_server | `deepwiki.read_wiki_structure` | 0.560 | `deepwiki.read_wiki_contents` |
| or-jev-factored-fitq | one_server | fixed | claude-fable-5-1-055@one_server | `svelte.get-documentation` | 1.000 | `svelte.list-sections` |
| or-jev-factored-fitq | one_server | fixed | claude-haiku-4-5-002@one_server | `astro-docs.search_astro_docs` | 1.000 | *abstain* |
| or-jev-factored-fitq | one_server | fixed | claude-haiku-4-5-034@one_server | `gitmcp.search_generic_code` | 0.540 | `gitmcp.match_common_libs_owner_repo_mapping` |
| or-jev-factored-fitq | one_server | fixed | claude-haiku-4-5-053@one_server | `microsoft-learn.microsoft_docs_fetch` | 0.960 | `microsoft-learn.microsoft_docs_search` |
| or-jev-factored-fitq | one_server | fixed | claude-haiku-4-5-056@one_server | `svelte.get-documentation` | 0.970 | `svelte.list-sections` |
| or-jev-factored-fitq | one_server | fixed | claude-sonnet-5-5-023@one_server | `deepwiki.read_wiki_structure` | 0.520 | `deepwiki.read_wiki_contents` |
| or-jev-factored-fitq | one_server | fixed | claude-sonnet-5-5-024@one_server | `deepwiki.read_wiki_structure` | 0.740 | `deepwiki.read_wiki_contents` |
| or-jev-factored-fitq | one_server | fixed | claude-sonnet-5-5-055@one_server | `svelte.get-documentation` | 1.000 | `svelte.list-sections` |
| or-jev-factored-fitq | one_server | fixed | gpt-5.6-luna-004@one_server | `aws-knowledge.aws___search_documentation` | 0.510 | `aws-knowledge.aws___read_documentation` |
| or-jev-factored-fitq | one_server | fixed | gpt-5.6-sol-024@one_server | `deepwiki.read_wiki_structure` | 0.640 | `deepwiki.read_wiki_contents` |
| or-jev-factored-fitq | one_server | fixed | gpt-5.6-sol-029@one_server | `gitmcp.match_common_libs_owner_repo_mapping` | 0.560 | `gitmcp.fetch_generic_documentation` |
| or-jev-factored-fitq | one_server | fixed | gpt-5.6-terra-004@one_server | *abstained* | 0.740 | `aws-knowledge.aws___read_documentation` |
| or-jev-factored-fitq | one_server | fixed | gpt-5.6-terra-020@one_server | `context7.resolve-library-id` | 0.620 | `context7.query-docs` |
| or-jev-factored-fitq | one_server | fixed | gpt-5.6-terra-060@one_server | *abstained* | 0.850 | `svelte.playground-link` |
| or-jev-factored-fitq | one_server | fixed | gpt-6-astra-032@one_server | `gitmcp.match_common_libs_owner_repo_mapping` | 0.510 | `gitmcp.search_generic_documentation` |
