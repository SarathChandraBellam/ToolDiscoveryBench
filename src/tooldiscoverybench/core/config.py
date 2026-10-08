"""YAML config loading with ``${VAR}`` / ``${VAR:-default}`` env expansion, and a tiny .env loader."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml

_ENV_REF = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?::-([^}]*))?\}")


def expand_env(value: Any) -> Any:
    """Recursively replace ``${VAR}`` and ``${VAR:-default}`` in strings."""
    if isinstance(value, str):
        return _ENV_REF.sub(lambda m: os.environ.get(m.group(1), m.group(2) or ""), value)
    if isinstance(value, list):
        return [expand_env(v) for v in value]
    if isinstance(value, dict):
        return {k: expand_env(v) for k, v in value.items()}
    return value


def load_yaml(path: str | Path) -> dict[str, Any]:
    with open(path) as fh:
        data = yaml.safe_load(fh) or {}
    expanded: dict[str, Any] = expand_env(data)
    return expanded


def load_dotenv(path: str | Path = ".env") -> None:
    """Load ``KEY=value`` lines into the environment. Values already set win."""
    env_file = Path(path)
    if not env_file.exists():
        return
    for raw_line in env_file.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
