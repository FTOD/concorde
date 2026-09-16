"""Concorde's capability inventory (proposal section 6): one Python module per capability.

A capability is the executable unit the host runs. Every module independently declares:

- ``PUBLIC``: a required boolean selecting a developer-facing Skill and launcher entry.
- ``CONTEXT_SELECTION``: ``"discover"`` for discovery-worker selection, ``"bound"`` for an already
  selected Module, or ``"none"`` for deterministic host work without Agent context selection.
- ``DETERMINISTIC``: a required boolean; true means no supported path calls a model, including
  routing and transitive composition.
- ``AGENTS``: the Agent objects it launches itself, and ``USES``: capabilities it composes.
- ``REQUEST``/``RESPONSE`` schemas and ``run(host, configuration, request)``.

These properties are independent contracts, not capability classes. A capability can compose other
capabilities regardless of their size or public exposure. Non-public capabilities are admitted only
through declared host composition. A bound context never becomes permission to discover more.
A module missing from the inventory, or an inventory name with no module, is invalid.
Determinism does not promise identical output, purity or absence of filesystem/process effects.

Every external identifier a capability owns — its skill name, its wire type names, its Studio
graph — is ``concorde-`` plus this module's own hyphenated name; ``external_name`` is the one
place that spells that rule out, so nothing else has to.
"""

from __future__ import annotations

CAPABILITIES = (
    "main",
    "dev_loop",
    "specify_loop",
    "issues",
    "init",
    "configure",
    "validate",
    "deliver",
    "specify",
    "review",
    "context_solve",
    "plan",
    "tasks",
    "implement",
)


def external_name(module_name: str) -> str:
    """Return the ``concorde-<hyphenated>`` identity a capability module's name derives."""

    return "concorde-" + module_name.replace("_", "-")
