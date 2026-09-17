"""Branch-local Issue management and solving, with reporting independent of execution."""

from concorde.harness.operation_state import StateContract, run_host
from concorde.spec import contract_shapes as shapes
from concorde.spec.issue_shapes import ISSUE_ID, LEGACY_RECORD, RECORD, REPORT

from . import external_name

PUBLIC = True
CONTEXT_SELECTION = "bound"
DETERMINISTIC = False
PROFILE = None
USES = ("issue_solver", "dev_loop", "specify", "review", "validate")
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
        "issues": shapes.array({"anyOf": [RECORD, LEGACY_RECORD]}),
        "decision": {"anyOf": [shapes.STRING, {"type": "null"}]},
    }
)


STATE = StateContract(f"{EXTERNAL_NAME}-request", None)


def run(state, runtime):
    return run_host(EXTERNAL_NAME, state, runtime)
