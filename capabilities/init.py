"""Lifecycle: propose and apply explicit project initialization with a pinned Protocol and an
honest registry stub. Deterministic; runs no agent cognition and selects no context."""
from concorde.host import contract_shapes as shapes

from . import external_name

CLASS = "lifecycle"
AGENTS = ()
USES = ()
EXTERNAL_NAME = external_name(__name__.rsplit(".", 1)[-1])

_CONFIGURATION = shapes.typed_schema("concorde-capability-configuration")

REQUEST = shapes.obj({
    "action": {"enum": ["propose", "apply"]},
    "name": shapes.STRING,
    "target_id": shapes.STRING,
    "configuration": _CONFIGURATION,
    "proposal": shapes.typed_schema("concorde-project-proposal"),
}, ("name", "target_id", "configuration", "proposal"))

RESPONSE = shapes.obj({
    "status": {"enum": ["proposed", "applied"]},
    "proposal": {"anyOf": [shapes.typed_schema("concorde-project-proposal"), {"type": "null"}]},
    "files": shapes.array(shapes.PATH),
})


def run(host, configuration, request):
    from concorde.host.capability_service import run_capability
    return run_capability(EXTERNAL_NAME, configuration, request, host_context=host)
