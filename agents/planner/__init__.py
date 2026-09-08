"""Planner Agent: plans contract-level work from the Spec alone (A1)."""

from __future__ import annotations

from concorde.host.agent_model import Agent, Constraints
from concorde.host.effects import EffectDeclaration
from concorde.host.harness import SPEC_CAPSULE

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
