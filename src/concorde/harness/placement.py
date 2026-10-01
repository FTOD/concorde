"""Where a worker may run, and the Git administrative paths it must never see.

Every worktree a worker runs in lies directly in ``.claude/worktrees/`` of its repository's primary
worktree: a task worktree, an unbound checkout. That one placement makes the Git metadata of the
repository known wherever the repository lies, inside or outside the user's home, so the Harness
can hide it through every tool. Workers checks the placement before it generates anything and
hands the Harness the primary worktree and the Git administrative paths it finds here:

- the repository's common Git directory, with its ``worktrees/`` and ``modules/``, and the
  worktree's own Git directory, as Git itself reports them;
- every ``.git`` entry inside the worktree, the worktree's own and each submodule's, file or
  directory;
- for each ``.git`` file, the Git directory it points to and that directory's common directory.

Only read-only Git runs here; nothing is written.
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

WORKTREES = ".claude/worktrees"


class PlacementError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def _git(worktree: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *arguments],
        cwd=worktree,
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
    )


def _real(path: str | Path) -> Path:
    return Path(os.path.realpath(path))


def primary_worktree(worktree: Path) -> Path:
    """The primary worktree of the repository ``worktree`` belongs to: the first entry Git lists.

    ``PlacementError`` ``worktree_misplaced`` when Git lists none, or the repository is bare.
    """
    listed = _git(worktree, "worktree", "list", "--porcelain")
    lines = listed.stdout.splitlines()
    if listed.returncode != 0 or not lines or not lines[0].startswith("worktree "):
        said = (listed.stderr or listed.stdout).strip() or "no output"
        raise PlacementError(
            "worktree_misplaced",
            f"{worktree} is not a worktree of a Git repository with a primary worktree "
            f"(git worktree list --porcelain exited {listed.returncode}: {said}); a worker "
            f"runs only in a worktree directly inside {WORKTREES}/ of its repository's "
            "primary worktree",
        )
    first = lines[: lines.index("") if "" in lines else len(lines)]
    if "bare" in first:
        raise PlacementError(
            "worktree_misplaced",
            f"the repository of {worktree} is bare and has no primary worktree; a worker runs "
            f"only in a worktree directly inside {WORKTREES}/ of its repository's primary "
            "worktree",
        )
    return _real(lines[0][len("worktree ") :])


def check_placement(worktree: Path) -> Path:
    """The primary worktree, once ``worktree`` is known to lie directly in its
    ``.claude/worktrees/``; ``PlacementError`` ``worktree_misplaced`` naming the rule otherwise."""
    worktree = _real(worktree)
    primary = primary_worktree(worktree)
    expected = primary / WORKTREES
    if worktree.parent != expected:
        raise PlacementError(
            "worktree_misplaced",
            f"the worktree {worktree} does not lie directly in {expected}/: a worker runs only "
            f"in a worktree directly inside {WORKTREES}/ of its repository's primary worktree "
            f"{primary}, where Workers knows every Git administrative path to hide from it",
        )
    return primary


def _pointed(dot_git: Path) -> list[Path]:
    """The Git directory a ``.git`` file points to, and that directory's common directory."""
    try:
        text = dot_git.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    first = text.splitlines()[0] if text else ""
    if not first.startswith("gitdir:"):
        return []
    target = first[len("gitdir:") :].strip()
    if not target:
        return []
    directory = Path(target)
    if not directory.is_absolute():
        directory = dot_git.parent / directory
    found = [_real(directory)]
    common = directory / "commondir"
    try:
        named = common.read_text(encoding="utf-8").strip()
    except OSError:
        named = ""
    if named:
        named_path = Path(named)
        found.append(
            _real(named_path if named_path.is_absolute() else directory / named_path)
        )
    return found


def git_paths(worktree: Path, skip: tuple[Path, ...] = ()) -> tuple[Path, ...]:
    """Every Git administrative path of the repository ``worktree`` belongs to, as real paths.

    The walk for ``.git`` entries does not descend into a ``.git`` entry, a symbolic link or a
    directory of ``skip``, such as the runtime paths, which are no part of the project.
    """
    worktree = _real(worktree)
    found: list[Path] = []
    reported = _git(
        worktree, "rev-parse", "--path-format=absolute", "--git-dir", "--git-common-dir"
    )
    if reported.returncode == 0:
        found += [_real(line) for line in reported.stdout.splitlines() if line.strip()]
    skipped = {_real(path) for path in skip}
    for directory, names, files in os.walk(worktree):
        here = Path(directory)
        for name in (*names, *files):
            if name == ".git":
                entry = here / name
                found += [entry, _real(entry)]
                if entry.is_file() and not entry.is_symlink():
                    found += _pointed(entry)
        names[:] = [
            name
            for name in names
            if name != ".git"
            and not (here / name).is_symlink()
            and (here / name) not in skipped
        ]
    ordered = sorted(set(found))
    return tuple(
        path
        for path in ordered
        if not any(other != path and other in path.parents for other in ordered)
    )


@dataclass(frozen=True)
class Placement:
    """What Workers hands the Harness about where a worker runs."""

    primary: Path
    git: tuple[Path, ...]


def place(worktree: Path, skip: tuple[Path, ...] = ()) -> Placement:
    """The placement of a worker in ``worktree``, once it lies where a worker may run."""
    return Placement(check_placement(worktree), git_paths(worktree, skip))


__all__ = [
    "WORKTREES",
    "Placement",
    "PlacementError",
    "check_placement",
    "git_paths",
    "place",
    "primary_worktree",
]
