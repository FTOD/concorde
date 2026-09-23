"""Choose bounded work or an evidence-grounded disposition for one selected Issue."""

from concorde.harness.worker_profile import AgentDefinition

DEFINITION = AgentDefinition(
    name="issue_solver",
    instructions="agents/issue_solver/spec.md",
    workspace="capsule",
    phase="issue-solve",
    context="concorde-agent-stage-context",
    result="concorde-agent-stage-result",
    reads=("spec-context",),
    writes=(),
    stage_inputs=("concorde-issue-selection", "concorde-issue-context"),
    required_inputs=("concorde-issue-selection",),
    output_fields=("issue_decision",),
    tools=("read", "grep", "find", "ls"),
    timeout_seconds=1800,
    hook="concorde.issue_solving.native:issue_solver",
)
