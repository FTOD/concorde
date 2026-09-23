"""Plan contract-level work for one Module from its complete Spec."""

from concorde.harness.worker_profile import AgentDefinition

DEFINITION = AgentDefinition(
    name="planner",
    instructions="agents/planner/spec.md",
    workspace="capsule",
    phase="plan",
    context="concorde-agent-stage-context",
    result="concorde-agent-stage-result",
    reads=("spec-context", "references"),
    writes=(),
    stage_inputs=("concorde-plan-artifact",),
    output_fields=("plan",),
    tools=("read", "grep", "find", "ls"),
    timeout_seconds=1800,
    hook="concorde.planning.hooks:planner",
)
