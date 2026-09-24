"""Centralized configuration for data paths and project settings.

All Track C modules import paths from here. When Track A/B produce real
data, update config.yaml (or set CONFIG_PATH env var) — no code changes
needed in any module.

Usage:
    from src.config import get_config, get_path

    cfg = get_config()
    corrected = get_path("data.corrected_grid")
"""

import os
from pathlib import Path
from typing import Any

import yaml
_ROOT_DIR = Path(__file__).resolve().parent.parent

try:
    from dotenv import load_dotenv
    load_dotenv(_ROOT_DIR / ".env")
except ImportError:
    pass

_DEFAULT_CONFIG = _ROOT_DIR / "config.yaml"
_config_cache: dict | None = None


def get_config(config_path: str | Path | None = None) -> dict:
    """Load and cache the YAML config.

    Resolution order:
      1. Explicit ``config_path`` argument
      2. ``CONFIG_PATH`` environment variable
      3. ``config.yaml`` at repo root
    """
    global _config_cache

    if _config_cache is not None and config_path is None:
        return _config_cache

    path = Path(
        config_path
        or os.environ.get("CONFIG_PATH", "")
        or _DEFAULT_CONFIG
    )

    if not path.exists():
        raise FileNotFoundError(
            f"Config file not found: {path}. "
            "Set CONFIG_PATH env var or create config.yaml at repo root."
        )

    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    _config_cache = cfg
    return cfg


def get_path(dotted_key: str, config_path: str | Path | None = None) -> Path:
    """Resolve a dotted config key (e.g. 'data.corrected_grid') to an
    absolute Path relative to the repo root.

    Returns:
        Absolute ``Path`` to the file/directory.

    Raises:
        KeyError: if the key is not found in the config.
    """
    cfg = get_config(config_path)
    keys = dotted_key.split(".")
    node: Any = cfg
    for k in keys:
        if not isinstance(node, dict) or k not in node:
            raise KeyError(f"Config key '{dotted_key}' not found (failed at '{k}').")
        node = node[k]

    return _ROOT_DIR / node


def get_root_dir() -> Path:
    """Return the project root directory."""
    return _ROOT_DIR


def reload_config(config_path: str | Path | None = None) -> dict:
    """Force-reload config (useful after Track A/B updates config.yaml)."""
    global _config_cache
    _config_cache = None
    return get_config(config_path)
