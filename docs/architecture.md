# Architecture

```
configs/servers.yaml ──► catalog.pull ──► data/catalog/public.json ─┐
scripts/make_distractors.py ──────────► distractors_synthetic.json ─┤
                                                                    ▼
data/golden/*.jsonl ──► golden.loader ──► evaluation.runner ◄── catalog.store
                                               │    ▲
                         catalog.sampling ─────┘    │
                                               ▼    │
                                         routers.* (bm25, embedding, jev, strands)
                                               │
                                               ▼
                         evaluation.metrics ──► evaluation.report ──► runs/<ts>/
```

## Packages

| Package | Responsibility |
|---|---|
| `core` | Data types (`Tool`, `GoldenItem`, `RouteResult`) and config loading with `${ENV}` expansion. |
| `mcp` | A small MCP Streamable-HTTP client: `initialize`, then paginated `tools/list`. It handles JSON and SSE responses and times each round-trip. |
| `catalog` | `pull` snapshots servers, `store` reads and writes JSON, `sampling` builds the per-question catalog. |
| `golden` | Loads JSONL question sets and validates gold labels against a catalog. |
| `routers` | The `Router` interface, a lazy registry, and implementations. Each model-backed router lives in its own subpackage. |
| `evaluation` | `runner` orchestrates a run, `metrics` scores rows and summarises, `report` renders Markdown and CSV. |
| `cli` | The `tdb` command. |

## Design decisions

**Identical catalogs for every router.** `sample_catalog` is seeded by
`(question id, size, seed)`, so every router sees exactly the same tools in the same order
for a given question and size. Differences in results come from the router, not the sample.

**Hard negatives first.** When shrinking the catalog, tools from the gold tool's own server
are kept before others. Small catalogs therefore stay hard instead of trivially easy.

**Routers report errors; they don't raise.** A failed call becomes a scored row with an
`error` field, so one flaky request doesn't kill a run, and error rates show up in the report.

**Skip, don't fail, on missing credentials.** `Router.unavailable_reason()` lets the runner
skip a router with a clear message when its key or SDK is missing.

**Lazy optional dependencies.** Strands, fastembed and provider SDKs are imported only when
their router is built, so the core install stays at `httpx`, `pydantic` and `pyyaml`.

**Own MCP client for catalog pulls.** Pulling a catalog only needs `initialize` and
`tools/list`. A ~100-line client avoids churn in SDK transport APIs and gives precise timings.
