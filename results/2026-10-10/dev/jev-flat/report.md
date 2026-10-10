# ToolDiscoveryBench — dev-jev-flat

## Accuracy

| router | suite | tools | n | no-tool | err | **acc** | top-1 | lenient | top-3 | server@1 | abstain ✓ | false abstain | refused |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| or-jev-flat | multi_confused | fixed | 274 | 52 | 0 | **85.4%** | 85.6% | 92.8% | 98.6% | 94.6% | 84.6% | 0.0% | 0.0% |
| or-jev-flat | multi_server | fixed | 490 | 103 | 0 | **89.6%** | 90.4% | 93.3% | 98.2% | 96.9% | 86.4% | 0.5% | 0.0% |
| or-jev-flat | one_server | fixed | 490 | 103 | 0 | **93.3%** | 92.8% | 95.9% | 99.0% | 99.2% | 95.1% | 0.8% | 0.0% |

*acc: answerable questions need the gold tool first, no-tool questions need an abstain. top-1 / lenient / top-3 / server@1 are over answerable questions only; lenient also accepts tools labelled acceptable. abstain ✓: share of no-tool questions where the router abstained. false abstain: share of answerable ones where it did. refused: share of questions where the backend refused a per-server sub-question (scored as P = 0 for that server, which can flatter accuracy).*

## Speed, cost and calibration

| router | suite | tools | p50 ms | p95 ms | calls | in-tok | $/1k q | ECE | Brier | conf ✓ | conf ✗ |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| or-jev-flat | multi_confused | fixed | 157 | 224 | 1.000 | 1,354 | 0.057 | 0.043 | 0.092 | 0.921 | 0.620 |
| or-jev-flat | multi_server | fixed | 159 | 223 | 1.000 | 1,235 | 0.052 | 0.030 | 0.067 | 0.941 | 0.626 |
| or-jev-flat | one_server | fixed | 155 | 221 | 1.000 | 612 | 0.026 | 0.018 | 0.058 | 0.952 | 0.774 |

*Calibration columns are filled only for calibrated routers (Jev). conf ✓ / ✗ is the mean top-1 probability when right vs wrong; a big gap lets you set an abstain threshold.*

## Top-1 with 95% bootstrap confidence intervals

| router | suite | tools | n | top-1 | 95% CI | test n | test top-1 | test 95% CI |
|---|---|---:|---:|---:|---|---:|---:|---|
| or-jev-flat | multi_confused | fixed | 222 | 85.6% | 80.6%–90.1% | 0 | – | – |
| or-jev-flat | multi_server | fixed | 387 | 90.4% | 87.6%–93.3% | 0 | – | – |
| or-jev-flat | one_server | fixed | 387 | 92.8% | 90.2%–95.1% | 0 | – | – |

*Answerable questions only; 1000 seeded resamples over questions (repeats averaged per question). *test* is the frozen held-out split (`data/golden/splits/test_qids.txt`); publish numbers from it with repeats ≥ 3.*

## Accuracy by question tag (all suites and sizes pooled)

| router | confusable | generator:claude | generator:cursor-bot | generator:openai | judges_split | multi_server | multi_server_confused | needs_human_review | no_tool | one_server | relabelled | rewritten | split:dev |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| or-jev-flat | 87.0% | 89.4% | 89.7% | 90.8% | 64.9% | 89.6% | 85.4% | 89.7% | 89.5% | 93.3% | 61.1% | 100.0% | 90.1% |

## Accuracy by question author (model family that wrote the question)

| router | claude | cursor | gpt |
|---|---:|---:|---:|
| or-jev-flat | 89.4% | 89.7% | 90.8% |

## Accuracy by question author (exact model)

| router | claude-fable-5-1 | claude-haiku-4-5 | claude-opus-5-5 | claude-sonnet-5-5 | cursor-bot | gpt-5.5 | gpt-5.6-luna | gpt-5.6-sol | gpt-5.6-terra | gpt-6-astra |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| or-jev-flat | 94.2% | 83.1% | 94.4% | 86.8% | 89.7% | 92.9% | 88.9% | 93.8% | 87.8% | 89.9% |

## Accuracy without possibly contaminated questions

| router | suite | tools | n | acc | top-1 | n kept | acc kept | top-1 kept |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| or-jev-flat | multi_confused | fixed | 274 | 85.4% | 85.6% | 201 | 83.6% | 83.2% |
| or-jev-flat | multi_server | fixed | 490 | 89.6% | 90.4% | 341 | 88.9% | 89.4% |
| or-jev-flat | one_server | fixed | 490 | 93.3% | 92.8% | 341 | 92.7% | 92.1% |

*kept: questions not written by `gpt-5.6-sol`, `claude-opus-5-5`, `gpt-5.6-luna` (judges of the labels, or the same model line as a router under test).*

## Misses (repeat 0, first 200)

| router | suite | tools | item | picked | p | gold |
|---|---|---:|---|---|---:|---|
| or-jev-flat | multi_confused | fixed | claude-fable-5-1-023@multi_server_confused | `gitmcp.fetch_generic_documentation` | 0.660 | `deepwiki.read_wiki_contents` |
| or-jev-flat | multi_confused | fixed | claude-haiku-4-5-003@multi_server_confused | `aws-knowledge.aws___read_documentation` | 0.670 | `aws-knowledge.aws___search_documentation` |
| or-jev-flat | multi_confused | fixed | claude-haiku-4-5-008@multi_server_confused | `aws-knowledge.aws___get_regional_availability` | 0.680 | `aws-knowledge.aws___list_regions` |
| or-jev-flat | multi_confused | fixed | claude-haiku-4-5-011@multi_server_confused | `aws-knowledge.aws___retrieve_skill` | 0.560 | `aws-knowledge.aws___search_documentation` |
| or-jev-flat | multi_confused | fixed | claude-haiku-4-5-022@multi_server_confused | `context7.resolve-library-id` | 0.780 | `deepwiki.ask_wiki_question` |
| or-jev-flat | multi_confused | fixed | claude-haiku-4-5-023@multi_server_confused | `gitmcp.match_common_libs_owner_repo_mapping` | 0.610 | `deepwiki.read_wiki_structure` |
| or-jev-flat | multi_confused | fixed | claude-haiku-4-5-025@multi_server_confused | `context7.resolve-library-id` | 0.430 | `deepwiki.read_wiki_contents` |
| or-jev-flat | multi_confused | fixed | claude-haiku-4-5-040@multi_server_confused | `huggingface.hf_fs` | 0.730 | `huggingface.hub_repo_search` |
| or-jev-flat | multi_confused | fixed | claude-haiku-4-5-055@multi_server_confused | `svelte.get-documentation` | 1.000 | `svelte.list-sections` |
| or-jev-flat | multi_confused | fixed | claude-opus-5-5-062@multi_server_confused | `svelte.get-documentation` | 0.600 | `svelte.svelte-autofixer` |
| or-jev-flat | multi_confused | fixed | claude-sonnet-5-5-019@multi_server_confused | `context7.resolve-library-id` | 0.540 | `context7.query-docs` |
| or-jev-flat | multi_confused | fixed | claude-sonnet-5-5-021@multi_server_confused | `context7.resolve-library-id` | 0.540 | `deepwiki.ask_wiki_question` |
| or-jev-flat | multi_confused | fixed | claude-sonnet-5-5-022@multi_server_confused | `context7.resolve-library-id` | 0.400 | `deepwiki.ask_wiki_question` |
| or-jev-flat | multi_confused | fixed | claude-sonnet-5-5-032@multi_server_confused | `gitmcp.match_common_libs_owner_repo_mapping` | 0.710 | `gitmcp.search_generic_documentation` |
| or-jev-flat | multi_confused | fixed | claude-sonnet-5-5-056@multi_server_confused | `svelte.get-documentation` | 0.960 | `svelte.list-sections` |
| or-jev-flat | multi_confused | fixed | claude-sonnet-5-5-069@multi_server_confused | `svelte.get-documentation` | 0.410 | `svelte.svelte-autofixer` |
| or-jev-flat | multi_confused | fixed | cursor-bot-003@multi_server_confused | `astro-docs.search_astro_docs` | 0.590 | *abstain* |
| or-jev-flat | multi_confused | fixed | cursor-bot-007@multi_server_confused | `astro-docs.search_astro_docs` | 0.700 | *abstain* |
| or-jev-flat | multi_confused | fixed | cursor-bot-020@multi_server_confused | `cloudflare-docs.search_cloudflare_documentation` | 0.500 | *abstain* |
| or-jev-flat | multi_confused | fixed | cursor-bot-022@multi_server_confused | `cloudflare-docs.search_cloudflare_documentation` | 0.530 | *abstain* |
| or-jev-flat | multi_confused | fixed | cursor-bot-034@multi_server_confused | `deepwiki.read_wiki_contents` | 0.350 | *abstain* |
| or-jev-flat | multi_confused | fixed | cursor-bot-049@multi_server_confused | `huggingface.hf_whoami` | 0.600 | *abstain* |
| or-jev-flat | multi_confused | fixed | cursor-bot-050@multi_server_confused | `huggingface.hf_whoami` | 0.400 | *abstain* |
| or-jev-flat | multi_confused | fixed | cursor-bot-060@multi_server_confused | `kiwi.search-flight` | 0.600 | *abstain* |
| or-jev-flat | multi_confused | fixed | gpt-5.5-019@multi_server_confused | `context7.resolve-library-id` | 0.630 | `context7.query-docs` |
| or-jev-flat | multi_confused | fixed | gpt-5.5-020@multi_server_confused | `context7.resolve-library-id` | 0.800 | `context7.query-docs` |
| or-jev-flat | multi_confused | fixed | gpt-5.5-021@multi_server_confused | `context7.resolve-library-id` | 0.520 | `deepwiki.ask_wiki_question` |
| or-jev-flat | multi_confused | fixed | gpt-5.6-luna-019@multi_server_confused | `context7.resolve-library-id` | 0.700 | `context7.query-docs` |
| or-jev-flat | multi_confused | fixed | gpt-5.6-luna-023@multi_server_confused | `gitmcp.fetch_generic_documentation` | 0.530 | `deepwiki.read_wiki_contents` |
| or-jev-flat | multi_confused | fixed | gpt-5.6-luna-054@multi_server_confused | `microsoft-learn.microsoft_docs_search` | 0.840 | `microsoft-learn.microsoft_docs_fetch` |
| or-jev-flat | multi_confused | fixed | gpt-5.6-luna-057@multi_server_confused | `svelte.get-documentation` | 0.980 | `svelte.list-sections` |
| or-jev-flat | multi_confused | fixed | gpt-5.6-sol-020@multi_server_confused | `context7.resolve-library-id` | 0.760 | `context7.query-docs` |
| or-jev-flat | multi_confused | fixed | gpt-5.6-sol-022@multi_server_confused | `context7.resolve-library-id` | 0.390 | `deepwiki.ask_wiki_question` |
| or-jev-flat | multi_confused | fixed | gpt-5.6-terra-019@multi_server_confused | `context7.resolve-library-id` | 0.550 | `context7.query-docs` |
| or-jev-flat | multi_confused | fixed | gpt-5.6-terra-021@multi_server_confused | `context7.resolve-library-id` | 0.470 | `deepwiki.ask_wiki_question` |
| or-jev-flat | multi_confused | fixed | gpt-5.6-terra-022@multi_server_confused | `gitmcp.match_common_libs_owner_repo_mapping` | 0.600 | `deepwiki.ask_wiki_question` |
| or-jev-flat | multi_confused | fixed | gpt-5.6-terra-024@multi_server_confused | `deepwiki.read_wiki_structure` | 0.530 | `deepwiki.read_wiki_contents` |
| or-jev-flat | multi_confused | fixed | gpt-5.6-terra-032@multi_server_confused | `context7.resolve-library-id` | 0.400 | `gitmcp.search_generic_documentation` |
| or-jev-flat | multi_confused | fixed | gpt-6-astra-020@multi_server_confused | `context7.resolve-library-id` | 0.750 | `context7.query-docs` |
| or-jev-flat | multi_confused | fixed | gpt-6-astra-031@multi_server_confused | `gitmcp.match_common_libs_owner_repo_mapping` | 0.780 | `gitmcp.search_generic_documentation` |
| or-jev-flat | multi_server | fixed | claude-fable-5-1-019@multi_server | `context7.resolve-library-id` | 0.860 | `context7.query-docs` |
| or-jev-flat | multi_server | fixed | claude-fable-5-1-023@multi_server | `gitmcp.fetch_generic_documentation` | 0.800 | `deepwiki.read_wiki_contents` |
| or-jev-flat | multi_server | fixed | claude-fable-5-1-064@multi_server | `huggingface.hf_whoami` | 0.600 | *abstain* |
| or-jev-flat | multi_server | fixed | claude-haiku-4-5-003@multi_server | `aws-knowledge.aws___read_documentation` | 0.750 | `aws-knowledge.aws___search_documentation` |
| or-jev-flat | multi_server | fixed | claude-haiku-4-5-008@multi_server | `aws-knowledge.aws___get_regional_availability` | 0.600 | `aws-knowledge.aws___list_regions` |
| or-jev-flat | multi_server | fixed | claude-haiku-4-5-022@multi_server | *abstained* | 0.110 | `deepwiki.ask_wiki_question` |
| or-jev-flat | multi_server | fixed | claude-haiku-4-5-040@multi_server | `huggingface.hf_fs` | 0.790 | `huggingface.hub_repo_search` |
| or-jev-flat | multi_server | fixed | claude-haiku-4-5-054@multi_server | `microsoft-learn.microsoft_docs_fetch` | 0.530 | `microsoft-learn.microsoft_docs_search` |
| or-jev-flat | multi_server | fixed | claude-haiku-4-5-055@multi_server | `svelte.get-documentation` | 1.000 | `svelte.list-sections` |
| or-jev-flat | multi_server | fixed | claude-haiku-4-5-067@multi_server | `huggingface.hf_whoami` | 0.570 | *abstain* |
| or-jev-flat | multi_server | fixed | claude-haiku-4-5-068@multi_server | `cloudflare-docs.search_cloudflare_documentation` | 0.580 | *abstain* |
| or-jev-flat | multi_server | fixed | claude-opus-5-5-020@multi_server | `context7.resolve-library-id` | 0.500 | `context7.query-docs` |
| or-jev-flat | multi_server | fixed | claude-opus-5-5-021@multi_server | `gitmcp.match_common_libs_owner_repo_mapping` | 0.610 | `deepwiki.ask_wiki_question` |
| or-jev-flat | multi_server | fixed | claude-opus-5-5-062@multi_server | `svelte.get-documentation` | 0.550 | `svelte.svelte-autofixer` |
| or-jev-flat | multi_server | fixed | claude-opus-5-5-064@multi_server | `huggingface.hf_whoami` | 0.600 | *abstain* |
| or-jev-flat | multi_server | fixed | claude-sonnet-5-5-019@multi_server | `context7.resolve-library-id` | 0.550 | `context7.query-docs` |
| or-jev-flat | multi_server | fixed | claude-sonnet-5-5-021@multi_server | `gitmcp.match_common_libs_owner_repo_mapping` | 0.660 | `deepwiki.ask_wiki_question` |
| or-jev-flat | multi_server | fixed | claude-sonnet-5-5-022@multi_server | `context7.resolve-library-id` | 0.360 | `deepwiki.ask_wiki_question` |
| or-jev-flat | multi_server | fixed | claude-sonnet-5-5-032@multi_server | `gitmcp.match_common_libs_owner_repo_mapping` | 0.530 | `gitmcp.search_generic_documentation` |
| or-jev-flat | multi_server | fixed | claude-sonnet-5-5-056@multi_server | `svelte.get-documentation` | 0.990 | `svelte.list-sections` |
| or-jev-flat | multi_server | fixed | claude-sonnet-5-5-066@multi_server | `huggingface.hf_whoami` | 0.790 | *abstain* |
| or-jev-flat | multi_server | fixed | claude-sonnet-5-5-069@multi_server | `svelte.get-documentation` | 0.410 | `svelte.svelte-autofixer` |
| or-jev-flat | multi_server | fixed | cursor-bot-007@multi_server | `astro-docs.search_astro_docs` | 0.920 | *abstain* |
| or-jev-flat | multi_server | fixed | cursor-bot-020@multi_server | `cloudflare-docs.search_cloudflare_documentation` | 0.500 | *abstain* |
| or-jev-flat | multi_server | fixed | cursor-bot-034@multi_server | `deepwiki.read_wiki_contents` | 0.390 | *abstain* |
| or-jev-flat | multi_server | fixed | cursor-bot-038@multi_server | `gitmcp.match_common_libs_owner_repo_mapping` | 0.570 | *abstain* |
| or-jev-flat | multi_server | fixed | cursor-bot-049@multi_server | `huggingface.hf_whoami` | 0.630 | *abstain* |
| or-jev-flat | multi_server | fixed | cursor-bot-050@multi_server | `huggingface.hf_whoami` | 0.340 | *abstain* |
| or-jev-flat | multi_server | fixed | gpt-5.5-019@multi_server | `context7.resolve-library-id` | 0.630 | `context7.query-docs` |
| or-jev-flat | multi_server | fixed | gpt-5.5-020@multi_server | `gitmcp.search_generic_documentation` | 0.280 | `context7.query-docs` |
| or-jev-flat | multi_server | fixed | gpt-5.5-021@multi_server | `gitmcp.match_common_libs_owner_repo_mapping` | 0.660 | `deepwiki.ask_wiki_question` |
| or-jev-flat | multi_server | fixed | gpt-5.5-022@multi_server | `gitmcp.match_common_libs_owner_repo_mapping` | 0.700 | `deepwiki.ask_wiki_question` |
| or-jev-flat | multi_server | fixed | gpt-5.6-luna-019@multi_server | `context7.resolve-library-id` | 0.450 | `context7.query-docs` |
| or-jev-flat | multi_server | fixed | gpt-5.6-luna-023@multi_server | `deepwiki.read_wiki_structure` | 0.930 | `deepwiki.read_wiki_contents` |
| or-jev-flat | multi_server | fixed | gpt-5.6-luna-054@multi_server | `microsoft-learn.microsoft_docs_search` | 0.770 | `microsoft-learn.microsoft_docs_fetch` |
| or-jev-flat | multi_server | fixed | gpt-5.6-luna-057@multi_server | `svelte.get-documentation` | 1.000 | `svelte.list-sections` |
| or-jev-flat | multi_server | fixed | gpt-5.6-luna-066@multi_server | `huggingface.hf_whoami` | 0.720 | *abstain* |
| or-jev-flat | multi_server | fixed | gpt-5.6-sol-004@multi_server | *abstained* | 0.160 | `aws-knowledge.aws___read_documentation` |
| or-jev-flat | multi_server | fixed | gpt-5.6-sol-020@multi_server | `gitmcp.search_generic_documentation` | 0.300 | `context7.query-docs` |
| or-jev-flat | multi_server | fixed | gpt-5.6-sol-031@multi_server | `gitmcp.match_common_libs_owner_repo_mapping` | 0.470 | `gitmcp.search_generic_documentation` |
| or-jev-flat | multi_server | fixed | gpt-5.6-sol-066@multi_server | `huggingface.hf_whoami` | 0.530 | *abstain* |
| or-jev-flat | multi_server | fixed | gpt-5.6-terra-019@multi_server | `context7.resolve-library-id` | 0.520 | `context7.query-docs` |
| or-jev-flat | multi_server | fixed | gpt-5.6-terra-021@multi_server | `gitmcp.match_common_libs_owner_repo_mapping` | 0.380 | `deepwiki.ask_wiki_question` |
| or-jev-flat | multi_server | fixed | gpt-5.6-terra-024@multi_server | `deepwiki.read_wiki_structure` | 0.740 | `deepwiki.read_wiki_contents` |
| or-jev-flat | multi_server | fixed | gpt-5.6-terra-032@multi_server | `gitmcp.match_common_libs_owner_repo_mapping` | 0.750 | `gitmcp.search_generic_documentation` |
| or-jev-flat | multi_server | fixed | gpt-6-astra-004@multi_server | `gitmcp.fetch_generic_url_content` | 0.490 | `aws-knowledge.aws___read_documentation` |
| or-jev-flat | multi_server | fixed | gpt-6-astra-020@multi_server | `context7.resolve-library-id` | 0.740 | `context7.query-docs` |
| or-jev-flat | multi_server | fixed | gpt-6-astra-031@multi_server | `gitmcp.match_common_libs_owner_repo_mapping` | 0.660 | `gitmcp.search_generic_documentation` |
| or-jev-flat | multi_server | fixed | gpt-6-astra-034@multi_server | `gitmcp.match_common_libs_owner_repo_mapping` | 0.800 | `gitmcp.search_generic_code` |
| or-jev-flat | multi_server | fixed | gpt-6-astra-058@multi_server | `svelte.get-documentation` | 0.620 | `svelte.list-sections` |
| or-jev-flat | multi_server | fixed | gpt-6-astra-064@multi_server | `huggingface.hf_whoami` | 0.540 | *abstain* |
| or-jev-flat | one_server | fixed | claude-fable-5-1-019@one_server | `context7.resolve-library-id` | 0.900 | `context7.query-docs` |
| or-jev-flat | one_server | fixed | claude-fable-5-1-064@one_server | `huggingface.hf_whoami` | 0.530 | *abstain* |
| or-jev-flat | one_server | fixed | claude-haiku-4-5-008@one_server | `aws-knowledge.aws___get_regional_availability` | 0.760 | `aws-knowledge.aws___list_regions` |
| or-jev-flat | one_server | fixed | claude-haiku-4-5-022@one_server | *abstained* | 0.310 | `deepwiki.ask_wiki_question` |
| or-jev-flat | one_server | fixed | claude-haiku-4-5-040@one_server | `huggingface.hf_fs` | 0.570 | `huggingface.hub_repo_search` |
| or-jev-flat | one_server | fixed | claude-haiku-4-5-054@one_server | `microsoft-learn.microsoft_docs_fetch` | 0.670 | `microsoft-learn.microsoft_docs_search` |
| or-jev-flat | one_server | fixed | claude-haiku-4-5-055@one_server | `svelte.get-documentation` | 1.000 | `svelte.list-sections` |
| or-jev-flat | one_server | fixed | claude-opus-5-5-019@one_server | `context7.resolve-library-id` | 0.520 | `context7.query-docs` |
| or-jev-flat | one_server | fixed | claude-opus-5-5-020@one_server | `context7.resolve-library-id` | 0.910 | `context7.query-docs` |
| or-jev-flat | one_server | fixed | claude-sonnet-5-5-019@one_server | `context7.resolve-library-id` | 0.860 | `context7.query-docs` |
| or-jev-flat | one_server | fixed | claude-sonnet-5-5-032@one_server | `gitmcp.match_common_libs_owner_repo_mapping` | 0.670 | `gitmcp.search_generic_documentation` |
| or-jev-flat | one_server | fixed | claude-sonnet-5-5-056@one_server | `svelte.get-documentation` | 0.970 | `svelte.list-sections` |
| or-jev-flat | one_server | fixed | claude-sonnet-5-5-066@one_server | `huggingface.hf_whoami` | 0.540 | *abstain* |
| or-jev-flat | one_server | fixed | claude-sonnet-5-5-069@one_server | *abstained* | 0.150 | `svelte.svelte-autofixer` |
| or-jev-flat | one_server | fixed | cursor-bot-007@one_server | `astro-docs.search_astro_docs` | 0.660 | *abstain* |
| or-jev-flat | one_server | fixed | cursor-bot-049@one_server | `huggingface.hf_whoami` | 0.640 | *abstain* |
| or-jev-flat | one_server | fixed | gpt-5.5-019@one_server | `context7.resolve-library-id` | 0.880 | `context7.query-docs` |
| or-jev-flat | one_server | fixed | gpt-5.5-020@one_server | `context7.resolve-library-id` | 0.910 | `context7.query-docs` |
| or-jev-flat | one_server | fixed | gpt-5.6-luna-019@one_server | `context7.resolve-library-id` | 0.860 | `context7.query-docs` |
| or-jev-flat | one_server | fixed | gpt-5.6-luna-023@one_server | `deepwiki.read_wiki_structure` | 0.990 | `deepwiki.read_wiki_contents` |
| or-jev-flat | one_server | fixed | gpt-5.6-luna-054@one_server | `microsoft-learn.microsoft_docs_search` | 0.710 | `microsoft-learn.microsoft_docs_fetch` |
| or-jev-flat | one_server | fixed | gpt-5.6-luna-057@one_server | `svelte.get-documentation` | 0.980 | `svelte.list-sections` |
| or-jev-flat | one_server | fixed | gpt-5.6-sol-004@one_server | *abstained* | 0.270 | `aws-knowledge.aws___read_documentation` |
| or-jev-flat | one_server | fixed | gpt-5.6-sol-020@one_server | `context7.resolve-library-id` | 0.820 | `context7.query-docs` |
| or-jev-flat | one_server | fixed | gpt-5.6-terra-019@one_server | `context7.resolve-library-id` | 0.900 | `context7.query-docs` |
| or-jev-flat | one_server | fixed | gpt-5.6-terra-024@one_server | `deepwiki.read_wiki_structure` | 0.800 | `deepwiki.read_wiki_contents` |
| or-jev-flat | one_server | fixed | gpt-5.6-terra-032@one_server | `gitmcp.match_common_libs_owner_repo_mapping` | 0.840 | `gitmcp.search_generic_documentation` |
| or-jev-flat | one_server | fixed | gpt-6-astra-020@one_server | `context7.resolve-library-id` | 0.870 | `context7.query-docs` |
| or-jev-flat | one_server | fixed | gpt-6-astra-031@one_server | `gitmcp.match_common_libs_owner_repo_mapping` | 0.760 | `gitmcp.search_generic_documentation` |
| or-jev-flat | one_server | fixed | gpt-6-astra-033@one_server | `gitmcp.match_common_libs_owner_repo_mapping` | 0.780 | `gitmcp.search_generic_code` |
| or-jev-flat | one_server | fixed | gpt-6-astra-034@one_server | `gitmcp.match_common_libs_owner_repo_mapping` | 0.550 | `gitmcp.search_generic_code` |
| or-jev-flat | one_server | fixed | gpt-6-astra-058@one_server | `svelte.get-documentation` | 0.890 | `svelte.list-sections` |
| or-jev-flat | one_server | fixed | gpt-6-astra-064@one_server | `huggingface.hf_whoami` | 0.480 | *abstain* |
