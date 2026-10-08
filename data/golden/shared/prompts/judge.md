# Judge instructions

You are deciding gold labels for a tool-selection benchmark. For each user request, three AI
agents independently chose which MCP tool to call **first**. Their choices were then executed
against the live servers. Your job is to decide which tool(s) are a correct first call, using
both the tool descriptions and what the executed calls actually returned.

## Inputs (read only these two files; paths are relative to the repository root)

- `data/golden/shared/catalog_for_labelers.json`: the 31 tools,
  with descriptions and input schemas.
- `data/golden/<family>/labeling/judge_pack.jsonl` (the family is given in your task): one record per request. Each has the
  `question`, `executed_first_calls` (tool, how many of the 3 agents picked it first, the
  arguments used, execution `status` and a `result_snippet`), `alternatives_mentioned` (other
  tools the agents said would also be acceptable, with counts) and `mean_confidence`.

Do not open any other file, especially `data/golden/shared/candidates.jsonl`,
`data/golden/shared/drafted_questions_v2.jsonl` or any golden set. Do not execute anything.

## Deciding

For each record:

1. `gold`: every tool_id that is a genuinely correct *first* call for this request. Usually one.
   Include a second tool only when it is truly as good, not merely workable. You may include a
   tool nobody picked if it is clearly correct, but say why in `notes`.
2. `result_useful` for the most-voted executed call:
   - `yes`: the result contains what the request needs (or the right starting point for it).
   - `partial`: relevant but incomplete.
   - `no`: irrelevant or wrong.
   - `unverified`: could not be checked for reasons unrelated to tool choice, such as a quota
     error, a repository the server hasn't indexed, an intentionally skipped side-effect tool,
     or an empty result caused by the data simply not existing.
   A tool can still be the right choice when the result is `unverified`.
3. `question_issue`: `null`, or a short note if the request itself is flawed: a renamed or
   non-existent repo, a false premise, too vague to have a right first call, or wording that
   copies a tool description.
4. `status`:
   - `accept`: you are confident in `gold`.
   - `review`: a human should look. Use this when the agents disagreed and it is a close call,
     when the request is ambiguous, or when `question_issue` is set.
5. `notes`: one short sentence explaining the decision when status is `review`, when gold
   differs from the majority pick, or when gold has more than one tool. Otherwise empty.

## Output

Write one JSON object per line, for every record, to
`data/golden/<family>/labeling/judgments.jsonl`:

```json
{"id": "...", "gold": ["server.tool"], "result_useful": "yes", "question_issue": null, "status": "accept", "notes": ""}
```

Verify there is exactly one line per record, each id appears once, and every gold tool_id exists in
the catalog. Fix any problems before finishing.
