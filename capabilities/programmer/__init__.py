"""Fulfil one Module's implementation tasks in its candidate worktree."""
from concorde.harness.worker_profile import WorkerProfile, Child, Contract
from concorde.harness.effects import EffectDeclaration
from concorde.harness.capability_state import StateContract, run_model
from .. import external_name

PROFILE = WorkerProfile(
    name="programmer", spec="capabilities/programmer/spec.md", workspace="project",
    contract=Contract(
        phase="implementation",
        context="concorde-agent-stage-context", result="concorde-agent-stage-result",
        effects=EffectDeclaration(("spec-context", "implementation", "references"), ("implementation",), False, "none"),
        stage_inputs=("concorde-implementation-task", "concorde-review-result"),
        required_inputs=("concorde-implementation-task",),
        output_fields=("tasks",)),
    tools=("read", "grep", "find", "ls", "edit", "write", "bash", "run_checks"),
    children=(Child("scout", "capabilities/programmer/children/scout.md"),
              Child("planner", "capabilities/programmer/children/planner.md"),
              Child("verifier", "capabilities/programmer/children/verifier.md")),
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
