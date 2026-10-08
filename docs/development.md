# Development

The project uses [uv](https://docs.astral.sh/uv/) with Python 3.12 (pinned in `.python-version`).

```bash
uv sync                          # core + dev tools
uv sync --extra strands          # + Strands Agents and boto3
uv sync --all-extras             # everything
```

## Checks

```bash
uv run black src tests scripts   # format
uv run ruff check src tests scripts --fix
uv run mypy                      # strict, configured in pyproject.toml
uv run pytest                    # offline unit tests
```

All four must pass before committing. Configuration for each lives in `pyproject.toml`.

## Tests

Unit tests are fully offline:

- Jev uses `httpx.MockTransport`, so request payloads and response parsing are checked
  without a key.
- Strands uses a scripted `Model` subclass that streams tool calls, so both modes run
  without a provider.

Shared fixtures (a four-tool catalog) are in `tests/conftest.py`.

## Layout

```
src/tooldiscoverybench/
  cli.py                  tdb command
  core/                   models.py, config.py
  mcp/                    client.py (Streamable-HTTP initialize + tools/list)
  catalog/                pull.py, store.py, sampling.py
  golden/                 loader.py
  routers/
    base.py, registry.py
    baselines/            bm25.py, embedding.py
    jev/                  client.py (HTTP + dialects), router.py (modes)
    strands/              models.py (provider factory), router.py (modes)
  evaluation/             metrics.py, runner.py, report.py
tests/unit/               one file per area
```
