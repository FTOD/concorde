"""Route one task to exactly one owning Module from explicitly selected complete Module Specs."""
from concorde.harness.agent_model import Agent, Contract
from concorde.harness.effects import EffectDeclaration

AGENT = Agent(
    name="router", spec="agents/router/spec.md", workspace="capsule",
    contract=Contract(
        phase="route", action="route",
        context="concorde-main-stage-context", result="concorde-main-stage-result",
        effects=EffectDeclaration(("discovery-context",), (), False, "none"),
        output_fields=("routes",),
        outcomes=("routed", "expand", "spec_incomplete", "unsupported", "conflicting")),
    tools=("read", "grep", "find", "ls"),
    timeout_seconds=900,
)
