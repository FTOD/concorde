"""Author the documents of one accepted target descriptor from a topology proposal."""
from concorde.harness.agent_model import Agent, Contract
from concorde.harness.effects import EffectDeclaration

AGENT = Agent(
    name="topology_author", spec="agents/topology_author/spec.md", workspace="capsule",
    contract=Contract(
        phase="topology-author",
        context="concorde-topology-author-context", result="concorde-topology-author-result",
        effects=EffectDeclaration(("spec-context",), (), False, "none"),
        output_fields=("documents",)),
    tools=("read", "grep", "find", "ls"),
    timeout_seconds=1800,
)
