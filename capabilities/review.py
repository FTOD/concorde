"""Internal stage: independent read-only Spec or code review of the bound target.

Never projected as a user-invocable Skill; the executable boundary has no direct entry for it."""
from concorde.spec import contract_shapes as shapes
from agents import code_reviewer, spec_reviewer

from . import external_name

CLASS = "stage"
AGENTS = (spec_reviewer.AGENT, code_reviewer.AGENT)
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
    from concorde.development.capability_service import run_capability
    return run_capability(EXTERNAL_NAME, configuration, request, host_context=host)
