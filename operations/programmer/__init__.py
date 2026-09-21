"""Fulfil one Module's implementation tasks in its candidate worktree."""

from concorde.harness.effects import EffectDeclaration
from concorde.harness.worker_profile import Contract, WorkerProfile

from .. import external_name

PROFILE = WorkerProfile(
    name="programmer",
    spec="operations/programmer/spec.md",
    workspace="project",
    contract=Contract(
        phase="implementation",
        context="concorde-agent-stage-context",
        result="concorde-agent-stage-result",
        effects=EffectDeclaration(
            ("spec-context", "implementation", "references"),
            ("implementation",),
            False,
            "none",
        ),
        stage_inputs=("concorde-implementation-task", "concorde-review-result"),
        required_inputs=("concorde-implementation-task",),
        output_fields=("tasks",),
    ),
    tools=("read", "grep", "find", "ls", "edit", "write", "bash", "run_checks"),
    timeout_seconds=3600,
)

PUBLIC = False
CONTEXT_SELECTION = "bound"
DETERMINISTIC = False
USES = ()
EXTERNAL_NAME = external_name(__name__.rsplit(".", 1)[-1])
KIND = "agent"
