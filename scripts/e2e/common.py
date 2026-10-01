"""What the end-to-end tools share: the checkout, the end-to-end root, errors, commands, clones."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

CHECKOUT = Path(__file__).resolve().parents[2]
# Where prepared projects live unless CONCORDE_E2E_ROOT says otherwise: in this checkout's
# .claude/worktrees/, which Git ignores and where every worktree a worker runs in lies, each as
# test-<name>, removed when its test is done.
DEFAULT_ROOT = CHECKOUT / ".claude/worktrees"
# The prefix of every test project's directory, and of every scratch clone the tools make there.
TEST_PREFIX = "test-"


class E2EError(Exception):
    def __init__(self, code: str, detail: str, **evidence):
        super().__init__(detail)
        self.code = code
        self.detail = detail
        self.evidence = evidence


def run(command: list[str], cwd: Path, **options) -> subprocess.CompletedProcess:
    """Run a command; ``E2EError`` names it, its exit status and its output when it fails."""
    completed = subprocess.run(
        command, cwd=cwd, capture_output=True, text=True, check=False, **options
    )
    if completed.returncode != 0:
        raise E2EError(
            "command_failed",
            f"`{' '.join(command)}` in {cwd} exited with status {completed.returncode}",
            stdout=completed.stdout[-3000:],
            stderr=completed.stderr[-3000:],
        )
    return completed


def e2e_root() -> Path:
    return Path(os.environ.get("CONCORDE_E2E_ROOT") or DEFAULT_ROOT).expanduser()


def test_directory(root: Path, name: str) -> Path:
    """The directory of the test project ``name`` under the end-to-end root ``root``."""
    return root / f"{TEST_PREFIX}{name}"


def repository_url(repo: str) -> str:
    return f"https://github.com/{repo}.git"


def clone(url: str, rev: str, project: Path) -> None:
    """Check ``rev`` of ``url`` out as the branch ``main`` of a new repository ``project``, with
    no history before it. ``rev`` may be a tag, a branch or a commit, as SWE-bench's base commits
    are, which ``git clone --branch`` does not accept."""
    project.mkdir(parents=True)
    run(["git", "init", "-q"], cwd=project)
    run(["git", "remote", "add", "origin", url], cwd=project)
    run(["git", "fetch", "-q", "--depth", "1", "origin", rev], cwd=project)
    run(["git", "checkout", "-q", "-b", "main", "FETCH_HEAD"], cwd=project)
