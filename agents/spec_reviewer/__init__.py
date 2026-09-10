"""Spec reviewer Agent: independent read-only Spec review of one bound target (A1)."""

from __future__ import annotations

from concorde.harness.agent_model import Agent, Constraints
from concorde.harness.effects import EffectDeclaration
from concorde.harness.harness import SPEC_CAPSULE

AGENT = Agent(
    name="spec_reviewer",
    spec="agents/spec_reviewer/spec.md",
    harness=SPEC_CAPSULE,
    constraints=Constraints(
        effects=EffectDeclaration(("spec-context",), (), False, "none"),
        contexts=("concorde-review-stage-context",),
        results=("concorde-review-stage-result",),
    ),
)
