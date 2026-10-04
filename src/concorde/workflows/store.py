"""The workflow record of a workspace: the steps a workflow ran there and the reports it gave.

The record is the ``trace.json`` of the workflow's trace node, ``workflow/`` of the workspace folder
the binding names, beside the answers passed to steps (``answers/``), the saved reports
(``reports/``) and one trace node per step (``steps/<n>-<key>/``), inside which the step's run keeps
its own node. A workspace runs at most one workflow. Nothing else writes the record or the step
nodes, and they are written only while the workflow lock ``locks/workflows/<workspace>.lock`` of the
binding's ``.concorde`` is held. The lock is never taken again on a file that was removed or replaced
while waiting for it, and once held the binding is read again: whoever retires the workspace, as a
task's close does, removes the lock file while holding it, so a step or report that finds the lock
gone or the binding gone or changed is refused with ``workspace_retired`` before it writes anything.
A step is recorded as starting, without a run, before its run is launched, and its run is
written into it once announced; a later call finds a step still starting when the command that
launched it ended first, and adopts the run found in the step's node (``adopt``). Paths inside the
record are relative to the workflow's node; the record ``load`` returns names the answers files
absolutely, as the step command passes them on.
"""

from __future__ import annotations

import json
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from ..kernel import binding as workspace_binding
from ..kernel.refusal import KernelError
from ..execution.runs import RUN_ID, Store
from ..kernel.schema import register, validate_typed
from ..kernel.tracing.kinds import NodeKind, register as register_kinds
from ..kernel.tracing import layout, locks
from ..kernel.tracing import node as trace

_TEXT = {"type": "string", "minLength": 1}
_RELATIVE = {"type": "string", "minLength": 1, "format": "project-path"}
_MODE = {"enum": ["interactive", "no-ask"]}
# A free-form object, such as an error link: the typed-value check closes an object that has no
# additionalProperties.
_OBJECT = {"type": "object", "additionalProperties": {}}
# contract.workflows.workflow-trace, version 2
WORKFLOW_TRACE = "concorde-workflow-trace"
register(
    WORKFLOW_TRACE,
    2,
    {
        "type": "object",
        "additionalProperties": False,
        "required": ["workflow", "steps", "reports"],
        "properties": {
            "workflow": _TEXT,
            "steps": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "key",
                        "name",
                        "run_id",
                        "mode",
                        "answers",
                        "error",
                        "superseded",
                        "node",
                        "at",
                    ],
                    "properties": {
                        "key": _TEXT,
                        "name": _TEXT,
                        "run_id": {"anyOf": [{"type": "null"}, _TEXT]},
                        "mode": _MODE,
                        "answers": {"anyOf": [{"type": "null"}, _RELATIVE]},
                        "error": {"anyOf": [{"type": "null"}, _OBJECT]},
                        "superseded": {"type": "boolean"},
                        "node": _RELATIVE,
                        "at": _TEXT,
                    },
                },
            },
            "reports": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["status", "path", "rendered", "at"],
                    "properties": {
                        "status": _TEXT,
                        "path": _RELATIVE,
                        "rendered": _RELATIVE,
                        "at": _TEXT,
                    },
                },
            },
        },
    },
)
# contract.workflows.step-trace, version 2
STEP_TRACE = "concorde-step-trace"
register(
    STEP_TRACE,
    2,
    {
        "type": "object",
        "additionalProperties": False,
        "required": ["key", "name", "run_id", "mode", "superseded", "state"],
        "properties": {
            "key": _TEXT,
            "name": _TEXT,
            "run_id": {"anyOf": [{"type": "null"}, _TEXT]},
            "mode": _MODE,
            "superseded": {"type": "boolean"},
            "state": {"enum": ["running", "finished", "lost", "refused"]},
        },
    },
)
register_kinds(
    NodeKind("workflow", WORKFLOW_TRACE, ("workspace", "workflow", "mode")),
    NodeKind("step", STEP_TRACE, ("workspace", "workflow", "operation", "command")),
)
# How a report's status ends the workflow's node.
REPORT_STATUS = {
    "ok": "ok",
    "blocked": "blocked",
    "failed": "failed",
    "awaiting_decision": "blocked",
}


class WorkflowError(Exception):
    """A step or report Workflows refuses; ``code`` names why."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


class WorkspaceRetired(WorkflowError):
    """The workspace was retired, or its binding changed, while the command waited for its workflow
    lock; ``found`` names what was found: ``lock_removed``, ``binding_gone``,
    ``binding_untrusted`` or ``binding_changed``."""

    def __init__(self, found: str, message: str):
        super().__init__("workspace_retired", message)
        self.found = found


@dataclass(frozen=True)
class Workspace:
    """The bound workspace a workflow runs in."""

    root: Path
    binding: dict

    @property
    def name(self) -> str:
        return self.binding["workspace"]

    @property
    def store(self) -> Store:
        """Where the workspace's runs and locks are kept."""
        return Store(Path(self.binding["concorde"]), Path(self.binding["traces"]))

    @property
    def directory(self) -> Path:
        """The workflow's trace node folder."""
        return layout.workflow_folder(Path(self.binding["traces"]))

    @property
    def lock(self) -> Path:
        return layout.lock_file(Path(self.binding["concorde"]), "workflow", self.name)


def workspace(here: Path) -> Workspace:
    """The bound workspace ``here`` lies in; ``WorkflowError`` when it is not one."""
    try:
        root = workspace_binding.toplevel(here)
        bound = workspace_binding.load(root)
    except KernelError as error:
        raise WorkflowError(error.code, str(error)) from error
    if bound is None:
        raise WorkflowError(
            "binding_required",
            f"{root} has no workspace binding ({workspace_binding.BINDING}); a workflow runs "
            "only in a bound workspace, such as a task worktree",
        )
    return Workspace(root, bound)


def now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def base_key(key: str) -> str:
    """A step key without its restart generation and answers digest."""
    return key.split("@", 1)[0].split("#", 1)[0]


def record_path(space: Workspace) -> Path:
    return space.directory / layout.TRACE


def load(space: Workspace) -> dict | None:
    """The workspace's workflow record, or None before its first step."""
    path = record_path(space)
    if not path.exists():
        return None
    try:
        node = json.loads(path.read_text(encoding="utf-8"))
        content = node.get("content") if isinstance(node, dict) else None
        data = validate_typed(content, WORKFLOW_TRACE)["data"]
    except (OSError, ValueError, KernelError) as error:
        raise WorkflowError(
            "record_unreadable", f"the workflow record {path} cannot be read: {error}"
        ) from error
    steps = [
        {
            **step,
            "answers": (space.directory / step["answers"]).as_posix()
            if step["answers"]
            else None,
        }
        for step in data["steps"]
    ]
    reports = [
        {
            **item,
            "path": (space.directory / item["path"]).as_posix(),
            "rendered": (space.directory / item["rendered"]).as_posix(),
        }
        for item in data["reports"]
    ]
    return {
        "workspace": space.name,
        "workflow": data["workflow"],
        "steps": steps,
        "reports": reports,
        "_node": node,
    }


def _relative(space: Workspace, path: str | None) -> str | None:
    if not path:
        return None
    try:
        return Path(path).relative_to(space.directory).as_posix()
    except ValueError:
        return layout.relative(space.directory, Path(path))


def _write(space: Workspace, record: dict, *, ended: dict | None = None) -> None:
    """Write the workflow's node from ``record``; ``ended`` ends it with a report's status."""
    node = record.get("_node")
    steps = [
        {
            "key": step["key"],
            "name": step["name"],
            "run_id": step["run_id"],
            "mode": step["mode"],
            "answers": _relative(space, step.get("answers")),
            "error": step.get("error"),
            "superseded": bool(step.get("superseded")),
            "node": step["node"],
            "at": step["at"],
        }
        for step in record["steps"]
    ]
    reports = [
        {
            "status": item["status"],
            "path": _relative(space, item["path"]),
            "rendered": _relative(space, item["rendered"]),
            "at": item["at"],
        }
        for item in record["reports"]
    ]
    if node is None:
        node = {
            "schema_version": 1,
            "id": record["workflow"],
            "kind": "workflow",
            "started_at": trace.now(),
            "ended_at": None,
            "status": "running",
            "outcome": None,
            "usage": trace.usage(),
            "error": None,
            "metadata": {"workspace": space.name, "workflow": record["workflow"]},
            "artifacts": [],
            "references": [],
            "content": None,
        }
    node = dict(node)
    current = [step for step in record["steps"] if not step.get("superseded")]
    if current:
        node["metadata"] = {**node["metadata"], "mode": current[-1]["mode"]}
    if ended is None:
        node.update(
            ended_at=None,
            status="running",
            outcome=None,
            error=None,
            usage=trace.usage(),
        )
    else:
        status = REPORT_STATUS.get(ended["status"], "running")
        at = trace.now()
        node.update(
            ended_at=None if status == "running" else at,
            status=status,
            outcome=None if status == "running" else ended["status"],
            error=ended.get("error") if status in ("blocked", "failed") else None,
            usage=trace.usage(
                duration_seconds=trace.seconds_between(node["started_at"], at)
            )
            if status != "running"
            else trace.usage(),
        )
    node["content"] = {
        "type_id": WORKFLOW_TRACE,
        "schema_version": 2,
        "data": {"workflow": record["workflow"], "steps": steps, "reports": reports},
    }
    trace.write(space.directory, node)
    record["_node"] = node


@contextmanager
def step_lock(space: Workspace, wait: float | None = None):
    """The workspace's workflow lock, held while a key is looked up, started and recorded, a step's
    node ended or a report saved; ``WorkspaceRetired`` when the workspace was retired meanwhile,
    ``locks.LockBusy`` when another command still holds it after ``wait`` seconds (None: as long
    as it takes).

    The lock is a leaf: nothing waits for another lock while holding it, so that a close holding
    the workspace lock always gets it soon. A lock file removed or replaced while this process
    waited for it is never taken again, and once held the binding must still be the one the
    command read, since a close removes the worktree with its binding before it moves the
    workspace folder and removes the lock file while holding the lock.
    """
    try:
        with locks.hold(
            space.lock, f"workflow of workspace {space.name}", wait=wait, retake=False
        ):
            _check_binding(space)
            yield
    except locks.LockGone as gone:
        raise WorkspaceRetired(
            "lock_removed",
            f"the workspace {space.name} was retired while this command waited for its workflow "
            f"lock: {gone}",
        ) from None


def _check_binding(space: Workspace) -> None:
    """Refuse with ``WorkspaceRetired`` unless the worktree's binding is still the one read."""
    path = workspace_binding.path_of(space.root)
    try:
        current = workspace_binding.load(space.root)
    except KernelError as error:
        raise WorkspaceRetired(
            "binding_untrusted",
            f"the workspace {space.name} was retired while this command waited for its workflow "
            f"lock: its binding {path} can no longer be trusted ({error.code}: {error})",
        ) from None
    if current is None:
        raise WorkspaceRetired(
            "binding_gone",
            f"the workspace {space.name} was retired while this command waited for its workflow "
            f"lock: its binding {path} is gone",
        )
    if current != space.binding:
        changed = sorted(
            key
            for key in {*space.binding, *current}
            if space.binding.get(key) != current.get(key)
        )
        raise WorkspaceRetired(
            "binding_changed",
            f"the binding {path} changed while this command waited for the workflow lock of "
            f"workspace {space.name} (changed: {', '.join(changed)}); a workflow writes only in "
            "the workspace whose binding it read",
        )


def starting(step: dict) -> bool:
    """Whether a recorded step is still starting: recorded before its run was launched, with
    neither the run nor a refusal written into it yet."""
    return step["run_id"] is None and step.get("error") is None


def current_steps(record: dict | None) -> list[dict]:
    """The steps no later rerun superseded, in record order."""
    return [
        step for step in (record or {}).get("steps", []) if not step.get("superseded")
    ]


def check_step(
    space: Workspace, record: dict | None, workflow: str, key: str, name: str
) -> None:
    """Refuse a step the workspace cannot take, before anything is started for it.

    ``workflow_conflict`` when the workspace runs another workflow and ``step_conflict`` when the
    key is recorded for another Operation or command.
    """
    if record is not None and record["workflow"] != workflow:
        raise WorkflowError(
            "workflow_conflict",
            f"workspace {space.name} runs the workflow {record['workflow']}; a step of "
            f"{workflow} is refused, since a workspace runs at most one workflow",
        )
    for step in (record or {}).get("steps", []):
        if step["key"] == key and step["name"] != name:
            raise WorkflowError(
                "step_conflict",
                f"step key {key} of workspace {space.name} is recorded for {step['name']} "
                f"(run {step['run_id']}), not {name}",
            )


def next_step_folder(space: Workspace, record: dict | None, key: str) -> Path:
    """The trace node folder the next recorded step gets, for its run to be placed in."""
    number = len((record or {}).get("steps", [])) + 1
    return layout.step_folder(space.directory, number, key)


def step_node(space: Workspace, step: dict) -> dict | None:
    return trace.read(space.directory / step["node"])


def _write_step(
    space: Workspace,
    step: dict,
    *,
    state: str,
    result: dict | None = None,
    error: dict | None = None,
) -> None:
    """Write the step's node: running while the step starts and its run runs, ended once it
    finished, was lost or was refused. An ended node is written again only to mark it superseded.
    The node's identity is its folder name, ``<n>-<key>``: a retried key has one node per attempt."""
    folder = space.directory / step["node"]
    existing = trace.read(folder)
    data = {
        "key": step["key"],
        "name": step["name"],
        "run_id": step["run_id"],
        "mode": step["mode"],
        "superseded": bool(step.get("superseded")),
        "state": state,
    }
    if existing is not None and existing.get("ended_at") and state != "running":
        existing["content"]["data"]["superseded"] = data["superseded"]
        trace.write(folder, existing)
        return
    kind = "command" if step["name"] in _commands() else "operation"
    record = existing or {
        "schema_version": 1,
        "id": folder.name,
        "kind": "step",
        "started_at": trace.now(),
        "ended_at": None,
        "status": "running",
        "outcome": None,
        "usage": trace.usage(),
        "error": None,
        "metadata": {
            "workspace": space.name,
            "workflow": (load(space) or {}).get("workflow")
            or step.get("workflow")
            or "",
            kind: step["name"],
        },
        "artifacts": [],
        "references": [],
        "content": None,
    }
    if not record["metadata"].get("workflow"):
        record["metadata"].pop("workflow", None)
    if state != "running":
        status = (
            (result or {}).get("status", "failed") if state == "finished" else "failed"
        )
        at = (result or {}).get("finished_at") or trace.now()
        record.update(
            ended_at=at,
            status=status if status in ("ok", "blocked", "failed") else "failed",
            outcome=state,
            error=error or (result or {}).get("error"),
            usage=trace.usage(
                duration_seconds=trace.seconds_between(record["started_at"], at)
            ),
        )
        if record["status"] not in ("blocked", "failed"):
            record["error"] = None
    record["content"] = {"type_id": STEP_TRACE, "schema_version": 2, "data": data}
    trace.write(folder, record)


def _commands() -> set[str]:
    from ..execution.commands.catalog import COMMANDS

    return set(COMMANDS)


def record_step(
    space: Workspace,
    workflow: str,
    key: str,
    name: str,
    mode: str,
    answers: str | None,
    folder: Path | None = None,
) -> dict:
    """Record one step as starting, before its run is launched, under the held workflow lock: name
    the workflow on the first step, supersede, append, and write the step's node.

    When a current step has the same base key, it and every step recorded after it are marked
    superseded, so a retried or answered step makes the procedure's later steps run again.
    ``set_run`` writes the announced run, or the refusal, into the step.
    """
    record = load(space)
    check_step(space, record, workflow, key, name)
    record = record or {
        "workspace": space.name,
        "workflow": workflow,
        "steps": [],
        "reports": [],
    }
    steps = record["steps"]
    folder = folder or next_step_folder(space, record, key)
    earlier = next(
        (
            index
            for index, step in enumerate(steps)
            if not step.get("superseded") and base_key(step["key"]) == base_key(key)
        ),
        None,
    )
    superseded = []
    if earlier is not None:
        for step in steps[earlier:]:
            step["superseded"] = True
            superseded.append(step)
    entry = {
        "key": key,
        "name": name,
        "run_id": None,
        "mode": mode,
        "answers": answers,
        "error": None,
        "superseded": False,
        "node": folder.relative_to(space.directory).as_posix(),
        "at": now(),
    }
    steps.append(entry)
    _write(space, record)
    for step in superseded:
        node = step_node(space, step)
        if node is not None:
            _write_step(space, step, state=(node["content"]["data"]["state"]))
    _write_step(space, {**entry, "workflow": workflow}, state="running")
    return record


def set_run(
    space: Workspace, node: str, run_id: str | None, error: dict | None = None
) -> dict:
    """Write into the starting step whose node is ``node`` its announced run, or the refusal of a
    run that did not start, under the held workflow lock; the step. ``WorkflowError``
    (``record_unwritable``) when the record cannot be written, the step staying starting."""
    record = load(space)
    step = next(
        (
            s
            for s in (record or {}).get("steps", [])
            if s["node"] == node and starting(s)
        ),
        None,
    )
    if step is None:
        raise WorkflowError(
            "record_unwritable",
            f"the workflow record of workspace {space.name} holds no starting step in {node}",
        )
    step.update(run_id=run_id, error=error)
    try:
        _write(space, record)
        _write_step(
            space,
            step,
            state="refused" if run_id is None else "running",
            error=error,
        )
    except OSError as failure:
        raise WorkflowError(
            "record_unwritable",
            f"the workflow record of workspace {space.name} could not record the step in "
            f"{node}: {failure}",
        ) from failure
    return step


def node_run(space: Workspace, step: dict) -> str | None:
    """The run whose node lies in ``run/`` of the step's node, or None while none entered it."""
    found = trace.read(space.directory / step["node"] / "run")
    identity = (found or {}).get("id")
    return identity if isinstance(identity, str) and RUN_ID.match(identity) else None


def adopt(space: Workspace, step: dict) -> str | None:
    """The run of a step still starting, found in its node and written into the record under the
    held workflow lock; None while no run entered the node. The command that launched the run
    ended before it could record it, so the step's node, where the run was placed, names it."""
    run_id = node_run(space, step)
    if run_id is not None:
        set_run(space, step["node"], run_id)
        step["run_id"] = run_id
    return run_id


def end_step(
    space: Workspace,
    step: dict,
    state: str,
    result: dict | None,
    error: dict | None = None,
) -> None:
    """End a step's node once its run finished or was lost, with ``error`` as the step's own link
    for a lost one; a node already ended is kept."""
    node = step_node(space, step)
    if node is None or node.get("ended_at") or state == "running":
        return
    _write_step(space, step, state=state, result=result, error=error)


def record_report(space: Workspace, result: dict, rendered: str) -> dict:
    """Save a report and its rendering in the workflow's node, list it there and end the node
    with the report's status; the caller holds the workflow lock (``step_lock``). A workspace
    whose first step was lost before anything was recorded gets its workflow's node here."""
    record = load(space) or {
        "workspace": space.name,
        "workflow": result["workflow"],
        "steps": [],
        "reports": [],
    }
    number = len(record["reports"]) + 1
    folder = space.directory / "reports"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{number}.json"
    path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    text = folder / f"{number}.md"
    text.write_text(rendered, encoding="utf-8")
    record["reports"].append(
        {
            "status": result["status"],
            "path": path.as_posix(),
            "rendered": text.as_posix(),
            "at": now(),
        }
    )
    _write(space, record, ended=result)
    return record


def write_answers(space: Workspace, key: str, answers: list[dict]) -> str:
    folder = space.directory / "answers"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / (key.replace(":", "_").replace("@", "-") + ".json")
    path.write_text(
        json.dumps({"answers": answers}, indent=2, ensure_ascii=False) + "\n"
    )
    return path.as_posix()


__all__ = [
    "STEP_TRACE",
    "WORKFLOW_TRACE",
    "WorkflowError",
    "Workspace",
    "WorkspaceRetired",
    "adopt",
    "base_key",
    "check_step",
    "current_steps",
    "end_step",
    "load",
    "next_step_folder",
    "node_run",
    "record_report",
    "record_step",
    "set_run",
    "starting",
    "step_lock",
    "workspace",
    "write_answers",
]
