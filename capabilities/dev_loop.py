"""Global development loop: route one change, then specify, review, plan, task, implement,
validate and review code to a ready candidate.

``specify=false`` skips Spec authoring (the former fast loop); ``run_reviews=false`` records an
explicit skip for each review mode instead of running it. A review requirement already recorded
for a change cannot be disabled by a later ``run_reviews=false``.
"""
from concorde.capabilities import contract_shapes as shapes, roles

from . import external_name

CLASS = "global"
ROLES = (roles.COORDINATOR,)
USES = ("specify", "review", "plan", "tasks", "implement", "validate")
EXTERNAL_NAME = external_name(__name__.rsplit(".", 1)[-1])

REQUEST = shapes.obj({
    **shapes.TASK_FIELDS,
    "specify": {"type": "boolean"},
    "run_reviews": {"type": "boolean"},
}, ("target_id", *shapes.TASK_OPTIONAL, "specify", "run_reviews"))

RESPONSE = shapes.stage_response()


def run(host, configuration, request):
    from concorde.capabilities.operation_service import run_operation
    return run_operation(EXTERNAL_NAME, configuration, request, host_context=host)
