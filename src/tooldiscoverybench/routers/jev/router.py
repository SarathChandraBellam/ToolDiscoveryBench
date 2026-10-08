"""TypeSafe Jev as a tool router (see ``routers/decisions/router.py`` for the modes)."""

from __future__ import annotations

from typing import Any

from tooldiscoverybench.routers.decisions.router import DecisionRouter
from tooldiscoverybench.routers.decisions.types import DecisionClient
from tooldiscoverybench.routers.jev.client import JevClient


class JevRouter(DecisionRouter):
    def build_client(self, cfg: dict[str, Any]) -> DecisionClient:
        return JevClient(
            dialect=cfg.get("dialect", "typesafe"),
            model=cfg.get("model", "jev-latest"),
            base_url=cfg.get("base_url"),
            path=cfg.get("path"),
            question_type_key=cfg.get("question_type_key"),
            api_key=cfg.get("api_key"),
            api_key_env=cfg.get("api_key_env", "TYPESAFE_API_KEY"),
            timeout=float(cfg.get("timeout", 30)),
            max_retries=int(cfg.get("max_retries", 3)),
            transport=cfg.get("_transport"),
        )
