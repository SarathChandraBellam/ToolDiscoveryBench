# ToolDiscoveryBench — claude_v2 scaling, test split (2026-10-10)

## Accuracy

| router | suite | tools | n | no-tool | err | **acc** | top-1 | lenient | top-3 | server@1 | abstain ✓ | false abstain | refused |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| bm25 | claude_v2 | 10 | 165 | 33 | 0 | **36.4%** | 45.5% | 45.5% | 84.1% | 79.5% | 0.0% | 0.0% | 0.0% |
| bm25 | claude_v2 | 30 | 165 | 33 | 0 | **29.1%** | 36.4% | 36.4% | 81.8% | 70.5% | 0.0% | 0.0% | 0.0% |
| bm25 | claude_v2 | 75 | 165 | 33 | 0 | **27.3%** | 34.1% | 34.1% | 61.4% | 59.1% | 0.0% | 0.0% | 0.0% |
| bm25 | claude_v2 | 150 | 165 | 33 | 0 | **25.5%** | 31.8% | 31.8% | 56.8% | 52.3% | 0.0% | 0.0% | 0.0% |
| or-jev-flat | claude_v2 | 10 | 165 | 33 | 0 | **95.2%** | 95.5% | 95.5% | 100.0% | 100.0% | 93.9% | 0.0% | 0.0% |
| or-jev-flat | claude_v2 | 30 | 165 | 33 | 0 | **87.9%** | 93.9% | 93.9% | 100.0% | 97.0% | 63.6% | 0.0% | 0.0% |
| or-jev-flat | claude_v2 | 75 | 165 | 33 | 0 | **78.2%** | 86.4% | 86.4% | 98.5% | 93.2% | 45.5% | 0.0% | 0.0% |
| or-jev-flat | claude_v2 | 150 | 165 | 33 | 0 | **75.2%** | 82.6% | 82.6% | 98.5% | 91.7% | 45.5% | 0.0% | 0.0% |

*acc: answerable questions need the gold tool first, no-tool questions need an abstain. top-1 / lenient / top-3 / server@1 are over answerable questions only; lenient also accepts tools labelled acceptable. abstain ✓: share of no-tool questions where the router abstained. false abstain: share of answerable ones where it did. refused: share of questions where the backend refused a per-server sub-question (scored as P = 0 for that server, which can flatter accuracy).*

## Speed, cost and calibration

| router | suite | tools | p50 ms | p95 ms | calls | in-tok | $/1k q | ECE | Brier | conf ✓ | conf ✗ |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| bm25 | claude_v2 | 10 | 0 | 0 | 0.000 | – | – | – | – | – | – |
| bm25 | claude_v2 | 30 | 1 | 1 | 0.000 | – | – | – | – | – | – |
| bm25 | claude_v2 | 75 | 1 | 1 | 0.000 | – | – | – | – | – | – |
| bm25 | claude_v2 | 150 | 2 | 2 | 0.000 | – | – | – | – | – | – |
| or-jev-flat | claude_v2 | 10 | 201 | 262 | 1.000 | 850 | 0.036 | 0.052 | 0.035 | 0.949 | 0.642 |
| or-jev-flat | claude_v2 | 30 | 206 | 293 | 1.000 | 1,640 | 0.069 | 0.085 | 0.062 | 0.916 | 0.540 |
| or-jev-flat | claude_v2 | 75 | 215 | 327 | 1.000 | 3,407 | 0.143 | 0.103 | 0.118 | 0.904 | 0.576 |
| or-jev-flat | claude_v2 | 150 | 223 | 274 | 1.000 | 6,047 | 0.254 | 0.096 | 0.108 | 0.908 | 0.535 |

*Calibration columns are filled only for calibrated routers (Jev). conf ✓ / ✗ is the mean top-1 probability when right vs wrong; a big gap lets you set an abstain threshold.*

## Top-1 with 95% bootstrap confidence intervals

| router | suite | tools | n | top-1 | 95% CI | test n | test top-1 | test 95% CI |
|---|---|---:|---:|---:|---|---:|---:|---|
| bm25 | claude_v2 | 10 | 44 | 45.5% | 31.8%–59.1% | 44 | 45.5% | 31.8%–59.1% |
| bm25 | claude_v2 | 30 | 44 | 36.4% | 22.7%–50.0% | 44 | 36.4% | 22.7%–50.0% |
| bm25 | claude_v2 | 75 | 44 | 34.1% | 20.5%–47.7% | 44 | 34.1% | 20.5%–47.7% |
| bm25 | claude_v2 | 150 | 44 | 31.8% | 18.2%–45.5% | 44 | 31.8% | 18.2%–45.5% |
| or-jev-flat | claude_v2 | 10 | 44 | 95.5% | 88.6%–100.0% | 44 | 95.5% | 88.6%–100.0% |
| or-jev-flat | claude_v2 | 30 | 44 | 93.9% | 86.4%–99.2% | 44 | 93.9% | 86.4%–99.2% |
| or-jev-flat | claude_v2 | 75 | 44 | 86.4% | 75.8%–95.5% | 44 | 86.4% | 75.8%–95.5% |
| or-jev-flat | claude_v2 | 150 | 44 | 82.6% | 70.5%–93.2% | 44 | 82.6% | 70.5%–93.2% |

*Answerable questions only; 1000 seeded resamples over questions (repeats averaged per question). *test* is the frozen held-out split (`data/golden/splits/test_qids.txt`); publish numbers from it with repeats ≥ 3.*

## Accuracy by question tag (all suites and sizes pooled)

| router | cloud-docs | code | generator:cursor-bot | hard_negative | id_given | implicit_vendor | intra_server | lib-docs | ml-hub | multi_valid | needs_human_review | no_tool | paraphrase | repo-qa | split:test | travel | url_given |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| or-jev-flat | 94.1% | 100.0% | 62.1% | 90.9% | 16.7% | 100.0% | 100.0% | 83.3% | 100.0% | 81.2% | 62.1% | 62.1% | 100.0% | 80.6% | 84.1% | 100.0% | 83.3% |
| bm25 | 36.8% | 33.3% | 0.0% | 50.0% | 0.0% | 35.0% | 82.1% | 25.0% | 30.0% | 0.0% | 0.0% | 0.0% | 12.5% | 50.0% | 29.5% | 58.3% | 66.7% |

## Accuracy by question author (model family that wrote the question)

| router | cursor |
|---|---:|
| bm25 | 0.0% |
| or-jev-flat | 62.1% |

## Accuracy by question author (exact model)

| router | cursor-bot |
|---|---:|
| bm25 | 0.0% |
| or-jev-flat | 62.1% |

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
| or-jev-flat | claude_v2 | 10 | d-c7-query-03 | `context7.resolve-library-id` | 0.760 | `context7.query-docs` |
| or-jev-flat | claude_v2 | 10 | d-dw-read-02 | `deepwiki.read_wiki_structure` | 0.580 | `deepwiki.read_wiki_contents` |
| or-jev-flat | claude_v2 | 150 | cursor-bot-002 | `astro-docs.search_astro_docs` | 0.560 | *abstain* |
| or-jev-flat | claude_v2 | 150 | cursor-bot-036 | `gitmcp.match_common_libs_owner_repo_mapping` | 0.720 | *abstain* |
| or-jev-flat | claude_v2 | 150 | cursor-bot-055 | `huggingface.hf_whoami` | 0.520 | *abstain* |
| or-jev-flat | claude_v2 | 150 | cursor-bot-075 | `svelte.get-documentation` | 0.350 | *abstain* |
| or-jev-flat | claude_v2 | 150 | cursor-bot-076 | `syn-codehost.get_file` | 0.270 | *abstain* |
| or-jev-flat | claude_v2 | 150 | cursor-bot-078 | `svelte.get-documentation` | 0.490 | *abstain* |
| or-jev-flat | claude_v2 | 150 | d-aws-skill-01 | `aws-knowledge.aws___retrieve_skill` | 0.520 | `aws-knowledge.aws___search_documentation` |
| or-jev-flat | claude_v2 | 150 | d-aws-skill-02 | `aws-knowledge.aws___retrieve_skill` | 0.600 | `aws-knowledge.aws___search_documentation` |
| or-jev-flat | claude_v2 | 150 | d-c7-either-03 | `context7.query-docs` | 0.470 | `context7.resolve-library-id` |
| or-jev-flat | claude_v2 | 150 | d-c7-query-03 | `context7.resolve-library-id` | 0.490 | `context7.query-docs` |
| or-jev-flat | claude_v2 | 150 | d-dw-ask-03 | `context7.query-docs` | 0.360 | `deepwiki.ask_wiki_question` |
| or-jev-flat | claude_v2 | 150 | d-dw-read-02 | `gitmcp.fetch_generic_documentation` | 0.930 | `deepwiki.read_wiki_contents` |
| or-jev-flat | claude_v2 | 150 | d-gm-url-01 | `syn-web.fetch_url` | 0.870 | `gitmcp.fetch_generic_url_content` |
| or-jev-flat | claude_v2 | 150 | dw-01 | `gitmcp.search_generic_code` | 0.310 | `deepwiki.ask_wiki_question` |
| or-jev-flat | claude_v2 | 30 | cursor-bot-002 | `syn-storage.read_file` | 0.620 | *abstain* |
| or-jev-flat | claude_v2 | 30 | cursor-bot-013 | `aws-knowledge.aws___retrieve_skill` | 0.640 | *abstain* |
| or-jev-flat | claude_v2 | 30 | cursor-bot-076 | `syn-codehost.search_code` | 0.570 | *abstain* |
| or-jev-flat | claude_v2 | 30 | cursor-bot-078 | `svelte.get-documentation` | 0.500 | *abstain* |
| or-jev-flat | claude_v2 | 30 | d-c7-query-03 | `context7.resolve-library-id` | 0.620 | `context7.query-docs` |
| or-jev-flat | claude_v2 | 30 | d-dw-ask-03 | `context7.resolve-library-id` | 0.400 | `deepwiki.ask_wiki_question` |
| or-jev-flat | claude_v2 | 75 | cursor-bot-002 | `syn-codehost.get_file` | 0.830 | *abstain* |
| or-jev-flat | claude_v2 | 75 | cursor-bot-013 | `aws-knowledge.aws___search_documentation` | 0.490 | *abstain* |
| or-jev-flat | claude_v2 | 75 | cursor-bot-033 | `gitmcp.fetch_generic_documentation` | 0.320 | *abstain* |
| or-jev-flat | claude_v2 | 75 | cursor-bot-055 | `huggingface.hub_repo_details` | 0.570 | *abstain* |
| or-jev-flat | claude_v2 | 75 | cursor-bot-075 | `svelte.list-sections` | 0.320 | *abstain* |
| or-jev-flat | claude_v2 | 75 | cursor-bot-076 | `syn-codehost.get_file` | 0.500 | *abstain* |
| or-jev-flat | claude_v2 | 75 | d-aws-skill-01 | `aws-knowledge.aws___retrieve_skill` | 0.510 | `aws-knowledge.aws___search_documentation` |
| or-jev-flat | claude_v2 | 75 | d-aws-skill-02 | `aws-knowledge.aws___retrieve_skill` | 0.640 | `aws-knowledge.aws___search_documentation` |
| or-jev-flat | claude_v2 | 75 | d-c7-either-03 | `context7.query-docs` | 0.460 | `context7.resolve-library-id` |
| or-jev-flat | claude_v2 | 75 | d-dw-ask-03 | `gitmcp.search_generic_documentation` | 0.310 | `deepwiki.ask_wiki_question` |
| or-jev-flat | claude_v2 | 75 | d-dw-read-02 | `gitmcp.fetch_generic_documentation` | 0.960 | `deepwiki.read_wiki_contents` |
| or-jev-flat | claude_v2 | 75 | d-gm-url-01 | `syn-web.fetch_url` | 0.890 | `gitmcp.fetch_generic_url_content` |
