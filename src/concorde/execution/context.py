"""What a run definition declares, and the context and outcomes its steps work with.

An Operation (an AI worker job) and an execution command (a deterministic one) are both a fixed list
of steps run by the Execution runner. Each step receives the run's ``RunContext`` and returns
``Continue`` (with any output and host evidence it produced) or ``Stop`` (with a status, a summary,
host evidence and, unless the status is ``ok``, the run's error link). ``RunContext.fail`` builds
that link: the run's own account of the error and why it cannot handle it, with the errors it
received from its children as causes. ``RunContext.run_worker`` is the standard worker sequence of
an Operation: it computes the grant from the workspace's Specs, runs one worker through Workers and
maps its outcome to a step outcome.
"""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from ..errors import evidence, from_exception, link
from ..harness.models import (
    CONFIG,
    HANDLING,
    ModelConfigError,
    config_path,
    limits,
    load,
    runtime,
    worker_choice,
)


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
    # False for a provider that diagnoses the workspace's Specs itself, such as task-validation:
    # the runner then begins the run even when those Specs cannot be loaded.
    requires_loaded_specs: bool = True
    # "required": every run needs a workspace binding. "optional": an unbound run works on the
    # worktree it starts in and may launch only read-only workers.
    binding: str = "required"
    # The ids of the workers the Operation may launch, stable across runs; the first is the
    # default. The worker configuration, run records and evidence name workers by them.
    workers: tuple[str, ...] = ("worker",)
    kind: str = "operation"


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


# Task types whose workers may change files; an unbound run never launches one.
WRITING_TASK_TYPES = ("specify", "implement", "code-to-spec")


def component(
    actor: str, code: str, detail: str, reason: str, explanation: str, **extra
):
    """A link of a deterministic component the host called, such as Git, Tasks or Spec core."""
    return link(
        "component",
        actor,
        code,
        detail,
        reason=reason,
        explanation=explanation,
        **extra,
    )


def spec_cause(error: BaseException, actor: str = "Spec core") -> dict:
    """Spec tooling's own error as a component link: its message and location, its reason
    as the explanation, its remediation as the option, and its causes as nested links."""
    from ..spec.errors import SpecError

    if not isinstance(error, SpecError):
        return component(
            actor,
            "system_error",
            f"{type(error).__name__}: {error}",
            "environment",
            "the operating system refused an operation Spec tooling needed",
        )
    where = error.where()
    return link(
        "component",
        actor,
        error.code,
        str(error) + (f" (at {where})" if where else ""),
        reason={"system_error": "environment", "unexpected_error": "capability"}.get(
            error.code, "input"
        ),
        explanation=error.reason,
        evidence=[evidence("location", where, "")] if where else [],
        options=[error.remediation],
        recommendation=error.remediation,
        causes=[spec_cause(cause, actor) for cause in error.causes],
    )


def spec_finding(rule_id: str, source: str, line, message: str, explanation: str):
    """The link of one Spec validation finding, as Spec core reported it."""
    location = (source or "-") + (f":{line}" if line else "")
    return link(
        "component",
        "Spec core validation",
        "spec_finding",
        f"{rule_id} at {location}: {message}",
        reason="capability",
        explanation=explanation,
        evidence=[evidence("finding", location, rule_id)],
    )


# How an Operation treats each error code of a worker run record: the reason it cannot handle it,
# the explanation, the options it offers the main agent and its recommendation.
WORKER_HANDLING = {
    "audit_violation": (
        "permission",
        "an Operation never widens a grant and never retries with a wider one; giving the "
        "task the path (declaring it pending through specify, or binding more Modules) is the "
        "main agent's decision",
        [
            "run specify to declare the path as a pending file of a bound Module",
            "bind the Module that owns the path and run the Operation again",
            "discard the stray change and run the Operation with a narrower goal",
        ],
    ),
    "checks_failed": (
        "decision",
        "the Operation used every resume round it is configured with; whether to narrow the "
        "goal, change the Spec or allow more rounds is the main agent's decision",
        [
            "run the Operation again with a narrower goal or more --rounds",
            "run understand to check whether the Spec supports the change",
            "run test to get an interpretation of the failures",
        ],
    ),
    "worker_blocked": (
        "decision",
        "the worker's blocker needs a decision, a permission or a Spec change above the "
        "Operation",
        [
            "follow the worker's options in the cause",
            "run specify when the worker names a Spec gap",
        ],
    ),
    "worker_failed": (
        "decision",
        "the Operation does not rerun a worker that failed; rerunning or changing the task is "
        "the main agent's decision",
        ["follow the worker's options in the cause", "run the Operation again"],
    ),
    "worker_timeout": (
        "exhausted",
        "the Operation passes the configured limits to Workers and does not raise them; "
        f"raising limits.timeout_seconds in {CONFIG} is the main agent's decision",
        [
            f"raise limits.timeout_seconds in {CONFIG}",
            "run the Operation with a narrower goal",
        ],
    ),
    "worker_limit_reached": (
        "exhausted",
        "the Operation passes the configured limits to Workers and does not raise them; "
        f"raising limits.max_turns or limits.max_budget_usd in {CONFIG} is the main agent's "
        "decision",
        [
            f"raise limits.max_turns or limits.max_budget_usd in {CONFIG}",
            "run the Operation with a narrower goal",
        ],
    ),
    "worker_result_invalid": (
        "capability",
        "the Operation cannot repair a worker's answer and does not relaunch a worker",
        ["run the Operation again", "inspect the transcript in the cause's evidence"],
    ),
}
ENVIRONMENT_HANDLING = (
    "environment",
    "the failure lies in the environment the Operation runs in, which it cannot change",
    ["repair the environment named in the cause and run the Operation again"],
)


def interpreter_roots(interpreter: str, home: Path | None = None) -> tuple[Path, ...]:
    """What must be readable for a worker to run ``interpreter``.

    The sandbox makes a path readable at its real location, so the environment the interpreter
    belongs to and the installation it resolves to are not enough when the way between them
    passes through a symbolic link, such as uv's ``cpython-3.9-linux-x86_64-gnu`` pointing to
    ``cpython-3.9.25-linux-x86_64-gnu``: the directory holding each link on the way must be
    readable too. A directory that is the home itself or holds it is never included.
    """
    home = Path(os.path.realpath(home or Path.home()))
    roots = [Path(interpreter).parent.parent]
    pending = list(Path(interpreter).parts[1:])
    current = Path("/")
    hops = 0
    while pending and hops < 40:
        part = pending.pop(0)
        if part in ("", "."):
            continue
        if part == "..":
            current = current.parent
            continue
        candidate = current / part
        if candidate.is_symlink():
            hops += 1
            roots.append(current)
            target = Path(os.readlink(candidate))
            if target.is_absolute():
                current = Path("/")
                pending = list(target.parts[1:]) + pending
            else:
                pending = list(target.parts) + pending
        else:
            current = candidate
    roots.append(Path(os.path.realpath(interpreter)).parent.parent)
    return tuple(
        dict.fromkeys(
            root
            for root in roots
            if root.exists()
            and root != Path("/usr")
            and not (root == home or root in home.parents)
        )
    )


def withhold_writes(value: dict) -> dict:
    """A grant with every ``rw`` entry lowered to ``ro``; the entry list is otherwise unchanged."""
    return {
        **value,
        "entries": [
            {**entry, "level": "ro"} if entry["level"] == "rw" else dict(entry)
            for entry in value["entries"]
        ],
    }


@dataclass
class RunContext:
    name: str
    # The records directory: the binding's, or an unbound worktree's own ``.concorde``.
    records: Path
    # The workspace binding, or None for an unbound run.
    workspace: dict | None
    # The worktree the run works in: the bound workspace, or an unbound run's checkout.
    worktree: Path
    modules: list[str]
    run_id: str
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

    def run_worker(
        self,
        instructions: str,
        *,
        task_type: str,
        output_schema: dict | None = None,
        checks: bool = False,
        rounds: int | None = None,
        modules: list[str] | None = None,
        worker: str | None = None,
        read_only: bool = False,
        readable: tuple[Path, ...] = (),
        after_round=None,
    ):
        """The standard worker sequence; returns ``Continue`` or ``Stop``.

        ``worker`` is the id of the worker to launch, one the provider declares; the worker
        configuration chooses its backend, model and level.

        ``read_only`` withholds every writable level of the task type's grant, turning it into
        read access, as the Protocol lets a harness give less than a type assigns. ``readable``
        names host material outside the grant the worker may read as well, such as the logs of
        the checks the host ran for this run.
        """
        from ..harness.checks import checked_modules
        from ..harness.workers import WorkerRequest, run_worker
        from ..spec.grants import grant
        from ..spec.repository import SpecRepository
        from ..spec.repository_base import SpecError

        bound = modules or self.modules
        worker = worker or self.workers[0]
        if worker not in self.workers:
            raise ValueError(
                f"{self.name} declares the workers {', '.join(self.workers)}, not {worker}"
            )
        if self.unbound and task_type in WRITING_TASK_TYPES and not read_only:
            return self.fail(
                "failed",
                "unbound_write",
                f"A {task_type} worker needs a bound workspace.",
                f"{self.name} ran unbound in a checkout of {self.started_in}, which has no "
                f"workspace binding, and asked for a {task_type} worker, which may change "
                "files; an unbound run launches only read-only workers",
                reason="scope",
                explanation="changing Specs or code happens only in a bound workspace, which "
                "this run does not have",
                options=[
                    "run the Operation in a bound workspace, such as a task worktree "
                    "(concorde task open)"
                ],
            )
        try:
            frozen = grant(SpecRepository(self.worktree), bound, task_type).value
        except (SpecError, OSError, ValueError) as error:
            return self.grant_failure(task_type, bound, error)
        if read_only:
            frozen = withhold_writes(frozen)
            self.evidence.append(
                evidence(
                    "grant-withheld",
                    task_type,
                    "every writable level of the grant was lowered to read",
                )
            )
        try:
            config = load(self.worktree)
            backend, model = self.worker_model(worker, config)
        except ModelConfigError as error:
            return self.model_failure(worker, error)
        bounds = limits(config)
        readable_paths = tuple(
            Path(path) if os.path.isabs(path) else self.worktree / path
            for path in runtime(config)
            if (Path(path) if os.path.isabs(path) else self.worktree / path).exists()
        ) + tuple(Path(path) for path in readable if Path(path).exists())
        interpreter = self.project_interpreter()
        if interpreter is not None:
            # The environment the interpreter belongs to, and the installation it links to,
            # must be readable for the worker to run it; neither is ever writable.
            readable_paths += interpreter_roots(interpreter)
        record = run_worker(
            WorkerRequest(
                worktree=self.worktree,
                records=self.records,
                task_type=task_type,
                grant=frozen,
                instructions=instructions,
                check_modules=(
                    checked_modules(SpecRepository(self.worktree), bound)
                    if checks
                    else None
                ),
                runtime=readable_paths,
                output_schema=output_schema,
                rounds=rounds if rounds is not None else bounds["rounds"],
                timeout=float(bounds["timeout_seconds"]),
                max_turns=bounds["max_turns"],
                max_budget_usd=bounds["max_budget_usd"],
                model=model["model"],
                backend=backend,
                backend_source=model["backend_source"],
                reasoning=model["reasoning"],
                operation=self.name,
                worker=worker,
                operation_run=self.run_id,
                after_round=after_round,
                project_python=interpreter,
                started=self.worker_started,
            )
        )
        return self.absorb(record)

    def worker_started(self, run_id: str) -> None:
        """Name a worker run as soon as it exists, so a cancelled Operation still names it."""
        if run_id not in self.worker_runs:
            self.worker_runs.append(run_id)

    def project_interpreter(self) -> str | None:
        """The project's own interpreter, as its checks run it, or None when none is configured
        or it cannot be found."""
        from ..harness.checks import CheckError, project_python
        from ..spec.repository import SpecRepository
        from ..spec.repository_base import SpecError

        try:
            config = SpecRepository(self.worktree).config
            if not config.get("python"):
                return None
            return project_python(self.worktree, config, "worker")
        except (CheckError, SpecError, OSError):
            return None

    def worker_model(self, worker: str, config: dict | None = None) -> tuple[str, dict]:
        """The backend of this Operation's worker ``worker`` — the one the worker configuration
        of the worktree the run works in chooses, otherwise pi — and the model and level chosen
        for it there."""
        chosen = worker_choice(
            load(self.worktree) if config is None else config, self.name, worker
        )
        return chosen["backend"], chosen

    def model_failure(self, worker: str, error) -> Stop:
        """Stop ``failed``: the backend or the worker configuration cannot be settled."""
        path = config_path(self.worktree).as_posix()
        reason = HANDLING.get(error.code, ("input",))[0]
        return self.fail(
            "failed",
            "worker_model_unavailable",
            f"The {worker} worker could not be configured ({error.code}).",
            f"the backend and model of the {worker} worker of {self.name} in {self.worktree} "
            f"cannot be settled: {error.code}: {error} (configuration file {path})",
            reason=reason,
            explanation="an Operation runs a worker on the program the worker configuration "
            "chooses for it, otherwise on pi, with the model, level and limits given there, and "
            "never guesses, repairs or falls back from any of them",
            evidence=[evidence("worker_configuration", path, f"{error.code}: {error}")],
            causes=[
                component(
                    "Workers (worker configuration)",
                    error.code,
                    str(error),
                    reason,
                    "Workers reads the backend, model, level and limits from the file and "
                    "changes nothing",
                )
            ],
            options=[
                (
                    "install the program the worker runs on, or edit the backend of "
                    f"operations.{self.name}.workers.{worker} in {path}"
                ),
                f"correct {path} as the error says and commit it; an unbound run reads the "
                "committed file of its checkout",
            ],
        )

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

    def grant_failure(self, task_type: str, modules: list[str], error) -> Stop:
        code = getattr(error, "code", None) or "grant_unavailable"
        names = ", ".join(modules)
        return self.fail(
            "failed",
            "grant_unavailable",
            f"The {task_type} grant for {names} could not be computed ({code}).",
            f"the {task_type} grant for {names} cannot be computed from the Specs of "
            f"{self.worktree}: {code}: {error}",
            reason="scope",
            explanation="an Operation computes grants from the workspace's Specs and never "
            "repairs them; the Specs or the bound Modules must change first",
            evidence=[evidence("grant", names, f"{code}: {error}")],
            causes=[spec_cause(error, "Spec core (grant)")],
            options=[
                "bind every Module that binds the shared file",
                "repair the Specs with specify or by hand",
                "run concorde task-validation for every structural finding",
            ],
        )

    def checks_unavailable(self, error, modules: list[str] | None = None) -> Stop:
        """Stop ``failed`` because Check execution could not run the configured checks; its own
        link is the cause."""
        from ..harness.checks import service_error

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

    def absorb(self, record: dict):
        """Map one worker run record to a step outcome, adding host evidence."""
        self.worker_started(record["run_id"])
        self.last_record = record
        self.worker = record.get("worker_result")
        found = [
            evidence(
                "grant",
                record.get("grant_digest") or "",
                f"{record['task_type']} grant",
            ),
            evidence("context-identity", record.get("context_identity") or "", ""),
            evidence(
                "worker-model",
                record.get("backend") or "",
                f"{record.get('worker') or 'worker'} (backend from "
                f"{record.get('backend_source') or 'the request'}): model "
                f"{record.get('model') or 'the backend default'}, reasoning "
                f"{record.get('reasoning') or 'the backend default'}",
            ),
        ]
        rounds = record.get("rounds") or []
        for item in rounds:
            audit = item.get("audit")
            if audit:
                found.append(
                    evidence(
                        "audit",
                        str(item["round"]),
                        f"{len(audit['changed'])} changed, violations: {', '.join(audit['violations']) or 'none'}",
                    )
                )
            for check in item.get("checks") or []:
                found.append(
                    evidence(
                        "check",
                        check["check_id"],
                        f"{check['status']}, exit {check['exit_code']}; log {check['log']}",
                    )
                )
        found.append(evidence("rounds", "", f"{len(rounds)} round(s)"))
        if record.get("transcript"):
            found.append(evidence("transcript", record["transcript"], ""))
        if record.get("stderr_tail"):
            found.append(
                evidence("stderr", record["run_id"], record["stderr_tail"][-2000:])
            )
        status = record["status"]
        if status == "ok":
            return Continue(output=(self.worker or {}).get("output"), evidence=found)
        cause = record.get("error")
        code = cause["code"] if cause else "worker_run_failed"
        reason, explanation, options = WORKER_HANDLING.get(code, ENVIRONMENT_HANDLING)
        worker_options = [
            option
            for item in (cause or {}).get("causes", [])
            for option in item["options"]
        ]
        detail = (
            f"the {record['task_type']} worker run {record['run_id']} ended {status}: "
            f"{code}: {cause['detail'] if cause else 'the run record carries no error'}"
        )
        return self.fail(
            status,
            code,
            f"The worker run {record['run_id']} ended {status} ({code}).",
            detail,
            reason=reason,
            explanation=explanation,
            host_evidence=found,
            causes=[cause],
            options=worker_options + options,
        )


__all__ = [
    "Continue",
    "Provider",
    "RunContext",
    "Stop",
    "command",
    "component",
    "evidence",
    "spec_cause",
    "spec_finding",
]
