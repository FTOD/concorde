"""Internal stage: independent read-only Spec or code review of the bound target.

Never projected as a user-invocable Skill; the executable boundary has no direct entry for it."""
from concorde.capabilities import contract_shapes as shapes, roles

from . import external_name

CLASS = "stage"
ROLES = (roles.SPEC_REVIEWER, roles.CODE_REVIEWER)
USES = ()
EXTERNAL_NAME = external_name(__name__.rsplit(".", 1)[-1])

REQUEST = shapes.obj({
    **shapes.TASK_FIELDS,
    "review_mode": {"enum": ["spec", "code"]},
}, ("target_id", *shapes.TASK_OPTIONAL))

_BASE_RESPONSE = shapes.stage_response()
RESPONSE = {
    **_BASE_RESPONSE,
    "properties": {
        **_BASE_RESPONSE["properties"],
        "reviews": shapes.array(shapes.typed_schema("concorde-review-result")),
    },
    "required": [*_BASE_RESPONSE["required"], "reviews"],
}


def run(host, configuration, request):
    from concorde.capabilities.operation_service import run_operation
    return run_operation(EXTERNAL_NAME, configuration, request, host_context=host)
