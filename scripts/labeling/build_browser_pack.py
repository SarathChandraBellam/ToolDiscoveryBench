"""Build a single paste-able file for browser-enabled chat agents (Claude, ChatGPT, Grok, ...)
to act as labelers. Contains the instructions, the tool catalog and the blind questions.

    uv run python scripts/labeling/build_browser_pack.py
    -> data/golden/shared/browser_agent_pack.md

Each agent's JSONL answers go to data/golden/cross/labeling/votes_<agent>.jsonl, then the
normal pipeline runs with --family cross --models claude,chatgpt,grok.
"""

from __future__ import annotations

import json

from _common import SHARED, read_jsonl

DESC_CHARS = 350
BATCH = 40

INSTRUCTIONS = """\
# Tool-selection labeling task

You are helping build a benchmark that measures how well AI agents pick the right MCP
(Model Context Protocol) tool. Act as an agent that is connected to the public, no-auth MCP
servers listed below. For each user request, decide which tool you would call **first**,
with arguments, exactly as you would if you were really handling it.

## Step 1: understand the servers (use your browser)

All servers below are public and need no login. Before labeling, use your browser to learn
what each one is for, so your choices are grounded in what the servers actually do:

{server_table}

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

Reply in batches of {batch} requests, in the order given. Each batch is ONE fenced code block
of JSON Lines, one object per line, nothing else inside the block:

```jsonl
{{"id": "...", "tool_id": "server.tool", "arguments": {{}}, "acceptable_alternatives": [], "confidence": 0.9, "rationale": "...", "evidence_url": null}}
```

After each batch, stop and wait until I reply "continue". Put the Server notes before the
first batch. Every request id must appear exactly once across all batches.
"""


def main() -> None:
    tools = json.loads((SHARED / "catalog_for_labelers.json").read_text())
    questions = read_jsonl(SHARED / "questions_blind.jsonl")

    servers: dict[str, str] = {}
    for t in tools:
        servers.setdefault(t["server"], t["server_description"])
    server_table = "\n".join(f"- **{s}**: {d}" for s, d in servers.items())

    lines = [INSTRUCTIONS.format(server_table=server_table, batch=BATCH)]
    lines.append(f"## Tool catalog ({len(tools)} tools)\n")
    for t in tools:
        schema = t["input_schema"] or {}
        props = list((schema.get("properties") or {}).keys())
        required = schema.get("required") or []
        desc = " ".join(t["description"].split())
        if len(desc) > DESC_CHARS:
            desc = desc[: DESC_CHARS - 1] + "…"
        inputs = ", ".join(f"{p}*" if p in required else p for p in props) or "none"
        lines.append(f"- `{t['tool_id']}`: {desc}  \n  inputs: {inputs}")
    lines.append("\n(* = required input)\n")

    lines.append(f"## Requests ({len(questions)})\n")
    for i, q in enumerate(questions):
        if i % BATCH == 0:
            lines.append(f"\n### Batch {i // BATCH + 1}\n")
        lines.append(f"- `{q['id']}`: {q['question']}")

    out = SHARED / "browser_agent_pack.md"
    out.write_text("\n".join(lines) + "\n")
    print(f"{len(tools)} tools, {len(questions)} questions -> {out} ({out.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
