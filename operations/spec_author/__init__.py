"""Author one Module's owned Spec documents for a task."""

from concorde.harness.effects import EffectDeclaration
from concorde.harness.operation_state import StateContract, run_model
from concorde.harness.worker_profile import Contract, WorkerProfile

from .. import external_name

PROFILE = WorkerProfile(
    name="spec_author",
    spec="operations/spec_author/spec.md",
    workspace="capsule",
    contract=Contract(
        phase="specify",
        context="concorde-agent-stage-context",
        result="concorde-agent-stage-result",
        effects=EffectDeclaration(("spec-context",), (), False, "none"),
        output_fields=("documents",),
    ),
    tools=("read", "grep", "find", "ls"),
    timeout_seconds=1800,
)

PUBLIC = False
CONTEXT_SELECTION = "bound"
DETERMINISTIC = False
USES = ()
EXTERNAL_NAME = external_name(__name__.rsplit(".", 1)[-1])
STATE = StateContract(PROFILE.contract.context, PROFILE.contract.result)


def run(state, runtime):
    return run_model(PROFILE, state, runtime)
