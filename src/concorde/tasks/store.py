"""The Task store: task records and decision logs in the primary worktree, and the task commands.

A task is a branch ``concorde/<id>``, a worktree checked out on it, a record
``.concorde/tasks/<id>.json`` and a decision log ``.concorde/tasks/<id>.decisions.md``, all owned
by the primary worktree. Only this module writes records. Every change is one read, a check of
its preconditions and one atomic write bound to the bytes read; a concurrent change is retried
and reported as ``record_conflict`` after three attempts.
"""

from __future__ import annotations

import fcntl
import json
import os
import re
import subprocess
import tempfile
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from ..harness.models import CONFIG, inherit

TASK_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,47}$")
STATES = ("open", "active", "delivered", "closed", "failed")
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
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


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
    """Apply ``change(record) -> record`` bound to the bytes read; retry concurrent changes."""
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
            _write(path, _serialize(record))
        return record
    raise TaskError(
        "record_conflict", f"task {task_id} changed concurrently {ATTEMPTS} times"
    )


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
        if record["state"] not in ("open", "active", "delivered"):
            raise TaskError(
                "task_closed",
                f"task {task_id} is {record['state']}; a session works only in an open task",
            )
        record.setdefault("sessions", []).append(session)
        return record

    return update(primary, task_id, change)


def registered(root: Path, modules: list[str]) -> None:
    from ..spec.repository import SpecRepository
    from ..spec.repository_base import SpecError

    try:
        repository = SpecRepository(root)
    except (SpecError, OSError, ValueError) as error:
        detail = error.describe() if isinstance(error, SpecError) else str(error)
        raise TaskError(
            "specs_unloadable", f"the Specs of {root} cannot be loaded: {detail}"
        ) from error
    unknown = sorted(item for item in modules if item not in repository.modules)
    if unknown:
        raise TaskError(
            "unknown_module",
            f"{', '.join(unknown)} {'is' if len(unknown) == 1 else 'are'} not registered in "
            f"{root} (registered: {', '.join(sorted(repository.modules))})",
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
        "runs": [],
        "deliveries": [],
        "escalations": [],
        "sessions": [],
        "workflow": None,
        "closed": None,
    }
    with _locked(primary):
        _write(record_path(primary, task_id), _serialize(record))
        log = decision_log_path(primary, task_id)
        if not log.exists():
            log.write_text(f"# Decision log: {task_id}\n\nGoal: {goal}\n")
    return record


def list_tasks(primary: Path, state: str | None = None) -> list[dict]:
    directory = tasks_directory(primary)
    records = []
    for path in sorted(directory.glob("*.json")) if directory.is_dir() else []:
        try:
            records.append(json.loads(path.read_text()))
        except (OSError, ValueError) as error:
            raise TaskError(
                "record_unreadable", f"the task record {path} cannot be read: {error}"
            ) from error
    records.sort(key=lambda item: (item["created_at"], item["id"]))
    return [item for item in records if state is None or item["state"] == state]


def show_task(primary: Path, task_id: str) -> dict:
    record = load_task(primary, task_id)
    return {
        "record": record,
        "decision_log": decision_log_path(primary, task_id).as_posix(),
    }


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def begin_run(
    primary: Path,
    task_id: str,
    run_id: str,
    operation: str,
    modules: list[str],
    writes: bool,
    host_pid: int,
    *,
    check_modules: bool = True,
) -> dict:
    """Begin a run; ``check_modules=False`` leaves the Module check to the Operation itself."""
    record = load_task(primary, task_id)
    if record["state"] in ENDED:
        raise TaskError("task_closed", f"task {task_id} is {record['state']}")
    if check_modules:
        registered(Path(record["worktree"]), modules)

    def change(record):
        if record["state"] in ENDED:
            raise TaskError("task_closed", f"task {task_id} is {record['state']}")
        for run in record["runs"]:
            if run["status"] == "running":
                if _alive(run["host_pid"]):
                    raise TaskError(
                        "task_busy", f"run {run['run_id']} of task {task_id} is running"
                    )
                run["status"], run["finished_at"] = "interrupted", now()
        record["runs"].append(
            {
                "run_id": run_id,
                "operation": operation,
                "modules": list(modules),
                "writes": bool(writes),
                "status": "running",
                "host_pid": host_pid,
                "started_at": now(),
                "finished_at": None,
            }
        )
        for module in modules:
            if module not in record["modules"]:
                record["modules"].append(module)
        if record["state"] == "open" or (record["state"] == "delivered" and writes):
            record["state"] = "active"
        return record

    return update(primary, task_id, change)


def _running(record: dict, run_id: str) -> dict:
    for run in record["runs"]:
        if run["run_id"] == run_id and run["status"] == "running":
            return run
    raise TaskError("invalid_transition", f"run {run_id} is not running")


def finish_run(primary: Path, task_id: str, run_id: str, status: str) -> dict:
    def change(record):
        run = _running(record, run_id)
        run["status"], run["finished_at"] = status, now()
        return record

    return update(primary, task_id, change)


def record_delivery(
    primary: Path,
    task_id: str,
    run_id: str,
    commit: str,
    bundle: str,
    readiness_run: str,
) -> dict:
    def change(record):
        _running(record, run_id)
        if record["state"] not in ("active", "delivered"):
            raise TaskError(
                "invalid_transition",
                f"a task in state {record['state']} cannot be delivered",
            )
        record["deliveries"].append(
            {
                "run_id": run_id,
                "commit": commit,
                "bundle": bundle,
                "readiness_run": readiness_run,
                "at": now(),
            }
        )
        record["state"] = "delivered"
        return record

    return update(primary, task_id, change)


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
    with decision_log_path(primary, task_id).open("a", encoding="utf-8") as stream:
        stream.write(
            f"\n## Escalated to the {receiver}, {stamp}\n\n{render(error)}\n\n"
            f"```json\n{json.dumps(error, indent=2, ensure_ascii=False)}\n```\n"
        )
    return record


def base_key(key: str) -> str:
    """A step key without its restart generation and answers digest."""
    return key.split("@", 1)[0].split("#", 1)[0]


def current_steps(record: dict) -> list[dict]:
    """The workflow steps of a task record that no later rerun superseded, in record order."""
    workflow = record.get("workflow") or {}
    return [step for step in workflow.get("steps", []) if not step.get("superseded")]


def check_workflow_step(record: dict, workflow: str, key: str, operation: str) -> None:
    """Refuse a workflow step the task cannot take, before anything is started for it.

    ``task_closed`` for an ended task, ``workflow_conflict`` when the record names another
    workflow and ``step_conflict`` when the key is recorded for another Operation.
    """
    task_id = record["id"]
    if record["state"] in ENDED:
        raise TaskError(
            "task_closed",
            f"task {task_id} is {record['state']}; no workflow step is recorded for it",
        )
    current = record.get("workflow")
    if current is not None and current["name"] != workflow:
        raise TaskError(
            "workflow_conflict",
            f"task {task_id} runs the workflow {current['name']}; a step of {workflow} is "
            "refused, since a task runs at most one workflow",
        )
    for step in (current or {}).get("steps", []):
        if step["key"] == key and step["operation"] != operation:
            raise TaskError(
                "step_conflict",
                f"step key {key} of task {task_id} is recorded for {step['operation']} "
                f"(run {step['run_id']}), not {operation}",
            )


def record_workflow_step(
    primary: Path,
    task_id: str,
    workflow: str,
    key: str,
    operation: str,
    run_id: str | None,
    mode: str,
    answers: str | None,
    error: dict | None = None,
) -> dict:
    """Record one workflow step: name the workflow on the first step, supersede, append.

    When a current step has the same base key, it and every step recorded after it are marked
    superseded, so a retried or answered step makes the procedure's later steps run again.
    Refused as ``check_workflow_step`` refuses.
    """
    stamp = now()

    def change(record):
        check_workflow_step(record, workflow, key, operation)
        current = record.get("workflow") or {
            "name": workflow,
            "steps": [],
            "reports": [],
        }
        steps = current["steps"]
        earlier = next(
            (
                index
                for index, step in enumerate(steps)
                if not step.get("superseded") and base_key(step["key"]) == base_key(key)
            ),
            None,
        )
        if earlier is not None:
            for step in steps[earlier:]:
                step["superseded"] = True
        steps.append(
            {
                "key": key,
                "operation": operation,
                "run_id": run_id,
                "mode": mode,
                "answers": answers,
                "error": error,
                "superseded": False,
                "at": stamp,
            }
        )
        record["workflow"] = current
        return record

    return update(primary, task_id, change)


def record_workflow_report(
    primary: Path, task_id: str, status: str, path: str, log_text: str
) -> dict:
    """Append a workflow report to the task record and its text to the decision log."""
    stamp = now()

    def change(record):
        current = record.get("workflow")
        if current is None:
            raise TaskError(
                "no_workflow",
                f"task {task_id} names no workflow, so there is no workflow report to record",
            )
        current["reports"].append({"status": status, "path": path, "at": stamp})
        return record

    record = update(primary, task_id, change)
    with decision_log_path(primary, task_id).open("a", encoding="utf-8") as stream:
        stream.write(log_text)
    return record


def mergeable(primary: Path, task_id: str) -> tuple[dict, str]:
    """The record and branch head of a task ``close --merged`` accepts once the head is merged."""
    record = load_task(primary, task_id)
    if record["state"] in ENDED:
        raise TaskError(
            "invalid_transition", f"task {task_id} is already {record['state']}"
        )
    if record["state"] != "delivered" or not record["deliveries"]:
        raise TaskError(
            "not_merged",
            f"task {task_id} is {record['state']} with {len(record['deliveries'])} "
            "delivery(ies); only a delivered task can be closed as merged",
        )
    head = _git(primary, "rev-parse", record["branch"]).stdout.strip()
    if head != record["deliveries"][-1]["commit"]:
        raise TaskError(
            "not_merged",
            f"{record['branch']} is at {head}, not at its last delivery commit "
            f"{record['deliveries'][-1]['commit']}; deliver again, or close it completed "
            "or failed",
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
    if force and outcome == "merged":
        problems.append("--force applies only to closing without a merge")
    if problems:
        raise TaskError("invalid_input", "; ".join(problems))
    with merge_lock(primary, "close", task_id, wait):
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
) -> dict:
    """``close_task`` for a caller that already holds the merge lock."""
    errors = list(errors or [])
    record = load_task(primary, task_id)
    worktree = Path(record["worktree"])
    if record["state"] in ENDED:
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
                f"{result.stderr.strip()}",
            )
    if worktree.exists():
        arguments = ["worktree", "remove", str(worktree)]
        if force or submodules:
            arguments.insert(2, "--force")
        result = _git(primary, *arguments, check=False)
        if result.returncode != 0:
            raise TaskError(
                "worktree_failed",
                f"git {' '.join(arguments)} exited {result.returncode}: "
                f"{result.stderr.strip()}",
            )
        removed = True
    primary_head = _git(primary, "rev-parse", "HEAD").stdout.strip()

    stamp = now()
    state = "failed" if outcome == "failed" else "closed"

    def change(record):
        record["state"] = state
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

    closed = update(primary, task_id, change)
    _log_closing(primary, task_id, closed["closed"])
    return closed


def _log_closing(primary: Path, task_id: str, closed: dict) -> None:
    """Append how the task ended, with any error chains rendered and as JSON."""
    from ..errors import render

    lines = [f"\n## Closed: {closed['outcome']}, {closed['at']}\n"]
    if closed["note"]:
        lines.append(f"\n{closed['note']}\n")
    for error in closed["errors"]:
        lines.append(
            f"\n{render(error)}\n\n"
            f"```json\n{json.dumps(error, indent=2, ensure_ascii=False)}\n```\n"
        )
    with decision_log_path(primary, task_id).open("a", encoding="utf-8") as stream:
        stream.write("".join(lines))


__all__ = [
    "ENDED",
    "MERGE_WAIT",
    "OUTCOMES",
    "TaskError",
    "begin_run",
    "close_locked",
    "close_task",
    "decision_log_path",
    "escalate",
    "finish_run",
    "list_tasks",
    "load_task",
    "merge_lock",
    "merge_lock_path",
    "mergeable",
    "open_task",
    "primary_of",
    "record_delivery",
    "record_session",
    "record_workflow_report",
    "base_key",
    "check_workflow_step",
    "current_steps",
    "record_workflow_step",
    "require_primary",
    "show_task",
]
