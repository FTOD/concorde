"""The develop install: what makes a Concorde checkout a valid source for it, and its guidance.

A develop install runs the Concorde of an independent Concorde repository that the developer also
changes. It is made and updated only from the clean primary worktree of that repository, on a
branch: a task worktree disappears once its branch is merged, a detached checkout names no line of
development, and uncommitted changes would install a Concorde no commit records. The installer
calls ``check``, which the package descriptor names, before writing anything and adds the guidance
it answers to the main-session guidance it places.
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


def _git_path(package: Path, *argv: str) -> str:
    """The one path a Git query prints, kept whole whatever characters it holds."""
    done = _git(package, *argv)
    path = done.stdout.rstrip("\n")
    if done.returncode != 0 or not path:
        raise DevelopError(
            "develop_source_unreadable",
            f"`git -C {package} {' '.join(argv)}` failed "
            f"({done.stderr.strip() or 'it printed no path'}); a develop install needs Git "
            "to check the Concorde repository it installs from",
        )
    return path


def _primary_worktree(package: Path, common: Path) -> str:
    """Where the primary worktree of ``package``'s repository is, as far as Git records it.

    Git records it only as the parent of a common directory named ``.git`` or as
    ``core.worktree``; a repository made with ``--separate-git-dir`` records neither, and then
    the common directory is all a refusal can name.
    """
    if common.name == ".git":
        return f"primary worktree is {common.parent}"
    configured = _git(package, "config", "--get", "core.worktree").stdout.rstrip("\n")
    if configured:
        return f"primary worktree is {(common / configured).resolve()}"
    return (
        f"Git directory is {common}, which records no path for the primary worktree (the "
        "worktree whose `.git` file points to it)"
    )


def develop_source(package: str | Path) -> dict:
    """The repository, branch and commit a develop install of ``package`` installs from.

    Refuses a package that is not the root of the primary worktree of a Git repository, whose
    ``HEAD`` is detached, or that has uncommitted or untracked changes.
    """
    package = Path(package).resolve()
    top = _git(package, "rev-parse", "--show-toplevel")
    if top.returncode != 0 or Path(top.stdout.rstrip("\n")).resolve() != package:
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
    own, common = (
        Path(
            _git_path(package, "rev-parse", "--path-format=absolute", option)
        ).resolve()
        for option in ("--git-dir", "--git-common-dir")
    )
    if own != common:
        raise DevelopError(
            "develop_source_not_primary",
            f"{package} is a linked worktree of the Concorde repository whose "
            f"{_primary_worktree(package, common)}; a develop install is made from the "
            "primary worktree, since a task worktree disappears once its branch is merged",
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


def check(package) -> dict:
    """The installer's entry, which the package descriptor names under ``develop``: the source
    a develop install of ``package`` installs from with the guidance it adds, as
    ``{"source": {...}, "guidance": {"skill", "claude_md"}}``, or
    ``{"refusal": {"code", "message"}}`` when the checkout may not be installed from."""
    try:
        source = develop_source(package)
        skill, claude_md = guidance(package)
    except DevelopError as error:
        return {"refusal": {"code": error.code, "message": str(error)}}
    return {"source": source, "guidance": {"skill": skill, "claude_md": claude_md}}


__all__ = ["DevelopError", "check", "develop_source", "guidance"]
