"""Typed capability invocation helpers for integration tests."""

from __future__ import annotations

import json
from pathlib import Path

from concorde.spec.typed_data import typed


CONFIGURATION = typed("concorde-capability-configuration", {"model": "openai-codex/gpt-6-astra", "thinking": "medium"})


def invocation(capability: str, data: dict, *, configuration: dict | None = None,
               mode: str = "describe-policy") -> dict:
    from concorde.spec.typed_data import CAPABILITY_CONTRACTS

    return {"type_id": "concorde-capability-invocation", "schema_version": 3,
            "capability_id": capability, "mode": mode,
            "configuration": configuration or CONFIGURATION,
            "input": typed(CAPABILITY_CONTRACTS[capability][0], data)}


def configure(project: Path, configuration: dict | None = None) -> dict:
    value = configuration or CONFIGURATION
    path = project / ".concorde/config.json"
    document = json.loads(path.read_text())
    document["capability_configuration"] = value
    path.write_text(json.dumps(document) + "\n")
    return value
