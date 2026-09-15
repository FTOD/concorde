"""Author one Module's owned Spec documents for a task."""
from concorde.harness.agent_model import Agent, Contract
from concorde.harness.effects import EffectDeclaration

AGENT = Agent(
    name="spec_author", spec="agents/spec_author/spec.md", workspace="capsule",
    contract=Contract(
        phase="specify",
        context="concorde-agent-stage-context", result="concorde-agent-stage-result",
        effects=EffectDeclaration(("spec-context",), (), False, "none"),
        output_fields=("documents",)),
    tools=("read", "grep", "find", "ls"),
    timeout_seconds=1800,
)
