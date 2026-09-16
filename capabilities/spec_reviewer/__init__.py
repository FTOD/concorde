"""Review one Module's complete Spec collection against representative tasks."""
from concorde.harness.worker_profile import WorkerProfile, Child, Contract
from concorde.harness.effects import EffectDeclaration
from concorde.harness.capability_state import StateContract, run_model
from .. import external_name

PROFILE = WorkerProfile(
    name="spec_reviewer", spec="capabilities/spec_reviewer/spec.md", workspace="capsule",
    contract=Contract(
        phase="spec-review",
        context="concorde-review-stage-context", result="concorde-review-stage-result",
        effects=EffectDeclaration(("spec-context",), (), False, "none")),
    tools=("read", "grep", "find", "ls"),
    children=(Child("fact-check", "capabilities/spec_reviewer/children/fact-check.md"),
              Child("consistency", "capabilities/spec_reviewer/children/consistency.md")),
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
