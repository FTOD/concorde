"""The Task store: each task's folder in the primary worktree, and the task commands.

A task is a branch ``concorde/<id>``, a worktree checked out on it and bound as the workspace
``<id>``, and a folder ``.concorde/tasks/<id>/`` of the primary worktree holding its record
``task.json``, its trace node ``trace.json``, its decision log ``decisions.md``, its task session's
boundary under ``runtime/``, its sessions' and merge attempts' nodes under ``sessions/`` and
``merges/``, and the workspace folder ``workspace/`` its runs are traced in. The record names the
main agent's session the task's task sessions report to now, with every earlier name, and every
report a task session recorded before messaging it, with the main agent's answer. Closing moves
the whole folder to ``.concorde/history/<key>/`` and commits its decision log on the primary branch
as ``.concorde/decisions/<key>.md``, unless the task's merge commit already added it. Only this module
writes records and task nodes, and nothing below the task level writes them: whether a task is
active or delivered is derived each time from what the execution core recorded, its runs in its
workspace folder and its delivery commits on the branch, a delivery counting only when its commit
has exactly one parent; ``merging`` is stored while ``concorde task merge`` has put a merge into
the primary branch that its checks have not decided yet. Every change holds the task's lock
``.concorde/locks/tasks/<id>.lock`` and is one read, a check of its preconditions and one atomic
write bound to the bytes read.
"""

from __future__ import annotations

import contextlib
import shutil
import json
import os
import re
import subprocess
import tempfile
import time
from contextlib import ExitStack, contextmanager
from datetime import UTC, datetime
from pathlib import Path

from ..delivery.commits import delivery_commits, delivery_mismatches
from ..execution import binding as workspace_binding
from ..execution.runs import (
    RunError,
    Store,
    lock_holder,
    workspace_lock,
    workspace_runs,
)
from ..spec.typed_data import register
from ..tracing import layout, locks, retention
from ..tracing import node as trace
from ..tracing.node import Node, concorde_commit, protocol_version

TASK_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,47}$")
HISTORY_KEY = re.compile(r"^[a-z0-9][a-z0-9-]{0,47}(\.[0-9]+)?$")
RECORD = "task.json"
DECISIONS = "decisions.md"
# Where the decision logs of ended tasks are committed on the primary branch, by history key.
DECISION_LOGS = ".concorde/decisions"
_TEXT = {"type": "string", "minLength": 1}
# An object of any fields, such as an error link: Spec typed data admits unknown fields only
# through a schema-valued ``additionalProperties``.
_OBJECT = {"type": "object", "additionalProperties": {}}
# contract.tasks.task-trace, version 1
TASK_TRACE = "concorde-task-trace"
register(
    TASK_TRACE,
    1,
    {
        "type": "object",
        "additionalProperties": False,
        "required": ["goal", "worktree", "transitions", "escalations", "closing"],
        "properties": {
            "goal": _TEXT,
            "worktree": _TEXT,
            "transitions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["state", "at"],
                    "properties": {
                        "state": {"enum": ["open", "merging", "closed", "failed"]},
                        "at": _TEXT,
                    },
                },
            },
            "escalations": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["number", "at", "by", "error"],
                    "properties": {
                        "number": {"type": "integer", "minimum": 1},
                        "at": _TEXT,
                        "by": {"enum": ["main-agent", "task-session"]},
                        "error": _OBJECT,
                    },
                },
            },
            "closing": {
                "anyOf": [
                    {"type": "null"},
                    {
                        "type": "object",
                        "additionalProperties": False,
                        "required": [
                            "outcome",
                            "note",
                            "errors",
                            "primary_commit",
                            "worktree_removed",
                            "history",
                        ],
                        "properties": {
                            "outcome": {"enum": ["merged", "completed", "failed"]},
                            "note": {"anyOf": [{"type": "null"}, _TEXT]},
                            "errors": {"type": "array", "items": _OBJECT},
                            "primary_commit": {
                                "type": "string",
                                "pattern": "^[0-9a-f]{40}([0-9a-f]{24})?$",
                            },
                            "worktree_removed": {"type": "boolean"},
                            "history": _TEXT,
                        },
                    },
                ]
            },
        },
    },
)
# The stages of a task's life. Only open, merging, closed and failed are stored; active and
# delivered are derived from the workspace's runs and delivery commits whenever a task is read.
STATES = ("open", "active", "delivered", "merging", "closed", "failed")
# How a task ended: closed when its goal was reached, merged or not; failed when it was not.
OUTCOMES = ("merged", "completed", "failed")
ENDED = ("closed", "failed")
# The version of the task record: 3 names the main agent's sessions and holds the reports.
RECORD_VERSION = 3
ATTEMPTS = 3
# Where task worktrees go by default, relative to the primary worktree; Git must ignore it.
WORKTREES = ".claude/worktrees"
# How long open, close and merge wait for the merge lock by default, and how often they retry.
MERGE_WAIT = 300.0
LOCK_POLL = 0.2


class TaskError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _git(cwd: Path, *arguments: str, check: bool = True) -> subprocess.CompletedProcess:
    """Run Git; with ``check`` a failure is ``git_failed`` naming the command and its output."""
    try:
        result = subprocess.run(
            ["git", *arguments], cwd=cwd, check=False, capture_output=True, text=True
        )
    except OSError as error:
        raise TaskError(
            "git_failed", f"git {' '.join(arguments)} could not run in {cwd}: {error}"
        ) from error
    if check and result.returncode != 0:
        raise TaskError(
            "git_failed",
            f"git {' '.join(arguments)} in {cwd} exited {result.returncode}: "
            + (result.stderr.strip() or result.stdout.strip() or "(no output)"),
        )
    return result


def worktree_of(path: Path) -> Path:
    """The worktree ``path`` belongs to, primary or linked; ``git_failed`` outside one."""
    top = _git(path, "rev-parse", "--show-toplevel").stdout.strip()
    return Path(os.path.realpath(top))


def primary_of(path: Path) -> Path:
    """The primary worktree of the repository ``path`` belongs to."""
    common = _git(
        path, "rev-parse", "--path-format=absolute", "--git-common-dir"
    ).stdout.strip()
    return Path(os.path.realpath(common)).parent


def require_primary(path: Path) -> Path:
    """``path`` resolved, refused with ``not_primary`` unless it is the primary worktree."""
    here = Path(os.path.realpath(path))
    top = Path(
        os.path.realpath(_git(here, "rev-parse", "--show-toplevel").stdout.strip())
    )
    if top != primary_of(here):
        raise TaskError("not_primary", f"{top} is not the primary worktree")
    return top


def concorde(primary: Path) -> Path:
    return layout.concorde_of(primary)


def tasks_directory(primary: Path) -> Path:
    return layout.tasks_folder(concorde(primary))


def task_folder(primary: Path, task_id: str) -> Path:
    """The folder of a current task."""
    return layout.task_folder(concorde(primary), task_id)


def history_folder(primary: Path, key: str) -> Path:
    return layout.history_folder(concorde(primary)) / key


def found_folder(primary: Path, task_id: str) -> Path | None:
    """The folder of ``task_id``: the current task's, else the latest of that name in the
    history (a history key names one exactly); None when there is none."""
    current = task_folder(primary, task_id)
    if (current / RECORD).is_file():
        return current
    history = layout.history_folder(concorde(primary))
    if HISTORY_KEY.match(task_id or "") and (history / task_id / RECORD).is_file():
        if "." in task_id or not (history / f"{task_id}.2").exists():
            return history / task_id
    if TASK_ID.match(task_id or "") and history.is_dir():
        numbered = sorted(
            (
                int(item.name.rsplit(".", 1)[1])
                for item in history.glob(f"{task_id}.*")
                if item.name.rsplit(".", 1)[1].isdigit() and (item / RECORD).is_file()
            ),
            reverse=True,
        )
        if numbered:
            return history / f"{task_id}.{numbered[0]}"
    return None


def record_path(primary: Path, task_id: str) -> Path:
    return task_folder(primary, task_id) / RECORD


def decision_log_path(primary: Path, task_id: str) -> Path:
    """The decision log of a task: in its current folder, or once closed in the history."""
    folder = task_folder(primary, task_id)
    if not folder.exists():
        found = found_folder(primary, task_id)
        if found is not None:
            return found / DECISIONS
    return folder / DECISIONS


def committed_log(key: str) -> str:
    """The path, relative to the project, at which an ended task's decision log is committed."""
    return f"{DECISION_LOGS}/{key}.md"


def _in_head(primary: Path, path: str) -> bool:
    return _git(primary, "cat-file", "-e", f"HEAD:{path}", check=False).returncode == 0


def history_key(primary: Path, task_id: str) -> str:
    """The history key a closing task gets: free in the history and among the decision logs of
    the primary worktree, committed or not, so that no closed task replaces another."""

    def taken(key: str) -> bool:
        path = committed_log(key)
        return (primary / path).exists() or _in_head(primary, path)

    return layout.history_key(concorde(primary), task_id, taken)


def workspace_store(primary: Path, task_id: str, folder: Path | None = None) -> Store:
    """The run store of a task's workspace: its folder's ``workspace/``, locks under the primary
    worktree's ``.concorde``."""
    folder = folder or task_folder(primary, task_id)
    return Store(concorde(primary), layout.workspace_folder(folder))


def task_lock_path(primary: Path, task_id: str) -> Path:
    return layout.lock_file(concorde(primary), "task", task_id)


def unwritten_decision_log(primary: Path, record: dict) -> str | None:
    """A warning when the task's decision log holds nothing beyond what ``open`` wrote."""
    log = decision_log_path(primary, record["id"])
    opened = f"# Decision log: {record['id']}\n\nGoal: {record['goal']}"
    try:
        text = log.read_text(encoding="utf-8")
    except OSError:
        return f"the decision log {log} of task {record['id']} is missing"
    if text.strip() != opened.strip():
        return None
    return (
        f"the decision log {log} of task {record['id']} holds only its heading and goal: "
        "no decision taken without the developer and no non-ok result was recorded; "
        "append them before reporting the task"
    )


def _unknown(primary: Path, task_id: str) -> TaskError:
    directory = tasks_directory(primary)
    known = (
        sorted(path.parent.name for path in directory.glob(f"*/{RECORD}"))
        if directory.is_dir()
        else []
    )
    return TaskError(
        "unknown_task",
        f"no task {task_id!r} in {directory} (known tasks: {', '.join(known) or 'none'})",
    )


def load_task(primary: Path, task_id: str) -> dict:
    """The record of a current task; ``unknown_task`` for any other."""
    path = record_path(primary, task_id)
    if not TASK_ID.match(task_id or "") or not path.is_file():
        raise _unknown(primary, task_id)
    return _read_record(path)


def closed_in_history(primary: Path, task_id: str) -> dict | None:
    """The record of the latest task of that name in the history when no current task has it;
    None otherwise."""
    if not TASK_ID.match(task_id or "") or record_path(primary, task_id).is_file():
        return None
    folder = found_folder(primary, task_id)
    return None if folder is None else _read_record(folder / RECORD)


def load_unended(primary: Path, task_id: str, purpose: str) -> dict:
    """The record of a current task that is neither closed nor failed; ``task_closed`` for a task
    that ended, still current or moved to the history, saying ``purpose``; ``unknown_task``
    when there is none."""
    try:
        record = load_task(primary, task_id)
    except TaskError as error:
        record = (
            closed_in_history(primary, task_id)
            if error.code == "unknown_task"
            else None
        )
        if record is None:
            raise
    if record["state"] in ENDED:
        raise TaskError(
            "task_closed", f"task {task_id} is {record['state']}; {purpose}"
        )
    return record


def refuse_closed(primary: Path, task_id: str) -> dict:
    """The record of a current task, for ``close`` and ``merge``; ``invalid_transition`` for a
    task whose close moved it to the history, ``unknown_task`` when there is none."""
    try:
        return load_task(primary, task_id)
    except TaskError as error:
        ended = (
            closed_in_history(primary, task_id)
            if error.code == "unknown_task"
            else None
        )
        if ended is None:
            raise
        raise TaskError(
            "invalid_transition",
            f"task {task_id} is already {ended['state']}, with outcome "
            f"{(ended.get('closed') or {}).get('outcome')}, and its folder is in the history "
            f"({found_folder(primary, task_id)}), which is never changed",
        ) from None


def load_any(primary: Path, task_id: str) -> tuple[dict, Path]:
    """The record and folder of a current task or, when there is none, of the task in the
    history; ``unknown_task`` when neither exists."""
    folder = found_folder(primary, task_id)
    if folder is None:
        raise _unknown(primary, task_id)
    return _read_record(folder / RECORD), folder


def _read_record(path: Path) -> dict:
    try:
        return upgraded(json.loads(path.read_text()), path.parent)
    except (OSError, ValueError) as error:
        raise TaskError(
            "record_unreadable", f"the task record {path} cannot be read: {error}"
        ) from error


def upgraded(record: dict, folder: Path) -> dict:
    """``record`` in the current version. A record written before version 3 names no main
    agent's session and holds no reports: its sessions are those its task sessions were started
    for, from their nodes in ``folder``, the latest one its main, and it has no reports."""
    if record.get("schema_version", RECORD_VERSION) < RECORD_VERSION:
        mains = []
        for item in sessions(None, record["id"], folder):
            if item["main"] and (not mains or mains[-1]["main"] != item["main"]):
                mains.append({"main": item["main"], "at": item["started_at"]})
        record["schema_version"] = RECORD_VERSION
        record["main"] = mains[-1]["main"] if mains else None
        record["mains"] = mains
        record["reports"] = []
    return record


@contextmanager
def task_locked(primary: Path, task_id: str):
    """Hold the task's lock: every change of its record and trace is made while holding it."""
    with locks.hold(
        task_lock_path(primary, task_id),
        f"change of task {task_id}",
        wait=None,
        task=task_id,
    ):
        yield


def merge_lock_path(primary: Path) -> Path:
    return layout.lock_file(concorde(primary), "merge")


def _holder(path: Path) -> str:
    """The holder a live lock names, as text for a refusal."""
    try:
        text = path.read_text()
    except OSError as error:
        return f"a holder whose entry in {path} cannot be read ({error})"
    return locks.describe(text)


@contextmanager
def merge_lock(primary: Path, command: str, task_id: str, wait: float = MERGE_WAIT):
    """Hold the primary worktree's merge lock; yield the seconds spent waiting for it.

    The lock is a ``flock`` of this process, so the kernel releases it however the process
    ends. While holding it, the process names itself in the lock file for waiters that give up.
    """
    path = merge_lock_path(primary)
    try:
        with locks.hold(
            path,
            f"`concorde task {command}` of task {task_id}",
            wait=wait,
            task=task_id,
        ) as waited:
            yield waited
    except locks.LockBusy as busy:
        raise TaskError(
            "merge_busy",
            f"`concorde task {command}` of task {task_id} waited {wait:g} s for "
            f"the merge lock {path} of the primary worktree {primary}, which "
            f"is still held by {busy.holder}; one merge, open or close runs at a time",
        ) from None


def merge_lock_held(primary: Path) -> bool:
    """Whether a live process holds the merge lock now; never called while holding it."""
    return locks.held(merge_lock_path(primary))


@contextmanager
def task_workspace_locked(
    primary: Path, task_id: str, command: str, wait: float = MERGE_WAIT
):
    """Hold the task's workspace lock, waiting for it up to ``wait`` seconds, or refuse with
    ``workspace_busy``; yield the seconds spent waiting.

    ``merge`` and ``close`` take it before the merge lock, so that no run of the task's workspace
    commits on its branch or changes its worktree while the task is merged or closed, and so that
    waiting for a run of this task, such as a delivery still finishing, never holds up the merges
    of other tasks. The wait happens inside this process: a caller asks once and never polls.
    """
    started = time.monotonic()
    stack = ExitStack()
    try:
        stack.enter_context(
            workspace_lock(
                workspace_store(primary, task_id),
                task_id,
                f"`concorde task {command}` of task {task_id}",
                wait=wait,
                task=task_id,
            )
        )
    except RunError as error:
        raise TaskError(
            "workspace_busy",
            f"{error}; `concorde task {command}` waits up to {wait:g} s for the workspace "
            f"lock of task {task_id}, so that no run of its workspace changes the task branch "
            "or worktree while the task is merged or closed, and `concorde task show "
            f"{task_id}` names the run holding it",
        ) from None
    with stack:
        yield round(time.monotonic() - started, 3)


def _write(path: Path, data: bytes) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix=".task-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def _serialize(record: dict) -> bytes:
    return (json.dumps(record, indent=2) + "\n").encode()


def update(primary: Path, task_id: str, change, *, locked: bool = False) -> dict:
    """Apply ``change(record) -> record`` bound to the bytes read, holding the task's lock.

    ``locked`` says the caller already holds the task's lock. A change made meanwhile by a
    process that did not take the lock is detected and ``change`` is applied again to what is
    there, so the preconditions it checks hold for the record it writes.
    """
    path = record_path(primary, task_id)
    if not TASK_ID.match(task_id or "") or not path.is_file():
        raise _unknown(primary, task_id)
    with contextlib.nullcontext() if locked else task_locked(primary, task_id):
        for _ in range(ATTEMPTS):
            if not path.is_file():
                raise _unknown(primary, task_id)
            before = path.read_bytes()
            record = change(upgraded(json.loads(before), path.parent))
            record["updated_at"] = now()
            if path.read_bytes() != before:
                continue
            try:
                _write(path, _serialize(record))
            except OSError as error:
                raise TaskError(
                    "record_unwritable",
                    f"the task record {path} cannot be written: {error}",
                ) from error
            return record
    raise TaskError(
        "record_conflict", f"task {task_id} changed concurrently {ATTEMPTS} times"
    )


def _records(primary: Path, *, history: bool = False) -> list[dict]:
    """Every current task's record as stored, and with ``history`` every closed task's, in
    folder-name order."""
    parents = [tasks_directory(primary)]
    if history:
        parents.append(layout.history_folder(concorde(primary)))
    records = []
    for parent in parents:
        for path in sorted(parent.glob(f"*/{RECORD}")) if parent.is_dir() else []:
            try:
                records.append(upgraded(json.loads(path.read_text()), path.parent))
            except (OSError, ValueError) as error:
                raise TaskError(
                    "record_unreadable",
                    f"the task record {path} cannot be read: {error}",
                ) from error
    return records


# --- the task's trace ------------------------------------------------------------------------


def task_node(primary: Path, task_id: str, folder: Path | None = None) -> dict | None:
    """The task's own trace node as recorded, or None."""
    return trace.read(folder or task_folder(primary, task_id))


def _node_of(folder: Path) -> dict:
    record = trace.read(folder)
    if record is None:
        raise TaskError(
            "record_unreadable",
            f"the trace node {folder / layout.TRACE} of the task cannot be read",
        )
    return record


def _task_content(record: dict) -> dict:
    return dict(record["content"]["data"])


def change_trace(
    primary: Path, task_id: str, change, folder: Path | None = None
) -> dict:
    """Apply ``change(content) -> content`` to the task node's content; the caller holds the
    task's lock. Returns the node written."""
    folder = folder or task_folder(primary, task_id)
    record = _node_of(folder)
    record["content"] = {
        "type_id": TASK_TRACE,
        "schema_version": 1,
        "data": change(_task_content(record)),
    }
    try:
        trace.write(folder, record)
    except OSError as error:
        raise TaskError(
            "record_unwritable",
            f"the trace node {folder / layout.TRACE} of task {task_id} cannot be written: "
            f"{error}",
        ) from error
    return record


def _transition(primary: Path, task_id: str, state: str) -> None:
    def change(content):
        content["transitions"] = [
            *content["transitions"],
            {"state": state, "at": now()},
        ]
        return content

    change_trace(primary, task_id, change)


def escalations(primary: Path, task_id: str, folder: Path | None = None) -> list[dict]:
    """The task's escalations, numbered from 1, from its trace."""
    record = task_node(primary, task_id, folder)
    return list(_task_content(record)["escalations"]) if record else []


def unfinished_merge(primary: Path) -> dict | None:
    """The record of the current task stored as ``merging``, or None; merges run one at a
    time."""
    for record in _records(primary):
        if record["state"] == "merging":
            return record
    return None


def merge_commit(primary: Path, merging: dict) -> str | None:
    """The primary worktree's ``HEAD`` when it is the merge that ``merging`` began, else None.

    Once the merge recorded its commit, only that commit counts. Before, ``HEAD`` counts when it
    is a merge commit of exactly the commit before and the checked commit.
    """
    head = _git(primary, "rev-parse", "HEAD").stdout.strip()
    if merging.get("after"):
        return head if head == merging["after"] else None
    parents = _git(primary, "rev-list", "--parents", "-n", "1", "HEAD").stdout.split()
    if parents[1:] == [merging["before"], merging["checked"]]:
        return head
    return None


def incomplete_merge(primary: Path, record: dict) -> TaskError:
    """``merge_incomplete``: the task's merge ended before its checks decided whether it stays."""
    merging = record["merging"]
    head = _git(primary, "rev-parse", "HEAD", check=False).stdout.strip()
    if merge_commit(primary, merging) == head:
        where = f"at {head}, the merge commit"
    elif head == merging["before"]:
        where = f"back at {head}, the commit before the merge"
    else:
        where = (
            f"at {head}, which is neither the commit before the merge nor the merge "
            f"commit {merging.get('after') or '(never recorded)'}"
        )
    return TaskError(
        "merge_incomplete",
        f"task {record['id']} was interrupted while being merged: `concorde task merge` "
        f"(process {merging['pid']}, begun {merging['since']}) was merging its checked delivery "
        f"commit {merging['checked']} into {merging['branch']} of {primary}, which was at "
        f"{merging['before']}, and ended before its checks decided whether the merge stays; "
        f"the primary branch is now {where}. No process holds the merge lock, and until the "
        "merge is resumed or aborted every task open, merge, close, session and escalate is "
        f"refused: `concorde task merge {record['id']} --resume` reruns its checks on the merge "
        f"commit and closes the task or undoes the merge, and `concorde task merge "
        f"{record['id']} --abort` resets {merging['branch']} to {merging['before']} and returns "
        "the task to delivered",
    )


def guard_merges(primary: Path, task_id: str) -> None:
    """Refuse a command that takes no merge lock while a merge is unfinished.

    With no live holder of the merge lock, an unfinished merge is ``merge_incomplete`` for every
    task; while its merge still runs, only a command on the task being merged is refused, with
    ``merge_busy``.
    """
    record = unfinished_merge(primary)
    if record is None:
        return
    if not merge_lock_held(primary):
        raise incomplete_merge(primary, record)
    if record["id"] == task_id:
        raise TaskError(
            "merge_busy",
            f"task {task_id} is being merged by {_holder(merge_lock_path(primary))}; a task "
            "session or escalation for it waits until that merge has closed it or returned "
            "it to delivered",
        )


def begin_merge(primary: Path, task_id: str, merging: dict) -> dict:
    """Store the task as ``merging`` with what its merge is about to do."""

    def change(record):
        if record["state"] != "open":
            raise TaskError(
                "invalid_transition",
                f"task {task_id} is stored {record['state']}; only a delivered task is merged",
            )
        record["state"] = "merging"
        record["merging"] = merging
        return record

    with task_locked(primary, task_id):
        written = update(primary, task_id, change, locked=True)
        _transition(primary, task_id, "merging")
    return written


def merged_at(primary: Path, task_id: str, after: str) -> dict:
    """Record the commit the task's merge produced."""

    def change(record):
        record["merging"]["after"] = after
        return record

    return update(primary, task_id, change)


def end_merge(primary: Path, task_id: str) -> dict:
    """Return a ``merging`` task to ``open``, from which it derives as delivered again."""

    def change(record):
        record["state"] = "open"
        record["merging"] = None
        return record

    with task_locked(primary, task_id):
        written = update(primary, task_id, change, locked=True)
        _transition(primary, task_id, "open")
    return written


def _ignored_inside(primary: Path, worktree: Path) -> None:
    """Refuse a worktree inside the primary worktree that Git would not ignore there."""
    resolved = Path(os.path.realpath(worktree))
    if primary not in resolved.parents:
        return
    relative = resolved.relative_to(primary).as_posix()
    checked = _git(primary, "check-ignore", "-q", relative + "/", check=False)
    if checked.returncode != 0:
        raise TaskError(
            "worktree_not_ignored",
            f"the worktree path {relative}/ lies inside the primary worktree {primary} but Git "
            f"does not ignore it (git check-ignore exited {checked.returncode}), so the task's "
            f"checkout would appear as untracked files of the primary branch; add "
            f"{WORKTREES}/ (or the path's directory) to .gitignore, or pass --path outside "
            "the primary worktree",
        )


# --- task sessions, as nodes of the task's trace -----------------------------------------------

SESSION_TRACE = "concorde-session-trace"
_NULLABLE = {"anyOf": [{"type": "null"}, _TEXT]}
_TOKENS = {"type": "integer", "minimum": 0}
# The fields a session node's content gained with version 2, null until they are learnt.
SESSION_LEARNT = ("session_id", "claude_state", "models", "model_usage")
# contract.task-session.session-trace, version 2
register(
    SESSION_TRACE,
    2,
    {
        "type": "object",
        "additionalProperties": False,
        "required": ["name", "main", "model", "reported_id", *SESSION_LEARNT],
        "properties": {
            "name": _TEXT,
            "main": _NULLABLE,
            "model": _NULLABLE,
            "reported_id": _NULLABLE,
            "session_id": _NULLABLE,
            "claude_state": _NULLABLE,
            "models": {
                "anyOf": [
                    {"type": "null"},
                    {
                        "type": "object",
                        "additionalProperties": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": [
                                "tokens_in",
                                "tokens_out",
                                "tokens_cache_read",
                                "tokens_cache_write",
                                "messages",
                            ],
                            "properties": {
                                "tokens_in": _TOKENS,
                                "tokens_out": _TOKENS,
                                "tokens_cache_read": _TOKENS,
                                "tokens_cache_write": _TOKENS,
                                "messages": _TOKENS,
                            },
                        },
                    },
                ]
            },
            "model_usage": {"anyOf": [{"type": "null"}, {"type": "object"}]},
        },
    },
)


def session_content(data: dict) -> dict:
    """A session node's content data in the current version, from ``data`` of any version: a
    node written before version 2 has none of the learnt fields, which stay null."""
    return {
        "name": data["name"],
        "main": data.get("main"),
        "model": data.get("model"),
        "reported_id": data.get("reported_id"),
        **{key: data.get(key) for key in SESSION_LEARNT},
    }


def sessions_folder(primary: Path, task_id: str, folder: Path | None = None) -> Path:
    return (folder or task_folder(primary, task_id)) / "sessions"


def session_folder(primary: Path, task_id: str, session_id: str) -> Path:
    return sessions_folder(primary, task_id) / session_id


def sessions(primary: Path, task_id: str, folder: Path | None = None) -> list[dict]:
    """The task's Claude Code task sessions in the order they started, from its trace."""
    found = []
    parent = sessions_folder(primary, task_id, folder)
    for item in sorted(parent.iterdir()) if parent.is_dir() else []:
        record = trace.read(item)
        if record is None or record.get("kind") != "session":
            continue
        data = record["content"]["data"]
        found.append(
            {
                "id": record["id"],
                "name": data["name"],
                "main": data["main"],
                "model": data["model"],
                "reported_id": data["reported_id"],
                "session_id": data.get("session_id"),
                "started_at": record["started_at"],
                "directory": item.as_posix(),
            }
        )
    found.sort(key=lambda item: (item["started_at"], item["id"]))
    return found


def _current_open(primary: Path, task_id: str) -> dict:
    """The record of a current task that has not ended; ``task_closed`` otherwise."""
    return load_unended(primary, task_id, "a session works only in an open task")


def record_session(primary: Path, task_id: str, session: dict) -> dict:
    """Record a started task session as a node of the task's trace, for a task that has not
    ended, and its main session as the task's main. ``session`` names its identity, name, main
    session, model, the identity Claude Code reported and, when Claude Code told it, the full
    session id."""
    # Checked before taking the lock too, so no lock file is made again for a closed task.
    _current_open(primary, task_id)
    with task_locked(primary, task_id):
        record = _current_open(primary, task_id)
        if session.get("main"):
            record = _bind_main(primary, task_id, session["main"])
        folder = session_folder(primary, task_id, session["id"])
        node = Node(
            folder,
            session["id"],
            "session",
            content_type=SESSION_TRACE,
            metadata={"task": task_id, "model": session.get("model")},
            content=session_content(session),
            started_at=session.get("started_at"),
        )
        # Concorde does not see a session end; the task's end finishes the node.
        node.record["status"] = "unknown"
        node.start()
        if node.failure is not None:
            raise TaskError(
                "record_unwritable",
                f"the session node {folder} of task {task_id} cannot be written: {node.failure}",
            )
        return record


def _bind_main(primary: Path, task_id: str, main: str) -> dict:
    """Name ``main`` as the task's main agent's session in its record and, when it changes,
    append it to the names the record keeps; the caller holds the task's lock and checked that
    the task has not ended."""
    stamp = now()

    def change(record):
        if record["main"] != main:
            record["main"] = main
            record["mains"] = [*record["mains"], {"main": main, "at": stamp}]
        return record

    return update(primary, task_id, change, locked=True)


def rebind(primary: Path, task_id: str, main: str) -> dict:
    """Name ``main`` as the session the task's task sessions report to from now on."""
    main = (main or "").strip()
    if not main:
        raise TaskError(
            "invalid_input",
            "--main must name the main agent's session, which the task sessions report to",
        )
    purpose = "a task that ended has no task session to report"
    load_unended(primary, task_id, purpose)
    with task_locked(primary, task_id):
        former = load_unended(primary, task_id, purpose)["main"]
        record = _bind_main(primary, task_id, main)
    return {"record": record, "former": former}


def _append_log(
    primary: Path, task_id: str, heading: str, body: str, what: str
) -> None:
    """Append an entry to the task's decision log; ``decision_log_failed`` when the file system
    refuses, saying that ``what`` is recorded in the task record already."""
    path = decision_log_path(primary, task_id)
    try:
        with path.open("a", encoding="utf-8") as stream:
            stream.write(f"\n## {heading}\n\n{body}\n")
    except OSError as failure:
        raise TaskError(
            "decision_log_failed",
            f"{what} was written to the record of task {task_id} (`concorde task show "
            f"{task_id}` prints it), but appending it to the decision log {path} failed "
            f"afterwards: {failure}; recording it again would record it twice, so once the log "
            f"is writable append it there by hand under the heading `## {heading}`:\n{body}",
        ) from failure


def report(primary: Path, task_id: str, text: str, escalated: list[int]) -> dict:
    """Record a task session's report to the main agent in the task record and decision log,
    before the session messages it; the report and the main agent's session to message."""
    text = (text or "").strip()
    if not text:
        raise TaskError("invalid_input", "--text must give the report")
    purpose = "a task that ended has no main agent waiting for its report"
    load_unended(primary, task_id, purpose)
    stamp = now()
    entry = {}
    with task_locked(primary, task_id):
        record = load_unended(primary, task_id, purpose)
        known = len(escalations(primary, task_id))
        wrong = [number for number in escalated if not 1 <= number <= known]
        if wrong:
            raise TaskError(
                "unknown_escalation",
                f"--escalation {', '.join(map(str, wrong))} is not an escalation of task "
                f"{task_id}, which has {known} (numbered from 1 in record order)",
            )

        def change(record):
            entry.update(
                number=len(record["reports"]) + 1,
                at=stamp,
                main=record["main"],
                text=text,
                escalations=list(dict.fromkeys(escalated)),
                answer=None,
            )
            record["reports"] = [*record["reports"], dict(entry)]
            return record

        record = update(primary, task_id, change, locked=True)
    carried = (
        f"\n\nIt carries escalation(s) {', '.join(map(str, entry['escalations']))}."
        if entry["escalations"]
        else ""
    )
    _append_log(
        primary,
        task_id,
        f"Report {entry['number']} to the main agent ({record['main'] or 'no session named'}), "
        f"{stamp}",
        f"{text}{carried}",
        f"report {entry['number']}",
    )
    return {
        "report": entry,
        "main": record["main"],
        "decision_log": decision_log_path(primary, task_id).as_posix(),
    }


def answer(primary: Path, task_id: str, numbers: list[int], text: str) -> dict:
    """Record the main agent's answer to reports of the task in its record and decision log."""
    text = (text or "").strip()
    if not text:
        raise TaskError("invalid_input", "--text must give the answer")
    if not numbers:
        raise TaskError("invalid_input", "--report must name the reports answered")
    numbers = list(dict.fromkeys(numbers))
    purpose = "a task that ended has no task session to answer"
    load_unended(primary, task_id, purpose)
    stamp = now()
    answered = []
    with task_locked(primary, task_id):
        load_unended(primary, task_id, purpose)

        def change(record):
            known = record["reports"]
            wrong = [number for number in numbers if not 1 <= number <= len(known)]
            if wrong:
                raise TaskError(
                    "unknown_report",
                    f"--report {', '.join(map(str, wrong))} is not a report of task {task_id}, "
                    f"which has {len(known)} (numbered from 1 in record order)",
                )
            done = [n for n in numbers if known[n - 1]["answer"] is not None]
            if done:
                raise TaskError(
                    "already_answered",
                    f"report(s) {', '.join(map(str, done))} of task {task_id} were answered "
                    "already (`concorde task show` prints each answer); an answer is never "
                    "replaced",
                )
            updated = [dict(item) for item in known]
            answered.clear()
            for number in numbers:
                updated[number - 1]["answer"] = {"at": stamp, "text": text}
                answered.append(updated[number - 1])
            record["reports"] = updated
            return record

        update(primary, task_id, change, locked=True)
    _append_log(
        primary,
        task_id,
        f"Answer to report(s) {', '.join(map(str, numbers))} of the task session, {stamp}",
        text,
        f"the answer to report(s) {', '.join(map(str, numbers))}",
    )
    return {
        "answered": answered,
        "decision_log": decision_log_path(primary, task_id).as_posix(),
    }


def _registry(root: Path) -> set[str]:
    from ..spec.repository import SpecRepository
    from ..spec.repository_base import SpecError

    try:
        return set(SpecRepository(root).modules)
    except (SpecError, OSError, ValueError) as error:
        detail = error.describe() if isinstance(error, SpecError) else str(error)
        raise TaskError(
            "specs_unloadable", f"the Specs of {root} cannot be loaded: {detail}"
        ) from error


def registered(root: Path, modules: list[str]) -> None:
    known = _registry(root)
    unknown = sorted(item for item in modules if item not in known)
    if unknown:
        raise TaskError(
            "unknown_module",
            f"{', '.join(unknown)} {'is' if len(unknown) == 1 else 'are'} not registered in "
            f"{root} (registered: {', '.join(sorted(known))})",
        )


def open_task(
    primary: Path,
    task_id: str,
    goal: str,
    modules: list[str],
    *,
    base: str | None = None,
    path: Path | None = None,
    wait: float = MERGE_WAIT,
) -> dict:
    """Create the branch, the worktree, the record and the decision log of a new task.

    Holds the merge lock, so the task is never based on a merge that may still be undone.
    """
    primary = require_primary(primary)
    _prune(primary)
    with merge_lock(primary, "open", task_id, wait):
        unfinished = unfinished_merge(primary)
        if unfinished is not None:
            raise incomplete_merge(primary, unfinished)
        return _open_task(primary, task_id, goal, modules, base=base, path=path)


def _open_task(
    primary: Path,
    task_id: str,
    goal: str,
    modules: list[str],
    *,
    base: str | None,
    path: Path | None,
) -> dict:
    if not TASK_ID.match(task_id or ""):
        raise TaskError("invalid_task_id", f"invalid task identity: {task_id!r}")
    problems = []
    if not goal or not goal.strip():
        problems.append("the goal is empty")
    if not modules:
        problems.append("no Module is named")
    duplicates = sorted({item for item in modules if modules.count(item) > 1})
    if duplicates:
        problems.append(f"Modules are named twice: {', '.join(duplicates)}")
    if problems:
        raise TaskError(
            "invalid_input",
            "a task needs a goal and distinct Modules: " + "; ".join(problems),
        )
    if task_folder(primary, task_id).exists():
        raise TaskError(
            "task_exists",
            f"task {task_id} already exists ({task_folder(primary, task_id)}); choose another "
            "identity or close it first",
        )
    branch = f"concorde/{task_id}"
    if (
        _git(
            primary,
            "rev-parse",
            "--verify",
            "--quiet",
            f"refs/heads/{branch}",
            check=False,
        ).returncode
        == 0
    ):
        raise TaskError(
            "branch_exists",
            f"branch {branch} already exists in {primary} although no task record does; "
            "delete the branch or choose another task identity",
        )
    worktree = Path(os.path.abspath(path or primary / WORKTREES / task_id))
    if worktree.exists():
        raise TaskError(
            "path_exists",
            f"the worktree path {worktree} already exists; pass --path or remove it",
        )
    _ignored_inside(primary, worktree)
    registered(primary, modules)
    base_commit = _git(
        primary, "rev-parse", "--verify", f"{base or 'HEAD'}^{{commit}}"
    ).stdout.strip()
    worktree.parent.mkdir(parents=True, exist_ok=True)
    created = _git(
        primary,
        "worktree",
        "add",
        "-b",
        branch,
        str(worktree),
        base_commit,
        check=False,
    )
    if created.returncode != 0:
        raise TaskError(
            "worktree_failed",
            f"git worktree add -b {branch} {worktree} {base_commit} exited "
            f"{created.returncode}: {created.stderr.strip()}",
        )
    folder = task_folder(primary, task_id)
    workspace = layout.workspace_folder(folder)
    try:
        workspace.mkdir(parents=True)
        workspace_binding.write(
            worktree,
            {
                "schema_version": 2,
                "workspace": task_id,
                "root": os.path.realpath(worktree),
                "branch": branch,
                "base_commit": base_commit,
                "goal": goal,
                "modules": list(modules),
                "traces": os.path.realpath(workspace),
                "concorde": os.path.realpath(concorde(primary)),
            },
        )
    except (OSError, ValueError) as error:
        shutil.rmtree(folder, ignore_errors=True)
        raise TaskError(
            "binding_failed",
            f"the workspace binding {workspace_binding.BINDING} of the new worktree {worktree} "
            f"could not be written: {error}. The worktree and branch {branch} exist but no task "
            f"was recorded; remove them with git worktree remove {worktree} and git branch -D "
            f"{branch} before opening the task again",
        ) from error
    stamp = now()
    record = {
        "schema_version": RECORD_VERSION,
        "id": task_id,
        "goal": goal,
        "modules": list(modules),
        "branch": branch,
        "worktree": os.path.realpath(worktree),
        "base_commit": base_commit,
        "main": None,
        "mains": [],
        "reports": [],
        "state": "open",
        "created_at": stamp,
        "updated_at": stamp,
        "merging": None,
        "closed": None,
    }
    with task_locked(primary, task_id):
        node = Node(
            folder,
            task_id,
            "task",
            content_type=TASK_TRACE,
            metadata={
                "task": task_id,
                "modules": list(modules),
                "branch": branch,
                "base_commit": base_commit,
                "concorde_commit": concorde_commit(),
                "protocol_version": protocol_version(primary),
            },
            content={
                "goal": goal,
                "worktree": os.path.realpath(worktree),
                "transitions": [{"state": "open", "at": stamp}],
                "escalations": [],
                "closing": None,
            },
        )
        node.keep("record", RECORD)
        node.keep("decision-log", DECISIONS)
        node.start()
        _write(record_path(primary, task_id), _serialize(record))
        log = folder / DECISIONS
        if not log.exists():
            log.write_text(f"# Decision log: {task_id}\n\nGoal: {goal}\n")
    return record


def _prune(primary: Path) -> None:
    """Tracing's retention, at the start of every open and close; a Tracing configuration it
    cannot read refuses the command."""
    try:
        retention.prune(concorde(primary))
    except retention.ConfigError as error:
        raise TaskError("config_invalid", str(error)) from error


def deliveries(primary: Path, record: dict) -> list[dict]:
    """The delivery commits of the task's workspace on its branch, oldest first, as Delivery's
    reader recognises them by their subject; ``verified`` adds whether each has exactly one
    parent."""
    head = _git(
        primary, "rev-parse", "--verify", "--quiet", record["branch"], check=False
    ).stdout.strip()
    if not head:
        return []
    return delivery_commits(primary, record["base_commit"], head, record["id"])


def verified(primary: Path, delivery: dict) -> dict:
    """The delivery commit with ``mismatches``: how it fails Delivery's own check, empty when
    it verifies."""
    return {**delivery, "mismatches": delivery_mismatches(primary, delivery)}


def derived_state(primary: Path, record: dict, runs: list[dict] | None = None) -> str:
    """The task's state: merging, closed or failed as stored; otherwise delivered when its branch
    head is a delivery commit of its workspace that verifies and its worktree is clean, active when its workspace has runs or its branch moved past the base, and open
    before either."""
    if record["state"] in (*ENDED, "merging"):
        return record["state"]
    head = _git(
        primary, "rev-parse", "--verify", "--quiet", record["branch"], check=False
    ).stdout.strip()
    delivered = deliveries(primary, record)
    worktree = Path(record["worktree"])
    if (
        delivered
        and delivered[-1]["commit"] == head
        and not _dirty(worktree)
        and not delivery_mismatches(primary, delivered[-1])
    ):
        return "delivered"
    if runs is None:
        runs = workspace_runs(workspace_store(primary, record["id"]), record["id"])
    if runs or (head and head != record["base_commit"]) or _dirty(worktree):
        return "active"
    return "open"


def list_tasks(
    primary: Path, state: str | None = None, main: str | None = None
) -> list[dict]:
    """Every current and closed task record with its derived state, oldest first; ``state``
    filters on it and ``main`` on the main agent's session the record names."""
    records = _records(primary, history=True)
    records = [item for item in records if main is None or item["main"] == main]
    records.sort(key=lambda item: (item["created_at"], item["id"]))
    for record in records:
        record["state"] = derived_state(primary, record)
    return [item for item in records if state is None or item["state"] == state]


def show_task(primary: Path, task_id: str) -> dict:
    """The record with its derived state, the workspace's runs and delivery commits, each with
    how it fails to verify, the sessions and the escalations from the task's trace, who holds the workspace lock, and the paths of the decision log and of the
    task's folder, current or in the history."""
    record, folder = load_any(primary, task_id)
    store = workspace_store(primary, record["id"], folder)
    runs = workspace_runs(store, record["id"])
    record["state"] = derived_state(primary, record, runs)
    current = folder == task_folder(primary, record["id"])
    return {
        "record": record,
        "runs": runs,
        "deliveries": [verified(primary, item) for item in deliveries(primary, record)],
        "sessions": sessions(primary, record["id"], folder),
        "escalations": escalations(primary, record["id"], folder),
        "busy": lock_holder(store, record["id"]) if current else None,
        "decision_log": (folder / DECISIONS).as_posix(),
        "folder": folder.as_posix(),
    }


def _changes(worktree: Path) -> list[str]:
    """The worktree's uncommitted changes as ``git status`` entries, changes inside a submodule
    included whatever its ``ignore`` setting, without the new paths Git cannot version: a sandbox's ``/dev/null`` mounts of paths
    such as ``.bashrc`` are neither a file, a symbolic link nor a directory, are no content of the
    task, and Delivery leaves them out as well."""
    if not worktree.exists():
        return []
    raw = _git(
        worktree,
        "status",
        "--porcelain",
        "-z",
        "--no-renames",
        "--untracked-files=all",
        "--ignore-submodules=none",
        check=False,
    ).stdout
    entries = [entry for entry in raw.split("\0") if entry]
    changes = []
    for entry in entries:
        if entry.startswith("?? "):
            path = worktree / entry[3:]
            if not (path.is_symlink() or path.is_file() or path.is_dir()):
                continue
        changes.append(entry)
    return changes


def _dirty(worktree: Path) -> bool:
    return bool(_changes(worktree))


def _dirty_detail(worktree: Path) -> str:
    lines = _changes(worktree)
    shown = ", ".join(line[3:] for line in lines[:20])
    more = f" and {len(lines) - 20} more" if len(lines) > 20 else ""
    return f"{worktree} has {len(lines)} uncommitted change(s): {shown}{more}"


def escalate(primary: Path, task_id: str, error: dict) -> int:
    """Record an escalated error link in the task's trace and its decision log; its number.

    A ``task-session`` link escalates to the main agent, a ``main-agent`` link to the developer.
    """
    from ..errors import render

    stamp = now()
    receiver = "main agent" if error["level"] == "task-session" else "developer"
    by = "task-session" if error["level"] == "task-session" else "main-agent"
    number = 0
    with task_locked(primary, task_id):
        load_task(primary, task_id)

        def change(content):
            nonlocal number
            number = len(content["escalations"]) + 1
            content["escalations"] = [
                *content["escalations"],
                {"number": number, "at": stamp, "by": by, "error": error},
            ]
            return content

        change_trace(primary, task_id, change)
    path = decision_log_path(primary, task_id)
    try:
        with path.open("a", encoding="utf-8") as stream:
            stream.write(
                f"\n## Escalated to the {receiver}, {stamp}\n\n{render(error)}\n\n"
                f"```json\n{json.dumps(error, indent=2, ensure_ascii=False)}\n```\n"
            )
    except OSError as failure:
        raise TaskError(
            "decision_log_failed",
            f"the escalation was written to the trace of task {task_id} as escalation "
            f"{number} (`concorde task show {task_id}` prints it under escalations), "
            f"but appending it to the decision log {path} failed afterwards: {failure}; "
            "escalating again would record it twice, so once the log is writable append it "
            f"there by hand under the heading `## Escalated to the {receiver}, {stamp}`; the "
            f"escalated chain:\n{render(error)}",
        ) from failure
    return number


def mergeable(primary: Path, task_id: str) -> tuple[dict, str]:
    """The record and branch head of a task ``close --merged`` accepts once the head is merged:
    the head is the latest delivery commit, which verifies, and the worktree is clean."""
    record = load_task(primary, task_id)
    if record["state"] in ENDED:
        raise TaskError(
            "invalid_transition", f"task {task_id} is already {record['state']}"
        )
    delivered = deliveries(primary, record)
    if not delivered:
        raise TaskError(
            "not_merged",
            f"branch {record['branch']} of task {task_id} holds no delivery commit of its "
            "workspace since the base; only a delivered task can be closed as merged",
        )
    head = _git(primary, "rev-parse", record["branch"]).stdout.strip()
    if head != delivered[-1]["commit"]:
        raise TaskError(
            "not_merged",
            f"{record['branch']} is at {head}, not at its last delivery commit "
            f"{delivered[-1]['commit']}; deliver again, or close it completed or failed",
        )
    mismatches = delivery_mismatches(primary, delivered[-1])
    if mismatches:
        raise TaskError(
            "delivery_unverified",
            f"the head {head} of {record['branch']} of task {task_id} has the subject of a "
            "delivery commit of its workspace but does not verify, so Delivery did not create "
            "it and it may not hold what was validated: " + "; ".join(mismatches),
        )
    worktree = Path(record["worktree"])
    if _dirty(worktree):
        raise TaskError("dirty_worktree", _dirty_detail(worktree))
    return record, head


def close_task(
    primary: Path,
    task_id: str,
    outcome: str,
    *,
    note: str | None = None,
    errors: list[dict] | None = None,
    force: bool = False,
    wait: float = MERGE_WAIT,
) -> dict:
    """End a task, holding the merge lock: ``closed`` as merged or completed, or ``failed``.

    A merged task must have its latest delivery commit in the primary branch. A completed task
    reached its goal without merging and says how in ``note``. A failed task gives its reason in
    ``note`` and the error chains that caused it in ``errors``, or none when no error did. A task
    closed without a merge first has its Claude Code task sessions and the runs of its workspace
    that still run stopped; the close then waits for its workspace lock, so the task's folder moves to the history only once nothing of it runs.
    Once the task is closed, its Claude Code task sessions are removed from Claude's session
    list. ``{"record": <the closed record>, "warnings": [...]}``, the warnings naming what the
    close could not do besides, such as a session it did not remove.
    """
    primary = require_primary(primary)
    problems = []
    if outcome not in OUTCOMES:
        problems.append(f"the outcome {outcome!r} is none of {', '.join(OUTCOMES)}")
    if outcome in ("completed", "failed") and not (note and note.strip()):
        problems.append(
            "a completed task needs --note saying what it achieved"
            if outcome == "completed"
            else "a failed task needs --reason saying why it failed"
        )
    if errors and outcome != "failed":
        problems.append("only a failed task records the errors that caused it")
    if wait < 0:
        problems.append(f"--wait {wait:g} is negative")
    if force and outcome == "merged":
        problems.append("--force applies only to closing without a merge")
    if problems:
        raise TaskError("invalid_input", "; ".join(problems))
    refuse_closed(primary, task_id)
    _prune(primary)
    if outcome != "merged":
        stop_task(primary, task_id)
    started = time.monotonic()
    with task_workspace_locked(primary, task_id, "close", wait):
        remaining = max(0.0, wait - (time.monotonic() - started))
        with merge_lock(primary, "close", task_id, remaining):
            unfinished = unfinished_merge(primary)
            if unfinished is not None:
                raise incomplete_merge(primary, unfinished)
            warnings = []
            closed = close_locked(
                primary,
                task_id,
                outcome,
                note=note,
                errors=errors,
                force=force,
                warnings=warnings,
            )
    return {"record": closed, "warnings": warnings + end_sessions(primary, closed)}


def end_sessions(primary: Path, closed: dict) -> list[str]:
    """Remove the Claude Code task sessions of a task just closed from Claude's session list,
    after the close, which kept their transcripts; the warnings of those it did not remove."""
    from . import session

    folder = history_folder(primary, closed["closed"]["history"])
    return session.remove_sessions(primary, closed["id"], folder)


def stop_task(primary: Path, task_id: str) -> list[str]:
    """Stop what still runs for a task: first its Claude Code task sessions, with
    ``claude stop``, so none starts another run or keeps working in the worktree the close
    removes, then each run of its workspace whose runner holds its run lock and is visible to
    this process, with ``SIGTERM``. The runs end with their own results; the close then waits
    for the workspace lock. What was stopped, described."""
    import signal

    from . import session

    stopped = session.stop_sessions(primary, task_id)
    store = workspace_store(primary, task_id)
    for folder in store.folders():
        progress = load_progress_of(folder)
        run_id = (progress or {}).get("run_id") or folder.name
        lock = store.run_lock(run_id)
        for pid in locks.holder_pids(lock):
            try:
                os.kill(pid, signal.SIGTERM)
                stopped.append(f"run {run_id} (process {pid})")
            except OSError:
                continue
    return stopped


def load_progress_of(folder: Path) -> dict | None:
    try:
        value = json.loads((folder / layout.PROGRESS).read_text())
    except (OSError, ValueError):
        return None
    return value if isinstance(value, dict) else None


def close_locked(
    primary: Path,
    task_id: str,
    outcome: str,
    *,
    note: str | None = None,
    errors: list[dict] | None = None,
    force: bool = False,
    again: str | None = None,
    before_move=None,
    warnings: list[str] | None = None,
    key: str | None = None,
    at: str | None = None,
) -> dict:
    """``close_task`` for a caller already holding the merge lock and the workspace lock.

    Removing the worktree, writing the record, ending the trace node, appending to the decision
    log and moving the folder to the history cannot be one transaction, so a refusal after one of
    them says what this close did and that ``again`` (by default the same close) finishes it; the
    same close of a task whose record is closed but that is still current finishes the steps it
    lacks. Once the closing is logged, the decision log is committed on the primary branch as
    ``.concorde/decisions/<key>.md`` unless that file already holds it, as the merge commit of
    ``concorde task merge`` does with the closing dated ``at``; ``key``, the history key, is the
    one that merge chose, and free otherwise, and ``at`` the time the closing names, by default
    now. Before the folder moves, the transcripts of the task's Claude Code task
    sessions are copied into their nodes, which are finished from Claude Code's records, adding
    to ``warnings`` each transcript that cannot be kept, and
    ``before_move`` runs, such as a merge ending its attempt's node.
    """
    from . import session

    errors = list(errors or [])
    warnings = warnings if warnings is not None else []
    again = (
        again or f"`concorde task close {task_id} --{outcome}` with the same options"
    )
    record = load_task(primary, task_id)
    worktree = Path(record["worktree"])
    if record["state"] in ENDED:
        ended = record.get("closed") or {}
        if ended.get("outcome") != outcome:
            raise TaskError(
                "invalid_transition", f"task {task_id} is already {record['state']}"
            )
        if not _closing_logged(primary, task_id, ended):
            _log_closing(primary, task_id, ended)
        commit_decision_log(primary, task_id, ended, again)
        warnings.extend(session.finish_sessions(primary, task_id))
        if before_move is not None:
            before_move()
        _move_to_history(primary, task_id, ended["history"], again)
        return record
    if outcome == "merged":
        record, head = mergeable(primary, task_id)
        contained = _git(
            primary, "merge-base", "--is-ancestor", head, "HEAD", check=False
        )
        if contained.returncode != 0:
            raise TaskError(
                "not_merged", f"{head} is not contained in the primary branch"
            )
    elif _dirty(worktree) and not force:
        raise TaskError(
            "dirty_worktree", _dirty_detail(worktree) + "; pass --force to discard them"
        )
    removed = False
    if worktree.exists():
        # Git removes a worktree that holds submodule checkouts only with --force, which also
        # removes their repositories under the worktree's own administrative directory. The
        # checks above already refused a change inside a submodule unless the close is forced,
        # so the forced removal discards nothing they would have kept. Never `git submodule
        # deinit` here: it would unregister the submodules in the configuration every worktree
        # of the repository shares.
        submodules = (worktree / ".gitmodules").exists()
        arguments = ["worktree", "remove", str(worktree)]
        if force or submodules:
            arguments.insert(2, "--force")
        result = _git(primary, *arguments, check=False)
        if result.returncode != 0:
            raise TaskError(
                "worktree_failed",
                f"git {' '.join(arguments)} exited {result.returncode}: "
                f"{result.stderr.strip()}; this close changed nothing before it, the worktree "
                f"is as Git left it and the record of task {task_id} is unchanged; once the "
                f"cause is fixed, {again} finishes the close",
            )
        removed = True
    primary_head = _git(primary, "rev-parse", "HEAD").stdout.strip()

    stamp = at or now()
    state = "failed" if outcome == "failed" else "closed"
    key = key or history_key(primary, task_id)
    closing = {
        "state": state,
        "outcome": outcome,
        "note": note.strip() if note and note.strip() else None,
        "errors": errors,
        "at": stamp,
        "primary_commit": primary_head,
        "worktree_removed": removed,
        "history": key,
    }

    def change(record):
        record["state"] = state
        record["merging"] = None
        record["closed"] = closing
        return record

    try:
        with task_locked(primary, task_id):
            closed = update(primary, task_id, change, locked=True)
            _end_task_node(primary, task_id, closing, now())
    except TaskError as error:
        if not removed:
            raise
        raise TaskError(
            error.code,
            f"{error}; this close had already removed the worktree {worktree}, so task "
            f"{task_id} stays {record['state']} without it; once the cause is fixed, {again} "
            "finishes the close",
        ) from error
    _log_closing(primary, task_id, closed["closed"])
    commit_decision_log(primary, task_id, closed["closed"], again)
    warnings.extend(session.finish_sessions(primary, task_id))
    if before_move is not None:
        before_move()
    _move_to_history(primary, task_id, key, again)
    return closed


def _end_task_node(primary: Path, task_id: str, closing: dict, ended: str) -> None:
    """End the task's trace node at ``ended`` with how it ended, which a merge dates earlier,
    when its merge commit was made; the caller holds the task's lock."""
    folder = task_folder(primary, task_id)
    record = _node_of(folder)
    content = _task_content(record)
    content["transitions"] = [
        *content["transitions"],
        {"state": closing["state"], "at": closing["at"]},
    ]
    content["closing"] = {
        key: closing[key]
        for key in (
            "outcome",
            "note",
            "errors",
            "primary_commit",
            "worktree_removed",
            "history",
        )
    }
    status = "failed" if closing["state"] == "failed" else "ok"
    record.update(
        ended_at=ended,
        status=status,
        outcome=closing["outcome"],
        error=closing["errors"][0]
        if status == "failed" and closing["errors"]
        else None,
        usage=trace.usage(
            duration_seconds=trace.seconds_between(record["started_at"], ended)
        ),
        content={"type_id": TASK_TRACE, "schema_version": 1, "data": content},
        artifacts=[
            trace.artifact(folder, identity, name)
            for identity, name in (("record", RECORD), ("decision-log", DECISIONS))
            if (folder / name).exists()
        ],
    )
    try:
        trace.write(folder, record)
    except OSError as error:
        raise TaskError(
            "record_unwritable",
            f"the trace node {folder / layout.TRACE} of task {task_id} cannot be written: "
            f"{error}",
        ) from error


def _move_to_history(primary: Path, task_id: str, key: str, again: str) -> None:
    """Move the closed task's folder to the history and remove its task, workspace and
    workflow locks; the caller holds the workspace lock, so no run of the task runs."""
    folder = task_folder(primary, task_id)
    target = history_folder(primary, key)
    base = concorde(primary)
    with locks.hold(
        task_lock_path(primary, task_id),
        f"close of task {task_id}",
        wait=None,
        remove=True,
    ):
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                raise OSError(f"{target} already exists")
            os.rename(folder, target)
        except OSError as error:
            raise TaskError(
                "history_move_failed",
                f"task {task_id} is closed in its record and its decision log holds the "
                f"closing, but moving its folder {folder} to the history {target} failed: "
                f"{error}; the folder stays where it is, and once the cause is fixed, {again} "
                "moves it",
            ) from error
        # The runtime configuration of its task sessions is no trace.
        shutil.rmtree(target / "runtime", ignore_errors=True)
    for path in (
        layout.lock_file(base, "workspace", task_id),
        layout.lock_file(base, "workflow", task_id),
    ):
        path.unlink(missing_ok=True)


def commit_decision_log(primary: Path, task_id: str, closed: dict, again: str) -> None:
    """Commit the closed task's decision log on the primary branch as
    ``.concorde/decisions/<history key>.md``, in a commit of that file alone, unless the branch
    already holds it exactly, as it does after a merge whose log did not change once its merge
    commit copied it; other changes of the primary worktree, staged or not, stay as they were.
    """
    path = committed_log(closed["history"])
    source = decision_log_path(primary, task_id)
    target = primary / path
    held = subprocess.run(
        ["git", "cat-file", "blob", f"HEAD:{path}"],
        cwd=primary,
        capture_output=True,
        check=False,
    )
    try:
        if held.returncode == 0 and held.stdout == source.read_bytes():
            return
    except OSError:
        pass  # Committing reads the log again and says why it cannot.
    branch = _git(primary, "symbolic-ref", "-q", "--short", "HEAD", check=False)

    def refuse(problem: str) -> TaskError:
        return TaskError(
            "decision_log_uncommitted",
            f"task {task_id} is {closed['state']} in its record and its decision log {source} "
            f"holds the closing, but committing the log as {path} on the primary branch of "
            f"{primary} failed: {problem}; nothing was committed, and once the cause is fixed, "
            f"{again} commits it and finishes the close",
        )

    if branch.returncode != 0:
        raise refuse(
            "the primary worktree has a detached HEAD, so there is no branch to commit on"
        )
    try:
        data = source.read_bytes()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    except OSError as error:
        raise refuse(f"{type(error).__name__}: {error}") from error
    message = (
        f"concorde: keep the decision log of {task_id}\n\n"
        f"Task {task_id} ended {closed['outcome']}.\n\nConcorde-Task: {task_id}\n"
    )
    added = _git(primary, "add", "-f", "--", path, check=False)
    committed = (
        subprocess.run(
            ["git", "commit", "-q", "--only", "-F", "-", "--", path],
            cwd=primary,
            input=message,
            capture_output=True,
            text=True,
            check=False,
        )
        if added.returncode == 0
        else added
    )
    if committed.returncode != 0:
        output = (committed.stdout + committed.stderr).strip() or "(no output)"
        if _in_head(primary, path):
            # The branch holds an earlier copy: put it back, in the index and the worktree.
            _git(primary, "checkout", "-q", "HEAD", "--", path, check=False)
        else:
            _git(
                primary,
                "rm",
                "-q",
                "--cached",
                "--ignore-unmatch",
                "--",
                path,
                check=False,
            )
            target.unlink(missing_ok=True)
        raise refuse(
            f"git {'commit' if added.returncode == 0 else 'add'} exited "
            f"{committed.returncode} on {branch.stdout.strip()}: {output[-2000:]}"
        )


def _closing_heading(closed: dict) -> str:
    return f"## Closed: {closed['outcome']}, {closed['at']}"


def closing_entry(closed: dict) -> str:
    """The entry a close appends to the decision log: how the task ended, with ``note`` and
    the error chains of ``errors`` rendered and as JSON, dated ``at``."""
    from ..errors import render

    lines = [f"\n{_closing_heading(closed)}\n"]
    if closed["note"]:
        lines.append(f"\n{closed['note']}\n")
    for error in closed["errors"]:
        lines.append(
            f"\n{render(error)}\n\n"
            f"```json\n{json.dumps(error, indent=2, ensure_ascii=False)}\n```\n"
        )
    return "".join(lines)


def _closing_logged(primary: Path, task_id: str, closed: dict) -> bool:
    """Whether the decision log holds the closing of the record's ``closed``."""
    path = decision_log_path(primary, task_id)
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return False
    except OSError as error:
        raise TaskError(
            "decision_log_failed",
            f"task {task_id} is already {closed['state']}, and its decision log {path} cannot "
            f"be read to see whether it holds that closing: {error}",
        ) from error
    return _closing_heading(closed) in lines


def _log_closing(primary: Path, task_id: str, closed: dict) -> None:
    """Append how the task ended, with any error chains rendered and as JSON."""
    path = decision_log_path(primary, task_id)
    try:
        with path.open("a", encoding="utf-8") as stream:
            stream.write(closing_entry(closed))
    except OSError as error:
        raise TaskError(
            "decision_log_failed",
            f"task {task_id} is {closed['state']} in its record, with outcome "
            f"{closed['outcome']} at {closed['at']}, but appending its closing to the decision "
            f"log {path} failed afterwards: {error}; once the log is writable, "
            f"`concorde task close {task_id} --{closed['outcome']}` with the same options "
            "appends it and changes nothing else",
        ) from error


__all__ = [
    "ENDED",
    "MERGE_WAIT",
    "OUTCOMES",
    "STATES",
    "TaskError",
    "begin_merge",
    "close_locked",
    "close_task",
    "closing_entry",
    "commit_decision_log",
    "committed_log",
    "decision_log_path",
    "deliveries",
    "derived_state",
    "end_merge",
    "end_sessions",
    "escalate",
    "guard_merges",
    "history_key",
    "incomplete_merge",
    "list_tasks",
    "load_task",
    "merge_commit",
    "merge_lock",
    "merge_lock_held",
    "merge_lock_path",
    "mergeable",
    "merged_at",
    "open_task",
    "primary_of",
    "record_session",
    "require_primary",
    "session_content",
    "show_task",
    "task_workspace_locked",
    "unfinished_merge",
    "unwritten_decision_log",
    "verified",
]
