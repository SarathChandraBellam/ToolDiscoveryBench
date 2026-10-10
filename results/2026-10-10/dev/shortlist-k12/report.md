# ToolDiscoveryBench — dev-shortlist-k12

## Accuracy

| router | suite | tools | n | no-tool | err | **acc** | top-1 | lenient | top-3 | server@1 | abstain ✓ | false abstain | refused |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| shortlist-bge-jev | multi_confused | fixed | 274 | 52 | 0 | **88.0%** | 88.3% | 94.6% | 97.7% | 95.5% | 86.5% | 0.5% | 0.0% |
| shortlist-bge-jev | multi_server | fixed | 490 | 103 | 0 | **89.0%** | 89.9% | 92.5% | 97.4% | 96.6% | 85.4% | 1.0% | 0.0% |

*acc: answerable questions need the gold tool first, no-tool questions need an abstain. top-1 / lenient / top-3 / server@1 are over answerable questions only; lenient also accepts tools labelled acceptable. abstain ✓: share of no-tool questions where the router abstained. false abstain: share of answerable ones where it did. refused: share of questions where the backend refused a per-server sub-question (scored as P = 0 for that server, which can flatter accuracy).*

## Speed, cost and calibration

| router | suite | tools | p50 ms | p95 ms | calls | in-tok | $/1k q | ECE | Brier | conf ✓ | conf ✗ |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| shortlist-bge-jev | multi_confused | fixed | 183 | 248 | 1.000 | 1,214 | 0.051 | 0.039 | 0.084 | 0.922 | 0.653 |
| shortlist-bge-jev | multi_server | fixed | 188 | 252 | 1.000 | 1,159 | 0.049 | 0.036 | 0.071 | 0.943 | 0.646 |

*Calibration columns are filled only for calibrated routers (Jev). conf ✓ / ✗ is the mean top-1 probability when right vs wrong; a big gap lets you set an abstain threshold.*

## Top-1 with 95% bootstrap confidence intervals

| router | suite | tools | n | top-1 | 95% CI | test n | test top-1 | test 95% CI |
|---|---|---:|---:|---:|---|---:|---:|---|
| shortlist-bge-jev | multi_confused | fixed | 222 | 88.3% | 83.8%–92.3% | 0 | – | – |
| shortlist-bge-jev | multi_server | fixed | 387 | 89.9% | 86.8%–92.8% | 0 | – | – |

*Answerable questions only; 1000 seeded resamples over questions (repeats averaged per question). *test* is the frozen held-out split (`data/golden/splits/test_qids.txt`); publish numbers from it with repeats ≥ 3.*

## Accuracy by question tag (all suites and sizes pooled)

| router | confusable | generator:claude | generator:cursor-bot | generator:openai | judges_split | multi_server | multi_server_confused | needs_human_review | no_tool | relabelled | rewritten | split:dev |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| shortlist-bge-jev | 87.5% | 87.0% | 87.5% | 90.3% | 60.5% | 89.0% | 88.0% | 87.5% | 85.8% | 54.2% | 100.0% | 88.6% |

## Accuracy by question author (model family that wrote the question)

| router | claude | cursor | gpt |
|---|---:|---:|---:|
| shortlist-bge-jev | 87.0% | 87.5% | 90.3% |

## Accuracy by question author (exact model)

| router | claude-fable-5-1 | claude-haiku-4-5 | claude-opus-5-5 | claude-sonnet-5-5 | cursor-bot | gpt-5.5 | gpt-5.6-luna | gpt-5.6-sol | gpt-5.6-terra | gpt-6-astra |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| shortlist-bge-jev | 91.9% | 77.9% | 90.8% | 88.1% | 87.5% | 89.5% | 88.7% | 92.0% | 87.7% | 92.7% |

## Accuracy without possibly contaminated questions

| router | suite | tools | n | acc | top-1 | n kept | acc kept | top-1 kept |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| shortlist-bge-jev | multi_confused | fixed | 274 | 88.0% | 88.3% | 201 | 86.1% | 85.9% |
| shortlist-bge-jev | multi_server | fixed | 490 | 89.0% | 89.9% | 341 | 88.9% | 89.4% |

*kept: questions not written by `gpt-5.6-sol`, `claude-opus-5-5`, `gpt-5.6-luna` (judges of the labels, or the same model line as a router under test).*

## Misses (repeat 0, first 200)

| router | suite | tools | item | picked | p | gold |
|---|---|---:|---|---|---:|---|
| shortlist-bge-jev | multi_confused | fixed | claude-fable-5-1-023@multi_server_confused | `gitmcp.fetch_generic_documentation` | 0.850 | `deepwiki.read_wiki_contents` |
| shortlist-bge-jev | multi_confused | fixed | claude-haiku-4-5-003@multi_server_confused | `aws-knowledge.aws___read_documentation` | 0.630 | `aws-knowledge.aws___search_documentation` |
| shortlist-bge-jev | multi_confused | fixed | claude-haiku-4-5-008@multi_server_confused | `aws-knowledge.aws___get_regional_availability` | 0.760 | `aws-knowledge.aws___list_regions` |
| shortlist-bge-jev | multi_confused | fixed | claude-haiku-4-5-011@multi_server_confused | `aws-knowledge.aws___retrieve_skill` | 0.570 | `aws-knowledge.aws___search_documentation` |
| shortlist-bge-jev | multi_confused | fixed | claude-haiku-4-5-022@multi_server_confused | `context7.resolve-library-id` | 0.740 | `deepwiki.ask_wiki_question` |
| shortlist-bge-jev | multi_confused | fixed | claude-haiku-4-5-025@multi_server_confused | `context7.resolve-library-id` | 0.440 | `deepwiki.read_wiki_contents` |
| shortlist-bge-jev | multi_confused | fixed | claude-haiku-4-5-032@multi_server_confused | `gitmcp.search_generic_documentation` | 0.800 | `gitmcp.match_common_libs_owner_repo_mapping` |
| shortlist-bge-jev | multi_confused | fixed | claude-haiku-4-5-040@multi_server_confused | `huggingface.hf_fs` | 0.650 | `huggingface.hub_repo_search` |
| shortlist-bge-jev | multi_confused | fixed | claude-haiku-4-5-055@multi_server_confused | `svelte.get-documentation` | 1.000 | `svelte.list-sections` |
| shortlist-bge-jev | multi_confused | fixed | claude-sonnet-5-5-019@multi_server_confused | `context7.resolve-library-id` | 0.640 | `context7.query-docs` |
| shortlist-bge-jev | multi_confused | fixed | claude-sonnet-5-5-021@multi_server_confused | `context7.resolve-library-id` | 0.540 | `deepwiki.ask_wiki_question` |
| shortlist-bge-jev | multi_confused | fixed | claude-sonnet-5-5-022@multi_server_confused | `context7.resolve-library-id` | 0.360 | `deepwiki.ask_wiki_question` |
| shortlist-bge-jev | multi_confused | fixed | claude-sonnet-5-5-056@multi_server_confused | `svelte.get-documentation` | 0.990 | `svelte.list-sections` |
| shortlist-bge-jev | multi_confused | fixed | claude-sonnet-5-5-069@multi_server_confused | *abstained* | 0.240 | `svelte.svelte-autofixer` |
| shortlist-bge-jev | multi_confused | fixed | cursor-bot-003@multi_server_confused | `astro-docs.search_astro_docs` | 0.540 | *abstain* |
| shortlist-bge-jev | multi_confused | fixed | cursor-bot-007@multi_server_confused | `astro-docs.search_astro_docs` | 0.680 | *abstain* |
| shortlist-bge-jev | multi_confused | fixed | cursor-bot-022@multi_server_confused | `cloudflare-docs.search_cloudflare_documentation` | 0.520 | *abstain* |
| shortlist-bge-jev | multi_confused | fixed | cursor-bot-049@multi_server_confused | `huggingface.hf_whoami` | 0.650 | *abstain* |
| shortlist-bge-jev | multi_confused | fixed | cursor-bot-050@multi_server_confused | `huggingface.hf_whoami` | 0.310 | *abstain* |
| shortlist-bge-jev | multi_confused | fixed | cursor-bot-053@multi_server_confused | `huggingface.hf_whoami` | 0.540 | *abstain* |
| shortlist-bge-jev | multi_confused | fixed | cursor-bot-060@multi_server_confused | `kiwi.search-flight` | 0.570 | *abstain* |
| shortlist-bge-jev | multi_confused | fixed | gpt-5.5-019@multi_server_confused | `context7.resolve-library-id` | 0.660 | `context7.query-docs` |
| shortlist-bge-jev | multi_confused | fixed | gpt-5.5-020@multi_server_confused | `context7.resolve-library-id` | 0.750 | `context7.query-docs` |
| shortlist-bge-jev | multi_confused | fixed | gpt-5.5-021@multi_server_confused | `context7.resolve-library-id` | 0.560 | `deepwiki.ask_wiki_question` |
| shortlist-bge-jev | multi_confused | fixed | gpt-5.6-luna-023@multi_server_confused | `deepwiki.read_wiki_structure` | 0.590 | `deepwiki.read_wiki_contents` |
| shortlist-bge-jev | multi_confused | fixed | gpt-5.6-luna-054@multi_server_confused | `microsoft-learn.microsoft_docs_search` | 0.900 | `microsoft-learn.microsoft_docs_fetch` |
| shortlist-bge-jev | multi_confused | fixed | gpt-5.6-luna-057@multi_server_confused | `svelte.get-documentation` | 0.980 | `svelte.list-sections` |
| shortlist-bge-jev | multi_confused | fixed | gpt-5.6-sol-020@multi_server_confused | `context7.resolve-library-id` | 0.600 | `context7.query-docs` |
| shortlist-bge-jev | multi_confused | fixed | gpt-5.6-sol-022@multi_server_confused | `context7.resolve-library-id` | 0.600 | `deepwiki.ask_wiki_question` |
| shortlist-bge-jev | multi_confused | fixed | gpt-5.6-terra-021@multi_server_confused | `context7.resolve-library-id` | 0.530 | `deepwiki.ask_wiki_question` |
| shortlist-bge-jev | multi_confused | fixed | gpt-5.6-terra-022@multi_server_confused | `gitmcp.match_common_libs_owner_repo_mapping` | 0.610 | `deepwiki.ask_wiki_question` |
| shortlist-bge-jev | multi_confused | fixed | gpt-5.6-terra-024@multi_server_confused | `deepwiki.read_wiki_structure` | 0.530 | `deepwiki.read_wiki_contents` |
| shortlist-bge-jev | multi_confused | fixed | gpt-6-astra-020@multi_server_confused | `context7.resolve-library-id` | 0.810 | `context7.query-docs` |
| shortlist-bge-jev | multi_server | fixed | claude-fable-5-1-018@multi_server | `context7.query-docs` | 0.640 | `context7.resolve-library-id` |
| shortlist-bge-jev | multi_server | fixed | claude-fable-5-1-019@multi_server | `context7.resolve-library-id` | 0.810 | `context7.query-docs` |
| shortlist-bge-jev | multi_server | fixed | claude-fable-5-1-023@multi_server | `gitmcp.fetch_generic_documentation` | 0.860 | `deepwiki.read_wiki_contents` |
| shortlist-bge-jev | multi_server | fixed | claude-fable-5-1-064@multi_server | `huggingface.hf_whoami` | 0.730 | *abstain* |
| shortlist-bge-jev | multi_server | fixed | claude-haiku-4-5-003@multi_server | `aws-knowledge.aws___read_documentation` | 0.720 | `aws-knowledge.aws___search_documentation` |
| shortlist-bge-jev | multi_server | fixed | claude-haiku-4-5-008@multi_server | `aws-knowledge.aws___get_regional_availability` | 0.610 | `aws-knowledge.aws___list_regions` |
| shortlist-bge-jev | multi_server | fixed | claude-haiku-4-5-022@multi_server | *abstained* | 0.120 | `deepwiki.ask_wiki_question` |
| shortlist-bge-jev | multi_server | fixed | claude-haiku-4-5-023@multi_server | `gitmcp.match_common_libs_owner_repo_mapping` | 0.640 | `deepwiki.read_wiki_structure` |
| shortlist-bge-jev | multi_server | fixed | claude-haiku-4-5-040@multi_server | `huggingface.hf_fs` | 0.780 | `huggingface.hub_repo_search` |
| shortlist-bge-jev | multi_server | fixed | claude-haiku-4-5-054@multi_server | `microsoft-learn.microsoft_docs_fetch` | 0.610 | `microsoft-learn.microsoft_docs_search` |
| shortlist-bge-jev | multi_server | fixed | claude-haiku-4-5-055@multi_server | `svelte.get-documentation` | 1.000 | `svelte.list-sections` |
| shortlist-bge-jev | multi_server | fixed | claude-haiku-4-5-067@multi_server | `huggingface.hf_whoami` | 0.560 | *abstain* |
| shortlist-bge-jev | multi_server | fixed | claude-haiku-4-5-068@multi_server | `cloudflare-docs.search_cloudflare_documentation` | 0.620 | *abstain* |
| shortlist-bge-jev | multi_server | fixed | claude-opus-5-5-017@multi_server | `context7.query-docs` | 0.970 | `context7.resolve-library-id` |
| shortlist-bge-jev | multi_server | fixed | claude-opus-5-5-019@multi_server | `context7.resolve-library-id` | 0.470 | `context7.query-docs` |
| shortlist-bge-jev | multi_server | fixed | claude-opus-5-5-020@multi_server | `context7.resolve-library-id` | 0.520 | `context7.query-docs` |
| shortlist-bge-jev | multi_server | fixed | claude-opus-5-5-021@multi_server | `gitmcp.match_common_libs_owner_repo_mapping` | 0.740 | `deepwiki.ask_wiki_question` |
| shortlist-bge-jev | multi_server | fixed | claude-opus-5-5-036@multi_server | *abstained* | 0.050 | `gitmcp.fetch_generic_url_content` |
| shortlist-bge-jev | multi_server | fixed | claude-opus-5-5-062@multi_server | `svelte.get-documentation` | 0.610 | `svelte.svelte-autofixer` |
| shortlist-bge-jev | multi_server | fixed | claude-opus-5-5-064@multi_server | `huggingface.hf_whoami` | 0.590 | *abstain* |
| shortlist-bge-jev | multi_server | fixed | claude-sonnet-5-5-019@multi_server | `context7.resolve-library-id` | 0.570 | `context7.query-docs` |
| shortlist-bge-jev | multi_server | fixed | claude-sonnet-5-5-021@multi_server | `gitmcp.match_common_libs_owner_repo_mapping` | 0.450 | `deepwiki.ask_wiki_question` |
| shortlist-bge-jev | multi_server | fixed | claude-sonnet-5-5-056@multi_server | `svelte.get-documentation` | 0.990 | `svelte.list-sections` |
| shortlist-bge-jev | multi_server | fixed | claude-sonnet-5-5-066@multi_server | `huggingface.hf_whoami` | 0.730 | *abstain* |
| shortlist-bge-jev | multi_server | fixed | claude-sonnet-5-5-069@multi_server | `svelte.get-documentation` | 0.390 | `svelte.svelte-autofixer` |
| shortlist-bge-jev | multi_server | fixed | cursor-bot-007@multi_server | `astro-docs.search_astro_docs` | 0.920 | *abstain* |
| shortlist-bge-jev | multi_server | fixed | cursor-bot-020@multi_server | `cloudflare-docs.search_cloudflare_documentation` | 0.690 | *abstain* |
| shortlist-bge-jev | multi_server | fixed | cursor-bot-034@multi_server | `deepwiki.read_wiki_contents` | 0.410 | *abstain* |
| shortlist-bge-jev | multi_server | fixed | cursor-bot-038@multi_server | `gitmcp.match_common_libs_owner_repo_mapping` | 0.610 | *abstain* |
| shortlist-bge-jev | multi_server | fixed | cursor-bot-049@multi_server | `huggingface.hf_whoami` | 0.580 | *abstain* |
| shortlist-bge-jev | multi_server | fixed | cursor-bot-050@multi_server | `huggingface.hf_whoami` | 0.400 | *abstain* |
| shortlist-bge-jev | multi_server | fixed | gpt-5.5-019@multi_server | `context7.resolve-library-id` | 0.670 | `context7.query-docs` |
| shortlist-bge-jev | multi_server | fixed | gpt-5.5-020@multi_server | `gitmcp.search_generic_documentation` | 0.270 | `context7.query-docs` |
| shortlist-bge-jev | multi_server | fixed | gpt-5.5-021@multi_server | `gitmcp.match_common_libs_owner_repo_mapping` | 0.640 | `deepwiki.ask_wiki_question` |
| shortlist-bge-jev | multi_server | fixed | gpt-5.5-022@multi_server | `gitmcp.match_common_libs_owner_repo_mapping` | 0.680 | `deepwiki.ask_wiki_question` |
| shortlist-bge-jev | multi_server | fixed | gpt-5.5-034@multi_server | `gitmcp.search_generic_documentation` | 0.630 | `gitmcp.search_generic_code` |
| shortlist-bge-jev | multi_server | fixed | gpt-5.6-luna-023@multi_server | `deepwiki.read_wiki_structure` | 0.910 | `deepwiki.read_wiki_contents` |
| shortlist-bge-jev | multi_server | fixed | gpt-5.6-luna-054@multi_server | `microsoft-learn.microsoft_docs_search` | 0.760 | `microsoft-learn.microsoft_docs_fetch` |
| shortlist-bge-jev | multi_server | fixed | gpt-5.6-luna-057@multi_server | `svelte.get-documentation` | 1.000 | `svelte.list-sections` |
| shortlist-bge-jev | multi_server | fixed | gpt-5.6-luna-066@multi_server | `huggingface.hf_whoami` | 0.600 | *abstain* |
| shortlist-bge-jev | multi_server | fixed | gpt-5.6-luna-070@multi_server | `gitmcp.fetch_generic_documentation` | 0.470 | *abstain* |
| shortlist-bge-jev | multi_server | fixed | gpt-5.6-sol-004@multi_server | *abstained* | 0.130 | `aws-knowledge.aws___read_documentation` |
| shortlist-bge-jev | multi_server | fixed | gpt-5.6-sol-020@multi_server | `gitmcp.search_generic_documentation` | 0.310 | `context7.query-docs` |
| shortlist-bge-jev | multi_server | fixed | gpt-5.6-sol-031@multi_server | `gitmcp.match_common_libs_owner_repo_mapping` | 0.390 | `gitmcp.search_generic_documentation` |
| shortlist-bge-jev | multi_server | fixed | gpt-5.6-sol-066@multi_server | `huggingface.hf_whoami` | 0.550 | *abstain* |
| shortlist-bge-jev | multi_server | fixed | gpt-5.6-terra-019@multi_server | `context7.resolve-library-id` | 0.570 | `context7.query-docs` |
| shortlist-bge-jev | multi_server | fixed | gpt-5.6-terra-021@multi_server | *abstained* | 0.300 | `deepwiki.ask_wiki_question` |
| shortlist-bge-jev | multi_server | fixed | gpt-5.6-terra-024@multi_server | `deepwiki.read_wiki_structure` | 0.760 | `deepwiki.read_wiki_contents` |
| shortlist-bge-jev | multi_server | fixed | gpt-5.6-terra-032@multi_server | `gitmcp.match_common_libs_owner_repo_mapping` | 0.750 | `gitmcp.search_generic_documentation` |
| shortlist-bge-jev | multi_server | fixed | gpt-6-astra-004@multi_server | `gitmcp.fetch_generic_url_content` | 0.460 | `aws-knowledge.aws___read_documentation` |
| shortlist-bge-jev | multi_server | fixed | gpt-6-astra-020@multi_server | `context7.resolve-library-id` | 0.720 | `context7.query-docs` |
| shortlist-bge-jev | multi_server | fixed | gpt-6-astra-034@multi_server | `gitmcp.match_common_libs_owner_repo_mapping` | 0.760 | `gitmcp.search_generic_code` |
| shortlist-bge-jev | multi_server | fixed | gpt-6-astra-058@multi_server | `svelte.get-documentation` | 0.630 | `svelte.list-sections` |
| shortlist-bge-jev | multi_server | fixed | gpt-6-astra-064@multi_server | `huggingface.hf_whoami` | 0.570 | *abstain* |
