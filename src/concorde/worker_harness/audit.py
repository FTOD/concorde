"""The write audit: what changed in a task worktree since a snapshot, judged against a grant.

The host runs read-only Git outside the worker. A snapshot records ``HEAD`` with the branch it
names, the index digest and the digest, content and executable bit, of every tracked change and
untracked file, and the same of every nested repository (an initialized submodule or an untracked
nested repository), its files keyed by their worktree-relative paths; after a round the same
measurement is taken again and every difference is judged: a changed or new file in the grant's
``rw`` list is allowed, anything else, including a deletion or a changed ``HEAD`` or index, is a
violation. Paths Git ignores are not observed. A violation is one string: ``HEAD`` or ``index``,
``<path>: HEAD`` or ``<path>: index`` for a nested repository, the path of a file written outside
``rw`` or the path followed by `` (deleted)`` for a deleted file. Which parts of a
writable file a worker may change, such as the entries of a shared glossary, is its caller's
question, asked in its round validation.
"""

from __future__ import annotations

import hashlib
import os
import subprocess
from collections.abc import Callable
from dataclasses import dataclass, field
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


def _git_maybe(repository: Path, *arguments: str) -> bytes | None:
    """The output of a read-only Git query that answers no with exit status 1, or None then."""
    completed = subprocess.run(
        ["git", *arguments],
        cwd=repository,
        check=False,
        capture_output=True,
        env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
    )
    if completed.returncode == 1:
        return None
    if completed.returncode != 0:
        raise subprocess.CalledProcessError(
            completed.returncode, completed.args, completed.stdout, completed.stderr
        )
    return completed.stdout


def _digest(path: Path) -> str | None:
    """A file's content and, as Git sees it, its executable bit; None when it is absent."""
    if path.is_symlink():
        return "link:" + str(path.readlink())
    if not path.is_file():
        return None
    mode = "755" if os.stat(path).st_mode & 0o111 else "644"
    return f"{mode}:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def _changed_paths(repository: Path) -> tuple[set[str], set[str]]:
    """Every tracked-changed and untracked file Git reports in one repository, ignored files
    excluded, and apart from them the untracked nested repositories it reports as a directory.

    A submodule's own record is no file: its files are measured inside it.
    """
    output = _git(
        repository, "status", "--porcelain=v2", "-z", "--untracked-files=all"
    ).split(b"\0")
    paths: set[str] = set()
    nested: set[str] = set()
    index = 0
    while index < len(output):
        record = output[index].decode("utf-8", "surrogateescape")
        index += 1
        if not record:
            continue
        kind = record[0]
        if kind == "1":
            fields = record.split(" ", 8)
            if not fields[2].startswith("S"):
                paths.add(fields[8])
        elif kind == "2":
            fields = record.split(" ", 9)
            if not fields[2].startswith("S"):
                paths.add(fields[9])
                paths.add(output[index].decode("utf-8", "surrogateescape"))
            index += 1
        elif kind == "u":
            fields = record.split(" ", 10)
            if not fields[2].startswith("S"):
                paths.add(fields[10])
        elif kind == "?":
            if record.endswith("/"):
                nested.add(record[2:-1])
            else:
                paths.add(record[2:])
    return paths, nested


def _submodules(repository: Path) -> set[str]:
    """The initialized submodules of one repository: its gitlinks whose ``.git`` exists."""
    output = _git(repository, "ls-files", "-z", "--stage").split(b"\0")
    links = {
        entry.split(b"\t", 1)[1].decode("utf-8", "surrogateescape")
        for entry in output
        if entry.startswith(b"160000 ")
    }
    return {path for path in links if os.path.lexists(repository / path / ".git")}


def _state(repository: Path) -> tuple[str, str | None]:
    """``HEAD`` with the branch it names (``HEAD`` itself when detached, ``unborn`` before the
    first commit) and the index digest of one repository."""
    named = _git_maybe(repository, "symbolic-ref", "-q", "HEAD")
    branch = named.decode().strip() if named is not None else "HEAD"
    commit = _git_maybe(repository, "rev-parse", "-q", "--verify", "HEAD^{commit}")
    head = f"{branch} {commit.decode().strip() if commit is not None else 'unborn'}"
    index_path = Path(
        _git(repository, "rev-parse", "--git-path", "index").decode().strip()
    )
    if not index_path.is_absolute():
        index_path = repository / index_path
    return head, _digest(index_path)


def _measure(
    worktree: Path,
    prefix: str,
    files: dict[str, str | None],
    repositories: dict[str, tuple[str, str | None]],
) -> None:
    """Measure the repository at ``prefix`` of ``worktree`` and every repository nested in it:
    its changed files, keyed by their worktree-relative path, and each nested repository's state."""
    repository = worktree / prefix if prefix else worktree
    paths, untracked = _changed_paths(repository)
    for path in paths:
        files[prefix + path] = _digest(repository / path)
    nested = _submodules(repository) | {
        path for path in untracked if os.path.lexists(repository / path / ".git")
    }
    for path in sorted(nested):
        repositories[prefix + path] = _state(repository / path)
        _measure(worktree, prefix + path + "/", files, repositories)


@dataclass(frozen=True)
class Snapshot:
    head: str
    index: str | None
    files: dict[str, str | None]
    # Each nested repository's HEAD and index, keyed by its worktree-relative path: the
    # initialized submodules and the untracked nested repositories, at any depth.
    repositories: dict[str, tuple[str, str | None]] = field(default_factory=dict)


def snapshot(worktree: Path) -> Snapshot:
    """The worktree's state: ``HEAD`` with the branch it names, the index digest and every changed
    file's digest, the files of every nested repository included, with each one's own state."""
    head, index = _state(worktree)
    files: dict[str, str | None] = {}
    repositories: dict[str, tuple[str, str | None]] = {}
    _measure(worktree, "", files, repositories)
    return Snapshot(head, index, files, repositories)


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
    for path in sorted(set(before.repositories) | set(after.repositories)):
        old_state = before.repositories.get(path, (None, None))
        new_state = after.repositories.get(path, (None, None))
        if old_state[0] != new_state[0]:
            violations.append(f"{path}: HEAD")
        if old_state[1] != new_state[1]:
            violations.append(f"{path}: index")
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
