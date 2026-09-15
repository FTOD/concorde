"""Fulfil one Module's implementation tasks in its candidate worktree."""
from concorde.harness.agent_model import Agent, Child, Contract
from concorde.harness.effects import EffectDeclaration

AGENT = Agent(
    name="programmer", spec="agents/programmer/spec.md", workspace="project",
    contract=Contract(
        phase="implementation",
        context="concorde-agent-stage-context", result="concorde-agent-stage-result",
        effects=EffectDeclaration(("spec-context", "implementation", "references"), ("implementation",), False, "none"),
        stage_inputs=("concorde-implementation-task", "concorde-review-result"),
        required_inputs=("concorde-implementation-task",),
        output_fields=("tasks",)),
    tools=("read", "grep", "find", "ls", "edit", "write", "bash", "run_checks"),
    children=(Child("scout", "agents/programmer/children/scout.md"),
              Child("planner", "agents/programmer/children/planner.md"),
              Child("verifier", "agents/programmer/children/verifier.md")),
    timeout_seconds=3600,
)
