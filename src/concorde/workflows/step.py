"""``concorde workflow step``: start or await one keyed run of a workflow in its workspace.

A step key names one run of the bound workspace: an Operation, or an execution command such as
``task-validation``, ``delivery`` or ``scaffold``. The first call for a key starts the run
detached, with the workspace's own ``concorde``, and records it in the workspace's workflow record;
every later call finds the recorded run and only waits for it, so repeating a call or relaunching a
whole workflow never starts a run twice. The step is recorded as starting before its run is
launched, so a call that finds it still starting, because the command that launched the run ended
before recording it, adopts the run found in the step's node instead of starting another. Answers
make a new key (the base key, ``@`` and a digest of the answers), are written next to the workflow
record and passed to the run with the run that asked them as ``--input``. Starting a new run for a
base key supersedes the steps recorded after it (see ``store.record_step``). The outcome is built
from the workflow record and the saved run result, never from what a caller relayed.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

from ..kernel import errors
from ..execution.commands.catalog import COMMANDS
from ..execution.runs import (
    RUN_ID_PATTERN,
    Store,
    load_result,
    lock_holder,
    result_path,
    run_state,
    waiting_runs,
)
from ..kernel.refusal import KernelError
from ..kernel.schema import validate
from ..kernel.tracing import locks
from . import store
from .output import ANSWER, BLOCKING, declared, pending
from .store import WorkflowError, Workspace, WorkspaceRetired

WAIT = 540.0
POLL = 0.5
# How long a run's launch is waited for: the detached runner's announcement, which Execution waits
# for at most 60 seconds before it ends the runner, and some time to start the launcher itself.
LAUNCH_WAIT = 90.0
KEY_PATTERN = "^[a-z][a-z0-9_:.-]*$"
# contract.workflows.step-request, version 7
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
NAME = {"type": "string", "pattern": "^[a-z][a-z_-]*$"}
# contract.workflows.step, version 7
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
        "blocking",
        "data",
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
        "blocking": {"anyOf": [{"type": "null"}, BLOCKING]},
        "data": {"type": "object"},
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


def run_folder(store: Store, run_id: str) -> Path:
    """The trace node folder of a step's run."""
    return store.find(run_id) or store.run_folder(run_id)


def host_output(store: Store, run_id: str) -> str:
    """The end of what a detached runner printed, where it reports failures outside its steps."""
    try:
        data = (run_folder(store, run_id) / "host.out").read_bytes()
    except OSError:
        return ""
    return data[-4000:].decode("utf-8", "replace").strip()


def lost_link(space: Workspace, workflow: str, key: str, name: str, run_id: str):
    output = host_output(space.store, run_id)
    directory = run_folder(space.store, run_id).as_posix()
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


def unstarted_link(space: Workspace, workflow: str, key: str, name: str) -> dict:
    """The ``step_lost`` link of a step recorded as starting whose run never entered its node."""
    return workflow_link(
        workflow,
        space.name,
        "step_lost",
        f"step {key} ({name}) was recorded as starting, but no run entered its node and no run "
        f"of workspace {space.name} runs: the command that started it ended before its run was "
        "announced",
        reason="environment",
        explanation="the workflow cannot tell why the command that started the step ended",
        options=[
            f"ask for step {store.base_key(key)} again, which starts its run anew"
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


def start_run(
    workflow: str, space: Workspace, argv: list[str], trace_at: Path | None = None
) -> dict:
    """Start the step's run detached in the workspace; the announced run.

    An Operation starts with ``concorde run <argv> --detach``, an execution command with
    ``concorde <argv> --detach``. ``StepError`` carries a ``step_refused`` link when the runner
    rejected the command line (its standard error as the cause), the detached runner did not
    start (its link as the cause), or the launcher could not be run or gave no answer within
    ``LAUNCH_WAIT`` seconds, when it is ended.
    """
    prefix = [] if argv[0] in COMMANDS else ["run"]
    placed = ["--trace-at", str(trace_at)] if trace_at is not None else []
    command = [*concorde_command(space.root), *prefix, *argv, *placed, "--detach"]
    environment = dict(os.environ)
    if command[1:3] == ["-m", "concorde"]:
        # This package itself: make it importable for the child.
        environment["PYTHONPATH"] = os.pathsep.join(
            [str(Path(__file__).resolve().parents[2])]
            + ([environment["PYTHONPATH"]] if environment.get("PYTHONPATH") else [])
        )
    shown = " ".join(command)
    try:
        completed = subprocess.run(
            command,
            cwd=space.root,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
            timeout=LAUNCH_WAIT,
        )
    except (OSError, subprocess.TimeoutExpired) as failure:
        ended = (
            f"gave no answer within {LAUNCH_WAIT:.0f} seconds and was ended"
            if isinstance(failure, subprocess.TimeoutExpired)
            else f"could not be run: {errors.exception_detail(failure)}"
        )
        cause = errors.link(
            "component",
            "Execution runner",
            "run_not_started",
            f"`{shown}` {ended}",
            reason="environment",
            explanation="a launcher that cannot be run or does not answer starts no run the "
            "workflow can name",
        )
        what = ended
    else:
        try:
            announced = (
                json.loads(completed.stdout) if completed.stdout.strip() else None
            )
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
        what = f"exited with status {completed.returncode}"
    raise StepError(
        workflow_link(
            workflow,
            space.name,
            "step_refused",
            f"the step's run could not start: `{shown}` {what}",
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
            result = load_result(space.store, step["run_id"])
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
    result = load_result(space.store, run_id) if state == "finished" else None
    declaration = declared((result or {}).get("output"))
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
            result_path(space.store, run_id).as_posix() if run_id else None
        ),
        "decision_points": len(pending(declaration, settled)),
        "blocking": declaration["blocking"],
        "data": declaration["data"],
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
            f"step {key} ({name}) started run {started}, but its workflow record could not "
            f"record it: {refusal.code}: {refusal}; the step stays recorded as starting, and "
            "asking for it again adopts the run from the step's node"
        )
        options = [
            f"ask for step {store.base_key(key)} again, which adopts run {started}"
        ]
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
                reason="environment" if started else "input",
                explanation="the workflow record could not be written"
                if started
                else "the workflow record refuses a step whose workflow or key does not "
                "admit it",
            )
        ],
        options=options,
    )


def retired(
    space: Workspace,
    workflow,
    key,
    name,
    refusal: WorkspaceRetired,
    *,
    run_id: str | None = None,
):
    """The ``workspace_retired`` outcome of a step whose workspace was retired while it waited for
    the workflow lock, with what the lock showed as the cause; nothing of it is recorded."""
    if run_id:
        detail = (
            f"step {key} ({name}) started run {run_id}, but its workspace {space.name} was "
            f"retired before the step could end its node: {refusal}; nothing more was written"
        )
    else:
        detail = (
            f"step {key} ({name}) was refused, since its workspace {space.name} was retired: "
            f"{refusal}; nothing was started or recorded"
        )
    return workflow_link(
        workflow,
        space.name,
        "workspace_retired",
        detail,
        reason="environment",
        explanation="a workflow writes its records only into the folder of a workspace that is "
        "still bound, and a retired workspace's folder has moved where nothing writes any more",
        evidence=[errors.evidence("run", run_id, "")] if run_id else [],
        options=[
            "run the workflow again in a worktree that is bound now, such as the worktree of "
            "an open task"
        ],
        causes=[
            errors.link(
                "component",
                "Workflows (workflow lock)",
                refusal.found,
                str(refusal),
                reason="environment",
                explanation="the workflow lock is held only on the lock file of a workspace "
                "whose binding is still the one the command read",
            )
        ],
    )


def busy(space: Workspace) -> bool:
    """Whether a run of the workspace holds its workspace lock or waits in the lobby for it."""
    return lock_holder(space.store, space.name) is not None or bool(
        waiting_runs(space.store, space.name)
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

    def left() -> float | None:
        return None if deadline is None else max(0.0, deadline - time.monotonic())

    def refused(link: dict, run_id: str | None = None) -> tuple[int, dict]:
        return 1, outcome(space, workflow, key, name, run_id, "refused", link, settled)

    def waiting() -> tuple[int, dict]:
        # Nothing was started by this call: asking again waits again.
        return 3, outcome(space, workflow, key, name, None, "running", None, settled)

    started = None
    try:
        while True:
            # A step still starting whose run has not entered its node yet.
            pending = None
            try:
                with store.step_lock(space, left()):
                    record = store.load(space)
                    store.check_step(space, record, workflow, key, name)
                    found = next(
                        (
                            s
                            for s in reversed(store.current_steps(record))
                            if s["key"] == key
                        ),
                        None,
                    )
                    if (
                        found is not None
                        and store.starting(found)
                        and store.adopt(space, found) is None
                    ):
                        # The command that started the step ended before it recorded the run.
                        # A run of the workspace may still be entering the step's node: wait.
                        # Otherwise its run never started, and it is started anew.
                        if busy(space):
                            pending = found
                        else:
                            store.end_step(
                                space,
                                found,
                                "lost",
                                None,
                                unstarted_link(space, workflow, key, name),
                            )
                            found = None
                    if pending is None:
                        state = (
                            run_state(space.store, found["run_id"]) if found else None
                        )
                        restart = found is None or (
                            request["retry"]
                            and state in ("finished", "lost", "refused")
                            and (load_result(space.store, found["run_id"]) or {}).get(
                                "status"
                            )
                            != "ok"
                        )
                        if not restart:
                            run_id = found["run_id"]
                            if run_id is None:
                                return refused(found.get("error"))
                            break
                    # One run of a workspace at a time: a run still holding the workspace, such
                    # as the previous step's whose runner is finishing, is waited for below.
                    if pending is None and not busy(space):
                        argv = list(request["argv"])
                        path = None
                        if answers:
                            path = store.write_answers(space, key, answers)
                            argv += ["--answers", path]
                            asked = asking_run(space, record, request["key"])
                            if asked:
                                argv += ["--input", asked]
                        # The step is recorded as starting, with its node, before its run is
                        # launched and placed inside that node.
                        folder = store.next_step_folder(space, record, key)
                        folder.mkdir(parents=True, exist_ok=True)
                        store.record_step(
                            space, workflow, key, name, mode, path, folder=folder
                        )
                        try:
                            announced = start_run(workflow, space, argv, folder / "run")
                            run_id, error = announced["run_id"], None
                        except StepError as refusal:
                            run_id, error = None, refusal.link
                        started = run_id
                        node = folder.relative_to(space.directory).as_posix()
                        store.set_run(space, node, run_id, error)
                        if error is not None:
                            return refused(error)
                        break
            except locks.LockBusy:
                # Another step or report command held the workflow lock until the bound ended.
                return waiting()
            # The workspace lock is waited for without the workflow lock, which is a leaf: a
            # close holding the workspace lock takes the workflow lock before it moves the
            # workspace folder. The key is looked up again once the workspace is free, or once
            # the run of a starting step has entered its node.
            while busy(space) and (
                pending is None or store.node_run(space, pending) is None
            ):
                if deadline is not None and time.monotonic() >= deadline:
                    return waiting()
                time.sleep(POLL if deadline is None else min(POLL, left()))
    except WorkspaceRetired as refusal:
        return refused(retired(space, workflow, key, name, refusal))
    except WorkflowError as refusal:
        return refused(
            rejected(space, workflow, key, name, refusal, started=started), started
        )
    while True:
        state = run_state(space.store, run_id)
        if state != "running" or (
            deadline is not None and time.monotonic() >= deadline
        ):
            break
        time.sleep(POLL if deadline is None else min(POLL, left()))
    if state in ("finished", "lost"):
        try:
            _end_step_node(space, workflow, key, name, run_id, state)
        except WorkspaceRetired as refusal:
            return refused(
                retired(space, workflow, key, name, refusal, run_id=run_id), run_id
            )
    value = outcome(space, workflow, key, name, run_id, state, None, settled)
    return {"finished": 0, "running": 3}.get(state, 1), value


# What an omitted optional field of a step request means. A step agent that retypes a request
# has less to copy when the script leaves these out.
REQUEST_DEFAULTS = {"answers": None, "retry": False, "restart": None}


def check_request(request) -> dict:
    """The request with its defaults if it satisfies its contract; ``KernelError`` otherwise."""
    validate(request, REQUEST_SCHEMA)
    # The schema dialect cannot restrict the first item alone: the name of an Operation or
    # command, as a step outcome and the workflow record name it.
    if not re.match(NAME["pattern"], request["argv"][0]):
        raise KernelError(
            "invalid_field",
            f"argv[0] {request['argv'][0]!r} is no Operation or command name: it must match "
            f"{NAME['pattern']}",
            field="/argv/0",
        )
    return {**REQUEST_DEFAULTS, **request}


__all__ = [
    "REQUEST_SCHEMA",
    "STEP_SCHEMA",
    "StepError",
    "answers_digest",
    "busy",
    "check_request",
    "run_step",
    "step_key",
    "unstarted_link",
    "workflow_link",
]


def _end_step_node(
    space: Workspace, workflow: str, key: str, name: str, run_id: str, state: str
) -> None:
    """End the step's trace node once its run finished or was lost."""
    with store.step_lock(space):
        record = store.load(space)
        for step in reversed((record or {}).get("steps", [])):
            if step["key"] == key and step["run_id"] == run_id:
                lost = (
                    lost_link(space, workflow, key, name, run_id)
                    if state == "lost"
                    else None
                )
                store.end_step(
                    space, step, state, load_result(space.store, run_id), lost
                )
                return
