"""Agent-harness simulation: how tool discovery strategies behave inside a real agent loop.

Built on LangChain ``deepagents``. Three setups answer the same questions with the same
catalog of 31 real tools (executed by logging stubs):

``all_tools``     every tool bound to the agent (how the gold labels were made)
``bm25_search``   tools deferred; the agent calls ``tool_search`` (repo BM25) and ``call_tool``
``router_first``  one upfront router call binds its top 3 tools, ``tool_search`` as fallback

See ``README.md`` (section *Agent harness simulation*) and ``python -m
tooldiscoverybench.harness --help``.
"""

SETUPS = ("all_tools", "bm25_search", "router_first")
