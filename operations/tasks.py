"""Operation: turn an admitted plan into tasks with observable acceptance conditions."""

from concorde.harness.operation_state import StateContract, run_host
from concorde.operations import shapes

from . import external_name

KIND = "agent-entry"
PUBLIC = True
CONTEXT_SELECTION = "bound"
DETERMINISTIC = False
PROFILE = None
USES = ("task_author",)
EXTERNAL_NAME = external_name(__name__.rsplit(".", 1)[-1])

REQUEST = shapes.obj(
    {
        **shapes.TASK_FIELDS,
        "repair_review": shapes.ARTIFACT,
        "repair_task_scope": shapes.obj({"tasks_digest": shapes.DIGEST}),
    },
    (*shapes.TASK_OPTIONAL, "repair_task_scope", "repair_review"),
)
RESPONSE = shapes.operation_response()
REQUEST_VERSION = 2
RESPONSE_VERSION = 3


STATE = StateContract(f"{EXTERNAL_NAME}-request", None)


def run(state, runtime):
    return run_host(EXTERNAL_NAME, state, runtime)
