"""The write audit: what changed in a task worktree since a snapshot, judged against a grant.

The host runs read-only Git outside the worker. A snapshot records ``HEAD`` with the branch it
names, the index digest and the digest, content and executable bit, of every tracked change and
untracked file; after a round the same measurement is taken
again and every difference is judged: a changed or new file in the grant's ``rw`` list is allowed,
anything else, including a deletion or a changed ``HEAD`` or index, is a violation. Paths Git
ignores are not observed. A violation is one string: ``HEAD`` or ``index``, the path of a file
written outside ``rw`` or the path followed by `` (deleted)`` for a deleted file. Which parts of a
writable file a worker may change, such as the entries of a shared glossary, is its caller's
question, asked in its round validation.
"""

from __future__ import annotations

import hashlib
import os
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path


def _git(worktree: Path, *arguments: str) -> bytes:
    return subprocess.run(
        ["git", *arguments],
        cwd=worktree,
        check=True,
        capture_output=True,
        # Read-only: never let ``git status`` refresh and rewrite the index.
        env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
    ).stdout


def _digest(path: Path) -> str | None:
    """A file's content and, as Git sees it, its executable bit; None when it is absent."""
    if path.is_symlink():
        return "link:" + str(path.readlink())
    if not path.is_file():
        return None
    mode = "755" if os.stat(path).st_mode & 0o111 else "644"
    return f"{mode}:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def _changed_paths(worktree: Path) -> set[str]:
    """Every tracked-changed and untracked path Git reports, ignored files excluded."""
    output = _git(
        worktree, "status", "--porcelain=v2", "-z", "--untracked-files=all"
    ).split(b"\0")
    paths: set[str] = set()
    index = 0
    while index < len(output):
        record = output[index].decode("utf-8", "surrogateescape")
        index += 1
        if not record:
            continue
        kind = record[0]
        if kind == "1":
            paths.add(record.split(" ", 8)[8])
        elif kind == "2":
            paths.add(record.split(" ", 9)[9])
            paths.add(output[index].decode("utf-8", "surrogateescape"))
            index += 1
        elif kind == "u":
            paths.add(record.split(" ", 10)[10])
        elif kind == "?":
            paths.add(record[2:])
    return paths


@dataclass(frozen=True)
class Snapshot:
    head: str
    index: str | None
    files: dict[str, str | None]


def snapshot(worktree: Path) -> Snapshot:
    """The worktree's state: ``HEAD`` with the branch it names, the index digest and every changed
    file's digest."""
    # The branch HEAD names (``HEAD`` itself when detached) and its commit: switching to another
    # branch at the same commit changes it too.
    branch = (
        _git(worktree, "rev-parse", "--symbolic-full-name", "HEAD").decode().strip()
    )
    head = f"{branch} {_git(worktree, 'rev-parse', 'HEAD').decode().strip()}"
    index_path = Path(
        _git(worktree, "rev-parse", "--git-path", "index").decode().strip()
    )
    if not index_path.is_absolute():
        index_path = worktree / index_path
    files = {path: _digest(worktree / path) for path in _changed_paths(worktree)}
    return Snapshot(head, _digest(index_path), files)


@dataclass(frozen=True)
class AuditResult:
    changed: tuple[str, ...]
    violations: tuple[str, ...]

    @property
    def clean(self) -> bool:
        return not self.violations

    def record(self) -> dict:
        return {
            "verdict": "clean" if self.clean else "violation",
            "changed": list(self.changed),
            "violations": list(self.violations),
        }


def audit(
    worktree: Path, before: Snapshot, writable: Callable[[str], bool]
) -> AuditResult:
    """Compare the worktree now with ``before`` and judge every change: ``writable`` tells
    whether the grant's most specific entry for a worktree-relative path is ``rw``."""
    after = snapshot(worktree)
    violations: list[str] = []
    if after.head != before.head:
        violations.append("HEAD")
    if after.index != before.index:
        violations.append("index")
    changed: list[str] = []
    for path in sorted(set(before.files) | set(after.files)):
        # A path Git did not report before was equal to HEAD. One it no longer reports is either
        # equal to HEAD again or, untracked before, gone: its entry now tells which.
        old = before.files.get(path, "HEAD")
        new = after.files[path] if path in after.files else _digest(worktree / path)
        if old == new:
            continue
        changed.append(path)
        if new is None:
            violations.append(f"{path} (deleted)")
        elif not writable(path):
            violations.append(path)  # a write outside rw
    return AuditResult(tuple(changed), tuple(dict.fromkeys(violations)))


__all__ = ["AuditResult", "Snapshot", "audit", "snapshot"]
