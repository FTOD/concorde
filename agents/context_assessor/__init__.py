"""Decide whether one Module's Spec context suffices for a task before planning."""
from concorde.harness.agent_model import Agent, Contract
from concorde.harness.effects import EffectDeclaration

AGENT = Agent(
    name="context_assessor", spec="agents/context_assessor/spec.md", workspace="capsule",
    contract=Contract(
        phase="context-solve",
        context="concorde-agent-stage-context", result="concorde-agent-stage-result",
        effects=EffectDeclaration(("spec-context",), (), False, "none"),
        outcomes=("sufficient", "spec_incomplete", "unsupported", "conflicting")),
    tools=("read", "grep", "find", "ls"),
    timeout_seconds=1800,
)
