"""Helpers shared by the composite routers."""

from __future__ import annotations

from typing import Any

from tooldiscoverybench.routers.base import Router

#: keys the runner consumes from a router entry; a child router must not receive them
CHILD_DROP_KEYS = {"concurrency", "usd_per_m_input", "abstain_threshold", "enabled"}


def build_child(spec: Any, role: str) -> Router:
    """Build a nested router from an inline config mapping (``type`` plus its options)."""
    from tooldiscoverybench.routers.registry import build_router

    if not isinstance(spec, dict) or "type" not in spec:
        raise ValueError(f"{role}: expected an inline router config with a 'type' key")
    cfg = {k: v for k, v in spec.items() if k not in CHILD_DROP_KEYS}
    cfg.setdefault("name", role)
    return build_router(cfg)
