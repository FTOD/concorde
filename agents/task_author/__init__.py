"""Task author Agent: turns an accepted plan into observable acceptance tasks (A1)."""

from __future__ import annotations

from concorde.host.agent_model import Agent, Constraints
from concorde.host.effects import EffectDeclaration
from concorde.host.harness import SPEC_CAPSULE

AGENT = Agent(
    name="task_author",
    spec="agents/task_author/spec.md",
    harness=SPEC_CAPSULE,
    constraints=Constraints(
        effects=EffectDeclaration(("spec-context",), (), False, "none"),
        contexts=("concorde-agent-stage-context",),
        results=("concorde-agent-stage-result",),
    ),
)
