"""The write audit: what changed in a task worktree since a snapshot, judged against a grant.

The host runs read-only Git outside the worker. A snapshot records ``HEAD``, the index digest and
the digest of every tracked change and untracked file; after a round the same measurement is taken
again and every difference is judged: a changed or new file in the grant's ``rw`` list is allowed,
anything else, including a deletion or a changed ``HEAD`` or index, is a violation. Paths Git
ignores are not observed.

The project glossary is the one writable file held by entry: every Module's concepts share it, so a
task may change only the entries its bound Modules own. The snapshot keeps the glossary's bytes,
and a changed glossary is compared entry by entry; each entry changed although another Module owns
it, before or after, is a violation named ``<glossary>#<concept>``.
"""

from __future__ import annotations

import hashlib
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

from ..spec.glossary import ownership_violations


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
    glossary: bytes | None = None


def _read(worktree: Path, path: str | None) -> bytes | None:
    if path is None:
        return None
    file = worktree / path
    return file.read_bytes() if file.is_file() and not file.is_symlink() else None


def snapshot(worktree: Path, glossary: str | None = None) -> Snapshot:
    """The worktree's state; with ``glossary``, also that file's exact bytes."""
    head = _git(worktree, "rev-parse", "HEAD").decode().strip()
    index_path = Path(
        _git(worktree, "rev-parse", "--git-path", "index").decode().strip()
    )
    if not index_path.is_absolute():
        index_path = worktree / index_path
    files = {path: _digest(worktree / path) for path in _changed_paths(worktree)}
    return Snapshot(head, _digest(index_path), files, _read(worktree, glossary))


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


def audit(
    worktree: Path,
    before: Snapshot,
    rw: list[str],
    glossary: str | None = None,
    modules: list[str] | tuple[str, ...] = (),
) -> AuditResult:
    """Compare the worktree now with ``before`` and judge every change against ``rw``; a change
    of the ``glossary`` is also judged entry by entry against the owners ``modules``."""
    after = snapshot(worktree, glossary)
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
        elif path == glossary:
            try:
                foreign = ownership_violations(before.glossary, after.glossary, modules)
            except (ValueError, UnicodeError) as error:
                foreign = [f"(unreadable: {error})"]
            violations.extend(f"{path}#{item}" for item in foreign)
    return AuditResult(tuple(changed), tuple(dict.fromkeys(violations)))


__all__ = ["AuditResult", "Snapshot", "audit", "rw_allows", "snapshot"]
