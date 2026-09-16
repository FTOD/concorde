"""Capability: plan a change from one complete Spec without implementation access.

Never projected as a user-invocable Skill; the executable boundary has no direct entry for it."""
from concorde.spec import contract_shapes as shapes

from . import external_name
from concorde.harness.capability_state import StateContract, run_host

PUBLIC = False
CONTEXT_SELECTION = "bound"
DETERMINISTIC = False
PROFILE = None
USES = ('context_assessor', 'planner')
EXTERNAL_NAME = external_name(__name__.rsplit(".", 1)[-1])

REQUEST = shapes.task_request(target_required=True)
RESPONSE = shapes.capability_response()


STATE = StateContract(f"{EXTERNAL_NAME}-request", None)


def run(state, runtime):
    return run_host(EXTERNAL_NAME, state, runtime)
