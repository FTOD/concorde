"""Review one Module's complete Spec collection against representative tasks."""
from concorde.harness.agent_model import Agent, Child, Contract
from concorde.harness.effects import EffectDeclaration

AGENT = Agent(
    name="spec_reviewer", spec="agents/spec_reviewer/spec.md", workspace="capsule",
    contract=Contract(
        phase="spec-review",
        context="concorde-review-stage-context", result="concorde-review-stage-result",
        effects=EffectDeclaration(("spec-context",), (), False, "none")),
    tools=("read", "grep", "find", "ls"),
    children=(Child("fact-check", "agents/spec_reviewer/children/fact-check.md"),
              Child("consistency", "agents/spec_reviewer/children/consistency.md")),
    timeout_seconds=1800,
)
