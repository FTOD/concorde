"""Decide whether one Module's Spec context suffices for a task before planning."""

from concorde.harness.worker_profile import AgentDefinition

DEFINITION = AgentDefinition(
    name="context_assessor",
    instructions="agents/context_assessor/spec.md",
    workspace="capsule",
    phase="context-solve",
    context="concorde-agent-stage-context",
    result="concorde-agent-stage-result",
    reads=("spec-context",),
    writes=(),
    outcomes=("sufficient", "spec_incomplete", "unsupported", "conflicting"),
    tools=("read", "grep", "find", "ls"),
    timeout_seconds=1800,
    hook="concorde.planning.hooks:context_assessor",
)
