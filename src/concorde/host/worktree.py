"""Fail-closed Git worktree boundary for agent-authored mutations."""

from __future__ import annotations

import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


class WorktreeBoundaryError(ValueError):
    """The requested mutation has no authorized isolated Git worktree."""


@dataclass(frozen=True)
class WorktreeBoundary:
    project_root: str
    repository_root: str
    head: str
    git_dir: str
    common_dir: str
    isolated: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _git(root: Path, *arguments: str) -> str:
    try:
        result = subprocess.run(
            ("git", "-C", str(root), *arguments),
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as error:
        raise WorktreeBoundaryError(f"cannot execute Git worktree preflight: {error}") from error
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "Git command failed"
        raise WorktreeBoundaryError(detail)
    value = result.stdout.strip()
    if not value:
        raise WorktreeBoundaryError("Git worktree preflight returned an empty value")
    return value


def inspect_worktree(project_root: str | Path) -> WorktreeBoundary:
    """Return immutable Git identity without reading working-tree file contents."""

    candidate = Path(project_root)
    if candidate.is_symlink():
        raise WorktreeBoundaryError(f"project root may not be a symlink: {candidate}")
    root = candidate.resolve()
    if not root.is_dir():
        raise WorktreeBoundaryError(f"project root is not a directory: {root}")

    repository_root = Path(_git(root, "rev-parse", "--show-toplevel")).resolve()
    git_dir = Path(_git(root, "rev-parse", "--absolute-git-dir")).resolve()
    common_value = _git(root, "rev-parse", "--path-format=absolute", "--git-common-dir")
    common_dir = Path(common_value).resolve()
    head = _git(root, "rev-parse", "--verify", "HEAD^{commit}")
    return WorktreeBoundary(
        project_root=root.as_posix(),
        repository_root=repository_root.as_posix(),
        head=head,
        git_dir=git_dir.as_posix(),
        common_dir=common_dir.as_posix(),
        isolated=git_dir != common_dir,
    )


def require_isolated_worktree(
    project_root: str | Path,
    *,
    allow_primary_worktree: bool = False,
) -> WorktreeBoundary:
    """Require a linked worktree unless the maintainer explicitly authorized primary mutation."""

    candidate = Path(project_root)
    if candidate.is_symlink():
        raise WorktreeBoundaryError(f"project root may not be a symlink: {candidate}")
    root = candidate.resolve()
    if not root.is_dir():
        raise WorktreeBoundaryError(f"project root is not a directory: {root}")
    try:
        probe = subprocess.run(
            ("git", "-C", str(root), "rev-parse", "--is-inside-work-tree"),
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as error:
        if not allow_primary_worktree:
            raise WorktreeBoundaryError(
                f"cannot execute Git worktree preflight: {error}"
            ) from error
        probe = None
    if probe is None or probe.returncode != 0 or probe.stdout.strip() != "true":
        if allow_primary_worktree:
            return WorktreeBoundary(
                project_root=root.as_posix(),
                repository_root="",
                head="",
                git_dir="",
                common_dir="",
                isolated=False,
            )
        raise WorktreeBoundaryError(
            "agent-authored mutation requires a committed linked Git worktree; this directory is "
            "not a Git worktree. Use --allow-primary-worktree only when the maintainer explicitly "
            "authorized mutation of this current directory."
        )
    boundary = inspect_worktree(project_root)
    if boundary.isolated or allow_primary_worktree:
        return boundary
    raise WorktreeBoundaryError(
        "agent-authored mutation is not allowed in the primary Git worktree; create a unique "
        f"branch and linked worktree from committed HEAD {boundary.head}, then retry there. "
        "Primary staged, unstaged, untracked, and ignored files are outside the request authority. "
        "Use --allow-primary-worktree only when the maintainer explicitly authorized mutation of "
        "the primary worktree for this request."
    )
