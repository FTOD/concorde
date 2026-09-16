"""Branch-local Issue management and solving, with reporting independent of execution."""
from concorde.spec import contract_shapes as shapes
from concorde.spec.issue_shapes import ISSUE_ID, RECORD, REPORT
from . import external_name
from concorde.harness.capability_state import StateContract, run_host

PUBLIC = True
CONTEXT_SELECTION = "bound"
DETERMINISTIC = False
PROFILE = None
USES = ('issue_solver', 'dev_loop', 'specify', 'review', 'validate')
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


STATE = StateContract(f"{EXTERNAL_NAME}-request", None)


def run(state, runtime):
    return run_host(EXTERNAL_NAME, state, runtime)
