"""BM25 baseline: pure Python, no dependencies, zero cost. The floor to beat."""

from __future__ import annotations

import math
import re
import time
from collections import Counter

from tooldiscoverybench.core.models import RouteResult, Tool
from tooldiscoverybench.routers.base import Router

_TOKEN = re.compile(r"[a-z0-9]+")
_CAMEL = re.compile(r"([a-z])([A-Z])")
_STOPWORDS = frozenset(
    (
        "a an the to of for in on and or is are be with by from i me my you your it this "
        "that how do what which can get show give find use using want need please"
    ).split()
)


def tokenize(text: str) -> list[str]:
    """Lowercase tokens; splits snake/kebab/camel case so tool names match prose."""
    text = _CAMEL.sub(r"\1 \2", text).replace("_", " ").replace("-", " ").lower()
    return [tok for tok in _TOKEN.findall(text) if tok not in _STOPWORDS]


def tool_text(tool: Tool, server_desc: dict[str, str]) -> str:
    # tool name repeated to weight it above description words
    return f"{tool.server} {tool.name} {tool.name} {tool.description} {server_desc.get(tool.server, '')}"


class BM25Router(Router):
    calibrated = False

    async def route(
        self, question: str, tools: list[Tool], server_desc: dict[str, str]
    ) -> RouteResult:
        started = time.perf_counter()
        k1 = float(self.cfg.get("k1", 1.5))
        b = float(self.cfg.get("b", 0.75))

        docs = [tokenize(tool_text(t, server_desc)) for t in tools]
        avgdl = sum(map(len, docs)) / max(1, len(docs))
        doc_freq = Counter(term for doc in docs for term in set(doc))
        n_docs = len(docs)
        query = tokenize(question)

        scores: list[tuple[str, float]] = []
        for tool, doc in zip(tools, docs, strict=True):
            tf = Counter(doc)
            score = 0.0
            for term in query:
                if term not in tf:
                    continue
                idf = math.log(1 + (n_docs - doc_freq[term] + 0.5) / (doc_freq[term] + 0.5))
                norm = tf[term] + k1 * (1 - b + b * len(doc) / avgdl)
                score += idf * tf[term] * (k1 + 1) / norm
            scores.append((tool.id, score))
        scores.sort(key=lambda kv: -kv[1])
        return RouteResult(scores, (time.perf_counter() - started) * 1000, False, calls=0)
