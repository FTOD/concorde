"""Author the documents of one accepted target descriptor from a topology proposal."""
from concorde.harness.worker_profile import WorkerProfile, Contract
from concorde.harness.effects import EffectDeclaration
from concorde.harness.capability_state import StateContract, run_model
from .. import external_name

PROFILE = WorkerProfile(
    name="topology_author", spec="capabilities/topology_author/spec.md", workspace="capsule",
    contract=Contract(
        phase="topology-author",
        context="concorde-topology-author-context", result="concorde-topology-author-result",
        effects=EffectDeclaration(("spec-context",), (), False, "none"),
        output_fields=("documents",)),
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
