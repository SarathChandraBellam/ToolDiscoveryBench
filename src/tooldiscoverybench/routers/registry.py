"""Router registry: config ``type:`` -> router class (imported lazily)."""

from __future__ import annotations

import importlib
from typing import Any

from tooldiscoverybench.routers.base import Router

_REGISTRY: dict[str, str] = {
    "bm25": "tooldiscoverybench.routers.baselines.bm25:BM25Router",
    "embedding": "tooldiscoverybench.routers.baselines.embedding:EmbeddingRouter",
    "jev": "tooldiscoverybench.routers.jev.router:JevRouter",
    "openrouter": "tooldiscoverybench.routers.jev.router:OpenRouterDecisionsRouter",
    "openai_decisions": "tooldiscoverybench.routers.openai_decisions.router:OpenAIDecisionsRouter",
    "strands": "tooldiscoverybench.routers.strands.router:StrandsRouter",
}


def register(type_name: str, dotted_path: str) -> None:
    """Register a router class as ``"package.module:ClassName"``."""
    _REGISTRY[type_name] = dotted_path


def available_types() -> list[str]:
    return sorted(_REGISTRY)


def build_router(cfg: dict[str, Any]) -> Router:
    cfg = dict(cfg)
    type_name = cfg.pop("type", cfg.get("name"))
    name = cfg.pop("name", type_name)
    cfg.pop("enabled", None)
    if type_name not in _REGISTRY:
        raise ValueError(f"unknown router type {type_name!r}; known: {available_types()}")
    module_name, class_name = _REGISTRY[type_name].split(":")
    cls = getattr(importlib.import_module(module_name), class_name)
    router: Router = cls(**cfg)
    router.name = str(name)
    return router
