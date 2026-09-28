"""The Task store: task records and decision logs in the primary worktree, and the task commands.

A task is a branch ``concorde/<id>``, a worktree checked out on it and bound as the workspace
``<id>``, a record ``.concorde/tasks/<id>.json`` and a decision log
``.concorde/tasks/<id>.decisions.md``, all owned by the primary worktree. Only this module writes
records, and nothing below the task level writes them: whether a task is active or delivered is
derived each time from what the execution core recorded, its runs in the run store and its
delivery commits on the branch, a delivery counting only when its commit verifies against its
evidence bundle; ``merging`` is stored while ``concorde task merge`` has put a merge
into the primary branch that its checks have not decided yet. Every change is one read, a check of
its preconditions and one atomic write bound to the bytes read; a concurrent change is retried and
reported as ``record_conflict`` after three attempts.
"""

from __future__ import annotations

import fcntl
import json
import os
import re
import subprocess
import tempfile
import time
from contextlib import ExitStack, contextmanager
from datetime import UTC, datetime
from pathlib import Path

from ..delivery.bundle import delivery_commits, delivery_mismatches
from ..execution import binding as workspace_binding
from ..execution.runs import RunError, lock_holder, workspace_lock, workspace_runs
from ..harness.models import CONFIG, inherit

TASK_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,47}$")
# The stages of a task's life. Only open, merging, closed and failed are stored; active and
# delivered are derived from the workspace's runs and delivery commits whenever a task is read.
STATES = ("open", "active", "delivered", "merging", "closed", "failed")
# How a task ended: closed when its goal was reached, merged or not; failed when it was not.
OUTCOMES = ("merged", "completed", "failed")
ENDED = ("closed", "failed")
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


def tasks_directory(primary: Path) -> Path:
    return primary / ".concorde/tasks"


def record_path(primary: Path, task_id: str) -> Path:
    return tasks_directory(primary) / f"{task_id}.json"


def decision_log_path(primary: Path, task_id: str) -> Path:
    return tasks_directory(primary) / f"{task_id}.decisions.md"


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
        sorted(path.stem for path in directory.glob("*.json"))
        if directory.is_dir()
        else []
    )
    return TaskError(
        "unknown_task",
        f"no task {task_id!r} in {directory} (known tasks: {', '.join(known) or 'none'})",
    )


def load_task(primary: Path, task_id: str) -> dict:
    path = record_path(primary, task_id)
    if not TASK_ID.match(task_id or "") or not path.is_file():
        raise _unknown(primary, task_id)
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError) as error:
        raise TaskError(
            "record_unreadable", f"the task record {path} cannot be read: {error}"
        ) from error


@contextmanager
def _locked(primary: Path):
    directory = tasks_directory(primary)
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / ".lock").open("a+b") as stream:
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def merge_lock_path(primary: Path) -> Path:
    return tasks_directory(primary) / "merge.lock"


def _holder(path: Path) -> str:
    """The holder a live lock names, as text for a refusal."""
    try:
        holder = json.loads(path.read_text() or "null")
    except (OSError, ValueError) as error:
        return f"a holder whose entry in {path} cannot be read ({error})"
    if not isinstance(holder, dict):
        return f"a holder that has not written its entry in {path} yet"
    return (
        f"`concorde task {holder.get('command')}` of task {holder.get('task')} "
        f"(process {holder.get('pid')}, holding it since {holder.get('since')})"
    )


@contextmanager
def merge_lock(primary: Path, command: str, task_id: str, wait: float = MERGE_WAIT):
    """Hold the primary worktree's merge lock; yield the seconds spent waiting for it.

    The lock is a ``flock`` of this process, so the kernel releases it however the process
    ends. While holding it, the process names itself in the lock file for waiters that give up.
    """
    directory = tasks_directory(primary)
    directory.mkdir(parents=True, exist_ok=True)
    path = merge_lock_path(primary)
    started = time.monotonic()
    descriptor = os.open(path, os.O_RDWR | os.O_CREAT, 0o644)
    with os.fdopen(descriptor, "r+") as stream:
        while True:
            try:
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() - started >= wait:
                    raise TaskError(
                        "merge_busy",
                        f"`concorde task {command}` of task {task_id} waited {wait:g} s for "
                        f"the merge lock {path} of the primary worktree {primary}, which "
                        f"is still held by {_holder(path)}; one merge, open or close runs at "
                        "a time",
                    ) from None
                time.sleep(LOCK_POLL)
        waited = round(time.monotonic() - started, 3)
        try:
            stream.seek(0)
            stream.truncate()
            stream.write(
                json.dumps(
                    {
                        "command": command,
                        "task": task_id,
                        "pid": os.getpid(),
                        "since": now(),
                    }
                )
            )
            stream.flush()
            yield waited
        finally:
            stream.seek(0)
            stream.truncate()
            stream.flush()
            fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def merge_lock_held(primary: Path) -> bool:
    """Whether a live process holds the merge lock now; never called while holding it."""
    path = merge_lock_path(primary)
    if not path.exists():
        return False
    with path.open("rb") as stream:
        try:
            fcntl.flock(stream.fileno(), fcntl.LOCK_SH | fcntl.LOCK_NB)
        except BlockingIOError:
            return True
        fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
    return False


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
                primary / ".concorde",
                task_id,
                f"`concorde task {command}` of task {task_id}",
                wait=wait,
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


def update(primary: Path, task_id: str, change) -> dict:
    """Apply ``change(record) -> record`` bound to the bytes read; retry concurrent changes.

    A retry reads the record again and calls ``change`` again, so the preconditions it checks
    hold for the record it writes.
    """
    path = record_path(primary, task_id)
    for _ in range(ATTEMPTS):
        if not TASK_ID.match(task_id or "") or not path.is_file():
            raise _unknown(primary, task_id)
        before = path.read_bytes()
        record = change(json.loads(before))
        record["updated_at"] = now()
        with _locked(primary):
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


def _records(primary: Path) -> list[dict]:
    """Every task record as stored, in file-name order."""
    directory = tasks_directory(primary)
    records = []
    for path in sorted(directory.glob("*.json")) if directory.is_dir() else []:
        try:
            records.append(json.loads(path.read_text()))
        except (OSError, ValueError) as error:
            raise TaskError(
                "record_unreadable", f"the task record {path} cannot be read: {error}"
            ) from error
    return records


def unfinished_merge(primary: Path) -> dict | None:
    """The record of the task stored as ``merging``, or None; merges run one at a time."""
    for record in _records(primary):
        if record["state"] == "merging":
            return record
    return None


def merge_commit(primary: Path, merging: dict) -> str | None:
    """The primary worktree's ``HEAD`` when it is the merge that ``merging`` began, else None.

    Once the merge recorded its commit, only that commit counts. Before, ``HEAD`` counts when it
    is a merge commit of exactly the commit before and the checked commit, or the checked commit
    itself when the merge fast-forwarded to it.
    """
    head = _git(primary, "rev-parse", "HEAD").stdout.strip()
    if merging.get("after"):
        return head if head == merging["after"] else None
    parents = _git(primary, "rev-list", "--parents", "-n", "1", "HEAD").stdout.split()
    if parents[1:] == [merging["before"], merging["checked"]]:
        return head
    ancestor = _git(
        primary, "merge-base", "--is-ancestor", merging["before"], head, check=False
    )
    if head == merging["checked"] and ancestor.returncode == 0:
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

    return update(primary, task_id, change)


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

    return update(primary, task_id, change)


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


def record_session(primary: Path, task_id: str, session: dict) -> dict:
    """Append a started task session to the record of an open, active or delivered task."""

    def change(record):
        if record["state"] in ENDED:
            raise TaskError(
                "task_closed",
                f"task {task_id} is {record['state']}; a session works only in an open task",
            )
        record.setdefault("sessions", []).append(session)
        return record

    return update(primary, task_id, change)


def _pi_session(record: dict, session_id: str) -> dict:
    for item in record.get("sessions") or []:
        if item.get("program") == "pi" and item.get("id") == session_id:
            return item
    raise TaskError(
        "no_session",
        f"task {record['id']} has no pi task session {session_id}",
    )


def begin_round(primary: Path, task_id: str, session_id: str, entry: dict) -> dict:
    """Append a running round to a pi task session of an unended task whose rounds have all
    ended.

    The task's state is checked inside the transaction, so a close stored between the caller's
    own check and this write refuses the round.
    """

    def change(record):
        if record["state"] in ENDED:
            raise TaskError(
                "task_closed",
                f"task {task_id} is {record['state']}; a round of a task session begins only "
                "in an open task",
            )
        found = _pi_session(record, session_id)
        running = [item for item in found["rounds"] if item["status"] == "running"]
        if running:
            raise TaskError(
                "session_busy",
                f"round {running[-1]['round']} of the task session of {task_id} is still "
                f"running (supervisor process {running[-1]['supervisor_pid']})",
            )
        found["rounds"].append(entry)
        return record

    return update(primary, task_id, change)


def finish_round(
    primary: Path, task_id: str, session_id: str, number: int, fields: dict
) -> dict:
    """Set the outcome of a running round of a pi task session, also of a closed task."""

    def change(record):
        found = _pi_session(record, session_id)
        for item in found["rounds"]:
            if item["round"] == number and item["status"] == "running":
                item.update(fields)
                item["ended_at"] = now()
                return record
        raise TaskError(
            "session_idle",
            f"round {number} of the task session {session_id} of {task_id} is not running",
        )

    return update(primary, task_id, change)


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
    if record_path(primary, task_id).exists():
        raise TaskError(
            "task_exists",
            f"task {task_id} already exists ({record_path(primary, task_id)}); choose another "
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
    try:
        inherit(primary, worktree)
    except OSError as error:
        raise TaskError(
            "config_copy_failed",
            f"the worker model configuration {CONFIG} of {primary} could not be copied into the "
            f"new worktree {worktree}: {error}. The worktree and branch {branch} exist but no "
            f"task was recorded; remove them with git worktree remove {worktree} and git branch "
            f"-D {branch} before opening the task again",
        ) from error
    try:
        workspace_binding.write(
            worktree,
            {
                "schema_version": 1,
                "workspace": task_id,
                "root": os.path.realpath(worktree),
                "branch": branch,
                "base_commit": base_commit,
                "goal": goal,
                "modules": list(modules),
                "records": os.path.realpath(primary / ".concorde"),
            },
        )
    except (OSError, ValueError) as error:
        raise TaskError(
            "binding_failed",
            f"the workspace binding {workspace_binding.BINDING} of the new worktree {worktree} "
            f"could not be written: {error}. The worktree and branch {branch} exist but no task "
            f"was recorded; remove them with git worktree remove {worktree} and git branch -D "
            f"{branch} before opening the task again",
        ) from error
    stamp = now()
    record = {
        "id": task_id,
        "goal": goal,
        "modules": list(modules),
        "branch": branch,
        "worktree": os.path.realpath(worktree),
        "base_commit": base_commit,
        "state": "open",
        "created_at": stamp,
        "updated_at": stamp,
        "escalations": [],
        "sessions": [],
        "merging": None,
        "closed": None,
    }
    with _locked(primary):
        _write(record_path(primary, task_id), _serialize(record))
        log = decision_log_path(primary, task_id)
        if not log.exists():
            log.write_text(f"# Decision log: {task_id}\n\nGoal: {goal}\n")
    return record


def deliveries(primary: Path, record: dict) -> list[dict]:
    """The delivery commits of the task's workspace on its branch, oldest first, as Delivery's
    reader recognises them by subject and trailers alone; ``verified`` adds whether each holds
    what its bundle says was validated."""
    head = _git(
        primary, "rev-parse", "--verify", "--quiet", record["branch"], check=False
    ).stdout.strip()
    if not head:
        return []
    return delivery_commits(primary, record["base_commit"], head, record["id"])


def verified(primary: Path, delivery: dict) -> dict:
    """The delivery commit with ``mismatches``: how it disagrees with its evidence bundle by
    Delivery's own check, empty when it verifies."""
    return {**delivery, "mismatches": delivery_mismatches(primary, delivery)}


def derived_state(primary: Path, record: dict, runs: list[dict] | None = None) -> str:
    """The task's state: merging, closed or failed as stored; otherwise delivered when its branch
    head is a delivery commit of its workspace that verifies against its bundle and its worktree
    is clean, active when its workspace has runs or its branch moved past the base, and open
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
        runs = workspace_runs(primary / ".concorde", record["id"])
    if runs or (head and head != record["base_commit"]) or _dirty(worktree):
        return "active"
    return "open"


def list_tasks(primary: Path, state: str | None = None) -> list[dict]:
    """Every task record with its derived state, oldest first; ``state`` filters on it."""
    records = _records(primary)
    records.sort(key=lambda item: (item["created_at"], item["id"]))
    for record in records:
        record["state"] = derived_state(primary, record)
    return [item for item in records if state is None or item["state"] == state]


def show_task(primary: Path, task_id: str) -> dict:
    """The record with its derived state, the workspace's runs and delivery commits, each with
    how it disagrees with its bundle, who holds the workspace lock, and the decision log's
    path."""
    record = load_task(primary, task_id)
    runs = workspace_runs(primary / ".concorde", task_id)
    record["state"] = derived_state(primary, record, runs)
    return {
        "record": record,
        "runs": runs,
        "deliveries": [verified(primary, item) for item in deliveries(primary, record)],
        "busy": lock_holder(primary / ".concorde", task_id),
        "decision_log": decision_log_path(primary, task_id).as_posix(),
    }


def _dirty(worktree: Path) -> bool:
    if not worktree.exists():
        return False
    status = _git(worktree, "status", "--porcelain", check=False).stdout
    return bool(status.strip())


def _dirty_detail(worktree: Path) -> str:
    lines = _git(worktree, "status", "--porcelain", check=False).stdout.splitlines()
    shown = ", ".join(line[3:] for line in lines[:20])
    more = f" and {len(lines) - 20} more" if len(lines) > 20 else ""
    return f"{worktree} has {len(lines)} uncommitted change(s): {shown}{more}"


def escalate(primary: Path, task_id: str, error: dict) -> dict:
    """Record an escalated error link in the task record and its decision log.

    A ``task-session`` link escalates to the main agent, a ``main-agent`` link to the developer.
    """
    from ..errors import render

    stamp = now()
    receiver = "main agent" if error["level"] == "task-session" else "developer"

    def change(record):
        record.setdefault("escalations", []).append({"at": stamp, "error": error})
        return record

    record = update(primary, task_id, change)
    path = decision_log_path(primary, task_id)
    try:
        with path.open("a", encoding="utf-8") as stream:
            stream.write(
                f"\n## Escalated to the {receiver}, {stamp}\n\n{render(error)}\n\n"
                f"```json\n{json.dumps(error, indent=2, ensure_ascii=False)}\n```\n"
            )
    except OSError as failure:
        number = len(record["escalations"])
        raise TaskError(
            "decision_log_failed",
            f"the escalation was written to the record of task {task_id} as escalation "
            f"{number} (`concorde task show {task_id}` prints it under record.escalations), "
            f"but appending it to the decision log {path} failed afterwards: {failure}; "
            "escalating again would record it twice, so once the log is writable append it "
            f"there by hand under the heading `## Escalated to the {receiver}, {stamp}`; the "
            f"escalated chain:\n{render(error)}",
        ) from failure
    return record


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
            f"the head {head} of {record['branch']} of task {task_id} has the subject and "
            f"trailers of a delivery commit of its workspace but does not verify against its "
            f"evidence bundle {delivered[-1]['bundle']}, so it may not hold what was validated: "
            + "; ".join(mismatches),
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
    ``note`` and the error chains that caused it in ``errors``, or none when no error did.
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
    load_task(primary, task_id)
    started = time.monotonic()
    with task_workspace_locked(primary, task_id, "close", wait):
        remaining = max(0.0, wait - (time.monotonic() - started))
        with merge_lock(primary, "close", task_id, remaining):
            unfinished = unfinished_merge(primary)
            if unfinished is not None:
                raise incomplete_merge(primary, unfinished)
            return close_locked(
                primary, task_id, outcome, note=note, errors=errors, force=force
            )


def close_locked(
    primary: Path,
    task_id: str,
    outcome: str,
    *,
    note: str | None = None,
    errors: list[dict] | None = None,
    force: bool = False,
    again: str | None = None,
) -> dict:
    """``close_task`` for a caller already holding the merge lock and the workspace lock.

    Removing the worktree, writing the record and appending to the decision log cannot be one
    transaction, so a refusal after one of them says what this close did and that ``again``
    (by default the same close) finishes it; the same close of a task whose record is closed
    but whose decision log lacks its closing appends it.
    """
    errors = list(errors or [])
    again = (
        again or f"`concorde task close {task_id} --{outcome}` with the same options"
    )
    record = load_task(primary, task_id)
    worktree = Path(record["worktree"])
    if record["state"] in ENDED:
        ended = record.get("closed") or {}
        if ended.get("outcome") == outcome and not _closing_logged(
            primary, task_id, ended
        ):
            _log_closing(primary, task_id, ended)
            return record
        raise TaskError(
            "invalid_transition", f"task {task_id} is already {record['state']}"
        )
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
    submodules = worktree.exists() and (worktree / ".gitmodules").exists()
    if submodules:
        # Git removes a worktree that holds submodule repositories only with --force. Deinit
        # first: it refuses local changes in a submodule unless the close is forced, so the
        # forced removal below discards nothing the checks above would have kept.
        arguments = ["submodule", "deinit", "--all", *(["--force"] if force else [])]
        result = _git(worktree, *arguments, check=False)
        if result.returncode != 0:
            raise TaskError(
                "worktree_failed",
                f"git {' '.join(arguments)} in {worktree} exited {result.returncode}: "
                f"{result.stderr.strip()}; Git may have deinitialized the submodules before "
                f"the one it stopped at (`git submodule update --init` in {worktree} restores "
                f"them), the worktree stays and the record of task {task_id} is unchanged; "
                f"once the cause is fixed, {again} finishes the close",
            )
    if worktree.exists():
        arguments = ["worktree", "remove", str(worktree)]
        if force or submodules:
            arguments.insert(2, "--force")
        result = _git(primary, *arguments, check=False)
        if result.returncode != 0:
            done = (
                f"this close deinitialized the submodules of {worktree} "
                f"(`git submodule update --init` there restores them)"
                if submodules
                else "this close changed nothing before it"
            )
            raise TaskError(
                "worktree_failed",
                f"git {' '.join(arguments)} exited {result.returncode}: "
                f"{result.stderr.strip()}; {done}, the worktree is as Git left it and the "
                f"record of task {task_id} is unchanged; once the cause is fixed, {again} "
                "finishes the close",
            )
        removed = True
    primary_head = _git(primary, "rev-parse", "HEAD").stdout.strip()

    stamp = now()
    state = "failed" if outcome == "failed" else "closed"

    def change(record):
        record["state"] = state
        record["merging"] = None
        record["closed"] = {
            "state": state,
            "outcome": outcome,
            "note": note.strip() if note and note.strip() else None,
            "errors": errors,
            "at": stamp,
            "primary_commit": primary_head,
            "worktree_removed": removed,
        }
        return record

    try:
        closed = update(primary, task_id, change)
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
    return closed


def _closing_heading(closed: dict) -> str:
    return f"## Closed: {closed['outcome']}, {closed['at']}"


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
    from ..errors import render

    lines = [f"\n{_closing_heading(closed)}\n"]
    if closed["note"]:
        lines.append(f"\n{closed['note']}\n")
    for error in closed["errors"]:
        lines.append(
            f"\n{render(error)}\n\n"
            f"```json\n{json.dumps(error, indent=2, ensure_ascii=False)}\n```\n"
        )
    path = decision_log_path(primary, task_id)
    try:
        with path.open("a", encoding="utf-8") as stream:
            stream.write("".join(lines))
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
    "decision_log_path",
    "deliveries",
    "derived_state",
    "end_merge",
    "escalate",
    "guard_merges",
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
    "show_task",
    "task_workspace_locked",
    "unfinished_merge",
    "unwritten_decision_log",
    "verified",
]
