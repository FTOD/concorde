"""Decide whether one Module's Spec context suffices for a task before planning."""

from concorde.harness.effects import EffectDeclaration
from concorde.harness.worker_profile import Contract, WorkerProfile

from .. import external_name

PROFILE = WorkerProfile(
    name="context_assessor",
    spec="operations/context_assessor/spec.md",
    workspace="capsule",
    contract=Contract(
        phase="context-solve",
        context="concorde-agent-stage-context",
        result="concorde-agent-stage-result",
        effects=EffectDeclaration(("spec-context",), (), False, "none"),
        outcomes=("sufficient", "spec_incomplete", "unsupported", "conflicting"),
    ),
    tools=("read", "grep", "find", "ls"),
    timeout_seconds=1800,
)

PUBLIC = False
CONTEXT_SELECTION = "bound"
DETERMINISTIC = False
USES = ()
EXTERNAL_NAME = external_name(__name__.rsplit(".", 1)[-1])
KIND = "agent"
