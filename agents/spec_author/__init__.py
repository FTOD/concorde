"""Spec author Agent: reconciles one target's complete Markdown collection and diagrams (A1)."""

from __future__ import annotations

from concorde.harness.agent_model import Agent, Constraints
from concorde.harness.effects import EffectDeclaration
from concorde.harness.harness import SPEC_CAPSULE

AGENT = Agent(
    name="spec_author",
    spec="agents/spec_author/spec.md",
    harness=SPEC_CAPSULE,
    constraints=Constraints(
        effects=EffectDeclaration(("spec-context",), (), False, "none"),
        contexts=("concorde-agent-stage-context", "concorde-topology-author-context"),
        results=("concorde-agent-stage-result", "concorde-topology-author-result"),
    ),
)
