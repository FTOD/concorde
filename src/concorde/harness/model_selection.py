"""Per-Agent-node model selection: the integration, model and reasoning effort of every launch.

The project capability configuration names a default ``integration``, ``model`` and
``reasoning_effort`` and, under ``agents``, overrides keyed either by an Agent (``programmer``) or
by one Agent node (``programmer/implementation``, the name ``AgentNode`` compiles and Studio
shows). A launch resolves the project default, then the Agent entry, then the node entry, each value
independently, so the most specific entry wins. An entry that switches to another integration
starts from that client's own defaults instead of inheriting a model or effort chosen for a
different client.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

from ..spec.typed_data import TypedDataError

# The effort levels each client's command line admits; a model may support only some of them.
REASONING_EFFORTS = {
    "codex": ("minimal", "low", "medium", "high", "xhigh", "max", "ultra"),
    "claude": ("low", "medium", "high", "xhigh", "max"),
}


@dataclass(frozen=True)
class AgentSelection:
    integration: str
    model: str | None = None
    reasoning_effort: str | None = None

    def wire(self) -> dict:
        return asdict(self)

    def model_arguments(self) -> dict:
        """The keyword arguments a Codex or Claude launch renderer takes."""
        return {"model": self.model, "reasoning_effort": self.reasoning_effort}


def _narrow(selection: AgentSelection, entry: dict) -> AgentSelection:
    integration = entry.get("integration", selection.integration)
    if integration != selection.integration:
        selection = AgentSelection(integration)
    return AgentSelection(integration, entry.get("model", selection.model),
                          entry.get("reasoning_effort", selection.reasoning_effort))


def agent_selection(configuration: dict, agent: str, mode: str | None = None) -> AgentSelection:
    """Resolve one Agent node's selection; ``agent`` may be bare, hyphenated or ``concorde-`` named."""
    from .agent_model import agent_key

    data = configuration["data"]
    selection = AgentSelection(data["integration"], data.get("model"), data.get("reasoning_effort"))
    overrides = data.get("agents", {})
    name = agent_key(agent)
    for key in (name, f"{name}/{mode}" if mode is not None else None):
        if key in overrides:
            selection = _narrow(selection, overrides[key])
    return selection


def validate_agent_selections(configuration: dict, field: str = "/configuration") -> None:
    """Reject keys naming no Agent or Agent node, and any node whose resolved selection cannot run."""
    from .agent_model import load_agents

    agents = load_agents()
    nodes = {name: (agent, None) for name, agent in agents.items()}
    nodes.update({f"{name}/{mode.name}": (agent, mode.name)
                  for name, agent in agents.items() for mode in agent.modes})
    for key in configuration["data"].get("agents", {}):
        if key not in nodes:
            raise TypedDataError("invalid_field", f"{field}/data/agents/" + key.replace("~", "~0").replace("/", "~1"),
                                 "names no Agent or Agent node; use an Agent such as programmer or an "
                                 "Agent node such as programmer/implementation")
    for key, (agent, mode) in sorted(nodes.items()):
        selection = agent_selection(configuration, agent.name, mode)
        if selection.integration not in agent.harness.integrations:
            raise TypedDataError("invalid_field", f"{field}/data/agents",
                                 f"{key} selects integration {selection.integration}, outside its Harness")
        if (selection.reasoning_effort is not None
                and selection.reasoning_effort not in REASONING_EFFORTS[selection.integration]):
            raise TypedDataError("invalid_field", f"{field}/data/agents",
                                 f"{key} selects reasoning effort {selection.reasoning_effort}, which "
                                 f"{selection.integration} does not admit")
