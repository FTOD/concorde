"""The ``configure_workers`` Operation: list and change the worker model configuration.

It runs with or without a task. Without one it works on the primary worktree, whose
configuration new tasks inherit; with ``--task`` it changes only that task's own copy. It launches no worker and changes no Spec or code.

One step, ``configure``:

1. Check the request: ``--operation`` names a catalog Operation that launches workers, ``--role``
   one of its roles, ``--worker`` a worker number that role may use, and ``--unset`` comes without
   a model or level.
2. Read ``.concorde/worker-models.json`` and take the backend from ``--backend``, otherwise from
   the file's ``backend`` section for the named role, Operation or default, otherwise from the
   main session that started the run. The ``backend`` section itself is edited by hand only.
3. List the candidates the installed program offers (not for ``--unset``), refuse a model or level
   it does not offer, and apply the change to ``.concorde/worker-models.json``.
4. Output the candidates, the file's entries for the backend and the effective backend, model and
   level of every worker role of every Operation, and of every worker number of a role that
   launches several workers.
"""

from __future__ import annotations

import argparse

from ..harness.models import (
    CLIENTS,
    HANDLING,
    ModelConfigError,
    candidates,
    check_choice,
    config_path,
    configured_backend,
    detect_client,
    load,
    save,
    selection,
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
        "backend": {"anyOf": [{"type": "null"}, {"enum": list(CLIENTS)}]},
        "backend_source": TEXT,
        "model": OPTIONAL_TEXT,
        "reasoning": OPTIONAL_TEXT,
        "model_source": TEXT,
        "reasoning_source": TEXT,
    },
}
# A role's effective choice and, for a role that launches several workers, each worker's.
ROLE_CHOSEN_SCHEMA = {
    **CHOSEN_SCHEMA,
    "properties": {
        **CHOSEN_SCHEMA["properties"],
        "workers": {"type": "object", "additionalProperties": CHOSEN_SCHEMA},
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
                "additionalProperties": ROLE_CHOSEN_SCHEMA,
            },
        },
    },
}


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--backend", choices=CLIENTS)
    parser.add_argument("--operation")
    parser.add_argument("--role")
    parser.add_argument("--worker", type=int)
    parser.add_argument("--model")
    parser.add_argument("--reasoning")
    parser.add_argument("--unset", action="store_true")
    parser.add_argument("--allow-unlisted", action="store_true")


def worker_roles() -> dict[str, tuple[str, ...]]:
    """Every catalog Operation that launches workers, with its worker roles."""
    roles = {}
    for name in CATALOG:
        chosen = provider(name)
        if chosen.task_type is not None:
            roles[name] = chosen.roles
    return roles


def numbered_roles() -> dict[str, dict[str, int]]:
    """Every catalog Operation with a role that launches several workers, with the highest worker
    number of each such role."""
    return {
        name: dict(provider(name).numbered)
        for name in CATALOG
        if provider(name).numbered
    }


def _request_problem(arguments, roles: dict) -> str | None:
    if arguments.role and not arguments.operation:
        return "--role names a worker role but no --operation says whose"
    if arguments.operation and arguments.operation not in roles:
        return (
            f"--operation {arguments.operation} is not a catalog Operation that launches "
            f"workers (those are: {', '.join(roles)})"
        )
    if arguments.role and arguments.role not in roles[arguments.operation]:
        return (
            f"--role {arguments.role} is not a worker role of {arguments.operation} (its roles: "
            f"{', '.join(roles[arguments.operation])})"
        )
    if arguments.worker is not None:
        if not arguments.role:
            return "--worker names a worker number but no --role says of which role"
        highest = numbered_roles().get(arguments.operation, {}).get(arguments.role)
        if highest is None:
            return (
                f"--worker applies only to a role that launches several workers; the "
                f"{arguments.role} role of {arguments.operation} launches one, so configure the "
                "role itself"
            )
        if not 1 <= arguments.worker <= highest:
            return (
                f"--worker {arguments.worker} is not a worker number of the {arguments.role} role "
                f"of {arguments.operation}, which numbers its workers from 1 to {highest}"
            )
    if arguments.unset and (arguments.model or arguments.reasoning):
        return "--unset removes an entry and takes no --model or --reasoning"
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
        explanation="the Operation neither guesses the main session's program nor repairs "
        "the configuration or the installed program",
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


def _effective(
    config: dict, operation: str, role: str, client: tuple, number: int | None = None
) -> dict:
    """The backend one worker role, or that role's worker ``number``, runs on and its model and
    level in that backend's section."""
    backend, source = configured_backend(config, operation, role, number) or client
    if backend is None:
        chosen = {
            "model": None,
            "reasoning": None,
            "model_source": source,
            "reasoning_source": source,
        }
    else:
        chosen = selection(config, backend, operation, role, number)
    return {"backend": backend, "backend_source": source, **chosen}


def _effective_role(
    config: dict, operation: str, role: str, client: tuple, highest: int | None
) -> dict:
    """A role's effective choice and, for a role that launches several workers, each worker's."""
    chosen = _effective(config, operation, role, client)
    if highest:
        chosen["workers"] = {
            str(number): _effective(config, operation, role, client, number)
            for number in range(1, highest + 1)
        }
    return chosen


def configure(ctx: RunContext):
    arguments = ctx.arguments
    roles = worker_roles()
    problem = _request_problem(arguments, roles)
    if problem:
        return ctx.fail(
            "failed",
            "invalid_request",
            f"The request was not admitted: {problem}.",
            f"configure_workers was asked for an impossible change: {problem}",
            reason="input",
            explanation="only the caller can say which Operation, role and value it means",
            options=[
                "run configure_workers without arguments to see the Operations and roles"
            ],
        )
    try:
        config = load(ctx.worktree)
        target = configured_backend(
            config, arguments.operation, arguments.role, arguments.worker
        )
        try:
            client = detect_client()
        except ModelConfigError as error:
            if not (arguments.backend or target):
                raise
            client = (None, f"no backend is known: {error}")
        if arguments.backend:
            backend, told = arguments.backend, "--backend"
        else:
            backend, told = target or client
        found = None
        if arguments.unset:
            action = "unset"
            changed = unset_choice(
                config, backend, arguments.operation, arguments.role, arguments.worker
            )
            if changed:
                save(ctx.worktree, config)
        else:
            found = candidates(backend)
            action = "set" if arguments.model or arguments.reasoning else "list"
            changed = action == "set"
            if changed:
                check_choice(
                    found,
                    config,
                    backend,
                    arguments.operation,
                    arguments.role,
                    arguments.model,
                    arguments.reasoning,
                    arguments.allow_unlisted,
                    arguments.worker,
                )
                set_choice(
                    config,
                    backend,
                    arguments.operation,
                    arguments.role,
                    arguments.model,
                    arguments.reasoning,
                    arguments.worker,
                )
                save(ctx.worktree, config)
    except ModelConfigError as error:
        return _refuse(ctx, error)
    path = config_path(ctx.worktree).as_posix()
    target = (
        "the default"
        if not arguments.operation
        else f"{arguments.operation}"
        + (f" {arguments.role}" if arguments.role else "")
        + (f" worker {arguments.worker}" if arguments.worker is not None else "")
    )
    numbered = numbered_roles()
    return Continue(
        output={
            "action": action,
            "backend": backend,
            "backend_from": told,
            "worktree": ctx.worktree.as_posix(),
            "config": path,
            "changed": changed,
            "candidates": found,
            "configured": config.get(backend) or {},
            "effective": {
                name: {
                    role: _effective_role(
                        config, name, role, client, numbered.get(name, {}).get(role)
                    )
                    for role in names
                }
                for name, names in roles.items()
            },
        },
        evidence=[
            evidence(
                "worker-models",
                path,
                f"{action} {target} for {backend}"
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

__all__ = [
    "CONFIGURATION_SCHEMA",
    "CONFIGURE_WORKERS",
    "numbered_roles",
    "worker_roles",
]
