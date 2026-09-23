"""Operation: independently review one Module's granted implementation against its Spec."""

from concorde.harness.operation_state import StateContract, run_host
from concorde.operations import shapes

from . import external_name

KIND = "workflow"
PUBLIC = True
CONTEXT_SELECTION = "bound"
DETERMINISTIC = False
PROFILE = None
USES = ("code_reviewer",)
EXTERNAL_NAME = external_name(__name__.rsplit(".", 1)[-1])

REQUEST = shapes.task_request(target_required=True)
_BASE_RESPONSE = shapes.operation_response()
RESPONSE = {
    **_BASE_RESPONSE,
    "properties": {
        **_BASE_RESPONSE["properties"],
        "reviews": shapes.array(shapes.typed_schema("concorde-review-result")),
    },
    "required": [*_BASE_RESPONSE["required"], "reviews"],
}
REQUEST_VERSION = 2
RESPONSE_VERSION = 3


STATE = StateContract(f"{EXTERNAL_NAME}-request", None)


def run(state, runtime):
    return run_host(EXTERNAL_NAME, state, runtime)
