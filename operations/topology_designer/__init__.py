"""Design one candidate topology change from selected complete Module Specs and the registry."""

from concorde.harness.effects import EffectDeclaration
from concorde.harness.operation_state import StateContract, run_model
from concorde.harness.worker_profile import Contract, WorkerProfile

from .. import external_name

PROFILE = WorkerProfile(
    name="topology_designer",
    spec="operations/topology_designer/spec.md",
    workspace="capsule",
    contract=Contract(
        phase="route",
        action="design-topology",
        context="concorde-main-stage-context",
        result="concorde-main-stage-result",
        effects=EffectDeclaration(("discovery-context",), (), False, "none"),
        output_fields=("topology_design",),
        outcomes=(
            "topology_proposed",
            "expand",
            "spec_incomplete",
            "unsupported",
            "conflicting",
        ),
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
