"""Build a deepagents agent for one setup and run it on a question or a conversation."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from langchain_core.callbacks import BaseCallbackHandler

from tooldiscoverybench.harness.middleware import DeferredToolsMiddleware, ToolRouterMiddleware
from tooldiscoverybench.harness.models import call_cost
from tooldiscoverybench.harness.routing import ROUTER_SOURCE, BudgetExhaustedError
from tooldiscoverybench.harness.tools import (
    MULTISTEP_STUB_RESULT,
    REQUEST_TOOL,
    SEARCH_TOOL,
    STUB_RESULT,
    CallLog,
    Catalog,
)

WORKSPACE = Path(__file__).parent / "workspace"
SKILL_SOURCES = ["/skills/"]
# deepagents built-ins hidden from the model: write/exec tools make no sense here, and in a
# smoke run free models answered "start my dev server" by exploring the (skills-only)
# filesystem with ls/glob until the step cap. read_file stays: skills need it.
EXCLUDED_BUILTINS = frozenset({"write_file", "edit_file", "execute", "task", "ls", "glob", "grep"})
NO_TOOL = "NO_TOOL"
SELECTOR_SOURCE = "tool_selection"  # metadata.lc_source of LLMToolSelectorMiddleware calls

#: setup -> how catalog tools are exposed
SETUP_KINDS = {
    "all_tools": "all",
    "bm25_search": "search:bm25",
    "regex_search": "search:regex",
    "router_first": "router",
    "router_first_jev": "router",
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
MULTISTEP_PROMPT = (
    "You are a developer assistant agent. Use your tools to carry out the user's request; do "
    "not answer from memory when a tool can help. A request may need several different "
    "integration tools one after another: call each one it needs, in the order the request "
    "asks for, one tool call at a time, then give a one-line final answer. Integration tools "
    "in this environment are stubs that return a short placeholder result; treat each call as "
    "successful and move on to the next step. Do not call a tool the request does not need."
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
SETUP_PROMPTS["router_first_jev"] = SETUP_PROMPTS["router_first"]
_ROUTER_NO_SEARCH = (
    "A router preselected the integration tools most likely to fit this request; they are "
    "loaded. Other integration tools exist but are not loaded."
)
_REQUEST_HINT = (
    f" If no loaded tool fits, first call `{REQUEST_TOOL}` with one sentence describing the "
    "capability you need: the router loads its best matches."
)


@dataclass(frozen=True)
class RouterOptions:
    """How ``ToolRouterMiddleware`` is configured for the router setups."""

    request_tools: bool = False  # expose request_tools(need) for mid-task re-routing
    search_fallback: bool = True  # keep BM25 tool_search as the last resort
    carry: str = "cap"  # tools loaded in earlier turns: cap | keep | replace
    carry_cap: int = 5
    multi_step: bool = False  # multi-step workflow: other base prompt and stub result text


def system_prompt(setup: str, options: RouterOptions) -> str:
    text = SETUP_PROMPTS[setup]
    if SETUP_KINDS[setup] == "router":
        if not options.search_fallback:
            text = _ROUTER_NO_SEARCH
        if options.request_tools:
            text += _REQUEST_HINT
            if options.search_fallback:
                text += f" Use `{SEARCH_TOOL}` only if that does not help."
    return f"{MULTISTEP_PROMPT if options.multi_step else BASE_PROMPT}\n\n{text}"


class UsageCounter(BaseCallbackHandler):
    """Chat-model calls and token usage of one run, split into agent vs router calls."""

    def __init__(self) -> None:
        self.calls = self.input_tokens = self.output_tokens = 0
        self.router_calls = self.router_input_tokens = self.router_output_tokens = 0
        self.errors = 0
        # LangChain's LLMToolSelectorMiddleware: its calls are counted like router calls
        self.selector_calls = self.selector_input_tokens = self.selector_output_tokens = 0
        self.selector_cost_usd = 0.0
        self.selector_latencies_ms: list[float] = []
        self._selector_started: dict[Any, float] = {}
        self.cost_usd = 0.0  # OpenRouter-billed cost of the agent's own model calls
        self._router_runs: set[Any] = set()

    def on_chat_model_start(self, serialized: Any, messages: Any, **kwargs: Any) -> None:
        source = (kwargs.get("metadata") or {}).get("lc_source")
        if source == SELECTOR_SOURCE:
            self.selector_calls += 1
            self._selector_started[kwargs.get("run_id")] = time.perf_counter()
        elif source == ROUTER_SOURCE:
            self.router_calls += 1
            self._router_runs.add(kwargs.get("run_id"))
        else:
            self.calls += 1

    def on_llm_end(self, response: Any, **kwargs: Any) -> None:
        router = kwargs.get("run_id") in self._router_runs
        started = self._selector_started.pop(kwargs.get("run_id"), None)
        if started is not None:
            self.selector_latencies_ms.append((time.perf_counter() - started) * 1000)
        for gens in response.generations:
            for gen in gens:
                usage = getattr(getattr(gen, "message", None), "usage_metadata", None) or {}
                i, o = (
                    int(usage.get("input_tokens", 0) or 0),
                    int(usage.get("output_tokens", 0) or 0),
                )
                if started is not None:
                    self.selector_input_tokens += i
                    self.selector_output_tokens += o
                    self.selector_cost_usd += call_cost(getattr(gen, "message", None)) or 0.0
                elif router:
                    self.router_input_tokens += i
                    self.router_output_tokens += o
                else:
                    self.input_tokens += i
                    self.output_tokens += o
                    self.cost_usd += call_cost(getattr(gen, "message", None)) or 0.0

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
    router_events: list[dict[str, Any]] = field(default_factory=list)  # one per router call
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
    setup: str,
    catalog: Catalog,
    router: Any = None,
    selector_model: Any = None,
    k: int = 3,
    options: RouterOptions | None = None,
) -> Any:
    kind = SETUP_KINDS[setup]
    options = options or RouterOptions()
    if kind == "all":
        return None
    if kind.startswith("search:"):
        return DeferredToolsMiddleware(catalog.names)
    if kind == "router":
        if router is None:
            raise ValueError(f"{setup} needs a router")
        return ToolRouterMiddleware(
            router,
            catalog.tools,
            request_tools=options.request_tools,
            carry=options.carry,  # type: ignore[arg-type]
            carry_cap=options.carry_cap,
        )
    if kind == "langchain_selector":
        from langchain.agents.middleware import LLMToolSelectorMiddleware

        catalog_names = set(catalog.names)

        class CatalogToolSelector(LLMToolSelectorMiddleware):  # type: ignore[type-arg]
            """LangChain's selector, unchanged, choosing among the catalog tools only: the
            agent's own built-ins (read_file for skills, write_todos, ...) are always kept."""

            def _prepare_selection_request(self, request: Any) -> Any:
                self.always_include = [
                    t.name
                    for t in request.tools
                    if not isinstance(t, dict) and t.name not in catalog_names
                ]
                return super()._prepare_selection_request(request)

        return CatalogToolSelector(model=selector_model, max_tools=k, on_parsing_failure="none")
    raise ValueError(setup)


def build_agent(
    model: Any,
    tools: list[Any],
    setup: str,
    max_model_calls: int,
    discovery: Any = None,
    options: RouterOptions | None = None,
    checkpointer: Any = None,
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
        system_prompt=system_prompt(setup, options or RouterOptions()),
        skills=SKILL_SOURCES,
        backend=FilesystemBackend(root_dir=str(WORKSPACE), virtual_mode=True),
        middleware=middleware,
        checkpointer=checkpointer,
    )


def _text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(
            str(part.get("text", "")) if isinstance(part, dict) else str(part) for part in content
        )
    return str(content)


def run_conversation(  # noqa: PLR0912, PLR0915 - one linear loop over turns
    model: Any,
    turns: list[str],
    setup: str,
    catalog: Catalog,
    router: Any = None,
    max_model_calls: int = 8,
    selector_model: Any = None,
    options: RouterOptions | None = None,
    task_timeout: float | None = None,
) -> list[AgentRun]:
    """Run ``turns`` as one conversation on one agent thread; one ``AgentRun`` per turn.

    The step cap applies per turn. ``task_timeout`` is a wall-clock cap per turn: a turn
    that is still running after that many seconds is abandoned and recorded as a
    ``TaskTimeout`` error, so one stuck call cannot stall a run. A turn that errors ends the
    conversation: later turns are returned as error rows without being run.
    """
    from langchain_core.messages import HumanMessage
    from langgraph.checkpoint.memory import InMemorySaver
    from langgraph.errors import GraphRecursionError

    options = options or RouterOptions()
    log = CallLog()
    kind = SETUP_KINDS[setup]
    tools: list[Any] = catalog.stubs(
        log, MULTISTEP_STUB_RESULT if options.multi_step else STUB_RESULT
    )
    if kind.startswith("search:") or (kind == "router" and options.search_fallback):
        variant = kind.split(":", 1)[1] if kind.startswith("search:") else "bm25"
        tools.append(catalog.search_tool(variant, log))
    discovery = discovery_middleware(setup, catalog, router, selector_model, options=options)
    multi = len(turns) > 1
    agent: Any = None
    runs: list[AgentRun] = []
    seen_messages = seen_events = 0
    for question in turns:
        usage = UsageCounter()
        run = AgentRun(CallLog(), usage, 0.0)
        runs.append(run)
        if runs[:-1] and runs[-2].error:
            run.error = "skipped: an earlier turn of this conversation errored"
            continue
        calls_before, searches_before = len(log.calls), len(log.searches)
        state: dict[str, Any] = {}
        started = time.perf_counter()
        try:
            if agent is None:
                agent = build_agent(
                    model,
                    tools,
                    setup,
                    max_model_calls,
                    discovery,
                    options,
                    InMemorySaver() if multi else None,
                )
            config: dict[str, Any] = {
                "callbacks": [usage],
                "recursion_limit": 40 * max_model_calls,
            }
            if multi:
                config["configurable"] = {"thread_id": "conversation"}
            box: dict[str, Any] = {"state": {}, "exc": None}

            def work(
                agent: Any = agent, config: Any = config, question: str = question, box: Any = box
            ) -> None:
                try:
                    # stream full states so a run that dies mid-way still yields its messages
                    for latest in agent.stream(
                        {"messages": [HumanMessage(question)]}, config=config, stream_mode="values"
                    ):
                        box["state"] = latest
                except BaseException as exc:  # noqa: BLE001 - re-raised in the caller below
                    box["exc"] = exc

            worker = threading.Thread(target=work, daemon=True, name="harness-task")
            worker.start()
            worker.join(task_timeout)
            state = box["state"]
            if worker.is_alive():  # abandoned: the daemon thread dies with the process
                run.error = f"TaskTimeout: turn still running after {task_timeout:.0f}s"
            elif box["exc"] is not None:
                raise box["exc"]
        except BudgetExhaustedError:
            raise  # paid-router spend cap: stop the whole run, write no row
        except GraphRecursionError:
            run.hit_step_cap = True
        except Exception as exc:  # noqa: BLE001 - scored as an error row
            run.error = f"{type(exc).__name__}: {exc}"[:800]
        run.latency_ms = (time.perf_counter() - started) * 1000
        run.log = CallLog(log.calls[calls_before:], log.searches[searches_before:])
        messages = list(state.get("messages", []))
        events = list(state.get("tdb_router_events", []))
        run.router_events = events[seen_events:]
        if kind == "all":
            run.initially_loaded = list(catalog.names)
        elif isinstance(discovery, ToolRouterMiddleware):
            run.initially_loaded = [
                *state.get("tdb_carry", []),
                *state.get("tdb_turn_picks", []),
            ]
        if isinstance(discovery, DeferredToolsMiddleware):
            run.loaded_at_end = discovery.loaded(state)
        _read_messages(run, messages[seen_messages:], catalog)
        seen_messages, seen_events = len(messages), len(events)
        run.hit_step_cap = run.hit_step_cap or usage.calls >= max_model_calls
    return runs


def run_agent(
    model: Any,
    question: str,
    setup: str,
    catalog: Catalog,
    router: Any = None,
    max_model_calls: int = 8,
    selector_model: Any = None,
    options: RouterOptions | None = None,
    task_timeout: float | None = None,
) -> AgentRun:
    """One single-turn run."""
    return run_conversation(
        model,
        [question],
        setup,
        catalog,
        router,
        max_model_calls,
        selector_model,
        options,
        task_timeout,
    )[0]


def _read_messages(run: AgentRun, messages: list[Any], catalog: Catalog) -> None:
    """Fill trace, built-in calls, skill reads, refused calls and final text for one turn."""
    from langchain_core.messages import AIMessage, ToolMessage

    ai = [m for m in messages if isinstance(m, AIMessage)]
    known = set(catalog.by_name) | {SEARCH_TOOL, REQUEST_TOOL}
    for msg in messages:
        if (
            isinstance(msg, ToolMessage)
            and msg.name in catalog.by_name
            and "is not loaded" in _text(msg.content)
        ):
            run.unloaded_calls.append(str(msg.name))
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
