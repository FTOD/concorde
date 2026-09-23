"""Child-process environments for tests: Concorde's own session variables never cross.

A developer session that runs this suite may itself be a Concorde worker or run Operations, and
carry variables such as ``CLAUDE_CONFIG_DIR`` or ``CONCORDE_RUN_ID`` that bind it to one run. A
process started by a test must not inherit them. This is a denylist on purpose: fixtures still
need PATH additions, package caches and scratch directories that an allowlist would drop.
"""

from __future__ import annotations

import os
from collections.abc import Mapping

SESSION_VARIABLES: tuple[str, ...] = (
    "CLAUDE_CONFIG_DIR",
    "CONCORDE_RUN_ID",
    "CONCORDE_GRANT",
)


def scrub_session(environment: Mapping[str, str]) -> dict[str, str]:
    """Copy ``environment`` without the variables that bind a process to one Concorde run."""
    return {
        key: value for key, value in environment.items() if key not in SESSION_VARIABLES
    }


def child_environment(**overrides: str) -> dict[str, str]:
    """The current environment without the session variables, plus explicit overrides."""
    return {**scrub_session(os.environ), **overrides}
