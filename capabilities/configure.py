"""Lifecycle: apply the initialized integration and enforcement configuration. Deterministic;
runs no agent cognition and selects no context."""
from concorde.capabilities import contract_shapes as shapes

from . import external_name

CLASS = "lifecycle"
ROLES = ()
USES = ()
EXTERNAL_NAME = external_name(__name__.rsplit(".", 1)[-1])

_CONFIGURATION = shapes.typed_schema("concorde-operation-configuration")

REQUEST = shapes.obj({"configuration": _CONFIGURATION})
RESPONSE = shapes.obj({"configuration": _CONFIGURATION, "status": {"const": "applied"}})


def run(host, configuration, request):
    from concorde.capabilities.operation_service import run_operation
    return run_operation(EXTERNAL_NAME, configuration, request, host_context=host)
