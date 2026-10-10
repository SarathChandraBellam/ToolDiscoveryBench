"""Build a deepagents agent for one setup and run it on one question."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from langchain_core.callbacks import BaseCallbackHandler

from tooldiscoverybench.harness.routing import RouterPick
from tooldiscoverybench.harness.tools import SEARCH_TOOL, CallLog, Catalog

WORKSPACE = Path(__file__).parent / "workspace"
SKILL_SOURCES = ["/skills/"]
# deepagents built-ins that make no sense for a read-only tool-selection run
EXCLUDED_BUILTINS = frozenset({"write_file", "edit_file", "execute", "task"})
NO_TOOL = "NO_TOOL"

BASE_PROMPT = (
    "You are a developer assistant agent. Use your tools to make progress on the user's "
    "request; do not answer from memory when a tool can help. Integration tools in this "
    "environment are stubs that return a short placeholder result: once you have called the "
    "right tool, stop and give a one-line final answer. If no available integration tool can "
    "handle the request (it needs an action, account or service none of them provides), call "
    f"no integration tool and reply exactly {NO_TOOL}."
)
SETUP_PROMPTS = {
    "all_tools": "All integration tools are loaded and can be called directly.",
    "bm25_search": (
        f"Integration tools are NOT loaded. Find them with `{SEARCH_TOOL}` (keyword query, "
        "returns up to 5 tools with schemas) and invoke one with `call_tool(name, arguments)`. "
        "You may search more than once. Search before concluding that no tool fits."
    ),
    "router_first": (
        "A router preselected the integration tools most likely to fit this request; they are "
        f"loaded and can be called directly. If none of them fits, use `{SEARCH_TOOL}` "
        "(returns up to 5 more tools with schemas) and `call_tool(name, arguments)`."
    ),
}


class UsageCounter(BaseCallbackHandler):
    """Counts chat-model calls and token usage across one agent run."""

    def __init__(self) -> None:
        self.calls = 0
        self.input_tokens = 0
        self.output_tokens = 0
        self.errors = 0

    def on_chat_model_start(self, serialized: Any, messages: Any, **kwargs: Any) -> None:
        self.calls += 1

    def on_llm_end(self, response: Any, **kwargs: Any) -> None:
        for gens in response.generations:
            for gen in gens:
                usage = getattr(getattr(gen, "message", None), "usage_metadata", None) or {}
                self.input_tokens += int(usage.get("input_tokens", 0) or 0)
                self.output_tokens += int(usage.get("output_tokens", 0) or 0)

    def on_llm_error(self, error: BaseException, **kwargs: Any) -> None:
        self.errors += 1


@dataclass
class AgentRun:
    log: CallLog
    usage: UsageCounter
    latency_ms: float
    final_text: str = ""
    error: str | None = None
    hit_step_cap: bool = False
    bound_tools: list[str] = field(default_factory=list)
    skills_read: list[str] = field(default_factory=list)
    builtin_calls: list[str] = field(default_factory=list)
    trace: list[str] = field(default_factory=list)  # compact per-model-step summary


def _register_profile(model: Any) -> None:
    """Hide write/exec built-ins and the general-purpose subagent for this model."""
    from deepagents import GeneralPurposeSubagentProfile, HarnessProfile, register_harness_profile
    from deepagents._models import get_model_identifier, get_model_provider

    provider, ident = get_model_provider(model), get_model_identifier(model)
    keys = {f"{provider}:{ident}"} if provider and ident else set()
    if provider:
        keys.add(provider)
    for key in keys:
        register_harness_profile(
            key,
            HarnessProfile(
                excluded_tools=EXCLUDED_BUILTINS,
                general_purpose_subagent=GeneralPurposeSubagentProfile(enabled=False),
            ),
        )


def build_agent(model: Any, tools: list[Any], setup: str, max_model_calls: int) -> Any:
    from deepagents import create_deep_agent
    from deepagents.backends import FilesystemBackend
    from langchain.agents.middleware import ModelCallLimitMiddleware

    _register_profile(model)
    return create_deep_agent(
        model=model,
        tools=tools,
        system_prompt=f"{BASE_PROMPT}\n\n{SETUP_PROMPTS[setup]}",
        skills=SKILL_SOURCES,
        backend=FilesystemBackend(root_dir=str(WORKSPACE), virtual_mode=True),
        middleware=[ModelCallLimitMiddleware(run_limit=max_model_calls, exit_behavior="end")],
    )


def setup_tools(
    setup: str, catalog: Catalog, log: CallLog, router_pick: RouterPick | None
) -> tuple[list[Any], list[str]]:
    """LangChain tools to bind for ``setup`` and the catalog ids bound directly."""
    if setup == "all_tools":
        ids = [t.id for t in catalog.tools]
        return catalog.stubs(ids, log), ids
    if setup == "bm25_search":
        return catalog.search_tools(log), []
    if setup == "router_first":
        ids = list(router_pick.tool_ids) if router_pick else []
        return catalog.stubs(ids, log) + catalog.search_tools(log), ids
    raise ValueError(f"unknown setup {setup!r}")


def _text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(
            str(part.get("text", "")) if isinstance(part, dict) else str(part) for part in content
        )
    return str(content)


def run_agent(
    model: Any,
    question: str,
    setup: str,
    catalog: Catalog,
    router_pick: RouterPick | None = None,
    max_model_calls: int = 8,
) -> AgentRun:
    from langchain_core.messages import AIMessage, HumanMessage

    log = CallLog()
    usage = UsageCounter()
    tools, bound = setup_tools(setup, catalog, log, router_pick)
    started = time.perf_counter()
    run = AgentRun(log, usage, 0.0, bound_tools=bound)
    messages: list[Any] = []
    try:
        agent = build_agent(model, tools, setup, max_model_calls)
        # stream full states so a run that dies mid-way still yields its messages
        for state in agent.stream(
            {"messages": [HumanMessage(question)]},
            config={"callbacks": [usage], "recursion_limit": 40 * max_model_calls},
            stream_mode="values",
        ):
            messages = state.get("messages", messages)
    except Exception as exc:  # noqa: BLE001 - scored as an error row
        from langgraph.errors import GraphRecursionError

        if isinstance(exc, GraphRecursionError):
            run.hit_step_cap = True  # the model-call cap normally ends the run first
        else:
            run.error = f"{type(exc).__name__}: {exc}"[:800]
    run.latency_ms = (time.perf_counter() - started) * 1000
    ai = [m for m in messages if isinstance(m, AIMessage)]
    catalog_names = set(catalog.by_name)
    for msg in ai:
        names = [c.get("name", "") for c in msg.tool_calls or []]
        run.trace.append(f"calls={names}" if names else f"text={_text(msg.content)[:120]!r}")
        for call in msg.tool_calls or []:
            name = call.get("name", "")
            if name in catalog_names or name in {SEARCH_TOOL, "call_tool"}:
                continue
            run.builtin_calls.append(name)
            if name == "read_file":
                path = str((call.get("args") or {}).get("file_path", ""))
                if path.endswith("SKILL.md"):
                    run.skills_read.append(path.split("/")[-2] if "/" in path else path)
    if ai:
        run.final_text = _text(ai[-1].content)[:500]
        run.hit_step_cap = run.hit_step_cap or usage.calls >= max_model_calls
    return run
