"""A disposable, built copy of this checkout with a saved private session selection."""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

from concorde.distribution.build import PRIVATE_PI_SESSION_SHIM as PI_SESSION_SHIM
from concorde.distribution.build import write_build

from .paths import REPOSITORY_ROOT


def set_up_selected_project(self) -> None:
    """Copy the package sources into a disposable project, build it and save a test selection.

    Sets ``root``, ``project``, ``selection_path``, ``selection`` and ``agent`` on the test case.
    """
    temporary = tempfile.TemporaryDirectory()
    self.addCleanup(temporary.cleanup)
    self.root = Path(temporary.name).resolve()
    self.project = self.root / "project"
    for directory in (
        "agents",
        "prompts",
        "protocol",
        "operations",
        "src",
        "pi",
        "scripts",
    ):
        shutil.copytree(
            REPOSITORY_ROOT / directory,
            self.project / directory,
            ignore=shutil.ignore_patterns("node_modules", "__pycache__"),
        )
    write_build(self.project)
    # Host infrastructure is explicit and local to this disposable fixture, not installed globally.
    (self.project / ".venv").symlink_to(Path(sys.prefix), target_is_directory=True)
    from concorde.distribution.session_selection import (
        save_selection,
        select_session,
    )

    self.selection_path = self.project / ".concorde/work/pi-selection.json"
    self.selection = select_session(
        self.project,
        pi_entry=self.project / PI_SESSION_SHIM,
        runtime=self.project / "scripts/run-operation.py",
    )
    save_selection(self.project, self.selection_path, self.selection)
    self.agent = self.root / "agent"
    self.agent.mkdir()
    (self.agent / "settings.json").write_text(
        json.dumps(
            {
                "defaultProjectTrust": "never",
                "quietStartup": True,
                "enableInstallTelemetry": False,
            }
        )
    )
