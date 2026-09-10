"""Derived compatibility projection of the Agent inventory onto the former Role shape.

``roles.py`` used to be the frozen source of role identities and their exact effect declarations.
Since the Agent model (workflow/agents-and-harnesses.md A1-A4, ``agent_model.py``, the top-level
``agents/`` package) now owns that identity -- ``Agent = spec.md + Harness + Constraints`` -- this
module is a thin, derived read-only projection: ``ROLES`` is rebuilt from ``agent_model.load_agents()``
on every import, one ``Role`` per Agent, so existing importers (``capabilities/*.py`` historically,
now migrated to import ``agents.<name>`` directly; ``package_validation.py``; test fixtures) keep
working without change. New code should use ``agent_model.load_agents``/``agent_definition``/
``resolve_agent`` directly instead of this projection.
"""

from __future__ import annotations

from dataclasses import dataclass

from .agent_model import agent_key, load_agents
from .effects import EffectDeclaration


@dataclass(frozen=True)
class Role:
    """One launchable agent identity: its root prompt and exact authority.

    Derived from one ``agent_model.Agent``: ``prompt`` is that Agent's ``spec`` path and
    ``effects`` is its ``constraints.effects``.
    """

    name: str
    prompt: str
    effects: EffectDeclaration


ROLES: dict[str, Role] = {
    name: Role(name=agent.name, prompt=agent.spec, effects=agent.constraints.effects)
    for name, agent in load_agents().items()
}
ROLE_NAMES: tuple[str, ...] = tuple(ROLES)


def external_role_name(role_name: str) -> str:
    """Return the ``concorde-<hyphenated>`` external identity for one role."""

    return "concorde-" + ROLES[role_name].name.replace("_", "-")


def role_key(name: str) -> str:
    """Normalize an external (``concorde-spec-engineer``) or bare (``spec-engineer``) role name."""

    return agent_key(name)
