"""Design one candidate topology change from selected complete Module Specs and the registry."""
from concorde.harness.agent_model import Agent, Contract
from concorde.harness.effects import EffectDeclaration

AGENT = Agent(
    name="topology_designer", spec="agents/topology_designer/spec.md", workspace="capsule",
    contract=Contract(
        phase="route", action="design-topology",
        context="concorde-main-stage-context", result="concorde-main-stage-result",
        effects=EffectDeclaration(("discovery-context",), (), False, "none"),
        output_fields=("topology_design",),
        outcomes=("topology_proposed", "expand", "spec_incomplete", "unsupported", "conflicting")),
    tools=("read", "grep", "find", "ls"),
    timeout_seconds=900,
)
