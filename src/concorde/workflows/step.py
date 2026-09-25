"""``concorde workflow step``: start or await one keyed Operation run of a workflow.

A step key names one Operation run of a task. The first call for a key starts the run detached,
with the task worktree's own ``concorde``, and records it in the task record; every later call
finds the recorded run and only waits for it, so repeating a call or relaunching a whole workflow
never starts an Operation twice. Answers make a new key (the base key, ``@`` and a digest of the
answers), are written next to the task record and passed to the run with the run that asked them
as ``--input``. Starting a new run for a base key supersedes the steps recorded after it (see
``store.record_workflow_step``). The outcome is built from the task record and the saved
Operation result, never from what a caller relayed.
"""

from __future__ import annotations

import copy
import fcntl
import hashlib
import json
import os
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path

from .. import errors
from ..spec.schema import validate
from ..tasks import store

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
# contract.workflows.step-request, version 3
REQUEST_SCHEMA: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": ["task", "workflow", "mode", "key", "argv"],
    "properties": {
        "task": {"type": "string", "minLength": 1},
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
# contract.workflows.step, version 1
STEP_SCHEMA: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "workflow",
        "task",
        "key",
        "operation",
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
        "task": {"type": "string", "minLength": 1},
        "key": {
            "type": "string",
            "pattern": "^[a-z][a-z0-9_:.-]*(?:#[a-z0-9-]+)?(?:@[0-9a-f]{8})?$",
        },
        "operation": {"type": "string", "pattern": "^[a-z][a-z_]*$"},
        "run_id": {
            "anyOf": [
                {
                    "type": "string",
                    "pattern": "^r-[0-9]{8}T[0-9]{6}-[a-z_]+-[0-9a-f]{8}$",
                },
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


def actor(workflow: str, task: str) -> str:
    return f"workflow {workflow} (task {task})"


def workflow_link(
    workflow, task, code, detail, *, reason, explanation, **extra
) -> dict:
    return errors.link(
        "workflow",
        actor(workflow, task),
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


def runs_directory(primary: Path) -> Path:
    return primary / ".concorde/runs"


def load_result(primary: Path, run_id: str | None) -> dict | None:
    if not run_id:
        return None
    path = runs_directory(primary) / run_id / "result.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def host_alive(primary: Path, run_id: str) -> bool:
    """Whether the host of a run without a result still lives, from its progress file."""
    try:
        state = json.loads(
            (runs_directory(primary) / run_id / "status.json").read_text()
        )
        pid = int(state["host_pid"])
    except (OSError, ValueError, KeyError, TypeError):
        return False
    return pid_alive(pid)


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


def run_state(primary: Path, run_id: str | None) -> str:
    """``finished``, ``running`` or ``lost`` for a recorded run; ``refused`` without one.

    The host writes ``result.json`` only after it finished the run in the task record, so a
    result means the task record is final as well.
    """
    if not run_id:
        return "refused"
    if load_result(primary, run_id) is not None:
        return "finished"
    if host_alive(primary, run_id):
        return "running"
    # The host may have written its result between the two reads.
    return "finished" if load_result(primary, run_id) is not None else "lost"


def host_output(primary: Path, run_id: str) -> str:
    """The end of what a detached host printed, where it reports failures outside its steps."""
    try:
        data = (runs_directory(primary) / run_id / "host.out").read_bytes()
    except OSError:
        return ""
    return data[-4000:].decode("utf-8", "replace").strip()


def lost_link(
    primary: Path, workflow: str, task: str, key: str, operation: str, run_id: str
):
    output = host_output(primary, run_id)
    directory = (runs_directory(primary) / run_id).as_posix()
    return workflow_link(
        workflow,
        task,
        "step_lost",
        f"the {operation} run {run_id} of step {key} has no result and its host no longer "
        "runs; it ended without writing its result",
        reason="environment",
        explanation="the workflow cannot recover a run whose host ended without a result",
        evidence=[
            errors.evidence("run", directory, ""),
            errors.evidence("host-output", f"{directory}/host.out", output[-2000:]),
        ],
        options=[
            f"read the host output, then run the step again with retry for {store.base_key(key)}"
        ],
        causes=[
            errors.link(
                "component",
                f"Operation host of {run_id}",
                "host_ended",
                "the host ended without a result; its output ends with: "
                + (output or "(nothing)"),
                reason="environment",
                explanation="a host that fails outside its provider steps writes only its "
                "output, not a result",
            )
        ],
    )


def running_run(primary: Path, record: dict) -> str | None:
    """A run of the task still running with a living host, if any."""
    for run in record.get("runs") or []:
        if run.get("status") == "running" and pid_alive(int(run.get("host_pid") or 0)):
            return run["run_id"]
    return None


@contextmanager
def step_lock(primary: Path, task: str):
    """The task's step lock, held while a key is looked up, started and recorded."""
    path = store.tasks_directory(primary) / f"{task}.workflow.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def concorde_command(worktree: Path) -> list[str]:
    """The task worktree's own ``concorde``: its installed command, or this checkout's script."""
    installed = worktree / ".concorde/bin/concorde"
    if installed.is_file():
        return [str(installed)]
    script = worktree / "scripts/concorde.py"
    if script.is_file():
        return [sys.executable, str(script)]
    return [sys.executable, "-m", "concorde"]


def start_run(workflow: str, task: dict, argv: list[str]) -> dict:
    """Start ``concorde run <argv> --detach`` in the task worktree; the announced run.

    ``StepError`` carries a ``step_refused`` link when ``concorde run`` rejected the command line
    (its standard error as the cause) or the detached host did not start (its link as the cause).
    """
    worktree = Path(task["worktree"])
    command = [*concorde_command(worktree), "run", *argv, "--detach"]
    environment = dict(os.environ)
    if command[1:3] == ["-m", "concorde"]:
        # This package itself: make it importable for the child.
        environment["PYTHONPATH"] = os.pathsep.join(
            [str(Path(__file__).resolve().parents[2])]
            + ([environment["PYTHONPATH"]] if environment.get("PYTHONPATH") else [])
        )
    completed = subprocess.run(
        command,
        cwd=worktree,
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
            "Operation runner (concorde run)",
            "command_refused" if completed.returncode == 2 else "run_not_started",
            f"`{shown}` exited with status {completed.returncode}: "
            f"{(completed.stderr or completed.stdout).strip() or '(no output)'}",
            reason="input" if completed.returncode == 2 else "environment",
            explanation="concorde run starts no run for a command line it cannot accept",
        )
    raise StepError(
        workflow_link(
            workflow,
            task["id"],
            "step_refused",
            f"the step's run could not start: `{shown}` exited with status "
            f"{completed.returncode}",
            reason="input",
            explanation="the workflow runs the command its procedure names and cannot correct "
            "a command line concorde run rejects or a host that does not start",
            evidence=[errors.evidence("command", shown, "")],
            options=[
                "correct the workflow script or the Operation arguments and run it again"
            ],
            causes=[cause],
        )
    )


def asking_run(primary: Path, record: dict, base: str) -> str | None:
    """The latest ok run of a base key, superseded or not: the run whose questions the answers
    settle. A retried or re-answered step supersedes the run that asked, yet still refers to it."""
    steps = ((record.get("workflow") or {}).get("steps")) or []
    for step in reversed(steps):
        if store.base_key(step["key"]) == base and step["run_id"]:
            result = load_result(primary, step["run_id"])
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


def write_answers(primary: Path, task: str, key: str, answers: list[dict]) -> str:
    folder = store.tasks_directory(primary) / f"{task}.answers"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / (key.replace(":", "_").replace("@", "-") + ".json")
    path.write_text(
        json.dumps({"answers": answers}, indent=2, ensure_ascii=False) + "\n"
    )
    return path.as_posix()


def created_modules(primary: Path, output: dict | None) -> list[dict]:
    """The Modules a scaffold created, each with the other created Modules its survey said it
    uses, in the scaffold's order."""
    if not output or "created" not in output:
        return []
    created = [item["id"] for item in output["created"]]
    survey = load_result(primary, output.get("survey_run")) or {}
    uses = {
        child["id"]: [use["target"] for use in child.get("uses", [])]
        for child in ((survey.get("output") or {}).get("children") or [])
    }
    return [
        {"id": identity, "uses": [t for t in uses.get(identity, []) if t in created]}
        for identity in created
    ]


def decision_points(operation: str, output: dict | None, settled=frozenset()) -> int:
    """Open questions, and for a survey decisions the worker took, that no answer settled."""
    if not output:
        return 0
    count = sum(
        1
        for item in output.get("open_questions") or []
        if item.get("id") not in settled
    )
    if operation == "survey":
        count += sum(
            1
            for item in output.get("decisions") or []
            if item.get("decided_by") == "worker" and item.get("id") not in settled
        )
    return count


def outcome(
    primary: Path,
    workflow: str,
    task: str,
    key: str,
    operation: str,
    run_id: str | None,
    state: str,
    error: dict | None = None,
    settled=frozenset(),
) -> dict:
    result = load_result(primary, run_id) if state == "finished" else None
    output = (result or {}).get("output")
    value = {
        "workflow": workflow,
        "task": task,
        "key": key,
        "operation": operation,
        "run_id": run_id,
        "state": state,
        "status": (result or {}).get("status"),
        "summary": (result or {}).get("summary"),
        "result_path": (
            (runs_directory(primary) / run_id / "result.json").as_posix()
            if run_id
            else None
        ),
        "decision_points": decision_points(operation, output, settled),
        "created_modules": created_modules(primary, output)
        if operation == "scaffold"
        else [],
        "ready": output.get("ready")
        if operation == "validate" and isinstance(output, dict)
        else None,
        "error": error,
    }
    if state == "lost" and error is None:
        value["error"] = lost_link(primary, workflow, task, key, operation, run_id)
    validate(value, STEP_SCHEMA)
    return value


def rejected(workflow, task_id, key, operation, refusal, *, started: str | None = None):
    """The ``step_rejected`` outcome of a step Tasks refused, with its refusal as the cause."""
    if started:
        detail = (
            f"step {key} ({operation}) started run {started}, but Tasks refused to record it: "
            f"{refusal.code}: {refusal}; the run is live and unrecorded"
        )
        options = [
            f"wait for run {started} to end, then run the step again with retry",
        ]
    else:
        detail = (
            f"Tasks refused step {key} ({operation}) of task {task_id}: {refusal.code}: "
            f"{refusal}; nothing was started"
        )
        options = ["run the workflow in the task it belongs to, or open a new task"]
    return workflow_link(
        workflow,
        task_id,
        "step_unrecorded" if started else "step_rejected",
        detail,
        reason="environment" if started else "input",
        explanation="the workflow cannot record a step the task does not accept",
        evidence=[errors.evidence("run", started, "")] if started else [],
        causes=[
            errors.link(
                "component",
                "Tasks",
                refusal.code,
                str(refusal),
                reason="input",
                explanation="Tasks refuses a step whose task, workflow or key does not "
                "admit it",
            )
        ],
        options=options,
    )


def run_step(
    primary: Path, request: dict, wait: float | None = WAIT
) -> tuple[int, dict]:
    """Start or await one step; the exit status (0 finished, 3 running, 1 otherwise) and the
    outcome. ``wait`` None waits until the run has finished or is lost."""
    workflow, task_id, mode = request["workflow"], request["task"], request["mode"]
    operation = request["argv"][0]
    answers = request["answers"]
    key = step_key(request["key"], answers, request["restart"])
    settled = frozenset(item["id"] for item in answers or [])
    deadline = None if wait is None else time.monotonic() + wait

    def refused(link: dict, run_id: str | None = None) -> tuple[int, dict]:
        return 1, outcome(
            primary, workflow, task_id, key, operation, run_id, "refused", link, settled
        )

    started = None
    try:
        with step_lock(primary, task_id):
            record = store.load_task(primary, task_id)
            store.check_workflow_step(record, workflow, key, operation)
            found = next(
                (s for s in reversed(store.current_steps(record)) if s["key"] == key),
                None,
            )
            state = run_state(primary, found["run_id"]) if found else None
            restart = found is None or (
                request["retry"]
                and state in ("finished", "lost", "refused")
                and (load_result(primary, found["run_id"]) or {}).get("status") != "ok"
            )
            if not restart:
                run_id = found["run_id"]
                if run_id is None:
                    return refused(found.get("error"))
            else:
                # One Operation of a task at a time: wait for a run still going, such as the
                # previous step's whose host is finishing, before starting this one.
                while running_run(primary, record) is not None:
                    if deadline is not None and time.monotonic() >= deadline:
                        return 3, outcome(
                            primary,
                            workflow,
                            task_id,
                            key,
                            operation,
                            None,
                            "running",
                            None,
                            settled,
                        )
                    time.sleep(POLL)
                    record = store.load_task(primary, task_id)
                argv = [operation, "--task", task_id, *request["argv"][1:]]
                path = None
                if answers:
                    path = write_answers(primary, task_id, key, answers)
                    argv += ["--answers", path]
                    asked = asking_run(primary, record, request["key"])
                    if asked:
                        argv += ["--input", asked]
                try:
                    announced = start_run(workflow, record, argv)
                    run_id, error = announced["run_id"], None
                except StepError as refusal:
                    run_id, error = None, refusal.link
                started = run_id
                store.record_workflow_step(
                    primary,
                    task_id,
                    workflow,
                    key,
                    operation,
                    run_id,
                    mode,
                    path,
                    error,
                )
                if error is not None:
                    return refused(error)
    except store.TaskError as refusal:
        return refused(
            rejected(workflow, task_id, key, operation, refusal, started=started),
            started,
        )
    while True:
        state = run_state(primary, run_id)
        if state != "running" or (
            deadline is not None and time.monotonic() >= deadline
        ):
            break
        time.sleep(POLL)
    value = outcome(
        primary, workflow, task_id, key, operation, run_id, state, None, settled
    )
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
    "load_result",
    "run_state",
    "run_step",
    "step_key",
    "workflow_link",
]
