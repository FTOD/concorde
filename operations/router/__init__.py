"""Route one task to exactly one owning Module from explicitly selected complete Module Specs."""

from concorde.harness.effects import EffectDeclaration
from concorde.harness.operation_state import StateContract, run_model
from concorde.harness.worker_profile import Contract, WorkerProfile

from .. import external_name

PROFILE = WorkerProfile(
    name="router",
    spec="operations/router/spec.md",
    workspace="capsule",
    contract=Contract(
        phase="route",
        action="route",
        context="concorde-main-stage-context",
        result="concorde-main-stage-result",
        effects=EffectDeclaration(("discovery-context",), (), False, "none"),
        output_fields=("routes",),
        outcomes=("routed", "expand", "spec_incomplete", "unsupported", "conflicting"),
    ),
    tools=("read", "grep", "find", "ls"),
    timeout_seconds=900,
)

PUBLIC = False
CONTEXT_SELECTION = "bound"
DETERMINISTIC = False
USES = ()
EXTERNAL_NAME = external_name(__name__.rsplit(".", 1)[-1])
STATE = StateContract(PROFILE.contract.context, PROFILE.contract.result)


def run(state, runtime):
    return run_model(PROFILE, state, runtime)
