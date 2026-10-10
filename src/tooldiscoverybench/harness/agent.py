"""Build a deepagents agent for one setup and run it on one question."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from langchain_core.callbacks import BaseCallbackHandler

from tooldiscoverybench.harness.middleware import DeferredToolsMiddleware, ToolRouterMiddleware
from tooldiscoverybench.harness.routing import ROUTER_SOURCE, RouterPick
from tooldiscoverybench.harness.tools import SEARCH_TOOL, CallLog, Catalog

WORKSPACE = Path(__file__).parent / "workspace"
SKILL_SOURCES = ["/skills/"]
# deepagents built-ins hidden from the model: write/exec tools make no sense here, and in a
# smoke run free models answered "start my dev server" by exploring the (skills-only)
# filesystem with ls/glob until the step cap. read_file stays: skills need it.
EXCLUDED_BUILTINS = frozenset({"write_file", "edit_file", "execute", "task", "ls", "glob", "grep"})
NO_TOOL = "NO_TOOL"
ROUTER_SOURCES = {ROUTER_SOURCE, "tool_selection"}  # ours + LangChain's LLMToolSelector

#: setup -> how catalog tools are exposed
SETUP_KINDS = {
    "all_tools": "all",
    "bm25_search": "search:bm25",
    "regex_search": "search:regex",
    "router_first": "router",
    "langchain_selector": "langchain_selector",
}

BASE_PROMPT = (
    "You are a developer assistant agent. Use your tools to make progress on the user's "
    "request; do not answer from memory when a tool can help. Integration tools in this "
    "environment are stubs that return a short placeholder result: once you have called the "
    "right tool, stop and give a one-line final answer. If no available integration tool can "
    "handle the request (it needs an action, account or service none of them provides), call "
    f"no integration tool and reply exactly {NO_TOOL}."
)
_SEARCH_HINT = (
    "Integration tools (documentation search for Astro, Svelte, AWS, Microsoft Learn, "
    "Cloudflare and other libraries; GitHub repository wikis and code search; Hugging Face "
    "Hub; flight search) are deferred: find them with `tool_search`, which loads up to 5 "
    "matching tools you can then call directly. Search again if needed. Search before "
    "concluding that no tool fits."
)
SETUP_PROMPTS = {
    "all_tools": "All integration tools are loaded and can be called directly.",
    "bm25_search": _SEARCH_HINT + " `tool_search` takes a natural-language `query`.",
    "regex_search": _SEARCH_HINT
    + " `tool_search` takes a Python regex `pattern` matched case-insensitively against tool "
    "names, descriptions and argument names/descriptions.",
    "router_first": (
        "A router preselected the integration tools most likely to fit this request; they are "
        "loaded. If none of them fits, other tools are deferred: "
        + _SEARCH_HINT[_SEARCH_HINT.index("find them") :]
        + " `tool_search` takes a natural-language `query`."
    ),
    "langchain_selector": "Relevant integration tools are loaded and can be called directly.",
}


class UsageCounter(BaseCallbackHandler):
    """Chat-model calls and token usage of one run, split into agent vs router calls."""

    def __init__(self) -> None:
        self.calls = self.input_tokens = self.output_tokens = 0
        self.router_calls = self.router_input_tokens = self.router_output_tokens = 0
        self.errors = 0
        self._router_runs: set[Any] = set()

    def on_chat_model_start(self, serialized: Any, messages: Any, **kwargs: Any) -> None:
        if (kwargs.get("metadata") or {}).get("lc_source") in ROUTER_SOURCES:
            self.router_calls += 1
            self._router_runs.add(kwargs.get("run_id"))
        else:
            self.calls += 1

    def on_llm_end(self, response: Any, **kwargs: Any) -> None:
        router = kwargs.get("run_id") in self._router_runs
        for gens in response.generations:
            for gen in gens:
                usage = getattr(getattr(gen, "message", None), "usage_metadata", None) or {}
                i, o = int(usage.get("input_tokens", 0) or 0), int(
                    usage.get("output_tokens", 0) or 0
                )
                if router:
                    self.router_input_tokens += i
                    self.router_output_tokens += o
                else:
                    self.input_tokens += i
                    self.output_tokens += o

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
    initially_loaded: list[str] = field(default_factory=list)
    loaded_at_end: list[str] = field(default_factory=list)
    unloaded_calls: list[str] = field(default_factory=list)
    router_pick: RouterPick | None = None
    skills_read: list[str] = field(default_factory=list)
    builtin_calls: list[str] = field(default_factory=list)
    trace: list[str] = field(default_factory=list)  # compact per-model-step summary


def _register_profile(model: Any) -> None:
    """Hide write/exec/fs-browsing built-ins and the general-purpose subagent."""
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


def discovery_middleware(
    setup: str, catalog: Catalog, router: Any = None, selector_model: Any = None, k: int = 3
) -> Any:
    kind = SETUP_KINDS[setup]
    if kind == "all":
        return None
    if kind.startswith("search:"):
        return DeferredToolsMiddleware(catalog.names)
    if kind == "router":
        if router is None:
            raise ValueError("router_first needs a router")
        return ToolRouterMiddleware(router, catalog.tools)
    if kind == "langchain_selector":
        from langchain.agents.middleware import LLMToolSelectorMiddleware

        builtins = ["read_file", "write_todos"]
        return LLMToolSelectorMiddleware(
            model=selector_model, max_tools=k, always_include=builtins, on_parsing_failure="none"
        )
    raise ValueError(setup)


def build_agent(
    model: Any, tools: list[Any], setup: str, max_model_calls: int, discovery: Any = None
) -> Any:
    from deepagents import create_deep_agent
    from deepagents.backends import FilesystemBackend
    from langchain.agents.middleware import ModelCallLimitMiddleware

    _register_profile(model)
    middleware: list[Any] = [
        ModelCallLimitMiddleware(run_limit=max_model_calls, exit_behavior="end")
    ]
    if discovery is not None:
        middleware.append(discovery)
    return create_deep_agent(
        model=model,
        tools=tools,
        system_prompt=f"{BASE_PROMPT}\n\n{SETUP_PROMPTS[setup]}",
        skills=SKILL_SOURCES,
        backend=FilesystemBackend(root_dir=str(WORKSPACE), virtual_mode=True),
        middleware=middleware,
    )


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
    router: Any = None,
    max_model_calls: int = 8,
    selector_model: Any = None,
) -> AgentRun:
    from langchain_core.messages import HumanMessage

    log = CallLog()
    usage = UsageCounter()
    kind = SETUP_KINDS[setup]
    tools: list[Any] = catalog.stubs(log)
    if kind.startswith("search:") or kind == "router":
        variant = kind.split(":", 1)[1] if kind.startswith("search:") else "bm25"
        tools.append(catalog.search_tool(variant, log))
    discovery = discovery_middleware(setup, catalog, router, selector_model)
    run = AgentRun(log, usage, 0.0)
    if kind == "all":
        run.initially_loaded = list(catalog.names)
    started = time.perf_counter()
    messages: list[Any] = []
    try:
        agent = build_agent(model, tools, setup, max_model_calls, discovery)
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
            run.hit_step_cap = True
        else:
            run.error = f"{type(exc).__name__}: {exc}"[:800]
    run.latency_ms = (time.perf_counter() - started) * 1000
    if isinstance(discovery, ToolRouterMiddleware):
        run.router_pick = discovery.pick
        run.initially_loaded = [e["tool"] for e in discovery.load_events if e["via"] == "router"]
    if isinstance(discovery, DeferredToolsMiddleware):
        run.loaded_at_end = list(discovery.loaded)
        run.unloaded_calls = list(discovery.rejected)
    _read_messages(run, messages, catalog)
    run.hit_step_cap = run.hit_step_cap or usage.calls >= max_model_calls
    return run


def _read_messages(run: AgentRun, messages: list[Any], catalog: Catalog) -> None:
    """Fill trace, built-in calls, skill reads and final text from the run's messages."""
    from langchain_core.messages import AIMessage

    ai = [m for m in messages if isinstance(m, AIMessage)]
    known = set(catalog.by_name) | {SEARCH_TOOL}
    for msg in ai:
        names = [c.get("name", "") for c in msg.tool_calls or []]
        run.trace.append(f"calls={names}" if names else f"text={_text(msg.content)[:120]!r}")
        for call in msg.tool_calls or []:
            name = call.get("name", "")
            if name in known:
                continue
            run.builtin_calls.append(name)
            if name == "read_file":
                path = str((call.get("args") or {}).get("file_path", ""))
                if path.endswith("SKILL.md"):
                    run.skills_read.append(path.split("/")[-2] if "/" in path else path)
    if ai:
        run.final_text = _text(ai[-1].content)[:500]
