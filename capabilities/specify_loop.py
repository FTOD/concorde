"""Spec loop: route, author or revise the Spec, and independently review it.

Stops with a completed Spec result or an attributed blocker. It never plans, implements,
validates code or marks a candidate ready. Repeated calls resume accepted authoring and
current review evidence; ``specify=false`` reviews the existing Spec without authoring.
"""
from concorde.spec import contract_shapes as shapes
from agents import router

from . import external_name

PUBLIC = True
CONTEXT_SELECTION = "discover"
DETERMINISTIC = False
AGENTS = (router.AGENT,)
USES = ("specify", "review")
EXTERNAL_NAME = external_name(__name__.rsplit(".", 1)[-1])

REQUEST = shapes.obj({
    **shapes.TASK_FIELDS,
    "specify": {"type": "boolean"},
    "run_reviews": {"type": "boolean"},
}, ("target_id", *shapes.TASK_OPTIONAL, "specify", "run_reviews"))
RESPONSE = shapes.capability_response()


def run(host, configuration, request):
    from concorde.development.capability_service import run_capability
    return run_capability(EXTERNAL_NAME, configuration, request, host_context=host)
