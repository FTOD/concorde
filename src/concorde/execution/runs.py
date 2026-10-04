"""The run store: where every Operation run and execution command run is kept, and its locks.

A run is a trace node of Tracing (``specs/concorde/tracing``): a folder holding its ``trace.json``,
its progress file ``status.json``, kept current by the process running it, and once it ended its run
result ``result.json``. A bound run's folder lies in the workspace folder its binding names, in
``runs/<run_id>/`` or, for a run a workflow step started, in ``run/`` of that step's node, once the
run holds the workspace lock; until then it lies in the lobby, ``lobby/<run_id>/`` of the binding's
``.concorde``, where a run refused before it held that lock stays, so that nothing of a run that has
not entered its workspace is ever written into the workspace folder, which a close moves. An unbound
run's folder lies in ``.concorde/unbound/<run_id>/`` of the worktree it started in. Its locks are files under
``locks/`` of the binding's ``.concorde``, or of that worktree's own: the runner holds the run lock
``locks/runs/<run_id>.lock`` from before its first progress file until after its result and removes
it as it exits, so whether a run still runs is read from that lock, which the kernel releases
however the runner ends, never from the recorded process identifier, which is only meaningful in
the PID namespace the runner ran in. A bound run holds the workspace lock
``locks/workspaces/<workspace>.lock`` for its whole life, so one workspace runs one thing at a time.
Neither lock lies in the workspace, so a run that only reads the workspace leaves it untouched.
"""

from __future__ import annotations

import copy
import json
import os
import re
import secrets
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from ..kernel import errors, locking
from ..kernel.refusal import KernelError
from ..kernel.schema import register, validate
from ..kernel.tracing.kinds import NodeKind, register as register_kinds
from ..kernel.tracing import layout, locks, reader, roots

KINDS = ("operation", "command")
RUN_ID_PATTERN = "^r-[0-9]{8}T[0-9]{6}-[a-z_]+-[0-9a-f]{8}$"
RUN_ID = re.compile(RUN_ID_PATTERN)
# The content type of a run's trace node, contract.execution.run-trace, version 1.
RUN_TRACE = "concorde-run-trace"
RUN_TRACE_SCHEMA: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "kind",
        "name",
        "argv",
        "exit_code",
        "steps",
        "worker_runs",
        "summary",
    ],
    "properties": {
        "kind": {"enum": list(KINDS)},
        "name": {"type": "string", "pattern": "^[a-z][a-z_-]*$"},
        "argv": {"type": "array", "items": {"type": "string"}},
        "exit_code": {"anyOf": [{"type": "null"}, {"type": "integer"}]},
        "steps": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["name", "started_at", "ended_at", "outcome"],
                "properties": {
                    "name": {"type": "string", "minLength": 1},
                    "started_at": {"type": "string", "minLength": 1},
                    "ended_at": {
                        "anyOf": [{"type": "null"}, {"type": "string", "minLength": 1}]
                    },
                    "outcome": {
                        "enum": ["running", "continue", "stop", "raised", "cancelled"]
                    },
                },
            },
        },
        "worker_runs": {"type": "array", "items": {"type": "string", "minLength": 1}},
        "summary": {"anyOf": [{"type": "null"}, {"type": "string", "minLength": 1}]},
    },
}
register(RUN_TRACE, 1, RUN_TRACE_SCHEMA)
register_kinds(
    NodeKind(
        "run",
        RUN_TRACE,
        (
            "workspace",
            "modules",
            "operation",
            "command",
            "commit",
            "base_commit",
            "concorde_commit",
            "protocol_version",
        ),
    ),
)

# The trace roots of the runs no workspace folder holds, relative to a ``.concorde``: the unbound
# runs of the worktree they started in, and the lobby of the ``.concorde`` a bound run's binding
# names, where it lies until it holds its workspace's lock and stays when it never does.
UNBOUND = "unbound"
LOBBY = "lobby"
TRACE_ROOTS = (
    roots.TraceRoot(
        name="unbound runs",
        folder=UNBOUND,
        place="worktree",
        kind="run",
        state="current",
        listed="unbound",
        period="unbound_days",
        alive_lock="run",
    ),
    roots.TraceRoot(
        name="lobby",
        folder=LOBBY,
        place="primary",
        kind="run",
        state="current",
        listed="never",
        period="unbound_days",
        alive_lock="run",
    ),
)
for _root in TRACE_ROOTS:
    roots.register(_root)

# contract.execution.run-result, version 4
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


@dataclass(frozen=True)
class Store:
    """Where the runs of one workspace, or the unbound runs of one worktree, are kept.

    ``workspace`` is the workspace folder a binding names, or None for the unbound runs kept in
    ``concorde``'s ``unbound/``; ``concorde`` is the ``.concorde`` whose ``locks/`` holds the locks.
    """

    concorde: Path
    workspace: Path | None = None

    def run_folder(self, run_id: str) -> Path:
        """Where a run started directly is kept."""
        if self.workspace is None:
            return Path(self.concorde) / UNBOUND / run_id
        return layout.run_folder(self.workspace, run_id)

    def lobby_folder(self, run_id: str) -> Path:
        """Where a bound run's node lies until it holds its workspace's lock."""
        return Path(self.concorde) / LOBBY / run_id

    def find(self, run_id: str) -> Path | None:
        """The folder of ``run_id``, started directly or by a workflow step, or still or for good
        in the lobby; None if unknown."""
        if not run_id or not RUN_ID.match(run_id):
            return None
        if self.workspace is None:
            folder = self.run_folder(run_id)
            return folder if folder.is_dir() else None
        found = reader.find_run(self.workspace, run_id)
        if found is not None:
            return found
        lobby = self.lobby_folder(run_id)
        if lobby.is_dir():
            return lobby
        # The run may have entered its workspace between the two reads.
        return reader.find_run(self.workspace, run_id)

    def folders(self) -> list[Path]:
        """Every run folder of the store."""
        if self.workspace is not None:
            return reader.workspace_runs(self.workspace)
        unbound = Path(self.concorde) / UNBOUND
        return (
            sorted(item for item in unbound.iterdir() if item.is_dir())
            if unbound.is_dir()
            else []
        )

    def run_lock(self, run_id: str) -> Path:
        return layout.lock_file(self.concorde, "run", run_id)

    def workspace_lock(self, workspace: str) -> Path:
        return locking.workspace_lock_path(self.concorde, workspace)


def store_of(root: Path, bound: dict | None) -> Store:
    """The store of a run started in the worktree ``root`` with the binding ``bound``."""
    if bound is None:
        return Store(root / layout.CONCORDE)
    return Store(Path(bound["concorde"]), Path(bound["traces"]))


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


def _json(path: Path) -> dict | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return value if isinstance(value, dict) else None


def load_result(store: Store, run_id: str | None) -> dict | None:
    """The saved run result of ``run_id``, or None when it has none (yet) or it is unreadable."""
    folder = store.find(run_id) if run_id else None
    return _json(folder / layout.RESULT) if folder else None


def result_path(store: Store, run_id: str) -> Path:
    """Where the result of ``run_id`` is or will be saved."""
    return (store.find(run_id) or store.run_folder(run_id)) / layout.RESULT


def load_progress(folder: Path) -> dict | None:
    return _json(Path(folder) / layout.PROGRESS)


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
def run_lock(store: Store, run_id: str, holder: str):
    """Hold the run lock of ``run_id`` for the life of the block, and remove it at its end.

    The descriptor is not inherited by the processes the runner starts, so a worker or check
    that outlives the runner never keeps its run alive.
    """
    with locks.hold(store.run_lock(run_id), holder, wait=None, remove=True):
        yield


def runner_alive(store: Store, run_id: str) -> bool:
    """Whether the runner of ``run_id`` still holds its run lock, from any PID namespace."""
    return locks.held(store.run_lock(run_id))


def run_state(store: Store, run_id: str | None) -> str:
    """``finished``, ``running`` or ``lost`` for a run; ``refused`` without one.

    The result is written before the run lock is released, so a run with a result has ended;
    one without a result whose lock nobody holds ended without writing it.
    """
    if not run_id:
        return "refused"
    if load_result(store, run_id) is not None:
        return "finished"
    if runner_alive(store, run_id):
        return "running"
    # The run may have written its result between the two reads.
    return "finished" if load_result(store, run_id) is not None else "lost"


def waiting_runs(store: Store, workspace: str | None) -> list[Path]:
    """The lobby folders of the runs of ``workspace`` whose runner still runs: the runs waiting
    for its lock. A run refused before it held the lock never entered the workspace and is not
    one of its runs; it is found by its identity."""
    if store.workspace is None or workspace is None:
        return []
    lobby = Path(store.concorde) / LOBBY
    try:
        folders = sorted(item for item in lobby.iterdir() if item.is_dir())
    except OSError:
        return []
    found = []
    for folder in folders:
        progress = load_progress(folder) or {}
        if progress.get("workspace") != workspace or not RUN_ID.match(folder.name):
            continue
        if runner_alive(store, folder.name) and not (folder / layout.RESULT).exists():
            found.append(folder)
    return found


def workspace_runs(store: Store, workspace: str | None) -> list[dict]:
    """Every run recorded for ``workspace`` (None: unbound runs), oldest first, with the runs
    waiting in the lobby for its lock.

    Each entry has the run identity, kind, name, Modules, status (``running``, ``lost`` or the
    result's status) and start time, from the result when there is one, else the progress file.
    """
    found = []
    for folder in [*store.folders(), *waiting_runs(store, workspace)]:
        result = _json(folder / layout.RESULT)
        progress = load_progress(folder)
        source = result or progress
        if not source or source.get("workspace") != workspace:
            continue
        run_id = source.get("run_id") or folder.name
        if not RUN_ID.match(run_id):
            continue
        status = result["status"] if result else run_state(store, run_id)
        found.append(
            {
                "run_id": run_id,
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


def _result_elsewhere(store: Store, run_id: str) -> dict | None:
    """The result of ``run_id`` traced outside ``store`` under the same ``.concorde``: another
    task's run, or an unbound run, so that its refusal can name whose run it is."""
    if not RUN_ID.match(run_id):
        return None
    try:
        folder, _ = reader.locate(run_id, [store.concorde])
    except reader.ReadError:
        return None
    return _json(folder / layout.RESULT)


def admit_inputs(
    store: Store, workspace: str | None, requested: list[str]
) -> dict[str, dict]:
    """The outputs of earlier ``ok`` runs of the same workspace (or of no workspace)."""
    admitted = {}
    for identity in requested:
        result = load_result(store, identity) or _result_elsewhere(store, identity)
        if result is None:
            raise RunError(
                "input_not_admissible",
                f"--input {identity} has no readable result at {result_path(store, identity)}",
            )
        try:
            validate(result, RESULT_SCHEMA)
        except KernelError as problem:
            raise RunError(
                "input_not_admissible",
                f"--input {identity} has a result that does not satisfy the current run result "
                f"contract at {problem.field or '/'}: {problem}; a result an older Concorde "
                "wrote is not admitted",
            ) from None
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


def lock_path(store: Store, workspace: str) -> Path:
    """The lock of ``workspace``, under the locks directory, which Git ignores."""
    return store.workspace_lock(workspace)


@contextmanager
def workspace_lock(
    store: Store,
    workspace: str,
    holder: str,
    wait: float = 0.0,
    waiting: Callable[[str], None] | None = None,
    retake: bool = True,
):
    """Hold the Kernel's lock of ``workspace`` or raise ``workspace_busy`` naming its holder.

    A busy lock is waited for up to ``wait`` seconds inside this process, so a caller that
    wants to queue behind the running run asks once instead of polling; ``waiting`` is told
    the holder when the wait begins. With ``retake`` False, a lock file its holder removed while
    this process waited, as the close that retires the workspace does, raises
    ``workspace_retired`` instead of being taken again. Execution's holder lines never name a task.
    """
    try:
        with locking.workspace_lock(
            store.concorde,
            workspace,
            holder,
            wait=wait,
            waiting=waiting,
            retake=retake,
        ):
            yield
    except KernelError as error:
        raise RunError(error.code, str(error)) from None


def lock_holder(store: Store, workspace: str) -> str | None:
    """Who holds the lock of ``workspace`` now, or None when nobody does."""
    return locking.workspace_lock_holder(store.concorde, workspace)


__all__ = [
    "KINDS",
    "RESULT_SCHEMA",
    "RUN_ID",
    "RUN_TRACE",
    "RunError",
    "Store",
    "admit_inputs",
    "load_progress",
    "load_result",
    "lock_holder",
    "lock_path",
    "new_run_id",
    "now",
    "pid_alive",
    "result_path",
    "run_lock",
    "run_state",
    "runner_alive",
    "store_of",
    "waiting_runs",
    "workspace_lock",
    "workspace_runs",
]
