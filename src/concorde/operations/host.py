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
import json
import os
import secrets
import signal
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

from ..spec.schema import ContractError, validate
from ..tasks import store
from .catalog import CATALOG, provider
from .provider import Continue, RunContext, Stop, evidence, host_escalation

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
        "escalation",
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
        "escalation": {"anyOf": [{"type": "null"}, {"$ref": "#/$defs/escalation"}]},
        "started_at": {"type": "string", "minLength": 1},
        "finished_at": {"type": "string", "minLength": 1},
    },
    "$defs": {
        "evidence": {
            "type": "object",
            "additionalProperties": False,
            "required": ["kind", "ref", "detail"],
            "properties": {
                "kind": {"type": "string", "minLength": 1},
                "ref": {"type": "string"},
                "detail": {"type": "string"},
            },
        },
        "escalation": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "source",
                "problem",
                "attempts",
                "options",
                "recommendation",
                "blocking",
                "impact",
            ],
            "properties": {
                "source": {"enum": ["worker", "host"]},
                "problem": {"type": "string", "minLength": 1},
                "attempts": {"type": "array", "items": {"type": "string"}},
                "options": {"type": "array", "items": {"type": "string"}},
                "recommendation": {"type": "string"},
                "blocking": {"type": "boolean"},
                "impact": {"type": "string"},
            },
        },
    },
}


class Cancelled(Exception):
    pass


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run_id(operation: str) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    return f"r-{stamp}-{operation}-{secrets.token_hex(4)}"


def parse(argv) -> tuple[argparse.Namespace, object] | None:
    """The parsed command line and the provider, or None for a command-line error."""
    words = list(argv)
    if not words or words[0] not in CATALOG:
        return None
    name = words[0]
    try:
        chosen = provider(name)
    except (ImportError, AttributeError):
        return None
    command = argparse.ArgumentParser(prog=f"concorde run {name}")
    command.add_argument("--task", required=True)
    command.add_argument("--modules")
    command.add_argument("--input", action="append", default=[])
    if chosen.add_arguments:
        chosen.add_arguments(command)
    try:
        return command.parse_args(words[1:]), chosen
    except SystemExit:
        return None


def _inputs(primary: Path, task: dict, requested: list[str]) -> dict[str, dict]:
    admitted = {}
    runs = {run["run_id"]: run for run in task["runs"]}
    for identity in requested:
        run = runs.get(identity)
        path = primary / ".concorde/runs" / identity / "result.json"
        if run is None or run["status"] != "ok" or not path.is_file():
            raise store.TaskError(
                "input_not_admissible",
                f"{identity} is not an ok run of task {task['id']}",
            )
        result = json.loads(path.read_text())
        admitted[identity] = {
            "operation": result["operation"],
            "output": result["output"],
        }
    return admitted


def execute(argv, cwd: Path | None = None) -> tuple[int, dict | None]:
    """Run one Operation; return the exit status and the envelope (None on a usage error)."""
    parsed = parse(argv)
    if parsed is None:
        return 2, None
    arguments, chosen = parsed
    here = Path(os.path.realpath(cwd or Path.cwd()))
    try:
        primary = store.primary_of(here)
    except Exception:  # noqa: BLE001 -- not a Git repository
        return 2, None
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
            )
            begun = True
        except store.TaskError as refusal:
            stop = Stop(
                "failed",
                f"The run was refused before it began: {refusal.code}.",
                [evidence("refused", refusal.code, str(refusal))],
                host_escalation(str(refusal)),
            )
        if stop is None:
            stop = _steps(chosen, context)
    except Cancelled:
        stop = Stop(
            "failed",
            "The run was cancelled.",
            [evidence("cancelled", "", "SIGINT or SIGTERM")],
            host_escalation("the run was cancelled before it finished"),
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
    raise Cancelled()


def _steps(chosen, context: RunContext) -> Stop | None:
    for step in chosen.steps:
        try:
            outcome = step(context)
        except Cancelled:
            raise
        except Exception as error:  # noqa: BLE001 -- a step error is a failed result
            trace = context.run_dir / "traceback.txt"
            trace.write_text(traceback.format_exc())
            return Stop(
                "failed",
                f"The step {step.__name__} raised {type(error).__name__}.",
                [
                    evidence(
                        "host-error",
                        step.__name__,
                        f"{type(error).__name__}: {error}; traceback {trace}",
                    )
                ],
                host_escalation(
                    f"{step.__name__} raised {type(error).__name__}: {error}"
                ),
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
    escalation = None if status == "ok" else (stop.escalation if stop else None)
    if status != "ok" and escalation is None:
        escalation = host_escalation(summary)
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
        "escalation": escalation,
        "started_at": started,
        "finished_at": now(),
    }
    try:
        validate(envelope, RESULT_SCHEMA)
        if status == "ok" and chosen.output_schema is not None:
            validate(envelope["output"], chosen.output_schema)
    except ContractError as error:
        envelope.update(
            status="failed",
            summary="The run produced an invalid result.",
            output=None,
            escalation=host_escalation(f"invalid result: {error}"),
        )
        envelope["host_evidence"].append(evidence("invalid-output", "", str(error)))
    return envelope


def main(argv) -> int:
    status, envelope = execute(argv)
    if envelope is None:
        sys.stderr.write(
            "usage: concorde run <operation> --task <task-id> [--modules ids] "
            f"[--input run-id]... ; operations: {', '.join(CATALOG)}\n"
        )
        return 2
    sys.stdout.write(json.dumps(envelope, indent=2) + "\n")
    return status


__all__ = ["RESULT_SCHEMA", "execute", "main"]
