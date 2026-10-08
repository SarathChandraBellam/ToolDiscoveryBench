# Routers

Every router implements `tooldiscoverybench.routers.base.Router`:

```python
async def route(self, question: str, tools: list[Tool], server_desc: dict[str, str]) -> RouteResult
```

`RouteResult.ranked` is a best-first list of `(tool_id, score)`. Tool ids are `server.tool`.
Set `calibrated = True` only when scores are real probabilities. Set `abstained = True` when
the router decides no tool fits.

## Decision models: Jev and OpenAI Decisions

Both answer typed questions with probabilities instead of generated text, so they share one
router, `routers/decisions/router.py:DecisionRouter`. Each backend is a small client with
`ask(state, questions) -> DecisionResponse`. Each tool becomes one option in a `choice`
question, with its description as the option text.

Abstention (`allow_abstain`, default on): a `__none__` option ("none of the listed tools can
handle this request") is added to the top-level question. When it beats every tool the router
abstains, and its probability is reported as `p_none`.

| Mode | Requests | How it works |
|---|---|---|
| `flat` | 1 (or N+1 above 255 tools) | One choice over all tools. Above Jev's 255-option limit the catalog is chunked; each chunk's top `chunk_keep` tools go to a final round. |
| `factored` | 1 | One request holding a "which server?" question plus a "which tool on server S?" question for every multi-tool server. Combined as P(server) × P(tool \| server). |
| `hierarchical` | 2 | Pick servers first, then choose among the tools of the top `top_servers` servers. Tools on pruned servers stay in the ranking at p = 0. |

### TypeSafe Jev (`type: jev`)

Dialects:

- `typesafe` (default): `POST https://api.typesafe.ai/v1/systemone`. The model id is bare (`jev-latest`) and questions use `type`.
- `decisions`: any `/v1/decisions` gateway such as Bifrost or NanoGPT. Set `base_url`, `path` and `question_type_key`; the model id becomes `typesafe/jev-latest`.

### OpenAI Decisions API (`type: openai_decisions`)

`POST https://api.openai.com/v1/decisions` (public beta), model `gpt-6-luna`. The request
carries `input` (the user request) and `questions`, each `{"type": "choice", "name",
"instructions", "choices": [{"value", "description"}]}`. Answers come back in question order
with `choice`, `probabilities` (a list of `{value, probability}`) and `confidence`; a
`refusal` answer is recorded as an error row. Options: `model`, `base_url`, `api_key_env`
(default `OPENAI_API_KEY`), `organization`, `project`, `max_options` (default 255; OpenAI
does not publish a limit yet).

Both clients retry 429 and 529 responses with exponential backoff. Cost uses `usd_per_m_input`
(Jev $0.042, `gpt-6-luna` $0.10 per 1M input tokens; neither bills output).

## Strands Agents (`type: strands`)

| Mode | How it works |
|---|---|
| `native` | Every tool is registered as a stub Strands tool with its real MCP input schema. The model makes a tool call; a `BeforeToolCallEvent` hook records the first tool and cancels execution, and a one-turn limit stops the loop. |
| `structured` | The catalog goes in the system prompt and the model returns `{tool_id, alternatives, confidence}`. Ids not in the catalog are dropped. Confidence is self-reported. |

Providers: `bedrock` (default), `anthropic`, `openai`, `huggingface`, `litellm`. Tool names
are rewritten to `server__tool` and sanitised to the `[A-Za-z0-9_-]{1,64}` pattern providers
accept.

`huggingface` runs the agent on any chat model served by Hugging Face Inference Providers,
through its OpenAI-compatible router `https://router.huggingface.co/v1` with `HF_TOKEN`
(install with `uv sync --extra huggingface`). Set `model_id` to a Hub id such as
`Qwen/Qwen3-32B`, optionally pinned to a provider: `Qwen/Qwen3-32B:cerebras`.

Abstention: in `native` mode the model is told to call no tool when nothing fits; in
`structured` mode it may return `tool_id: "none"`.

## Baselines

- `bm25`: pure Python. Tokenisation splits snake, kebab and camel case so
  `aws___get_regional_availability` matches "regional availability". The tool name is
  weighted double.
- `embedding`: fastembed `BAAI/bge-small-en-v1.5`. Tool vectors are built once in `setup()`.

## Threshold abstention for any router

Add `abstain_threshold: <score>` to any router entry in `configs/bench.yaml`. The runner
then abstains whenever the top score is below it. This is how BM25 and embedding baselines
are scored on no-tool questions.

## Adding a router

To add another decision API, write a client with `ask()`, `configured`, `api_key_env`,
`max_options` and `aclose()`, then subclass `DecisionRouter` and return it from
`build_client()`. All three modes and abstention come with it.


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
