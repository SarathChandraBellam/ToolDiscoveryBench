"""TypeSafe Jev as a tool router (see ``routers/decisions/router.py`` for the modes)."""

from __future__ import annotations

from typing import Any

from tooldiscoverybench.routers.decisions.router import DecisionRouter
from tooldiscoverybench.routers.decisions.types import DecisionClient
from tooldiscoverybench.routers.jev.client import JevClient


class JevRouter(DecisionRouter):
    default_dialect = "typesafe"

    def build_client(self, cfg: dict[str, Any]) -> DecisionClient:
        return JevClient(
            dialect=cfg.get("dialect", self.default_dialect),
            model=cfg.get("model", "jev-latest"),
            base_url=cfg.get("base_url"),
            path=cfg.get("path"),
            question_type_key=cfg.get("question_type_key"),
            api_key=cfg.get("api_key"),
            api_key_env=cfg.get("api_key_env"),
            timeout=float(cfg.get("timeout", 30)),
            max_retries=int(cfg.get("max_retries", 3)),
            transport=cfg.get("_transport"),
        )


class OpenRouterDecisionsRouter(JevRouter):
    """Any decision model on OpenRouter (``/api/alpha/decisions``), one ``OPENROUTER_API_KEY``.

    ``model: typesafe/jev-1.13`` (pinned), ``~typesafe/jev-latest`` (alias) or
    ``openai/gpt-6-luna-decisions``.
    """

    default_dialect = "openrouter"
