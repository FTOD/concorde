"""The develop install: what makes a Concorde checkout a valid source for it, and its guidance.

A develop install runs the Concorde of an independent Concorde repository that the developer also
changes. It is made and updated only from the clean primary worktree of that repository, on a
branch: a task worktree disappears once its branch is merged, a detached checkout names no line of
development, and uncommitted changes would install a Concorde no commit records. The installer
calls ``develop_source`` before writing anything and adds ``guidance`` to the main-session guidance
it places.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

SKILL_SECTION = "generated/dogfooding/skill.md"
CLAUDE_MD_SECTION = "generated/dogfooding/claude-md.md"
# How many uncommitted paths a refusal names before it only counts the rest.
SHOWN_CHANGES = 10


class DevelopError(RuntimeError):
    """A refused develop install, with the code the installer reports it under."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def _git(package: Path, *argv: str) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            ["git", "-C", str(package), *argv],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise DevelopError(
            "develop_source_unreadable",
            f"`git -C {package} {' '.join(argv)}` could not run ({error}); a develop install "
            "needs Git to check the Concorde repository it installs from",
        ) from error


def develop_source(package: str | Path) -> dict:
    """The repository, branch and commit a develop install of ``package`` installs from.

    Refuses a package that is not the root of the primary worktree of a Git repository, whose
    ``HEAD`` is detached, or that has uncommitted or untracked changes.
    """
    package = Path(package).resolve()
    top = _git(package, "rev-parse", "--show-toplevel")
    if top.returncode != 0 or Path(top.stdout.strip()).resolve() != package:
        found = (
            f"it lies inside the worktree {top.stdout.strip()}"
            if top.returncode == 0
            else f"it is not in a Git worktree ({top.stderr.strip() or 'git failed'})"
        )
        raise DevelopError(
            "develop_source_not_repository",
            f"a develop install is made from the root of a Concorde repository's worktree, but "
            f"{package} is not one: {found}",
        )
    directories = _git(
        package, "rev-parse", "--path-format=absolute", "--git-dir", "--git-common-dir"
    )
    own, common = (Path(line).resolve() for line in directories.stdout.split())
    if own != common:
        raise DevelopError(
            "develop_source_not_primary",
            f"{package} is a linked worktree of the Concorde repository whose primary "
            f"worktree is {common.parent}; a develop install is made from the primary "
            "worktree, since a task worktree disappears once its branch is merged",
        )
    branch = _git(package, "symbolic-ref", "--quiet", "--short", "HEAD")
    if branch.returncode != 0:
        raise DevelopError(
            "develop_source_detached",
            f"the HEAD of {package} is detached; check out the branch tasks merge into "
            "before installing from it",
        )
    status = _git(package, "status", "--porcelain", "--untracked-files=normal")
    changed = [line[3:] for line in status.stdout.splitlines() if line.strip()]
    if status.returncode != 0 or changed:
        shown = ", ".join(changed[:SHOWN_CHANGES])
        more = len(changed) - SHOWN_CHANGES
        detail = (
            status.stderr.strip()
            if status.returncode != 0
            else f"{shown}{f' and {more} more' if more > 0 else ''}"
        )
        raise DevelopError(
            "develop_source_dirty",
            f"{package} has uncommitted changes ({detail}); a develop install runs only "
            "committed Concorde, so commit or merge them first",
        )
    commit = _git(package, "rev-parse", "--verify", "HEAD").stdout.strip()
    return {
        "repository": str(package),
        "branch": branch.stdout.strip(),
        "commit": commit,
    }


def guidance(package: str | Path) -> tuple[str, str]:
    """The rendered develop sections of the skill and of the ``CLAUDE.md`` block."""
    package = Path(package)
    sections = []
    for relative in (SKILL_SECTION, CLAUDE_MD_SECTION):
        path = package / relative
        if not path.is_file():
            raise DevelopError("stale_build", f"{path} is missing; run the build")
        sections.append(path.read_text(encoding="utf-8"))
    return sections[0], sections[1]


__all__ = ["DevelopError", "develop_source", "guidance"]
