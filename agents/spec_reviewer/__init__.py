"""Review one Module's complete Spec collection against representative tasks."""

from concorde.harness.worker_profile import AgentDefinition

DEFINITION = AgentDefinition(
    name="spec_reviewer",
    instructions="agents/spec_reviewer/spec.md",
    workspace="capsule",
    phase="spec-review",
    context="concorde-review-stage-context",
    result="concorde-review-stage-result",
    reads=("spec-context",),
    writes=(),
    tools=("read", "grep", "find", "ls"),
    timeout_seconds=1800,
    hook="concorde.review.native:spec_reviewer",
)
