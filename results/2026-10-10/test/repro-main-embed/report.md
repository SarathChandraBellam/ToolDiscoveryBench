# ToolDiscoveryBench — repro-main-embed

## Accuracy

| router | suite | tools | n | no-tool | err | **acc** | top-1 | lenient | top-3 | server@1 | abstain ✓ | false abstain | refused |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| embed-bge-small | multi_confused | fixed | 393 | 87 | 0 | **47.3%** | 60.8% | 66.7% | 82.4% | 78.4% | 0.0% | 0.0% | 0.0% |
| embed-bge-small | multi_server | fixed | 618 | 132 | 0 | **51.5%** | 65.4% | 69.8% | 89.5% | 84.6% | 0.0% | 0.0% | 0.0% |
| embed-bge-small | one_server | fixed | 618 | 132 | 0 | **58.3%** | 74.1% | 81.5% | 98.1% | 100.0% | 0.0% | 0.0% | 0.0% |

*acc: answerable questions need the gold tool first, no-tool questions need an abstain. top-1 / lenient / top-3 / server@1 are over answerable questions only; lenient also accepts tools labelled acceptable. abstain ✓: share of no-tool questions where the router abstained. false abstain: share of answerable ones where it did. refused: share of questions where the backend refused a per-server sub-question (scored as P = 0 for that server, which can flatter accuracy).*

## Speed, cost and calibration

| router | suite | tools | p50 ms | p95 ms | calls | in-tok | $/1k q | ECE | Brier | conf ✓ | conf ✗ |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| embed-bge-small | multi_confused | fixed | 4 | 7 | 0.000 | – | – | – | – | – | – |
| embed-bge-small | multi_server | fixed | 9 | 30 | 0.000 | – | – | – | – | – | – |
| embed-bge-small | one_server | fixed | 16 | 33 | 0.000 | – | – | – | – | – | – |

*Calibration columns are filled only for calibrated routers (Jev). conf ✓ / ✗ is the mean top-1 probability when right vs wrong; a big gap lets you set an abstain threshold.*

## Top-1 with 95% bootstrap confidence intervals

| router | suite | tools | n | top-1 | 95% CI | test n | test top-1 | test 95% CI |
|---|---|---:|---:|---:|---|---:|---:|---|
| embed-bge-small | multi_confused | fixed | 102 | 60.8% | 51.0%–69.6% | 102 | 60.8% | 51.0%–69.6% |
| embed-bge-small | multi_server | fixed | 162 | 65.4% | 57.4%–72.8% | 162 | 65.4% | 57.4%–72.8% |
| embed-bge-small | one_server | fixed | 162 | 74.1% | 66.7%–80.9% | 162 | 74.1% | 66.7%–80.9% |

*Answerable questions only; 1000 seeded resamples over questions (repeats averaged per question). *test* is the frozen held-out split (`data/golden/splits/test_qids.txt`); publish numbers from it with repeats ≥ 3.*

## Accuracy by question tag (all suites and sizes pooled)

| router | confusable | generator:claude | generator:cursor-bot | generator:openai | judges_split | multi_server | multi_server_confused | needs_human_review | no_tool | one_server | relabelled | rewritten | split:test |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| embed-bge-small | 59.3% | 53.5% | 0.0% | 70.7% | 13.9% | 51.5% | 47.3% | 0.0% | 0.0% | 58.3% | 0.0% | 100.0% | 53.0% |

## Accuracy by question author (model family that wrote the question)

| router | claude | cursor | gpt |
|---|---:|---:|---:|
| embed-bge-small | 53.5% | 0.0% | 70.7% |

## Accuracy by question author (exact model)

| router | claude-fable-5-1 | claude-haiku-4-5 | claude-opus-5-5 | claude-sonnet-5-5 | cursor-bot | gpt-5.5 | gpt-5.6-luna | gpt-5.6-sol | gpt-5.6-terra | gpt-6-astra |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| embed-bge-small | 52.1% | 45.0% | 66.7% | 56.1% | 0.0% | 64.6% | 79.0% | 65.9% | 69.2% | 73.3% |

## Accuracy without possibly contaminated questions

| router | suite | tools | n | acc | top-1 | n kept | acc kept | top-1 kept |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| embed-bge-small | multi_confused | fixed | 393 | 47.3% | 60.8% | 303 | 38.6% | 54.2% |
| embed-bge-small | multi_server | fixed | 618 | 51.5% | 65.4% | 450 | 46.0% | 61.6% |
| embed-bge-small | one_server | fixed | 618 | 58.3% | 74.1% | 450 | 52.0% | 69.6% |

*kept: questions not written by `gpt-5.6-sol`, `claude-opus-5-5`, `gpt-5.6-luna` (judges of the labels, or the same model line as a router under test).*

## Misses (repeat 0, first 200)

| router | suite | tools | item | picked | p | gold |
|---|---|---:|---|---|---:|---|
| embed-bge-small | multi_confused | fixed | claude-fable-5-1-006@multi_server_confused | `aws-knowledge.aws___get_regional_availability` | 0.600 | `aws-knowledge.aws___search_documentation` |
| embed-bge-small | multi_confused | fixed | claude-fable-5-1-009@multi_server_confused | `aws-knowledge.aws___list_regions` | 0.643 | `aws-knowledge.aws___get_regional_availability` |
| embed-bge-small | multi_confused | fixed | claude-fable-5-1-020@multi_server_confused | `svelte.list-sections` | 0.578 | `context7.query-docs` |
| embed-bge-small | multi_confused | fixed | claude-fable-5-1-022@multi_server_confused | `context7.query-docs` | 0.629 | `deepwiki.ask_wiki_question` |
| embed-bge-small | multi_confused | fixed | claude-fable-5-1-024@multi_server_confused | `aws-knowledge.aws___read_documentation` | 0.675 | `deepwiki.read_wiki_contents` |
| embed-bge-small | multi_confused | fixed | claude-fable-5-1-026@multi_server_confused | `deepwiki.read_wiki_contents` | 0.701 | `deepwiki.read_wiki_structure` |
| embed-bge-small | multi_confused | fixed | claude-fable-5-1-030@multi_server_confused | `deepwiki.read_wiki_contents` | 0.667 | `gitmcp.fetch_generic_documentation` |
| embed-bge-small | multi_confused | fixed | claude-fable-5-1-041@multi_server_confused | `huggingface.hub_repo_search` | 0.770 | `huggingface.hub_repo_details` |
| embed-bge-small | multi_confused | fixed | claude-fable-5-1-055@multi_server_confused | `svelte.get-documentation` | 0.840 | `svelte.list-sections` |
| embed-bge-small | multi_confused | fixed | claude-fable-5-1-058@multi_server_confused | `svelte.get-documentation` | 0.693 | `svelte.list-sections` |
| embed-bge-small | multi_confused | fixed | claude-haiku-4-5-002@multi_server_confused | `astro-docs.search_astro_docs` | 0.592 | *abstain* |
| embed-bge-small | multi_confused | fixed | claude-haiku-4-5-019@multi_server_confused | `aws-knowledge.aws___search_documentation` | 0.696 | `context7.resolve-library-id` |
| embed-bge-small | multi_confused | fixed | claude-haiku-4-5-020@multi_server_confused | `aws-knowledge.aws___search_documentation` | 0.660 | `context7.resolve-library-id` |
| embed-bge-small | multi_confused | fixed | claude-haiku-4-5-030@multi_server_confused | `deepwiki.read_wiki_contents` | 0.742 | `gitmcp.match_common_libs_owner_repo_mapping` |
| embed-bge-small | multi_confused | fixed | claude-haiku-4-5-031@multi_server_confused | `huggingface.hub_repo_search` | 0.724 | `gitmcp.search_generic_documentation` |
| embed-bge-small | multi_confused | fixed | claude-haiku-4-5-033@multi_server_confused | `microsoft-learn.microsoft_code_sample_search` | 0.665 | `gitmcp.match_common_libs_owner_repo_mapping` |
| embed-bge-small | multi_confused | fixed | claude-haiku-4-5-034@multi_server_confused | `gitmcp.search_generic_code` | 0.637 | `gitmcp.match_common_libs_owner_repo_mapping` |
| embed-bge-small | multi_confused | fixed | claude-haiku-4-5-036@multi_server_confused | `aws-knowledge.aws___search_documentation` | 0.649 | `gitmcp.fetch_generic_url_content` |
| embed-bge-small | multi_confused | fixed | claude-haiku-4-5-050@multi_server_confused | `kiwi.feedback-to-devs` | 0.605 | `microsoft-learn.microsoft_docs_search` |
| embed-bge-small | multi_confused | fixed | claude-haiku-4-5-053@multi_server_confused | `microsoft-learn.microsoft_docs_fetch` | 0.792 | `microsoft-learn.microsoft_docs_search` |
| embed-bge-small | multi_confused | fixed | claude-haiku-4-5-056@multi_server_confused | `svelte.get-documentation` | 0.731 | `svelte.list-sections` |
| embed-bge-small | multi_confused | fixed | claude-opus-5-5-003@multi_server_confused | `aws-knowledge.aws___get_regional_availability` | 0.711 | `aws-knowledge.aws___read_documentation` |
| embed-bge-small | multi_confused | fixed | claude-opus-5-5-031@multi_server_confused | `deepwiki.read_wiki_contents` | 0.628 | `gitmcp.search_generic_documentation` |
| embed-bge-small | multi_confused | fixed | claude-sonnet-5-5-013@multi_server_confused | `aws-knowledge.aws___get_regional_availability` | 0.623 | `cloudflare-docs.search_cloudflare_documentation` |
| embed-bge-small | multi_confused | fixed | claude-sonnet-5-5-020@multi_server_confused | `context7.resolve-library-id` | 0.644 | `context7.query-docs` |
| embed-bge-small | multi_confused | fixed | claude-sonnet-5-5-040@multi_server_confused | `cloudflare-docs.search_cloudflare_documentation` | 0.575 | `huggingface.hub_repo_search` |
| embed-bge-small | multi_confused | fixed | claude-sonnet-5-5-055@multi_server_confused | `svelte.get-documentation` | 0.776 | `svelte.list-sections` |
| embed-bge-small | multi_confused | fixed | cursor-bot-001@multi_server_confused | `astro-docs.search_astro_docs` | 0.657 | *abstain* |
| embed-bge-small | multi_confused | fixed | cursor-bot-002@multi_server_confused | `astro-docs.search_astro_docs` | 0.589 | *abstain* |
| embed-bge-small | multi_confused | fixed | cursor-bot-004@multi_server_confused | `astro-docs.search_astro_docs` | 0.626 | *abstain* |
| embed-bge-small | multi_confused | fixed | cursor-bot-006@multi_server_confused | `astro-docs.search_astro_docs` | 0.572 | *abstain* |
| embed-bge-small | multi_confused | fixed | cursor-bot-011@multi_server_confused | `aws-knowledge.aws___retrieve_skill` | 0.527 | *abstain* |
| embed-bge-small | multi_confused | fixed | cursor-bot-013@multi_server_confused | `aws-knowledge.aws___get_regional_availability` | 0.589 | *abstain* |
| embed-bge-small | multi_confused | fixed | cursor-bot-014@multi_server_confused | `aws-knowledge.aws___get_regional_availability` | 0.598 | *abstain* |
| embed-bge-small | multi_confused | fixed | cursor-bot-024@multi_server_confused | `cloudflare-docs.search_cloudflare_documentation` | 0.642 | *abstain* |
| embed-bge-small | multi_confused | fixed | cursor-bot-026@multi_server_confused | `context7.resolve-library-id` | 0.575 | *abstain* |
| embed-bge-small | multi_confused | fixed | cursor-bot-033@multi_server_confused | `deepwiki.ask_wiki_question` | 0.722 | *abstain* |
| embed-bge-small | multi_confused | fixed | cursor-bot-036@multi_server_confused | `deepwiki.read_wiki_contents` | 0.623 | *abstain* |
| embed-bge-small | multi_confused | fixed | cursor-bot-043@multi_server_confused | `gitmcp.match_common_libs_owner_repo_mapping` | 0.574 | *abstain* |
| embed-bge-small | multi_confused | fixed | cursor-bot-047@multi_server_confused | `gitmcp.match_common_libs_owner_repo_mapping` | 0.616 | *abstain* |
| embed-bge-small | multi_confused | fixed | cursor-bot-048@multi_server_confused | `gitmcp.match_common_libs_owner_repo_mapping` | 0.647 | *abstain* |
| embed-bge-small | multi_confused | fixed | cursor-bot-054@multi_server_confused | `huggingface.hub_repo_search` | 0.539 | *abstain* |
| embed-bge-small | multi_confused | fixed | cursor-bot-055@multi_server_confused | `huggingface.hub_repo_details` | 0.614 | *abstain* |
| embed-bge-small | multi_confused | fixed | cursor-bot-056@multi_server_confused | `kiwi.feedback-to-devs` | 0.539 | *abstain* |
| embed-bge-small | multi_confused | fixed | cursor-bot-057@multi_server_confused | `kiwi.search-flight` | 0.682 | *abstain* |
| embed-bge-small | multi_confused | fixed | cursor-bot-058@multi_server_confused | `kiwi.feedback-to-devs` | 0.566 | *abstain* |
| embed-bge-small | multi_confused | fixed | cursor-bot-064@multi_server_confused | `kiwi.search-flight` | 0.621 | *abstain* |
| embed-bge-small | multi_confused | fixed | cursor-bot-068@multi_server_confused | `context7.query-docs` | 0.518 | *abstain* |
| embed-bge-small | multi_confused | fixed | cursor-bot-069@multi_server_confused | `aws-knowledge.aws___get_regional_availability` | 0.514 | *abstain* |
| embed-bge-small | multi_confused | fixed | cursor-bot-074@multi_server_confused | `svelte.playground-link` | 0.644 | *abstain* |
| embed-bge-small | multi_confused | fixed | cursor-bot-075@multi_server_confused | `svelte.svelte-autofixer` | 0.724 | *abstain* |
| embed-bge-small | multi_confused | fixed | cursor-bot-076@multi_server_confused | `svelte.svelte-autofixer` | 0.700 | *abstain* |
| embed-bge-small | multi_confused | fixed | cursor-bot-078@multi_server_confused | `svelte.svelte-autofixer` | 0.726 | *abstain* |
| embed-bge-small | multi_confused | fixed | cursor-bot-079@multi_server_confused | `svelte.playground-link` | 0.675 | *abstain* |
| embed-bge-small | multi_confused | fixed | cursor-bot-080@multi_server_confused | `svelte.get-documentation` | 0.656 | *abstain* |
| embed-bge-small | multi_confused | fixed | gpt-5.5-026@multi_server_confused | `deepwiki.read_wiki_contents` | 0.727 | `deepwiki.read_wiki_structure` |
| embed-bge-small | multi_confused | fixed | gpt-5.5-030@multi_server_confused | `microsoft-learn.microsoft_docs_search` | 0.673 | `gitmcp.fetch_generic_documentation` |
| embed-bge-small | multi_confused | fixed | gpt-5.5-031@multi_server_confused | `aws-knowledge.aws___search_documentation` | 0.638 | `gitmcp.search_generic_documentation` |
| embed-bge-small | multi_confused | fixed | gpt-5.5-061@multi_server_confused | `svelte.get-documentation` | 0.694 | `svelte.svelte-autofixer` |
| embed-bge-small | multi_confused | fixed | gpt-5.6-luna-021@multi_server_confused | `context7.resolve-library-id` | 0.579 | `deepwiki.ask_wiki_question` |
| embed-bge-small | multi_confused | fixed | gpt-5.6-luna-026@multi_server_confused | `svelte.get-documentation` | 0.689 | `deepwiki.read_wiki_structure` |
| embed-bge-small | multi_confused | fixed | gpt-5.6-luna-042@multi_server_confused | `huggingface.hub_repo_search` | 0.680 | `huggingface.hub_repo_details` |
| embed-bge-small | multi_confused | fixed | gpt-5.6-sol-024@multi_server_confused | `deepwiki.ask_wiki_question` | 0.707 | `deepwiki.read_wiki_contents` |
| embed-bge-small | multi_confused | fixed | gpt-5.6-sol-042@multi_server_confused | `kiwi.feedback-to-devs` | 0.583 | `huggingface.hub_repo_details` |
| embed-bge-small | multi_confused | fixed | gpt-5.6-terra-006@multi_server_confused | `aws-knowledge.aws___get_regional_availability` | 0.621 | `aws-knowledge.aws___search_documentation` |
| embed-bge-small | multi_confused | fixed | gpt-5.6-terra-031@multi_server_confused | `astro-docs.search_astro_docs` | 0.682 | `gitmcp.search_generic_documentation` |
| embed-bge-small | multi_confused | fixed | gpt-5.6-terra-040@multi_server_confused | `huggingface.hub_repo_details` | 0.708 | `huggingface.hub_repo_search` |
| embed-bge-small | multi_confused | fixed | gpt-6-astra-014@multi_server_confused | `kiwi.feedback-to-devs` | 0.556 | `cloudflare-docs.search_cloudflare_documentation` |
| embed-bge-small | multi_confused | fixed | gpt-6-astra-032@multi_server_confused | `aws-knowledge.aws___search_documentation` | 0.589 | `gitmcp.search_generic_documentation` |
| embed-bge-small | multi_server | fixed | claude-fable-5-1-002@multi_server | `cloudflare-docs.search_cloudflare_documentation` | 0.546 | `astro-docs.search_astro_docs` |
| embed-bge-small | multi_server | fixed | claude-fable-5-1-006@multi_server | `aws-knowledge.aws___get_regional_availability` | 0.600 | `aws-knowledge.aws___search_documentation` |
| embed-bge-small | multi_server | fixed | claude-fable-5-1-009@multi_server | `aws-knowledge.aws___list_regions` | 0.643 | `aws-knowledge.aws___get_regional_availability` |
| embed-bge-small | multi_server | fixed | claude-fable-5-1-020@multi_server | `huggingface.hf_fs` | 0.601 | `context7.query-docs` |
| embed-bge-small | multi_server | fixed | claude-fable-5-1-022@multi_server | `context7.query-docs` | 0.629 | `deepwiki.ask_wiki_question` |
| embed-bge-small | multi_server | fixed | claude-fable-5-1-026@multi_server | `deepwiki.read_wiki_contents` | 0.701 | `deepwiki.read_wiki_structure` |
| embed-bge-small | multi_server | fixed | claude-fable-5-1-030@multi_server | `gitmcp.fetch_generic_url_content` | 0.601 | `gitmcp.fetch_generic_documentation` |
| embed-bge-small | multi_server | fixed | claude-fable-5-1-041@multi_server | `huggingface.hub_repo_search` | 0.770 | `huggingface.hub_repo_details` |
| embed-bge-small | multi_server | fixed | claude-fable-5-1-047@multi_server | `kiwi.search-flight` | 0.689 | `kiwi.feedback-to-devs` |
| embed-bge-small | multi_server | fixed | claude-fable-5-1-054@multi_server | `microsoft-learn.microsoft_docs_search` | 0.712 | `microsoft-learn.microsoft_docs_fetch` |
| embed-bge-small | multi_server | fixed | claude-fable-5-1-055@multi_server | `svelte.get-documentation` | 0.840 | `svelte.list-sections` |
| embed-bge-small | multi_server | fixed | claude-fable-5-1-058@multi_server | `svelte.get-documentation` | 0.693 | `svelte.list-sections` |
| embed-bge-small | multi_server | fixed | claude-fable-5-1-065@multi_server | `svelte.playground-link` | 0.505 | *abstain* |
| embed-bge-small | multi_server | fixed | claude-fable-5-1-066@multi_server | `cloudflare-docs.search_cloudflare_documentation` | 0.465 | *abstain* |
| embed-bge-small | multi_server | fixed | claude-haiku-4-5-002@multi_server | `astro-docs.search_astro_docs` | 0.592 | *abstain* |
| embed-bge-small | multi_server | fixed | claude-haiku-4-5-019@multi_server | `aws-knowledge.aws___search_documentation` | 0.696 | `context7.resolve-library-id` |
| embed-bge-small | multi_server | fixed | claude-haiku-4-5-020@multi_server | `astro-docs.search_astro_docs` | 0.658 | `context7.resolve-library-id` |
| embed-bge-small | multi_server | fixed | claude-haiku-4-5-030@multi_server | `aws-knowledge.aws___search_documentation` | 0.680 | `gitmcp.match_common_libs_owner_repo_mapping` |
| embed-bge-small | multi_server | fixed | claude-haiku-4-5-033@multi_server | `svelte.get-documentation` | 0.666 | `gitmcp.match_common_libs_owner_repo_mapping` |
| embed-bge-small | multi_server | fixed | claude-haiku-4-5-034@multi_server | `aws-knowledge.aws___get_regional_availability` | 0.641 | `gitmcp.match_common_libs_owner_repo_mapping` |
| embed-bge-small | multi_server | fixed | claude-haiku-4-5-036@multi_server | `cloudflare-docs.migrate_pages_to_workers_guide` | 0.638 | `gitmcp.fetch_generic_url_content` |
| embed-bge-small | multi_server | fixed | claude-haiku-4-5-050@multi_server | `kiwi.feedback-to-devs` | 0.605 | `microsoft-learn.microsoft_docs_search` |
| embed-bge-small | multi_server | fixed | claude-haiku-4-5-053@multi_server | `microsoft-learn.microsoft_docs_fetch` | 0.792 | `microsoft-learn.microsoft_docs_search` |
| embed-bge-small | multi_server | fixed | claude-haiku-4-5-056@multi_server | `svelte.get-documentation` | 0.731 | `svelte.list-sections` |
| embed-bge-small | multi_server | fixed | claude-haiku-4-5-069@multi_server | `kiwi.feedback-to-devs` | 0.481 | *abstain* |
| embed-bge-small | multi_server | fixed | claude-opus-5-5-003@multi_server | `aws-knowledge.aws___get_regional_availability` | 0.711 | `aws-knowledge.aws___read_documentation` |
| embed-bge-small | multi_server | fixed | claude-opus-5-5-031@multi_server | `deepwiki.read_wiki_contents` | 0.628 | `gitmcp.search_generic_documentation` |
| embed-bge-small | multi_server | fixed | claude-opus-5-5-034@multi_server | `cloudflare-docs.search_cloudflare_documentation` | 0.561 | `gitmcp.search_generic_code` |
| embed-bge-small | multi_server | fixed | claude-opus-5-5-065@multi_server | `cloudflare-docs.migrate_pages_to_workers_guide` | 0.726 | *abstain* |
| embed-bge-small | multi_server | fixed | claude-opus-5-5-066@multi_server | `deepwiki.read_wiki_contents` | 0.394 | *abstain* |
| embed-bge-small | multi_server | fixed | claude-opus-5-5-067@multi_server | `kiwi.search-flight` | 0.573 | *abstain* |
| embed-bge-small | multi_server | fixed | claude-sonnet-5-5-005@multi_server | `aws-knowledge.aws___retrieve_skill` | 0.634 | `aws-knowledge.aws___search_documentation` |
| embed-bge-small | multi_server | fixed | claude-sonnet-5-5-020@multi_server | `context7.resolve-library-id` | 0.644 | `context7.query-docs` |
| embed-bge-small | multi_server | fixed | claude-sonnet-5-5-036@multi_server | `microsoft-learn.microsoft_code_sample_search` | 0.636 | `gitmcp.fetch_generic_url_content` |
| embed-bge-small | multi_server | fixed | claude-sonnet-5-5-040@multi_server | `gitmcp.search_generic_documentation` | 0.552 | `huggingface.hub_repo_search` |
| embed-bge-small | multi_server | fixed | claude-sonnet-5-5-055@multi_server | `svelte.get-documentation` | 0.776 | `svelte.list-sections` |
| embed-bge-small | multi_server | fixed | claude-sonnet-5-5-058@multi_server | `svelte.get-documentation` | 0.762 | `svelte.list-sections` |
| embed-bge-small | multi_server | fixed | claude-sonnet-5-5-068@multi_server | `aws-knowledge.aws___get_regional_availability` | 0.563 | *abstain* |
| embed-bge-small | multi_server | fixed | claude-sonnet-5-5-070@multi_server | `huggingface.hf_fs` | 0.635 | *abstain* |
| embed-bge-small | multi_server | fixed | cursor-bot-001@multi_server | `astro-docs.search_astro_docs` | 0.657 | *abstain* |
| embed-bge-small | multi_server | fixed | cursor-bot-002@multi_server | `astro-docs.search_astro_docs` | 0.589 | *abstain* |
| embed-bge-small | multi_server | fixed | cursor-bot-004@multi_server | `huggingface.hub_repo_details` | 0.641 | *abstain* |
| embed-bge-small | multi_server | fixed | cursor-bot-006@multi_server | `astro-docs.search_astro_docs` | 0.572 | *abstain* |
| embed-bge-small | multi_server | fixed | cursor-bot-011@multi_server | `deepwiki.ask_wiki_question` | 0.541 | *abstain* |
| embed-bge-small | multi_server | fixed | cursor-bot-013@multi_server | `aws-knowledge.aws___get_regional_availability` | 0.589 | *abstain* |
| embed-bge-small | multi_server | fixed | cursor-bot-014@multi_server | `aws-knowledge.aws___get_regional_availability` | 0.598 | *abstain* |
| embed-bge-small | multi_server | fixed | cursor-bot-024@multi_server | `cloudflare-docs.search_cloudflare_documentation` | 0.642 | *abstain* |
| embed-bge-small | multi_server | fixed | cursor-bot-026@multi_server | `context7.resolve-library-id` | 0.575 | *abstain* |
| embed-bge-small | multi_server | fixed | cursor-bot-033@multi_server | `deepwiki.ask_wiki_question` | 0.722 | *abstain* |
| embed-bge-small | multi_server | fixed | cursor-bot-036@multi_server | `deepwiki.read_wiki_contents` | 0.623 | *abstain* |
| embed-bge-small | multi_server | fixed | cursor-bot-043@multi_server | `gitmcp.match_common_libs_owner_repo_mapping` | 0.574 | *abstain* |
| embed-bge-small | multi_server | fixed | cursor-bot-047@multi_server | `gitmcp.match_common_libs_owner_repo_mapping` | 0.616 | *abstain* |
| embed-bge-small | multi_server | fixed | cursor-bot-048@multi_server | `gitmcp.match_common_libs_owner_repo_mapping` | 0.647 | *abstain* |
| embed-bge-small | multi_server | fixed | cursor-bot-054@multi_server | `huggingface.hub_repo_search` | 0.539 | *abstain* |
| embed-bge-small | multi_server | fixed | cursor-bot-055@multi_server | `huggingface.hub_repo_details` | 0.614 | *abstain* |
| embed-bge-small | multi_server | fixed | cursor-bot-056@multi_server | `cloudflare-docs.search_cloudflare_documentation` | 0.543 | *abstain* |
| embed-bge-small | multi_server | fixed | cursor-bot-057@multi_server | `kiwi.search-flight` | 0.682 | *abstain* |
| embed-bge-small | multi_server | fixed | cursor-bot-058@multi_server | `kiwi.feedback-to-devs` | 0.566 | *abstain* |
| embed-bge-small | multi_server | fixed | cursor-bot-064@multi_server | `kiwi.search-flight` | 0.621 | *abstain* |
| embed-bge-small | multi_server | fixed | cursor-bot-068@multi_server | `context7.query-docs` | 0.518 | *abstain* |
| embed-bge-small | multi_server | fixed | cursor-bot-069@multi_server | `aws-knowledge.aws___get_regional_availability` | 0.514 | *abstain* |
| embed-bge-small | multi_server | fixed | cursor-bot-074@multi_server | `svelte.playground-link` | 0.644 | *abstain* |
| embed-bge-small | multi_server | fixed | cursor-bot-075@multi_server | `svelte.svelte-autofixer` | 0.724 | *abstain* |
| embed-bge-small | multi_server | fixed | cursor-bot-076@multi_server | `svelte.svelte-autofixer` | 0.700 | *abstain* |
| embed-bge-small | multi_server | fixed | cursor-bot-078@multi_server | `svelte.svelte-autofixer` | 0.726 | *abstain* |
| embed-bge-small | multi_server | fixed | cursor-bot-079@multi_server | `svelte.playground-link` | 0.675 | *abstain* |
| embed-bge-small | multi_server | fixed | cursor-bot-080@multi_server | `svelte.get-documentation` | 0.656 | *abstain* |
| embed-bge-small | multi_server | fixed | gpt-5.5-017@multi_server | `context7.query-docs` | 0.740 | `context7.resolve-library-id` |
| embed-bge-small | multi_server | fixed | gpt-5.5-026@multi_server | `deepwiki.read_wiki_contents` | 0.727 | `deepwiki.read_wiki_structure` |
| embed-bge-small | multi_server | fixed | gpt-5.5-030@multi_server | `microsoft-learn.microsoft_docs_search` | 0.673 | `gitmcp.fetch_generic_documentation` |
| embed-bge-small | multi_server | fixed | gpt-5.5-031@multi_server | `cloudflare-docs.search_cloudflare_documentation` | 0.624 | `gitmcp.search_generic_documentation` |
| embed-bge-small | multi_server | fixed | gpt-5.5-061@multi_server | `svelte.get-documentation` | 0.694 | `svelte.svelte-autofixer` |
| embed-bge-small | multi_server | fixed | gpt-5.5-063@multi_server | `aws-knowledge.aws___get_regional_availability` | 0.454 | *abstain* |
| embed-bge-small | multi_server | fixed | gpt-5.5-065@multi_server | `huggingface.hub_repo_search` | 0.709 | *abstain* |
| embed-bge-small | multi_server | fixed | gpt-5.6-luna-021@multi_server | `gitmcp.match_common_libs_owner_repo_mapping` | 0.565 | `deepwiki.ask_wiki_question` |
| embed-bge-small | multi_server | fixed | gpt-5.6-luna-022@multi_server | `cloudflare-docs.search_cloudflare_documentation` | 0.629 | `deepwiki.ask_wiki_question` |
| embed-bge-small | multi_server | fixed | gpt-5.6-luna-026@multi_server | `deepwiki.read_wiki_contents` | 0.687 | `deepwiki.read_wiki_structure` |
| embed-bge-small | multi_server | fixed | gpt-5.6-luna-034@multi_server | `huggingface.hub_repo_details` | 0.620 | `gitmcp.search_generic_code` |
| embed-bge-small | multi_server | fixed | gpt-5.6-luna-042@multi_server | `huggingface.hub_repo_search` | 0.680 | `huggingface.hub_repo_details` |
| embed-bge-small | multi_server | fixed | gpt-5.6-luna-063@multi_server | `kiwi.search-flight` | 0.581 | *abstain* |
| embed-bge-small | multi_server | fixed | gpt-5.6-sol-019@multi_server | `svelte.playground-link` | 0.573 | `context7.query-docs` |
| embed-bge-small | multi_server | fixed | gpt-5.6-sol-024@multi_server | `deepwiki.ask_wiki_question` | 0.707 | `deepwiki.read_wiki_contents` |
| embed-bge-small | multi_server | fixed | gpt-5.6-sol-042@multi_server | `kiwi.feedback-to-devs` | 0.583 | `huggingface.hub_repo_details` |
| embed-bge-small | multi_server | fixed | gpt-5.6-sol-054@multi_server | `microsoft-learn.microsoft_docs_search` | 0.670 | `microsoft-learn.microsoft_docs_fetch` |
| embed-bge-small | multi_server | fixed | gpt-5.6-sol-058@multi_server | `svelte.get-documentation` | 0.822 | `svelte.list-sections` |
| embed-bge-small | multi_server | fixed | gpt-5.6-sol-067@multi_server | `aws-knowledge.aws___get_regional_availability` | 0.386 | *abstain* |
| embed-bge-small | multi_server | fixed | gpt-5.6-sol-070@multi_server | `kiwi.feedback-to-devs` | 0.541 | *abstain* |
| embed-bge-small | multi_server | fixed | gpt-5.6-terra-006@multi_server | `aws-knowledge.aws___get_regional_availability` | 0.621 | `aws-knowledge.aws___search_documentation` |
| embed-bge-small | multi_server | fixed | gpt-5.6-terra-030@multi_server | `deepwiki.ask_wiki_question` | 0.627 | `gitmcp.fetch_generic_documentation` |
| embed-bge-small | multi_server | fixed | gpt-5.6-terra-031@multi_server | `astro-docs.search_astro_docs` | 0.682 | `gitmcp.search_generic_documentation` |
| embed-bge-small | multi_server | fixed | gpt-5.6-terra-040@multi_server | `huggingface.hub_repo_details` | 0.708 | `huggingface.hub_repo_search` |
| embed-bge-small | multi_server | fixed | gpt-5.6-terra-043@multi_server | `huggingface.hub_repo_search` | 0.745 | `huggingface.hf_fs` |
| embed-bge-small | multi_server | fixed | gpt-5.6-terra-054@multi_server | `microsoft-learn.microsoft_docs_search` | 0.729 | `microsoft-learn.microsoft_docs_fetch` |
| embed-bge-small | multi_server | fixed | gpt-5.6-terra-055@multi_server | `svelte.get-documentation` | 0.822 | `svelte.list-sections` |
| embed-bge-small | multi_server | fixed | gpt-5.6-terra-064@multi_server | `huggingface.hf_fs` | 0.475 | *abstain* |
| embed-bge-small | multi_server | fixed | gpt-5.6-terra-068@multi_server | `microsoft-learn.microsoft_docs_search` | 0.592 | *abstain* |
| embed-bge-small | multi_server | fixed | gpt-6-astra-005@multi_server | `aws-knowledge.aws___retrieve_skill` | 0.762 | `aws-knowledge.aws___search_documentation` |
| embed-bge-small | multi_server | fixed | gpt-6-astra-014@multi_server | `kiwi.feedback-to-devs` | 0.556 | `cloudflare-docs.search_cloudflare_documentation` |
| embed-bge-small | multi_server | fixed | gpt-6-astra-032@multi_server | `aws-knowledge.aws___search_documentation` | 0.589 | `gitmcp.search_generic_documentation` |
| embed-bge-small | multi_server | fixed | gpt-6-astra-054@multi_server | `microsoft-learn.microsoft_code_sample_search` | 0.648 | `microsoft-learn.microsoft_docs_fetch` |
| embed-bge-small | one_server | fixed | claude-fable-5-1-006@one_server | `aws-knowledge.aws___get_regional_availability` | 0.600 | `aws-knowledge.aws___search_documentation` |
| embed-bge-small | one_server | fixed | claude-fable-5-1-009@one_server | `aws-knowledge.aws___list_regions` | 0.643 | `aws-knowledge.aws___get_regional_availability` |
| embed-bge-small | one_server | fixed | claude-fable-5-1-026@one_server | `deepwiki.read_wiki_contents` | 0.701 | `deepwiki.read_wiki_structure` |
| embed-bge-small | one_server | fixed | claude-fable-5-1-030@one_server | `gitmcp.fetch_generic_url_content` | 0.601 | `gitmcp.fetch_generic_documentation` |
| embed-bge-small | one_server | fixed | claude-fable-5-1-041@one_server | `huggingface.hub_repo_search` | 0.770 | `huggingface.hub_repo_details` |
| embed-bge-small | one_server | fixed | claude-fable-5-1-047@one_server | `kiwi.search-flight` | 0.689 | `kiwi.feedback-to-devs` |
| embed-bge-small | one_server | fixed | claude-fable-5-1-054@one_server | `microsoft-learn.microsoft_docs_search` | 0.712 | `microsoft-learn.microsoft_docs_fetch` |
| embed-bge-small | one_server | fixed | claude-fable-5-1-055@one_server | `svelte.get-documentation` | 0.840 | `svelte.list-sections` |
| embed-bge-small | one_server | fixed | claude-fable-5-1-058@one_server | `svelte.get-documentation` | 0.693 | `svelte.list-sections` |
| embed-bge-small | one_server | fixed | claude-fable-5-1-065@one_server | `huggingface.hf_fs` | 0.503 | *abstain* |
| embed-bge-small | one_server | fixed | claude-fable-5-1-066@one_server | `aws-knowledge.aws___search_documentation` | 0.446 | *abstain* |
| embed-bge-small | one_server | fixed | claude-haiku-4-5-002@one_server | `astro-docs.search_astro_docs` | 0.592 | *abstain* |
| embed-bge-small | one_server | fixed | claude-haiku-4-5-019@one_server | `context7.query-docs` | 0.635 | `context7.resolve-library-id` |
| embed-bge-small | one_server | fixed | claude-haiku-4-5-020@one_server | `context7.query-docs` | 0.655 | `context7.resolve-library-id` |
| embed-bge-small | one_server | fixed | claude-haiku-4-5-030@one_server | `gitmcp.fetch_generic_documentation` | 0.643 | `gitmcp.match_common_libs_owner_repo_mapping` |
| embed-bge-small | one_server | fixed | claude-haiku-4-5-033@one_server | `gitmcp.search_generic_code` | 0.659 | `gitmcp.match_common_libs_owner_repo_mapping` |
| embed-bge-small | one_server | fixed | claude-haiku-4-5-034@one_server | `gitmcp.search_generic_code` | 0.637 | `gitmcp.match_common_libs_owner_repo_mapping` |
| embed-bge-small | one_server | fixed | claude-haiku-4-5-036@one_server | `gitmcp.search_generic_documentation` | 0.607 | `gitmcp.fetch_generic_url_content` |
| embed-bge-small | one_server | fixed | claude-haiku-4-5-050@one_server | `microsoft-learn.microsoft_code_sample_search` | 0.554 | `microsoft-learn.microsoft_docs_search` |
| embed-bge-small | one_server | fixed | claude-haiku-4-5-053@one_server | `microsoft-learn.microsoft_docs_fetch` | 0.792 | `microsoft-learn.microsoft_docs_search` |
| embed-bge-small | one_server | fixed | claude-haiku-4-5-056@one_server | `svelte.get-documentation` | 0.731 | `svelte.list-sections` |
| embed-bge-small | one_server | fixed | claude-haiku-4-5-069@one_server | `kiwi.feedback-to-devs` | 0.481 | *abstain* |
| embed-bge-small | one_server | fixed | claude-opus-5-5-003@one_server | `aws-knowledge.aws___get_regional_availability` | 0.711 | `aws-knowledge.aws___read_documentation` |
| embed-bge-small | one_server | fixed | claude-opus-5-5-031@one_server | `gitmcp.match_common_libs_owner_repo_mapping` | 0.623 | `gitmcp.search_generic_documentation` |
| embed-bge-small | one_server | fixed | claude-opus-5-5-065@one_server | `cloudflare-docs.migrate_pages_to_workers_guide` | 0.726 | *abstain* |
| embed-bge-small | one_server | fixed | claude-opus-5-5-066@one_server | `context7.query-docs` | 0.346 | *abstain* |
| embed-bge-small | one_server | fixed | claude-opus-5-5-067@one_server | `kiwi.search-flight` | 0.573 | *abstain* |
| embed-bge-small | one_server | fixed | claude-sonnet-5-5-005@one_server | `aws-knowledge.aws___retrieve_skill` | 0.634 | `aws-knowledge.aws___search_documentation` |
| embed-bge-small | one_server | fixed | claude-sonnet-5-5-020@one_server | `context7.resolve-library-id` | 0.644 | `context7.query-docs` |
| embed-bge-small | one_server | fixed | claude-sonnet-5-5-055@one_server | `svelte.get-documentation` | 0.776 | `svelte.list-sections` |
| embed-bge-small | one_server | fixed | claude-sonnet-5-5-058@one_server | `svelte.get-documentation` | 0.762 | `svelte.list-sections` |
