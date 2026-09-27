"""``concorde workflow step``: start or await one keyed run of a workflow in its workspace.

A step key names one run of the bound workspace: an Operation, or an execution command such as
``task-validation``, ``delivery`` or ``scaffold``. The first call for a key starts the run
detached, with the workspace's own ``concorde``, and records it in the workspace's workflow record;
every later call finds the recorded run and only waits for it, so repeating a call or relaunching a
whole workflow never starts a run twice. Answers make a new key (the base key, ``@`` and a digest
of the answers), are written next to the workflow record and passed to the run with the run that
asked them as ``--input``. Starting a new run for a base key supersedes the steps recorded after it
(see ``store.record_step``). The outcome is built from the workflow record and the saved run
result, never from what a caller relayed.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

from .. import errors
from ..commands.catalog import COMMANDS
from ..execution.runs import (
    RUN_ID_PATTERN,
    load_result,
    lock_holder,
    run_directory,
    run_state,
)
from ..spec.schema import validate
from . import store
from .store import WorkflowError, Workspace

WAIT = 540.0
POLL = 0.5
KEY_PATTERN = "^[a-z][a-z0-9_:.-]*$"
ANSWER = {
    "type": "object",
    "additionalProperties": False,
    "required": ["id", "question", "answer"],
    "properties": {
        "id": {"type": "string", "pattern": "^[dq]\\.[a-z0-9-]+$"},
        "question": {"type": "string", "minLength": 1},
        "answer": {"type": "string", "minLength": 1},
    },
}
# contract.workflows.step-request, version 4
REQUEST_SCHEMA: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": ["workflow", "mode", "key", "argv"],
    "properties": {
        "workflow": {"type": "string", "minLength": 1},
        "mode": {"enum": ["interactive", "no-ask"]},
        "key": {"type": "string", "pattern": KEY_PATTERN},
        "argv": {
            "type": "array",
            "minItems": 1,
            "items": {"type": "string", "minLength": 1},
        },
        "answers": {
            "anyOf": [
                {"type": "null"},
                {"type": "array", "minItems": 1, "items": ANSWER},
            ]
        },
        "retry": {"type": "boolean"},
        "restart": {
            "anyOf": [{"type": "null"}, {"type": "string", "pattern": "^[a-z0-9-]+$"}]
        },
    },
}
MODULE_ID = {
    "type": "string",
    "pattern": "^module\\.[a-z][a-z0-9-]*(?:\\.[a-z0-9-]+)*$",
}
NAME = {"type": "string", "pattern": "^[a-z][a-z_-]*$"}
# contract.workflows.step, version 4
STEP_SCHEMA: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "workflow",
        "workspace",
        "key",
        "name",
        "run_id",
        "state",
        "status",
        "summary",
        "result_path",
        "decision_points",
        "created_modules",
        "ready",
        "error",
    ],
    "properties": {
        "workflow": {"type": "string", "minLength": 1},
        "workspace": {"type": "string", "minLength": 1},
        "key": {
            "type": "string",
            "pattern": "^[a-z][a-z0-9_:.-]*(?:#[a-z0-9-]+)?(?:@[0-9a-f]{8})?$",
        },
        "name": NAME,
        "run_id": {
            "anyOf": [
                {"type": "string", "pattern": RUN_ID_PATTERN},
                {"type": "null"},
            ]
        },
        "state": {"enum": ["running", "finished", "lost", "refused"]},
        "status": {"anyOf": [{"enum": ["ok", "blocked", "failed"]}, {"type": "null"}]},
        "summary": {"anyOf": [{"type": "string", "minLength": 1}, {"type": "null"}]},
        "result_path": {
            "anyOf": [{"type": "string", "minLength": 1}, {"type": "null"}]
        },
        "decision_points": {"type": "integer", "minimum": 0},
        "created_modules": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["id", "uses"],
                "properties": {
                    "id": MODULE_ID,
                    "uses": {"type": "array", "items": MODULE_ID},
                },
            },
        },
        "ready": {"anyOf": [{"type": "boolean"}, {"type": "null"}]},
        "error": {"anyOf": [{"type": "null"}, {"$ref": "#/$defs/error"}]},
    },
    "$defs": copy.deepcopy(errors.DEFS),
}


class StepError(Exception):
    """A step that cannot go on; ``link`` is the workflow's error link."""

    def __init__(self, link: dict, state: str = "refused"):
        super().__init__(link["detail"])
        self.link = link
        self.state = state


def actor(workflow: str, workspace: str) -> str:
    return f"workflow {workflow} (workspace {workspace})"


def workflow_link(
    workflow, workspace, code, detail, *, reason, explanation, **extra
) -> dict:
    return errors.link(
        "workflow",
        actor(workflow, workspace),
        code,
        detail,
        reason=reason,
        explanation=explanation,
        **extra,
    )


def answers_digest(answers: list[dict]) -> str:
    canonical = json.dumps(
        answers, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:8]


def step_key(base: str, answers: list[dict] | None, restart: str | None = None) -> str:
    """The key of a step: its base key, the restart generation after ``#`` and the answers
    digest after ``@``."""
    key = f"{base}#{restart}" if restart else base
    return f"{key}@{answers_digest(answers)}" if answers else key


def host_output(records: Path, run_id: str) -> str:
    """The end of what a detached runner printed, where it reports failures outside its steps."""
    try:
        data = (run_directory(records, run_id) / "host.out").read_bytes()
    except OSError:
        return ""
    return data[-4000:].decode("utf-8", "replace").strip()


def lost_link(space: Workspace, workflow: str, key: str, name: str, run_id: str):
    output = host_output(space.records, run_id)
    directory = run_directory(space.records, run_id).as_posix()
    return workflow_link(
        workflow,
        space.name,
        "step_lost",
        f"the {name} run {run_id} of step {key} has no result and its runner no longer "
        "runs; it ended without writing its result",
        reason="environment",
        explanation="the workflow cannot recover a run whose runner ended without a result",
        evidence=[
            errors.evidence("run", directory, ""),
            errors.evidence("host-output", f"{directory}/host.out", output[-2000:]),
        ],
        options=[
            f"read the runner output, then run the step again with retry for "
            f"{store.base_key(key)}"
        ],
        causes=[
            errors.link(
                "component",
                f"Execution runner of {run_id}",
                "host_ended",
                "the runner ended without a result; its output ends with: "
                + (output or "(nothing)"),
                reason="environment",
                explanation="a runner that fails outside its steps writes only its output, "
                "not a result",
            )
        ],
    )


def concorde_command(worktree: Path) -> list[str]:
    """The workspace's own ``concorde``: its installed command, or this checkout's script."""
    installed = worktree / ".concorde/bin/concorde"
    if installed.is_file():
        return [str(installed)]
    script = worktree / "scripts/concorde.py"
    if script.is_file():
        return [sys.executable, str(script)]
    return [sys.executable, "-m", "concorde"]


def start_run(workflow: str, space: Workspace, argv: list[str]) -> dict:
    """Start the step's run detached in the workspace; the announced run.

    An Operation starts with ``concorde run <argv> --detach``, an execution command with
    ``concorde <argv> --detach``. ``StepError`` carries a ``step_refused`` link when the runner
    rejected the command line (its standard error as the cause) or the detached runner did not
    start (its link as the cause).
    """
    prefix = [] if argv[0] in COMMANDS else ["run"]
    command = [*concorde_command(space.root), *prefix, *argv, "--detach"]
    environment = dict(os.environ)
    if command[1:3] == ["-m", "concorde"]:
        # This package itself: make it importable for the child.
        environment["PYTHONPATH"] = os.pathsep.join(
            [str(Path(__file__).resolve().parents[2])]
            + ([environment["PYTHONPATH"]] if environment.get("PYTHONPATH") else [])
        )
    completed = subprocess.run(
        command,
        cwd=space.root,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    shown = " ".join(command)
    try:
        announced = json.loads(completed.stdout) if completed.stdout.strip() else None
    except ValueError:
        announced = None
    if (
        completed.returncode == 0
        and isinstance(announced, dict)
        and announced.get("run_id")
    ):
        return announced
    if isinstance(announced, dict) and isinstance(announced.get("error"), dict):
        cause = announced["error"]
    else:
        cause = errors.link(
            "component",
            "Execution runner",
            "command_refused" if completed.returncode == 2 else "run_not_started",
            f"`{shown}` exited with status {completed.returncode}: "
            f"{(completed.stderr or completed.stdout).strip() or '(no output)'}",
            reason="input" if completed.returncode == 2 else "environment",
            explanation="the runner starts no run for a command line it cannot accept",
        )
    raise StepError(
        workflow_link(
            workflow,
            space.name,
            "step_refused",
            f"the step's run could not start: `{shown}` exited with status "
            f"{completed.returncode}",
            reason="input",
            explanation="the workflow runs the command its procedure names and cannot correct "
            "a command line the runner rejects or a runner that does not start",
            evidence=[errors.evidence("command", shown, "")],
            options=[
                "correct the workflow script or the step's arguments and run it again"
            ],
            causes=[cause],
        )
    )


def asking_run(space: Workspace, record: dict | None, base: str) -> str | None:
    """The latest ok run of a base key, superseded or not: the run whose questions the answers
    settle. A retried or re-answered step supersedes the run that asked, yet still refers to it."""
    for step in reversed((record or {}).get("steps", [])):
        if store.base_key(step["key"]) == base and step["run_id"]:
            result = load_result(space.records, step["run_id"])
            if result is not None and result.get("status") == "ok":
                return step["run_id"]
    return None


def answered(path: str | None) -> set[str]:
    """The identities a step's answers file answers."""
    if not path:
        return set()
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
        return {item["id"] for item in value.get("answers") or []}
    except (OSError, ValueError, AttributeError, KeyError, TypeError):
        return set()


def created_modules(records: Path, output: dict | None) -> list[dict]:
    """The Modules a scaffold created, each with the other created Modules its survey said it
    uses, in the scaffold's order."""
    if not output or "created" not in output:
        return []
    created = [item["id"] for item in output["created"]]
    survey = load_result(records, output.get("survey_run")) or {}
    uses = {
        child["id"]: [use["target"] for use in child.get("uses", [])]
        for child in ((survey.get("output") or {}).get("children") or [])
    }
    return [
        {"id": identity, "uses": [t for t in uses.get(identity, []) if t in created]}
        for identity in created
    ]


def decision_points(name: str, output: dict | None, settled=frozenset()) -> int:
    """Open questions, and for a survey decisions the worker took, that no answer settled."""
    if not output:
        return 0
    count = sum(
        1
        for item in output.get("open_questions") or []
        if item.get("id") not in settled
    )
    if name == "survey":
        count += sum(
            1
            for item in output.get("decisions") or []
            if item.get("decided_by") == "worker" and item.get("id") not in settled
        )
    return count


def outcome(
    space: Workspace,
    workflow: str,
    key: str,
    name: str,
    run_id: str | None,
    state: str,
    error: dict | None = None,
    settled=frozenset(),
) -> dict:
    result = load_result(space.records, run_id) if state == "finished" else None
    output = (result or {}).get("output")
    value = {
        "workflow": workflow,
        "workspace": space.name,
        "key": key,
        "name": name,
        "run_id": run_id,
        "state": state,
        "status": (result or {}).get("status"),
        "summary": (result or {}).get("summary"),
        "result_path": (
            (run_directory(space.records, run_id) / "result.json").as_posix()
            if run_id
            else None
        ),
        "decision_points": decision_points(name, output, settled),
        "created_modules": created_modules(space.records, output)
        if name == "scaffold"
        else [],
        "ready": output.get("ready")
        if name == "task-validation" and isinstance(output, dict)
        else None,
        "error": error,
    }
    if state == "lost" and error is None:
        value["error"] = lost_link(space, workflow, key, name, run_id)
    validate(value, STEP_SCHEMA)
    return value


def rejected(
    space: Workspace, workflow, key, name, refusal, *, started: str | None = None
):
    """The ``step_rejected`` outcome of a step Workflows refused, with its refusal as the cause."""
    if started:
        detail = (
            f"step {key} ({name}) started run {started}, but its workflow record refused it: "
            f"{refusal.code}: {refusal}; the run is live and unrecorded"
        )
        options = [f"wait for run {started} to end, then run the step again with retry"]
    else:
        detail = (
            f"the workflow record of workspace {space.name} refused step {key} ({name}): "
            f"{refusal.code}: {refusal}; nothing was started"
        )
        options = [
            "run the workflow in the workspace it belongs to, or in a new workspace"
        ]
    return workflow_link(
        workflow,
        space.name,
        "step_unrecorded" if started else "step_rejected",
        detail,
        reason="environment" if started else "input",
        explanation="the workflow cannot record a step its workspace does not accept",
        evidence=[errors.evidence("run", started, "")] if started else [],
        causes=[
            errors.link(
                "component",
                "Workflows (workflow record)",
                refusal.code,
                str(refusal),
                reason="input",
                explanation="the workflow record refuses a step whose workflow or key does "
                "not admit it",
            )
        ],
        options=options,
    )


def run_step(
    space: Workspace, request: dict, wait: float | None = WAIT
) -> tuple[int, dict]:
    """Start or await one step; the exit status (0 finished, 3 running, 1 otherwise) and the
    outcome. ``wait`` None waits until the run has finished or is lost."""
    workflow, mode = request["workflow"], request["mode"]
    name = request["argv"][0]
    answers = request["answers"]
    key = step_key(request["key"], answers, request["restart"])
    settled = frozenset(item["id"] for item in answers or [])
    deadline = None if wait is None else time.monotonic() + wait

    def refused(link: dict, run_id: str | None = None) -> tuple[int, dict]:
        return 1, outcome(space, workflow, key, name, run_id, "refused", link, settled)

    started = None
    try:
        with store.step_lock(space):
            record = store.load(space)
            store.check_step(space, record, workflow, key, name)
            found = next(
                (s for s in reversed(store.current_steps(record)) if s["key"] == key),
                None,
            )
            state = run_state(space.records, found["run_id"]) if found else None
            restart = found is None or (
                request["retry"]
                and state in ("finished", "lost", "refused")
                and (load_result(space.records, found["run_id"]) or {}).get("status")
                != "ok"
            )
            if not restart:
                run_id = found["run_id"]
                if run_id is None:
                    return refused(found.get("error"))
            else:
                # One run of a workspace at a time: wait for a run still holding the workspace,
                # such as the previous step's whose runner is finishing, before starting this one.
                while lock_holder(space.records, space.name) is not None:
                    if deadline is not None and time.monotonic() >= deadline:
                        return 3, outcome(
                            space, workflow, key, name, None, "running", None, settled
                        )
                    time.sleep(POLL)
                argv = list(request["argv"])
                path = None
                if answers:
                    path = store.write_answers(space, key, answers)
                    argv += ["--answers", path]
                    asked = asking_run(space, record, request["key"])
                    if asked:
                        argv += ["--input", asked]
                try:
                    announced = start_run(workflow, space, argv)
                    run_id, error = announced["run_id"], None
                except StepError as refusal:
                    run_id, error = None, refusal.link
                started = run_id
                store.record_step(space, workflow, key, name, run_id, mode, path, error)
                if error is not None:
                    return refused(error)
    except WorkflowError as refusal:
        return refused(
            rejected(space, workflow, key, name, refusal, started=started), started
        )
    while True:
        state = run_state(space.records, run_id)
        if state != "running" or (
            deadline is not None and time.monotonic() >= deadline
        ):
            break
        time.sleep(POLL)
    value = outcome(space, workflow, key, name, run_id, state, None, settled)
    return {"finished": 0, "running": 3}.get(state, 1), value


# What an omitted optional field of a step request means. A step agent that retypes a request
# has less to copy when the script leaves these out.
REQUEST_DEFAULTS = {"answers": None, "retry": False, "restart": None}


def check_request(request) -> dict:
    """The request with its defaults if it satisfies its contract; ``ContractError`` otherwise."""
    validate(request, REQUEST_SCHEMA)
    return {**REQUEST_DEFAULTS, **request}


__all__ = [
    "REQUEST_SCHEMA",
    "STEP_SCHEMA",
    "StepError",
    "answers_digest",
    "check_request",
    "run_step",
    "step_key",
    "workflow_link",
]
