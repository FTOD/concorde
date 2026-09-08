"""Internal stage: assess a task for missing Spec information within one frozen context.

Never projected as a user-invocable Skill; the executable boundary has no direct entry for it."""
from concorde.host import contract_shapes as shapes
from agents import context_assessor

from . import external_name

CLASS = "stage"
AGENTS = (context_assessor.AGENT,)
USES = ()
EXTERNAL_NAME = external_name(__name__.rsplit(".", 1)[-1])

REQUEST = shapes.task_request(target_required=True)
RESPONSE = shapes.stage_response()


def run(host, configuration, request):
    from concorde.host.capability_service import run_capability
    return run_capability(EXTERNAL_NAME, configuration, request, host_context=host)
