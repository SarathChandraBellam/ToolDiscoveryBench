"""Read and write catalog snapshots (JSON)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tooldiscoverybench.core.models import Tool


def save_catalog(catalog: dict[str, Any], path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(catalog, indent=2))


def load_catalog(*paths: str | Path) -> tuple[list[Tool], dict[str, str]]:
    """Load and merge catalog files. Returns ``(tools, server_descriptions)``."""
    tools: list[Tool] = []
    server_desc: dict[str, str] = {}
    seen: set[str] = set()
    for path in paths:
        data = json.loads(Path(path).read_text())
        synthetic = bool(data.get("synthetic", False))
        for server_name, server in data["servers"].items():
            fallback = (server.get("instructions") or "")[:300]
            server_desc.setdefault(server_name, server.get("description") or fallback)
            for raw in server.get("tools", []):
                tool = Tool(
                    server=server_name,
                    name=raw["name"],
                    description=raw.get("description", ""),
                    input_schema=raw.get("input_schema", {}),
                    synthetic=synthetic,
                )
                if tool.id not in seen:
                    seen.add(tool.id)
                    tools.append(tool)
    return tools, server_desc
