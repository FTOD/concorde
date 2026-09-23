"""Operation: propose a change of the stored operation configuration, or apply the reviewed proposal
whose digest the request names; a proposal made with accept_protocol also rebinds the project to the
Protocol copy the installer placed under .concorde/protocol/. Deterministic; runs no Agent and
selects no context."""

from concorde.harness import configure


KIND = "host"
PUBLIC = True
DETERMINISTIC = True
OWNER = "module.harness.admission"
AGENTS = ()
USES = ()

# Request admission owns the concorde-configure request and response; the declaration names the
# same schemas.
REQUEST = configure.REQUEST
RESPONSE = configure.RESPONSE
REQUEST_VERSION = configure.REQUEST_VERSION
RESPONSE_VERSION = configure.RESPONSE_VERSION


MUTATION = {"policy": "by-action", "actions": ["apply"]}
WORKSPACE = "primary-opt-in"
TARGET = {"selection": "none", "hook": None}
DEFAULT_TASK = "Configure the project's operation settings"
CONFIGURATION = "stored"
ENTRY_POINT = "concorde.harness.configure:run"
