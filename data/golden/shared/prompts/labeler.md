# Labeler instructions

You are acting as an AI agent that has a set of MCP tools available. For each user request,
decide which tool call you would make **first**, exactly as you would if you were really
handling the request, including the arguments.

## Inputs (read only these two files; paths are relative to the repository root)

- `data/golden/shared/catalog_for_labelers.json`: the 31 available
  tools. Each has `tool_id` (`server.tool`), the server description, the tool description and
  its JSON input schema.
- `data/golden/shared/questions_blind.jsonl`: the user requests,
  one JSON object per line with `id` and `question`.

Do **not** open any other file in the repository, especially `data/golden/shared/candidates.jsonl`,
`data/golden/shared/drafted_questions_v2.jsonl` or any model-family folder under `data/golden/`. Those contain other people's answers, and reading them
would invalidate your labels. Do not call any tools on the network and do not execute anything;
you only decide.

## For every request

1. Pick the single tool you would call first. It must be one of the catalog `tool_id`s.
   If a request genuinely needs no tool from the catalog, use `"tool_id": null`.
2. Fill `arguments` so they satisfy the tool's input schema (required fields present,
   sensible values taken from the request).
3. List `acceptable_alternatives`: other tool_ids that would also be a reasonable *first*
   call. Leave it empty when your pick is clearly the only good first call.
4. Give `confidence` (0 to 1) that your first call is the best one.
5. Give a one-sentence `rationale`.

Judge each request on its own. Follow tool descriptions' own instructions about ordering
(for example, if a tool says another tool must be called before it).

## Output

Write one JSON object per line, for **every** request, to the output path given in your
task, in this exact shape:

```json
{"id": "...", "tool_id": "server.tool", "arguments": {...}, "acceptable_alternatives": ["server.tool"], "confidence": 0.9, "rationale": "..."}
```

Write the file in a few chunks if that's easier, but the final file must have exactly one
line per request, one per request id, valid JSON on each line. After writing, verify the line count and
that every `tool_id` exists in the catalog, then fix any problems.
