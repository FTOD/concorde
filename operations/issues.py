"""Branch-local Issue management and solving, with reporting independent of execution."""

from concorde.harness.operation_state import StateContract, run_host
from concorde.operations import shapes
from concorde.issues.shapes import ISSUE_ID, RECORD, REPORT

from . import external_name

KIND = "workflow"
PUBLIC = True
CONTEXT_SELECTION = "bound"
DETERMINISTIC = False
PROFILE = None
USES = ("issue_solver", "spec_review", "code_review", "validate")
EXTERNAL_NAME = external_name(__name__.rsplit(".", 1)[-1])
REQUEST = shapes.obj(
    {
        **shapes.TASK_FIELDS,
        "action": {"enum": ["list", "show", "report", "solve", "reopen"]},
        "issue_id": ISSUE_ID,
        "report": REPORT,
        "expected_revision": shapes.DIGEST,
        "note": shapes.STRING,
    },
    (
        "target_id",
        "task",
        *shapes.TASK_OPTIONAL,
        "issue_id",
        "report",
        "expected_revision",
        "note",
    ),
)
BASE = shapes.operation_response()
RESPONSE = shapes.obj(
    {
        **BASE["properties"],
        "issues": shapes.array(RECORD),
        "decision": {"anyOf": [shapes.STRING, {"type": "null"}]},
    }
)
REQUEST_VERSION = 1
RESPONSE_VERSION = 2


STATE = StateContract(f"{EXTERNAL_NAME}-request", None)


def run(state, runtime):
    return run_host(EXTERNAL_NAME, state, runtime)
