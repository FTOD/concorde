"""Internal stage: plan a change from one complete Spec without implementation access.

Never projected as a user-invocable Skill; the executable boundary has no direct entry for it."""
from concorde.host import contract_shapes as shapes, roles

from . import external_name

CLASS = "stage"
ROLES = (roles.CONTEXT_ASSESSOR, roles.PLANNER)
USES = ()
EXTERNAL_NAME = external_name(__name__.rsplit(".", 1)[-1])

REQUEST = shapes.task_request(target_required=True)
RESPONSE = shapes.stage_response()


def run(host, configuration, request):
    from concorde.host.capability_service import run_capability
    return run_capability(EXTERNAL_NAME, configuration, request, host_context=host)
