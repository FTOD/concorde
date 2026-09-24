"""``concorde run``: the Operation host's runner (see the Operations host Spec).

1. Parse the command line and look up the catalog entry; only then create the run.
2. Resolve the task and its worktree; check ``--modules`` and ``--input``.
3. Begin the run in the task record.
4. Execute the provider's steps in order.
5. Compose and check the envelope.
6. Write ``result.json``, finish the run in the task record, print the envelope and exit.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import secrets
import signal
import sys
from datetime import datetime, timezone
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
        "task": {"type": "string", "minLength": 1},
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
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run_id(operation: str) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    return f"r-{stamp}-{operation}-{secrets.token_hex(4)}"


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
    command.add_argument("--task", required=True)
    command.add_argument("--modules")
    command.add_argument("--input", action="append", default=[])
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


def execute(argv, cwd: Path | None = None) -> tuple[int, dict]:
    """Run one Operation; return the exit status and the envelope; ``UsageError`` otherwise."""
    arguments, chosen = parse(argv)
    here = Path(os.path.realpath(cwd or Path.cwd()))
    try:
        primary = store.primary_of(here)
    except Exception as error:  # noqa: BLE001 -- not a Git repository
        raise UsageError(
            f"{here} is not inside a Git repository: {errors.exception_detail(error)}"
        ) from None
    identity = run_id(chosen.name)
    run_dir = primary / ".concorde/runs" / identity
    run_dir.mkdir(parents=True)
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
    )
    begun = False
    stop: Stop | None = None
    previous = {
        sig: signal.signal(sig, _cancel) for sig in (signal.SIGINT, signal.SIGTERM)
    }
    try:
        try:
            task = store.load_task(primary, arguments.task)
            context.task = task
            context.worktree = Path(task["worktree"])
            if not context.worktree.is_dir():
                raise store.TaskError(
                    "missing_worktree", f"{context.worktree} does not exist"
                )
            modules = (
                [item.strip() for item in arguments.modules.split(",") if item.strip()]
                if arguments.modules
                else list(task["modules"])
            )
            context.modules = modules
            context.inputs = _inputs(primary, task, arguments.input)
            store.begin_run(
                primary,
                task["id"],
                identity,
                chosen.name,
                modules,
                chosen.writes,
                os.getpid(),
                check_modules=chosen.requires_loaded_specs,
            )
            begun = True
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
    (run_dir / "result.json").write_text(json.dumps(envelope, indent=2) + "\n")
    if begun:
        try:
            store.finish_run(primary, context.task["id"], identity, envelope["status"])
        except store.TaskError as error:
            envelope["host_evidence"].append(evidence("record", error.code, str(error)))
            (run_dir / "result.json").write_text(json.dumps(envelope, indent=2) + "\n")
    return (0 if envelope["status"] == "ok" else 1), envelope


def _cancel(signum, frame):
    raise Cancelled(signal.Signals(signum).name)


def _steps(chosen, context: RunContext) -> Stop | None:
    for step in chosen.steps:
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
        "task": context.task.get("id", "?"),
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


def main(argv) -> int:
    try:
        status, envelope = execute(argv)
    except UsageError as error:
        sys.stderr.write(
            f"concorde run: {error}\nusage: concorde run <operation> --task <task-id> "
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
