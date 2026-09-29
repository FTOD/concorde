"""The input measurement a readiness is bound to (see the Validation contracts).

The changed paths are everything Git reports as different between the base commit and the working
tree, staged or not, plus the untracked paths Git does not ignore. A submodule counts as changed
when its checked-out commit differs, never for changes inside its own worktree: the task commits
only the submodule's commit, and looking inside may need objects a partial clone has to fetch
over a network the caller may not have. Each gets its Git file mode and the SHA-256 digest of
its bytes, both ``None`` when it no longer exists. The input digest covers the head and base
commits, the changed paths and the digest of ``.concorde/config.json`` with the configured checks
under ``.concorde/checks/``. Delivery measures through
this module too, so both sides compute the same digest for the same worktree.
"""

from __future__ import annotations

import hashlib
import json
import os
import stat
import subprocess
from pathlib import Path


class MeasurementError(Exception):
    """Git could not report the worktree's changes, or the configuration is unreadable."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def git(worktree: Path, *arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *arguments], cwd=worktree, capture_output=True, check=False
    )


def _output(worktree: Path, *arguments: str) -> bytes:
    result = git(worktree, *arguments)
    if result.returncode != 0:
        raise MeasurementError(
            "git_failed",
            f"git {' '.join(arguments)} failed: "
            + result.stderr.decode("utf-8", "replace").strip(),
        )
    return result.stdout


def current_branch(worktree: Path) -> str | None:
    """The branch the worktree's head is on, or ``None`` when it is detached."""
    result = git(worktree, "symbolic-ref", "-q", "HEAD")
    if result.returncode != 0:
        return None
    name = result.stdout.decode().strip()
    return name.removeprefix("refs/heads/")


def head_commit(worktree: Path) -> str:
    return _output(worktree, "rev-parse", "--verify", "HEAD^{commit}").decode().strip()


def _paths(raw: bytes) -> set[str]:
    return {item for item in raw.decode("utf-8", "surrogateescape").split("\0") if item}


def _special(worktree: Path, relative: str) -> bool:
    """Whether an untracked path is no content of the task: Git cannot version it, or it is a
    sandbox's placeholder.

    Git cannot version a path that is neither a file, a symbolic link nor a directory, such as the
    ``/dev/null`` character device mounted over it. A placeholder is an empty regular file with no
    write bits and a single link: before mounting ``/dev/null`` over an absent path, the sandbox
    creates it on the host with bubblewrap's ``ensure_file(dest, 0444)`` and removes it only once
    no sandbox of its Claude Code process is alive, so another command sees it as a regular file
    meanwhile. This is the signature by which the sandbox runtime itself recognises one it left
    behind (``isStaleBwrapMountPoint``); a file a task creates has write bits, content or another
    link. It holds on the host and inside any sandbox, unlike a mount point in
    ``/proc/self/mountinfo``, which exists only inside the sandbox that mounted it.
    """
    path = worktree / relative
    if path.is_symlink():
        return False
    try:
        status = path.stat()
    except OSError:
        return True
    if stat.S_ISDIR(status.st_mode):
        return False
    if not stat.S_ISREG(status.st_mode):
        return True
    return status.st_size == 0 and status.st_mode & 0o222 == 0 and status.st_nlink == 1


def special_paths(worktree: Path) -> list[str]:
    """Unignored new paths that are no content of the task, such as a sandbox's mounts.

    Claude Code's Bash sandbox hides some paths of its working directory, such as ``.bashrc`` or
    ``.claude/settings.json``, behind ``/dev/null`` mounts, which Git inside that sandbox lists as
    untracked, and outside it, while a sandbox of the same session is alive, as the empty read-only
    placeholder files it mounts over (see ``_special``); they are no content of the task, and
    ``git add`` refuses the mounts.
    """
    new = _paths(_output(worktree, "ls-files", "--others", "--exclude-standard", "-z"))
    return sorted(path for path in new if _special(worktree, path))


def changed_paths(worktree: Path, base: str) -> list[str]:
    """Every path changed since ``base``, committed or not, and every unignored new path.

    New paths that are no content of the task (see ``special_paths``) are left out.
    """
    tracked = _paths(
        _output(
            worktree,
            "diff",
            "--name-only",
            "--no-renames",
            "--ignore-submodules=dirty",
            "-z",
            base,
        )
    )
    new = _paths(_output(worktree, "ls-files", "--others", "--exclude-standard", "-z"))
    new = {path for path in new if not _special(worktree, path)}
    return sorted(
        tracked | new, key=lambda path: path.encode("utf-8", "surrogateescape")
    )


def path_digest(worktree: Path, relative: str) -> str | None:
    """The digest of one changed path's current content; ``None`` when it is gone."""
    path = worktree / relative
    if path.is_symlink():
        return sha256(b"symlink:" + os.fsencode(os.readlink(path)))
    if path.is_file():
        return sha256(path.read_bytes())
    if path.is_dir():  # a submodule: its checked-out commit
        result = git(path, "rev-parse", "HEAD")
        return sha256(b"gitlink:" + result.stdout.strip())
    return None


def path_mode(worktree: Path, relative: str) -> str | None:
    """Git's file mode of one changed path in the worktree; ``None`` when it is gone.

    A regular file is ``100755`` when its owner may execute it, Git's own rule, else ``100644``.
    """
    path = worktree / relative
    if path.is_symlink():
        return "120000"
    if path.is_file():
        return "100755" if path.stat().st_mode & stat.S_IXUSR else "100644"
    if path.is_dir():  # a submodule
        return "160000"
    return None


def canonical(value) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def measure(worktree: Path, base: str) -> dict:
    """The ``inputs`` object of a readiness for the worktree as it is now."""
    worktree = Path(worktree)
    head = head_commit(worktree)
    base_commit = (
        _output(worktree, "rev-parse", "--verify", f"{base}^{{commit}}")
        .decode()
        .strip()
    )
    changed = [
        {
            "path": path,
            "mode": path_mode(worktree, path),
            "digest": path_digest(worktree, path),
        }
        for path in changed_paths(worktree, base_commit)
    ]
    config_digest = configuration_digest(worktree)
    value = {
        "head": head,
        "base": base_commit,
        "changed": changed,
        "config_digest": config_digest,
    }
    return {**value, "digest": sha256(canonical(value))}


def configuration_digest(worktree: Path) -> str:
    """The digest of the configuration and every entry of the checks directory.

    It is the digest of the canonical JSON object that maps ``.concorde/config.json`` and each
    entry of ``.concorde/checks/`` to the digest of its bytes (a symbolic link's by its link
    text, any other non-file entry as ``null``), so a changed check command changes it as a
    changed configuration does.
    """
    files = {}
    try:
        files[".concorde/config.json"] = sha256(
            (worktree / ".concorde/config.json").read_bytes()
        )
        checks = worktree / ".concorde/checks"
        if checks.is_dir() and not checks.is_symlink():
            for name in sorted(os.listdir(checks)):
                entry = checks / name
                files[f".concorde/checks/{name}"] = (
                    sha256(b"symlink:" + os.fsencode(os.readlink(entry)))
                    if entry.is_symlink()
                    else sha256(entry.read_bytes())
                    if entry.is_file()
                    else None
                )
    except OSError as error:
        raise MeasurementError(
            "config_unreadable",
            f"the configuration or its checks cannot be read: {error}",
        ) from error
    return sha256(canonical(files))


def has_uncommitted(worktree: Path) -> bool:
    """Whether the worktree has a staged, unstaged or new unignored change against its head.

    A new path that is no content of the task (see ``special_paths``) is no change.
    """
    raw = _output(
        worktree,
        "status",
        "--porcelain=v1",
        "-z",
        "--untracked-files=all",
        "--ignore-submodules=dirty",
    ).decode("utf-8", "surrogateescape")
    entries = [entry for entry in raw.split("\0") if entry]
    return any(
        not (entry.startswith("?? ") and _special(worktree, entry[3:]))
        for entry in entries
    )


__all__ = [
    "MeasurementError",
    "changed_paths",
    "current_branch",
    "has_uncommitted",
    "head_commit",
    "measure",
    "path_digest",
    "path_mode",
    "sha256",
    "special_paths",
]
