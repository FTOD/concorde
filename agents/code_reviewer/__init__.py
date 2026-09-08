"""Code reviewer Agent: independent read-only code review of one bound target (A1)."""

from __future__ import annotations

from concorde.host.agent_model import Agent, Constraints
from concorde.host.effects import EffectDeclaration
from concorde.host.harness import IMPLEMENTATION_WORKSPACE

AGENT = Agent(
    name="code_reviewer",
    spec="agents/code_reviewer/spec.md",
    harness=IMPLEMENTATION_WORKSPACE,
    constraints=Constraints(
        effects=EffectDeclaration(("spec-context", "implementation"), (), False, "none"),
        contexts=("concorde-review-stage-context",),
        results=("concorde-review-stage-result",),
    ),
)
