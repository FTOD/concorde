"""The ``configure_workers`` Operation: list and change the worker model configuration.

It runs with or without a task. Without one it works on the primary worktree, whose
configuration new tasks inherit; with ``--task`` it changes only that task's own copy. It launches
no worker and changes no Spec or code.

One step, ``configure``:

1. Check the request: ``--operation`` names a catalog Operation that launches workers,
   ``--worker`` one of the worker ids it declares, and ``--unset`` comes without a backend, model
   or level.
2. Read ``.concorde/worker-models.json`` and find the entry the request names: the default, an
   Operation's default or one worker's. A change is checked against the candidates of the
   program the entry resolves to after it (pi when nothing chooses one); ``--candidates`` lists
   another program's models without changing anything.
3. List the candidates of that program (not for ``--unset``), refuse a model or level it does not
   offer, and apply the change to the file.
4. Output the candidates, the file as written and the effective backend, model and level of every
   worker of every Operation, by worker id.
"""

from __future__ import annotations

import argparse
import copy

from ..harness.models import (
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
from .catalog import CATALOG, provider
from .provider import Continue, Provider, RunContext, component, evidence

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


def _refuse(ctx: RunContext, error: ModelConfigError) -> object:
    reason, explanation, options = HANDLING.get(
        error.code,
        ("input", "the request is not admitted", []),
    )
    return ctx.fail(
        "failed",
        "configuration_refused",
        f"The worker model configuration was not changed ({error.code}).",
        f"configure_workers could not complete for {config_path(ctx.worktree)}: "
        f"{error.code}: {error}",
        reason=reason,
        explanation="the Operation neither guesses a program or model nor repairs the "
        "configuration or the installed program",
        evidence=[
            evidence("worker-models", config_path(ctx.worktree).as_posix(), str(error))
        ],
        causes=[
            component(
                "Workers (worker model configuration)",
                error.code,
                str(error),
                reason,
                explanation,
                options=options,
            )
        ],
        options=options,
    )


def configure(ctx: RunContext):
    arguments = ctx.arguments
    ids = worker_ids()
    problem = _request_problem(arguments, ids)
    if problem:
        return ctx.fail(
            "failed",
            "invalid_request",
            f"The request was not admitted: {problem}.",
            f"configure_workers was asked for an impossible change: {problem}",
            reason="input",
            explanation="only the caller can say which Operation, worker and value it means",
            options=[
                "run configure_workers without arguments to see the Operations and their workers"
            ],
        )
    operation, worker = arguments.operation, arguments.worker
    try:
        config = load(ctx.worktree)
        found = None
        if arguments.unset:
            action = "unset"
            current = choice(config, operation, worker)
            backend, told = current["backend"], current["backend_source"]
            changed = unset_choice(config, operation, worker)
            if changed:
                save(ctx.worktree, config)
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
                save(ctx.worktree, config)
    except ModelConfigError as error:
        return _refuse(ctx, error)
    path = config_path(ctx.worktree).as_posix()
    target = (
        "the default"
        if not operation
        else f"{operation} {worker}"
        if worker
        else f"{operation}'s default"
    )
    return Continue(
        output={
            "action": action,
            "backend": backend,
            "backend_from": told,
            "worktree": ctx.worktree.as_posix(),
            "config": path,
            "changed": changed,
            "candidates": found,
            "configured": config,
            "effective": {
                name: {each: choice(config, name, each) for each in workers}
                for name, workers in ids.items()
            },
        },
        evidence=[
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


CONFIGURE_WORKERS = Provider(
    name="configure_workers",
    task_type=None,
    writes=False,
    steps=(configure,),
    output_schema=CONFIGURATION_SCHEMA,
    add_arguments=add_arguments,
    requires_loaded_specs=False,
    task_scope="optional",
)

__all__ = ["CONFIGURATION_SCHEMA", "CONFIGURE_WORKERS", "worker_ids"]
