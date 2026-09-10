"""Planner Agent: plans contract-level work from the Spec alone (A1)."""

from __future__ import annotations

from concorde.harness.agent_model import Agent, Constraints
from concorde.harness.effects import EffectDeclaration
from concorde.harness.harness import SPEC_CAPSULE

AGENT = Agent(
    name="planner",
    spec="agents/planner/spec.md",
    harness=SPEC_CAPSULE,
    constraints=Constraints(
        effects=EffectDeclaration(("spec-context",), (), False, "none"),
        contexts=("concorde-agent-stage-context",),
        results=("concorde-agent-stage-result",),
    ),
)
