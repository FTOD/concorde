"""Global reflection queue: report status, capture recorded gaps, and investigate, implement,
merge or close owned reflections."""
from concorde.host import contract_shapes as shapes, roles

from . import external_name

CLASS = "global"
ROLES = (roles.IMPLEMENTATION_WORKER,)
USES = ("dev_loop",)
EXTERNAL_NAME = external_name(__name__.rsplit(".", 1)[-1])

REQUEST = shapes.obj({
    **shapes.TASK_FIELDS,
    "action": {"enum": ["status", "record-gaps", "investigate", "implement", "merge", "close"]},
    "reflection_ids": shapes.array(shapes.STRING, unique=True),
    "gap_ids": shapes.array(shapes.DIGEST, unique=True),
}, (*shapes.TASK_OPTIONAL, "task", "gap_ids"))

_BASE_RESPONSE = shapes.stage_response()
RESPONSE = {
    **_BASE_RESPONSE,
    "properties": {
        **_BASE_RESPONSE["properties"],
        "reflections": shapes.array(shapes.obj({
            "id": shapes.STRING, "target_id": shapes.STRING, "status": shapes.STRING,
            "triage": shapes.STRING, "bucket": shapes.STRING,
            "plan_status": shapes.NULLABLE_ID, "verification": shapes.NULLABLE_ID,
        })),
        "gap_records": shapes.array(shapes.obj({
            "id": shapes.DIGEST, "target_id": shapes.STRING, "task": shapes.STRING,
            "phase": shapes.STRING, "gap": shapes.GAP,
            "status": {"enum": ["open", "resolved"]}, "reflection_id": shapes.NULLABLE_ID,
        })),
    },
}


def run(host, configuration, request):
    from concorde.host.capability_service import run_capability
    return run_capability(EXTERNAL_NAME, configuration, request, host_context=host)
