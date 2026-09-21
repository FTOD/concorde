"""Choose bounded work or an evidence-grounded disposition for one selected Issue."""

from concorde.harness.effects import EffectDeclaration
from concorde.harness.worker_profile import Contract, WorkerProfile

from .. import external_name

PROFILE = WorkerProfile(
    name="issue_solver",
    spec="operations/issue_solver/spec.md",
    workspace="capsule",
    contract=Contract(
        phase="issue-solve",
        context="concorde-agent-stage-context",
        result="concorde-agent-stage-result",
        effects=EffectDeclaration(("spec-context",), (), False, "none"),
        stage_inputs=("concorde-issue-selection",),
        required_inputs=("concorde-issue-selection",),
        output_fields=("issue_decision",),
    ),
    tools=("read", "grep", "find", "ls"),
)

PUBLIC = False
CONTEXT_SELECTION = "bound"
DETERMINISTIC = False
USES = ()
EXTERNAL_NAME = external_name(__name__.rsplit(".", 1)[-1])
KIND = "agent"
