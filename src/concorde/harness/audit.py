"""The write audit: what changed in a task worktree since a snapshot, judged against a grant.

The host runs read-only Git outside the worker. A snapshot records ``HEAD``, the index digest and
the digest of every tracked change and untracked file; after a round the same measurement is taken
again and every difference is judged: a changed or new file in the grant's ``rw`` list is allowed,
anything else, including a deletion or a changed ``HEAD`` or index, is a violation. Paths Git
ignores are not observed.
"""

from __future__ import annotations

import hashlib
import os
import subprocess
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
    if path.is_symlink():
        return "link:" + str(path.readlink())
    if not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
    head = _git(worktree, "rev-parse", "HEAD").decode().strip()
    index_path = Path(
        _git(worktree, "rev-parse", "--git-path", "index").decode().strip()
    )
    if not index_path.is_absolute():
        index_path = worktree / index_path
    files = {path: _digest(worktree / path) for path in _changed_paths(worktree)}
    return Snapshot(head, _digest(index_path), files)


def rw_allows(rw: list[str], path: str) -> bool:
    return any(
        path == entry or (entry.endswith("/") and path.startswith(entry))
        for entry in rw
    )


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


def audit(worktree: Path, before: Snapshot, rw: list[str]) -> AuditResult:
    """Compare the worktree now with ``before`` and judge every change against ``rw``."""
    after = snapshot(worktree)
    violations: list[str] = []
    if after.head != before.head:
        violations.append("HEAD")
    if after.index != before.index:
        violations.append("index")
    changed: list[str] = []
    for path in sorted(set(before.files) | set(after.files)):
        # A path Git no longer reports is equal to HEAD again.
        old, new = before.files.get(path, "HEAD"), after.files.get(path, "HEAD")
        if old == new:
            continue
        changed.append(path)
        if new is None or not rw_allows(rw, path):
            violations.append(path)  # a deletion, or a write outside rw
    return AuditResult(tuple(changed), tuple(dict.fromkeys(violations)))


__all__ = ["AuditResult", "Snapshot", "audit", "rw_allows", "snapshot"]
