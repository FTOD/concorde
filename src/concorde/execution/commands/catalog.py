"""The command catalog: the execution commands the installed parts register.

Each is a ``concorde <name>`` command of the bound workspace that launches no worker. Its run is
recorded in the run store, so a later run may admit its output with ``--input`` and a workflow
may take it as a step. A part registers its commands when its code loads; Execution provides none.
"""

from __future__ import annotations

from ..operations.catalog import Catalog

COMMANDS = Catalog("command")


__all__ = ["COMMANDS"]
