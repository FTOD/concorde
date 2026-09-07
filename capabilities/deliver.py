"""Lifecycle: from the primary worktree, verify, merge and clean up one ready candidate change.
Deterministic; runs no agent cognition and selects no context."""
from concorde.capabilities import contract_shapes as shapes

from . import external_name

CLASS = "lifecycle"
ROLES = ()
USES = ()
EXTERNAL_NAME = external_name(__name__.rsplit(".", 1)[-1])

REQUEST = shapes.obj({
    "change_id": shapes.STRING,
    "target_id": shapes.STRING,
    "task": shapes.STRING,
    "focus_id": shapes.STRING,
    "constraints": shapes.array(shapes.STRING),
    "keep_worktree": {"type": "boolean"},
}, ("target_id", "task", "focus_id", "constraints", "keep_worktree"))

RESPONSE = shapes.stage_response()


def run(host, configuration, request):
    from concorde.capabilities.operation_service import run_operation
    return run_operation(EXTERNAL_NAME, configuration, request, host_context=host)
