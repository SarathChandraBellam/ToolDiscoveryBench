"""Auto option hints: a router-side preprocessing step run once per catalog.

Real catalogs only carry each tool's MCP description and input schema, so nothing here is
hand-written. When a decision router with ``option_text: auto`` loads a catalog it:

1. keeps every tool's MCP description verbatim (same ``desc_chars`` cut as ``plain``);
2. derives ``key_args`` mechanically from the input schema (no LLM);
3. asks an LLM (via OpenRouter, temperature 0, reasoning off) for one ``use_when`` and one
   ``not_when`` line per tool, from catalog data only: the tool's name, description and
   schema, its sibling tools on the same server, and the ids of tools on other servers. It
   never sees benchmark questions or labels.

Step 3 is cached under ``data/cache/auto_hints/<fingerprint>.json``, keyed by the catalog
content, model and prompt, together with its generation cost, so a catalog is processed once.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import time
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

from tooldiscoverybench.core.models import Tool

DEFAULT_MODEL = "anthropic/claude-haiku-5.5"
DEFAULT_CACHE_DIR = "data/cache/auto_hints"
OPENROUTER_CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"
MAX_KEY_ARGS = 6
DESC_CHARS = 2000  # cap very long upstream descriptions in the generation prompt
SIBLING_CHARS = 300
MAX_OTHER_IDS = 200

SYSTEM_PROMPT = """\
You write short routing hints for tools exposed by MCP servers. A routing model reads one
line per tool (the tool's own description plus your hints) and must pick the single tool an
AI agent should call FIRST for a user's request, or decide that no listed tool fits. Your
hints must help it tell similar tools apart.

You are given one target tool (its name, its description from the MCP server and its input
schema), the other tools on the same server (names and descriptions), and the ids of tools
on other servers that may appear in the same catalog.

Write a JSON object with exactly these two string fields:

- "use_when": the kinds of user requests for which this tool is the right FIRST call
  (at most 35 words). Mention any precondition that decides it (e.g. an id, URL or path
  already given).
- "not_when": requests that look related but should go to a different tool, naming that
  tool in parentheses when it is listed, and requests this tool cannot serve even though
  they sound related (at most 50 words).

Rules: use only the information given. Do not invent capabilities. Be specific and
concrete. Output only the JSON object, no prose and no code fences."""

Log = Callable[[str], None]


@dataclass(frozen=True)
class AutoHint:
    use_when: str = ""
    not_when: str = ""


# ------------------------------------------------------------------ mechanical parts
def key_args_from_schema(schema: dict[str, Any], limit: int = MAX_KEY_ARGS) -> str:
    """``repoName (string, required), question (string, required)``; ``none`` if no args."""
    props: dict[str, Any] = schema.get("properties") or {}
    if not props:
        return "none"
    required = [n for n in (schema.get("required") or []) if n in props]
    names = required + [n for n in props if n not in required]
    parts = []
    for name in names[:limit]:
        typ = props[name].get("type") if isinstance(props[name], dict) else None
        typ = "/".join(typ) if isinstance(typ, list) else typ
        bits = [b for b in (typ, "required" if name in required else "") if b]
        parts.append(f"{name} ({', '.join(bits)})" if bits else name)
    if len(names) > limit:
        parts.append(f"+{len(names) - limit} more")
    return ", ".join(parts)


def _sentence(text: str) -> str:
    text = " ".join(text.split())
    return text if not text or text.endswith((".", "!", "?")) else text + "."


def auto_option_text(tool: Tool, hint: AutoHint | None, desc_chars: int) -> str:
    """The plain option text (verbatim description) plus the auto lines and key args."""
    text = f"[{tool.server}] {tool.name}: {tool.short_desc(desc_chars)}"
    if hint is None:
        return text
    extra = []
    if hint.use_when:
        extra.append("Use when: " + _sentence(hint.use_when))
    if hint.not_when:
        extra.append("Not when: " + _sentence(hint.not_when))
    extra.append("Key args: " + _sentence(key_args_from_schema(tool.input_schema)))
    return text + " " + " ".join(extra)


# ------------------------------------------------------------------- LLM generation
def _clip(text: str, n: int) -> str:
    text = " ".join((text or "").split())
    return text if len(text) <= n else text[: n - 1] + "…"


def _schema_view(schema: dict[str, Any]) -> dict[str, Any]:
    props = {
        name: {
            k: (_clip(v, 200) if k == "description" else v)
            for k, v in (p.items() if isinstance(p, dict) else [])
            if k in ("type", "description", "enum")
        }
        for name, p in (schema.get("properties") or {}).items()
    }
    return {"properties": props, "required": schema.get("required") or []}


def user_message(tool: Tool, tools: list[Tool], server_desc: dict[str, str]) -> str:
    siblings = [
        f"- {t.id}: {_clip(t.description, SIBLING_CHARS)}"
        for t in tools
        if t.server == tool.server and t.id != tool.id
    ]
    others = [t.id for t in tools if t.server != tool.server][:MAX_OTHER_IDS]
    return "\n".join(
        [
            f"Server: {tool.server}",
            f"Server description: {server_desc.get(tool.server, '')}",
            "",
            f"Target tool: {tool.id}",
            f"Description: {_clip(tool.description, DESC_CHARS)}",
            f"Input schema: {json.dumps(_schema_view(tool.input_schema))}",
            "",
            "Other tools on the same server:",
            *(siblings or ["(none)"]),
            "",
            "Tools on other servers (ids only): " + ", ".join(others),
        ]
    )


def parse_reply(text: str) -> AutoHint:
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < start:
        raise ValueError("no JSON object in reply")
    data = json.loads(text[start : end + 1])
    fields = {}
    for key in ("use_when", "not_when"):
        value = data.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"missing {key}")
        fields[key] = " ".join(value.split())
    return AutoHint(**fields)


def fingerprint(tools: list[Tool], model: str) -> str:
    payload = json.dumps(
        {
            "model": model,
            "prompt": SYSTEM_PROMPT,
            "tools": [[t.id, t.description, t.input_schema] for t in tools],
        },
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode()).hexdigest()


async def generate_auto_hints(
    tools: list[Tool],
    server_desc: dict[str, str],
    *,
    model: str = DEFAULT_MODEL,
    api_key: str,
    max_usd: float = 0.25,
    concurrency: int = 8,
    transport: httpx.AsyncBaseTransport | None = None,
) -> tuple[dict[str, AutoHint], float]:
    """One temperature-0 call per tool. Returns ``(hints, cost_usd)``; aborts over ``max_usd``."""
    hints: dict[str, AutoHint] = {}
    spent = 0.0
    sem = asyncio.Semaphore(concurrency)
    async with httpx.AsyncClient(
        timeout=120, transport=transport, headers={"Authorization": f"Bearer {api_key}"}
    ) as http:

        async def one(tool: Tool) -> None:
            nonlocal spent
            body = {
                "model": model,
                "temperature": 0,
                "max_tokens": 1000,
                "reasoning": {"enabled": False},
                "usage": {"include": True},
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message(tool, tools, server_desc)},
                ],
            }
            async with sem:
                for attempt in range(3):
                    if spent > max_usd:
                        raise RuntimeError(f"auto hints: spend ${spent:.4f} over ${max_usd}")
                    resp = await http.post(OPENROUTER_CHAT_URL, json=body)
                    resp.raise_for_status()
                    data = resp.json()
                    spent += float((data.get("usage") or {}).get("cost") or 0)
                    try:
                        hints[tool.id] = parse_reply(data["choices"][0]["message"]["content"] or "")
                        return
                    except (ValueError, KeyError, IndexError) as exc:
                        if attempt == 2:
                            raise RuntimeError(f"auto hints: {tool.id}: {exc}") from exc

        await asyncio.gather(*(one(t) for t in tools))
    return hints, spent


async def load_or_generate(
    tools: list[Tool],
    server_desc: dict[str, str],
    *,
    model: str = DEFAULT_MODEL,
    cache_dir: str | Path = DEFAULT_CACHE_DIR,
    api_key_env: str = "OPENROUTER_API_KEY",
    max_usd: float = 0.25,
    transport: httpx.AsyncBaseTransport | None = None,
    log: Log = print,
) -> tuple[dict[str, AutoHint], dict[str, Any]]:
    """Cached per catalog: ``(hints by tool id, generator metadata incl. cost_usd)``."""
    fp = fingerprint(tools, model)
    path = Path(cache_dir) / f"{fp[:16]}.json"
    if path.exists():
        data = json.loads(path.read_text())
        meta = dict(data["generator"], cached=True)
        log(
            f"auto hints: cached {path} ({meta['n_tools']} tools, generated for "
            f"${meta['cost_usd']:.4f} with {meta['model']})"
        )
        return {k: AutoHint(**v) for k, v in data["tools"].items()}, meta

    api_key = os.environ.get(api_key_env, "")
    if not api_key:
        raise RuntimeError(f"option_text: auto needs {api_key_env} to preprocess this catalog")
    started = time.time()
    hints, cost = await generate_auto_hints(
        tools, server_desc, model=model, api_key=api_key, max_usd=max_usd, transport=transport
    )
    meta = {
        "model": model,
        "temperature": 0,
        "reasoning": "disabled",
        "prompt_sha256": hashlib.sha256(SYSTEM_PROMPT.encode()).hexdigest(),
        "catalog_fingerprint": fp,
        "n_tools": len(tools),
        "n_servers": len({t.server for t in tools}),
        "cost_usd": round(cost, 6),
        "seconds": round(time.time() - started, 1),
    }
    by_server: dict[str, list[str]] = defaultdict(list)
    for t in tools:
        by_server[t.server].append(t.id)
    path.parent.mkdir(parents=True, exist_ok=True)
    ordered = {t.id: vars(hints[t.id]) for t in tools}
    path.write_text(json.dumps({"generator": meta, "tools": ordered}, indent=2) + "\n")
    log(f"auto hints: generated {len(hints)} tools for ${cost:.4f} with {model} -> {path}")
    return hints, dict(meta, cached=False)
