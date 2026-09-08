"""Context assessor Agent: decides whether one task is resolvable from the admitted Spec (A1)."""

from __future__ import annotations

from concorde.host.agent_model import Agent, Constraints
from concorde.host.effects import EffectDeclaration
from concorde.host.harness import SPEC_CAPSULE

AGENT = Agent(
    name="context_assessor",
    spec="agents/context_assessor/spec.md",
    harness=SPEC_CAPSULE,
    constraints=Constraints(
        effects=EffectDeclaration(("spec-context",), (), False, "none"),
        contexts=("concorde-agent-stage-context",),
        results=("concorde-agent-stage-result",),
    ),
)
