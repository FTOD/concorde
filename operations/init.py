"""Operation: propose and apply explicit project initialization with a pinned Protocol and an
honest registry stub. Deterministic; runs no agent cognition and selects no context."""

from concorde.spec.initialize import INIT_REQUEST, INIT_RESPONSE


KIND = "host"
PUBLIC = True
DETERMINISTIC = True
OWNER = "module.spec"
AGENTS = ()
USES = ()

# Spec tooling owns the concorde-init request and response and registers them itself; the
# declaration names the same schemas.
REQUEST = INIT_REQUEST
RESPONSE = INIT_RESPONSE
REQUEST_VERSION = 3
RESPONSE_VERSION = 1


MUTATION = {"policy": "by-action", "actions": ["apply"]}
WORKSPACE = "primary-opt-in"
TARGET = {"selection": "none", "hook": None}
DEFAULT_TASK = "Initialize the project Spec"
CONFIGURATION = "request"
ENTRY_POINT = "concorde.spec.initialize:run"
