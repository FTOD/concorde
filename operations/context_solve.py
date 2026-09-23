"""Operation: assess a task for missing Spec information within one frozen context."""

from concorde.operations import shapes


KIND = "agent-call"
PUBLIC = True
DETERMINISTIC = False
OWNER = "module.planning"
AGENTS = (("context_assessor", "context-solve"),)
USES = ()

REQUEST = shapes.task_request(target_required=True)
RESPONSE = shapes.operation_response()
REQUEST_VERSION = 1
RESPONSE_VERSION = 3


MUTATION = {"policy": "never", "actions": []}
WORKSPACE = "none"
TARGET = {"selection": "bound-module", "hook": None}
DEFAULT_TASK = None
CONFIGURATION = "stored"
ENTRY_POINT = "concorde.planning.hooks:context_assessor"
