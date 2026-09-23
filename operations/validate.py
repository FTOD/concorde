"""Operation: run deterministic Spec and configured code checks and record readiness for the
current candidate. Deterministic; runs no agent cognition and selects no context."""

from concorde.operations import shapes


KIND = "host"
PUBLIC = True
DETERMINISTIC = True
OWNER = "module.validation"
AGENTS = ()
USES = ()

REQUEST = shapes.obj(
    {
        **shapes.TASK_FIELDS,
        "run_checks": {"type": "boolean"},
    },
    (*shapes.TASK_OPTIONAL, "run_checks"),
)

RESPONSE = shapes.operation_response()
REQUEST_VERSION = 1
RESPONSE_VERSION = 3


MUTATION = {"policy": "always", "actions": []}
WORKSPACE = "candidate"
TARGET = {
    "selection": "provider-hook",
    "hook": "concorde.validation.validate:select_target",
}
DEFAULT_TASK = None
CONFIGURATION = "stored"
ENTRY_POINT = "concorde.validation.validate:run"
