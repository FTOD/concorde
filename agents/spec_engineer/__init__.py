"""Stable spec_engineer capability boundary and explicit task modes."""
from concorde.harness.agent_model import Agent, Constraints, Mode
from concorde.harness.effects import EffectDeclaration
from concorde.harness.harness import SPEC_CAPSULE

MODES = (
    Mode('specify', "agents/spec_engineer/modes/specify.md",
        Constraints(EffectDeclaration(('spec-context',), (), False, "none"),
                    contexts=('concorde-agent-stage-context',), results=('concorde-agent-stage-result',)),
        phase='specify', action=None, stage_inputs=(), required_inputs=(),
        output_fields=('documents',), outcomes=()),
    Mode('context-solve', "agents/spec_engineer/modes/context-solve.md",
        Constraints(EffectDeclaration(('spec-context',), (), False, "none"),
                    contexts=('concorde-agent-stage-context',), results=('concorde-agent-stage-result',)),
        phase='context-solve', action=None, stage_inputs=(), required_inputs=(),
        output_fields=(), outcomes=('sufficient', 'spec_incomplete', 'unsupported', 'conflicting')),
    Mode('plan', "agents/spec_engineer/modes/plan.md",
        Constraints(EffectDeclaration(('spec-context',), (), False, "none"),
                    contexts=('concorde-agent-stage-context',), results=('concorde-agent-stage-result',)),
        phase='plan', action=None, stage_inputs=('concorde-plan-artifact',), required_inputs=(),
        output_fields=('plan',), outcomes=()),
    Mode('tasks', "agents/spec_engineer/modes/tasks.md",
        Constraints(EffectDeclaration(('spec-context',), (), False, "none"),
                    contexts=('concorde-agent-stage-context',), results=('concorde-agent-stage-result',)),
        phase='tasks', action=None, stage_inputs=('concorde-plan-artifact', 'concorde-implementation-task', 'concorde-review-result'), required_inputs=('concorde-plan-artifact',),
        output_fields=('tasks',), outcomes=()),
    Mode('spec-review', "agents/spec_engineer/modes/spec-review.md",
        Constraints(EffectDeclaration(('spec-context',), (), False, "none"),
                    contexts=('concorde-review-stage-context',), results=('concorde-review-stage-result',)),
        phase='spec-review', action=None, stage_inputs=(), required_inputs=(),
        output_fields=(), outcomes=()),
    Mode('topology-author', "agents/spec_engineer/modes/topology-author.md",
        Constraints(EffectDeclaration(('spec-context',), (), False, "none"),
                    contexts=('concorde-topology-author-context',), results=('concorde-topology-author-result',)),
        phase='topology-author', action=None, stage_inputs=(), required_inputs=(),
        output_fields=('documents',), outcomes=()),
)

AGENT = Agent(
    name='spec_engineer', spec="agents/spec_engineer/spec.md", harness=SPEC_CAPSULE,
    constraints=Constraints(EffectDeclaration(('spec-context',), (), False, "none"),
        contexts=('concorde-agent-stage-context', 'concorde-review-stage-context', 'concorde-topology-author-context'), results=('concorde-agent-stage-result', 'concorde-review-stage-result', 'concorde-topology-author-result')),
    modes=MODES,
)
