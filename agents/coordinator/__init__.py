"""Stable coordinator capability boundary and explicit task modes."""
from concorde.harness.agent_model import Agent, Constraints, Mode
from concorde.harness.effects import EffectDeclaration
from concorde.harness.harness import DISCOVERY_CAPSULE

MODES = (
    Mode('ask', "agents/coordinator/modes/ask.md",
        Constraints(EffectDeclaration(('discovery-context',), (), False, "none"),
                    contexts=('concorde-main-stage-context',), results=('concorde-main-stage-result',)),
        phase='route', action='ask', stage_inputs=(), required_inputs=(),
        output_fields=(), outcomes=('completed', 'expand', 'spec_incomplete', 'unsupported', 'conflicting')),
    Mode('route', "agents/coordinator/modes/route.md",
        Constraints(EffectDeclaration(('discovery-context',), (), False, "none"),
                    contexts=('concorde-main-stage-context',), results=('concorde-main-stage-result',)),
        phase='route', action='route', stage_inputs=(), required_inputs=(),
        output_fields=('routes',), outcomes=('routed', 'expand', 'spec_incomplete', 'unsupported', 'conflicting')),
    Mode('design-topology', "agents/coordinator/modes/design-topology.md",
        Constraints(EffectDeclaration(('discovery-context',), (), False, "none"),
                    contexts=('concorde-main-stage-context',), results=('concorde-main-stage-result',)),
        phase='route', action='design-topology', stage_inputs=(), required_inputs=(),
        output_fields=('topology_design',), outcomes=('topology_proposed', 'expand', 'spec_incomplete', 'unsupported', 'conflicting')),
)

AGENT = Agent(
    name='coordinator', spec="agents/coordinator/spec.md", harness=DISCOVERY_CAPSULE,
    constraints=Constraints(EffectDeclaration(('discovery-context',), (), False, "none"),
        contexts=('concorde-main-stage-context',), results=('concorde-main-stage-result',)),
    modes=MODES,
)
