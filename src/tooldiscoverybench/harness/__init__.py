"""Agent-harness simulation: how tool discovery strategies behave inside a real agent loop.

Built on LangChain ``deepagents``. These setups answer the same questions with the same
catalog of 31 real tools (executed by logging stubs):

``all_tools``           every tool loaded (no discovery; how the gold labels were made)
``bm25_search``         tools deferred; Anthropic-style ``tool_search`` with a BM25 query
``regex_search``        tools deferred; Anthropic-style ``tool_search`` with a regex pattern
``router_first``        ``ToolRouterMiddleware``: a router pick loads 3 tools on every new
                        user message (and on ``request_tools``), BM25 ``tool_search`` as
                        fallback. Router: free model (default) or BM25 shortlist
``router_first_jev``    the same with the paid Jev decision router (needs
                        ``--allow-paid-router``; spend capped)
``langchain_selector``  optional: LangChain's ``LLMToolSelectorMiddleware`` (re-selects 3
                        tools before every model call); not in the default run

See ``README.md`` (section *Agent harness simulation*) and ``python -m
tooldiscoverybench.harness --help``.
"""

SETUPS = (
    "all_tools",
    "bm25_search",
    "regex_search",
    "router_first",
    "router_first_jev",
    "langchain_selector",
)
DEFAULT_SETUPS = SETUPS[:4]
