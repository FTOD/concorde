"""A project installed without some parts: its own ``concorde`` refuses their commands.

Distribution's ``concorde`` refuses a command of a part the project has not installed with its
``part_missing`` link naming the part, which this helper prints with Distribution's own code. ``without`` gives a test project such a ``concorde``, tracked at
``.concorde/bin/concorde`` like an installed one and so present in every task worktree opened after
it: it refuses the commands of the parts named, and runs every other command with this checkout's
package. ``without_spec`` removes the registry mirror whose existence tells that the spec part is
installed.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from tests.concorde.support.paths import REPOSITORY_ROOT

# The commands each part registers that the parts relying on it ask for.
COMMANDS = {
    "execution": ("run",),
    "method": ("delivery", "task-validation"),
    "issues": ("issues",),
}

SCRIPT = """\
#!{python}
import json, os, sys

sys.path.insert(0, {source!r})
from concorde.distribution.cli import part_missing

ABSENT = {absent!r}
words = sys.argv[1:]
if words and words[0] in ABSENT:
    print(json.dumps({{"error": part_missing(ABSENT[words[0]], "commands", words[0])}}))
    sys.exit(1)
os.environ["PYTHONPATH"] = {source!r}
os.execv(sys.executable, [sys.executable, "-m", "concorde", *words])
"""


def _commit(root: Path, message: str) -> None:
    subprocess.run(["git", "add", "-A"], cwd=root, check=True, capture_output=True)
    subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", message],
        cwd=root,
        check=True,
        capture_output=True,
    )


def without(root: Path, *parts: str) -> Path:
    """Commit a ``concorde`` of ``root`` that refuses the commands of ``parts``; its path."""
    absent = {command: part for part in parts for command in COMMANDS[part]}
    path = root / ".concorde/bin/concorde"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        SCRIPT.format(
            python=sys.executable, absent=absent, source=str(REPOSITORY_ROOT / "src")
        )
    )
    path.chmod(0o755)
    _commit(root, f"install Concorde without {', '.join(parts)}")
    return path


def without_spec(root: Path) -> None:
    """Remove and commit away the registry mirror, as a project without the spec part has none."""
    (root / ".concorde/specs.json").unlink()
    _commit(root, "install Concorde without the spec part")


__all__ = ["COMMANDS", "without", "without_spec"]
