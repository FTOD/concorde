"""Shared helper for tests that exercise the real build or the real graph.

Any test that needs a working built package as a *prerequisite* (worktree affinity, worktree
creation, a Studio graph bound to a temporary root) should build the package root into its own
temporary directory first, rather than depending on the actual checkout being pre-built. Tests
that exercise ``build``/``check_build``/``write_build`` themselves are not this helper's concern;
they call those functions directly.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from .paths import REPOSITORY_ROOT


def build_package_copy(root: Path, integration: str = "all"):
    """Copy ``prompts/`` and ``skills/`` into ``root`` and build them there.

    Requires ``concorde.capabilities.build`` to already be importable (callers insert
    ``RUNTIME_ROOT`` onto ``sys.path`` before importing this helper, as usual). Returns the
    ``BuildResult``.
    """

    from concorde.capabilities.build import write_build

    shutil.copytree(REPOSITORY_ROOT / "prompts", root / "prompts", dirs_exist_ok=True)
    shutil.copytree(REPOSITORY_ROOT / "skills", root / "skills", dirs_exist_ok=True)
    return write_build(root, integration)
