"""Operation: run deterministic Spec and configured code checks and record readiness for the
current candidate. Deterministic; runs no agent cognition and selects no context."""

from concorde.harness.operation_state import StateContract, run_host
from concorde.spec import contract_shapes as shapes

from . import external_name

KIND = "host"
PUBLIC = True
CONTEXT_SELECTION = "none"
DETERMINISTIC = True
PROFILE = None
USES = ()
EXTERNAL_NAME = external_name(__name__.rsplit(".", 1)[-1])

REQUEST = shapes.obj(
    {
        **shapes.TASK_FIELDS,
        "run_checks": {"type": "boolean"},
    },
    (*shapes.TASK_OPTIONAL, "run_checks"),
)

RESPONSE = shapes.operation_response()


STATE = StateContract(f"{EXTERNAL_NAME}-request", None)


def run(state, runtime):
    return run_host(EXTERNAL_NAME, state, runtime)
