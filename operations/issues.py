"""Branch-local Issue management and solving, with reporting independent of execution."""

from concorde.operations import shapes
from concorde.issues.shapes import ISSUE_ID, RECORD, REPORT


KIND = "pi-workflow"
PUBLIC = True
DETERMINISTIC = False
OWNER = "module.issue-solving"
AGENTS = (("issue_solver", "issue-solve"),)
USES = ("concorde-spec-review", "concorde-code-review", "concorde-validate")
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


MUTATION = {"policy": "by-action", "actions": ["solve"]}
WORKSPACE = "candidate"
TARGET = {
    "selection": "provider-hook",
    "hook": "concorde.issue_solving.bookkeeping:select_target",
}
DEFAULT_TASK = None
CONFIGURATION = "stored"
ENTRY_POINT = "concorde.issue_solving.native:issues_workflow"
