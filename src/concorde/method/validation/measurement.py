"""The input measurement a readiness is bound to (see the Validation contracts).

The changed paths are everything Git reports as different between the base commit and the working
tree, staged or not, plus the untracked paths Git does not ignore. A submodule counts as changed
when its checked-out commit differs, never for changes inside its own worktree: the task commits
only the submodule's commit, and looking inside may need objects a partial clone has to fetch
over a network the caller may not have. Each gets its Git file mode and the SHA-256 digest of
its bytes, both ``None`` when it no longer exists or when Git would not commit it (see
``ignored_paths``), which Delivery commits as deleted although its file stays on disk. The input
digest covers the head and base commits, the changed paths and the digest of
``.concorde/config.json`` with the configured checks under ``.concorde/checks/``. Delivery
measures through this module too, so both sides compute the same digest for the same worktree.

Git hands over a path as bytes, which this module keeps as a ``str`` decoded with
``surrogateescape``, so that it names the file exactly; the measurement records it as text with
``recorded_path``, which ``real_path`` reverses.
"""

from __future__ import annotations

import hashlib
import json
import os
import stat
import subprocess
from pathlib import Path


class MeasurementError(Exception):
    """Git could not report the worktree's changes, or a changed path or the configuration is
    unreadable."""

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


# A byte that is no part of valid UTF-8, as ``surrogateescape`` decodes it.
_ESCAPED = range(0xDC80, 0xDD00)


def recorded_path(path: str) -> str:
    """The text the measurement records for ``path`` (see the contracts): the path itself when
    its bytes are valid UTF-8 and it does not begin with ``"``; otherwise the path in double
    quotes, ``"`` and ``\\`` preceded by ``\\`` and each byte that is no part of valid UTF-8
    written ``\\`` and its three octal digits, as Git quotes a path."""
    if not path.startswith('"') and not any(ord(char) in _ESCAPED for char in path):
        return path
    quoted = []
    for char in path:
        if char in '"\\':
            quoted.append("\\" + char)
        elif ord(char) in _ESCAPED:
            quoted.append(f"\\{ord(char) - 0xDC00:03o}")
        else:
            quoted.append(char)
    return '"' + "".join(quoted) + '"'


def real_path(recorded: str) -> str:
    """The path ``recorded_path`` recorded, decoded with ``surrogateescape`` again."""
    if not recorded.startswith('"'):
        return recorded
    text, result, index = recorded[1:-1], [], 0
    while index < len(text):
        char = text[index]
        if char != "\\":
            result.append(char)
            index += 1
        elif text[index + 1] in '"\\':
            result.append(text[index + 1])
            index += 2
        else:
            result.append(chr(0xDC00 + int(text[index + 1 : index + 4], 8)))
            index += 4
    return "".join(result)


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


def _changes(worktree: Path, base: str) -> tuple[list[str], set[str]]:
    """The changed paths (see ``changed_paths``) and those of them Git would not commit (see
    ``ignored_paths``)."""
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
    unignored = _paths(
        _output(worktree, "ls-files", "--others", "--exclude-standard", "-z")
    )
    new = {path for path in unignored if not _special(worktree, path)}
    changed = sorted(
        tracked | new, key=lambda path: path.encode("utf-8", "surrogateescape")
    )
    # Only a path the diff lists can be in the base and out of the index.
    candidates = {
        path
        for path in tracked - unignored
        if os.path.lexists(worktree / path)
        and not any(other.startswith(path + "/") for other in unignored)
    }
    if candidates:
        candidates -= _paths(_output(worktree, "ls-files", "--cached", "-z"))
    return changed, candidates


def changed_paths(worktree: Path, base: str) -> list[str]:
    """Every path changed since ``base``, committed or not, and every unignored new path.

    New paths that are no content of the task (see ``special_paths``) are left out.
    """
    return _changes(worktree, base)[0]


def ignored_paths(worktree: Path, base: str) -> set[str]:
    """The changed paths since ``base`` that exist but that Git would not commit.

    Such a path is in the base, the index does not hold it and ``git add -A`` would add nothing
    at it: Git ignores it, or it lies beyond a symbolic link, or it is a directory holding nothing
    Git would add. This happens when the branch untracked the path, such as with
    ``git rm --cached``, while its file stays on disk under an ignore rule. Delivery commits the
    path's deletion, so the measurement records it as deleted.
    """
    return _changes(worktree, base)[1]


def path_digest(worktree: Path, relative: str) -> str | None:
    """The digest of one changed path's current content; ``None`` when it is gone."""
    path = worktree / relative
    if path.is_symlink():
        return sha256(b"symlink:" + os.fsencode(os.readlink(path)))
    if path.is_file():
        return sha256(path.read_bytes())
    if path.is_dir():  # a submodule: its checked-out commit
        return sha256(b"gitlink:" + gitlink_commit(worktree, relative))
    return None


def gitlink_commit(worktree: Path, relative: str) -> bytes:
    """The commit a directory that is a submodule or another repository stands for: the commit
    it has checked out when it is the top level of a repository whose head names one; otherwise,
    such as for a submodule not initialized, the commit the worktree's index records for it, or
    nothing when the index records none."""
    path = worktree / relative
    prefix = git(path, "rev-parse", "--show-prefix")
    if prefix.returncode == 0 and not prefix.stdout.strip():
        head = git(path, "rev-parse", "--verify", "-q", "HEAD^{commit}")
        if head.returncode == 0:
            return head.stdout.strip()
    staged = _output(worktree, "ls-files", "-s", "-z", "--", f":(literal){relative}")
    for entry in staged.split(b"\0"):
        fields, _, name = entry.partition(b"\t")
        mode, _, rest = fields.partition(b" ")
        if mode == b"160000" and name == os.fsencode(relative):
            return rest.partition(b" ")[0]
    return b""


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


def _measured(worktree: Path, relative: str, ignored: set[str]) -> dict:
    """One changed path's entry; ``path_unreadable`` when the operating system refuses it.

    A path in ``ignored`` (see ``ignored_paths``) is recorded as deleted.
    """
    if relative in ignored:
        return {"path": recorded_path(relative), "mode": None, "digest": None}
    try:
        mode, digest = path_mode(worktree, relative), path_digest(worktree, relative)
    except OSError as error:
        raise MeasurementError(
            "path_unreadable",
            f"the changed path {recorded_path(relative)} cannot be read: {error}",
        ) from error
    return {"path": recorded_path(relative), "mode": mode, "digest": digest}


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
    paths, ignored = _changes(worktree, base_commit)
    changed = [_measured(worktree, path, ignored) for path in paths]
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
    changed configuration does. A missing configuration cannot be measured.
    """

    def digest(entry: Path) -> str | None:
        if entry.is_symlink():
            return sha256(b"symlink:" + os.fsencode(os.readlink(entry)))
        return sha256(entry.read_bytes()) if entry.is_file() else None

    files = {}
    try:
        config = worktree / ".concorde/config.json"
        files[".concorde/config.json"] = (
            digest(config) if config.is_symlink() else sha256(config.read_bytes())
        )
        checks = worktree / ".concorde/checks"
        if checks.is_dir() and not checks.is_symlink():
            for name in sorted(os.listdir(checks)):
                files[recorded_path(f".concorde/checks/{name}")] = digest(checks / name)
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
    "ignored_paths",
    "measure",
    "path_digest",
    "path_mode",
    "real_path",
    "recorded_path",
    "sha256",
    "special_paths",
]
