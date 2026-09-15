"""Capability: route an observational task, then independently review its Spec or code read-only.

Composing capabilities may reuse an already bound target without repeating discovery."""
from concorde.spec import contract_shapes as shapes
from agents import code_reviewer, router, spec_reviewer

from . import external_name

PUBLIC = True
CONTEXT_SELECTION = "discover"
DETERMINISTIC = False
AGENTS = (router.AGENT, spec_reviewer.AGENT, code_reviewer.AGENT)
USES = ()
EXTERNAL_NAME = external_name(__name__.rsplit(".", 1)[-1])

REQUEST = shapes.obj({
    **shapes.TASK_FIELDS,
    "review_mode": {"enum": ["spec", "code"]},
}, ("target_id", *shapes.TASK_OPTIONAL))

_BASE_RESPONSE = shapes.capability_response()
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
