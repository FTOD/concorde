"""Child-process environments for tests: the ambient Concorde selection never crosses.

A tester or developer session that runs this suite may carry ``CONCORDE_SESSION_SELECTION``, a
``concorde/1`` entry in ``PI_SUBAGENT_EXTENSION_BINDINGS``, ``CONCORDE_NATIVE_PROJECT_ROOT`` or
``CONCORDE_WORKER_POLICY``. Those bind *that* session to one exact candidate Pi entry, native
project or terminal-worker grant. A fixture install, harness or launcher started by a test must
not inherit them: the private entry verifies a selection against its own workspace and refuses a
foreign one, and a terminal-worker policy refuses every Operation. Every test that derives a
child environment from ``os.environ`` starts from :func:`scrub_selection`.

This is a denylist on purpose. ``concorde.harness.harness.SAFE_ENVIRONMENT`` is the runtime's
allowlist for terminal workers; fixtures still need PATH additions, package caches, wheelhouses,
scratch directories and other test variables that an allowlist would drop.
"""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from contextlib import contextmanager
from unittest.mock import patch

SELECTION_VARIABLES: tuple[str, ...] = (
    "CONCORDE_SESSION_SELECTION",
    "CONCORDE_NATIVE_PROJECT_ROOT",
    "CONCORDE_WORKER_POLICY",
)
BINDINGS_VARIABLE = "PI_SUBAGENT_EXTENSION_BINDINGS"
CONCORDE_BINDING = "concorde/1"


def scrub_selection(environment: Mapping[str, str]) -> dict[str, str]:
    """Copy ``environment`` without the variables that bind a process to a selected candidate.

    Other pi-subagents extension bindings are kept; only the Concorde binding is removed, and
    the variable disappears when nothing else remains. An unreadable bindings value is dropped.
    """
    result = dict(environment)
    for key in SELECTION_VARIABLES:
        result.pop(key, None)
    raw = result.get(BINDINGS_VARIABLE)
    if raw is not None:
        try:
            bindings = json.loads(raw)
        except ValueError:
            bindings = None
        if isinstance(bindings, dict):
            bindings.pop(CONCORDE_BINDING, None)
        if bindings:
            result[BINDINGS_VARIABLE] = json.dumps(bindings)
        else:
            result.pop(BINDINGS_VARIABLE)
    return result


def child_environment(**overrides: str) -> dict[str, str]:
    """The current environment without the ambient selection, plus explicit overrides."""
    return {**scrub_selection(os.environ), **overrides}


@contextmanager
def scrubbed_process_environment(**overrides: str):
    """Run in-process code (an installer, a launcher entry) under a scrubbed ``os.environ``.

    ``patch.dict(..., clear=True)`` replaces the whole mapping for the block and restores it
    afterwards, so subprocesses the code starts from ``os.environ`` inherit no ambient selection.
    """
    with patch.dict(os.environ, child_environment(**overrides), clear=True):
        yield
