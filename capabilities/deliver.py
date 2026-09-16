"""Capability: stage a verified change, clean up, and explicitly merge from the primary session.
Deterministic; runs no agent cognition and selects no context."""
from concorde.spec import contract_shapes as shapes

from . import external_name
from concorde.harness.capability_state import StateContract, run_host

PUBLIC = True
CONTEXT_SELECTION = "none"
DETERMINISTIC = True
PROFILE = None
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

RESPONSE = shapes.capability_response()


STATE = StateContract(f"{EXTERNAL_NAME}-request", None)


def run(state, runtime):
    return run_host(EXTERNAL_NAME, state, runtime)
