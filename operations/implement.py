"""Operation: implement or investigate tasks under a host-granted code boundary."""

from concorde.operations import shapes


KIND = "agent-call"
PUBLIC = True
DETERMINISTIC = False
OWNER = "module.implementation"
AGENTS = (("programmer", "implementation"),)
USES = ()

REQUEST = shapes.task_request(target_required=True)
_BASE_RESPONSE = shapes.operation_response()
# Component work the caller completes first: each component Module and its derived task.
RESPONSE = {
    **_BASE_RESPONSE,
    "properties": {
        **_BASE_RESPONSE["properties"],
        "components": shapes.array(
            shapes.obj({"target_id": shapes.STRING, "task": shapes.STRING})
        ),
    },
    "required": [*_BASE_RESPONSE["required"], "components"],
}
REQUEST_VERSION = 1
RESPONSE_VERSION = 4


MUTATION = {"policy": "always", "actions": []}
WORKSPACE = "candidate"
TARGET = {"selection": "bound-module", "hook": None}
DEFAULT_TASK = None
CONFIGURATION = "stored"
ENTRY_POINT = "concorde.implementation.hooks:programmer"
