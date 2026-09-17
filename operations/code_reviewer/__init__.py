"""Review one Module's granted implementation against its complete contracts, read-only."""

from concorde.harness.effects import EffectDeclaration
from concorde.harness.operation_state import StateContract, run_model
from concorde.harness.worker_profile import Child, Contract, WorkerProfile

from .. import external_name

PROFILE = WorkerProfile(
    name="code_reviewer",
    spec="operations/code_reviewer/spec.md",
    workspace="project",
    contract=Contract(
        phase="code-review",
        context="concorde-review-stage-context",
        result="concorde-review-stage-result",
        effects=EffectDeclaration(
            ("spec-context", "implementation", "references"), (), False, "none"
        ),
    ),
    tools=("read", "grep", "find", "ls"),
    children=(
        Child("scout", "operations/code_reviewer/children/scout.md"),
        Child("verifier", "operations/code_reviewer/children/verifier.md"),
    ),
    timeout_seconds=3600,
)

PUBLIC = False
CONTEXT_SELECTION = "bound"
DETERMINISTIC = False
USES = ()
EXTERNAL_NAME = external_name(__name__.rsplit(".", 1)[-1])
STATE = StateContract(PROFILE.contract.context, PROFILE.contract.result)


def run(state, runtime):
    return run_model(PROFILE, state, runtime)
