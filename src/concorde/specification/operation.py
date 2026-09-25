"""The ``specify`` Operation: a worker changes the bound Modules' own Spec documents.

Steps (the step table of the Specification Module Spec):

1. ``baseline``: validate the task worktree's Specs and remember the errors, the bound Modules'
   owned documents and their pending realization entries.
2. ``change``: the standard worker sequence for task type ``specify`` (grant, settings, brief,
   launch, audit, proposed deletions, run record) with one round and no checks. An audit
   violation or a run without a worker ends the run here; a worker that ended ``blocked`` or
   ``failed`` for any other reason is remembered and the following steps still run.
3. ``reconcile``: regenerate the registry's mirrored fields in the task worktree.
4. ``revalidate``: validate again and split the errors into new and pre-existing ones.
5. ``observe``: compute the Spec change from the host's own observations and decide the status:
   the worker's non-``ok`` status wins, then a new error ends the run ``blocked``.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path

from ..operations.provider import (
    Continue,
    Provider,
    RunContext,
    Stop,
    spec_cause,
    evidence,
    load_prompt,
    protocol_guide,
    spec_finding,
)

MODULE_ID = {"type": "string", "pattern": "^module\\."}
FINDING = {
    "type": "object",
    "additionalProperties": False,
    "required": ["rule_id", "path", "message"],
    "properties": {
        "rule_id": {"type": "string", "minLength": 1},
        "path": {"anyOf": [{"type": "string", "minLength": 1}, {"type": "null"}]},
        "message": {"type": "string", "minLength": 1},
    },
}
PROMISE_CHANGES = {
    "type": "array",
    "items": {
        "type": "object",
        "additionalProperties": False,
        "required": ["module", "kind", "id", "change", "description"],
        "properties": {
            "module": MODULE_ID,
            "kind": {
                "enum": [
                    "requirement",
                    "scenario",
                    "contract",
                    "concept",
                    "realization",
                    "relation",
                    "explanation",
                ]
            },
            "id": {"anyOf": [{"type": "string", "minLength": 1}, {"type": "null"}]},
            "change": {"enum": ["added", "changed", "removed"]},
            "description": {"type": "string", "minLength": 1},
        },
    },
}
PROPOSED_DOCUMENTS = {
    "type": "array",
    "items": {
        "type": "object",
        "additionalProperties": False,
        "required": ["module", "path", "role", "reason"],
        "properties": {
            "module": MODULE_ID,
            "path": {"type": "string", "minLength": 1},
            "role": {"enum": ["module", "implementation"]},
            "reason": {"type": "string", "minLength": 1},
        },
    },
}

# The worker's part of the Spec change: what it claims, never what the host observes.
WORKER_OUTPUT_SCHEMA: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": ["summary", "promise_changes", "proposed_documents"],
    "properties": {
        "summary": {"type": "string", "minLength": 1},
        "promise_changes": PROMISE_CHANGES,
        "proposed_documents": PROPOSED_DOCUMENTS,
    },
}

# contract.specification.spec-change, version 1 (specs/concorde/operations/specification/contracts.md)
SPEC_CHANGE_SCHEMA: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "intent",
        "summary",
        "changed_documents",
        "deleted_documents",
        "pending_declared",
        "promise_changes",
        "proposed_documents",
        "affected_modules",
        "validation",
    ],
    "properties": {
        "intent": {"type": "string", "minLength": 1},
        "summary": {"type": "string", "minLength": 1},
        "changed_documents": {
            "type": "array",
            "items": {"type": "string", "minLength": 1},
        },
        "deleted_documents": {
            "type": "array",
            "items": {"type": "string", "minLength": 1},
        },
        "pending_declared": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["module", "realization", "path"],
                "properties": {
                    "module": MODULE_ID,
                    "realization": {"type": "string", "pattern": "^realization\\."},
                    "path": {"type": "string", "minLength": 1},
                },
            },
        },
        "promise_changes": PROMISE_CHANGES,
        "proposed_documents": PROPOSED_DOCUMENTS,
        "affected_modules": {"type": "array", "items": MODULE_ID},
        "validation": {
            "type": "object",
            "additionalProperties": False,
            "required": ["new_errors", "pre_existing_errors", "warnings"],
            "properties": {
                "new_errors": {"type": "array", "items": {"$ref": "#/$defs/finding"}},
                "pre_existing_errors": {
                    "type": "array",
                    "items": {"$ref": "#/$defs/finding"},
                },
                "warnings": {"type": "array", "items": {"$ref": "#/$defs/finding"}},
            },
        },
    },
    "$defs": {"finding": FINDING},
}


@dataclass
class State:
    """What the steps of one specify run hand each other."""

    baseline_errors: set = field(default_factory=set)
    repository: object | None = None
    documents: tuple[str, ...] = ()
    pending: set = field(default_factory=set)
    stop: Stop | None = None
    record: dict | None = None
    validation: dict | None = None


def state(ctx: RunContext) -> State:
    return vars(ctx).setdefault("specification", State())


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--intent", required=True)


def key(finding) -> tuple:
    # Line numbers shift with any edit; a finding is the same when rule, file and message are.
    return (finding.rule_id, finding.source, finding.message)


def finding_value(finding) -> dict:
    return {
        "rule_id": finding.rule_id,
        "path": finding.source or None,
        "message": finding.message,
    }


def pending_entries(worktree: Path, documents) -> set[tuple[str, str, str]]:
    """(Module, realization, path) of every pending entry declared in the given metadata files."""
    found = set()
    for path in documents:
        if not path.endswith(".json"):
            continue
        try:
            metadata = json.loads((worktree / path).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not isinstance(metadata, dict):
            continue
        owner = (metadata.get("document") or {}).get("owner")
        for record in metadata.get("defines") or []:
            if not isinstance(record, dict) or record.get("type") != "realization":
                continue
            for entry in record.get("pending") or []:
                if isinstance(owner, str) and isinstance(entry, str):
                    found.add((owner, record.get("id", ""), entry))
    return found


def baseline(ctx: RunContext):
    """Step 1: validate the task worktree's Specs as a baseline."""
    from ..spec.repository import SpecRepository
    from ..spec.repository_base import SpecError
    from ..spec.validation import validate_repository

    current = state(ctx)
    result = validate_repository(ctx.worktree)
    unloadable = [f for f in result.findings if f.rule_id == "CONCORDE-SOURCE-008"]
    try:
        if unloadable:
            raise SpecError(unloadable[0].message, "invalid_spec")
        repository = SpecRepository(ctx.worktree)
        documents = sorted(
            {
                path
                for module in ctx.modules
                if module in repository.modules
                for path in repository.spec_scope(module)
            }
        )
    except (SpecError, OSError, ValueError) as error:
        code = getattr(error, "code", None) or "specs_unloadable"
        return ctx.fail(
            "failed",
            "specs_unloadable",
            "The task worktree's Specs could not be loaded for the baseline.",
            f"the Specs of {ctx.worktree} could not be loaded before the change: {code}: "
            f"{error}",
            reason="scope",
            explanation="a specify worker edits Spec documents under a grant computed from "
            "loadable Specs; repairing the configuration, registry or Protocol binding is "
            "outside what specify may change",
            evidence=[evidence("spec-load", ctx.worktree.as_posix(), str(error))],
            causes=[spec_cause(error)],
            options=["repair the configuration, registry or Protocol binding by hand"],
        )
    errors = {key(f) for f in result.findings if f.severity == "error"}
    current.baseline_errors = errors
    current.repository = repository
    current.documents = tuple(documents)
    current.pending = pending_entries(ctx.worktree, documents)
    return Continue(
        evidence=[
            evidence(
                "baseline",
                result.status,
                f"{len(errors)} error(s) before the change",
            )
        ]
    )


def instructions(ctx: RunContext) -> str:
    parts = [
        load_prompt("specify").strip(),
        "\n\n## This run\n\n",
        f"Bound Modules: {', '.join(ctx.modules)}\n\n",
        f"Intent: {ctx.arguments.intent}\n\n",
        f"The task's own goal: {ctx.task.get('goal', '(none)')}\n",
    ]
    if ctx.inputs:
        parts.append(
            "\nAdmitted inputs (outputs of earlier ok runs of this task):\n\n```json\n"
            + json.dumps(ctx.inputs, indent=2)
            + "\n```\n"
        )
    parts.append(protocol_guide(ctx.worktree))
    return "".join(parts)


def change(ctx: RunContext):
    """Steps 2 to 5: run the specify worker once; stop only when nothing may be observed."""
    from ..harness.runs import read_record

    current = state(ctx)
    outcome = ctx.run_worker(
        instructions(ctx),
        task_type="specify",
        output_schema=WORKER_OUTPUT_SCHEMA,
        checks=False,
        rounds=0,
    )
    if not ctx.worker_runs:
        return outcome  # the grant could not be computed; no worker ran
    record = read_record(ctx.primary, ctx.worker_runs[-1])
    current.record = record
    if isinstance(outcome, Continue):
        return Continue(evidence=outcome.evidence)
    violated = any(
        error["code"] == "audit_violation" for error in record.get("errors") or []
    ) or any(
        (item.get("audit") or {}).get("verdict") == "violation"
        for item in record.get("rounds") or []
    )
    if violated:
        return outcome  # a write outside the grant: no validation, nothing is observed
    current.stop = outcome
    return Continue(evidence=outcome.evidence)


def reconcile(ctx: RunContext):
    """Step 6: regenerate the registry's mirrored fields in the task worktree."""
    from ..spec.registry import registry_command

    result = registry_command(ctx.worktree, write=True)
    detail = (
        ", ".join(result.result.get("regenerated", []))
        if result.status == "success"
        else "; ".join(f.message for f in result.findings)
    )
    return Continue(evidence=[evidence("registry", result.status, detail)])


def revalidate(ctx: RunContext):
    """Step 7: validate again and compare with the baseline."""
    from ..spec.validation import validate_repository

    current = state(ctx)
    result = validate_repository(ctx.worktree)
    errors = [f for f in result.findings if f.severity == "error"]
    new = [f for f in errors if key(f) not in current.baseline_errors]
    old = [f for f in errors if key(f) in current.baseline_errors]
    warnings = [f for f in result.findings if f.severity == "warning"]
    current.validation = {
        "new_errors": [finding_value(f) for f in new],
        "pre_existing_errors": [finding_value(f) for f in old],
        "warnings": [finding_value(f) for f in warnings],
    }
    found = [
        evidence(
            "validation",
            result.status,
            f"{len(new)} new error(s), {len(old)} pre-existing, {len(warnings)} warning(s)",
        )
    ]
    found += [evidence("new-error", f.rule_id, f"{f.source}: {f.message}") for f in new]
    return Continue(evidence=found)


def affected_modules(
    ctx: RunContext, touched: set[str]
) -> tuple[list[str], list[dict]]:
    """Modules whose Spec context, before or after the change, contains a touched document."""
    from ..spec.repository import SpecRepository
    from ..spec.repository_base import SpecError

    affected: set[str] = set()
    notes = []
    repositories = [("before", state(ctx).repository)]
    try:
        repositories.append(("after", SpecRepository(ctx.worktree)))
    except (SpecError, OSError, ValueError) as error:
        notes.append(evidence("spec-load", "after", str(error)))
    for label, repository in repositories:
        if repository is None:
            continue
        for module in repository.modules:
            try:
                paths = set(repository.spec_context(module).paths)
            except (SpecError, OSError, ValueError) as error:
                notes.append(evidence("spec-context", f"{label} {module}", str(error)))
                continue
            if paths & touched:
                affected.add(module)
    return sorted(affected), notes


def observe(ctx: RunContext):
    """Steps 8 and 9: the Spec change from the host's own observations, and the status."""
    current = state(ctx)
    record = current.record or {}
    changed = sorted(
        {
            path
            for item in record.get("rounds") or []
            for path in (item.get("audit") or {}).get("changed", [])
        }
    )
    deleted = sorted(record.get("deleted") or [])
    after = pending_entries(ctx.worktree, current.documents)
    declared = [
        {"module": module, "realization": realization, "path": path}
        for module, realization, path in sorted(after - current.pending)
    ]
    affected, notes = affected_modules(ctx, set(changed) | set(deleted))
    claims = ((record.get("worker_result") or {}).get("output")) or {}
    output = {
        "intent": ctx.arguments.intent,
        "summary": claims.get("summary")
        or (record.get("worker_result") or {}).get("summary")
        or "The worker gave no account of its change.",
        "changed_documents": changed,
        "deleted_documents": deleted,
        "pending_declared": declared,
        "promise_changes": claims.get("promise_changes", []),
        "proposed_documents": claims.get("proposed_documents", []),
        "affected_modules": affected,
        "validation": current.validation,
    }
    found = notes + [
        evidence(
            "spec-change",
            "",
            f"{len(changed)} changed, {len(deleted)} deleted, "
            f"{len(declared)} pending declared, affected: {', '.join(affected) or 'none'}",
        )
    ]
    found += [
        evidence("deletion-refused", path, "not an owned document of a bound Module")
        for path in record.get("deletions_refused") or []
    ]
    if current.stop is not None:
        ctx.output = output
        return Stop(
            current.stop.status,
            current.stop.summary,
            found,
            current.stop.error,
        )
    new = current.validation["new_errors"]
    if new:
        ctx.output = output
        listing = "; ".join(
            f"{item['rule_id']} {item['path'] or ''}: {item['message']}" for item in new
        )
        return ctx.fail(
            "blocked",
            "new_structural_errors",
            f"The change introduced {len(new)} structural error(s); the edits stay in the task "
            "worktree.",
            f"after the worker's change the task's Specs have {len(new)} new structural "
            f"error(s), so they do not validate until these are repaired: {listing}",
            reason="decision",
            explanation="specify runs its worker once and never repairs a Spec automatically; "
            "whether to repair, rerun or discard the edits is the main agent's decision",
            evidence=found,
            causes=[
                spec_finding(
                    item["rule_id"],
                    item["path"],
                    None,
                    item["message"],
                    "validation diagnoses the Specs; it does not change them",
                )
                for item in new
            ],
            options=[
                "repair the documents by hand",
                "run specify again with a corrected intent",
                "discard the edits",
            ],
        )
    return Continue(output=output, evidence=found)


SPECIFY = Provider(
    name="specify",
    task_type="specify",
    writes=True,
    steps=(baseline, change, reconcile, revalidate, observe),
    output_schema=SPEC_CHANGE_SCHEMA,
    add_arguments=add_arguments,
)

__all__ = ["SPECIFY", "SPEC_CHANGE_SCHEMA", "WORKER_OUTPUT_SCHEMA"]
