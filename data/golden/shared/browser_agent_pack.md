# Tool-selection labeling task

You are helping build a benchmark that measures how well AI agents pick the right MCP
(Model Context Protocol) tool. Act as an agent that is connected to the public, no-auth MCP
servers listed below. For each user request, decide which tool you would call **first**,
with arguments, exactly as you would if you were really handling it.

## Step 1: understand the servers (use your browser)

All servers below are public and need no login. Before labeling, use your browser to learn
what each one is for, so your choices are grounded in what the servers actually do:

- **deepwiki**: Q&A and generated wiki pages for public GitHub repositories
- **context7**: Up-to-date, version-specific library and framework documentation
- **aws-knowledge**: AWS documentation, regional availability and AWS skills
- **microsoft-learn**: Microsoft Learn docs (Azure, .NET, M365, Entra) and code samples
- **huggingface**: Search Hugging Face models, datasets, Spaces and papers
- **cloudflare-docs**: Cloudflare developer documentation (Workers, R2, D1, etc.)
- **gitmcp**: Generic docs/code lookup for any GitHub repository
- **astro-docs**: Astro web framework documentation
- **svelte**: Svelte and SvelteKit docs plus a Svelte code autofixer
- **kiwi**: Kiwi.com flight search

Visit each server's homepage or documentation (search for the server name plus "MCP server"
if needed), and note anything that changes how you'd choose between overlapping tools: what
each docs server covers, which tool must be called before another, what input each tool
needs. Write a short "Server notes" section (3 to 6 bullets) with the URLs you used.

Rules for browsing:
- Read only. Do not sign in, submit forms, send messages or create accounts.
- Do not search for this benchmark, its answers, or the request texts themselves.
- If you cannot reach a site, say so in your notes and rely on the tool descriptions.

## Step 2: label every request

The tool catalog (the only tools you have) and the requests follow. For each request:

1. `tool_id`: the single tool you would call first, written exactly as in the catalog
   (`server.tool`). Use `null` only if no tool in the catalog fits at all.
2. `arguments`: values for that tool's inputs, taken from the request (include every
   required input).
3. `acceptable_alternatives`: other tool_ids that would also be a reasonable first call.
   Empty when your pick is clearly the only good one.
4. `confidence`: 0 to 1, how sure you are your first call is the best one.
5. `rationale`: one sentence.
6. `evidence_url`: a URL from Step 1 that informed the choice, or `null`.

Follow ordering rules stated in tool descriptions (for example, a tool that says another
tool must be called before it). Judge each request on its own.

## Output format

Reply in batches of 40 requests, in the order given. Each batch is ONE fenced code block
of JSON Lines, one object per line, nothing else inside the block:

```jsonl
{"id": "...", "tool_id": "server.tool", "arguments": {}, "acceptable_alternatives": [], "confidence": 0.9, "rationale": "...", "evidence_url": null}
```

After each batch, stop and wait until I reply "continue". Put the Server notes before the
first batch. Every request id must appear exactly once across all batches.

## Tool catalog (31 tools)

- `deepwiki.ask_wiki_question`: Ask any question about a GitHub repository's codebase and get an AI-powered answer grounded in its DeepWiki.  
  inputs: repoName*, question*
- `deepwiki.read_wiki_contents`: View documentation about a GitHub repository.  
  inputs: repoName*
- `deepwiki.read_wiki_structure`: Get a list of documentation topics for a GitHub repository.  
  inputs: repoName*
- `context7.resolve-library-id`: Resolves a package/product name to a Context7-compatible library ID and returns matching libraries. You MUST call this function before 'Query Documentation' tool to obtain a valid Context7-compatible library ID UNLESS the user explicitly provides a library ID in the format '/org/project' or '/org/project/version' in their query. Each result includ…  
  inputs: query*, libraryName*
- `context7.query-docs`: Retrieves and queries up-to-date documentation and code examples from Context7 for any programming library or framework. You must call 'Resolve Context7 Library ID' tool first to obtain the exact Context7-compatible library ID required to use this tool, UNLESS the user explicitly provides a library ID in the format '/org/project' or '/org/project/…  
  inputs: libraryId*, query*
- `aws-knowledge.aws___read_documentation`: Fetch full AWS doc pages as markdown. `search_documentation` already returns verbatim page chunks, so don't re-read a URL whose chunk you already have to "confirm" or "round out" an answer -- the chunk is the real page text; treat it as authoritative. Reading the full page is justified ONLY when the chunks genuinely lack the content: - an enumerat…  
  inputs: requests
- `aws-knowledge.aws___search_documentation`: AWS docs search. Each result's `context` is verbatim page text -- a real chunk of the actual page, not a short snippet -- and usually already contains the answer, so answer directly from it. Use `read_documentation` only when the chunks genuinely lack the needed detail. Pick ONE topic. Add a 2nd ONLY if query genuinely spans domains. Extra topics …  
  inputs: limit, search_phrase*, topics
- `aws-knowledge.aws___list_regions`: Retrieve a list of all AWS regions.  
  inputs: none
- `aws-knowledge.aws___get_regional_availability`: AWS resource availability per region. - Max 10 regions; multi-region needs `filters`; single-region supports `next_token`. - Status: isAvailableIn | isNotAvailableIn | isPlannedIn | Not Found. - Response key: products | service_apis | cfn_resources. Not for region counts/docs/vague queries -- use `search_documentation` / `list_regions`. Filter val…  
  inputs: regions, resource_type*, filters, next_token, region
- `aws-knowledge.aws___retrieve_skill`: Retrieve an AWS skill (workflows, references). Returns SKILL.md, or `file` if given. Call `search_documentation` FIRST and copy `skill_name` verbatim -- it is an opaque registry ID. Never guess or fabricate `skill_name` or `file`.  
  inputs: file, skill_name*
- `microsoft-learn.microsoft_docs_search`: Search official Microsoft/Azure documentation to find the most relevant and trustworthy content for a user's query. This tool returns up to 10 high-quality content chunks (each max 500 tokens), extracted from Microsoft Learn and other official sources. Each result includes the article title, URL, and a self-contained content excerpt optimized for …  
  inputs: query
- `microsoft-learn.microsoft_code_sample_search`: Search for code snippets and examples in official Microsoft Learn documentation. This tool retrieves relevant code samples from Microsoft documentation pages providing developers with practical implementation examples and best practices for Microsoft/Azure products and services related coding tasks. This tool will help you use the **LATEST OFFICIA…  
  inputs: query*, language
- `microsoft-learn.microsoft_docs_fetch`: Fetch and convert a Microsoft Learn documentation webpage to markdown format. This tool retrieves the latest complete content of Microsoft documentation webpages including Azure, .NET, Microsoft 365, and other Microsoft technologies. ## When to Use This Tool - When search results provide incomplete information or truncated content - When you need …  
  inputs: url*
- `huggingface.hf_whoami`: Inspect the current Hugging Face authentication context, including the account, visible organization memberships, and credential access details. Read-only and never returns credential values.  
  inputs: none
- `huggingface.hub_repo_search`: Search Hugging Face repositories with a shared query interface. You can target models, datasets, spaces, or aggregate across multiple repo types in one call. Include links to repositories in your response.  
  inputs: query, repo_types, author, filters, sort, limit
- `huggingface.hub_repo_details`: Get details for one or more Hugging Face repos (model, dataset, or space). Auto-detects type unless specified. For datasets, use operations: overview, dataset_structure, dataset_preview. Use dataset_structure first to discover configs, splits, sizes, and schema. Use dataset_preview only when config and split are known, unless the dataset has a sin…  
  inputs: repo_ids*, repo_type, operations, config, split, offset, limit
- `huggingface.hf_fs`: When to use: Hugging Face Hub models, datasets, Spaces, collections, papers, daily papers, today's trending models, current paper leaderboard, docs, and repository files. Examples: {"operations":[{"cmd":"ls","args":["hf://models/trending","--limit","10"]}]} {"operations":[{"cmd":"ls","args":["hf://papers/trending"]}]} {"operations":[{"cmd":"ls","a…  
  inputs: operations*
- `cloudflare-docs.search_cloudflare_documentation`: Search the Cloudflare documentation. This tool should be used to answer any question about Cloudflare products or features, including: - Workers, Pages, R2, Images, Stream, D1, Durable Objects, KV, Workflows, Hyperdrive, Queues - AI Search, Workers AI, Vectorize, AI Gateway, Browser Run - Zero Trust, Access, Tunnel, Gateway, Browser Isolation, WAR…  
  inputs: query*
- `cloudflare-docs.migrate_pages_to_workers_guide`: ALWAYS read this guide before migrating Pages projects to Workers.  
  inputs: none
- `gitmcp.match_common_libs_owner_repo_mapping`: Match a library name to an owner/repo. Don't use it if you have an owner and repo already. Use this first if only a library name was provided. If found - you can use owner and repo to call other tools. If not found - try to use the library name directly in other tools.  
  inputs: library*
- `gitmcp.fetch_generic_documentation`: Fetch documentation for any GitHub repository by providing owner and project name  
  inputs: owner*, repo*
- `gitmcp.search_generic_documentation`: Semantically search in documentation for any GitHub repository by providing owner, project name, and search query. Useful for specific queries.  
  inputs: owner*, repo*, query*
- `gitmcp.search_generic_code`: Search for code in any GitHub repository by providing owner, project name, and search query. Returns matching files. Supports pagination with 30 results per page.  
  inputs: owner*, repo*, query*, page
- `gitmcp.fetch_generic_url_content`: Generic tool to fetch content from any absolute URL, respecting robots.txt rules. Use this to retrieve referenced urls (absolute urls) that were mentioned in previously fetched documentation.  
  inputs: url*
- `astro-docs.search_astro_docs`: Search the official Astro framework docs  
  inputs: query*
- `svelte.get-documentation`: Retrieves full documentation content for Svelte 5 or SvelteKit sections. Supports flexible search by title (e.g., "$state", "routing") or file path (e.g., "cli/overview"). Can accept a single section name or an array of sections. Before running this, make sure to analyze the users query, as well as the output from list-sections (which should be ca…  
  inputs: section*
- `svelte.list-sections`: Lists all available Svelte 5 and SvelteKit documentation sections in a structured format. Each section includes a "use_cases" field that describes WHEN this documentation would be useful. You should carefully analyze the use_cases field to determine which sections are relevant for the user's query. The use_cases contain comma-separated keywords de…  
  inputs: none
- `svelte.playground-link`: Generates a Playground link given a Svelte code snippet. Once you have the final version of the code you want to send to the user, ALWAYS ask the user if it wants a playground link to allow it to quickly check the code in the playground before calling this tool. NEVER use this tool if you have written the component to a file in the user project. T…  
  inputs: name*, tailwind*, files*
- `svelte.svelte-autofixer`: Given a svelte component or module returns a list of suggestions to fix any issues it has. This tool MUST be used whenever the user is asking to write svelte code before sending the code back to the user  
  inputs: code*, desired_svelte_version*, async, filename
- `kiwi.search-flight`: # Search for flights Searches Kiwi.com for available flights between two locations for the given dates and passengers. City or airport names are resolved automatically, so call this whenever the user wants to search for flights — whether they gave IATA codes or just place names. ## Result shape Returns `{ query, currency, passengers, resultsCount,…  
  inputs: flyFrom*, flyTo*, departureDate*, departureDateFlexDays, departureDateTo, returnDate, returnDateFlexDays, returnDateTo, adults, children, infants, cabinClass, currency, locale, nights_in_dst_from, nights_in_dst_to, one_for_city, max_sector_stopovers, price_from, price_to, max_fly_duration, select_airlines, exclude_airlines, dtime_from, dtime_to, atime_from, atime_to, ret_dtime_from, ret_dtime_to, ret_atime_from, ret_atime_to, stopover_from, stopover_to, adults_hold_bags, adults_hand_bags, children_hold_bags, children_hand_bags, allow_self_transfer, allow_overnight_stopovers, allow_diff_airport_connection, stopover_airports, exclude_stopover_airports, stopover_countries, exclude_stopover_countries, fly_days, ret_fly_days, sort
- `kiwi.feedback-to-devs`: Send feedback, bug reports, or feature requests about the Kiwi.com search-flight MCP tool to its developers. This channel is ONLY for the flight search tool — search results, pricing, itineraries, filters, or errors in search responses. Do NOT use it for other MCP servers, Claude/app behaviour, account or booking management, voice mode, or unrelat…  
  inputs: text*

(* = required input)

## Requests (162)


### Batch 1

- `sv-02`: Check this Svelte component for problems: <script>let count = 0;</script><button on:click={() => count++}>{count}</button>
- `d-sv-doc-01`: How do snippets replace slots in Svelte 5?
- `c7-02`: Get up-to-date docs for /tanstack/query on how to use useInfiniteQuery.
- `ms-05`: Show a Python snippet using the azure-identity DefaultAzureCredential with Key Vault secrets.
- `x-06`: How is the Svelte compiler organized internally in the sveltejs/svelte repo?
- `d-hf-search-04`: Search the hub for GGUF quantizations of Qwen coder models.
- `d-ms-fetch-01`: Read https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/function-calling and pull out the key steps.
- `d-dw-ask-02`: In encode/starlette, what happens to a request when a middleware raises before calling the next app?
- `d-x-01`: Is there an official MCP server for Azure, and how do I connect it to VS Code?
- `d-c7-query-01`: Using library /pydantic/pydantic, how do I write a model_validator that runs before field validation?
- `dw-01`: In the langchain-ai/langgraph repo, how does the checkpointer persist graph state between steps?
- `d-aws-regions-03`: List every AWS region name alongside its identifier.
- `gm-04`: Semantically search the docs of pydantic/pydantic-ai for how to define a tool with dependencies.
- `d-hf-fs-01`: What models are trending on Hugging Face right now?
- `ms-01`: How do I register an app in Microsoft Entra ID and configure the on-behalf-of flow?
- `gm-05`: Get the content of https://raw.githubusercontent.com/astral-sh/ruff/main/CHANGELOG.md
- `dw-03`: Show me the full generated wiki documentation for the vercel/next.js repository.
- `cf-02`: I want to move my Cloudflare Pages project over to Workers. What steps do I follow?
- `d-as-03`: Astro middleware: how do I read cookies and redirect unauthenticated users?
- `d-gm-code-03`: grep the psf/requests repo for 'merge_environment_settings'.
- `d-c7-query-03`: /websites/react_dev: how does useActionState differ from useFormState?
- `as-02`: Astro: how do I enable server-side rendering with the Node adapter?
- `d-sv-play-01`: Turn this Svelte counter into a playground link I can open: <script>let c = $state(0);</script><button onclick={() => c++}>{c}</button>
- `d-x-10`: How do I write a Svelte 5 component that fetches data on mount?
- `d-gm-map-01`: Which GitHub repo hosts the 'httpx' Python library?
- `d-cf-search-02`: What are the limits on Workers KV value size and writes per second?
- `d-hf-who-01`: Am I authenticated with Hugging Face, and which orgs can I see?
- `dw-05`: What table of contents does the wiki for modelcontextprotocol/python-sdk have?
- `d-cf-search-04`: Can Cloudflare Workers AI run embedding models, and which ones?
- `d-sv-play-02`: Create an online Svelte REPL link for my todo-list component code.
- `d-cf-migrate-02`: Guide me through porting a Pages project to Workers static assets.
- `d-hf-details-03`: What hardware is the Space black-forest-labs/FLUX.1-dev running on and when was it last updated?
- `d-dw-struct-01`: What sections are in the DeepWiki for pola-rs/polars? Just the outline.
- `d-aws-read-01`: Open https://docs.aws.amazon.com/lambda/latest/dg/configuration-memory.html and summarize it.
- `d-dw-ask-01`: Why does the openai/openai-agents-python repo run guardrails in parallel with the first model call? Explain from the code.
- `d-gm-url-02`: What does https://peps.python.org/pep-0758/ propose?
- `hf-05`: Search for datasets of Indian legal judgments on the Hugging Face Hub.
- `d-aws-avail-03`: Is the AWS::SageMaker::Endpoint CloudFormation resource available in me-central-1?
- `d-c7-either-03`: How do I set up a Celery beat schedule in the newest Celery version?
- `d-aws-read-02`: Get me the full text of the AWS docs page at https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lock.html

### Batch 2

- `d-gm-fetchdoc-03`: Get the project docs from github.com/BerriAI/litellm.
- `d-aws-skill-01`: Is there an AWS skill for building an AgentCore agent? Fetch its SKILL.md.
- `d-ms-code-03`: Example Bicep for a storage account with private endpoints, please.
- `d-kw-02`: I'm flexible by two days: Mumbai to London around 5 January, back two weeks later.
- `sv-04`: What documentation sections are available for SvelteKit?
- `d-x-03`: What's the newest version of the transformers library and what changed?
- `x-07`: Plan a weekend trip: what flights leave Chennai for Colombo on Saturday morning?
- `gm-01`: Search the code of the encode/httpx GitHub repo for where the Transport class is defined.
- `dw-02`: List the documentation topics DeepWiki has for facebook/react.
- `d-kw-03`: Family trip: 2 adults and a child from Hyderabad to Kuala Lumpur on 22 December.
- `kw-03`: Report a bug to the flight search tool's developers: the return date was ignored in my last search.
- `d-gm-map-02`: Find the owner/repo for the tailwindcss project.
- `x-03`: How do I set up Durable Objects alarms?
- `d-x-06`: Explain OAuth 2.0 token exchange (RFC 8693) as Entra implements it.
- `cf-03`: What are the R2 storage pricing tiers and free limits?
- `d-dw-ask-03`: How does the scheduler in apache/airflow decide which task instances to queue first?
- `d-ms-code-01`: Show me TypeScript code that uses MSAL to acquire a token silently in a single-page app.
- `d-aws-skill-02`: Get the AWS skill workflow for setting up a static website on S3 with CloudFront.
- `kw-02`: Any direct flights from Bengaluru to Singapore next Friday, returning Sunday?
- `d-gm-code-02`: Search modelcontextprotocol/python-sdk code for where the session id header is read.
- `d-cf-migrate-01`: We're on Cloudflare Pages with Functions. What do we need to change to run the same site on Workers?
- `d-gm-searchdoc-03`: Look through microsoft/autogen's docs for anything about termination conditions.
- `dw-04`: Ask the strands-agents/sdk-python codebase: where are hooks registered before a tool call?
- `d-ms-search-04`: What's the difference between Azure Functions Flex Consumption and Premium plans?
- `d-dw-read-03`: Show me everything DeepWiki has written about the redis/redis codebase.
- `d-as-01`: How do I add view transitions between pages in Astro?
- `d-as-02`: What's the syntax for an Astro island that only hydrates when visible?
- `d-cf-search-03`: How do I set up Zero Trust access for a self-hosted internal app with Cloudflare Tunnel?
- `d-hf-search-02`: Which Spaces demo text-to-SQL with small models?
- `d-ms-code-04`: Python sample for sending a message to an Azure Service Bus queue.
- `x-02`: Where's the rate limit for Lambda concurrent executions documented?
- `d-hf-who-02`: Check what access my current HF token has.
- `d-hf-details-01`: What's the license and parameter count of meta-llama/Llama-3.1-8B-Instruct?
- `d-gm-code-01`: Find the file in fastapi/fastapi where Depends is resolved.
- `d-aws-avail-04`: Before I deploy in Jakarta, check whether Amazon Kendra is offered there.
- `c7-01`: Find the Context7 library ID for Pydantic so I can pull its docs.
- `d-gm-map-03`: I only know the library name 'tRPC'. What's its GitHub location?
- `d-c7-resolve-02`: Which Context7 libraries match 'langgraph'? I need the exact identifier.
- `ms-04`: What are the throttling limits for Azure OpenAI Service deployments?
- `d-ms-search-02`: What are the SLA guarantees for Azure Cosmos DB multi-region writes?

### Batch 3

- `hf-01`: Find the most downloaded text-embedding models on Hugging Face under 500M parameters.
- `d-dw-ask-04`: I'm reading the jlowin/fastmcp source. Where is the auth provider plugged into the HTTP transport?
- `d-c7-query-02`: For /vercel/next.js, show the latest way to define a server action with form data.
- `d-x-05`: How do I rate-limit requests at the edge before they reach my origin?
- `d-x-02`: How do I store embeddings in pgvector on Amazon Aurora PostgreSQL?
- `d-aws-read-03`: Read the Bedrock pricing documentation page https://docs.aws.amazon.com/bedrock/latest/userguide/bedrock-pricing.html for me.
- `d-kw-fb-02`: Send a feature request to the Kiwi MCP team: support multi-city itineraries.
- `d-sv-doc-03`: What does the $effect.pre rune do?
- `x-01`: I need docs on how to stream responses in FastAPI.
- `d-sv-fix-02`: Review my component and tell me what to modernize for runes: <script>import { onMount } from 'svelte'; let items = []; onMount(async () => { items = await (await fetch('/api')).json(); });</script>{#each items as i}<p>{i}</p>{/each}
- `d-c7-either-01`: What's the current recommended way to configure structured logging in structlog?
- `d-ms-fetch-03`: Summarize this page: https://learn.microsoft.com/en-us/entra/identity/conditional-access/overview
- `d-gm-fetchdoc-01`: Fetch the documentation for the GitHub repo pydantic/logfire.
- `aws-02`: Read this page for me: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway.html
- `d-ms-fetch-02`: Grab the full Learn article at https://learn.microsoft.com/en-us/graph/auth-v2-service as markdown.
- `d-ms-search-03`: How do I grant an app Mail.Read application permission and get admin consent in Entra?
- `d-gm-searchdoc-01`: Search the docs of strands-agents/sdk-python for how structured output is configured.
- `d-sv-list-01`: Which Svelte documentation topics exist about stores and state?
- `d-x-09`: What instance types does SageMaker serverless inference support?
- `x-04`: What's the default token lifetime for access tokens issued by the identity platform used by Microsoft 365?
- `d-dw-read-01`: Dump the whole DeepWiki write-up for tiangolo/fastapi, I want to read it offline.
- `d-gm-fetchdoc-02`: Load the README/docs of microsoft/markitdown so I can see how to install it.
- `d-dw-read-02`: Pull the complete generated documentation for the langchain-ai/langgraph repository.
- `kw-01`: Find me the cheapest flight from Hyderabad to Bangkok on 14 November for two adults.
- `d-hf-search-01`: Find open-weight Telugu speech recognition models.
- `d-kw-fb-01`: Tell the flight search tool's developers that results ignore my cabin class filter.
- `d-c7-either-02`: Show me up-to-date examples of Zod discriminated unions.
- `d-gm-searchdoc-02`: In the documentation of run-llama/llama_index, find the section about ingestion pipelines.
- `d-c7-resolve-03`: I want current docs for the Polars Python package. Start by finding the right library.
- `cf-01`: How do I bind a D1 database to a Cloudflare Worker in wrangler.toml?
- `d-aws-regions-02`: What's the region code for AWS in Hyderabad?
- `c7-03`: How do I configure retries in the latest version of the httpx Python library?
- `d-aws-search-03`: How do Bedrock Guardrails handle PII redaction in model outputs?
- `c7-04`: Show current documentation examples for Prisma's createMany with skipDuplicates.
- `d-ms-search-05`: How do I limit who can create Teams in my Microsoft 365 tenant?
- `d-aws-search-01`: How do I give a Lambda function permission to read from a specific DynamoDB table only?
- `d-as-04`: How do I deploy an Astro site to Cloudflare?
- `x-05`: Find a small multilingual reranker I can self-host.
- `d-x-04`: Find me a dataset of Hyderabad real estate prices.
- `d-aws-avail-01`: Can I use Amazon Bedrock in ap-south-2?

### Batch 4

- `d-aws-search-04`: Explain the difference between ECS on Fargate and ECS on EC2 for a batch workload.
- `d-gm-url-03`: Download the text at https://raw.githubusercontent.com/pallets/flask/main/README.md.
- `aws-05`: Which of these regions support the AWS::Bedrock::Agent CloudFormation resource: us-east-1, eu-west-1, ap-south-1?
- `d-sv-fix-03`: Lint this .svelte file for errors: <script>let { count } = $props(); count++;</script>
- `d-ms-search-01`: How do I configure conditional access to require MFA for guest users?
- `d-hf-details-02`: Show the columns and a few sample rows of the dataset openai/gsm8k.
- `d-aws-search-02`: What's the maximum payload size for an Amazon SQS message?
- `d-aws-regions-01`: How many AWS regions are there today, and what are their codes?
- `gm-02`: Which GitHub owner/repo is the 'zod' library?
- `sv-01`: Explain how the $derived rune works in Svelte 5.
- `d-kw-01`: Flights from Delhi to Dubai on 20 December, one adult, economy, cheapest first.
- `d-aws-search-05`: How do I set up an AgentCore Gateway target that points at an OpenAPI spec?
- `as-01`: How do content collections work in Astro and how do I define a schema for them?
- `aws-03`: Which AWS regions exist right now? Give me the full list with codes.
- `d-dw-struct-02`: Give me the topic list for the kubernetes/kubernetes generated wiki so I can pick what to read.
- `d-x-07`: Where in the vllm-project/vllm code is the KV cache block manager?
- `d-x-08`: Book me something cheap to Goa from Bengaluru next weekend.
- `d-sv-list-02`: Give me an index of the SvelteKit docs sections.
- `d-dw-struct-03`: Before I dive in, what areas does the wiki for huggingface/transformers cover?
- `gm-03`: Fetch the README and docs for the github repo astral-sh/uv.
- `aws-07`: Load the AWS skill for deploying a serverless API so I can follow its workflow.
- `d-hf-fs-03`: Show today's daily papers on Hugging Face.
- `d-sv-fix-01`: Is this Svelte 5 code valid? <script>export let name;</script><h1>Hello {name}</h1>
- `hf-03`: Which Hugging Face account and orgs am I logged in as?
- `d-c7-resolve-01`: What's the Context7 id for SQLAlchemy?
- `ms-02`: Give me a C# code sample that calls Microsoft Graph to list a user's calendar events.
- `d-hf-fs-02`: Read the config.json file inside the repo Qwen/Qwen2.5-7B-Instruct.
- `d-cf-search-01`: How do I add a cron trigger to a Worker?
- `hf-02`: Tell me the license, size and tags of the model BAAI/bge-m3.
- `aws-01`: How do I configure inbound OAuth with Microsoft Entra ID for a Bedrock AgentCore Runtime?
- `d-dw-ask-05`: Explain the architecture of the duckdb/duckdb query optimizer at a high level.
- `d-gm-url-01`: Fetch https://modelcontextprotocol.io/specification/2025-06-18/basic/transports and tell me what changed for Streamable HTTP.
- `aws-06`: What's the recommended way to set up S3 cross-region replication with KMS-encrypted objects?
- `d-kw-04`: What's the shortest flight option from Kochi to Doha this Sunday?
- `d-ms-code-02`: I need a PowerShell snippet to list all Azure resource groups with their tags.
- `hf-04`: What are today's trending papers on Hugging Face?
- `d-sv-doc-02`: Show the SvelteKit docs on form actions with progressive enhancement.
- `ms-03`: Fetch https://learn.microsoft.com/en-us/entra/identity-platform/v2-oauth2-on-behalf-of-flow as markdown.
- `aws-04`: Is Amazon Bedrock AgentCore available in ap-south-1 (Mumbai)?
- `d-hf-search-03`: List the top datasets for financial sentiment classification, sorted by downloads.

### Batch 5

- `sv-03`: Make me a shareable playground link for this Svelte snippet so I can send it to a colleague.
- `d-aws-avail-02`: Which regions support the Lambda CreateFunctionUrlConfig API?
