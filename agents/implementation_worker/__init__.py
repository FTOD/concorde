"""Implementation worker Agent: fulfils task acceptance under a granted code boundary (A1)."""

from __future__ import annotations

from concorde.host.agent_model import Agent, Constraints
from concorde.host.effects import EffectDeclaration
from concorde.host.harness import IMPLEMENTATION_WORKSPACE

AGENT = Agent(
    name="implementation_worker",
    spec="agents/implementation_worker/spec.md",
    harness=IMPLEMENTATION_WORKSPACE,
    constraints=Constraints(
        effects=EffectDeclaration(("spec-context", "implementation"), ("implementation",), False, "none"),
        contexts=("concorde-agent-stage-context",),
        results=("concorde-agent-stage-result",),
    ),
)
