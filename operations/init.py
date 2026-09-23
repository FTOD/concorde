"""Operation: propose and apply explicit project initialization with a pinned Protocol and an
honest registry stub. Deterministic; runs no agent cognition and selects no context."""

from concorde.harness.operation_state import StateContract, run_host
from concorde.spec.initialize import INIT_REQUEST, INIT_RESPONSE

from . import external_name

KIND = "host"
PUBLIC = True
CONTEXT_SELECTION = "none"
DETERMINISTIC = True
PROFILE = None
USES = ()
EXTERNAL_NAME = external_name(__name__.rsplit(".", 1)[-1])

# Spec tooling owns the concorde-init request and response and registers them itself; the
# declaration names the same schemas.
REQUEST = INIT_REQUEST
RESPONSE = INIT_RESPONSE
REQUEST_VERSION = 3
RESPONSE_VERSION = 1


STATE = StateContract(f"{EXTERNAL_NAME}-request", None)


def run(state, runtime):
    return run_host(EXTERNAL_NAME, state, runtime)
