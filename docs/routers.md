# Routers

Every router implements `tooldiscoverybench.routers.base.Router`:

```python
async def route(self, question: str, tools: list[Tool], server_desc: dict[str, str]) -> RouteResult
```

`RouteResult.ranked` is a best-first list of `(tool_id, score)`. Tool ids are `server.tool`.
Set `calibrated = True` only when scores are real probabilities.

## TypeSafe Jev (`type: jev`)

Jev answers typed questions (`choice`, `score`, `noul`) with probabilities instead of text.
Each tool becomes one option in a `choice` question, with its description as the option text.

| Mode | Requests | How it works |
|---|---|---|
| `flat` | 1 (or N+1 above 255 tools) | One choice over all tools. Above Jev's 255-option limit the catalog is chunked; each chunk's top `chunk_keep` tools go to a final round. |
| `factored` | 1 | One request holding a "which server?" question plus a "which tool on server S?" question for every multi-tool server. Combined as P(server) × P(tool \| server). |
| `hierarchical` | 2 | Pick servers first, then choose among the tools of the top `top_servers` servers. Tools on pruned servers stay in the ranking at p = 0. |

Dialects:

- `typesafe` (default): `POST https://api.typesafe.ai/v1/systemone`. The model id is bare (`jev-latest`) and questions use `type`.
- `decisions`: any `/v1/decisions` gateway such as Bifrost or NanoGPT. Set `base_url`, `path` and `question_type_key`; the model id becomes `typesafe/jev-latest`.

Retries 429 and 529 responses with exponential backoff. Cost uses `usd_per_m_input`.

## Strands Agents (`type: strands`)

| Mode | How it works |
|---|---|
| `native` | Every tool is registered as a stub Strands tool with its real MCP input schema. The model makes a tool call; a `BeforeToolCallEvent` hook records the first tool and cancels execution, and a one-turn limit stops the loop. |
| `structured` | The catalog goes in the system prompt and the model returns `{tool_id, alternatives, confidence}`. Ids not in the catalog are dropped. Confidence is self-reported. |

Providers: `bedrock` (default), `anthropic`, `openai`, `litellm`. Tool names are rewritten to
`server__tool` and sanitised to the `[A-Za-z0-9_-]{1,64}` pattern providers accept.

## Baselines

- `bm25`: pure Python. Tokenisation splits snake, kebab and camel case so
  `aws___get_regional_availability` matches "regional availability". The tool name is
  weighted double.
- `embedding`: fastembed `BAAI/bge-small-en-v1.5`. Tool vectors are built once in `setup()`.

## Adding a router

1. Subclass `Router` and implement `route()`. Override `unavailable_reason()` if it needs
   credentials, `setup()` if it builds an index, and `aclose()` if it holds clients.
2. Register it:

   ```python
   from tooldiscoverybench.routers import register
   register("myrouter", "mypackage.module:MyRouter")
   ```

   or add it to `_REGISTRY` in `routers/registry.py`.
3. Add an entry to `configs/bench.yaml` with `type: myrouter`. Every other key in the entry
   is passed to the constructor.
4. Add a unit test with a fake transport or model. See `tests/unit/test_jev.py`.
