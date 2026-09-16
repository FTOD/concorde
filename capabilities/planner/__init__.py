"""Plan contract-level work for one Module from its complete Spec."""
from concorde.harness.worker_profile import WorkerProfile, Child, Contract
from concorde.harness.effects import EffectDeclaration
from concorde.harness.capability_state import StateContract, run_model
from .. import external_name

PROFILE = WorkerProfile(
    name="planner", spec="capabilities/planner/spec.md", workspace="capsule",
    contract=Contract(
        phase="plan",
        context="concorde-agent-stage-context", result="concorde-agent-stage-result",
        effects=EffectDeclaration(("spec-context", "references"), (), False, "none"),
        stage_inputs=("concorde-plan-artifact",),
        output_fields=("plan",)),
    tools=("read", "grep", "find", "ls"),
    children=(Child("scout", "capabilities/planner/children/scout.md"),),
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
