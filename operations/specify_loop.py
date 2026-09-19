"""Spec loop: route, author or revise the Spec, and independently review it.

Stops with a completed Spec result or an attributed blocker. It never plans, implements,
validates code or marks a candidate ready. Repeated calls resume accepted authoring and
current review evidence; ``specify=false`` reviews the existing Spec without authoring.
"""

from concorde.harness.operation_state import StateContract, run_host
from concorde.spec import contract_shapes as shapes

from . import external_name

PUBLIC = True
CONTEXT_SELECTION = "discover"
DETERMINISTIC = False
PROFILE = None
USES = ("router", "specify", "spec_review")
EXTERNAL_NAME = external_name(__name__.rsplit(".", 1)[-1])

REQUEST = shapes.obj(
    {
        **shapes.TASK_FIELDS,
        "specify": {"type": "boolean"},
        "run_reviews": {"type": "boolean"},
    },
    ("target_id", *shapes.TASK_OPTIONAL, "specify", "run_reviews"),
)
RESPONSE = shapes.operation_response()


STATE = StateContract(f"{EXTERNAL_NAME}-request", None)


def run(state, runtime):
    return run_host(EXTERNAL_NAME, state, runtime)
