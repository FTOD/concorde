"""Operation: turn an admitted plan into tasks with observable acceptance conditions."""

from concorde.operations import shapes


KIND = "agent-call"
PUBLIC = True
DETERMINISTIC = False
OWNER = "module.planning"
AGENTS = (("task_author", "tasks"),)
USES = ()

REQUEST = shapes.obj(
    {
        **shapes.TASK_FIELDS,
        "repair_review": shapes.ARTIFACT,
        "repair_task_scope": shapes.obj({"tasks_digest": shapes.DIGEST}),
    },
    (*shapes.TASK_OPTIONAL, "repair_task_scope", "repair_review"),
)
RESPONSE = shapes.operation_response()
REQUEST_VERSION = 2
RESPONSE_VERSION = 3


MUTATION = {"policy": "always", "actions": []}
WORKSPACE = "candidate"
TARGET = {"selection": "bound-module", "hook": None}
DEFAULT_TASK = None
CONFIGURATION = "stored"
ENTRY_POINT = "concorde.planning.hooks:task_author"
