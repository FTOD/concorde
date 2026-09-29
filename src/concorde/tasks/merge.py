"""``concorde task merge``: merge a delivered task into the primary branch under the merge lock.

The whole critical section runs in this one process, which holds the merge lock from the checks
before the merge to the close after it: the merge, the post-merge checks, the reset that undoes a
merge whose checks failed, and closing the task. The kernel releases the lock however the process
ends, so no other session has to wait for this one to announce that it is done. It also holds the
task's workspace lock, so no run of the task changes its branch meanwhile, and merges the exact
commit it checked, always as a merge commit that also adds the task's decision log as
``.concorde/decisions/<history key>.md`` and names the task in its ``Concorde-Task`` trailer. Before ``git merge`` it stores the task as ``merging``; a process that ends
before its checks decided leaves that state behind, which refuses every other mutating task
command until ``--resume`` reruns the checks or ``--abort`` resets the primary branch.

Every attempt, a merge, a ``--resume`` or an ``--abort``, is a trace node ``merges/<n>/`` of the
task, ended with how the attempt ended; each check it runs is a node ``checks/<i>/`` below it with
the check's output as ``output.log``.
"""

from __future__ import annotations

import os
import shlex
import subprocess
import sys
import time
from pathlib import Path

from .. import errors
from ..spec.typed_data import register
from ..tracing import node as trace
from ..tracing.node import Node
from . import store
from .store import TaskError

_TEXT = {"type": "string", "minLength": 1}
_COMMIT = {"type": "string", "pattern": "^[0-9a-f]{40}([0-9a-f]{24})?$"}
# contract.tasks.merge-trace, version 1
MERGE_TRACE = "concorde-merge-trace"
register(
    MERGE_TRACE,
    1,
    {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "attempt",
            "branch",
            "before",
            "checked",
            "after",
            "checks",
            "waited_seconds",
        ],
        "properties": {
            "attempt": {"enum": ["merge", "resume", "abort"]},
            "branch": _TEXT,
            "before": _COMMIT,
            "checked": {"anyOf": [{"type": "null"}, _COMMIT]},
            "after": {"anyOf": [{"type": "null"}, _COMMIT]},
            "checks": {
                "type": "array",
                "items": {"type": "array", "items": {"type": "string"}},
            },
            "waited_seconds": {"type": "number", "minimum": 0},
        },
    },
)
# contract.tasks.merge-check-trace, version 1
MERGE_CHECK_TRACE = "concorde-merge-check-trace"
register(
    MERGE_CHECK_TRACE,
    1,
    {
        "type": "object",
        "additionalProperties": False,
        "required": ["argv", "exit_code"],
        "properties": {
            "argv": {"type": "array", "items": {"type": "string"}},
            "exit_code": {"anyOf": [{"type": "null"}, {"type": "integer"}]},
        },
    },
)
# The outcome of an attempt that a refusal ended, by the refusal's code.
REFUSED = {
    "merge_conflict": "conflict",
    "check_failed": "check_failed",
    "rollback_failed": "rollback_failed",
    "git_failed": "git_failed",
}


class Attempt:
    """One merge attempt's trace node, ``merges/<n>/`` of the task."""

    def __init__(self, primary: Path, task_id: str, kind: str, merging: dict, waited):
        parent = store.task_folder(primary, task_id) / "merges"
        earlier = (
            sorted(item for item in parent.iterdir() if item.is_dir())
            if parent.is_dir()
            else []
        )
        for folder in earlier:
            # An attempt whose process ended before it decided was interrupted.
            found = trace.read(folder)
            if found is not None and found.get("status") == "running":
                found.update(
                    ended_at=trace.now(), status="failed", outcome="interrupted"
                )
                trace.write(folder, found)
        number = 1 + len(earlier)
        self.task_id = task_id
        self.folder = parent / str(number)
        self.checks = 0
        self.data = {
            "attempt": kind,
            "branch": merging["branch"],
            "before": merging["before"],
            "checked": merging.get("checked"),
            "after": merging.get("after"),
            "checks": [list(argv) for argv in merging.get("checks") or []],
            "waited_seconds": float(waited),
        }
        self.node = Node(
            self.folder,
            f"merge-{number}",
            "merge",
            content_type=MERGE_TRACE,
            metadata={"task": task_id, "branch": merging["branch"]},
            content=self.data,
        ).start()

    def merged(self, after: str) -> None:
        self.data["after"] = after
        self.node.update(content=self.data, commit=after)

    def check_folder(self) -> Path:
        self.checks += 1
        return self.folder / "checks" / str(self.checks)

    def end(self, status: str, outcome: str, error: dict | None = None) -> None:
        if self.node.record["status"] == "running" and self.folder.is_dir():
            self.node.finish(status, outcome=outcome, error=error, content=self.data)

    def refused(self, refusal: TaskError) -> None:
        self.end(
            "failed",
            REFUSED.get(refusal.code, "refused"),
            errors.link(
                "component",
                f"Tasks (concorde task merge of task {self.task_id})",
                refusal.code,
                str(refusal),
                reason="decision"
                if refusal.code in ("merge_conflict", "check_failed")
                else "environment",
                explanation="the merge attempt ended with this refusal",
            ),
        )


# A check that runs longer than this is stopped and counts as failed, so the lock is not held
# for ever by a check that hangs.
CHECK_TIMEOUT = 1800
# How much of a failed check's output a refusal quotes; the log holds all of it.
OUTPUT_TAIL = 2000
LISTED = 20


def default_checks() -> list[list[str]]:
    """``concorde spec-validation`` of the primary worktree, by this Python and this package."""
    return [[sys.executable, "-m", "concorde", "spec-validation"]]


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
    """The primary worktree's changed paths, by the same rule as a task worktree's: new paths Git
    cannot version, such as a sandbox's mounts of ``.bashrc``, are left out."""
    return [entry[3:] for entry in store._changes(primary)]


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


def _stays_merging(task_id: str) -> str:
    return (
        f"; task {task_id} stays merging, which refuses every other mutating task command, "
        f"until `concorde task merge {task_id} --abort` restores the primary branch"
    )


def _rollback(primary: Path, task_id: str, before: str, failure: str) -> str:
    """Reset the primary branch to ``before``; the text of what is left, or ``rollback_failed``."""
    reset = store._git(primary, "reset", "--keep", before, check=False)
    if reset.returncode != 0:
        raise TaskError(
            "rollback_failed",
            f"{failure}; then git reset --keep {before} in {primary} exited "
            f"{reset.returncode}: {(reset.stderr or reset.stdout).strip() or '(no output)'}; "
            f"the primary branch is at {_head(primary)} and its worktree as Git left it"
            + _stays_merging(task_id),
        )
    left = _status(primary)
    if left:
        return (
            f"; the primary branch is back at {before}, but these paths the checks created "
            f"remain in the primary worktree: {_listed(left)}"
        )
    return f"; the primary branch is back at {before}, clean"


def _merge(
    primary: Path, record: dict, branch: str, before: str, checked: str, key: str
) -> str:
    """Merge the checked commit as a merge commit that adds the task's decision log; the
    merge's head, or an aborted conflict or Git refusal refused."""
    merged = store._git(
        primary, "merge", "--no-ff", "--no-commit", checked, check=False
    )
    if merged.returncode != 0:
        output = (merged.stdout + merged.stderr).strip() or "(no output)"
        conflicts = store._git(
            primary, "diff", "--name-only", "--diff-filter=U", check=False
        ).stdout.split()
        failure = (
            f"git merge --no-ff --no-commit {checked} ({record['branch']}) into {branch} of "
            f"{primary} exited {merged.returncode}: {output[-OUTPUT_TAIL:]}"
        )
        _undo_merge(primary, record, branch, before, failure, conflicts)
    in_progress = store._git(
        primary, "rev-parse", "-q", "--verify", "MERGE_HEAD", check=False
    )
    if in_progress.returncode != 0:
        # Already contained: nothing to merge, and closing commits the decision log alone.
        return _head(primary)
    path = store.committed_log(key)
    target = primary / path
    source = store.decision_log_path(primary, record["id"])
    message = f"Merge branch '{record['branch']}' at {checked}\n\nConcorde-Task: {record['id']}\n"
    try:
        if source.is_file():
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.read_bytes())
            added = store._git(primary, "add", "-f", "--", path, check=False)
            if added.returncode != 0:
                raise OSError(
                    f"git add -f {path} exited {added.returncode}: "
                    f"{(added.stdout + added.stderr).strip() or '(no output)'}"
                )
        committed = subprocess.run(
            ["git", "commit", "-q", "-F", "-"],
            cwd=primary,
            input=message,
            capture_output=True,
            text=True,
            check=False,
        )
        if committed.returncode != 0:
            raise OSError(
                f"git commit of the merge exited {committed.returncode}: "
                f"{(committed.stdout + committed.stderr).strip()[-OUTPUT_TAIL:] or '(no output)'}"
            )
    except OSError as error:
        failure = (
            f"merging {checked} ({record['branch']}) into {branch} of {primary} with the "
            f"decision log {source} as {path} failed: {error}"
        )
        _undo_merge(primary, record, branch, before, failure, [], target)
    return _head(primary)


def _undo_merge(
    primary: Path,
    record: dict,
    branch: str,
    before: str,
    failure: str,
    conflicts: list[str],
    written: Path | None = None,
) -> None:
    """Abort the merge in progress, remove the decision log it wrote, return the primary branch
    to ``before`` and the task to delivered, and refuse with ``merge_conflict`` or
    ``git_failed``."""
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
                f"{_head(primary)} and its worktree as Git left it"
                + _stays_merging(record["id"]),
            )
    if written is not None:
        written.unlink(missing_ok=True)
    left = (
        _rollback(primary, record["id"], before, failure)
        if _head(primary) != before
        else ""
    )
    store.end_merge(primary, record["id"])
    if conflicts:
        raise TaskError(
            "merge_conflict",
            f"merging task {record['id']} ({record['branch']}) into {branch} conflicts in "
            f"{len(conflicts)} path(s): {_listed(conflicts)}; the merge was aborted{left} and "
            f"the task is still delivered",
        )
    raise TaskError(
        "git_failed",
        failure
        + (
            left
            or f"; the merge was aborted and the primary branch is back at {before}"
        )
        + "; the task is still delivered",
    )


def _check(
    primary: Path, argv: list[str], attempt: "Attempt"
) -> tuple[dict, str | None]:
    """Run one check in the primary worktree as a node of the attempt; its result and, when it
    failed, why."""
    folder = attempt.check_folder()
    node = Node(
        folder,
        f"check-{attempt.checks}",
        "merge-check",
        content_type=MERGE_CHECK_TRACE,
        content={"argv": list(argv), "exit_code": None},
    )
    node.keep("output", "output.log")
    node.start()
    log = folder / "output.log"
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
            f"[exit {code} after {seconds} s]\n"
        )
    node.finish(
        "ok" if problem is None else "failed",
        outcome="passed" if problem is None else "failed",
        content={"argv": list(argv), "exit_code": code if code >= 0 else None},
        used={"duration_seconds": seconds},
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
    *,
    resume: bool = False,
    abort: bool = False,
) -> dict:
    """Merge a delivered task into the primary branch, check it, and close the task; or, with
    ``resume`` or ``abort``, finish a merge of it whose process ended before its checks decided.
    """
    primary = store.require_primary(here)
    if resume and abort:
        raise TaskError("invalid_input", "--resume and --abort exclude each other")
    if (resume or abort) and checks:
        raise TaskError(
            "invalid_input",
            "--resume reruns the checks the interrupted merge recorded and --abort runs none, "
            "so neither takes --check",
        )
    commands = parse_checks(list(checks or []))
    if wait < 0:
        raise TaskError("invalid_input", f"--wait {wait:g} is negative")
    store.load_task(primary, task_id)
    started = time.monotonic()
    # The task's own runs are waited for first, without the merge lock, so that a delivery still
    # finishing in the task never holds up the merges of other tasks.
    with store.task_workspace_locked(primary, task_id, "merge", wait):
        remaining = max(0.0, wait - (time.monotonic() - started))
        with store.merge_lock(primary, "merge", task_id, remaining):
            waited = round(time.monotonic() - started, 3)
            unfinished = store.unfinished_merge(primary)
            if unfinished is not None and not (
                (resume or abort) and unfinished["id"] == task_id
            ):
                raise store.incomplete_merge(primary, unfinished)
            record = store.load_task(primary, task_id)
            if (resume or abort) and record["state"] != "merging":
                raise TaskError(
                    "not_merging",
                    f"task {task_id} is {store.derived_state(primary, record)}, not merging; "
                    "--resume and --abort finish only a merge whose process ended before its "
                    "checks decided",
                )
            if abort:
                return _abort(primary, record, waited)
            if resume:
                return _resume(primary, record, waited)
            return _merge_new(primary, task_id, commands, waited)


def _merge_new(primary: Path, task_id: str, commands: list[list[str]], waited) -> dict:
    record, checked = store.mergeable(primary, task_id)
    branch = _primary_branch(primary)
    before = _head(primary)
    merging = {
        "before": before,
        "checked": checked,
        "branch": branch,
        "after": None,
        "history": store.history_key(primary, task_id),
        "checks": commands,
        "since": store.now(),
        "pid": os.getpid(),
    }
    store.begin_merge(primary, task_id, merging)
    attempt = Attempt(primary, task_id, "merge", merging, waited)
    try:
        after = _merge(primary, record, branch, before, checked, merging["history"])
    except TaskError as refusal:
        attempt.refused(refusal)
        raise
    attempt.merged(after)
    merging = store.merged_at(primary, task_id, after)["merging"]
    return _check_and_close(primary, record, merging, attempt, waited)


def _check_and_close(
    primary: Path, record: dict, merging: dict, attempt: Attempt, waited
) -> dict:
    """Run the merge's checks on its commit; close the task, or undo the merge and refuse."""
    try:
        return _checked_close(primary, record, merging, attempt, waited)
    except TaskError as refusal:
        attempt.refused(refusal)
        raise


def _checked_close(
    primary: Path, record: dict, merging: dict, attempt: Attempt, waited
) -> dict:
    task_id, branch = record["id"], merging["branch"]
    before, after = merging["before"], merging["after"]
    results = []
    for argv in merging["checks"]:
        result, problem = _check(primary, argv, attempt)
        results.append(result)
        if problem:
            left = _rollback(primary, task_id, before, problem)
            store.end_merge(primary, task_id)
            raise TaskError(
                "check_failed",
                f"after merging task {task_id} into {branch} at {after}, {problem}{left}; "
                f"the full output is in the checks of {attempt.folder}; the task is delivered "
                "again",
            )
    paths = _status(primary)
    if paths:
        problem = (
            f"the checks left {len(paths)} uncommitted path(s) in the primary worktree: "
            f"{_listed(paths)}"
        )
        left = _rollback(primary, task_id, before, problem)
        store.end_merge(primary, task_id)
        raise TaskError(
            "check_failed",
            f"after merging task {task_id} into {branch} at {after}, {problem}{left}; "
            f"the checks' output is in {attempt.folder}; the task is delivered again",
        )
    # Read before closing, which appends how the task ended.
    warnings = [
        text
        for text in (store.unwritten_decision_log(primary, record),)
        if text is not None
    ]
    try:
        folder = attempt.folder
        closed = store.close_locked(
            primary,
            task_id,
            "merged",
            again=f"`concorde task merge {task_id} --resume`",
            before_move=lambda: attempt.end("ok", "merged"),
            warnings=warnings,
            key=merging.get("history"),
        )
    except TaskError as error:
        if error.code in ("decision_log_failed", "decision_log_uncommitted"):
            raise TaskError(
                error.code,
                f"task {task_id} was merged into {branch} at {after}, every check passed and "
                f"the task is closed as merged, but {error}",
            ) from error
        raise TaskError(
            error.code,
            f"task {task_id} was merged into {branch} at {after} and every check passed, but "
            f"closing it failed: {error}; the merge stays and the task stays merging, and "
            f"once the cause is fixed `concorde task merge {task_id} --resume` reruns the "
            "checks and closes it",
        ) from error
    return {
        "record": closed,
        "merge": {
            "before": before,
            "after": after,
            "checks": results,
            "waited_seconds": waited,
            "log": (
                store.history_folder(primary, closed["closed"]["history"])
                / folder.relative_to(store.task_folder(primary, task_id))
            ).as_posix(),
        },
        "warnings": warnings + store.end_sessions(primary, closed),
    }


def _diverged(primary: Path, record: dict, where: str) -> TaskError:
    merging = record["merging"]
    return TaskError(
        "merge_diverged",
        f"the interrupted merge of task {record['id']} merged {merging['checked']} into "
        f"{merging['branch']} of {primary} at {merging['before']}, but the primary worktree "
        f"{where}; Tasks resets only a merge it made, so restore {merging['branch']} by hand "
        f"to {merging['before']} or to the merge commit "
        f"{merging.get('after') or '(never recorded)'} and run the command again",
    )


def _resume(primary: Path, record: dict, waited) -> dict:
    """Rerun the recorded checks on the merge commit, then close or undo."""
    merging = record["merging"]
    branch = _primary_branch(primary)
    if branch != merging["branch"]:
        raise _diverged(primary, record, f"is now on branch {branch}")
    after = store.merge_commit(primary, merging)
    if after is None:
        head = _head(primary)
        if head == merging["before"]:
            detail = (
                "the commit before the merge, so the merge never landed or was undone"
            )
        else:
            detail = "neither the commit before the merge nor the merge commit"
        raise TaskError(
            "not_resumable",
            f"task {record['id']} is merging, but {branch} of {primary} is at {head}, "
            f"{detail}; only a merge whose commit is still the primary branch's head can be "
            f"checked again, and `concorde task merge {record['id']} --abort` returns the "
            "task to delivered when the branch is at the commit before the merge or at the "
            "merge commit",
        )
    merging = dict(merging, after=after)
    attempt = Attempt(primary, record["id"], "resume", merging, waited)
    return _check_and_close(primary, record, merging, attempt, waited)


def _abort(primary: Path, record: dict, waited) -> dict:
    """Reset the primary branch to the commit before the merge and return the task to
    delivered."""
    merging = record["merging"]
    attempt = Attempt(primary, record["id"], "abort", merging, waited)
    try:
        return _aborted(primary, record, attempt, waited)
    except TaskError as refusal:
        attempt.refused(refusal)
        raise


def _aborted(primary: Path, record: dict, attempt: Attempt, waited) -> dict:
    merging = record["merging"]
    before = merging["before"]
    in_progress = store._git(
        primary, "rev-parse", "-q", "--verify", "MERGE_HEAD", check=False
    )
    if in_progress.returncode == 0:
        aborted = store._git(primary, "merge", "--abort", check=False)
        if aborted.returncode != 0:
            raise TaskError(
                "rollback_failed",
                f"--abort found a merge in progress in {primary}, and git merge --abort "
                f"exited {aborted.returncode}: {aborted.stderr.strip() or '(no output)'}; "
                f"the primary branch is at {_head(primary)} and its worktree as Git left it"
                + _stays_merging(record["id"]),
            )
    branch = store._git(primary, "symbolic-ref", "-q", "--short", "HEAD", check=False)
    if branch.returncode != 0 or branch.stdout.strip() != merging["branch"]:
        where = (
            f"is on branch {branch.stdout.strip()}"
            if branch.returncode == 0
            else f"has a detached HEAD at {_head(primary)}"
        )
        raise _diverged(primary, record, where)
    head = _head(primary)
    undone = None
    if head != before:
        if store.merge_commit(primary, merging) != head:
            raise _diverged(primary, record, f"is at {head}")
        _rollback(primary, record["id"], before, f"--abort of the merge at {head}")
        undone = head
    left = _status(primary)
    attempt.end("ok", "aborted")
    ended = store.end_merge(primary, record["id"])
    ended["state"] = store.derived_state(primary, ended)
    return {
        "record": ended,
        "abort": {
            "before": before,
            "undone": undone,
            "left": left,
            "waited_seconds": waited,
        },
    }


__all__ = ["CHECK_TIMEOUT", "default_checks", "merge_task", "parse_checks"]
