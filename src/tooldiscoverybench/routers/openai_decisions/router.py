"""OpenAI Decisions API (``/v1/decisions``) as a tool router.

Same modes and abstention as Jev (see ``routers/decisions/router.py``); only the backend differs.
"""

from __future__ import annotations

from typing import Any

from tooldiscoverybench.routers.decisions.router import DecisionRouter
from tooldiscoverybench.routers.decisions.types import DecisionClient
from tooldiscoverybench.routers.openai_decisions.client import DEFAULT_MODEL, OpenAIDecisionsClient


class OpenAIDecisionsRouter(DecisionRouter):
    def build_client(self, cfg: dict[str, Any]) -> DecisionClient:
        return OpenAIDecisionsClient(
            model=cfg.get("model", DEFAULT_MODEL),
            base_url=cfg.get("base_url"),
            api_key=cfg.get("api_key"),
            api_key_env=cfg.get("api_key_env", "OPENAI_API_KEY"),
            organization=cfg.get("organization"),
            project=cfg.get("project"),
            max_options=int(cfg.get("max_options", 255)),
            timeout=float(cfg.get("timeout", 30)),
            max_retries=int(cfg.get("max_retries", 3)),
            transport=cfg.get("_transport"),
        )
