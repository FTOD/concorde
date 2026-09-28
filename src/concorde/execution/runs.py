"""The run store: every Operation run and execution command run, and the workspace lock.

A run lives in ``<records>/runs/<run_id>/``: its progress file ``status.json``, kept current by the
process running it, and once it ended its run result ``result.json``. The runner holds the run lock,
an exclusive ``flock`` on the run directory itself, from before its first progress file until its
end, so whether a run still runs is read from that lock, which the kernel releases however the
runner ends; never from the recorded process identifier, which is only meaningful in the PID
namespace the runner ran in (a runner started in a sandboxed shell records a small number such as
2, naming an unrelated process on the host). ``<records>`` is the
binding's records directory, or an unbound worktree's own ``.concorde``. A bound run holds the
workspace lock ``<records>/runs/locks/<workspace>.lock`` for its whole life, so one workspace runs one
thing at a time; the kernel releases the lock however the run ends. The lock lies outside the
workspace, so a run that only reads the workspace leaves it untouched.
"""

from __future__ import annotations

import copy
import fcntl
import json
import os
import re
import secrets
import time
from collections.abc import Callable
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

from .. import errors

KINDS = ("operation", "command")
RUN_ID_PATTERN = "^r-[0-9]{8}T[0-9]{6}-[a-z_]+-[0-9a-f]{8}$"
RUN_ID = re.compile(RUN_ID_PATTERN)
# How often a run waiting with ``--wait`` tries the workspace lock again, inside its own process.
LOCK_POLL = 0.2

# contract.execution.run-result, version 2
RESULT_SCHEMA: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "kind",
        "name",
        "workspace",
        "commit",
        "modules",
        "run_id",
        "status",
        "summary",
        "output",
        "worker",
        "worker_runs",
        "host_evidence",
        "error",
        "started_at",
        "finished_at",
    ],
    "properties": {
        "kind": {"enum": list(KINDS)},
        "name": {"type": "string", "pattern": "^[a-z][a-z_-]*$"},
        "workspace": {"anyOf": [{"type": "null"}, {"type": "string", "minLength": 1}]},
        "commit": {
            "anyOf": [
                {"type": "null"},
                {"type": "string", "pattern": "^[0-9a-f]{40}([0-9a-f]{24})?$"},
            ]
        },
        "modules": {"type": "array", "items": {"type": "string", "minLength": 1}},
        "run_id": {"type": "string", "pattern": RUN_ID_PATTERN},
        "status": {"enum": ["ok", "blocked", "failed"]},
        "summary": {"type": "string", "minLength": 1},
        "output": {"anyOf": [{"type": "null"}, {"type": "object"}]},
        "worker": {"anyOf": [{"type": "null"}, {"type": "object"}]},
        "worker_runs": {"type": "array", "items": {"type": "string", "minLength": 1}},
        "host_evidence": {"type": "array", "items": {"$ref": "#/$defs/evidence"}},
        "error": {"anyOf": [{"type": "null"}, {"$ref": "#/$defs/error"}]},
        "started_at": {"type": "string", "minLength": 1},
        "finished_at": {"type": "string", "minLength": 1},
    },
    "$defs": copy.deepcopy(errors.DEFS),
}


class RunError(Exception):
    """A run the store refuses before it begins; ``code`` names why."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def now() -> str:
    """The UTC time with microseconds, so the runs of one workspace started within one second
    still sort in the order they started."""
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def id_name(name: str) -> str:
    """The name as it appears inside a run identity, where only ``[a-z_]`` is allowed."""
    return name.replace("-", "_")


def new_run_id(name: str) -> str:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
    return f"r-{stamp}-{id_name(name)}-{secrets.token_hex(4)}"


def runs_directory(records: Path) -> Path:
    return records / "runs"


def run_directory(records: Path, run_id: str) -> Path:
    return runs_directory(records) / run_id


def load_result(records: Path, run_id: str | None) -> dict | None:
    """The saved run result of ``run_id``, or None when it has none (yet) or it is unreadable."""
    if not run_id:
        return None
    try:
        return json.loads(
            (run_directory(records, run_id) / "result.json").read_text(encoding="utf-8")
        )
    except (OSError, ValueError):
        return None


def load_progress(records: Path, run_id: str) -> dict | None:
    try:
        return json.loads((run_directory(records, run_id) / "status.json").read_text())
    except (OSError, ValueError):
        return None


def pid_alive(pid: int) -> bool:
    """Whether a process lives, a zombie not counting; no process has a pid below 1."""
    if pid < 1:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    try:
        # A child that ended but was not reaped yet is not alive.
        stat = Path(f"/proc/{pid}/stat").read_text()
        return stat.rsplit(")", 1)[1].split()[0] != "Z"
    except (OSError, IndexError):
        return True


@contextmanager
def run_lock(run_dir: Path):
    """Hold the run lock of the run in ``run_dir`` for the life of the block.

    The descriptor is not inherited by the processes the runner starts, so a worker or check
    that outlives the runner never keeps its run alive.
    """
    descriptor = os.open(run_dir, os.O_RDONLY | os.O_DIRECTORY)
    try:
        # Blocking: a reader probing the lock holds it shared only for an instant.
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        yield
    finally:
        os.close(descriptor)


def runner_alive(run_dir: Path) -> bool:
    """Whether the runner of the run in ``run_dir`` still holds its run lock.

    Works from any PID namespace that sees the run store, since the lock belongs to the run
    directory, not to a process identifier.
    """
    try:
        descriptor = os.open(run_dir, os.O_RDONLY | os.O_DIRECTORY)
    except OSError:
        return False
    try:
        fcntl.flock(descriptor, fcntl.LOCK_SH | fcntl.LOCK_NB)
    except BlockingIOError:
        return True
    except OSError:
        return False
    finally:
        # Closing the descriptor releases the probe's own shared lock.
        os.close(descriptor)
    return False


def run_state(records: Path, run_id: str | None) -> str:
    """``finished``, ``running`` or ``lost`` for a run; ``refused`` without one.

    The result is written before the run lock is released, so a run with a result has ended;
    one without a result whose lock nobody holds ended without writing it.
    """
    if not run_id:
        return "refused"
    if load_result(records, run_id) is not None:
        return "finished"
    if runner_alive(run_directory(records, run_id)):
        return "running"
    # The run may have written its result between the two reads.
    return "finished" if load_result(records, run_id) is not None else "lost"


def workspace_runs(records: Path, workspace: str | None) -> list[dict]:
    """Every run recorded for ``workspace`` (None: unbound runs), oldest first.

    Each entry has the run identity, kind, name, Modules, status (``running``, ``lost`` or the
    result's status) and start time, from the result when there is one, else the progress file.
    """
    directory = runs_directory(records)
    found = []
    for path in sorted(directory.iterdir()) if directory.is_dir() else []:
        if not RUN_ID.match(path.name):
            continue
        result = load_result(records, path.name)
        source = result or load_progress(records, path.name)
        if not source or source.get("workspace") != workspace:
            continue
        status = result["status"] if result else run_state(records, path.name)
        found.append(
            {
                "run_id": path.name,
                "kind": source.get("kind"),
                "name": source.get("name"),
                "modules": list(source.get("modules") or []),
                "status": status,
                "started_at": source.get("started_at") or "",
                "finished_at": (result or {}).get("finished_at"),
            }
        )
    found.sort(key=lambda item: (item["started_at"], item["run_id"]))
    return found


def admit_inputs(
    records: Path, workspace: str | None, requested: list[str]
) -> dict[str, dict]:
    """The outputs of earlier ``ok`` runs of the same workspace (or of no workspace)."""
    admitted = {}
    for identity in requested:
        result = load_result(records, identity)
        if result is None:
            raise RunError(
                "input_not_admissible",
                f"--input {identity} has no readable result at "
                f"{run_directory(records, identity) / 'result.json'}",
            )
        if result.get("workspace") != workspace:
            owner = result.get("workspace") or "no workspace"
            here = workspace or "no workspace"
            raise RunError(
                "input_not_admissible",
                f"--input {identity} is a run of {owner}, not of {here}; a run admits only "
                "runs of its own workspace",
            )
        if result.get("status") != "ok":
            raise RunError(
                "input_not_admissible",
                f"--input {identity} ({result.get('name')}) ended {result.get('status')}; "
                "only an ok run's output is admitted",
            )
        admitted[identity] = {"name": result["name"], "output": result["output"]}
    return admitted


def lock_path(records: Path, workspace: str) -> Path:
    """The lock of ``workspace``, in the run store, which Git ignores like every run."""
    return runs_directory(records) / "locks" / f"{workspace}.lock"


@contextmanager
def workspace_lock(
    records: Path,
    workspace: str,
    holder: str,
    wait: float = 0.0,
    waiting: Callable[[str], None] | None = None,
):
    """Hold the lock of ``workspace`` or raise ``workspace_busy`` naming its holder.

    A busy lock is waited for up to ``wait`` seconds inside this process, so a caller that
    wants to queue behind the running run asks once instead of polling; ``waiting`` is told
    the holder when the wait begins.
    """
    path = lock_path(records, workspace)
    path.parent.mkdir(parents=True, exist_ok=True)
    stream = path.open("a+")
    try:
        started = time.monotonic()
        told = False
        while True:
            try:
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                stream.seek(0)
                current = stream.read().strip() or "an unnamed run"
                waited = time.monotonic() - started
                if waited >= wait:
                    after = f" after waiting {waited:.0f} s" if wait > 0 else ""
                    raise RunError(
                        "workspace_busy",
                        f"the workspace {workspace} is busy{after}: {current} holds its "
                        f"lock {path}; one workspace runs one Operation or command at a time",
                    ) from None
                if waiting is not None and not told:
                    waiting(current)
                    told = True
                time.sleep(LOCK_POLL)
        stream.seek(0)
        stream.truncate()
        stream.write(f"{holder} (process {os.getpid()})\n")
        stream.flush()
        try:
            yield
        finally:
            stream.seek(0)
            stream.truncate()
            stream.flush()
            fcntl.flock(stream, fcntl.LOCK_UN)
    finally:
        stream.close()


def lock_holder(records: Path, workspace: str) -> str | None:
    """Who holds the lock of ``workspace`` now, or None when nobody does."""
    path = lock_path(records, workspace)
    if not path.exists():
        return None
    with path.open("a+") as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_SH | fcntl.LOCK_NB)
        except BlockingIOError:
            stream.seek(0)
            return stream.read().strip() or "an unnamed run"
        fcntl.flock(stream, fcntl.LOCK_UN)
    return None


__all__ = [
    "KINDS",
    "RESULT_SCHEMA",
    "RUN_ID",
    "RunError",
    "admit_inputs",
    "load_progress",
    "load_result",
    "lock_holder",
    "lock_path",
    "new_run_id",
    "now",
    "pid_alive",
    "run_directory",
    "run_lock",
    "run_state",
    "runner_alive",
    "runs_directory",
    "workspace_lock",
    "workspace_runs",
]
