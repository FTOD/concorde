"""``concorde run``: the Operation host's runner (see the Operations host Spec).

1. Parse the command line and look up the catalog entry; only then create the run.
2. Resolve the task and its worktree, or without ``--task`` the primary worktree (refused in a
   task worktree);
   check ``--modules`` and ``--input``.
3. Begin the run in the task record (a run without a task has none).
4. Execute the provider's steps in order.
5. Compose and check the envelope.
6. Finish the run in the task record, write ``result.json``, print the envelope and exit.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import re
import secrets
import signal
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

from .. import errors
from ..spec.schema import ContractError, validate
from ..tasks import store
from .catalog import CATALOG, provider
from .provider import Continue, RunContext, Stop, component, evidence

RESULT_SCHEMA: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "operation",
        "task",
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
        "operation": {"type": "string", "pattern": "^[a-z][a-z_]*$"},
        "task": {"anyOf": [{"type": "null"}, {"type": "string", "minLength": 1}]},
        "modules": {"type": "array", "items": {"type": "string", "minLength": 1}},
        "run_id": {
            "type": "string",
            "pattern": "^r-[0-9]{8}T[0-9]{6}-[a-z_]+-[0-9a-f]{8}$",
        },
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

# How the runner treats a refusal of Tasks before the run begins.
REFUSALS = {
    "task_busy": (
        "decision",
        "one task runs one Operation at a time; waiting for the running Operation or "
        "cancelling it is the main agent's decision",
        [
            "wait for the running Operation to finish",
            "cancel it, then run this one again",
        ],
    ),
    "modules_removed": (
        "input",
        "the task names only Modules its branch removed or renamed, and which of its current "
        "Modules the run works on is for the caller to name",
        ["run the Operation again naming the task's current Modules with --modules"],
    ),
    "specs_unloadable": (
        "scope",
        "the Operation needs the task worktree's Specs to load and never repairs them",
        [
            "run validate for the task to see why the Specs do not load",
            "repair the Specs by hand",
        ],
    ),
}
INPUT_REFUSAL = (
    "input",
    "the task, Modules or inputs named on the command line are refused and only the caller "
    "can correct them",
    ["correct the command line and run the Operation again"],
)


class Cancelled(Exception):
    pass


def now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def run_id(operation: str) -> str:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
    return f"r-{stamp}-{operation}-{secrets.token_hex(4)}"


RUN_ID = re.compile(RESULT_SCHEMA["properties"]["run_id"]["pattern"])
# How long ``--detach`` waits for the detached host to write its progress file.
DETACH_WAIT = 60.0
# The environment variable through which a detaching parent hands the host its run identity.
RUN_ID_VARIABLE = "CONCORDE_RUN_ID"


class UsageError(Exception):
    """A malformed command line; no run is created."""


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise UsageError(f"{self.prog}: {message}")


def parse(argv) -> tuple[argparse.Namespace, object]:
    """The parsed command line and the provider; ``UsageError`` names what is wrong."""
    words = list(argv)
    if not words:
        raise UsageError("no Operation named")
    if words[0] not in CATALOG:
        raise UsageError(f"unknown Operation {words[0]!r}")
    name = words[0]
    try:
        chosen = provider(name)
    except (ImportError, AttributeError) as error:
        raise UsageError(
            f"the provider of {name} cannot be loaded: {errors.exception_detail(error)}"
        ) from error
    command = _Parser(prog=f"concorde run {name}")
    command.add_argument("--task", required=chosen.task_scope == "required")
    command.add_argument("--modules")
    command.add_argument("--input", action="append", default=[])
    command.add_argument("--detach", action="store_true")
    if chosen.add_arguments:
        chosen.add_arguments(command)
    return command.parse_args(words[1:]), chosen


def _inputs(primary: Path, task: dict, requested: list[str]) -> dict[str, dict]:
    admitted = {}
    runs = {run["run_id"]: run for run in task["runs"]}
    for identity in requested:
        run = runs.get(identity)
        path = primary / ".concorde/runs" / identity / "result.json"
        if run is None:
            known = ", ".join(sorted(runs)) or "none"
            raise store.TaskError(
                "input_not_admissible",
                f"--input {identity} is not a run of task {task['id']} (its runs: {known})",
            )
        if run["status"] != "ok":
            raise store.TaskError(
                "input_not_admissible",
                f"--input {identity} ({run['operation']}) ended {run['status']}; only an ok "
                "run's output is admitted",
            )
        if not path.is_file():
            raise store.TaskError(
                "input_not_admissible",
                f"--input {identity} has no saved result at {path}",
            )
        result = json.loads(path.read_text())
        admitted[identity] = {
            "operation": result["operation"],
            "output": result["output"],
        }
    return admitted


def _project_inputs(primary: Path, requested: list[str]) -> dict[str, dict]:
    """The outputs of earlier ``ok`` runs without a task, for a run without a task."""
    admitted = {}
    for identity in requested:
        path = primary / ".concorde/runs" / identity / "result.json"
        try:
            result = json.loads(path.read_text())
        except (OSError, ValueError) as error:
            raise store.TaskError(
                "input_not_admissible",
                f"--input {identity} has no readable result at {path}: {error}",
            ) from error
        if result.get("task") is not None:
            raise store.TaskError(
                "input_not_admissible",
                f"--input {identity} belongs to task {result['task']}; a run without a task "
                "admits only runs without a task",
            )
        if result.get("status") != "ok":
            raise store.TaskError(
                "input_not_admissible",
                f"--input {identity} ({result.get('operation')}) ended {result.get('status')}; "
                "only an ok run's output is admitted",
            )
        admitted[identity] = {
            "operation": result["operation"],
            "output": result["output"],
        }
    return admitted


def _named_modules(arguments) -> list[str] | None:
    if not arguments.modules:
        return None
    return [item.strip() for item in arguments.modules.split(",") if item.strip()]


def _task_modules(chosen, context: RunContext, task: dict) -> list[str]:
    """The task record's Modules the task worktree still registers.

    A Module the task branch removed or renamed stays in the record, which only grows; the run
    leaves it out with ``removed-module`` evidence. When the worktree's Specs do not load, the
    record's list is kept whole: the Module check of step 3, or the provider itself, reports why.
    """
    modules = list(task["modules"])
    try:
        kept, removed = store.current_modules(context.worktree, modules)
    except store.TaskError:
        return modules
    if removed and not kept:
        raise store.TaskError(
            "modules_removed",
            f"every Module task {task['id']} names ({', '.join(removed)}) is no longer "
            f"registered in its worktree {context.worktree}: the task branch removed or "
            "renamed them, so the run has no Module to work on; name the task's current "
            "Modules with --modules",
        )
    for module in removed:
        context.evidence.append(
            evidence(
                "removed-module",
                module,
                f"task {task['id']} names {module}, which its worktree no longer registers: "
                f"the task branch removed or renamed it, so {chosen.name} leaves it out",
            )
        )
    return kept


def _resolve_task(chosen, context: RunContext, primary: Path, arguments) -> None:
    """Steps 2 and 3 for a run of a task: its worktree, Modules and inputs; begin the run."""
    task = store.load_task(primary, arguments.task)
    context.task = task
    context.worktree = Path(task["worktree"])
    if not context.worktree.is_dir():
        raise store.TaskError("missing_worktree", f"{context.worktree} does not exist")
    context.modules = _named_modules(arguments) or _task_modules(chosen, context, task)
    context.inputs = _inputs(primary, task, arguments.input)
    store.begin_run(
        primary,
        task["id"],
        context.run_id,
        chosen.name,
        context.modules,
        chosen.writes,
        os.getpid(),
        check_modules=chosen.requires_loaded_specs,
    )


def _resolve_project(
    chosen, context: RunContext, primary: Path, here: Path, arguments
) -> Stop | None:
    """Step 2 for a run without a task: the primary worktree, and no task record.

    A task worktree is refused: a run there without its task would read the task's files without
    the task's one-run-at-a-time lock, so a concurrent writing run would break its audit.
    """
    context.task = {}
    worktree = store.worktree_of(here)
    context.worktree = worktree
    if worktree != primary:
        owner = next(
            (
                task["id"]
                for task in store.list_tasks(primary)
                if Path(task.get("worktree") or "") == worktree
            ),
            None,
        )
        hint = f"--task {owner}" if owner else "--task <the task of this worktree>"
        return context.fail(
            "failed",
            "task_worktree_without_task",
            f"{chosen.name} without a task runs only in the primary worktree; pass {hint}.",
            f"{chosen.name} was started without --task in {worktree}, which is "
            + (f"the worktree of task {owner}" if owner else "not the primary worktree")
            + f", not in the primary worktree {primary}",
            reason="input",
            explanation="a run without a task works only on the primary worktree; in a task's "
            "worktree it must run as a run of that task, so the task's lock keeps a "
            "concurrent writing run from breaking its audit",
            evidence=[evidence("refused", "task_worktree_without_task", str(worktree))],
            options=[
                f"run it again with {hint}",
                f"run it from the primary worktree {primary} to work on the merged project",
            ],
            recommendation=f"run it again with {hint}",
        )
    context.modules = _named_modules(arguments) or []
    if context.modules and chosen.requires_loaded_specs:
        store.registered(context.worktree, context.modules)
    context.inputs = _project_inputs(primary, arguments.input)
    return None


def _primary(here: Path) -> Path:
    try:
        return store.primary_of(here)
    except Exception as error:  # noqa: BLE001 -- not a Git repository
        raise UsageError(
            f"{here} is not inside a Git repository: {errors.exception_detail(error)}"
        ) from None


def execute(
    argv, cwd: Path | None = None, identity: str | None = None
) -> tuple[int, dict]:
    """Run one Operation; return the exit status and the envelope; ``UsageError`` otherwise.

    ``identity`` is the run identity a detaching parent chose and announced; its run directory
    may already exist, holding the detached host's own output files.
    """
    arguments, chosen = parse(argv)
    here = Path(os.path.realpath(cwd or Path.cwd()))
    primary = _primary(here)
    if identity is not None and not RUN_ID.match(identity):
        raise UsageError(f"invalid run identity {identity!r}")
    identity = identity or run_id(chosen.name)
    run_dir = primary / ".concorde/runs" / identity
    run_dir.mkdir(parents=True, exist_ok=True)
    started = now()
    context = RunContext(
        operation=chosen.name,
        primary=primary,
        task={"id": arguments.task},
        worktree=here,
        modules=[],
        run_id=identity,
        run_dir=run_dir,
        arguments=arguments,
        roles=chosen.roles,
    )
    begun = False
    stop: Stop | None = None
    _progress(context, phase="running", step=None)
    previous = {
        sig: signal.signal(sig, _cancel) for sig in (signal.SIGINT, signal.SIGTERM)
    }
    try:
        try:
            if arguments.task:
                _resolve_task(chosen, context, primary, arguments)
                begun = True
            else:
                stop = _resolve_project(chosen, context, primary, here, arguments)
        except store.TaskError as refusal:
            reason, explanation, options = REFUSALS.get(refusal.code, INPUT_REFUSAL)
            stop = context.fail(
                "failed",
                "refused",
                f"The run was refused before it began: {refusal.code}: {refusal}",
                f"{chosen.name} was refused before it began: {refusal.code}: {refusal}",
                reason=reason,
                explanation=explanation,
                evidence=[evidence("refused", refusal.code, str(refusal))],
                causes=[
                    component(
                        "Tasks",
                        refusal.code,
                        str(refusal),
                        "input",
                        "Tasks refuses a run whose task, Modules or state do not admit it",
                    )
                ],
                options=options,
            )
        if stop is None:
            stop = _steps(chosen, context)
    except Cancelled as cancelled:
        stop = context.fail(
            "failed",
            "cancelled",
            "The run was cancelled.",
            f"{chosen.name} received {cancelled} before it finished; the worker processes it "
            "started were ended",
            reason="environment",
            explanation="a signal from outside ended the run; the host does not resume it",
            evidence=[evidence("cancelled", "", str(cancelled))],
            options=["run the Operation again"],
        )
    finally:
        for sig, handler in previous.items():
            signal.signal(sig, handler)
    envelope = _envelope(chosen, context, stop, started)
    # The run is finished in the task record before its result exists, so whoever sees the
    # result (a workflow step waiting for it) also sees a task free for its next run.
    if begun:
        try:
            store.finish_run(primary, context.task["id"], identity, envelope["status"])
        except store.TaskError as error:
            envelope["host_evidence"].append(evidence("record", error.code, str(error)))
    (run_dir / "result.json").write_text(json.dumps(envelope, indent=2) + "\n")
    _progress(
        context,
        phase="finished",
        step=None,
        status=envelope["status"],
        summary=envelope["summary"],
    )
    return (0 if envelope["status"] == "ok" else 1), envelope


def _progress(context: RunContext, **fields) -> None:
    """Rewrite the run's progress file ``status.json``; a failed write never changes the run."""
    path = context.run_dir / "status.json"
    try:
        state = json.loads(path.read_text()) if path.exists() else {}
    except (OSError, ValueError):
        state = {}
    state.update(
        kind="operation",
        run_id=context.run_id,
        operation=context.operation,
        task=context.task.get("id"),
        modules=context.modules,
        host_pid=os.getpid(),
        updated_at=now(),
        **fields,
    )
    state.setdefault("started_at", state["updated_at"])
    state.setdefault("phase", "running")
    state.setdefault("status", None)
    temporary = path.with_suffix(".json.tmp")
    try:
        temporary.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")
        temporary.replace(path)
    except OSError:
        pass


def _cancel(signum, frame):
    raise Cancelled(signal.Signals(signum).name)


def _steps(chosen, context: RunContext) -> Stop | None:
    for step in chosen.steps:
        _progress(context, step=step.__name__)
        try:
            outcome = step(context)
        except Cancelled:
            raise
        except Exception as error:  # noqa: BLE001 -- a step error is a failed result
            return context.exception(
                f"host step {step.__name__}",
                error,
                "host_error",
                f"The step {step.__name__} raised {type(error).__name__}: {error}",
            )
        context.evidence.extend(outcome.evidence)
        if isinstance(outcome, Continue):
            if outcome.output is not None:
                context.output = outcome.output
            continue
        return outcome
    return None


def _envelope(chosen, context: RunContext, stop: Stop | None, started: str) -> dict:
    evidence_list = list(context.evidence)
    if stop is not None:
        evidence_list.extend(
            item for item in stop.evidence if item not in evidence_list
        )
    status = stop.status if stop is not None else "ok"
    summary = (
        stop.summary
        if stop is not None
        else f"{chosen.name} finished for {', '.join(context.modules)}."
        if context.modules
        else f"{chosen.name} finished."
    )
    error = None if status == "ok" else (stop.error if stop else None)
    if status != "ok" and error is None:
        error = context.fail(
            status,
            "missing_error",
            summary,
            f"the step that stopped the run with status {status} gave no error: {summary}",
            reason="capability",
            explanation="the host cannot reconstruct an error the step did not report",
        ).error
    envelope = {
        "operation": chosen.name,
        "task": context.task.get("id") or None,
        "modules": context.modules,
        "run_id": context.run_id,
        "status": status,
        "summary": summary,
        "output": context.output,
        "worker": context.worker,
        "worker_runs": context.worker_runs,
        "host_evidence": evidence_list,
        "error": error,
        "started_at": started,
        "finished_at": now(),
    }
    try:
        validate(envelope, RESULT_SCHEMA)
        if status == "ok" and chosen.output_schema is not None:
            validate(envelope["output"], chosen.output_schema)
    except ContractError as problem:
        invalid = evidence("invalid-output", problem.field, str(problem))
        envelope["host_evidence"].append(invalid)
        envelope.update(
            status="failed",
            summary=f"The run produced an invalid result: {problem}",
            output=None,
            error=context.fail(
                "failed",
                "invalid_result",
                "invalid result",
                f"the result of {chosen.name} does not satisfy the result contract or the "
                f"provider's output contract: {problem}",
                reason="capability",
                explanation="the host never returns a result that breaks its contract and "
                "cannot repair one",
                evidence=[invalid],
                causes=[error] if isinstance(error, dict) and "level" in error else [],
                options=["report an Issue against the provider"],
            ).error,
        )
    return envelope


SOURCE_ROOT = Path(__file__).resolve().parents[2]


def detach(
    argv, cwd: Path | None = None, wait: float = DETACH_WAIT
) -> tuple[int, dict]:
    """``concorde run --detach``: start the host as a process of its own and announce the run.

    The command line is checked first, so a malformed one starts nothing (``UsageError``). The
    run identity is chosen here and handed to the host, which writes its progress file as its
    first act; this returns once that file exists, with status 0 and the run's identity and
    result path, or with status 1 and an error link when the host ended or stayed silent
    before writing it.
    """
    words = [word for word in argv if word != "--detach"]
    _, chosen = parse(words)
    here = Path(os.path.realpath(cwd or Path.cwd()))
    primary = _primary(here)
    identity = run_id(chosen.name)
    run_dir = primary / ".concorde/runs" / identity
    run_dir.mkdir(parents=True)
    environment = dict(os.environ, **{RUN_ID_VARIABLE: identity})
    environment["PYTHONPATH"] = os.pathsep.join(
        [str(SOURCE_ROOT)]
        + ([environment["PYTHONPATH"]] if environment.get("PYTHONPATH") else [])
    )
    output = run_dir / "host.out"
    with output.open("wb") as stream:
        process = subprocess.Popen(
            [sys.executable, "-m", "concorde.operations.host", *words],
            cwd=here,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=stream,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    progress = run_dir / "status.json"
    result = run_dir / "result.json"
    deadline = time.monotonic() + wait
    while not progress.exists():
        if process.poll() is not None or time.monotonic() > deadline:
            break
        time.sleep(0.05)
    announced = {
        "run_id": identity,
        "operation": chosen.name,
        "host_pid": process.pid,
        "progress": progress.as_posix(),
        "result": result.as_posix(),
    }
    if progress.exists():
        return 0, announced
    ended = process.poll()
    if ended is None:
        # A host that did not announce itself in time must not start the Operation later,
        # unrecorded by whoever asked for it.
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except OSError:
            pass
        process.wait()
    tail = output.read_bytes()[-4000:].decode("utf-8", "replace").strip()
    detail = (
        f"the detached host of {chosen.name} (process {process.pid}) "
        + (
            f"exited with status {ended}"
            if ended is not None
            else f"wrote no progress file within {wait:.0f} seconds"
        )
        + f" before announcing run {identity}; its output ends with: {tail or '(nothing)'}"
    )
    return 1, {
        **announced,
        "error": errors.link(
            "component",
            "Operation runner (concorde run --detach)",
            "detach_failed",
            detail,
            reason="environment",
            explanation="the runner only starts the detached host; it cannot repair a host "
            "that ends or hangs before its first write",
            evidence=[errors.evidence("host-output", output.as_posix(), "")],
            options=[
                "run the same command without --detach to see the host fail directly"
            ],
        ),
    }


def main(argv) -> int:
    argv = list(argv)
    if "--detach" in argv:
        try:
            status, announced = detach(argv)
        except UsageError as error:
            sys.stderr.write(f"concorde run: {error}\n")
            return 2
        sys.stdout.write(json.dumps(announced, indent=2) + "\n")
        return status
    try:
        status, envelope = execute(argv, identity=os.environ.pop(RUN_ID_VARIABLE, None))
    except UsageError as error:
        sys.stderr.write(
            f"concorde run: {error}\nusage: concorde run <operation> [--task <task-id>] "
            f"[--modules ids] [--input run-id]... ; operations: {', '.join(CATALOG)}\n"
        )
        return 2
    except Exception as error:  # noqa: BLE001 -- the runner itself failed; say exactly how
        link = errors.from_exception(
            "Operation runner (concorde run)",
            error,
            explanation="the runner failed outside every provider step, so no result could "
            "be written",
        )
        sys.stderr.write("concorde run failed:\n" + errors.render(link) + "\n")
        return 1
    sys.stdout.write(json.dumps(envelope, indent=2) + "\n")
    if envelope["error"] is not None:
        sys.stderr.write(
            f"{envelope['operation']} ended {envelope['status']}: {envelope['summary']}\n"
            + errors.render(envelope["error"])
            + "\n"
        )
    return status


__all__ = ["RESULT_SCHEMA", "UsageError", "execute", "main"]


if __name__ == "__main__":  # the detached host started by ``detach``
    sys.exit(main(sys.argv[1:]))
