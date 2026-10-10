"""Execute each distinct (question, tool) call proposed by the labelers against the live MCP
servers and store a result snippet, so labels can be grounded in what the call returned.

    uv run python scripts/labeling/execute_calls.py --family claude

Tools with side effects on third parties are never executed (see NO_EXECUTE).
"""

from __future__ import annotations

import json
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from _common import ROOT, labeling_dir, parse_family_args, read_jsonl, write_jsonl

from tooldiscoverybench.core.config import load_yaml
from tooldiscoverybench.mcp.client import MCPHttpClient

NO_EXECUTE = {"kiwi.feedback-to-devs"}  # sends a message to a third party
SNIPPET_CHARS = 1500
WORKERS = 6


def _text(result: dict[str, Any]) -> str:
    parts = []
    for block in result.get("content", []):
        if block.get("type") == "text":
            parts.append(block.get("text", ""))
        else:
            parts.append(f"[{block.get('type')} block]")
    if not parts and result.get("structuredContent") is not None:
        parts.append(json.dumps(result["structuredContent"]))
    return "\n".join(parts)


def main() -> None:
    args = parse_family_args(__doc__ or "")
    lab = labeling_dir(args.family)
    # the last listed labeler is usually the strongest; its arguments win for a shared tool
    models = list(reversed(args.models))
    servers = load_yaml(ROOT / "configs" / "servers.yaml")["servers"]
    votes = {m: {v["id"]: v for v in read_jsonl(lab / f"votes_{m}.jsonl")} for m in models}
    jobs: dict[tuple[str, str], dict[str, Any]] = {}
    for model in models:
        for qid, vote in votes[model].items():
            tool_id = vote["tool_id"]
            if tool_id and (qid, tool_id) not in jobs:
                jobs[(qid, tool_id)] = {
                    "id": qid,
                    "tool_id": tool_id,
                    "arguments": vote.get("arguments") or {},
                    "args_from": model,
                }

    def run(job: dict[str, Any]) -> dict[str, Any]:
        server, tool = job["tool_id"].split(".", 1)
        if job["tool_id"] in NO_EXECUTE:
            return {**job, "status": "skipped", "reason": "side effect on a third party"}
        client = MCPHttpClient(servers[server]["url"], timeout=90)
        started = time.perf_counter()
        try:
            result = client.call_tool(tool, job["arguments"])
        except Exception as exc:  # noqa: BLE001 - recorded, not fatal
            return {
                **job,
                "status": "error",
                "error": f"{type(exc).__name__}: {exc}"[:500],
                "ms": round((time.perf_counter() - started) * 1000),
            }
        text = _text(result)
        return {
            **job,
            "status": "tool_error" if result.get("isError") else "ok",
            "chars": len(text),
            "snippet": text[:SNIPPET_CHARS],
            "ms": round((time.perf_counter() - started) * 1000),
        }

    print(f"executing {len(jobs)} calls with {WORKERS} workers ...")
    with ThreadPoolExecutor(WORKERS) as pool:
        results = list(pool.map(run, jobs.values()))
    out = lab / "executions.jsonl"
    write_jsonl(out, results)
    counts: dict[str, int] = {}
    for r in results:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    print(counts, "->", out)


if __name__ == "__main__":
    main()
