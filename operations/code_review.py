"""Operation: independently review one Module's granted implementation against its Spec."""

from concorde.operations import shapes


KIND = "pi-workflow"
PUBLIC = True
DETERMINISTIC = False
OWNER = "module.review"
AGENTS = (("code_reviewer", "code-review"),)
USES = ()

REQUEST = shapes.task_request(target_required=True)
_BASE_RESPONSE = shapes.operation_response()
RESPONSE = {
    **_BASE_RESPONSE,
    "properties": {
        **_BASE_RESPONSE["properties"],
        "reviews": shapes.array(shapes.typed_schema("concorde-review-result")),
    },
    "required": [*_BASE_RESPONSE["required"], "reviews"],
}
REQUEST_VERSION = 2
RESPONSE_VERSION = 3


MUTATION = {"policy": "never", "actions": []}
WORKSPACE = "none"
TARGET = {"selection": "bound-module", "hook": None}
DEFAULT_TASK = None
CONFIGURATION = "stored"
ENTRY_POINT = "concorde.review.native:review_workflow"
