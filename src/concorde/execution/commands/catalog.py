"""The command catalog: the execution commands, deterministic runs recorded like Operations.

Each is a ``concorde <name>`` command of the bound workspace that launches no worker. Its run is
recorded in the run store, so a later run may admit its output with ``--input`` and a workflow
may take it as a step.
"""

from __future__ import annotations

import importlib

# name -> "module:attribute" of the definition; imported only when the command runs.
COMMANDS: dict[str, str] = {
    "task-validation": "concorde.method.validation.command:TASK_VALIDATION",
    "delivery": "concorde.method.delivery.command:DELIVERY",
    "scaffold": "concorde.method.scaffold.command:SCAFFOLD",
}


def command(name: str):
    """The definition of an execution command; KeyError for an unknown name."""
    module, attribute = COMMANDS[name].split(":")
    return getattr(importlib.import_module(module), attribute)


__all__ = ["COMMANDS", "command"]
