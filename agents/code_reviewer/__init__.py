"""Review one Module's implementation against its complete contracts, read-only."""

from concorde.harness.worker_profile import AgentDefinition

DEFINITION = AgentDefinition(
    name="code_reviewer",
    instructions="agents/code_reviewer/spec.md",
    workspace="project",
    phase="code-review",
    context="concorde-review-stage-context",
    result="concorde-review-stage-result",
    reads=("spec-context", "implementation", "references"),
    writes=(),
    tools=("read", "grep", "find", "ls", "run_checks"),
    timeout_seconds=3600,
    hook="concorde.review.native:code_reviewer",
)
