"""Branch-local Issue management and solving, with reporting independent of execution."""
from concorde.spec import contract_shapes as shapes
from concorde.spec.issue_shapes import ISSUE_ID, RECORD, REPORT
from agents import issue_solver
from . import external_name

PUBLIC = True
CONTEXT_SELECTION = "bound"
DETERMINISTIC = False
AGENTS = (issue_solver.AGENT,)
USES = ("dev_loop", "specify", "review", "validate")
EXTERNAL_NAME = external_name(__name__.rsplit(".", 1)[-1])
REQUEST = shapes.obj({
    **shapes.TASK_FIELDS,
    "action": {"enum": ["list", "show", "report", "solve", "reopen"]},
    "issue_id": ISSUE_ID,
    "report": REPORT,
    "expected_revision": shapes.DIGEST,
    "note": shapes.STRING,
}, ("target_id", "task", *shapes.TASK_OPTIONAL, "issue_id", "report", "expected_revision", "note"))
BASE = shapes.capability_response()
RESPONSE = shapes.obj({**BASE["properties"], "issues": shapes.array(RECORD),
    "decision": {"anyOf": [shapes.STRING, {"type": "null"}]}})


def run(host, configuration, request):
    from concorde.development.capability_service import run_capability
    return run_capability(EXTERNAL_NAME, configuration, request, host_context=host)
