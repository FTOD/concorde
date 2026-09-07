"""Lifecycle: run deterministic Spec and configured code checks and record readiness for the
current candidate. Deterministic; runs no agent cognition and selects no context."""
from concorde.capabilities import contract_shapes as shapes

from . import external_name

CLASS = "lifecycle"
ROLES = ()
USES = ()
EXTERNAL_NAME = external_name(__name__.rsplit(".", 1)[-1])

REQUEST = shapes.obj({
    **shapes.TASK_FIELDS,
    "run_checks": {"type": "boolean"},
}, (*shapes.TASK_OPTIONAL, "run_checks"))

RESPONSE = shapes.stage_response()


def run(host, configuration, request):
    from concorde.capabilities.operation_service import run_operation
    return run_operation(EXTERNAL_NAME, configuration, request, host_context=host)
