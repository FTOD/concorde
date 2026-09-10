"""Concorde's capability inventory (proposal section 6): one Python module per capability.

A capability is the executable unit the host runs: a module declaring ``CLASS`` (``"global"``,
``"lifecycle"`` or ``"stage"``), ``DETERMINISTIC`` (a required bool: no supported path calls a
model, including host routing and transitive composition), ``AGENTS`` (the ``agent_model.Agent`` objects, from the top-level
``agents/`` package, it launches itself), ``USES`` (the other capabilities it composes),
``REQUEST``/``RESPONSE`` (JSON Schema dicts) and a ``run(host, configuration, request)`` function.
A module not listed here, or a listed name with no module, is a validation error (deferred to the
B2 validator consolidation).

``DETERMINISTIC`` is independent of context-selection class and describes the whole capability,
not one invocation. False means a model call is possible, even if a status or preview path makes
none. True does not promise identical output, purity or absence of filesystem/process effects.

Every external identifier a capability owns — its skill name, its wire type names, its Studio
graph — is ``concorde-`` plus this module's own hyphenated name; ``external_name`` is the one
place that spells that rule out, so nothing else has to.
"""

from __future__ import annotations

CAPABILITIES = (
    "main",
    "dev_loop",
    "reflections_triage",
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
