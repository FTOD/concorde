"""The Execution runner: ``concorde run <operation>`` and the execution commands.

One runner executes both kinds of run definition in the worktree it is started in:

1. Parse the command line and look up the definition; only then create the run.
2. Read the workspace binding of the worktree. A bound run takes the workspace lock and works on
   the binding's Modules; an unbound run, for a definition that allows it, works in a throwaway
   detached checkout of the worktree's ``HEAD``. Check ``--modules`` and ``--input``.
3. Execute the definition's steps in order.
4. Remove an unbound run's checkout, compose and check the run result, write ``result.json``,
   release the lock, print the result.

``--detach`` starts the same runner as a process of its own and announces the run at once.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

from .. import errors
from ..spec.schema import ContractError, validate
from . import binding as binding_file
from .checkout import Checkout, open_checkout
from .context import Continue, Provider, RunContext, Stop, component, evidence
from .runs import (
    RESULT_SCHEMA,
    RUN_ID,
    RunError,
    admit_inputs,
    new_run_id,
    now,
    run_directory,
    run_lock,
    workspace_lock,
)

KINDS = ("operation", "command")
# How long ``--detach`` waits for the detached runner to write its progress file.
DETACH_WAIT = 60.0
# The environment variable through which a detaching parent hands the runner its run identity.
RUN_ID_VARIABLE = "CONCORDE_RUN_ID"
SOURCE_ROOT = Path(__file__).resolve().parents[2]

# How the runner treats a refusal before the steps begin: the reason it cannot handle it, the
# explanation and the options.
REFUSALS = {
    "workspace_busy": (
        "decision",
        "one workspace runs one Operation or command at a time; waiting for the running one or "
        "cancelling it is the caller's decision",
        [
            "start this run again with --wait <seconds>, which waits for the lock inside the "
            "runner and starts as soon as the running run ends, instead of polling",
            "cancel the running run, then run this one again",
        ],
    ),
    "modules_removed": (
        "input",
        "the binding names only Modules the workspace removed or renamed, and which of its "
        "current Modules the run works on is for the caller to name",
        ["run it again naming the workspace's current Modules with --modules"],
    ),
    "specs_unloadable": (
        "scope",
        "the run needs the workspace's Specs to load and never repairs them",
        [
            "run concorde task-validation in the workspace to see why the Specs do not load",
            "repair the Specs by hand",
        ],
    ),
    "binding_required": (
        "scope",
        "the definition works only in a bound workspace, and binding one is the task level's "
        "decision",
        ["run it in a bound workspace, such as a task worktree (concorde task open)"],
    ),
    "binding_unreadable": (
        "environment",
        "the runner reads the workspace binding and never repairs it",
        ["restore the binding by opening the task again, or remove the broken file"],
    ),
    "binding_invalid": (
        "input",
        "the runner trusts only a binding that satisfies its contract and never repairs one",
        [
            "restore the binding by preparing the workspace again (for a task, from its record), or remove the broken file"
        ],
    ),
    "binding_misplaced": (
        "input",
        "a binding copied from another worktree would bind the wrong workspace",
        ["remove the copied .concorde/workspace.json"],
    ),
    "checkout_unavailable": (
        "environment",
        "an unbound run works only in a throwaway checkout of the commit it examines, which Git "
        "could not create, and never falls back to working in the worktree it started in",
        [
            "repair what Git reports in the cause and run it again",
            "run it in a bound workspace, such as a task worktree (concorde task open)",
        ],
    ),
}
# The component of the runner that refused, by refusal code; the run store otherwise.
REFUSING = {"checkout_unavailable": "Execution (unbound checkout)"}
INPUT_REFUSAL = (
    "input",
    "the Modules or inputs named on the command line are refused and only the caller can "
    "correct them",
    ["correct the command line and run it again"],
)


class Cancelled(Exception):
    pass


class UsageError(Exception):
    """A malformed command line; no run is created."""


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise UsageError(f"{self.prog}: {message}")


def prog(kind: str, name: str) -> str:
    return f"concorde run {name}" if kind == "operation" else f"concorde {name}"


def definition(kind: str, name: str) -> Provider:
    """The Operation or execution command ``name``; ``UsageError`` for an unknown one."""
    if kind == "operation":
        from ..operations.catalog import CATALOG, provider

        table, load = CATALOG, provider
    else:
        from ..commands.catalog import COMMANDS, command

        table, load = COMMANDS, command
    if name not in table:
        from ..commands.catalog import COMMANDS

        if kind == "operation" and name in COMMANDS:
            raise UsageError(
                f"{name} is a command, not an Operation: it runs no worker; run "
                f"`concorde {name}`"
            )
        raise UsageError(f"unknown {kind} {name!r}")
    try:
        chosen = load(name)
    except (ImportError, AttributeError) as error:
        raise UsageError(
            f"the definition of {name} cannot be loaded: {errors.exception_detail(error)}"
        ) from error
    if chosen.kind != kind:
        raise UsageError(f"{name} is declared as a {chosen.kind}, not a {kind}")
    return chosen


def parse(kind: str, name: str, words) -> tuple[argparse.Namespace, Provider]:
    """The parsed command line and the definition; ``UsageError`` names what is wrong."""
    chosen = definition(kind, name)
    command = _Parser(prog=prog(kind, name))
    command.add_argument("--modules")
    command.add_argument("--input", action="append", default=[])
    command.add_argument("--detach", action="store_true")
    command.add_argument("--wait", type=float, default=0.0)
    if chosen.add_arguments:
        chosen.add_arguments(command)
    arguments = command.parse_args(list(words))
    if arguments.wait < 0:
        raise UsageError(f"{command.prog}: --wait {arguments.wait:g} is negative")
    return arguments, chosen


def _named_modules(arguments) -> list[str] | None:
    if not arguments.modules:
        return None
    return [item.strip() for item in arguments.modules.split(",") if item.strip()]


def _registry(root: Path) -> set[str]:
    from ..spec.repository import SpecRepository
    from ..spec.repository_base import SpecError

    try:
        return set(SpecRepository(root).modules)
    except (SpecError, OSError, ValueError) as error:
        detail = error.describe() if isinstance(error, SpecError) else str(error)
        raise RunError(
            "specs_unloadable", f"the Specs of {root} cannot be loaded: {detail}"
        ) from error


def _registered(root: Path, modules: list[str]) -> None:
    known = _registry(root)
    unknown = sorted(item for item in modules if item not in known)
    if unknown:
        raise RunError(
            "unknown_module",
            f"{', '.join(unknown)} {'is' if len(unknown) == 1 else 'are'} not registered in "
            f"{root} (registered: {', '.join(sorted(known))})",
        )


def _bound_modules(chosen: Provider, context: RunContext) -> list[str]:
    """The binding's Modules the workspace still registers.

    A Module the workspace removed or renamed stays in the binding; the run leaves it out with
    ``removed-module`` evidence. When the Specs do not load, the binding's list is kept whole:
    the Module check, or the definition itself, reports why.
    """
    modules = list(context.workspace["modules"])
    try:
        known = _registry(context.worktree)
    except RunError:
        return modules
    kept = [item for item in modules if item in known]
    removed = [item for item in modules if item not in known]
    if removed and not kept:
        raise RunError(
            "modules_removed",
            f"every Module the binding of workspace {context.workspace_name} names "
            f"({', '.join(removed)}) is no longer registered in {context.worktree}: the "
            "workspace removed or renamed them, so the run has no Module to work on; name its "
            "current Modules with --modules",
        )
    for module in removed:
        context.evidence.append(
            evidence(
                "removed-module",
                module,
                f"the binding of workspace {context.workspace_name} names {module}, which the "
                f"workspace no longer registers, so {chosen.name} leaves it out",
            )
        )
    return kept


def _checkout(chosen: Provider, context: RunContext) -> Checkout:
    """Admit an unbound run and move it into a throwaway checkout of its worktree's ``HEAD``."""
    if chosen.binding == "required":
        raise RunError(
            "binding_required",
            f"{chosen.name} works only in a bound workspace, and {context.worktree} has no "
            f"workspace binding ({binding_file.BINDING})",
        )
    checkout = open_checkout(context.worktree, context.run_id)
    context.origin, context.worktree = context.worktree, checkout.path
    context.commit = checkout.commit
    context.evidence.append(
        evidence(
            "checkout",
            checkout.commit,
            f"the run works in {checkout.path}, a detached checkout of {checkout.commit}, the "
            f"HEAD of {checkout.origin}, removed when the run ends",
        )
    )
    context.evidence.extend(checkout.evidence)
    return checkout


def _resolve(chosen: Provider, context: RunContext, arguments) -> Stop | None:
    """The Modules and inputs of a bound or an unbound run, once it is admitted."""
    if context.workspace is not None:
        context.modules = _named_modules(arguments) or _bound_modules(chosen, context)
    else:
        context.modules = _named_modules(arguments) or []
    if context.modules and chosen.requires_loaded_specs:
        _registered(context.worktree, context.modules)
    context.inputs = admit_inputs(
        context.records, context.workspace_name, arguments.input
    )
    return None


def _refused(chosen: Provider, context: RunContext, refusal) -> Stop:
    reason, explanation, options = REFUSALS.get(refusal.code, INPUT_REFUSAL)
    actor = (
        "Execution (workspace binding)"
        if isinstance(refusal, binding_file.BindingError)
        else REFUSING.get(refusal.code, "Execution (run store)")
    )
    return context.fail(
        "failed",
        "refused",
        f"The run was refused before it began: {refusal.code}: {refusal}",
        f"{chosen.name} was refused before it began: {refusal.code}: {refusal}",
        reason=reason,
        explanation=explanation,
        evidence=[evidence("refused", refusal.code, str(refusal))],
        causes=[
            component(
                actor,
                refusal.code,
                str(refusal),
                "input",
                "the runner refuses a run whose workspace, Modules or inputs do not admit it",
            )
        ],
        options=options,
    )


def _worktree(here: Path) -> Path:
    try:
        return binding_file.toplevel(here)
    except binding_file.BindingError as error:
        raise UsageError(str(error)) from None


def execute(
    kind: str,
    name: str,
    words,
    cwd: Path | None = None,
    identity: str | None = None,
) -> tuple[int, dict]:
    """Run one Operation or execution command; the exit status and the run result.

    ``UsageError`` for a malformed command line. ``identity`` is the run identity a detaching
    parent chose and announced; its run directory may already hold the detached runner's output.
    """
    arguments, chosen = parse(kind, name, words)
    here = Path(os.path.realpath(cwd or Path.cwd()))
    root = _worktree(here)
    try:
        bound = binding_file.load(root)
        broken = None
    except binding_file.BindingError as error:
        bound, broken = None, error
    records = binding_file.records_of(root, bound)
    if identity is not None and not RUN_ID.match(identity):
        raise UsageError(f"invalid run identity {identity!r}")
    identity = identity or new_run_id(chosen.name)
    run_dir = run_directory(records, identity)
    run_dir.mkdir(parents=True, exist_ok=True)
    started = now()
    context = RunContext(
        name=chosen.name,
        records=records,
        workspace=bound,
        worktree=root,
        modules=[],
        run_id=identity,
        run_dir=run_dir,
        arguments=arguments,
        workers=chosen.workers,
        kind=chosen.kind,
    )
    stop: Stop | None = None
    checkout: Checkout | None = None
    # Held from before the first progress file until after the result: whoever reads the run
    # store tells a running run from a dead one by this lock, from any PID namespace.
    with run_lock(run_dir):
        _progress(context, phase="running", step=None)
        previous = {
            sig: signal.signal(sig, _cancel) for sig in (signal.SIGINT, signal.SIGTERM)
        }
        with contextlib.ExitStack() as held:
            try:
                try:
                    if broken is not None:
                        raise broken
                    if bound is not None:
                        held.enter_context(
                            workspace_lock(
                                records,
                                bound["workspace"],
                                f"{chosen.name} run {identity}",
                                wait=arguments.wait,
                                waiting=lambda holder: _progress(
                                    context, step="workspace-lock", waiting_for=holder
                                ),
                            )
                        )
                        _progress(context, step=None, waiting_for=None)
                    else:
                        checkout = _checkout(chosen, context)
                        # However the runner leaves, the checkout does not outlive it.
                        held.callback(checkout.close)
                        _progress(context, step=None)
                    stop = _resolve(chosen, context, arguments)
                except (RunError, binding_file.BindingError) as refusal:
                    stop = _refused(chosen, context, refusal)
                if stop is None:
                    stop = _steps(chosen, context)
            except Cancelled as cancelled:
                stop = _cancelled(chosen, context, cancelled)
            finally:
                for sig, handler in previous.items():
                    signal.signal(sig, handler)
            if checkout is not None:
                context.evidence.extend(checkout.close())
            envelope = _envelope(chosen, context, stop, started)
            # The result is written while the lock is still held, so a run admitted after this one
            # always finds it written. Seeing the result does not mean the lock is free: it is
            # released only when this block ends.
            (run_dir / "result.json").write_text(json.dumps(envelope, indent=2) + "\n")
            _progress(
                context,
                phase="finished",
                step=None,
                status=envelope["status"],
                summary=envelope["summary"],
            )
    return (0 if envelope["status"] == "ok" else 1), envelope


def _cancelled(chosen: Provider, context: RunContext, cancelled: Cancelled) -> Stop:
    # Each worker run the Operation started, with the progress file and record it ended.
    runs = context.run_dir.parent
    workers = [
        evidence(
            "worker-run",
            (runs / worker / "record.json").as_posix(),
            f"worker run {worker}, ended by the cancellation "
            f"(progress {(runs / worker / 'status.json').as_posix()})",
        )
        for worker in context.worker_runs
    ]
    return context.fail(
        "failed",
        "cancelled",
        "The run was cancelled.",
        f"{chosen.name} received {cancelled} before it finished"
        + (
            "; the worker processes it started were ended: "
            + ", ".join(context.worker_runs)
            if context.worker_runs
            else ""
        ),
        reason="environment",
        explanation="a signal from outside ended the run; the runner does not resume it",
        evidence=[evidence("cancelled", "", str(cancelled)), *workers],
        options=["run it again"],
    )


def _progress(context: RunContext, **fields) -> None:
    """Rewrite the run's progress file ``status.json``; a failed write never changes the run."""
    path = context.run_dir / "status.json"
    try:
        state = json.loads(path.read_text()) if path.exists() else {}
    except (OSError, ValueError):
        state = {}
    state.update(
        kind=context.kind,
        run_id=context.run_id,
        name=context.name,
        workspace=context.workspace_name,
        worktree=context.worktree.as_posix(),
        commit=context.commit,
        modules=context.modules,
        host_pid=os.getpid(),
        updated_at=now(),
        **fields,
    )
    state.setdefault("started_at", state["updated_at"])
    state.setdefault("phase", "running")
    state.setdefault("status", None)
    state.setdefault("waiting_for", None)
    temporary = path.with_suffix(".json.tmp")
    try:
        temporary.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")
        temporary.replace(path)
    except OSError:
        pass


def _cancel(signum, frame):
    raise Cancelled(signal.Signals(signum).name)


def _steps(chosen: Provider, context: RunContext) -> Stop | None:
    for step in chosen.steps:
        _progress(context, step=step.__name__)
        try:
            outcome = step(context)
        except Cancelled:
            raise
        except Exception as error:  # noqa: BLE001 -- a step error is a failed result
            return context.exception(
                f"step {step.__name__}",
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


def _envelope(chosen: Provider, context: RunContext, stop: Stop | None, started: str):
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
            explanation="the runner cannot reconstruct an error the step did not report",
        ).error
    envelope = {
        "kind": chosen.kind,
        "name": chosen.name,
        "workspace": context.workspace_name,
        "commit": context.commit,
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
                f"the result of {chosen.name} does not satisfy the run result contract or its "
                f"output contract: {problem}",
                reason="capability",
                explanation="the runner never returns a result that breaks its contract and "
                "cannot repair one",
                evidence=[invalid],
                causes=[error] if isinstance(error, dict) and "level" in error else [],
                options=[f"report an Issue against {chosen.name}"],
            ).error,
        )
    return envelope


def detach(
    kind: str, name: str, words, cwd: Path | None = None, wait: float = DETACH_WAIT
) -> tuple[int, dict]:
    """``--detach``: start the runner as a process of its own and announce the run.

    The command line is checked first, so a malformed one starts nothing (``UsageError``). The
    run identity is chosen here and handed to the runner, which writes its progress file as its
    first act; this returns once that file exists, with status 0 and the run's identity and
    result path, or with status 1 and an error link when the runner ended or stayed silent
    before writing it.
    """
    words = [word for word in words if word != "--detach"]
    _, chosen = parse(kind, name, words)
    here = Path(os.path.realpath(cwd or Path.cwd()))
    root = _worktree(here)
    try:
        bound = binding_file.load(root)
    except binding_file.BindingError:
        bound = None  # the runner itself refuses the broken binding, with a result
    records = binding_file.records_of(root, bound)
    identity = new_run_id(chosen.name)
    run_dir = run_directory(records, identity)
    run_dir.mkdir(parents=True)
    environment = dict(os.environ, **{RUN_ID_VARIABLE: identity})
    environment["PYTHONPATH"] = os.pathsep.join(
        [str(SOURCE_ROOT)]
        + ([environment["PYTHONPATH"]] if environment.get("PYTHONPATH") else [])
    )
    output = run_dir / "host.out"
    with output.open("wb") as stream:
        process = subprocess.Popen(
            [sys.executable, "-m", "concorde.execution.runner", kind, name, *words],
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
        "kind": chosen.kind,
        "name": chosen.name,
        "host_pid": process.pid,
        "progress": progress.as_posix(),
        "result": result.as_posix(),
    }
    if progress.exists():
        return 0, announced
    ended = process.poll()
    if ended is None:
        # A runner that did not announce itself in time must not start the run later,
        # unrecorded by whoever asked for it.
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except OSError:
            pass
        process.wait()
    tail = output.read_bytes()[-4000:].decode("utf-8", "replace").strip()
    detail = (
        f"the detached runner of {chosen.name} (process {process.pid}) "
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
            f"Execution runner ({prog(kind, name)} --detach)",
            "detach_failed",
            detail,
            reason="environment",
            explanation="the runner only starts the detached process; it cannot repair one "
            "that ends or hangs before its first write",
            evidence=[errors.evidence("host-output", output.as_posix(), "")],
            options=["run the same command without --detach to see it fail directly"],
        ),
    }


def _usage(kind: str, name: str | None) -> str:
    if kind == "operation":
        from ..operations.catalog import CATALOG

        return (
            "usage: concorde run <operation> [--modules ids] [--input run-id]... [--detach] "
            "[--wait seconds]; "
            f"operations: {', '.join(CATALOG)}"
        )
    return (
        f"usage: concorde {name} [--modules ids] [--input run-id]... [--detach] "
        "[--wait seconds]"
    )


def run_main(kind: str, name: str | None, words) -> int:
    """The command-line entry of both kinds; ``name`` None takes the Operation from ``words``."""
    words = list(words)
    if name is None:
        if not words:
            sys.stderr.write(
                f"concorde run: no Operation named\n{_usage(kind, None)}\n"
            )
            return 2
        name, words = words[0], words[1:]
    label = prog(kind, name)
    if "--detach" in words:
        try:
            status, announced = detach(kind, name, words)
        except UsageError as error:
            sys.stderr.write(f"{label}: {error}\n")
            return 2
        sys.stdout.write(json.dumps(announced, indent=2) + "\n")
        return status
    try:
        status, envelope = execute(
            kind, name, words, identity=os.environ.pop(RUN_ID_VARIABLE, None)
        )
    except UsageError as error:
        sys.stderr.write(f"{label}: {error}\n{_usage(kind, name)}\n")
        return 2
    except Exception as error:  # noqa: BLE001 -- the runner itself failed; say exactly how
        link = errors.from_exception(
            f"Execution runner ({label})",
            error,
            explanation="the runner failed outside every step, so no result could be written",
        )
        sys.stderr.write(f"{label} failed:\n" + errors.render(link) + "\n")
        return 1
    sys.stdout.write(json.dumps(envelope, indent=2) + "\n")
    if envelope["error"] is not None:
        sys.stderr.write(
            f"{envelope['name']} ended {envelope['status']}: {envelope['summary']}\n"
            + errors.render(envelope["error"])
            + "\n"
        )
    return status


__all__ = ["KINDS", "UsageError", "definition", "detach", "execute", "run_main"]


if __name__ == "__main__":  # the detached runner started by ``detach``
    sys.exit(run_main(sys.argv[1], sys.argv[2], sys.argv[3:]))
