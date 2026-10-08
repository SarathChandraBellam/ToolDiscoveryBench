# Intent

## Why this exists

Agents connected to many MCP servers hit two problems as the tool count grows:

1. **Accuracy.** The model has to pick the right tool from dozens or hundreds of
   overlapping descriptions. Several docs servers all say "search the docs", and many
   servers expose both a search tool and a read tool.
2. **Cost and latency.** Sending every tool schema on every call burns tokens and time.

A common fix is to put a **router** in front of the agent that narrows the catalog to
a few candidates. ToolDiscoveryBench measures how good different routers are at that
job, on real MCP catalogs, with numbers that can be compared side by side.

## The question

> Given a user request and a catalog of MCP tools, how often does a router name the
> tool that should be called **first**, how confident is it when right versus wrong,
> and how long does it take?

## What is being compared

| Router | Why it is interesting |
|---|---|
| **TypeSafe Jev** | A decision model that returns calibrated probabilities over options you define, with no generated text. Cheap, fast, and the probabilities could support an abstain threshold. |
| **Strands Agents** | The status quo: an LLM sees the tools and picks one, either through real tool calling or structured output. |
| **BM25 / embeddings** | Free, local baselines. A router that can't beat these isn't worth a network call. |

## Hypotheses

- H1: Jev's top-1 accuracy is close to an LLM router's at a fraction of the latency and cost.
- H2: Jev's probabilities are calibrated well enough that "confidence below X" reliably flags
  wrong picks, so an agent can fall back to a slower path only when needed.
- H3: Accuracy drops for every router as the catalog grows, and the drop is steepest on
  hard negatives (same-server tools, overlapping docs servers).
- H4: Factoring the decision (server first, then tool) holds accuracy better than one flat
  choice once the catalog passes a few dozen tools.

## Scope

In scope:

- First-tool selection for a single user request.
- Real tool catalogs pulled live from public MCP servers, plus authenticated servers when
  credentials are available.
- Synthetic distractors only to stretch catalog size, flagged so results can be split.

Out of scope for now:

- Multi-step agent loops and tool-call sequencing.
- Whether the chosen tool's output actually answers the question.
- Argument filling (which parameters to pass).

## What "done" looks like for v1

- One command produces a report comparing every router across catalog sizes 10, 30, 75 and 150.
- The report shows top-1 / top-3 accuracy, server accuracy, p50 / p95 latency, tokens, cost
  per 1k questions, and calibration for Jev.
- Results are reproducible: same catalog snapshot, same seed, same per-question catalogs for
  every router.
