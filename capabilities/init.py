"""Capability: propose and apply explicit project initialization with a pinned Protocol and an
honest registry stub. Deterministic; runs no agent cognition and selects no context."""
from concorde.spec import contract_shapes as shapes

from . import external_name
from concorde.harness.capability_state import StateContract, run_host

PUBLIC = True
CONTEXT_SELECTION = "none"
DETERMINISTIC = True
PROFILE = None
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


STATE = StateContract(f"{EXTERNAL_NAME}-request", None)


def run(state, runtime):
    return run_host(EXTERNAL_NAME, state, runtime)
