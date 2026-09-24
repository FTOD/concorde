"""The ``validate`` Operation: decide a task worktree's readiness (see the Validation Spec).

1. Require that the task worktree's head is the task branch.
2. Measure the inputs.
3. Validate the structure of the task worktree's Specs, as they read with the confirmations applied.
4. Sort the findings: errors block, filled pending entries become confirmations, warnings are kept.
5. Require every changed path to be a document member, a control record or bound by a Module.
6. Derive the changed Modules.
7. Run the configured checks of the changed and the bound Modules.
8. Measure the inputs again and compare the input digest.
9. Save the readiness in the run directory and return it as the output.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from ..errors import link
from ..harness.checks import affected_modules, check_error, run_checks
from ..operations.provider import (
    Continue,
    Provider,
    RunContext,
    Stop,
    component,
    evidence,
    spec_cause,
)
from ..spec.repository import SpecRepository
from ..spec.repository_base import SpecError, bound_by, control_path, covers
from ..spec.validation import (
    build_path,
    generated,
    generated_outputs,
    validate_repository,
)
from . import confirmations as confirming
from .measurement import MeasurementError, current_branch, measure

SHA256 = {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"}
COMMIT = {"type": "string", "pattern": "^[0-9a-f]{40}([0-9a-f]{24})?$"}
TEXT = {"type": "string", "minLength": 1}

READINESS_SCHEMA: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "task",
        "ready",
        "inputs",
        "modules",
        "blocking",
        "warnings",
        "confirmations",
        "checks",
    ],
    "properties": {
        "task": TEXT,
        "ready": {"type": "boolean"},
        "inputs": {
            "type": "object",
            "additionalProperties": False,
            "required": ["head", "base", "changed", "config_digest", "digest"],
            "properties": {
                "head": COMMIT,
                "base": COMMIT,
                "changed": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["path", "digest"],
                        "properties": {
                            "path": TEXT,
                            "digest": {"anyOf": [{"type": "null"}, SHA256]},
                        },
                    },
                },
                "config_digest": SHA256,
                "digest": SHA256,
            },
        },
        "modules": {"type": "array", "items": TEXT},
        "blocking": {"type": "array", "items": {"$ref": "#/$defs/finding"}},
        "warnings": {"type": "array", "items": {"$ref": "#/$defs/finding"}},
        "confirmations": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "module",
                    "realization",
                    "entry",
                    "metadata",
                    "metadata_digest",
                ],
                "properties": {
                    "module": TEXT,
                    "realization": TEXT,
                    "entry": TEXT,
                    "metadata": TEXT,
                    "metadata_digest": SHA256,
                },
            },
        },
        "checks": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "check",
                    "module",
                    "status",
                    "exit_code",
                    "measured_digest",
                    "log",
                ],
                "properties": {
                    "check": TEXT,
                    "module": TEXT,
                    "status": {"enum": ["passed", "failed", "timeout"]},
                    "exit_code": {"anyOf": [{"type": "null"}, {"type": "integer"}]},
                    "measured_digest": SHA256,
                    "log": TEXT,
                },
            },
        },
    },
    "$defs": {
        "finding": {
            "type": "object",
            "additionalProperties": False,
            "required": ["kind", "ref", "detail"],
            "properties": {
                "kind": {"enum": ["load", "structural", "unbound", "check"]},
                "ref": TEXT,
                "detail": TEXT,
            },
        }
    },
}


@dataclass
class State:
    inputs: dict | None = None
    repository: SpecRepository | None = None
    blocking: list[dict] = field(default_factory=list)
    warnings: list[dict] = field(default_factory=list)
    confirmations: list[dict] = field(default_factory=list)
    changed_modules: list[str] = field(default_factory=list)
    checks: list[dict] = field(default_factory=list)
    # The error link of each blocking finding, in the order of ``blocking``.
    links: list[dict] = field(default_factory=list)


def _state(ctx: RunContext) -> State:
    if not hasattr(ctx, "validation"):
        ctx.validation = State()
    return ctx.validation


def finding(kind: str, ref: str, detail: str) -> dict:
    return {"kind": kind, "ref": ref or "-", "detail": detail or "-"}


# Why no step of validate repairs a finding of each kind, and what repairs it.
FINDING_HANDLING = {
    "load": (
        "Spec core",
        "the task worktree's Specs do not load; validate diagnoses them and never repairs them",
    ),
    "structural": (
        "Spec core validation",
        "validate diagnoses the Specs; repairing a Spec is a specify task or a hand edit",
    ),
    "unbound": (
        "Validation",
        "binding a changed path to a Module is a Spec change, which validate never makes",
    ),
    "check": (
        "Check execution",
        "the check could not run as configured; validate never changes a check",
    ),
}


def block(state: "State", kind: str, ref: str, detail: str, cause: dict | None = None):
    """Record one blocking finding with its error link."""
    state.blocking.append(finding(kind, ref, detail))
    actor, explanation = FINDING_HANDLING[kind]
    state.links.append(
        cause
        or link(
            "component",
            actor,
            f"{kind}_finding",
            f"{ref}: {detail}",
            reason="capability",
            explanation=explanation,
            evidence=[evidence(kind, ref, detail)],
        )
    )


def require_task_branch(ctx: RunContext):
    """Stop unless the task worktree's head is on the task branch (shared with Delivery)."""
    branch = current_branch(ctx.worktree)
    expected = ctx.task["branch"]
    if branch != expected:
        found = branch or "a detached head"
        return ctx.fail(
            "failed",
            "wrong_branch",
            f"The task worktree is on {found}, not on the task branch {expected}.",
            f"the task worktree {ctx.worktree} is on {found}, but {ctx.operation} works only "
            f"on the task branch {expected}",
            reason="permission",
            explanation="Operations never switch branches or change Git state of a task "
            "worktree; only the main agent does",
            evidence=[evidence("git", "wrong_branch", f"{ctx.worktree} is on {found}")],
            options=[f"check out {expected} in {ctx.worktree}"],
            recommendation=f"check out {expected} and run the Operation again",
        )
    return Continue()


def measurement_failed(ctx: RunContext, error: MeasurementError) -> Stop:
    return ctx.fail(
        "failed",
        "measurement_failed",
        f"The inputs of the task worktree could not be measured ({error.code}).",
        f"the changes of {ctx.worktree} since {ctx.task.get('base_commit')} cannot be "
        f"measured: {error.code}: {error}",
        reason="environment",
        explanation="the measurement reads Git and the configuration; the Operation cannot "
        "repair either",
        evidence=[evidence("git", error.code, str(error))],
        causes=[
            component(
                "Validation measurement",
                error.code,
                str(error),
                "environment",
                "Git or the configuration could not be read",
            )
        ],
        options=[
            "repair the worktree's Git state",
            "restore .concorde/config.json",
        ],
    )


def check_branch(ctx: RunContext):
    return require_task_branch(ctx)


def measure_inputs(ctx: RunContext):
    try:
        _state(ctx).inputs = measure(ctx.worktree, ctx.task["base_commit"])
    except MeasurementError as error:
        return measurement_failed(ctx, error)
    return Continue()


def _structural(item) -> dict:
    location = item.source + (f":{item.line}" if item.line else "")
    return finding("structural", f"{item.rule_id} {location}", item.message)


def validate_structure(ctx: RunContext):
    state = _state(ctx)
    overrides: dict[str, bytes] = {}
    load_error = None
    try:
        state.repository = SpecRepository(ctx.worktree)
        state.confirmations, overrides = confirming.plan(state.repository)
    except (SpecError, OSError, ValueError) as error:
        load_error = error
        state.repository = None
        block(
            state,
            "load",
            getattr(error, "path", None) or ".concorde/specs.json",
            error.describe() if isinstance(error, SpecError) else str(error),
            spec_cause(error),
        )
    # The load error's own causes are the fatal problems; validation reports them again.
    reported = {
        (getattr(cause, "rule_id", None), cause.path, str(cause))
        for cause in getattr(load_error, "causes", ())
    }
    if state.repository is not None:
        for module in ctx.modules:
            if module not in state.repository.modules:
                block(
                    state,
                    "structural",
                    module,
                    f"the task names {module}, which the task worktree's registry does "
                    "not register",
                )
    result = validate_repository(ctx.worktree, document_overrides=overrides or None)
    changed = {
        item["path"] for item in state.inputs["changed"] if item["digest"] is not None
    }
    for item in result.findings:
        if item.rule_id == "CONCORDE-SOURCE-008":
            if load_error is None:
                block(state, "load", item.source, item.message)
            continue
        if (item.rule_id, item.source or None, f"{item.rule_id}: {item.message}") in (
            reported
        ):
            continue
        if item.severity == "error":
            if (
                item.rule_id == "CHK.binds.unbound"
                and item.source in changed
                and state.repository is not None
            ):
                continue  # reported once, as an unbound change, by require_accounted
            value = _structural(item)
            block(state, "structural", value["ref"], value["detail"])
        elif item.severity == "warning":
            state.warnings.append(_structural(item))
    summary = result.result.get("summary", {})
    return Continue(
        evidence=[
            evidence(
                "readiness",
                "structure",
                f"{summary.get('errors', 0)} error(s), {summary.get('warnings', 0)} "
                f"warning(s), {len(state.confirmations)} confirmation(s)",
            )
        ]
    )


def sort_findings(ctx: RunContext):
    """Errors already block and warnings are kept; confirmations are listed, never blocking."""
    state = _state(ctx)
    state.confirmations.sort(key=lambda item: (item["module"], item["entry"]))
    return Continue()


def require_accounted(ctx: RunContext):
    state = _state(ctx)
    repository = state.repository
    if repository is None:
        return Continue()
    members = set(repository.source_documents)
    outputs = generated_outputs(repository.root)
    entries = [
        entry for module in repository.modules.values() for entry in module.files
    ]
    external = [
        entry
        for module in repository.modules.values()
        for entry in repository.external_inclusions(module)
    ]
    for item in state.inputs["changed"]:
        path = item["path"]
        if item["digest"] is None:
            continue  # a deletion leaves nothing to bind
        if (
            path in members
            or control_path(path)
            or generated(path, outputs)
            or build_path(path)
            or any(covers(entry, path) for entry in external)
            or any(bound_by(entry, path) for entry in entries)
        ):
            continue
        block(
            state,
            "unbound",
            path,
            "no Module binds this changed path and it is neither a Spec document member "
            "nor a control record",
        )
    return Continue()


def derive_changed_modules(ctx: RunContext):
    state = _state(ctx)
    if state.repository is None:
        return Continue()
    paths = [item["path"] for item in state.inputs["changed"]]
    state.changed_modules = affected_modules(state.repository, paths)
    return Continue()


def run_configured_checks(ctx: RunContext):
    state = _state(ctx)
    if state.repository is None:
        return Continue()
    selected = sorted(set(state.changed_modules) | set(ctx.modules))
    log_directory = ctx.run_dir / "checks"
    found = []
    for module in selected:
        try:
            results = run_checks(
                ctx.worktree, modules=[module], log_directory=log_directory
            )
        except SpecError as error:
            if error.code == "check_sandbox_unavailable":
                stop = ctx.checks_unavailable(error, [module])
                stop.evidence[:0] = found
                return stop
            if error.code == "stale_evidence":
                return inputs_changed(ctx, found, str(error))
            block(state, "check", module, f"{error.code}: {error}")
            found.append(evidence("check", module, f"{error.code}: {error}"))
            continue
        for result in results:
            log = Path(result["log"])
            try:
                log = log.relative_to(ctx.primary)
            except ValueError:
                pass
            timeout = result["status"] == "timeout"
            entry = {
                "check": result["check_id"],
                "module": result["module"],
                "status": result["status"],
                "exit_code": None if timeout else result["exit_code"],
                "measured_digest": result["source_digest"],
                "log": log.as_posix(),
            }
            state.checks.append(entry)
            exit_text = "timed out" if timeout else f"exit {result['exit_code']}"
            found.append(
                evidence(
                    "check",
                    entry["check"],
                    f"{entry['status']}, {exit_text}; log {entry['log']}",
                )
            )
            if result["status"] != "passed":
                block(
                    state,
                    "check",
                    entry["check"],
                    f"{entry['module']} check {entry['status']} ({exit_text}); "
                    f"log {entry['log']}",
                    check_error(result),
                )
    return Continue(evidence=found)


def inputs_changed(ctx: RunContext, found: list[dict], detail: str) -> Stop:
    return ctx.fail(
        "failed",
        "inputs_changed",
        "The task worktree changed while validate ran (inputs_changed); no readiness was "
        "issued.",
        f"the task worktree {ctx.worktree} changed while validate ran, so no readiness "
        f"describes it: {detail}",
        reason="environment",
        explanation="something outside validate changed the worktree; a readiness is only "
        "issued for inputs that stayed the same",
        evidence=[evidence("readiness", "inputs_changed", detail)],
        host_evidence=found,
        options=["let the worktree settle and run validate again"],
        recommendation="run validate again once nothing else changes the worktree",
    )


def remeasure(ctx: RunContext):
    state = _state(ctx)
    try:
        again = measure(ctx.worktree, ctx.task["base_commit"])
    except MeasurementError as error:
        return measurement_failed(ctx, error)
    if again["digest"] != state.inputs["digest"]:
        return inputs_changed(
            ctx,
            [],
            f"input digest {state.inputs['digest']} at the start, {again['digest']} at "
            "the end",
        )
    return Continue()


def readiness_of(ctx: RunContext) -> tuple[dict, list[dict]]:
    """The readiness the steps before decided, saved in the run directory, and its evidence."""
    state = _state(ctx)
    modules = sorted(set(state.changed_modules) | set(ctx.modules))
    readiness = {
        "task": ctx.task["id"],
        "ready": not state.blocking,
        "inputs": state.inputs,
        "modules": modules,
        "blocking": state.blocking,
        "warnings": state.warnings,
        "confirmations": state.confirmations,
        "checks": state.checks,
    }
    path = ctx.run_dir / "readiness.json"
    path.write_text(json.dumps(readiness, indent=2) + "\n")
    saved = path.relative_to(ctx.primary).as_posix()
    found = [
        evidence(
            "readiness",
            state.inputs["digest"],
            f"{'ready' if readiness['ready'] else 'not ready'}; "
            f"{len(state.inputs['changed'])} changed path(s), {len(state.checks)} check(s), "
            f"{len(state.warnings)} warning(s); saved {saved}",
        )
    ]
    return readiness, found


def not_deliverable(ctx: RunContext) -> dict:
    """The Validation link explaining why the decided readiness is not ready."""
    state = _state(ctx)
    reasons = [
        f"{item['kind']} {item['ref']}: {item['detail']}" for item in state.blocking
    ]
    return component(
        "Validation",
        "not_deliverable",
        f"task {ctx.task['id']} is not deliverable: {len(reasons)} blocking finding(s), each "
        "a cause below: " + " | ".join(reasons),
        "decision",
        "Validation only decides readiness and never repairs; each finding needs a Spec "
        "change (specify) or a code change (implement)",
        evidence=[
            evidence("blocking", item["ref"], item["detail"]) for item in state.blocking
        ],
        causes=state.links,
    )


def issue_readiness(ctx: RunContext):
    state = _state(ctx)
    readiness, found = readiness_of(ctx)
    ctx.output = readiness
    saved = (ctx.run_dir / "readiness.json").relative_to(ctx.primary).as_posix()
    if readiness["ready"]:
        return Stop("ok", "Readiness decided: ready.", found)
    reasons = [
        f"{item['kind']} {item['ref']}: {item['detail']}" for item in state.blocking
    ]
    return ctx.fail(
        "blocked",
        "not_deliverable",
        f"Not deliverable: {len(reasons)} blocking finding(s). " + " | ".join(reasons),
        f"task {ctx.task['id']} is not deliverable: {len(reasons)} blocking finding(s), each "
        f"a cause below; delivery, which decides the same readiness again, refuses the task "
        f"until they are repaired (readiness in {saved})",
        reason="decision",
        explanation="validate only decides readiness and never repairs; each finding needs "
        "a Spec change (specify) or a code change (implement), which the main agent chooses",
        evidence=[
            evidence("blocking", item["ref"], item["detail"]) for item in state.blocking
        ],
        host_evidence=found,
        causes=state.links,
        options=[
            "repair each blocking finding in the task worktree and run validate again",
            "run specify for a Spec finding, implement for a code or check finding",
        ],
        recommendation="repair the first blocking finding: " + reasons[0],
    )


# Steps 2-8: what decides a readiness; Delivery runs them too before it commits.
READINESS_STEPS = (
    measure_inputs,
    validate_structure,
    sort_findings,
    require_accounted,
    derive_changed_modules,
    run_configured_checks,
    remeasure,
)

VALIDATE = Provider(
    name="validate",
    task_type=None,
    writes=False,
    steps=(check_branch, *READINESS_STEPS, issue_readiness),
    output_schema=READINESS_SCHEMA,
    requires_loaded_specs=False,
)


__all__ = [
    "READINESS_SCHEMA",
    "READINESS_STEPS",
    "VALIDATE",
    "not_deliverable",
    "readiness_of",
    "require_task_branch",
]
