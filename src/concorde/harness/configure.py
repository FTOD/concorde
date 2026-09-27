"""``concorde configure-workers``: list and change the worker model configuration.

A plain command of the worktree it runs in: it launches no worker, records no run and changes no
Spec or code, only that worktree's ``.concorde/worker-models.json``. In the primary worktree it
changes the configuration new task worktrees inherit; in a task worktree only that worktree's copy.

1. Check the request: ``--operation`` names a catalog Operation that launches workers,
   ``--worker`` one of the worker ids it declares, and ``--unset`` comes without a backend, model
   or level.
2. Read ``.concorde/worker-models.json`` and find the entry the request names: the default, an
   Operation's default or one worker's. A change is checked against the candidates of the
   program the entry resolves to after it (pi when nothing chooses one); ``--candidates`` lists
   another program's models without changing anything.
3. List the candidates of that program (not for ``--unset``), refuse a model or level it does not
   offer, and apply the change to the file.
4. Print the command result: the candidates, the file as written and the effective backend, model
   and level of every worker of every Operation, by worker id; or the error link.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import subprocess
import sys
from pathlib import Path

from .. import errors
from ..errors import evidence
from ..spec.schema import validate
from .models import (
    CLIENTS,
    HANDLING,
    ModelConfigError,
    candidates,
    check_choice,
    choice,
    config_path,
    load,
    save,
    set_choice,
    unset_choice,
)

TEXT = {"type": "string", "minLength": 1}
OPTIONAL_TEXT = {"anyOf": [{"type": "null"}, TEXT]}
CHOSEN_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "backend",
        "backend_source",
        "model",
        "reasoning",
        "model_source",
        "reasoning_source",
    ],
    "properties": {
        "backend": {"enum": list(CLIENTS)},
        "backend_source": TEXT,
        "model": OPTIONAL_TEXT,
        "reasoning": OPTIONAL_TEXT,
        "model_source": TEXT,
        "reasoning_source": TEXT,
    },
}
# contract.operations.worker-configuration (specs/concorde/operations/contracts.md)
CONFIGURATION_SCHEMA: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "action",
        "backend",
        "backend_from",
        "worktree",
        "config",
        "changed",
        "candidates",
        "configured",
        "effective",
    ],
    "properties": {
        "action": {"enum": ["list", "set", "unset"]},
        "backend": {"enum": list(CLIENTS)},
        "backend_from": TEXT,
        "worktree": TEXT,
        "config": TEXT,
        "changed": {"type": "boolean"},
        "candidates": {"anyOf": [{"type": "null"}, {"type": "object"}]},
        "configured": {"type": "object"},
        "effective": {
            "type": "object",
            "additionalProperties": {
                "type": "object",
                "additionalProperties": CHOSEN_SCHEMA,
            },
        },
    },
}


# contract.workers.configure-workers-result, version 1
RESULT_SCHEMA: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": ["command", "status", "output", "evidence", "error"],
    "properties": {
        "command": {"const": "configure-workers"},
        "status": {"enum": ["ok", "failed"]},
        "output": {"anyOf": [{"type": "null"}, {"type": "object"}]},
        "evidence": {"type": "array", "items": {"$ref": "#/$defs/evidence"}},
        "error": {"anyOf": [{"type": "null"}, {"$ref": "#/$defs/error"}]},
    },
    "$defs": copy.deepcopy(errors.DEFS),
}


class UsageError(Exception):
    pass


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise UsageError(f"{self.prog}: {message}")


class Refused(Exception):
    """The command's own error link, carried to the result."""

    def __init__(self, link: dict):
        super().__init__(link["detail"])
        self.link = link


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--operation")
    parser.add_argument("--worker")
    parser.add_argument("--backend", choices=CLIENTS)
    parser.add_argument("--candidates", choices=CLIENTS)
    parser.add_argument("--model")
    parser.add_argument("--reasoning")
    parser.add_argument("--unset", action="store_true")
    parser.add_argument("--allow-unlisted", action="store_true")


def worker_ids() -> dict[str, tuple[str, ...]]:
    """Every catalog Operation that launches workers, with the ids of its workers."""
    from ..operations.catalog import CATALOG, provider

    found = {}
    for name in CATALOG:
        chosen = provider(name)
        if chosen.task_type is not None:
            found[name] = chosen.workers
    return found


def _request_problem(arguments, ids: dict) -> str | None:
    if arguments.worker and not arguments.operation:
        return "--worker names a worker but no --operation says whose"
    if arguments.operation and arguments.operation not in ids:
        return (
            f"--operation {arguments.operation} is not a catalog Operation that launches "
            f"workers (those are: {', '.join(ids)})"
        )
    if arguments.worker and arguments.worker not in ids[arguments.operation]:
        return (
            f"--worker {arguments.worker} is not a worker of {arguments.operation} (its workers: "
            f"{', '.join(ids[arguments.operation])})"
        )
    if arguments.unset and (
        arguments.backend or arguments.model or arguments.reasoning
    ):
        return "--unset removes an entry and takes no --backend, --model or --reasoning"
    if arguments.candidates and (
        arguments.backend or arguments.model or arguments.reasoning or arguments.unset
    ):
        return (
            "--candidates only lists a program's models; a change is checked against the "
            "program its entry runs on, which --backend sets"
        )
    if arguments.allow_unlisted and not arguments.model:
        return "--allow-unlisted applies only to a --model"
    return None


def actor(worktree: Path) -> str:
    return f"concorde configure-workers ({worktree})"


def _refuse(worktree: Path, error: ModelConfigError) -> Refused:
    reason, explanation, options = HANDLING.get(
        error.code,
        ("input", "the request is not admitted", []),
    )
    return Refused(
        errors.link(
            "command",
            actor(worktree),
            "configuration_refused",
            f"configure-workers could not complete for {config_path(worktree)}: "
            f"{error.code}: {error}",
            reason=reason,
            explanation="the command neither guesses a program or model nor repairs the "
            "configuration or the installed program",
            evidence=[
                evidence("worker-models", config_path(worktree).as_posix(), str(error))
            ],
            causes=[
                errors.link(
                    "component",
                    "Workers (worker model configuration)",
                    error.code,
                    str(error),
                    reason=reason,
                    explanation=explanation,
                    options=options,
                )
            ],
            options=options,
        )
    )


def configure(worktree: Path, arguments) -> tuple[dict, list[dict]]:
    """The output and evidence of one request; ``Refused`` carries the command's error link."""
    ids = worker_ids()
    problem = _request_problem(arguments, ids)
    if problem:
        raise Refused(
            errors.link(
                "command",
                actor(worktree),
                "invalid_request",
                f"configure-workers was asked for an impossible change: {problem}",
                reason="input",
                explanation="only the caller can say which Operation, worker and value it "
                "means",
                options=[
                    "run concorde configure-workers without arguments to see the Operations "
                    "and their workers"
                ],
            )
        )
    operation, worker = arguments.operation, arguments.worker
    try:
        config = load(worktree)
        found = None
        if arguments.unset:
            action = "unset"
            current = choice(config, operation, worker)
            backend, told = current["backend"], current["backend_source"]
            changed = unset_choice(config, operation, worker)
            if changed:
                save(worktree, config)
        else:
            changed = bool(arguments.backend or arguments.model or arguments.reasoning)
            action = "set" if changed else "list"
            proposed = copy.deepcopy(config)
            if changed:
                set_choice(
                    proposed,
                    operation,
                    worker,
                    arguments.backend,
                    arguments.model,
                    arguments.reasoning,
                )
            after = choice(proposed, operation, worker)
            backend = after["backend"]
            told = "--backend" if arguments.backend else after["backend_source"]
            if arguments.candidates and not changed:
                backend, told = arguments.candidates, "--candidates"
            found = candidates(backend)
            if changed:
                check_choice(
                    found,
                    backend,
                    arguments.model,
                    arguments.reasoning,
                    arguments.allow_unlisted,
                    after["model"],
                )
                config = proposed
                save(worktree, config)
    except ModelConfigError as error:
        raise _refuse(worktree, error) from None
    path = config_path(worktree).as_posix()
    target = (
        "the default"
        if not operation
        else f"{operation} {worker}"
        if worker
        else f"{operation}'s default"
    )
    return (
        {
            "action": action,
            "backend": backend,
            "backend_from": told,
            "worktree": worktree.as_posix(),
            "config": path,
            "changed": changed,
            "candidates": found,
            "configured": config,
            "effective": {
                name: {each: choice(config, name, each) for each in workers}
                for name, workers in ids.items()
            },
        },
        [
            evidence(
                "worker-models",
                path,
                f"{action} {target} on {backend}"
                + (
                    ""
                    if action == "list"
                    else f": {'changed' if changed else 'no entry'}"
                ),
            )
        ],
    )


def _toplevel(here: Path) -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=here,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise UsageError(
            f"{here} is not inside a Git worktree: {result.stderr.strip() or 'git refused'}"
        )
    return Path(os.path.realpath(result.stdout.strip()))


def result(worktree: Path, arguments) -> dict:
    """The command result of one parsed request in ``worktree``."""
    try:
        output, found = configure(worktree, arguments)
        value = {
            "command": "configure-workers",
            "status": "ok",
            "output": output,
            "evidence": found,
            "error": None,
        }
        validate(output, CONFIGURATION_SCHEMA)
    except Refused as refusal:
        value = {
            "command": "configure-workers",
            "status": "failed",
            "output": None,
            "evidence": list(refusal.link["evidence"]),
            "error": refusal.link,
        }
    validate(value, RESULT_SCHEMA)
    return value


def main(argv, cwd: Path | None = None) -> int:
    """``concorde configure-workers``: print the command result; 0 ok, 1 refused, 2 usage."""
    parser = _Parser(prog="concorde configure-workers")
    add_arguments(parser)
    here = Path(os.path.realpath(cwd or Path.cwd()))
    try:
        arguments = parser.parse_args(list(argv))
        worktree = _toplevel(here)
    except UsageError as error:
        link = errors.link(
            "command",
            actor(here),
            "invalid_request",
            str(error),
            reason="input",
            explanation="the command runs only a well-formed request inside a Git worktree",
            options=["correct the command line; see concorde configure-workers --help"],
        )
        sys.stdout.write(json.dumps({"error": link}, indent=2) + "\n")
        return 2
    value = result(worktree, arguments)
    sys.stdout.write(json.dumps(value, indent=2, ensure_ascii=False) + "\n")
    if value["error"] is not None:
        sys.stderr.write(errors.render(value["error"]) + "\n")
    return 0 if value["status"] == "ok" else 1


__all__ = ["CONFIGURATION_SCHEMA", "RESULT_SCHEMA", "main", "result", "worker_ids"]
