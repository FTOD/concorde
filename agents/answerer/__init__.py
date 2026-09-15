"""Answer one question from explicitly selected complete Module Specs."""
from concorde.harness.agent_model import Agent, Contract
from concorde.harness.effects import EffectDeclaration

AGENT = Agent(
    name="answerer", spec="agents/answerer/spec.md", workspace="capsule",
    contract=Contract(
        phase="route", action="ask",
        context="concorde-main-stage-context", result="concorde-main-stage-result",
        effects=EffectDeclaration(("discovery-context",), (), False, "none"),
        outcomes=("completed", "expand", "spec_incomplete", "unsupported", "conflicting")),
    tools=("read", "grep", "find", "ls"),
    timeout_seconds=900,
)
