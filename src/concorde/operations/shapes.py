"""Shared building blocks of the capabilities' request and response schemas.

Each Operation declaration under ``operations/`` builds its own ``REQUEST`` and ``RESPONSE`` from
these shapes and the owners' shapes; the catalog registers them as typed values.
"""

from __future__ import annotations

from ..harness.checks import CHECK_RESULT
from ..issues.shapes import BLOCKER
from ..spec.typed_data import (
    ARTIFACT,
    DIGEST,
    PATH,
    STRING,
    array,
    obj,
    typed_schema,
)

__all__ = [
    "ARTIFACT",
    "BLOCKER",
    "CHECK_RESULT",
    "DIGEST",
    "NULLABLE_ID",
    "PATH",
    "STRING",
    "TASK_FIELDS",
    "TASK_OPTIONAL",
    "array",
    "obj",
    "operation_response",
    "task_request",
    "typed_schema",
]

TASK_FIELDS = {
    "target_id": STRING,
    "task": STRING,
    "focus_id": STRING,
    "constraints": array(STRING),
    "change_id": STRING,
}
TASK_OPTIONAL = ("focus_id", "constraints", "change_id")
NULLABLE_ID = {"anyOf": [STRING, {"type": "null"}]}


def task_request(target_required: bool = True) -> dict:
    """The task-selection request shape shared by the Module-bound capabilities.

    ``target_required=True`` (the target is already bound) requires ``target_id``;
    ``target_required=False`` (a bookkeeping request may omit selection) leaves it optional
    alongside the other task fields.
    """

    optional = TASK_OPTIONAL if target_required else ("target_id", *TASK_OPTIONAL)
    return obj(TASK_FIELDS, optional)


def operation_response() -> dict:
    """The common response shape shared by capabilities."""

    return obj(
        {
            "target_id": STRING,
            "focus_id": NULLABLE_ID,
            "change_id": NULLABLE_ID,
            "context_id": {"anyOf": [DIGEST, {"type": "null"}]},
            "outcome": {
                "enum": [
                    "completed",
                    "ready",
                    "spec_incomplete",
                    "unsupported",
                    "conflicting",
                    "failed",
                    "described",
                    "delivered",
                ]
            },
            "answer": {"type": "string"},
            "artifacts": array(ARTIFACT),
            "blockers": array(BLOCKER),
            "checks": array(CHECK_RESULT),
            "completed_operations": array(STRING),
        }
    )
