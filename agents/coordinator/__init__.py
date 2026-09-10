"""Coordinator Agent: answers from complete Spec contexts, routes work and designs topology (A1)."""

from __future__ import annotations

from concorde.harness.agent_model import Agent, Constraints
from concorde.harness.effects import EffectDeclaration
from concorde.harness.harness import DISCOVERY_CAPSULE

AGENT = Agent(
    name="coordinator",
    spec="agents/coordinator/spec.md",
    harness=DISCOVERY_CAPSULE,
    constraints=Constraints(
        effects=EffectDeclaration(("discovery-context",), (), False, "none"),
        contexts=("concorde-main-stage-context",),
        results=("concorde-main-stage-result",),
    ),
)
