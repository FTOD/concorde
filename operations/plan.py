"""Operation: plan a change from one complete Spec without implementation access."""

from concorde.harness.operation_state import StateContract, run_host
from concorde.spec import contract_shapes as shapes

from . import external_name

KIND = "workflow"
PUBLIC = True
CONTEXT_SELECTION = "bound"
DETERMINISTIC = False
PROFILE = None
USES = ("context_assessor", "planner")
EXTERNAL_NAME = external_name(__name__.rsplit(".", 1)[-1])

REQUEST = shapes.task_request(target_required=True)
RESPONSE = shapes.operation_response()


STATE = StateContract(f"{EXTERNAL_NAME}-request", None)


def run(state, runtime):
    return run_host(EXTERNAL_NAME, state, runtime)
