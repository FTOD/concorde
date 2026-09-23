"""Turn an accepted plan into implementation acceptance tasks."""

from concorde.harness.worker_profile import AgentDefinition

DEFINITION = AgentDefinition(
    name="task_author",
    instructions="agents/task_author/spec.md",
    workspace="capsule",
    phase="tasks",
    context="concorde-agent-stage-context",
    result="concorde-agent-stage-result",
    reads=("spec-context", "references"),
    writes=(),
    stage_inputs=(
        "concorde-plan-artifact",
        "concorde-task-identity-constraints",
        "concorde-implementation-task",
        "concorde-review-result",
        "concorde-task-scope-feedback",
        "concorde-issue-context",
    ),
    required_inputs=("concorde-plan-artifact", "concorde-task-identity-constraints"),
    output_fields=("tasks",),
    tools=("read", "grep", "find", "ls"),
    timeout_seconds=1800,
    hook="concorde.planning.hooks:task_author",
)
