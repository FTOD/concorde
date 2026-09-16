"""Capability: turn an admitted plan into tasks with observable acceptance conditions.

Never projected as a user-invocable Skill; the executable boundary has no direct entry for it."""
from concorde.spec import contract_shapes as shapes

from . import external_name
from concorde.harness.capability_state import StateContract, run_host

PUBLIC = False
CONTEXT_SELECTION = "bound"
DETERMINISTIC = False
PROFILE = None
USES = ('task_author',)
EXTERNAL_NAME = external_name(__name__.rsplit(".", 1)[-1])

REQUEST = shapes.obj({**shapes.TASK_FIELDS,
    "repair_task_scope": shapes.obj({"tasks_digest": shapes.DIGEST}),
}, (*shapes.TASK_OPTIONAL, "repair_task_scope"))
RESPONSE = shapes.capability_response()


STATE = StateContract(f"{EXTERNAL_NAME}-request", None)


def run(state, runtime):
    return run_host(EXTERNAL_NAME, state, runtime)
