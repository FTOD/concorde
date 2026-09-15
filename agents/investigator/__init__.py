"""Investigate selected reflections against one Module's contract and code, read-only."""
from concorde.harness.agent_model import Agent, Child, Contract
from concorde.harness.effects import EffectDeclaration

AGENT = Agent(
    name="investigator", spec="agents/investigator/spec.md", workspace="project",
    contract=Contract(
        phase="implementation",
        context="concorde-agent-stage-context", result="concorde-agent-stage-result",
        effects=EffectDeclaration(("spec-context", "implementation"), (), False, "none"),
        stage_inputs=("concorde-reflection-selection",),
        required_inputs=("concorde-reflection-selection",),
        output_fields=("reflection_findings",)),
    tools=("read", "grep", "find", "ls", "bash"),
    children=(Child("scout", "agents/investigator/children/scout.md"),),
    timeout_seconds=3600,
)
