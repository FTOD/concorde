"""Global development loop: route one change, then specify, review, plan, task, implement,
validate and review code to a ready candidate.

``specify=false`` skips Spec authoring (the former fast loop); ``run_reviews=false`` records an
explicit skip for each review mode instead of running it. A review requirement already recorded
for a change cannot be disabled by a later ``run_reviews=false``.
"""
from concorde.host import contract_shapes as shapes
from agents import coordinator

from . import external_name

CLASS = "global"
AGENTS = (coordinator.AGENT,)
USES = ("specify", "review", "plan", "tasks", "implement", "validate")
EXTERNAL_NAME = external_name(__name__.rsplit(".", 1)[-1])

REQUEST = shapes.obj({
    **shapes.TASK_FIELDS,
    "specify": {"type": "boolean"},
    "run_reviews": {"type": "boolean"},
}, ("target_id", *shapes.TASK_OPTIONAL, "specify", "run_reviews"))

RESPONSE = shapes.stage_response()


def run(host, configuration, request):
    from concorde.host.capability_service import run_capability
    return run_capability(EXTERNAL_NAME, configuration, request, host_context=host)
