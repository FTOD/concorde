"""Stable programmer capability boundary and explicit task modes."""
from concorde.harness.agent_model import Agent, Constraints, Mode
from concorde.harness.effects import EffectDeclaration
from concorde.harness.harness import IMPLEMENTATION_WORKSPACE

MODES = (
    Mode('implementation', "agents/programmer/modes/implementation.md",
        Constraints(EffectDeclaration(('spec-context', 'implementation'), ('implementation',), False, "none"),
                    contexts=('concorde-agent-stage-context',), results=('concorde-agent-stage-result',)),
        phase='implementation', action=None, stage_inputs=('concorde-implementation-task', 'concorde-review-result'), required_inputs=('concorde-implementation-task',),
        output_fields=('tasks',), outcomes=()),
    Mode('code-review', "agents/programmer/modes/code-review.md",
        Constraints(EffectDeclaration(('spec-context', 'implementation'), (), False, "none"),
                    contexts=('concorde-review-stage-context',), results=('concorde-review-stage-result',)),
        phase='code-review', action=None, stage_inputs=(), required_inputs=(),
        output_fields=(), outcomes=()),
    Mode('investigation', "agents/programmer/modes/investigation.md",
        Constraints(EffectDeclaration(('spec-context', 'implementation'), (), False, "none"),
                    contexts=('concorde-agent-stage-context',), results=('concorde-agent-stage-result',)),
        phase='implementation', action=None, stage_inputs=('concorde-reflection-selection',), required_inputs=('concorde-reflection-selection',),
        output_fields=('reflection_findings',), outcomes=()),
)

AGENT = Agent(
    name='programmer', spec="agents/programmer/spec.md", harness=IMPLEMENTATION_WORKSPACE,
    constraints=Constraints(EffectDeclaration(('spec-context', 'implementation'), ('implementation',), False, "none"),
        contexts=('concorde-agent-stage-context', 'concorde-review-stage-context'), results=('concorde-agent-stage-result', 'concorde-review-stage-result')),
    modes=MODES,
)
