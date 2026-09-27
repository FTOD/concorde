"""The workflow record of a workspace: the steps a workflow ran there and the reports it gave.

Workflows keeps it itself, in the run store of the workspace's records directory at
``runs/workflows/<workspace>/record.json``, next to the step lock, the answers passed to steps and
the saved reports. A workspace runs at most one workflow. Nothing else writes the record, and it is written only while
the step lock is held.
"""

from __future__ import annotations

import fcntl
import json
import os
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from ..execution import binding as workspace_binding


class WorkflowError(Exception):
    """A step or report Workflows refuses; ``code`` names why."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class Workspace:
    """The bound workspace a workflow runs in."""

    root: Path
    binding: dict

    @property
    def name(self) -> str:
        return self.binding["workspace"]

    @property
    def records(self) -> Path:
        return Path(self.binding["records"])

    @property
    def directory(self) -> Path:
        return self.records / "runs" / "workflows" / self.name


def workspace(here: Path) -> Workspace:
    """The bound workspace ``here`` lies in; ``WorkflowError`` when it is not one."""
    try:
        root = workspace_binding.toplevel(here)
        bound = workspace_binding.load(root)
    except workspace_binding.BindingError as error:
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
    return space.directory / "record.json"


def load(space: Workspace) -> dict | None:
    """The workspace's workflow record, or None before its first step."""
    path = record_path(space)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise WorkflowError(
            "record_unreadable", f"the workflow record {path} cannot be read: {error}"
        ) from error


def _write(space: Workspace, record: dict) -> None:
    path = record_path(space)
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(dir=path.parent, prefix=".record-")
    with os.fdopen(handle, "w", encoding="utf-8") as stream:
        stream.write(json.dumps(record, indent=2, ensure_ascii=False) + "\n")
    os.replace(temporary, path)


@contextmanager
def step_lock(space: Workspace):
    """The workspace's step lock, held while a key is looked up, started and recorded."""
    path = space.directory / "step.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


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


def record_step(
    space: Workspace,
    workflow: str,
    key: str,
    name: str,
    run_id: str | None,
    mode: str,
    answers: str | None,
    error: dict | None = None,
) -> dict:
    """Record one step under the held step lock: name the workflow on the first step, supersede,
    append.

    When a current step has the same base key, it and every step recorded after it are marked
    superseded, so a retried or answered step makes the procedure's later steps run again.
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
            "name": name,
            "run_id": run_id,
            "mode": mode,
            "answers": answers,
            "error": error,
            "superseded": False,
            "at": now(),
        }
    )
    _write(space, record)
    return record


def record_report(space: Workspace, result: dict, rendered: str) -> dict:
    """Save a report and its rendering next to the record and list it there."""
    with step_lock(space):
        record = load(space)
        if record is None:
            raise WorkflowError(
                "no_workflow",
                f"workspace {space.name} ran no workflow step; there is nothing to report",
            )
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
        _write(space, record)
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
    "WorkflowError",
    "Workspace",
    "base_key",
    "check_step",
    "current_steps",
    "load",
    "record_report",
    "record_step",
    "step_lock",
    "workspace",
    "write_answers",
]
