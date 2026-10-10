# ToolDiscoveryBench — test-luna-flat

## Accuracy

| router | suite | tools | n | no-tool | err | **acc** | top-1 | lenient | top-3 | server@1 | abstain ✓ | false abstain | refused |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| or-luna-flat | multi_confused | fixed | 393 | 87 | 0 | **80.9%** | 76.5% | 93.1% | 98.0% | 98.0% | 96.6% | 0.0% | 0.0% |
| or-luna-flat | multi_server | fixed | 618 | 132 | 0 | **89.8%** | 87.7% | 95.7% | 95.7% | 98.1% | 97.7% | 1.2% | 0.0% |
| or-luna-flat | one_server | fixed | 618 | 132 | 0 | **90.3%** | 88.9% | 96.9% | 99.4% | 99.4% | 95.5% | 0.6% | 0.0% |

*acc: answerable questions need the gold tool first, no-tool questions need an abstain. top-1 / lenient / top-3 / server@1 are over answerable questions only; lenient also accepts tools labelled acceptable. abstain ✓: share of no-tool questions where the router abstained. false abstain: share of answerable ones where it did. refused: share of questions where the backend refused a per-server sub-question (scored as P = 0 for that server, which can flatter accuracy).*

## Speed, cost and calibration

| router | suite | tools | p50 ms | p95 ms | calls | in-tok | $/1k q | ECE | Brier | conf ✓ | conf ✗ |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| or-luna-flat | multi_confused | fixed | 110 | 399 | 1.000 | 1,021 | 0.102 | 0.141 | 0.166 | 0.909 | 0.743 |
| or-luna-flat | multi_server | fixed | 108 | 252 | 1.000 | 920 | 0.092 | 0.075 | 0.099 | 0.903 | 0.743 |
| or-luna-flat | one_server | fixed | 106 | 167 | 1.000 | 389 | 0.039 | 0.069 | 0.099 | 0.936 | 0.830 |

*Calibration columns are filled only for calibrated routers (Jev). conf ✓ / ✗ is the mean top-1 probability when right vs wrong; a big gap lets you set an abstain threshold.*

## Top-1 with 95% bootstrap confidence intervals

| router | suite | tools | n | top-1 | 95% CI | test n | test top-1 | test 95% CI |
|---|---|---:|---:|---:|---|---:|---:|---|
| or-luna-flat | multi_confused | fixed | 102 | 76.5% | 68.6%–84.3% | 102 | 76.5% | 68.6%–84.3% |
| or-luna-flat | multi_server | fixed | 162 | 87.7% | 82.1%–92.0% | 162 | 87.7% | 82.1%–92.0% |
| or-luna-flat | one_server | fixed | 162 | 88.9% | 84.0%–93.2% | 162 | 88.9% | 84.0%–93.2% |

*Answerable questions only; 1000 seeded resamples over questions (repeats averaged per question). *test* is the frozen held-out split (`data/golden/splits/test_qids.txt`); publish numbers from it with repeats ≥ 3.*

## Accuracy by question tag (all suites and sizes pooled)

| router | confusable | generator:claude | generator:cursor-bot | generator:openai | judges_split | multi_server | multi_server_confused | needs_human_review | no_tool | one_server | relabelled | rewritten | split:test |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| or-luna-flat | 81.9% | 78.4% | 98.8% | 92.3% | 30.6% | 89.8% | 80.9% | 98.8% | 96.6% | 90.3% | 29.6% | 100.0% | 87.8% |

## Accuracy by question author (model family that wrote the question)

| router | claude | cursor | gpt |
|---|---:|---:|---:|
| or-luna-flat | 78.4% | 98.8% | 92.3% |

## Accuracy by question author (exact model)

| router | claude-fable-5-1 | claude-haiku-4-5 | claude-opus-5-5 | claude-sonnet-5-5 | cursor-bot | gpt-5.5 | gpt-5.6-luna | gpt-5.6-sol | gpt-5.6-terra | gpt-6-astra |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| or-luna-flat | 83.6% | 63.3% | 97.4% | 73.2% | 98.8% | 97.9% | 91.9% | 92.7% | 89.2% | 90.0% |

## Accuracy without possibly contaminated questions

| router | suite | tools | n | acc | top-1 | n kept | acc kept | top-1 kept |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| or-luna-flat | multi_confused | fixed | 393 | 80.9% | 76.5% | 303 | 79.2% | 72.2% |
| or-luna-flat | multi_server | fixed | 618 | 89.8% | 87.7% | 450 | 87.3% | 83.9% |
| or-luna-flat | one_server | fixed | 618 | 90.3% | 88.9% | 450 | 88.7% | 86.6% |

*kept: questions not written by `gpt-5.6-sol`, `claude-opus-5-5`, `gpt-5.6-luna` (judges of the labels, or the same model line as a router under test).*

## Misses (repeat 0, first 200)

| router | suite | tools | item | picked | p | gold |
|---|---|---:|---|---|---:|---|
| or-luna-flat | multi_confused | fixed | claude-fable-5-1-004@multi_server_confused | `aws-knowledge.aws___search_documentation` | 0.960 | `aws-knowledge.aws___read_documentation` |
| or-luna-flat | multi_confused | fixed | claude-fable-5-1-020@multi_server_confused | `context7.resolve-library-id` | 0.940 | `context7.query-docs` |
| or-luna-flat | multi_confused | fixed | claude-fable-5-1-022@multi_server_confused | `context7.resolve-library-id` | 0.810 | `deepwiki.ask_wiki_question` |
| or-luna-flat | multi_confused | fixed | claude-fable-5-1-055@multi_server_confused | `svelte.get-documentation` | 0.980 | `svelte.list-sections` |
| or-luna-flat | multi_confused | fixed | claude-haiku-4-5-002@multi_server_confused | `context7.query-docs` | 0.590 | *abstain* |
| or-luna-flat | multi_confused | fixed | claude-haiku-4-5-010@multi_server_confused | `aws-knowledge.aws___search_documentation` | 0.980 | `aws-knowledge.aws___get_regional_availability` |
| or-luna-flat | multi_confused | fixed | claude-haiku-4-5-019@multi_server_confused | `context7.query-docs` | 0.610 | `context7.resolve-library-id` |
| or-luna-flat | multi_confused | fixed | claude-haiku-4-5-030@multi_server_confused | `gitmcp.fetch_generic_documentation` | 0.660 | `gitmcp.match_common_libs_owner_repo_mapping` |
| or-luna-flat | multi_confused | fixed | claude-haiku-4-5-031@multi_server_confused | `gitmcp.search_generic_code` | 0.850 | `gitmcp.search_generic_documentation` |
| or-luna-flat | multi_confused | fixed | claude-haiku-4-5-033@multi_server_confused | `gitmcp.search_generic_code` | 0.920 | `gitmcp.match_common_libs_owner_repo_mapping` |
| or-luna-flat | multi_confused | fixed | claude-haiku-4-5-053@multi_server_confused | `microsoft-learn.microsoft_docs_fetch` | 0.730 | `microsoft-learn.microsoft_docs_search` |
| or-luna-flat | multi_confused | fixed | claude-opus-5-5-003@multi_server_confused | `aws-knowledge.aws___search_documentation` | 0.750 | `aws-knowledge.aws___read_documentation` |
| or-luna-flat | multi_confused | fixed | claude-sonnet-5-5-020@multi_server_confused | `gitmcp.search_generic_code` | 0.480 | `context7.query-docs` |
| or-luna-flat | multi_confused | fixed | claude-sonnet-5-5-023@multi_server_confused | `deepwiki.read_wiki_structure` | 0.720 | `deepwiki.read_wiki_contents` |
| or-luna-flat | multi_confused | fixed | claude-sonnet-5-5-024@multi_server_confused | `deepwiki.read_wiki_structure` | 0.350 | `deepwiki.read_wiki_contents` |
| or-luna-flat | multi_confused | fixed | claude-sonnet-5-5-052@multi_server_confused | `microsoft-learn.microsoft_docs_search` | 0.500 | `microsoft-learn.microsoft_code_sample_search` |
| or-luna-flat | multi_confused | fixed | claude-sonnet-5-5-055@multi_server_confused | `svelte.get-documentation` | 0.960 | `svelte.list-sections` |
| or-luna-flat | multi_confused | fixed | gpt-5.5-026@multi_server_confused | `deepwiki.read_wiki_contents` | 0.650 | `deepwiki.read_wiki_structure` |
| or-luna-flat | multi_confused | fixed | gpt-5.6-luna-009@multi_server_confused | `aws-knowledge.aws___search_documentation` | 0.620 | `aws-knowledge.aws___get_regional_availability` |
| or-luna-flat | multi_confused | fixed | gpt-5.6-luna-058@multi_server_confused | `svelte.list-sections` | 0.990 | `svelte.get-documentation` |
| or-luna-flat | multi_confused | fixed | gpt-5.6-sol-042@multi_server_confused | `huggingface.hub_repo_search` | 0.520 | `huggingface.hub_repo_details` |
| or-luna-flat | multi_confused | fixed | gpt-5.6-terra-020@multi_server_confused | `context7.resolve-library-id` | 0.830 | `context7.query-docs` |
| or-luna-flat | multi_confused | fixed | gpt-5.6-terra-040@multi_server_confused | `huggingface.hf_fs` | 0.920 | `huggingface.hub_repo_search` |
| or-luna-flat | multi_confused | fixed | gpt-5.6-terra-052@multi_server_confused | `microsoft-learn.microsoft_docs_search` | 0.660 | `microsoft-learn.microsoft_code_sample_search` |
| or-luna-flat | multi_confused | fixed | gpt-6-astra-032@multi_server_confused | `gitmcp.match_common_libs_owner_repo_mapping` | 0.650 | `gitmcp.search_generic_documentation` |
| or-luna-flat | multi_server | fixed | claude-fable-5-1-004@multi_server | `aws-knowledge.aws___search_documentation` | 0.590 | `aws-knowledge.aws___read_documentation` |
| or-luna-flat | multi_server | fixed | claude-fable-5-1-020@multi_server | `context7.resolve-library-id` | 0.420 | `context7.query-docs` |
| or-luna-flat | multi_server | fixed | claude-fable-5-1-055@multi_server | `svelte.get-documentation` | 1.000 | `svelte.list-sections` |
| or-luna-flat | multi_server | fixed | claude-fable-5-1-058@multi_server | `svelte.get-documentation` | 0.990 | `svelte.list-sections` |
| or-luna-flat | multi_server | fixed | claude-haiku-4-5-010@multi_server | `aws-knowledge.aws___search_documentation` | 0.710 | `aws-knowledge.aws___get_regional_availability` |
| or-luna-flat | multi_server | fixed | claude-haiku-4-5-030@multi_server | `gitmcp.fetch_generic_documentation` | 0.970 | `gitmcp.match_common_libs_owner_repo_mapping` |
| or-luna-flat | multi_server | fixed | claude-haiku-4-5-031@multi_server | `gitmcp.fetch_generic_documentation` | 0.950 | `gitmcp.search_generic_documentation` |
| or-luna-flat | multi_server | fixed | claude-haiku-4-5-033@multi_server | `gitmcp.search_generic_code` | 0.980 | `gitmcp.match_common_libs_owner_repo_mapping` |
| or-luna-flat | multi_server | fixed | claude-haiku-4-5-034@multi_server | `gitmcp.search_generic_code` | 0.450 | `gitmcp.match_common_libs_owner_repo_mapping` |
| or-luna-flat | multi_server | fixed | claude-haiku-4-5-036@multi_server | *abstained* | 0.290 | `gitmcp.fetch_generic_url_content` |
| or-luna-flat | multi_server | fixed | claude-haiku-4-5-053@multi_server | `microsoft-learn.microsoft_docs_fetch` | 0.860 | `microsoft-learn.microsoft_docs_search` |
| or-luna-flat | multi_server | fixed | claude-haiku-4-5-056@multi_server | `svelte.get-documentation` | 0.660 | `svelte.list-sections` |
| or-luna-flat | multi_server | fixed | claude-sonnet-5-5-052@multi_server | `microsoft-learn.microsoft_docs_search` | 0.510 | `microsoft-learn.microsoft_code_sample_search` |
| or-luna-flat | multi_server | fixed | claude-sonnet-5-5-055@multi_server | `svelte.get-documentation` | 0.980 | `svelte.list-sections` |
| or-luna-flat | multi_server | fixed | claude-sonnet-5-5-070@multi_server | `huggingface.hf_whoami` | 0.530 | *abstain* |
| or-luna-flat | multi_server | fixed | gpt-5.6-luna-009@multi_server | `aws-knowledge.aws___search_documentation` | 0.550 | `aws-knowledge.aws___get_regional_availability` |
| or-luna-flat | multi_server | fixed | gpt-5.6-luna-040@multi_server | `huggingface.hf_fs` | 0.590 | `huggingface.hub_repo_search` |
| or-luna-flat | multi_server | fixed | gpt-5.6-terra-020@multi_server | `context7.resolve-library-id` | 0.970 | `context7.query-docs` |
| or-luna-flat | multi_server | fixed | gpt-5.6-terra-030@multi_server | `deepwiki.read_wiki_structure` | 0.980 | `gitmcp.fetch_generic_documentation` |
| or-luna-flat | multi_server | fixed | gpt-5.6-terra-060@multi_server | *abstained* | 0.230 | `svelte.playground-link` |
| or-luna-flat | multi_server | fixed | gpt-6-astra-032@multi_server | `gitmcp.match_common_libs_owner_repo_mapping` | 0.430 | `gitmcp.search_generic_documentation` |
| or-luna-flat | one_server | fixed | claude-fable-5-1-004@one_server | `aws-knowledge.aws___search_documentation` | 0.760 | `aws-knowledge.aws___read_documentation` |
| or-luna-flat | one_server | fixed | claude-fable-5-1-020@one_server | `context7.resolve-library-id` | 1.000 | `context7.query-docs` |
| or-luna-flat | one_server | fixed | claude-fable-5-1-024@one_server | `deepwiki.read_wiki_structure` | 0.710 | `deepwiki.read_wiki_contents` |
| or-luna-flat | one_server | fixed | claude-fable-5-1-055@one_server | `svelte.get-documentation` | 0.980 | `svelte.list-sections` |
| or-luna-flat | one_server | fixed | claude-haiku-4-5-002@one_server | `astro-docs.search_astro_docs` | 0.930 | *abstain* |
| or-luna-flat | one_server | fixed | claude-haiku-4-5-010@one_server | `aws-knowledge.aws___search_documentation` | 0.650 | `aws-knowledge.aws___get_regional_availability` |
| or-luna-flat | one_server | fixed | claude-haiku-4-5-030@one_server | `gitmcp.fetch_generic_documentation` | 0.760 | `gitmcp.match_common_libs_owner_repo_mapping` |
| or-luna-flat | one_server | fixed | claude-haiku-4-5-033@one_server | `gitmcp.search_generic_code` | 0.840 | `gitmcp.match_common_libs_owner_repo_mapping` |
| or-luna-flat | one_server | fixed | claude-haiku-4-5-036@one_server | *abstained* | 0.290 | `gitmcp.fetch_generic_url_content` |
| or-luna-flat | one_server | fixed | claude-haiku-4-5-053@one_server | `microsoft-learn.microsoft_docs_fetch` | 0.980 | `microsoft-learn.microsoft_docs_search` |
| or-luna-flat | one_server | fixed | claude-haiku-4-5-056@one_server | `svelte.get-documentation` | 0.990 | `svelte.list-sections` |
| or-luna-flat | one_server | fixed | claude-sonnet-5-5-012@one_server | `aws-knowledge.aws___search_documentation` | 0.540 | `aws-knowledge.aws___retrieve_skill` |
| or-luna-flat | one_server | fixed | claude-sonnet-5-5-024@one_server | `deepwiki.read_wiki_structure` | 0.760 | `deepwiki.read_wiki_contents` |
| or-luna-flat | one_server | fixed | claude-sonnet-5-5-055@one_server | `svelte.get-documentation` | 1.000 | `svelte.list-sections` |
| or-luna-flat | one_server | fixed | cursor-bot-055@one_server | `huggingface.hf_whoami` | 0.660 | *abstain* |
| or-luna-flat | one_server | fixed | gpt-5.6-luna-058@one_server | `svelte.list-sections` | 0.880 | `svelte.get-documentation` |
| or-luna-flat | one_server | fixed | gpt-5.6-sol-019@one_server | `context7.resolve-library-id` | 0.930 | `context7.query-docs` |
| or-luna-flat | one_server | fixed | gpt-5.6-sol-024@one_server | `deepwiki.read_wiki_structure` | 0.960 | `deepwiki.read_wiki_contents` |
| or-luna-flat | one_server | fixed | gpt-5.6-terra-031@one_server | `gitmcp.fetch_generic_documentation` | 0.610 | `gitmcp.search_generic_documentation` |
| or-luna-flat | one_server | fixed | gpt-6-astra-032@one_server | `gitmcp.match_common_libs_owner_repo_mapping` | 0.890 | `gitmcp.search_generic_documentation` |
