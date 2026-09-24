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
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

TASK_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,47}$")
STATES = ("open", "active", "delivered", "merged", "abandoned")
ATTEMPTS = 3


class TaskError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _git(cwd: Path, *arguments: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *arguments], cwd=cwd, check=check, capture_output=True, text=True
    )


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


def load_task(primary: Path, task_id: str) -> dict:
    path = record_path(primary, task_id)
    if not TASK_ID.match(task_id or "") or not path.is_file():
        raise TaskError("unknown_task", f"no task {task_id!r}")
    return json.loads(path.read_text())


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
            raise TaskError("unknown_task", f"no task {task_id!r}")
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


def _registered(root: Path, modules: list[str]) -> None:
    from ..spec.repository import SpecRepository
    from ..spec.repository_base import SpecError

    try:
        repository = SpecRepository(root)
    except (SpecError, OSError, ValueError) as error:
        raise TaskError("specs_unloadable", str(error)) from error
    unknown = sorted(item for item in modules if item not in repository.modules)
    if unknown:
        raise TaskError("unknown_module", f"unregistered Module: {', '.join(unknown)}")


def open_task(
    primary: Path,
    task_id: str,
    goal: str,
    modules: list[str],
    *,
    base: str | None = None,
    path: Path | None = None,
) -> dict:
    """Create the branch, the worktree, the record and the decision log of a new task."""
    primary = require_primary(primary)
    if not TASK_ID.match(task_id or ""):
        raise TaskError("invalid_task_id", f"invalid task identity: {task_id!r}")
    if not goal or not modules or len(set(modules)) != len(modules):
        raise TaskError("invalid_input", "a task needs a goal and distinct Modules")
    if record_path(primary, task_id).exists():
        raise TaskError("task_exists", f"task {task_id} already exists")
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
        raise TaskError("branch_exists", f"branch {branch} already exists")
    worktree = Path(
        os.path.abspath(path or primary.parent / f"{primary.name}.tasks" / task_id)
    )
    if worktree.exists():
        raise TaskError("path_exists", f"{worktree} already exists")
    _registered(primary, modules)
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
        raise TaskError("worktree_failed", created.stderr.strip())
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
    records = [
        json.loads(path.read_text())
        for path in sorted(directory.glob("*.json"))
        if directory.is_dir()
    ]
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
    if record["state"] in ("merged", "abandoned"):
        raise TaskError("task_closed", f"task {task_id} is {record['state']}")
    if check_modules:
        _registered(Path(record["worktree"]), modules)

    def change(record):
        if record["state"] in ("merged", "abandoned"):
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


def close_task(
    primary: Path,
    task_id: str,
    *,
    merged: bool = False,
    abandoned: bool = False,
    force: bool = False,
) -> dict:
    primary = require_primary(primary)
    if merged == abandoned:
        raise TaskError(
            "invalid_input", "close needs exactly one of --merged or --abandoned"
        )
    record = load_task(primary, task_id)
    worktree = Path(record["worktree"])
    if record["state"] in ("merged", "abandoned"):
        raise TaskError(
            "invalid_transition", f"task {task_id} is already {record['state']}"
        )
    if merged:
        if record["state"] != "delivered" or not record["deliveries"]:
            raise TaskError("not_merged", f"task {task_id} is not delivered")
        head = _git(primary, "rev-parse", record["branch"]).stdout.strip()
        if head != record["deliveries"][-1]["commit"]:
            raise TaskError(
                "not_merged", "the task branch moved after its last delivery"
            )
        contained = _git(
            primary, "merge-base", "--is-ancestor", head, "HEAD", check=False
        )
        if contained.returncode != 0:
            raise TaskError(
                "not_merged", f"{head} is not contained in the primary branch"
            )
        if _dirty(worktree):
            raise TaskError("dirty_worktree", f"{worktree} has uncommitted changes")
    elif _dirty(worktree) and not force:
        raise TaskError("dirty_worktree", f"{worktree} has uncommitted changes")
    removed = False
    if worktree.exists():
        arguments = ["worktree", "remove", str(worktree)]
        if force:
            arguments.insert(2, "--force")
        result = _git(primary, *arguments, check=False)
        if result.returncode != 0:
            raise TaskError("worktree_failed", result.stderr.strip())
        removed = True
    primary_head = _git(primary, "rev-parse", "HEAD").stdout.strip()

    def change(record):
        record["state"] = "merged" if merged else "abandoned"
        record["closed"] = {
            "state": record["state"],
            "at": now(),
            "primary_commit": primary_head,
            "worktree_removed": removed,
        }
        return record

    return update(primary, task_id, change)


__all__ = [
    "TaskError",
    "begin_run",
    "close_task",
    "decision_log_path",
    "finish_run",
    "list_tasks",
    "load_task",
    "open_task",
    "primary_of",
    "record_delivery",
    "require_primary",
    "show_task",
]
