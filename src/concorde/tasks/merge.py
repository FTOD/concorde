"""``concorde task merge``: merge a delivered task into the primary branch under the merge lock.

The whole critical section runs in this one process, which holds the merge lock from the checks
before the merge to the close after it: the merge, the post-merge checks, the reset that undoes a
merge whose checks failed, and closing the task. The kernel releases the lock however the process
ends, so no other session has to wait for this one to announce that it is done.
"""

from __future__ import annotations

import os
import shlex
import subprocess
import sys
import time
from pathlib import Path

from . import store
from .store import TaskError

# A check that runs longer than this is stopped and counts as failed, so the lock is not held
# for ever by a check that hangs.
CHECK_TIMEOUT = 1800
# How much of a failed check's output a refusal quotes; the log holds all of it.
OUTPUT_TAIL = 2000
LISTED = 20


def default_checks() -> list[list[str]]:
    """``concorde validate`` of the primary worktree, by this Python and this package."""
    return [[sys.executable, "-m", "concorde", "validate"]]


def parse_checks(texts: list[str]) -> list[list[str]]:
    checks = []
    for text in texts:
        try:
            words = shlex.split(text)
        except ValueError as error:
            raise TaskError(
                "invalid_input", f"--check {text!r} cannot be split into words: {error}"
            ) from error
        if not words:
            raise TaskError("invalid_input", f"--check {text!r} names no command")
        checks.append(words)
    return checks or default_checks()


def _environment() -> dict:
    """The environment of a check: the running package first on Python's path."""
    package = str(Path(__file__).resolve().parents[2])
    environment = dict(os.environ)
    environment["PYTHONPATH"] = os.pathsep.join(
        item for item in (package, environment.get("PYTHONPATH")) if item
    )
    return environment


def _listed(paths: list[str]) -> str:
    more = f" and {len(paths) - LISTED} more" if len(paths) > LISTED else ""
    return ", ".join(paths[:LISTED]) + more


def _status(primary: Path) -> list[str]:
    lines = store._git(
        primary, "status", "--porcelain", "--untracked-files=all"
    ).stdout.splitlines()
    return [line[3:] for line in lines if line.strip()]


def _primary_branch(primary: Path) -> str:
    """The primary worktree's branch, refused as ``primary_dirty`` unless it is clean."""
    branch = store._git(primary, "symbolic-ref", "-q", "--short", "HEAD", check=False)
    if branch.returncode != 0:
        head = store._git(primary, "rev-parse", "HEAD").stdout.strip()
        raise TaskError(
            "primary_dirty",
            f"the primary worktree {primary} has a detached HEAD at {head}; a task is merged "
            "only into a checked-out branch",
        )
    paths = _status(primary)
    if paths:
        raise TaskError(
            "primary_dirty",
            f"the primary worktree {primary} has {len(paths)} uncommitted or untracked "
            f"path(s): {_listed(paths)}; a merge starts only from a clean primary worktree, "
            "so that undoing it cannot touch anyone's work",
        )
    return branch.stdout.strip()


def _head(primary: Path) -> str:
    return store._git(primary, "rev-parse", "HEAD").stdout.strip()


def _rollback(primary: Path, before: str, failure: str) -> str:
    """Reset the primary branch to ``before``; the text of what is left, or ``rollback_failed``."""
    reset = store._git(primary, "reset", "--keep", before, check=False)
    if reset.returncode != 0:
        raise TaskError(
            "rollback_failed",
            f"{failure}; then git reset --keep {before} in {primary} exited "
            f"{reset.returncode}: {(reset.stderr or reset.stdout).strip() or '(no output)'}; "
            f"the primary branch is at {_head(primary)} and its worktree as Git left it",
        )
    left = _status(primary)
    if left:
        return (
            f"; the primary branch is back at {before}, but these paths the checks created "
            f"remain in the primary worktree: {_listed(left)}"
        )
    return f"; the primary branch is back at {before}, clean"


def _merge(primary: Path, record: dict, branch: str, before: str) -> str:
    """Merge the task branch; the merge's head, or an aborted conflict refused."""
    merged = store._git(primary, "merge", "--no-edit", record["branch"], check=False)
    if merged.returncode == 0:
        return _head(primary)
    output = (merged.stdout + merged.stderr).strip() or "(no output)"
    conflicts = store._git(
        primary, "diff", "--name-only", "--diff-filter=U", check=False
    ).stdout.split()
    failure = (
        f"git merge --no-edit {record['branch']} into {branch} of {primary} exited "
        f"{merged.returncode}: {output[-OUTPUT_TAIL:]}"
    )
    in_progress = store._git(
        primary, "rev-parse", "-q", "--verify", "MERGE_HEAD", check=False
    )
    if in_progress.returncode == 0:
        aborted = store._git(primary, "merge", "--abort", check=False)
        if aborted.returncode != 0:
            raise TaskError(
                "rollback_failed",
                f"{failure}; then git merge --abort exited {aborted.returncode}: "
                f"{aborted.stderr.strip() or '(no output)'}; the primary branch is at "
                f"{_head(primary)} and its worktree as Git left it",
            )
    left = _rollback(primary, before, failure) if _head(primary) != before else ""
    if conflicts:
        raise TaskError(
            "merge_conflict",
            f"merging task {record['id']} ({record['branch']}) into {branch} conflicts in "
            f"{len(conflicts)} path(s): {_listed(conflicts)}; the merge was aborted{left} and "
            f"the task is still delivered",
        )
    raise TaskError("git_failed", failure + left)


def _check(primary: Path, argv: list[str], log: Path) -> tuple[dict, str | None]:
    """Run one check in the primary worktree; its result and, when it failed, why."""
    started = time.monotonic()
    try:
        ran = subprocess.run(
            argv,
            cwd=primary,
            env=_environment(),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=CHECK_TIMEOUT,
            check=False,
        )
        code, output = ran.returncode, ran.stdout or ""
        problem = None if code == 0 else f"exited {code}"
    except subprocess.TimeoutExpired as error:
        code, output = -1, error.stdout if isinstance(error.stdout, str) else ""
        problem = f"was stopped after {CHECK_TIMEOUT} s"
    except OSError as error:
        code, output = -1, ""
        problem = f"could not run: {error}"
    seconds = round(time.monotonic() - started, 3)
    with log.open("a", encoding="utf-8") as stream:
        stream.write(
            f"$ {shlex.join(argv)}\n{output}"
            f"{'' if output.endswith(chr(10)) or not output else chr(10)}"
            f"[exit {code} after {seconds} s]\n\n"
        )
    result = {"argv": list(argv), "exit_code": code, "seconds": seconds}
    if problem is None:
        return result, None
    tail = output.strip()[-OUTPUT_TAIL:] or "(no output)"
    return result, f"the check `{shlex.join(argv)}` {problem}; its output ends: {tail}"


def merge_task(
    here: Path,
    task_id: str,
    checks: list[str] | None = None,
    wait: float = store.MERGE_WAIT,
) -> dict:
    """Merge a delivered task into the primary branch, check it, and close the task."""
    primary = store.require_primary(here)
    commands = parse_checks(list(checks or []))
    if wait < 0:
        raise TaskError("invalid_input", f"--wait {wait:g} is negative")
    with store.merge_lock(primary, "merge", task_id, wait) as waited:
        record, _ = store.mergeable(primary, task_id)
        branch = _primary_branch(primary)
        before = _head(primary)
        after = _merge(primary, record, branch, before)
        log = store.tasks_directory(primary) / f"{task_id}.merge.log"
        with log.open("a", encoding="utf-8") as stream:
            stream.write(
                f"# {store.now()} merged {record['branch']} into {branch}: "
                f"{before} -> {after}\n\n"
            )
        results = []
        for argv in commands:
            result, problem = _check(primary, argv, log)
            results.append(result)
            if problem:
                left = _rollback(primary, before, problem)
                raise TaskError(
                    "check_failed",
                    f"after merging task {task_id} into {branch} at {after}, {problem}{left}; "
                    f"the full output is in {log}; the task is still delivered",
                )
        paths = _status(primary)
        if paths:
            problem = (
                f"the checks left {len(paths)} uncommitted path(s) in the primary worktree: "
                f"{_listed(paths)}"
            )
            left = _rollback(primary, before, problem)
            raise TaskError(
                "check_failed",
                f"after merging task {task_id} into {branch} at {after}, {problem}{left}; "
                f"the checks' output is in {log}; the task is still delivered",
            )
        try:
            record = store.close_locked(primary, task_id, "merged")
        except TaskError as error:
            raise TaskError(
                error.code,
                f"task {task_id} was merged into {branch} at {after} and every check passed, "
                f"but closing it failed: {error}; the merge stays, and "
                f"`concorde task close {task_id} --merged` finishes the task",
            ) from error
    return {
        "record": record,
        "merge": {
            "before": before,
            "after": after,
            "checks": results,
            "waited_seconds": waited,
            "log": log.as_posix(),
        },
    }


__all__ = ["CHECK_TIMEOUT", "default_checks", "merge_task", "parse_checks"]
