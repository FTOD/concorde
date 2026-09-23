"""Typed operation invocation helpers for integration tests."""

from __future__ import annotations

import json
from pathlib import Path

from concorde.spec.typed_data import typed

CONFIGURATION = typed(
    "concorde-operation-configuration",
    {"model": "openai-codex/gpt-6-astra", "thinking": "medium"},
)


def invocation(
    operation: str,
    data: dict,
    *,
    configuration: dict | None = None,
    mode: str = "describe-policy",
) -> dict:
    from concorde.operations.catalog import OPERATION_CONTRACTS

    return {
        "type_id": "concorde-operation-invocation",
        "schema_version": 3,
        "operation_id": operation,
        "mode": mode,
        "configuration": configuration or CONFIGURATION,
        "input": typed(OPERATION_CONTRACTS[operation][0], data),
    }


def configure(project: Path, configuration: dict | None = None) -> dict:
    value = configuration or CONFIGURATION
    path = project / ".concorde/config.json"
    document = json.loads(path.read_text())
    document["operation_configuration"] = value
    path.write_text(json.dumps(document) + "\n")
    return value
