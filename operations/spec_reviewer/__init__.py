"""Review one Module's complete Spec collection against representative tasks."""

from concorde.harness.effects import EffectDeclaration
from concorde.harness.worker_profile import Contract, WorkerProfile

from .. import external_name

PROFILE = WorkerProfile(
    name="spec_reviewer",
    spec="operations/spec_reviewer/spec.md",
    workspace="capsule",
    contract=Contract(
        phase="spec-review",
        context="concorde-review-stage-context",
        result="concorde-review-stage-result",
        effects=EffectDeclaration(("spec-context",), (), False, "none"),
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
