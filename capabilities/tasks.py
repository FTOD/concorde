"""Internal stage: turn an admitted plan into tasks with observable acceptance conditions.

Never projected as a user-invocable Skill; the executable boundary has no direct entry for it."""
from concorde.spec import contract_shapes as shapes
from agents import spec_engineer

from . import external_name

CLASS = "stage"
DETERMINISTIC = False
AGENTS = (spec_engineer.AGENT,)
USES = ()
EXTERNAL_NAME = external_name(__name__.rsplit(".", 1)[-1])

REQUEST = shapes.task_request(target_required=True)
RESPONSE = shapes.stage_response()


def run(host, configuration, request):
    from concorde.development.capability_service import run_capability
    return run_capability(EXTERNAL_NAME, configuration, request, host_context=host)
