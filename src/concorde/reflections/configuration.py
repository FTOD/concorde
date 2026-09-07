"""Shared reflection settings validated by initialization and the queue Tool."""

from __future__ import annotations

import copy

from ..capabilities.operation_data import safe_path


def validate_configuration(value: object) -> dict:
    if not isinstance(value, dict) or type(value.get("schema_version")) is not int or value["schema_version"] != 1:
        raise ValueError("reflection-triage config must use schema_version 1")
    if value.get("order") not in ("newest-first", "oldest-first"):
        raise ValueError("config order must be newest-first or oldest-first")
    if not isinstance(value.get("require_approval"), bool):
        raise ValueError("config require_approval must be boolean")
    skip = value.get("skip")
    if not isinstance(skip, list) or any(not isinstance(item, str) for item in skip) or len(skip) != len(set(skip)):
        raise ValueError("config skip must be a unique string list")
    for key in ("plans_dir", "worktrees_dir"):
        safe_path(value.get(key), "/" + key)
    return copy.deepcopy(value)
