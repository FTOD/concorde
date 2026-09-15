"""Review one Module's granted implementation against its complete contracts, read-only."""
from concorde.harness.agent_model import Agent, Child, Contract
from concorde.harness.effects import EffectDeclaration

AGENT = Agent(
    name="code_reviewer", spec="agents/code_reviewer/spec.md", workspace="project",
    contract=Contract(
        phase="code-review",
        context="concorde-review-stage-context", result="concorde-review-stage-result",
        effects=EffectDeclaration(("spec-context", "implementation", "references"), (), False, "none")),
    tools=("read", "grep", "find", "ls"),
    children=(Child("scout", "agents/code_reviewer/children/scout.md"),
              Child("verifier", "agents/code_reviewer/children/verifier.md")),
    timeout_seconds=3600,
)
