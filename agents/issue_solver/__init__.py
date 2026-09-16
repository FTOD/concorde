"""Choose bounded work or an evidence-grounded disposition for one selected Issue."""
from concorde.harness.agent_model import Agent, Contract
from concorde.harness.effects import EffectDeclaration

AGENT = Agent(
    name="issue_solver", spec="agents/issue_solver/spec.md", workspace="capsule",
    contract=Contract(
        phase="issue-solve", context="concorde-agent-stage-context", result="concorde-agent-stage-result",
        effects=EffectDeclaration(("spec-context",), (), False, "none"),
        stage_inputs=("concorde-issue-selection",), required_inputs=("concorde-issue-selection",),
        output_fields=("issue_decision",)),
    tools=("read", "grep", "find", "ls"),
)
