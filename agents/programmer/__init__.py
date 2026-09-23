"""Fulfil one Module's implementation tasks in its candidate worktree."""

from concorde.harness.worker_profile import AgentDefinition

DEFINITION = AgentDefinition(
    name="programmer",
    instructions="agents/programmer/spec.md",
    workspace="project",
    phase="implementation",
    context="concorde-agent-stage-context",
    result="concorde-agent-stage-result",
    reads=("spec-context", "implementation", "references"),
    writes=("implementation",),
    stage_inputs=(
        "concorde-implementation-task",
        "concorde-review-result",
        "concorde-issue-context",
    ),
    required_inputs=("concorde-implementation-task",),
    output_fields=("tasks",),
    tools=("read", "grep", "find", "ls", "edit", "write", "bash", "run_checks"),
    timeout_seconds=3600,
    hook="concorde.implementation.hooks:programmer",
)
