"""The ``specify`` Operation: a worker changes the bound Modules' own Spec documents.

Steps (the step table of the Specification Module Spec):

1. ``baseline``: validate the task worktree's Specs and remember the errors and the bound
   Modules' owned documents.
2. ``change``: the standard worker sequence for task type ``specify`` (grant, settings, brief,
   launch, audit, proposed deletions, run record) with repair rounds and no checks. When the
   worker ends ``blocked`` proposing new documents of the bound Modules, the host creates them,
   empty and registered, and launches the worker once more to fill them. An audit violation or a
   run without a worker ends the run here; a worker that ended ``blocked`` or ``failed`` for any
   other reason is remembered and the following steps still run.
3. ``reconcile``: regenerate the registry's mirrored fields in the task worktree.
4. ``revalidate``: validate again and split the errors into new and pre-existing ones.
5. ``observe``: compute the Spec change from the host's own observations and decide the status:
   the worker's non-``ok`` status wins, then a new error ends the run ``blocked``.
"""

from __future__ import annotations

import argparse
import json
import os
import posixpath
import re
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

from ...execution.context import (
    Continue,
    RunContext,
    Stop,
    evidence,
)
from ..prompts import (
    load_prompt,
    protocol_guide,
)
from ..specs import spec_cause, spec_finding
from ..workers import operation, run_worker

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

# contract.specification.spec-change, version 3 (specs/concorde/execution/operations/specification/contracts.md)
SPEC_CHANGE_SCHEMA: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "intent",
        "summary",
        "changed_documents",
        "created_documents",
        "deleted_documents",
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
        "created_documents": {
            "type": "array",
            "items": {"type": "string", "minLength": 1},
        },
        "deleted_documents": {
            "type": "array",
            "items": {"type": "string", "minLength": 1},
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
    stop: Stop | None = None
    record: dict | None = None
    # The run records of every worker launch, the relaunch after creating documents included.
    records: list = field(default_factory=list)
    # The reading files of the documents the host created for the worker.
    created: list = field(default_factory=list)
    # Every file the host wrote creating them: the reading files, their metadata and the metadata
    # of the entries whose ``owns`` registers them.
    written: list = field(default_factory=list)
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


def baseline(ctx: RunContext):
    """Step 1: validate the task worktree's Specs as a baseline."""
    from ...spec.repository import SpecRepository
    from ...spec.repository_base import SpecError
    from ...spec.validation import validate_repository

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
    errors = {key(f) for f in result.findings if f.strictness == "error"}
    current.baseline_errors = errors
    current.repository = repository
    current.documents = tuple(documents)
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
        f"The workspace's goal: {ctx.goal or '(none)'}\n",
    ]
    if ctx.inputs:
        parts.append(
            "\nAdmitted inputs (outputs of earlier ok runs of this task):\n\n```json\n"
            + json.dumps(ctx.inputs, indent=2)
            + "\n```\n"
        )
    parts.append(protocol_guide(ctx.worktree))
    return "".join(parts)


# Resume rounds in which the worker repairs what the host's validation reports.
REPAIR_ROUNDS = 2


def reconciled_registry(root: Path) -> bytes | None:
    """The registry as step 6 would regenerate it from the entries now in the worktree, or None
    when an entry cannot be read; validation then sees the registry on disk."""
    from ...spec.registry import mirrored_registry, serialize
    from ...spec.repository_base import SpecError

    try:
        value, _stale = mirrored_registry(root)
    except (SpecError, OSError, ValueError):
        return None
    return serialize(value).encode("utf-8")


def validation_repair(ctx: RunContext) -> str | None:
    """After a round: the errors the baseline did not have, as a resume prompt, or None.

    The registry sits outside the worker's grant and step 6 regenerates its mirrored fields from
    the entries, so the round is validated against that reconciled registry, held in memory: a
    stale mirror is never an error the worker is asked to repair.
    """
    from ...spec.validation import validate_repository
    from ..prompts import spec_repair_prompt

    errors = [
        finding
        for finding in validate_repository(
            ctx.worktree, registry_bytes=reconciled_registry(ctx.worktree)
        ).findings
        if finding.strictness == "error"
        and key(finding) not in state(ctx).baseline_errors
    ]
    return spec_repair_prompt(errors)


def title_of(path: str) -> str:
    """A document title from its file name: ``delivery-terms.md`` gives ``Delivery terms``."""
    words = Path(path).stem.replace("_", " ").replace("-", " ").split()
    return " ".join(words).capitalize() or "Document"


def document_refusal(ctx: RunContext, proposal: dict) -> str | None:
    """Why the host does not create a proposed document, or None when it may.

    The path is checked as a path and as the filesystem holds it: a symbolic link, dangling or
    not, at any component of the reading file's or its metadata's path is refused, so that no
    write the host makes follows a link out of the entry's folder.
    """
    from ...spec.typed_data import TypedDataError, checked_path, safe_path

    repository = state(ctx).repository
    module, path = proposal["module"], proposal["path"]
    if (
        module not in ctx.modules
        or repository is None
        or module not in repository.modules
    ):
        return f"{module} is not a Module this run is bound to"
    entry = repository.modules[module].primary_document
    folder = PurePosixPath(entry).parent
    try:
        safe_path(path)
    except TypedDataError:
        return "the path is not a canonical project-relative path"
    candidate = PurePosixPath(path)
    if candidate.suffix != ".md":
        return "the path is not a project-relative Markdown file"
    if folder not in candidate.parents:
        return f"the path lies outside {folder.as_posix()}/, the folder of {module}'s entry"
    for each in (path, path + ".json"):
        try:
            target = checked_path(ctx.worktree, each)
        except TypedDataError:
            return f"a component of {each} is a symbolic link"
        if os.path.lexists(target):
            return "a file already exists at the path or its metadata path"
    return None


def document_identity(module: str, path: str, taken: set[str]) -> str:
    """A document identity for a created document, unique against ``taken``.

    It is ``document.<module>.<name>``, the name made of the file's stem; when that is taken, by
    an existing document or another created one, the folders below the entry's folder are added,
    then a number, so that two files of the same name never share an identity.
    """
    local = module.split(".", 1)[1]

    def slug(text: str) -> str:
        words = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
        return words if words and words[0].isalpha() else f"d-{words or 'document'}"

    stem = slug(PurePosixPath(path).stem)
    folders = [slug(part) for part in PurePosixPath(path).parent.parts]
    candidates = [f"document.{local}.{stem}"]
    candidates += [
        f"document.{local}.{'-'.join(folders[index:] + [stem])}"
        for index in range(len(folders) - 1, -1, -1)
    ]
    for candidate in candidates:
        if candidate not in taken:
            return candidate
    number = 2
    while f"{candidates[0]}-{number}" in taken:
        number += 1
    return f"{candidates[0]}-{number}"


def document_identities(ctx: RunContext) -> set[str]:
    """Every document identity the Specs hold, before the change and, when they load, now."""
    from ...spec.repository import SpecRepository
    from ...spec.repository_base import SpecError

    repositories = [state(ctx).repository]
    try:
        repositories.append(SpecRepository(ctx.worktree))
    except (SpecError, OSError, ValueError):
        pass
    return {
        unit.document_id
        for repository in repositories
        if repository is not None
        for unit in repository.units.values()
    }


def refused(proposals: list[dict], reasons: dict[int, str]):
    """No document created: ``document-refused`` evidence for each refused proposal."""
    return (
        [],
        [],
        [
            evidence("document-refused", proposals[index]["path"], reason)
            for index, reason in sorted(reasons.items())
        ],
    )


def create_documents(ctx: RunContext, proposals: list[dict]):
    """Create every proposed document, empty and owned by its Module, or none of them.

    Returns the created reading files, every file written to create them and the evidence; a
    proposal the host refuses leaves every proposal uncreated, since the worker's change needs all
    of them. Every content is computed and every proposal checked before the first write: a path
    proposed more than once, a path the host may not create and an entry whose metadata cannot
    take the document are refused before anything is written. The files are then written in one
    Spec core file transaction, which restores every file it wrote when a write fails, and
    which refuses a symbolic link at any path component.
    """
    from ...spec.changes import apply_files, file_change
    from ...spec.registry import registry_command
    from ...spec.repository_base import SpecError
    from ...spec.typed_data import TypedDataError

    paths = [PurePosixPath(proposal["path"]).as_posix() for proposal in proposals]
    reasons = {
        index: reason
        for index, (proposal, path) in enumerate(zip(proposals, paths))
        if (
            reason := "the path is proposed more than once"
            if paths.count(path) > 1
            else document_refusal(ctx, proposal)
        )
        is not None
    }
    if reasons:
        return refused(proposals, reasons)
    repository = state(ctx).repository
    taken = document_identities(ctx)
    entries: dict[str, dict] = {}
    for index, proposal in enumerate(proposals):
        entry = repository.modules[proposal["module"]].primary_document
        if entry in entries:
            continue
        try:
            metadata = json.loads(
                (ctx.worktree / (entry + ".json")).read_text(encoding="utf-8")
            )
            owns = metadata["module"]["owns"]
            if not isinstance(owns, list):
                raise TypeError("its module block's owns is not a list")
        except (OSError, ValueError, KeyError, TypeError) as error:
            reason = (
                f"the metadata {entry}.json cannot register the document: "
                f"{type(error).__name__}: {error}"
            )
            return refused(
                proposals,
                {
                    other: reason
                    for other, each in enumerate(proposals)
                    if repository.modules[each["module"]].primary_document == entry
                },
            )
        entries[entry] = metadata
    contents: dict[str, str] = {}
    found = []
    for proposal, path in zip(proposals, paths):
        module = proposal["module"]
        entry = repository.modules[module].primary_document
        # The created document may lie below the entry's folder, so the link may climb.
        link = posixpath.relpath(entry, posixpath.dirname(path))
        title = repository.modules[module].title
        identity = document_identity(module, path, taken)
        taken.add(identity)
        contents[path] = (
            f"# {title_of(path)}\n\nPart of the Spec of [{title}]({link}).\n"
        )
        contents[path + ".json"] = (
            json.dumps(
                {
                    "schema_version": 3,
                    "document": {
                        "id": identity,
                        "owner": module,
                        "role": proposal["role"],
                    },
                    "defines": [],
                    "relations": [],
                    "extensions": {},
                },
                indent=2,
            )
            + "\n"
        )
        entries[entry]["module"]["owns"].append(path)
        found.append(
            evidence(
                "document-created",
                path,
                f"{proposal['role']} document {identity} of {module}: "
                f"{proposal['reason']}",
            )
        )
    for entry, metadata in entries.items():
        contents[entry + ".json"] = (
            json.dumps(metadata, indent=2, ensure_ascii=False) + "\n"
        )
    try:
        changes = [
            file_change(ctx.worktree, path, text) for path, text in contents.items()
        ]
        written = apply_files(ctx.worktree, changes, set(contents))
    except (SpecError, TypedDataError, OSError) as error:
        detail = error.describe() if isinstance(error, SpecError) else str(error)
        return (
            [],
            [],
            [evidence("document-creation-failed", ", ".join(paths), detail)],
        )
    registry = registry_command(ctx.worktree, write=True)
    found.append(evidence("registry", registry.status, registry_detail(registry)))
    return paths, written, found


def launch(ctx: RunContext, created: list[str]):
    """One specify worker launch; ``created`` names the documents the host made for it."""
    text = instructions(ctx)
    if created:
        text += (
            "\n\n## Documents the host created for you\n\n"
            "An earlier worker of this run needed these documents, so the host created them, "
            "empty and owned by their Modules; fill them to carry out the intent:\n\n"
            + "".join(f"- `{path}` (and `{path}.json`)\n" for path in created)
        )
    return run_worker(
        ctx,
        text,
        task_type="specify",
        output_schema=WORKER_OUTPUT_SCHEMA,
        checks=False,
        rounds=REPAIR_ROUNDS,
        validate=lambda _result: validation_repair(ctx),
    )


def violated(record: dict, outcome) -> bool:
    """Whether the worker run wrote outside its grant: a file outside ``rw`` or a glossary entry
    another Module owns, found by the audit, the round validation or the check after the run."""
    codes = {
        (record.get("error") or {}).get("code"),
        (getattr(outcome, "error", None) or {}).get("code"),
    }
    return "audit_violation" in codes or any(
        (item.get("audit") or {}).get("verdict") == "violation"
        for item in record.get("rounds") or []
    )


def change(ctx: RunContext):
    """Steps 2 to 5: run the specify worker, once more after creating the documents it needs;
    stop only when nothing may be observed."""

    current = state(ctx)
    outcome = launch(ctx, [])
    if not ctx.worker_runs:
        return outcome  # the grant could not be computed; no worker ran
    record = ctx.last_record
    current.records.append(record)
    found = list(outcome.evidence)
    proposals = ((record.get("worker_result") or {}).get("output") or {}).get(
        "proposed_documents"
    ) or []
    if (
        isinstance(outcome, Stop)
        and outcome.status == "blocked"
        and proposals
        and not violated(record, outcome)
    ):
        created, written, notes = create_documents(ctx, proposals)
        found += notes
        if created:
            current.created = created
            current.written = written
            outcome = launch(ctx, created)
            record = ctx.last_record
            current.records.append(record)
            found += outcome.evidence
    current.record = record
    if isinstance(outcome, Continue):
        return Continue(evidence=found)
    if violated(record, outcome):
        outcome.evidence[:] = found
        return outcome  # a write outside the grant: no validation, nothing is observed
    current.stop = Stop(outcome.status, outcome.summary, found, outcome.error)
    return Continue(evidence=found)


def registry_detail(result) -> str:
    """What the registry command did: the regenerated Modules, or its refusal in full."""
    if result.status in ("success", "unchanged"):
        return ", ".join(result.result.get("regenerated", []))
    if result.error is not None:
        return result.error.describe()
    return "; ".join(f.message for f in result.findings)


def reconcile(ctx: RunContext):
    """Step 6: regenerate the registry's mirrored fields in the task worktree."""
    from ...spec.registry import registry_command

    result = registry_command(ctx.worktree, write=True)
    return Continue(
        evidence=[evidence("registry", result.status, registry_detail(result))]
    )


def revalidate(ctx: RunContext):
    """Step 7: validate again and compare with the baseline."""
    from ...spec.validation import validate_repository

    current = state(ctx)
    result = validate_repository(ctx.worktree)
    errors = [f for f in result.findings if f.strictness == "error"]
    new = [f for f in errors if key(f) not in current.baseline_errors]
    old = [f for f in errors if key(f) in current.baseline_errors]
    warnings = [f for f in result.findings if f.strictness == "warning"]
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
    from ...spec.repository import SpecRepository
    from ...spec.repository_base import SpecError

    affected: set[str] = set()
    notes = []
    before = state(ctx).repository
    repositories = [("before", before)]
    try:
        repositories.append(("after", SpecRepository(ctx.worktree)))
    except (SpecError, OSError, ValueError) as error:
        detail = error.describe() if isinstance(error, SpecError) else str(error)
        notes.append(evidence("spec-load", "after", detail))
        # No Module's context after the change can be computed: name each one known.
        notes += [
            evidence(
                "spec-context",
                f"after {module}",
                f"not computed, since the Specs after the change do not load: {detail}",
            )
            for module in sorted(
                set(ctx.modules) | set(getattr(before, "modules", None) or ())
            )
        ]
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
    records = current.records or [record]
    changed = sorted(
        {
            path
            for each in records
            for item in each.get("rounds") or []
            for path in (item.get("audit") or {}).get("changed", [])
        }
        | set(current.written)
    )
    deleted = sorted({path for each in records for path in each.get("deleted") or []})
    affected, notes = affected_modules(ctx, set(changed) | set(deleted))
    claims = ((record.get("worker_result") or {}).get("output")) or {}
    output = {
        "intent": ctx.arguments.intent,
        "summary": claims.get("summary")
        or (record.get("worker_result") or {}).get("summary")
        or "The worker gave no account of its change.",
        "changed_documents": changed,
        "created_documents": list(current.created),
        "deleted_documents": deleted,
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
            f"affected: {', '.join(affected) or 'none'}",
        )
    ]
    found += [
        evidence("deletion-refused", path, "not an owned document of a bound Module")
        for each in records
        for path in each.get("deletions_refused") or []
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
            explanation="the worker was resumed with the host's validation as many times as "
            "specify allows and the errors remain; whether to repair, rerun or discard the "
            "edits is the main agent's decision",
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


SPECIFY = operation(
    name="specify",
    task_type="specify",
    writes=True,
    steps=(baseline, change, reconcile, revalidate, observe),
    output_schema=SPEC_CHANGE_SCHEMA,
    add_arguments=add_arguments,
)

__all__ = ["SPECIFY", "SPEC_CHANGE_SCHEMA", "WORKER_OUTPUT_SCHEMA"]
