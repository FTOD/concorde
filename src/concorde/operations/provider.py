"""What an Operation provider declares, and the context and outcomes its steps work with.

A provider is a fixed list of steps. Each step receives the run's ``RunContext`` and returns
``Continue`` (with any output and host evidence it produced) or ``Stop`` (with a status, a summary,
host evidence and, unless the status is ``ok``, the Operation's error link). ``RunContext.fail``
builds that link: the Operation's own account of the error and why it cannot handle it, with the
errors it received from its children as causes. ``RunContext.run_worker`` is the standard worker
sequence: it computes the grant from the task worktree's Specs, runs one worker through Workers
and maps its outcome to a step outcome.
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from ..errors import evidence, from_exception, link
from ..harness.models import (
    HANDLING,
    ModelConfigError,
    config_path,
    load,
    selection,
    worker_backend,
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
    name: str
    task_type: str | None
    writes: bool
    steps: tuple[Callable, ...]
    output_schema: dict | None = None
    add_arguments: Callable[[argparse.ArgumentParser], None] | None = None
    # False for a provider that diagnoses the task worktree's Specs itself, such as validate:
    # the host then begins the run even when those Specs cannot be loaded.
    requires_loaded_specs: bool = True
    # "required": every run names a task. "optional": a run without --task works on the
    # primary worktree (project scope) and may launch only read-only workers.
    task_scope: str = "required"
    # The roles of the workers the Operation launches; the first is the default role. The worker
    # model configuration is keyed by Operation and role.
    roles: tuple[str, ...] = ("worker",)


# Task types whose workers may change files; a project-scope run never launches one.
WRITING_TASK_TYPES = ("specify", "implement", "code-to-spec")


PACKAGE_ROOT = Path(__file__).resolve().parents[3]


def load_prompt(name: str) -> str:
    """The rendered worker prompt ``generated/workers/<name>.md`` of this package."""
    path = PACKAGE_ROOT / "generated/workers" / f"{name}.md"
    if not path.is_file():
        raise FileNotFoundError(
            f"{path} is missing; run the build (python3 scripts/concorde.py build)"
        )
    return path.read_text(encoding="utf-8")


# The Protocol copy's guide to writing a Module specification, in every project Concorde is
# installed in; Spec-writing workers receive it with their brief, since no grant shows it.
PROTOCOL_GUIDE = ".concorde/protocol/kinds/module.md"


def protocol_guide(worktree: Path) -> str:
    """The project's Protocol writing guide as brief material, or a note that it is missing."""
    path = worktree / PROTOCOL_GUIDE
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        return (
            f"\n\n## The Protocol's writing guide\n\n(The project's copy {PROTOCOL_GUIDE} "
            f"cannot be read: {error}; follow the rules above.)\n"
        )
    return (
        f"\n\n## The Protocol's writing guide\n\nThe project's Protocol copy "
        f"({PROTOCOL_GUIDE}), which the host validates your documents against:\n\n"
        + text.strip()
        + "\n"
    )


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
        "raising workers.timeout_seconds in .concorde/config.json is the main agent's decision",
        ["raise workers.timeout_seconds", "run the Operation with a narrower goal"],
    ),
    "worker_limit_reached": (
        "exhausted",
        "the Operation passes the configured limits to Workers and does not raise them; "
        "raising workers.max_turns or workers.max_budget_usd is the main agent's decision",
        [
            "raise workers.max_turns or workers.max_budget_usd",
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
    operation: str
    primary: Path
    task: dict
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
    # The worker roles the provider declares; the first is the default.
    roles: tuple[str, ...] = ("worker",)

    @property
    def project_scope(self) -> bool:
        """Whether the run works without a task, on the primary worktree."""
        return not self.task.get("id")

    def workers_config(self) -> dict:
        config = json.loads((self.worktree / ".concorde/config.json").read_text())
        return config.get("workers") or {}

    def run_worker(
        self,
        instructions: str,
        *,
        task_type: str,
        output_schema: dict | None = None,
        checks: bool = False,
        rounds: int | None = None,
        modules: list[str] | None = None,
        role: str | None = None,
        read_only: bool = False,
        readable: tuple[Path, ...] = (),
    ):
        """The standard worker sequence; returns ``Continue`` or ``Stop``.

        ``read_only`` withholds every writable level of the task type's grant, turning it into
        read access, as the Protocol lets a harness give less than a type assigns. ``readable``
        names host material outside the grant the worker may read as well, such as the logs of
        the checks the host ran for this run.
        """
        from ..harness.workers import WorkerRequest, run_worker
        from ..spec.grants import grant
        from ..spec.repository import SpecRepository
        from ..spec.repository_base import SpecError

        bound = modules or self.modules
        role = role or self.roles[0]
        if self.project_scope and task_type in WRITING_TASK_TYPES and not read_only:
            return self.fail(
                "failed",
                "project_scope_write",
                f"A {task_type} worker needs a task.",
                f"{self.operation} ran without a task in {self.worktree} and asked for a "
                f"{task_type} worker, which may change files; a run without a task launches only "
                "read-only workers",
                reason="scope",
                explanation="changing Specs or code happens only inside a task's worktree, which "
                "this run does not have",
                options=["open a task and run the Operation with --task"],
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
            backend, model = self.worker_model(role)
        except ModelConfigError as error:
            return self.model_failure(role, error)
        config = self.workers_config()
        runtime = tuple(
            Path(path) if os.path.isabs(path) else self.worktree / path
            for path in config.get("runtime", [".venv", "node_modules"])
            if (Path(path) if os.path.isabs(path) else self.worktree / path).exists()
        ) + tuple(Path(path) for path in readable if Path(path).exists())
        record = run_worker(
            WorkerRequest(
                worktree=self.worktree,
                task_type=task_type,
                grant=frozen,
                instructions=instructions,
                check_modules=bound if checks else None,
                runtime=runtime,
                output_schema=output_schema,
                rounds=rounds if rounds is not None else int(config.get("rounds", 3)),
                timeout=float(config.get("timeout_seconds", 1800)),
                max_turns=int(config.get("max_turns", 200)),
                max_budget_usd=config.get("max_budget_usd"),
                model=model["model"],
                backend=backend,
                backend_source=model["backend_source"],
                reasoning=model["reasoning"],
                operation=self.operation,
                role=role,
            )
        )
        return self.absorb(record)

    def worker_model(self, role: str) -> tuple[str, dict]:
        """The backend of this Operation's worker ``role`` — the worktree's configured one, or the
        main session's — and the worktree's model choice for it in that backend."""
        config = load(self.worktree)
        backend, source = worker_backend(config, self.operation, role)
        return backend, {
            **selection(config, backend, self.operation, role),
            "backend_source": source,
        }

    def model_failure(self, role: str, error) -> Stop:
        """Stop ``failed``: the backend or the worker model configuration cannot be settled."""
        path = config_path(self.worktree).as_posix()
        reason = HANDLING.get(error.code, ("input",))[0]
        return self.fail(
            "failed",
            "worker_model_unavailable",
            f"The {role} worker could not be configured ({error.code}).",
            f"the backend and model of the {role} worker of {self.operation} in {self.worktree} "
            f"cannot be settled: {error.code}: {error} (configuration file {path})",
            reason=reason,
            explanation="an Operation runs a worker on the program the worktree's configuration "
            "chooses, otherwise on the main session's, with the worktree's model choice, and "
            "never guesses, repairs or falls back from either",
            evidence=[evidence("worker_models", path, f"{error.code}: {error}")],
            causes=[
                component(
                    "Workers (worker model configuration)",
                    error.code,
                    str(error),
                    reason,
                    "Workers reads the backend and models from the file and the client from the "
                    "environment, and changes neither",
                )
            ],
            options=[
                (
                    "run the Operation from the Claude Code or pi main session, or set "
                    "CONCORDE_CLIENT"
                ),
                (
                    "install the program the backend section of the configuration chooses, or "
                    "change that entry by hand"
                ),
                (
                    "inspect and fix the configuration with concorde run configure_workers"
                    + (f" --task {self.task['id']}" if not self.project_scope else "")
                ),
            ],
        )

    @property
    def actor(self) -> str:
        if self.project_scope:
            return (
                f"Operation {self.operation} {self.run_id} (no task, {self.worktree})"
            )
        return f"Operation {self.operation} {self.run_id} (task {self.task['id']})"

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
                "operation",
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
            explanation="an Operation computes grants from the task worktree's Specs and never "
            "repairs them; the Specs or the bound Modules must change first",
            evidence=[evidence("grant", names, f"{code}: {error}")],
            causes=[spec_cause(error, "Spec core (grant)")],
            options=[
                "bind every Module that binds the shared file",
                "repair the Specs with specify or by hand",
                "run validate for every structural finding",
            ],
        )

    def checks_unavailable(self, error, modules: list[str] | None = None) -> Stop:
        """Stop ``failed`` because Check execution could not run the configured checks."""
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
            causes=[
                component(
                    "Check execution",
                    code,
                    str(error),
                    "environment",
                    "a check that cannot run as configured produces no result",
                )
            ],
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
        self.worker_runs.append(record["run_id"])
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
                f"{record.get('role') or 'worker'} (backend from "
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
    "component",
    "evidence",
    "load_prompt",
    "spec_cause",
    "spec_finding",
]
