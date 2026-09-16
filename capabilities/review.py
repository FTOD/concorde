"""Capability: route an observational task, then independently review its Spec or code read-only.

Composing capabilities may reuse an already bound target without repeating discovery."""
from concorde.spec import contract_shapes as shapes

from . import external_name
from concorde.harness.capability_state import StateContract, run_host

PUBLIC = True
CONTEXT_SELECTION = "discover"
DETERMINISTIC = False
PROFILE = None
USES = ('router', 'spec_reviewer', 'code_reviewer')
EXTERNAL_NAME = external_name(__name__.rsplit(".", 1)[-1])

REQUEST = shapes.obj({
    **shapes.TASK_FIELDS,
    "review_mode": {"enum": ["spec", "code"]},
}, ("target_id", *shapes.TASK_OPTIONAL))

_BASE_RESPONSE = shapes.capability_response()
RESPONSE = {
    **_BASE_RESPONSE,
    "properties": {
        **_BASE_RESPONSE["properties"],
        "reviews": shapes.array(shapes.typed_schema("concorde-review-result")),
    },
    "required": [*_BASE_RESPONSE["required"], "reviews"],
}


STATE = StateContract(f"{EXTERNAL_NAME}-request", None)


def run(state, runtime):
    return run_host(EXTERNAL_NAME, state, runtime)
