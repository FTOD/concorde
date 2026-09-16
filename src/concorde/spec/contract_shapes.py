"""Shared JSON Schema building blocks for capability request/response contracts.

Import-cycle-free: this module imports only dependency-free wire and issue shapes. The top-level ``capabilities/``
package's modules build their own ``REQUEST``/``RESPONSE`` schemas from these shared shapes; the
internal (non-capability) data types — topology design/proposal/application, discovery context,
context snapshots, review internals — stay defined directly in ``contracts.py``.
"""

from __future__ import annotations

from .wire_shapes import ARTIFACT, DIGEST, PATH, STRING, array, obj, typed_schema
from .issue_shapes import BLOCKER

__all__ = [
    "ARTIFACT", "DIGEST", "PATH", "STRING", "array", "obj", "typed_schema",
    "TASK_FIELDS", "TASK_OPTIONAL", "NULLABLE_ID", "BLOCKER", "CHECK_RESULT", "ROUTE",
    "MAIN_OUTCOMES", "WORKTREE_SUMMARY", "COMPONENT_PROGRESS", "WORKSPACE_CONTEXT",
    "task_request", "capability_response",
]

TASK_FIELDS = {"target_id": STRING, "task": STRING, "focus_id": STRING,
               "constraints": array(STRING), "change_id": STRING}
TASK_OPTIONAL = ("focus_id", "constraints", "change_id")
NULLABLE_ID = {"anyOf": [STRING, {"type": "null"}]}
CHECK_RESULT = obj({"check_id": STRING, "target_id": STRING,
    "status": {"enum": ["passed", "failed", "timeout"]}, "exit_code": {"type": "integer"},
    "source_digest": DIGEST, "log_digest": DIGEST})
ROUTE = obj({"target_id": STRING, "focus_id": NULLABLE_ID, "task": STRING,
             "constraints": array(STRING)})
MAIN_OUTCOMES = {"enum": ["expand", "routed", "completed", "spec_incomplete",
                          "unsupported", "conflicting", "failed", "described",
                          "topology_proposed", "topology_prepared", "topology_applied"]}
WORKTREE_SUMMARY = obj({"path": STRING, "branch": NULLABLE_ID, "head": NULLABLE_ID,
    "managed": {"type": "boolean"}, "locked": {"type": "boolean"},
    "change_id": NULLABLE_ID, "target_id": NULLABLE_ID, "task": {"type": "string"},
    "phase": NULLABLE_ID, "status": STRING, "outcome": NULLABLE_ID})
COMPONENT_PROGRESS = obj({"target_id": STRING, "spec_status": STRING,
    "implementation_status": STRING, "outcome": NULLABLE_ID})
WORKSPACE_CONTEXT = obj({"kind": {"enum": ["primary", "change", "unversioned"]},
    "current_worktree": STRING, "current_branch": NULLABLE_ID,
    "primary_worktree": NULLABLE_ID, "primary_branch": NULLABLE_ID,
    "change_id": NULLABLE_ID, "phase": NULLABLE_ID, "status": NULLABLE_ID,
    "outcome": NULLABLE_ID, "blockers": array(BLOCKER), "components": array(COMPONENT_PROGRESS),
    "active_worktrees": array(WORKTREE_SUMMARY)})


def task_request(target_required: bool = True) -> dict:
    """The task-selection request shape shared by every capability.

    ``target_required=True`` (the target is already bound) requires
    ``target_id``; ``target_required=False`` (the router still has to route)
    leaves it optional alongside the other task fields.
    """

    optional = TASK_OPTIONAL if target_required else ("target_id", *TASK_OPTIONAL)
    return obj(TASK_FIELDS, optional)


def capability_response() -> dict:
    """The common response shape shared by capabilities."""

    return obj({
        "target_id": STRING, "focus_id": NULLABLE_ID, "change_id": NULLABLE_ID,
        "context_id": {"anyOf": [DIGEST, {"type": "null"}]},
        "outcome": {"enum": ["completed", "ready", "spec_incomplete", "unsupported",
                              "conflicting", "failed", "described", "delivered"]},
        "answer": {"type": "string"}, "artifacts": array(ARTIFACT), "blockers": array(BLOCKER),
        "checks": array(CHECK_RESULT), "completed_capabilities": array(STRING)})
