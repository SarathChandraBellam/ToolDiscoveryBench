"""Dense-retrieval baseline using fastembed (local ONNX, no API key).

Install with ``uv sync --extra embed``. Tool vectors are computed once in ``setup``,
mirroring a real tool-search index; only the query is embedded per question.
"""

from __future__ import annotations

import time
from typing import Any

from tooldiscoverybench.core.models import RouteResult, Tool
from tooldiscoverybench.routers.base import Router

DEFAULT_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


class EmbeddingRouter(Router):
    calibrated = False

    def __init__(self, **cfg: Any) -> None:
        super().__init__(**cfg)
        self._model: Any = None
        self._np: Any = None
        self._vectors: dict[str, Any] = {}

    def unavailable_reason(self) -> str | None:
        try:
            import fastembed  # noqa: F401
        except ImportError:
            return "fastembed not installed (uv sync --extra embed)"
        return None

    async def setup(self, all_tools: list[Tool], server_desc: dict[str, str]) -> None:
        import numpy as np
        from fastembed import TextEmbedding

        self._np = np
        self._model = TextEmbedding(self.cfg.get("model", "BAAI/bge-small-en-v1.5"))
        texts = [
            f"{t.server} {t.name}: {t.short_desc(600)} ({server_desc.get(t.server, '')})"
            for t in all_tools
        ]
        vectors = np.array(list(self._model.embed(texts)))
        self._vectors = {
            t.id: v / np.linalg.norm(v) for t, v in zip(all_tools, vectors, strict=True)
        }

    async def route(
        self, question: str, tools: list[Tool], server_desc: dict[str, str]
    ) -> RouteResult:
        np = self._np
        started = time.perf_counter()
        prefix = self.cfg.get("query_prefix", DEFAULT_QUERY_PREFIX)
        query = np.array(next(iter(self._model.embed([prefix + question]))))
        query /= np.linalg.norm(query)
        scores = sorted(
            ((t.id, float(self._vectors[t.id] @ query)) for t in tools), key=lambda kv: -kv[1]
        )
        return RouteResult(scores, (time.perf_counter() - started) * 1000, False, calls=0)
