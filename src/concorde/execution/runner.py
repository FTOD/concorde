"""The Execution runner: ``concorde run <operation>`` and the execution commands.

One runner executes both kinds of run definition in the worktree it is started in:

1. Parse the command line and look up the definition; only then create the run.
2. Read the workspace binding of the worktree. A bound run waits in the lobby for the workspace
   lock, checks once it holds it that the workspace was not retired meanwhile, then enters it and
   works on the binding's Modules; an unbound run, for a definition that allows it, works in a
   throwaway detached checkout of the worktree's ``HEAD``. Check ``--modules`` and ``--input``.
3. Execute the definition's steps in order.
4. Remove an unbound run's checkout, compose and check the run result, write ``result.json``
   and the run's trace node, release the locks, print the result.

Every run is a trace node: ``trace.json`` is written when the run lock is taken and again after the
result, in ``runs/<run-id>/`` of the binding's workspace folder, in the folder ``--trace-at`` names
there (a workflow step's), or in ``.concorde/unbound/<run-id>/`` of the worktree for an unbound run.
A bound run's node starts in the lobby, ``lobby/<run-id>/`` of the binding's ``.concorde``, and moves
into the workspace folder only once the run holds the workspace lock, so nothing is written into a
workspace folder that a close may be moving; a run refused before then stays in the lobby.

``--detach`` starts the same runner as a process of its own and announces the run at once.
"""

from __future__ import annotations

import argparse
import contextlib
import errno
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from ..kernel import errors
from ..kernel import binding as binding_file
from ..kernel.refusal import KernelError
from ..kernel.schema import validate
from .checkout import Checkout, open_checkout
from .context import Continue, Provider, RunContext, Stop, component, evidence
from ..kernel.tracing import layout, locks
from ..kernel.tracing.node import Node, TraceError, concorde_commit, protocol_version
from .runs import (
    RESULT_SCHEMA,
    RUN_ID,
    RUN_TRACE,
    RunError,
    Store,
    admit_inputs,
    new_run_id,
    now,
    run_lock,
    store_of,
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
    "workspace_retired": (
        "environment",
        "the workspace the run was started for was retired, or its binding changed, while the "
        "run waited for its lock, and the runner works only in the workspace whose binding it read",
        [
            "start the run again in a worktree that is bound now, such as the worktree of an "
            "open task"
        ],
    ),
    "run_store_unwritable": (
        "environment",
        "the runner keeps a run only in the run store and cannot record it elsewhere",
        [
            "repair what the cause names, such as a full or read-only file system, and run it again"
        ],
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
REFUSING = {
    "checkout_unavailable": "Execution (unbound checkout)",
    "workspace_retired": "Execution (workspace binding)",
}
INPUT_REFUSAL = (
    "input",
    "the Modules or inputs named on the command line are refused and only the caller can "
    "correct them",
    ["correct the command line and run it again"],
)


class Cancelled(Exception):
    pass


class RunUnrecorded(Exception):
    """The run's initial records could not be created: no step ran and no result is written.

    ``link`` is the runner's error link, written to standard error."""

    def __init__(self, link: dict):
        super().__init__(link["detail"])
        self.link = link


class ResultUnsaved(Exception):
    """A final write of a run failed once its result was composed: the run counts as lost.

    ``status`` and ``envelope`` are the exit status and the result the runner composed, which it
    still prints; ``link`` is the runner's error link, written to standard error."""

    def __init__(self, status: int, envelope: dict, link: dict):
        super().__init__(link["detail"])
        self.status, self.envelope, self.link = status, envelope, link


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
        from .operations.catalog import CATALOG, provider

        table, load = CATALOG, provider
    else:
        from .commands.catalog import COMMANDS, command

        table, load = COMMANDS, command
    if name not in table:
        from .commands.catalog import COMMANDS

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
    command.add_argument("--trace-at")
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
        context.store, context.workspace_name, arguments.input
    )
    return None


def _refused(chosen: Provider, context: RunContext, refusal) -> Stop:
    reason, explanation, options = REFUSALS.get(refusal.code, INPUT_REFUSAL)
    actor = (
        "Execution (workspace binding)"
        if isinstance(refusal, KernelError)
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


def _node_folder(arguments, store: Store, identity: str, bound: dict | None) -> Path:
    """The run's trace node folder: ``--trace-at``'s, inside the workspace folder, or the store's."""
    if not arguments.trace_at:
        return store.run_folder(identity)
    if bound is None:
        raise UsageError(
            "--trace-at places the run's trace node inside a bound workspace's folder, and this "
            "worktree has no usable workspace binding"
        )
    folder = Path(os.path.realpath(os.path.abspath(arguments.trace_at)))
    workspace = Path(os.path.realpath(bound["traces"]))
    if workspace != folder and workspace not in folder.parents:
        raise UsageError(
            f"--trace-at {arguments.trace_at} lies outside the workspace folder {workspace} the "
            "binding names; a run's trace node lies only inside its workspace's"
        )
    if (folder / layout.TRACE).exists():
        raise UsageError(
            f"--trace-at {arguments.trace_at} already holds a trace node; a run needs a folder "
            "of its own"
        )
    return folder


def _argv(words) -> list[str]:
    """The command line recorded in the run's node: without --detach and --trace-at."""
    kept, skip = [], False
    for word in words:
        if skip:
            skip = False
            continue
        if word == "--detach":
            continue
        if word == "--trace-at":
            skip = True
            continue
        if word.startswith("--trace-at="):
            continue
        kept.append(word)
    return kept


def _head(worktree: Path) -> str | None:
    try:
        found = subprocess.run(
            ["git", "rev-parse", "--verify", "--quiet", "HEAD"],
            cwd=worktree,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None
    return found.stdout.strip() or None if found.returncode == 0 else None


def _start_node(chosen: Provider, context: RunContext, words) -> Node:
    bound = context.workspace
    node = Node(
        context.run_dir,
        context.run_id,
        "run",
        content_type=RUN_TRACE,
        metadata={
            "operation" if chosen.kind == "operation" else "command": chosen.name,
            "workspace": context.workspace_name,
            "modules": list(bound["modules"]) if bound else [],
            "base_commit": bound["base_commit"] if bound else None,
            "commit": _head(context.worktree) if bound else None,
            "concorde_commit": concorde_commit(),
            "protocol_version": protocol_version(context.worktree),
        },
        content={
            "kind": chosen.kind,
            "name": chosen.name,
            "argv": _argv(words),
            "exit_code": None,
            "steps": [],
            "worker_runs": [],
            "summary": None,
        },
    )
    for identity, relative in (
        ("result", layout.RESULT),
        ("progress", layout.PROGRESS),
        ("host-output", "host.out"),
        ("readiness", "readiness.json"),
    ):
        node.keep(identity, relative)
    return node.start()


def _node_content(
    chosen: Provider, context: RunContext, words, exit_code, summary
) -> dict:
    return {
        "kind": chosen.kind,
        "name": chosen.name,
        "argv": _argv(words),
        "exit_code": exit_code,
        "steps": [dict(step) for step in context.steps],
        "worker_runs": list(context.worker_runs),
        "summary": summary,
    }


def _finish_node(
    chosen: Provider, context: RunContext, node: Node, words, envelope, status
):
    cancelled = any(item["kind"] == "cancelled" for item in envelope["host_evidence"])
    for path in sorted(context.run_dir.glob("traceback-*.txt")):
        node.keep(path.stem, path.name)
    for identity in context.inputs:
        node.refer("input", identity)
    for relation, target in context.references:
        node.refer(relation, target)
    node.finish(
        envelope["status"],
        outcome="cancelled" if cancelled else envelope["status"],
        error=envelope["error"],
        content=_node_content(chosen, context, words, status, envelope["summary"]),
        ended_at=envelope["finished_at"],
        modules=context.modules,
        commit=context.commit or node.record["metadata"].get("commit"),
    )


def _worktree(here: Path) -> Path:
    try:
        return binding_file.toplevel(here)
    except KernelError as error:
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
    except KernelError as error:
        bound, broken = None, error
    store = store_of(root, bound)
    if identity is not None and not RUN_ID.match(identity):
        raise UsageError(f"invalid run identity {identity!r}")
    identity = identity or new_run_id(chosen.name)
    node_folder = _node_folder(arguments, store, identity, bound)
    # A bound run waits in the lobby: nothing of it lies in the workspace folder until it holds
    # the workspace lock, since a close holding that lock moves the folder.
    run_dir = store.lobby_folder(identity) if bound is not None else node_folder
    started = now()
    context = RunContext(
        name=chosen.name,
        store=store,
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
    # The run lock is held from before the first progress file until after the result: whoever
    # reads the run store tells a running run from a dead one by it, from any PID namespace. Its
    # file is removed as the block ends. A run whose first records cannot be created runs no step.
    records = contextlib.ExitStack()
    try:
        run_dir.mkdir(parents=True, exist_ok=True)
        records.enter_context(
            run_lock(store, identity, f"{chosen.name} run {identity}")
        )
        node = _start_node(chosen, context, words)
        # The first progress file is a record the run cannot do without: a detaching command
        # announces the run by it, and a run without one runs no step.
        _progress(context, required=True, phase="running", step=None)
    except (OSError, TraceError) as error:
        with contextlib.suppress(OSError):
            records.close()
        raise RunUnrecorded(
            _unrecorded(kind, name, identity, run_dir, error)
        ) from error
    with records:
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
                                store,
                                bound["workspace"],
                                f"{chosen.name} run {identity}",
                                wait=arguments.wait,
                                waiting=lambda holder: _progress(
                                    context, step="workspace-lock", waiting_for=holder
                                ),
                                retake=False,
                            )
                        )
                        _revalidate(root, bound)
                        _enter(context, node, node_folder)
                        _progress(context, step=None, waiting_for=None)
                    else:
                        checkout = _checkout(chosen, context)
                        # However the runner leaves, the checkout does not outlive it.
                        held.callback(checkout.close)
                        _progress(context, step=None)
                    stop = _resolve(chosen, context, arguments)
                except (RunError, KernelError) as refusal:
                    stop = _refused(chosen, context, refusal)
                if stop is None:
                    stop = _steps(chosen, context, node, words)
            except Cancelled as cancelled:
                _end_step(context, "cancelled")
                stop = _cancelled(chosen, context, cancelled)
            finally:
                for sig, handler in previous.items():
                    signal.signal(sig, handler)
            if checkout is not None:
                context.evidence.extend(checkout.close())
            envelope = _envelope(chosen, context, stop, started)
            status = 0 if envelope["status"] == "ok" else 1
            # The result is written while the lock is still held, so a run admitted after this one
            # always finds it written. Seeing the result does not mean the lock is free: it is
            # released only when this block ends. It is published whole or not at all.
            written = None
            try:
                _publish(
                    context.run_dir / layout.RESULT,
                    json.dumps(envelope, indent=2) + "\n",
                )
                written = context.run_dir / layout.RESULT
                _progress(
                    context,
                    phase="finished",
                    step=None,
                    status=envelope["status"],
                    summary=envelope["summary"],
                )
                _finish_node(chosen, context, node, words, envelope, status)
            except (OSError, TraceError) as error:
                # Leaving the blocks releases the locks; the run is lost to every observer.
                unsaved = _unsaved(kind, name, context, envelope, written, error)
                raise ResultUnsaved(1, envelope, unsaved) from error
    return status, envelope


def _publish(path: Path, text: str) -> None:
    """Replace ``path`` with ``text`` atomically: a reader finds the old file, none, or the whole
    new one, never part of it."""
    handle, temporary = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.stem}-", suffix=".tmp"
    )
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            stream.write(text)
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def _unrecorded(kind: str, name: str, identity: str, folder: Path, error) -> dict:
    """The runner's link for a run whose first records could not be created."""
    label = prog(kind, name)
    return errors.link(
        "component",
        f"Execution runner ({label})",
        "run_unrecorded",
        f"run {identity} of {name} could not create its first records in {folder} (its folder, "
        f"run lock, trace.json or run progress file): {errors.exception_detail(error)}; no step "
        "ran and no result is written",
        reason="environment",
        explanation="the runner never works on a run it cannot record, and cannot repair the "
        "run store",
        causes=[
            errors.from_exception(
                "Execution (run store)",
                error,
                code="run_store_unwritable",
                reason="environment",
                explanation="the operating system or the trace node contract refused the write",
            )
        ],
        options=[
            "repair what the cause names, such as a full or read-only file system, and run it "
            "again"
        ],
    )


def _unsaved(
    kind: str, name: str, context: RunContext, envelope, written, error
) -> dict:
    """The runner's link for a run whose result or final trace.json could not be written."""
    label = prog(kind, name)
    kept = (
        f"its result was saved as {written}, but its trace node still says it runs"
        if written is not None
        else "no result was saved"
    )
    return errors.link(
        "component",
        f"Execution runner ({label})",
        "result_unsaved",
        f"run {context.run_id} of {name} ended {envelope['status']} ({envelope['summary']}), "
        f"but a final write in {context.run_dir} failed: {errors.exception_detail(error)}; "
        f"{kept}, so the run counts as lost: the result above was printed only",
        reason="environment",
        explanation="the runner cannot repair the run store, and does not repeat the work it "
        "could not record",
        causes=[
            errors.from_exception(
                "Execution (run store)",
                error,
                code="run_store_unwritable",
                reason="environment",
                explanation="the operating system or the trace node contract refused the write",
            ),
            *([envelope["error"]] if envelope["error"] else []),
        ],
        options=[
            "repair what the cause names, such as a full or read-only file system",
            "check what the run changed before running it again, since it may have done its "
            "work",
        ],
    )


def _revalidate(root: Path, bound: dict) -> None:
    """Refuse with ``workspace_retired`` unless the binding read at the parse still binds the
    worktree; the caller holds the workspace lock, so it cannot change any more."""
    path = binding_file.path_of(root)
    try:
        current = binding_file.load(root)
    except KernelError as error:
        raise RunError(
            "workspace_retired",
            f"the workspace {bound['workspace']} was retired while this run waited for its lock: "
            f"its binding {path} can no longer be trusted ({error.code}: {error})",
        ) from None
    if current is None:
        raise RunError(
            "workspace_retired",
            f"the workspace {bound['workspace']} was retired while this run waited for its lock: "
            f"its binding {path} is gone",
        )
    if current != bound:
        changed = sorted(
            key for key in {*bound, *current} if bound.get(key) != current.get(key)
        )
        raise RunError(
            "workspace_retired",
            f"the binding {path} changed while this run waited for the lock of workspace "
            f"{bound['workspace']} (changed: {', '.join(changed)}); the run works only in the "
            "workspace whose binding it read",
        )


def _enter(context: RunContext, node: Node, folder: Path) -> None:
    """Move the run's node from the lobby into the workspace folder, once it holds the lock.

    A rename keeps every file, the detached runner's open ``host.out`` included; across file
    systems the node is copied and this process's output follows its copy. ``run_store_unwritable``
    when the node cannot be moved.
    """
    lobby = context.run_dir
    try:
        folder.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.rename(lobby, folder)
        except OSError as error:
            if error.errno != errno.EXDEV:
                raise
            shutil.copytree(lobby, folder, dirs_exist_ok=True)
            _follow_output(lobby / "host.out", folder / "host.out")
            shutil.rmtree(lobby, ignore_errors=True)
    except OSError as error:
        raise RunError(
            "run_store_unwritable",
            f"the run's node {lobby} cannot be moved from the lobby into the workspace folder as "
            f"{folder}: {error}",
        ) from error
    context.run_dir = folder
    node.folder = folder


def _follow_output(old: Path, new: Path) -> None:
    """Point this process's standard output and error that write ``old`` at ``new`` instead."""
    try:
        before = os.stat(old)
    except OSError:
        return
    target = None
    for stream, descriptor in ((sys.stdout, 1), (sys.stderr, 2)):
        try:
            current = os.fstat(descriptor)
        except OSError:
            continue
        if (current.st_dev, current.st_ino) != (before.st_dev, before.st_ino):
            continue
        if target is None:
            target = os.open(new, os.O_WRONLY | os.O_APPEND)
        stream.flush()
        os.dup2(target, descriptor)
    if target is not None:
        os.close(target)


def _cancelled(chosen: Provider, context: RunContext, cancelled: Cancelled) -> Stop:
    # Each worker run the Operation started, with the progress file and record it ended.
    workers = [
        evidence(
            "worker-run",
            (layout.worker_folder(context.run_dir, worker) / layout.TRACE).as_posix(),
            f"worker run {worker}, ended by the cancellation (progress "
            f"{(layout.worker_folder(context.run_dir, worker) / layout.PROGRESS).as_posix()})",
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


def _progress(context: RunContext, *, required: bool = False, **fields) -> None:
    """Rewrite the run's progress file ``status.json``; a failed write never changes the run,
    except the first, ``required``, whose failure is raised."""
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
        if required:
            raise


def _cancel(signum, frame):
    raise Cancelled(signal.Signals(signum).name)


def _end_step(context: RunContext, outcome: str) -> None:
    """End the step that is running, if one is, with ``outcome``."""
    if context.steps and context.steps[-1]["ended_at"] is None:
        context.steps[-1].update(ended_at=now(), outcome=outcome)


def _steps(chosen: Provider, context: RunContext, node: Node, words) -> Stop | None:
    for step in chosen.steps:
        _progress(context, step=step.__name__)
        context.steps.append(
            {
                "name": step.__name__,
                "started_at": now(),
                "ended_at": None,
                "outcome": "running",
            }
        )
        node.update(content=_node_content(chosen, context, words, None, None))
        try:
            outcome = step(context)
        except Cancelled:
            raise
        except Exception as error:  # noqa: BLE001 -- a step error is a failed result
            _end_step(context, "raised")
            return context.exception(
                f"step {step.__name__}",
                error,
                "host_error",
                f"The step {step.__name__} raised {type(error).__name__}: {error}",
            )
        context.evidence.extend(outcome.evidence)
        if isinstance(outcome, Continue):
            _end_step(context, "continue")
            if outcome.output is not None:
                context.output = outcome.output
            continue
        _end_step(context, "stop")
        return outcome
    return None


def _envelope(chosen: Provider, context: RunContext, stop: Stop | None, started: str):
    evidence_list = [
        evidence("trace", context.run_id, context.run_dir.as_posix()),
        *context.evidence,
    ]
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
    except KernelError as problem:
        invalid = evidence(
            "invalid-output", problem.field, f"{problem.field or '/'}: {problem}"
        )
        envelope["host_evidence"].append(invalid)
        envelope.update(
            status="failed",
            summary="The run produced an invalid result: "
            f"{problem.field or '/'}: {problem}",
            output=None,
            error=context.fail(
                "failed",
                "invalid_result",
                "invalid result",
                f"the result of {chosen.name} does not satisfy the run result contract or its "
                f"output contract at {problem.field or '/'}: {problem}",
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
    first act, in the lobby for a bound run; this returns once that file exists, in the lobby or
    in the node the run moved to on entering its workspace, with status 0 and the run's identity,
    node and lobby, or with status 1 and an error link when the runner ended or stayed silent
    before writing it.
    """
    words = [word for word in words if word != "--detach"]
    arguments, chosen = parse(kind, name, words)
    here = Path(os.path.realpath(cwd or Path.cwd()))
    root = _worktree(here)
    try:
        bound = binding_file.load(root)
    except KernelError:
        bound = None  # the runner itself refuses the broken binding, with a result
    store = store_of(root, bound)
    identity = new_run_id(chosen.name)
    node_folder = _node_folder(arguments, store, identity, bound)
    lobby = store.lobby_folder(identity) if bound is not None else None
    run_dir = lobby or node_folder
    run_dir.mkdir(parents=True, exist_ok=True)
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
    progress = node_folder / layout.PROGRESS
    # The lobby first: a run moves from it into its node, never back.
    places = [run_dir / layout.PROGRESS, progress] if lobby else [progress]

    def written() -> bool:
        return any(place.exists() for place in places)

    deadline = time.monotonic() + wait
    while not written():
        if process.poll() is not None or time.monotonic() > deadline:
            break
        time.sleep(0.05)
    announced = {
        "run_id": identity,
        "kind": chosen.kind,
        "name": chosen.name,
        "host_pid": process.pid,
        "trace": node_folder.as_posix(),
        "progress": progress.as_posix(),
        "result": (node_folder / layout.RESULT).as_posix(),
        "lobby": lobby.as_posix() if lobby else None,
    }
    if written():
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
    if written():
        # Its progress file appeared before it was killed: the run exists, and its result or
        # its lost state tells how it ended.
        return 0, announced
    try:
        tail = output.read_bytes()[-4000:].decode("utf-8", "replace").strip()
    except OSError:
        tail = ""
    # No progress file, so no step ran: nothing of the run is left.
    shutil.rmtree(run_dir, ignore_errors=True)
    lock = store.run_lock(identity)
    if lock.exists() and not locks.held(lock):
        lock.unlink(missing_ok=True)
    detail = (
        f"the detached runner of {chosen.name} (process {process.pid}) "
        + (
            f"exited with status {ended}"
            if ended is not None
            else f"wrote no progress file within {wait:.0f} seconds"
        )
        + f" before announcing run {identity}, so no step ran and its folder {run_dir} was "
        f"removed; its output ended with: {tail or '(nothing)'}"
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
            options=["run the same command without --detach to see it fail directly"],
        ),
    }


def _usage(kind: str, name: str | None) -> str:
    if kind == "operation":
        from .operations.catalog import CATALOG

        return (
            "usage: concorde run <operation> [--modules ids] [--input run-id]... [--detach] "
            "[--wait seconds] [--trace-at folder]; "
            f"operations: {', '.join(CATALOG)}"
        )
    return (
        f"usage: concorde {name} [--modules ids] [--input run-id]... [--detach] "
        "[--wait seconds] [--trace-at folder]"
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
    except RunUnrecorded as unrecorded:
        sys.stderr.write(f"{label} failed:\n" + errors.render(unrecorded.link) + "\n")
        return 1
    except ResultUnsaved as unsaved:
        # The work is done but not recorded: the caller still gets the result, and the reason
        # nobody else will.
        sys.stdout.write(json.dumps(unsaved.envelope, indent=2) + "\n")
        sys.stderr.write(f"{label} failed:\n" + errors.render(unsaved.link) + "\n")
        return unsaved.status
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
