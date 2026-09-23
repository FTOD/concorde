"""Operation: apply the project's Pi worker model selection and, on explicit
request, accept the Protocol the installer placed under .concorde/protocol/ by rebinding to it.
Deterministic; runs no agent cognition and selects no context."""

from concorde.harness.operation_state import StateContract, run_host
from concorde.operations import shapes

from . import external_name

KIND = "host"
PUBLIC = True
CONTEXT_SELECTION = "none"
DETERMINISTIC = True
PROFILE = None
USES = ()
EXTERNAL_NAME = external_name(__name__.rsplit(".", 1)[-1])

_CONFIGURATION = shapes.typed_schema("concorde-operation-configuration")

# ``accept_protocol`` is the only way an updated installed Protocol becomes the project's binding:
# install and update never rewrite the binding silently. ``run_in_primary`` is the explicit opt-in
# to apply in the primary worktree instead of a relayed candidate.
REQUEST = shapes.obj(
    {
        "configuration": _CONFIGURATION,
        "accept_protocol": {"type": "boolean"},
        "run_in_primary": {"type": "boolean"},
    },
    ("accept_protocol", "run_in_primary"),
)
RESPONSE = shapes.obj({"configuration": _CONFIGURATION, "status": {"const": "applied"}})
REQUEST_VERSION = 3
RESPONSE_VERSION = 2


STATE = StateContract(f"{EXTERNAL_NAME}-request", None)


def run(state, runtime):
    return run_host(EXTERNAL_NAME, state, runtime)
