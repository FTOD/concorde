"""Operation: implement or investigate tasks under a host-granted code boundary."""

from concorde.harness.operation_state import StateContract, run_host
from concorde.operations import shapes

from . import external_name

KIND = "agent-entry"
PUBLIC = True
CONTEXT_SELECTION = "bound"
DETERMINISTIC = False
PROFILE = None
USES = ("programmer",)
EXTERNAL_NAME = external_name(__name__.rsplit(".", 1)[-1])

REQUEST = shapes.task_request(target_required=True)
RESPONSE = shapes.operation_response()
REQUEST_VERSION = 1
RESPONSE_VERSION = 3


STATE = StateContract(f"{EXTERNAL_NAME}-request", None)


def run(state, runtime):
    return run_host(EXTERNAL_NAME, state, runtime)
