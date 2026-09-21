"""Turn an accepted plan into implementation acceptance tasks."""

from concorde.harness.effects import EffectDeclaration
from concorde.harness.worker_profile import Contract, WorkerProfile

from .. import external_name

PROFILE = WorkerProfile(
    name="task_author",
    spec="operations/task_author/spec.md",
    workspace="capsule",
    contract=Contract(
        phase="tasks",
        context="concorde-agent-stage-context",
        result="concorde-agent-stage-result",
        effects=EffectDeclaration(("spec-context", "references"), (), False, "none"),
        stage_inputs=(
            "concorde-plan-artifact",
            "concorde-task-identity-constraints",
            "concorde-implementation-task",
            "concorde-review-result",
            "concorde-task-scope-feedback",
        ),
        required_inputs=(
            "concorde-plan-artifact",
            "concorde-task-identity-constraints",
        ),
        output_fields=("tasks",),
    ),
    tools=("read", "grep", "find", "ls"),
    timeout_seconds=1800,
)

PUBLIC = False
CONTEXT_SELECTION = "bound"
DETERMINISTIC = False
USES = ()
EXTERNAL_NAME = external_name(__name__.rsplit(".", 1)[-1])
KIND = "agent"
