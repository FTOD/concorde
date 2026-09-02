"""Deterministic Concorde architecture services."""

from __future__ import annotations

import json
from pathlib import Path


def _package_version() -> str:
    manifest = Path(__file__).resolve().parents[2] / "concorde.json"
    try:
        value = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return "source"
    version = value.get("version") if isinstance(value, dict) else None
    return version if isinstance(version, str) and version else "source"


__version__ = _package_version()
