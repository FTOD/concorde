"""Lifecycle: apply the initialized integration and enforcement configuration. Deterministic;
runs no agent cognition and selects no context."""
from concorde.spec import contract_shapes as shapes

from . import external_name

CLASS = "lifecycle"
AGENTS = ()
USES = ()
EXTERNAL_NAME = external_name(__name__.rsplit(".", 1)[-1])

_CONFIGURATION = shapes.typed_schema("concorde-capability-configuration")

REQUEST = shapes.obj({"configuration": _CONFIGURATION})
RESPONSE = shapes.obj({"configuration": _CONFIGURATION, "status": {"const": "applied"}})


def run(host, configuration, request):
    from concorde.development.capability_service import run_capability
    return run_capability(EXTERNAL_NAME, configuration, request, host_context=host)
