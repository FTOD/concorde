"""What a run definition declares, and the context and outcomes its steps work with.

An Operation (an AI worker job) and an execution command (a deterministic one) are both a fixed list
of steps run by the Execution runner. Each step receives the run's ``RunContext`` and returns
``Continue`` (with any output and host evidence it produced) or ``Stop`` (with a status, a summary,
host evidence and, unless the status is ``ok``, the run's error link). ``RunContext.fail`` builds
that link: the run's own account of the error and why it cannot handle it, with the errors it
received from its children as causes. Execution launches no worker: the steps that do, such as
those of Method's Operations, launch them through the worker harness themselves and record each
worker run on the context.
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from ..kernel.errors import evidence, from_exception, link
from .runs import Store


@dataclass
class Continue:
    output: dict | None = None
    evidence: list[dict] = field(default_factory=list)


@dataclass
class Stop:
    status: str
    summary: str
    evidence: list[dict] = field(default_factory=list)
    error: dict | None = None


@dataclass(frozen=True)
class Provider:
    """One runnable definition: an Operation (``kind`` operation, launching AI workers) or an
    execution command (``kind`` command, deterministic, launching none)."""

    name: str
    task_type: str | None
    writes: bool
    steps: tuple[Callable, ...]
    output_schema: dict | None = None
    add_arguments: Callable[[argparse.ArgumentParser], None] | None = None
    # The definition's own admission of the run's Modules, called once the inputs are admitted
    # and before the first step: it may narrow ``context.modules`` and refuses the run by
    # raising ``Refused``. None takes the Modules as names.
    admit: Callable[["RunContext"], None] | None = None
    # "required": every run needs a workspace binding. "optional": an unbound run works on the
    # worktree it starts in and may launch only read-only workers.
    binding: str = "required"
    # The ids of the workers the Operation may launch, stable across runs; the first is the
    # default. The worker configuration, run records and evidence name workers by them.
    workers: tuple[str, ...] = ("worker",)
    kind: str = "operation"
    # For a definition that may run unbound, what to link into its checkout: called with the
    # checkout's root before anything is linked, it returns the runtime paths, relative ones
    # linked from the worktree the run started in. None links nothing.
    runtime_paths: Callable[[Path], Sequence[str]] | None = None
    # The identity of the Module that provides the definition, such as
    # ``module.understanding``; the catalogs refuse a definition without one.
    module: str | None = None


class Refused(Exception):
    """A definition's admission refusing a run before its steps begin.

    ``actor`` is the component that refused, such as the providing part's admission; the reason,
    explanation and options say why the run cannot handle the refusal and what the caller may do.
    """

    def __init__(
        self,
        code: str,
        message: str,
        *,
        actor: str,
        reason: str = "input",
        explanation: str = "the Modules named for the run are refused and only the caller can "
        "correct them",
        options=("correct the command line and run it again",),
    ):
        super().__init__(message)
        self.code, self.actor = code, actor
        self.reason, self.explanation, self.options = reason, explanation, list(options)


def command(name: str, steps, **fields) -> Provider:
    """An execution command: deterministic steps, no worker and no task type."""
    return Provider(
        name=name,
        task_type=None,
        steps=tuple(steps),
        workers=(),
        kind="command",
        **fields,
    )


def component(
    actor: str, code: str, detail: str, reason: str, explanation: str, **extra
):
    """A link of a deterministic component a step called, such as Git or Check execution."""
    return link(
        "component",
        actor,
        code,
        detail,
        reason=reason,
        explanation=explanation,
        **extra,
    )


@dataclass
class RunContext:
    name: str
    # Where the run's workspace keeps its runs and locks: the binding's workspace folder and
    # ``.concorde``, or an unbound worktree's own ``.concorde``.
    store: Store
    # The workspace binding, or None for an unbound run.
    workspace: dict | None
    # The worktree the run works in: the bound workspace, or an unbound run's checkout.
    worktree: Path
    # The Modules the run works on, as names: ``--modules``, else the binding's, as the
    # definition's admission left them.
    modules: list[str]
    run_id: str
    # The run's trace node folder, where its result, progress file, checks and worker runs lie.
    run_dir: Path
    arguments: argparse.Namespace
    inputs: dict[str, dict] = field(default_factory=dict)
    output: dict | None = None
    worker: dict | None = None
    worker_runs: list[str] = field(default_factory=list)
    evidence: list[dict] = field(default_factory=list)
    # Provider-owned values shared between the steps of one run.
    state: dict = field(default_factory=dict)
    # The run record of the latest worker launch, as Workers wrote it.
    last_record: dict | None = None
    # The worker ids the provider declares; the first is the default.
    workers: tuple[str, ...] = ("worker",)
    kind: str = "operation"
    # The worktree an unbound run started in, once it works in its checkout; None otherwise.
    origin: Path | None = None
    # The commit an unbound run's checkout holds; None for a bound run.
    commit: str | None = None
    # Whether ``--modules`` named the Modules, rather than the binding.
    modules_named: bool = False
    # The steps that began, with their timings, for the run's trace node.
    steps: list[dict] = field(default_factory=list)
    # References of the run's trace node its steps add, as (relation, target).
    references: list[tuple[str, str]] = field(default_factory=list)

    @property
    def unbound(self) -> bool:
        """Whether the run works without a workspace binding, on a checkout of the worktree it
        started in."""
        return self.workspace is None

    @property
    def started_in(self) -> Path:
        """The worktree the run started in: an unbound run's origin, else its worktree."""
        return self.origin or self.worktree

    @property
    def workspace_name(self) -> str | None:
        return self.workspace["workspace"] if self.workspace else None

    @property
    def goal(self) -> str:
        return self.workspace["goal"] if self.workspace else ""

    @property
    def base_commit(self) -> str | None:
        return self.workspace["base_commit"] if self.workspace else None

    @property
    def branch(self) -> str | None:
        return self.workspace["branch"] if self.workspace else None

    def worker_started(self, run_id: str) -> None:
        """Name a worker run as soon as it exists, so a cancelled Operation still names it."""
        if run_id not in self.worker_runs:
            self.worker_runs.append(run_id)

    @property
    def actor(self) -> str:
        what = "Operation" if self.kind == "operation" else "Command"
        if self.unbound:
            at = f" at {self.commit}" if self.commit else ""
            return f"{what} {self.name} {self.run_id} (unbound, {self.started_in}{at})"
        return f"{what} {self.name} {self.run_id} (workspace {self.workspace_name})"

    def fail(
        self,
        status: str,
        code: str,
        summary: str,
        detail: str,
        *,
        reason: str,
        explanation: str,
        evidence: list[dict] | None = None,
        host_evidence: list[dict] | None = None,
        causes=(),
        attempts=(),
        options=(),
        recommendation: str = "",
    ) -> Stop:
        """Stop with ``status`` and this Operation's error link; ``causes`` are child errors.

        ``evidence`` belongs to the error and is also host evidence of the run; ``host_evidence``
        is host evidence of the run only.
        """
        found = list(evidence or [])
        options = list(options)
        return Stop(
            status,
            summary,
            list(host_evidence or []) + found,
            link(
                "operation" if self.kind == "operation" else "command",
                self.actor,
                code,
                detail,
                reason=reason,
                explanation=explanation,
                evidence=found,
                attempts=attempts,
                options=options,
                recommendation=recommendation or (options[0] if options else ""),
                causes=causes,
            ),
        )

    def checks_unavailable(self, error, modules: list[str] | None = None) -> Stop:
        """Stop ``failed`` because Check execution could not run the configured checks; its own
        link is the cause."""
        from .checks.checks import service_error

        code = getattr(error, "code", None) or "checks_unavailable"
        names = ", ".join(modules or self.modules)
        return self.fail(
            "failed",
            "checks_unavailable",
            f"The configured checks could not be run ({code}).",
            f"the configured checks of {names} could not run in {self.worktree}: {code}: "
            f"{error}",
            reason="environment",
            explanation="the Operation runs checks through Check execution and cannot repair "
            "their configuration or their sandbox",
            evidence=[evidence("checks_unavailable", code, str(error))],
            causes=[service_error(error)],
            options=[
                "repair the check configuration",
                "run the Operation on a host that supports the check sandbox",
            ],
        )

    def exception(self, actor: str, error: BaseException, code: str, summary: str):
        """Stop ``failed`` for an unexpected exception of a component the step called."""
        trace = (
            self.run_dir / f"traceback-{len(list(self.run_dir.glob('traceback*')))}.txt"
        )
        cause = from_exception(actor, error, trace=trace)
        return self.fail(
            "failed",
            code,
            summary,
            f"{actor} raised {cause['detail']}",
            reason="capability",
            explanation="the Operation has no recovery for an unexpected error of a "
            "component it relies on",
            evidence=[evidence("host-error", actor, cause["detail"])],
            causes=[cause],
            options=[
                "inspect the traceback in the cause's evidence",
                "report an Issue",
            ],
        )


__all__ = [
    "Continue",
    "Provider",
    "Refused",
    "RunContext",
    "Stop",
    "command",
    "component",
    "evidence",
]
