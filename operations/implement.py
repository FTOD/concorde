"""Operation: implement or investigate tasks under a host-granted code boundary."""

from concorde.operations import shapes


KIND = "agent-call"
PUBLIC = True
DETERMINISTIC = False
OWNER = "module.implementation"
AGENTS = (("programmer", "implementation"),)
USES = ()

REQUEST = shapes.task_request(target_required=True)
RESPONSE = shapes.operation_response()
REQUEST_VERSION = 1
RESPONSE_VERSION = 3


MUTATION = {"policy": "always", "actions": []}
WORKSPACE = "candidate"
TARGET = {"selection": "bound-module", "hook": None}
DEFAULT_TASK = None
CONFIGURATION = "stored"
ENTRY_POINT = "concorde.implementation.implement:implement"
