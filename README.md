# ToolDiscoveryBench

How accurately, and how fast, can a router pick the right MCP tool for a request?

ToolDiscoveryBench runs the same golden questions against the same real MCP tool catalogs
through several routers and reports accuracy, latency, cost and calibration side by side:

- **TypeSafe Jev**: a decision model returning calibrated probabilities over tool choices
- **Strands Agents**: an LLM picks the tool, via real tool calling or structured output
- **BM25** and **embeddings**: free local baselines

Why this matters and what it tries to answer: [intent.md](intent.md).

## Quick start

```bash
uv sync --extra strands          # Python 3.12, core + Strands + dev tools
cp .env.example .env             # add TYPESAFE_API_KEY, AWS credentials, ...

uv run tdb pull                  # snapshot tools/list from configs/servers.yaml
uv run python scripts/make_distractors.py
uv run tdb validate              # gold labels still match live tool names?
uv run tdb run --limit 5         # smoke test
uv run tdb run                   # full run -> runs/<timestamp>/report.md
uv run tdb ask "Is AgentCore available in Mumbai?" --router jev-factored
```

Routers whose keys, credentials or SDKs are missing are skipped with a message, not scored
as failures.

## What a run measures

Each question is shown to every router with its gold tool(s) plus seeded distractors at
catalog sizes 10, 30, 75 and 150. Same-server tools are added first because they are the
hardest negatives, and every router sees the identical catalog.

| | |
|---|---|
| Accuracy | top-1, top-3, MRR, right-server rate, top-1 by question tag |
| Speed | p50 / p95 latency per question, upstream calls per question |
| Cost | input tokens, USD per 1k questions |
| Calibration (Jev) | ECE, Brier, mean confidence when right vs wrong |

Details: [docs/metrics.md](docs/metrics.md).

## Routers

| Router | Modes |
|---|---|
| `jev` | `flat` (one choice, tournament above 255 tools), `factored` (server × tool in one request), `hierarchical` (server call, then tool call). Native TypeSafe API or any `/v1/decisions` gateway. |
| `strands` | `native` (stub tools with real MCP schemas, first tool call recorded), `structured` (pydantic pick). Bedrock, Anthropic, OpenAI or LiteLLM. |
| `bm25` | Pure Python, case-splitting tokeniser |
| `embedding` | fastembed `bge-small-en-v1.5`, local |

Details and how to add your own: [docs/routers.md](docs/routers.md).

## Catalog and golden set

- 10 no-auth public MCP servers, 31 real tools: DeepWiki, Context7, AWS Knowledge,
  Microsoft Learn, Hugging Face, Cloudflare Docs, GitMCP, Astro, Svelte, Kiwi.
- GitHub and a Microsoft 365 server are configured and switch on with tokens.
- 110 synthetic `syn-*` distractor tools let catalogs grow to 150.
- 50 questions covering every real tool, tagged by difficulty.

Details: [docs/golden-set.md](docs/golden-set.md).

## First baseline (BM25)

| Catalog size | 10 | 30 | 75 | 150 |
|---|---:|---:|---:|---:|
| top-1 | 70% | 64% | 46% | 46% |

This is the floor model-backed routers need to beat.

## Project layout

```
configs/      servers.yaml (MCP servers), bench.yaml (routers, sizes)
data/         catalog/ (pulled + synthetic), golden/ (questions)
docs/         architecture, routers, metrics, golden set, development
scripts/      make_distractors.py
src/tooldiscoverybench/
  core/ mcp/ catalog/ golden/ routers/ evaluation/ cli.py
tests/unit/
```

Architecture: [docs/architecture.md](docs/architecture.md) · Development: [docs/development.md](docs/development.md)

## Development

```bash
uv run black src tests scripts
uv run ruff check src tests scripts
uv run mypy
uv run pytest
```

## License

MIT
