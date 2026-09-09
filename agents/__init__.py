"""Concorde's Agent inventory (workflow/agents-and-harnesses.md A1): one Python package per named
Agent, each binding its authored ``spec.md``, Harness reference and Constraints/Permissions
(``concorde.host.agent_model.Agent``) in its own ``agents/<name>/__init__.py``.

This file is the package-owned inventory declaration -- it mirrors ``capabilities/__init__.py`` --
and belongs to the build (``implementation.build``, referenced by ``module.distribution``). Each
``agents/<name>/`` directory and its ``spec.md`` belong to ``implementation.agent-definitions``,
referenced by ``module.harness``, which owns Agent and Harness definitions; a capability that
launches an Agent does not own its definition.

A module named here with no matching ``agents/<name>/__init__.py`` package, or a package present
with no matching name here, is a validation error (``CONCORDE-AGENT-INVENTORY-001``).
"""

from __future__ import annotations

AGENTS = (
    "coordinator",
    "spec_author",
    "context_assessor",
    "planner",
    "task_author",
    "implementation_worker",
    "spec_reviewer",
    "code_reviewer",
)


def external_name(module_name: str) -> str:
    """Return the ``concorde-<hyphenated>`` identity an Agent module's name derives."""

    return "concorde-" + module_name.replace("_", "-")
