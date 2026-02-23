from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

DEFAULT_CONFIG_PATHS = [Path.cwd() / "config" / "antennalab.yaml"]


def find_config(explicit_path: str | Path | None = None) -> Path | None:
    if explicit_path:
        path = Path(explicit_path).expanduser()
        return path if path.exists() else None
    for path in DEFAULT_CONFIG_PATHS:
        if path.exists():
            return path
    return None


def load_config(explicit_path: str | Path | None = None) -> tuple[dict[str, Any], Path | None]:
    config_path = find_config(explicit_path)
    if config_path is None:
        return {}, None
    with config_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return data, config_path
