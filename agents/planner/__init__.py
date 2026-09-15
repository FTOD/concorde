"""Plan contract-level work for one Module from its complete Spec."""
from concorde.harness.agent_model import Agent, Child, Contract
from concorde.harness.effects import EffectDeclaration

AGENT = Agent(
    name="planner", spec="agents/planner/spec.md", workspace="capsule",
    contract=Contract(
        phase="plan",
        context="concorde-agent-stage-context", result="concorde-agent-stage-result",
        effects=EffectDeclaration(("spec-context", "references"), (), False, "none"),
        stage_inputs=("concorde-plan-artifact",),
        output_fields=("plan",)),
    tools=("read", "grep", "find", "ls"),
    children=(Child("scout", "agents/planner/children/scout.md"),),
    timeout_seconds=1800,
)
