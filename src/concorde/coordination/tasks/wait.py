"""``concorde task wait``: block until a task reaches a state, a run ends or a lock is released.

Nothing here polls. A lock or run wait blocks on the lock itself (``locks.wait_released``), which
the kernel releases however its holder ends. A task wait learns of every new holder of the task's
workspace lock from the kernel (``watch.Changes``), blocks on the lock until that holder lets it
go, and reads the task's state again: every change of a task to ``delivered``, ``merging``,
``closed`` or ``failed`` is made while that lock is held, by a delivery run, a merge or a close,
so those four are the states a task wait admits. A rebind wait learns of every write of the task's
record from the kernel (``watch.Changes`` on the task's folder, which also reports the folder
moving to the history) and reads the record again. A merge wait blocks on the task's merge attempt
lock, which ``concorde task merge`` holds until its output is complete and removes then, so it
returns after the merge's last word even when the close removed the workspace lock long before.
The project MCP server runs the same waits in a thread for ``register_wait``; this command is
their form for background Bash.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from ...kernel.tracing import layout, locks, reader
from ...kernel.tracing import node as trace
from ...kernel.tracing.watch import Changes, WatchError
from . import store
from .store import TaskError

# The states a task reaches only while its workspace lock is held, and so the ones a wait sees.
AWAITABLE = ("delivered", "merging", "closed", "failed")
LOCKS = ("merge", "workspace")


def lock_path(primary: Path, kind: str, task_id: str | None = None) -> Path:
    """The merge lock, or the workspace lock of ``task_id``, of the primary worktree."""
    if kind == "merge":
        return store.merge_lock_path(primary)
    if kind == "workspace":
        if not task_id:
            raise TaskError(
                "invalid_input", "a wait for a workspace lock names its task"
            )
        return layout.lock_file(store.concorde(primary), "workspace", task_id)
    raise TaskError("invalid_input", f"the lock {kind!r} is none of {', '.join(LOCKS)}")


def _remaining(deadline: float | None) -> float | None:
    return None if deadline is None else max(0.0, deadline - time.monotonic())


def _timeout(what: str, timeout: float | None) -> TaskError:
    return TaskError(
        "wait_timeout",
        f"{what} did not happen within {timeout:g} s; nothing was changed, and the same wait "
        "may be started again",
    )


def _deadline(timeout: float | None) -> float | None:
    if timeout is not None and timeout < 0:
        raise TaskError("invalid_input", f"--timeout {timeout:g} is negative")
    return None if timeout is None else time.monotonic() + timeout


def check_until(until: list[str]) -> list[str]:
    wrong = [state for state in until if state not in AWAITABLE]
    if not until or wrong:
        raise TaskError(
            "invalid_input",
            f"a task wait names states among {', '.join(AWAITABLE)}, the ones a task reaches "
            f"while its workspace lock is held; got {', '.join(until) or 'none'}",
        )
    return list(dict.fromkeys(until))


def task_state(primary: Path, task_id: str) -> tuple[dict, str]:
    record, _ = store.load_any(primary, task_id)
    return record, store.derived_state(primary, record)


def reached(primary: Path, task_id: str, until: list[str]) -> dict | None:
    """The wait's answer when the task is in one of ``until`` now, else None; ``wait_unreachable``
    when it ended in another state."""
    record, state = task_state(primary, task_id)
    if state in until:
        return {"task": task_id, "state": state}
    if record["state"] in store.ENDED:
        raise TaskError(
            "wait_unreachable",
            f"task {task_id} ended {state} and will never be {' or '.join(until)}",
        )
    return None


def wait_task(
    primary: Path, task_id: str, until: list[str], timeout: float | None = None
) -> dict:
    """Block until the task's derived state is one of ``until``."""
    until = check_until(until)
    deadline = _deadline(timeout)
    started = time.monotonic()
    path = lock_path(primary, "workspace", task_id)
    try:
        changes = Changes(path.parent, {path.name})
    except WatchError as error:
        raise TaskError(
            "wait_failed", f"the wait for task {task_id} cannot watch its lock: {error}"
        ) from error
    with changes:
        while True:
            found = reached(primary, task_id, until)
            if found is not None:
                return {**found, "waited_seconds": round(time.monotonic() - started, 3)}
            if deadline is not None and time.monotonic() >= deadline:
                raise _timeout(f"task {task_id} becoming {' or '.join(until)}", timeout)
            if locks.held(path):
                locks.wait_released(path, _remaining(deadline))
            else:
                changes.wait(_remaining(deadline))


def rebound(primary: Path, task_id: str, former: str) -> dict | None:
    """The wait's answer when the task's main agent's session is no longer ``former``, else
    None; ``wait_unreachable`` when the task ended."""
    record, _ = store.load_any(primary, task_id)
    if record["state"] in store.ENDED:
        raise TaskError(
            "wait_unreachable",
            f"task {task_id} ended {record['state']}, and its main agent's session will never "
            f"change from {record['main'] or 'none'}",
        )
    if record["main"] != former:
        return {"task": task_id, "main": record["main"], "former": former}
    return None


def wait_rebound(
    primary: Path, task_id: str, former: str, timeout: float | None = None
) -> dict:
    """Block until the task's record names a main agent's session other than ``former``."""
    former = (former or "").strip()
    if not former:
        raise TaskError(
            "invalid_input",
            "--rebound names the main agent's session to wait away from",
        )
    deadline = _deadline(timeout)
    started = time.monotonic()
    # Answered before watching too, so that the watch never makes the folder of a task that
    # already moved to the history.
    found = rebound(primary, task_id, former)
    if found is not None:
        return {**found, "waited_seconds": 0.0}
    folder = store.task_folder(primary, task_id)
    try:
        changes = Changes(folder, {store.RECORD})
    except WatchError as error:
        raise TaskError(
            "wait_failed",
            f"the wait for task {task_id} cannot watch its record: {error}",
        ) from error
    with changes:
        while True:
            found = rebound(primary, task_id, former)
            if found is not None:
                return {**found, "waited_seconds": round(time.monotonic() - started, 3)}
            if deadline is not None and time.monotonic() >= deadline:
                raise _timeout(
                    f"task {task_id} naming a main agent's session other than {former}",
                    timeout,
                )
            changes.wait(_remaining(deadline))


def locate_run(here: Path, run_id: str) -> tuple[Path, Path]:
    """The folder of ``run_id`` and the ``.concorde`` whose ``locks/`` holds its run lock."""
    try:
        return reader.locate(run_id, reader.roots(here))
    except reader.ReadError as error:
        raise TaskError("unknown_run", str(error)) from error


def run_answer(here: Path, run_id: str) -> dict | None:
    """The run's end, ``{"run", "status", "result"}``, once its runner holds no run lock; None
    while it runs."""
    folder, concorde = locate_run(here, run_id)
    if locks.held(layout.lock_file(concorde, "run", run_id)):
        return None
    folder, _ = locate_run(here, run_id)
    try:
        result = json.loads((folder / layout.RESULT).read_text())
    except (OSError, ValueError):
        result = None
    status = result.get("status") if isinstance(result, dict) else "lost"
    return {
        "run": run_id,
        "status": status,
        "result": (folder / layout.RESULT).as_posix() if result is not None else None,
    }


def wait_run(here: Path, run_id: str, timeout: float | None = None) -> dict:
    """Block until the runner of ``run_id`` let its run lock go, and answer how the run ended."""
    deadline = _deadline(timeout)
    started = time.monotonic()
    _, concorde = locate_run(here, run_id)
    path = layout.lock_file(concorde, "run", run_id)
    while True:
        found = run_answer(here, run_id)
        if found is not None:
            return {**found, "waited_seconds": round(time.monotonic() - started, 3)}
        if deadline is not None and time.monotonic() >= deadline:
            raise _timeout(f"the end of run {run_id}", timeout)
        locks.wait_released(path, _remaining(deadline))


def lock_answer(primary: Path, kind: str, task_id: str | None) -> dict:
    path = lock_path(primary, kind, task_id)
    return {
        "lock": kind,
        "task": task_id,
        "path": path.as_posix(),
        "holder": locks.entry(path),
    }


def wait_lock(
    primary: Path, kind: str, task_id: str | None = None, timeout: float | None = None
) -> dict:
    """Block until nobody holds the lock; answer who held it when the wait began."""
    deadline = _deadline(timeout)
    started = time.monotonic()
    answer = lock_answer(primary, kind, task_id)
    path = Path(answer.pop("path"))
    held = answer.pop("holder")
    if held is not None and not locks.wait_released(path, _remaining(deadline)):
        raise _timeout(f"the release of {path}", timeout)
    return {
        **answer,
        "released": True,
        "held_by": held,
        "waited_seconds": round(time.monotonic() - started, 3),
    }


def merge_answer(primary: Path, task_id: str) -> dict:
    """The task's latest merge attempt, wherever the task's folder is now: its node's folder,
    status and outcome and the files of the merge's output, or None for each when it has none."""
    _, folder = store.load_any(primary, task_id)
    merges = folder / "merges"
    numbers = sorted(
        int(item.name)
        for item in (merges.iterdir() if merges.is_dir() else [])
        if item.is_dir() and item.name.isdigit()
    )
    if not numbers:
        return {"task": task_id, "attempt": None}
    node = merges / str(numbers[-1])
    record = trace.read(node) or {}
    output, messages = node / "output.json", node / "messages.log"
    return {
        "task": task_id,
        "attempt": {
            "number": numbers[-1],
            "node": node.as_posix(),
            "status": record.get("status"),
            "outcome": record.get("outcome"),
            "output": output.as_posix() if output.is_file() else None,
            "messages": messages.as_posix() if messages.is_file() else None,
        },
    }


def wait_merge(primary: Path, task_id: str, timeout: float | None = None) -> dict:
    """Block until no ``concorde task merge`` of the task runs, and answer its latest attempt."""
    deadline = _deadline(timeout)
    started = time.monotonic()
    store.load_any(primary, task_id)
    path = store.attempt_lock_path(primary, task_id)
    held = locks.entry(path)
    if held is not None and not locks.wait_released(path, _remaining(deadline)):
        raise _timeout(f"the end of the merge of task {task_id}", timeout)
    return {
        **merge_answer(primary, task_id),
        "held_by": held,
        "waited_seconds": round(time.monotonic() - started, 3),
    }


__all__ = [
    "AWAITABLE",
    "LOCKS",
    "check_until",
    "lock_answer",
    "lock_path",
    "merge_answer",
    "reached",
    "rebound",
    "run_answer",
    "wait_lock",
    "wait_merge",
    "wait_rebound",
    "wait_run",
    "wait_task",
]
