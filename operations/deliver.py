"""Operation: stage a verified change, clean up, and explicitly merge from the primary session.
Deterministic; runs no agent cognition and selects no context."""

from concorde.operations import shapes


KIND = "host"
PUBLIC = True
DETERMINISTIC = True
OWNER = "module.delivery"
AGENTS = ()
USES = ()

REQUEST = shapes.obj(
    {
        "change_id": shapes.STRING,
        "target_id": shapes.STRING,
        "task": shapes.STRING,
        "focus_id": shapes.STRING,
        "constraints": shapes.array(shapes.STRING),
        "keep_worktree": {"type": "boolean"},
        "merge_primary": {"type": "boolean"},
    },
    ("target_id", "task", "focus_id", "constraints", "keep_worktree", "merge_primary"),
)

RESPONSE = shapes.operation_response()
REQUEST_VERSION = 1
RESPONSE_VERSION = 3


MUTATION = {"policy": "always", "actions": []}
WORKSPACE = "delivery-session"
TARGET = {"selection": "none", "hook": None}
DEFAULT_TASK = None
CONFIGURATION = "stored"
ENTRY_POINT = "concorde.harness.worktree_delivery:run"
