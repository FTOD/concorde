"""Internal stage: implement or investigate tasks under a host-granted code boundary.

Never projected as a user-invocable Skill; the executable boundary has no direct entry for it."""
from concorde.capabilities import contract_shapes as shapes, roles

from . import external_name

CLASS = "stage"
ROLES = (roles.IMPLEMENTATION_WORKER,)
USES = ()
EXTERNAL_NAME = external_name(__name__.rsplit(".", 1)[-1])

REQUEST = shapes.task_request(target_required=True)
RESPONSE = shapes.stage_response()


def run(host, configuration, request):
    from concorde.capabilities.operation_service import run_operation
    return run_operation(EXTERNAL_NAME, configuration, request, host_context=host)
