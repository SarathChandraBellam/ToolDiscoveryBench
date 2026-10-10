# ToolDiscoveryBench — dev-escalate

## Accuracy

| router | suite | tools | n | no-tool | err | **acc** | top-1 | lenient | top-3 | server@1 | abstain ✓ | false abstain | refused |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| escalate-jev-sonnet | multi_confused | fixed | 274 | 52 | 0 | **91.2%** | 96.4% | 98.6% | 99.1% | 100.0% | 69.2% | 0.0% | 0.0% |
| escalate-jev-sonnet | multi_server | fixed | 490 | 103 | 0 | **92.9%** | 97.7% | 98.7% | 99.5% | 100.0% | 74.8% | 0.0% | 0.0% |
| escalate-jev-sonnet | one_server | fixed | 490 | 103 | 0 | **94.7%** | 98.2% | 99.0% | 99.7% | 100.0% | 81.6% | 0.0% | 0.0% |

*acc: answerable questions need the gold tool first, no-tool questions need an abstain. top-1 / lenient / top-3 / server@1 are over answerable questions only; lenient also accepts tools labelled acceptable. abstain ✓: share of no-tool questions where the router abstained. false abstain: share of answerable ones where it did. refused: share of questions where the backend refused a per-server sub-question (scored as P = 0 for that server, which can flatter accuracy).*

## Speed, cost and calibration

| router | suite | tools | p50 ms | p95 ms | calls | in-tok | $/1k q | ECE | Brier | conf ✓ | conf ✗ |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| escalate-jev-sonnet | multi_confused | fixed | 220 | 4,811 | 1.453 | 2,255 | 2.680 | – | – | – | – |
| escalate-jev-sonnet | multi_server | fixed | 196 | 4,191 | 1.345 | 1,863 | 1.947 | – | – | – | – |
| escalate-jev-sonnet | one_server | fixed | 191 | 4,210 | 1.310 | 928 | 1.223 | – | – | – | – |

*Calibration columns are filled only for calibrated routers (Jev). conf ✓ / ✗ is the mean top-1 probability when right vs wrong; a big gap lets you set an abstain threshold.*

## Escalation (cascade routers)

| router | suite | tools | escalated | primary $/1k q | fallback $/1k q | total $/1k q | top-1 kept | top-1 escalated |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| escalate-jev-sonnet | multi_confused | fixed | 45.3% | 0.057 | 2.623 | 2.680 | 97.8% | 94.0% |
| escalate-jev-sonnet | multi_server | fixed | 34.5% | 0.052 | 1.896 | 1.947 | 98.9% | 94.6% |
| escalate-jev-sonnet | one_server | fixed | 31.0% | 0.026 | 1.197 | 1.223 | 98.6% | 97.2% |

*escalated: share of questions where the primary's decision confidence was below `escalate_below` and the fallback answered. top-1 kept / escalated split answerable questions by whether they escalated.*

## Top-1 with 95% bootstrap confidence intervals

| router | suite | tools | n | top-1 | 95% CI | test n | test top-1 | test 95% CI |
|---|---|---:|---:|---:|---|---:|---:|---|
| escalate-jev-sonnet | multi_confused | fixed | 222 | 96.4% | 93.7%–98.6% | 0 | – | – |
| escalate-jev-sonnet | multi_server | fixed | 387 | 97.7% | 95.9%–99.0% | 0 | – | – |
| escalate-jev-sonnet | one_server | fixed | 387 | 98.2% | 96.6%–99.2% | 0 | – | – |

*Answerable questions only; 1000 seeded resamples over questions (repeats averaged per question). *test* is the frozen held-out split (`data/golden/splits/test_qids.txt`); publish numbers from it with repeats ≥ 3.*

## Accuracy by question tag (all suites and sizes pooled)

| router | confusable | generator:claude | generator:cursor-bot | generator:openai | judges_split | multi_server | multi_server_confused | needs_human_review | no_tool | one_server | relabelled | rewritten | split:dev |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| escalate-jev-sonnet | 94.8% | 95.3% | 75.0% | 96.2% | 68.4% | 92.9% | 91.2% | 75.0% | 76.4% | 94.7% | 63.9% | 100.0% | 93.2% |

## Accuracy by question author (model family that wrote the question)

| router | claude | cursor | gpt |
|---|---:|---:|---:|
| escalate-jev-sonnet | 95.3% | 75.0% | 96.2% |

## Accuracy by question author (exact model)

| router | claude-fable-5-1 | claude-haiku-4-5 | claude-opus-5-5 | claude-sonnet-5-5 | cursor-bot | gpt-5.5 | gpt-5.6-luna | gpt-5.6-sol | gpt-5.6-terra | gpt-6-astra |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| escalate-jev-sonnet | 97.1% | 91.1% | 98.4% | 94.9% | 75.0% | 99.2% | 88.9% | 96.9% | 98.0% | 97.8% |

## Accuracy without possibly contaminated questions

| router | suite | tools | n | acc | top-1 | n kept | acc kept | top-1 kept |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| escalate-jev-sonnet | multi_confused | fixed | 274 | 91.2% | 96.4% | 201 | 90.0% | 97.3% |
| escalate-jev-sonnet | multi_server | fixed | 490 | 92.9% | 97.7% | 341 | 91.8% | 97.6% |
| escalate-jev-sonnet | one_server | fixed | 490 | 94.7% | 98.2% | 341 | 94.7% | 98.8% |

*kept: questions not written by `gpt-5.6-sol`, `claude-opus-5-5`, `gpt-5.6-luna` (judges of the labels, or the same model line as a router under test).*

## Misses (repeat 0, first 200)

| router | suite | tools | item | picked | p | gold |
|---|---|---:|---|---|---:|---|
| escalate-jev-sonnet | multi_confused | fixed | claude-haiku-4-5-029@multi_server_confused | `gitmcp.fetch_generic_documentation` | 0.600 | `gitmcp.match_common_libs_owner_repo_mapping` |
| escalate-jev-sonnet | multi_confused | fixed | claude-haiku-4-5-032@multi_server_confused | `gitmcp.search_generic_documentation` | 0.550 | `gitmcp.match_common_libs_owner_repo_mapping` |
| escalate-jev-sonnet | multi_confused | fixed | claude-haiku-4-5-055@multi_server_confused | `svelte.get-documentation` | 1.000 | `svelte.list-sections` |
| escalate-jev-sonnet | multi_confused | fixed | claude-sonnet-5-5-056@multi_server_confused | `svelte.get-documentation` | 0.950 | `svelte.list-sections` |
| escalate-jev-sonnet | multi_confused | fixed | cursor-bot-003@multi_server_confused | `astro-docs.search_astro_docs` | 0.400 | *abstain* |
| escalate-jev-sonnet | multi_confused | fixed | cursor-bot-007@multi_server_confused | `astro-docs.search_astro_docs` | 0.850 | *abstain* |
| escalate-jev-sonnet | multi_confused | fixed | cursor-bot-012@multi_server_confused | `aws-knowledge.aws___search_documentation` | 0.500 | *abstain* |
| escalate-jev-sonnet | multi_confused | fixed | cursor-bot-017@multi_server_confused | `cloudflare-docs.search_cloudflare_documentation` | 0.600 | *abstain* |
| escalate-jev-sonnet | multi_confused | fixed | cursor-bot-018@multi_server_confused | `cloudflare-docs.search_cloudflare_documentation` | 0.600 | *abstain* |
| escalate-jev-sonnet | multi_confused | fixed | cursor-bot-019@multi_server_confused | `cloudflare-docs.search_cloudflare_documentation` | 0.400 | *abstain* |
| escalate-jev-sonnet | multi_confused | fixed | cursor-bot-020@multi_server_confused | `cloudflare-docs.search_cloudflare_documentation` | 0.600 | *abstain* |
| escalate-jev-sonnet | multi_confused | fixed | cursor-bot-021@multi_server_confused | `cloudflare-docs.search_cloudflare_documentation` | 0.600 | *abstain* |
| escalate-jev-sonnet | multi_confused | fixed | cursor-bot-022@multi_server_confused | `cloudflare-docs.search_cloudflare_documentation` | 0.550 | *abstain* |
| escalate-jev-sonnet | multi_confused | fixed | cursor-bot-023@multi_server_confused | `cloudflare-docs.search_cloudflare_documentation` | 0.600 | *abstain* |
| escalate-jev-sonnet | multi_confused | fixed | cursor-bot-049@multi_server_confused | `huggingface.hf_whoami` | 0.500 | *abstain* |
| escalate-jev-sonnet | multi_confused | fixed | cursor-bot-050@multi_server_confused | `huggingface.hf_fs` | 0.550 | *abstain* |
| escalate-jev-sonnet | multi_confused | fixed | cursor-bot-051@multi_server_confused | `huggingface.hf_whoami` | 0.500 | *abstain* |
| escalate-jev-sonnet | multi_confused | fixed | cursor-bot-065@multi_server_confused | `microsoft-learn.microsoft_code_sample_search` | 0.450 | *abstain* |
| escalate-jev-sonnet | multi_confused | fixed | cursor-bot-066@multi_server_confused | `microsoft-learn.microsoft_docs_search` | 0.400 | *abstain* |
| escalate-jev-sonnet | multi_confused | fixed | cursor-bot-072@multi_server_confused | `microsoft-learn.microsoft_code_sample_search` | 0.400 | *abstain* |
| escalate-jev-sonnet | multi_confused | fixed | gpt-5.6-luna-023@multi_server_confused | `deepwiki.read_wiki_structure` | 0.550 | `deepwiki.read_wiki_contents` |
| escalate-jev-sonnet | multi_confused | fixed | gpt-5.6-luna-024@multi_server_confused | `deepwiki.read_wiki_structure` | 0.600 | `deepwiki.read_wiki_contents` |
| escalate-jev-sonnet | multi_confused | fixed | gpt-5.6-luna-054@multi_server_confused | `microsoft-learn.microsoft_docs_search` | 0.620 | `microsoft-learn.microsoft_docs_fetch` |
| escalate-jev-sonnet | multi_confused | fixed | gpt-5.6-luna-057@multi_server_confused | `svelte.get-documentation` | 0.980 | `svelte.list-sections` |
| escalate-jev-sonnet | multi_server | fixed | claude-fable-5-1-064@multi_server | `huggingface.hf_whoami` | 0.500 | *abstain* |
| escalate-jev-sonnet | multi_server | fixed | claude-fable-5-1-070@multi_server | `svelte.svelte-autofixer` | 0.550 | *abstain* |
| escalate-jev-sonnet | multi_server | fixed | claude-haiku-4-5-029@multi_server | `gitmcp.fetch_generic_documentation` | 0.800 | `gitmcp.match_common_libs_owner_repo_mapping` |
| escalate-jev-sonnet | multi_server | fixed | claude-haiku-4-5-032@multi_server | `gitmcp.search_generic_documentation` | 0.500 | `gitmcp.match_common_libs_owner_repo_mapping` |
| escalate-jev-sonnet | multi_server | fixed | claude-haiku-4-5-055@multi_server | `svelte.get-documentation` | 1.000 | `svelte.list-sections` |
| escalate-jev-sonnet | multi_server | fixed | claude-haiku-4-5-067@multi_server | `huggingface.hf_fs` | 0.500 | *abstain* |
| escalate-jev-sonnet | multi_server | fixed | claude-haiku-4-5-068@multi_server | `cloudflare-docs.search_cloudflare_documentation` | 0.600 | *abstain* |
| escalate-jev-sonnet | multi_server | fixed | claude-opus-5-5-064@multi_server | `huggingface.hf_whoami` | 0.550 | *abstain* |
| escalate-jev-sonnet | multi_server | fixed | claude-sonnet-5-5-056@multi_server | `svelte.get-documentation` | 0.990 | `svelte.list-sections` |
| escalate-jev-sonnet | multi_server | fixed | claude-sonnet-5-5-066@multi_server | `huggingface.hf_whoami` | 0.400 | *abstain* |
| escalate-jev-sonnet | multi_server | fixed | claude-sonnet-5-5-067@multi_server | `cloudflare-docs.search_cloudflare_documentation` | 0.800 | *abstain* |
| escalate-jev-sonnet | multi_server | fixed | cursor-bot-007@multi_server | `astro-docs.search_astro_docs` | 0.800 | *abstain* |
| escalate-jev-sonnet | multi_server | fixed | cursor-bot-010@multi_server | `aws-knowledge.aws___search_documentation` | 0.550 | *abstain* |
| escalate-jev-sonnet | multi_server | fixed | cursor-bot-016@multi_server | `aws-knowledge.aws___search_documentation` | 0.550 | *abstain* |
| escalate-jev-sonnet | multi_server | fixed | cursor-bot-017@multi_server | `cloudflare-docs.search_cloudflare_documentation` | 0.600 | *abstain* |
| escalate-jev-sonnet | multi_server | fixed | cursor-bot-018@multi_server | `cloudflare-docs.search_cloudflare_documentation` | 0.600 | *abstain* |
| escalate-jev-sonnet | multi_server | fixed | cursor-bot-020@multi_server | `cloudflare-docs.search_cloudflare_documentation` | 0.800 | *abstain* |
| escalate-jev-sonnet | multi_server | fixed | cursor-bot-021@multi_server | `cloudflare-docs.search_cloudflare_documentation` | 0.600 | *abstain* |
| escalate-jev-sonnet | multi_server | fixed | cursor-bot-028@multi_server | `context7.resolve-library-id` | 0.400 | *abstain* |
| escalate-jev-sonnet | multi_server | fixed | cursor-bot-049@multi_server | `huggingface.hf_whoami` | 0.600 | *abstain* |
| escalate-jev-sonnet | multi_server | fixed | cursor-bot-050@multi_server | `huggingface.hf_fs` | 0.550 | *abstain* |
| escalate-jev-sonnet | multi_server | fixed | cursor-bot-051@multi_server | `huggingface.hf_whoami` | 0.400 | *abstain* |
| escalate-jev-sonnet | multi_server | fixed | cursor-bot-067@multi_server | `microsoft-learn.microsoft_docs_search` | 0.600 | *abstain* |
| escalate-jev-sonnet | multi_server | fixed | cursor-bot-072@multi_server | `microsoft-learn.microsoft_docs_search` | 0.550 | *abstain* |
| escalate-jev-sonnet | multi_server | fixed | cursor-bot-077@multi_server | `svelte.list-sections` | 0.400 | *abstain* |
| escalate-jev-sonnet | multi_server | fixed | gpt-5.5-069@multi_server | `cloudflare-docs.search_cloudflare_documentation` | 0.800 | *abstain* |
| escalate-jev-sonnet | multi_server | fixed | gpt-5.6-luna-023@multi_server | `deepwiki.read_wiki_structure` | 0.620 | `deepwiki.read_wiki_contents` |
| escalate-jev-sonnet | multi_server | fixed | gpt-5.6-luna-054@multi_server | `microsoft-learn.microsoft_docs_search` | 0.720 | `microsoft-learn.microsoft_docs_fetch` |
| escalate-jev-sonnet | multi_server | fixed | gpt-5.6-luna-057@multi_server | `svelte.get-documentation` | 1.000 | `svelte.list-sections` |
| escalate-jev-sonnet | multi_server | fixed | gpt-5.6-luna-066@multi_server | `huggingface.hf_whoami` | 0.600 | *abstain* |
| escalate-jev-sonnet | multi_server | fixed | gpt-5.6-sol-065@multi_server | `cloudflare-docs.search_cloudflare_documentation` | 0.550 | *abstain* |
| escalate-jev-sonnet | multi_server | fixed | gpt-5.6-sol-066@multi_server | `huggingface.hf_whoami` | 0.600 | *abstain* |
| escalate-jev-sonnet | multi_server | fixed | gpt-5.6-terra-057@multi_server | `svelte.list-sections` | 0.800 | `svelte.get-documentation` |
| escalate-jev-sonnet | multi_server | fixed | gpt-6-astra-058@multi_server | `svelte.get-documentation` | 0.600 | `svelte.list-sections` |
| escalate-jev-sonnet | multi_server | fixed | gpt-6-astra-064@multi_server | `huggingface.hf_whoami` | 0.500 | *abstain* |
| escalate-jev-sonnet | one_server | fixed | claude-fable-5-1-064@one_server | `huggingface.hf_fs` | 0.500 | *abstain* |
| escalate-jev-sonnet | one_server | fixed | claude-haiku-4-5-055@one_server | `svelte.get-documentation` | 1.000 | `svelte.list-sections` |
| escalate-jev-sonnet | one_server | fixed | claude-haiku-4-5-067@one_server | `huggingface.hf_whoami` | 0.600 | *abstain* |
| escalate-jev-sonnet | one_server | fixed | claude-haiku-4-5-068@one_server | `cloudflare-docs.search_cloudflare_documentation` | 0.600 | *abstain* |
| escalate-jev-sonnet | one_server | fixed | claude-opus-5-5-064@one_server | `huggingface.hf_whoami` | 0.500 | *abstain* |
| escalate-jev-sonnet | one_server | fixed | claude-sonnet-5-5-056@one_server | `svelte.get-documentation` | 0.980 | `svelte.list-sections` |
| escalate-jev-sonnet | one_server | fixed | claude-sonnet-5-5-066@one_server | `huggingface.hf_whoami` | 0.500 | *abstain* |
| escalate-jev-sonnet | one_server | fixed | claude-sonnet-5-5-067@one_server | `cloudflare-docs.search_cloudflare_documentation` | 0.800 | *abstain* |
| escalate-jev-sonnet | one_server | fixed | cursor-bot-007@one_server | `astro-docs.search_astro_docs` | 0.600 | *abstain* |
| escalate-jev-sonnet | one_server | fixed | cursor-bot-016@one_server | `aws-knowledge.aws___search_documentation` | 0.500 | *abstain* |
| escalate-jev-sonnet | one_server | fixed | cursor-bot-020@one_server | `cloudflare-docs.search_cloudflare_documentation` | 0.800 | *abstain* |
| escalate-jev-sonnet | one_server | fixed | cursor-bot-022@one_server | `cloudflare-docs.search_cloudflare_documentation` | 0.400 | *abstain* |
| escalate-jev-sonnet | one_server | fixed | cursor-bot-023@one_server | `cloudflare-docs.search_cloudflare_documentation` | 0.600 | *abstain* |
| escalate-jev-sonnet | one_server | fixed | cursor-bot-028@one_server | `context7.resolve-library-id` | 0.600 | *abstain* |
| escalate-jev-sonnet | one_server | fixed | cursor-bot-049@one_server | `huggingface.hf_whoami` | 0.550 | *abstain* |
| escalate-jev-sonnet | one_server | fixed | cursor-bot-050@one_server | `huggingface.hf_fs` | 0.550 | *abstain* |
| escalate-jev-sonnet | one_server | fixed | cursor-bot-051@one_server | `huggingface.hf_whoami` | 0.400 | *abstain* |
| escalate-jev-sonnet | one_server | fixed | gpt-5.6-luna-023@one_server | `deepwiki.read_wiki_structure` | 0.990 | `deepwiki.read_wiki_contents` |
| escalate-jev-sonnet | one_server | fixed | gpt-5.6-luna-024@one_server | `deepwiki.read_wiki_structure` | 0.550 | `deepwiki.read_wiki_contents` |
| escalate-jev-sonnet | one_server | fixed | gpt-5.6-luna-054@one_server | `microsoft-learn.microsoft_docs_search` | 0.720 | `microsoft-learn.microsoft_docs_fetch` |
| escalate-jev-sonnet | one_server | fixed | gpt-5.6-luna-057@one_server | `svelte.get-documentation` | 0.980 | `svelte.list-sections` |
| escalate-jev-sonnet | one_server | fixed | gpt-5.6-luna-066@one_server | `huggingface.hf_whoami` | 0.620 | *abstain* |
| escalate-jev-sonnet | one_server | fixed | gpt-5.6-sol-065@one_server | `cloudflare-docs.search_cloudflare_documentation` | 0.600 | *abstain* |
| escalate-jev-sonnet | one_server | fixed | gpt-5.6-sol-066@one_server | `huggingface.hf_whoami` | 0.600 | *abstain* |
| escalate-jev-sonnet | one_server | fixed | gpt-5.6-terra-057@one_server | `svelte.list-sections` | 0.800 | `svelte.get-documentation` |
| escalate-jev-sonnet | one_server | fixed | gpt-6-astra-064@one_server | `huggingface.hf_whoami` | 0.600 | *abstain* |
