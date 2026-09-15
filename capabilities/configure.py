"""Capability: apply the initialized integration and enforcement configuration and, on explicit
request, accept the Protocol the installer placed under .concorde/protocol/ by rebinding to it.
Deterministic; runs no agent cognition and selects no context."""
from concorde.spec import contract_shapes as shapes

from . import external_name

PUBLIC = True
CONTEXT_SELECTION = "none"
DETERMINISTIC = True
AGENTS = ()
USES = ()
EXTERNAL_NAME = external_name(__name__.rsplit(".", 1)[-1])

_CONFIGURATION = shapes.typed_schema("concorde-capability-configuration")

# ``accept_protocol`` is the only way an updated installed Protocol becomes the project's binding:
# install and update never rewrite the binding silently.
REQUEST = shapes.obj({"configuration": _CONFIGURATION, "accept_protocol": {"type": "boolean"}},
                     ("accept_protocol",))
RESPONSE = shapes.obj({"configuration": _CONFIGURATION, "status": {"const": "applied"}})


def run(host, configuration, request):
    from concorde.development.capability_service import run_capability
    return run_capability(EXTERNAL_NAME, configuration, request, host_context=host)
