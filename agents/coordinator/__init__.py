"""Coordinator Agent: routes work and designs/synthesizes system topology (A1)."""

from __future__ import annotations

from concorde.host.agent_model import Agent, Constraints
from concorde.host.effects import EffectDeclaration
from concorde.host.harness import DISCOVERY_CAPSULE

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
