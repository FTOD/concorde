"""Lifecycle: stage a verified change, clean up, and explicitly merge from the primary session.
Deterministic; runs no agent cognition and selects no context."""
from concorde.spec import contract_shapes as shapes

from . import external_name

CLASS = "lifecycle"
DETERMINISTIC = True
AGENTS = ()
USES = ()
EXTERNAL_NAME = external_name(__name__.rsplit(".", 1)[-1])

REQUEST = shapes.obj({
    "change_id": shapes.STRING,
    "target_id": shapes.STRING,
    "task": shapes.STRING,
    "focus_id": shapes.STRING,
    "constraints": shapes.array(shapes.STRING),
    "keep_worktree": {"type": "boolean"},
    "merge_primary": {"type": "boolean"},
}, ("target_id", "task", "focus_id", "constraints", "keep_worktree", "merge_primary"))

RESPONSE = shapes.stage_response()


def run(host, configuration, request):
    from concorde.development.capability_service import run_capability
    return run_capability(EXTERNAL_NAME, configuration, request, host_context=host)
