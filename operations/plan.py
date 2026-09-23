"""Operation: plan a change from one complete Spec without implementation access."""

from concorde.operations import shapes


KIND = "pi-workflow"
PUBLIC = True
DETERMINISTIC = False
OWNER = "module.planning"
AGENTS = (("context_assessor", "context-solve"), ("planner", "plan"))
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
ENTRY_POINT = "concorde.planning.hooks:plan_workflow"
