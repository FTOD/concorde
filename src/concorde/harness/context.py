"""Immutable cognitive inputs, separate from host-only execution grants."""

from __future__ import annotations

from .timing import timed

from dataclasses import dataclass
from pathlib import Path

from ..spec.repository import (
    REFERENCE_SKIPPED_SUFFIXES,
    SpecError,
    SpecRepository,
    digest,
    entry_base,
    expand_entry,
    is_directory_entry,
    most_specific,
    read_file,
)
from ..spec.repository_base import RepositoryCore
from ..spec.typed_data import canonical
from .worker_profile import WorkerProfile, validate_worker_artifacts

PHASES = frozenset(
    {
        "plan",
        "tasks",
        "implementation",
        "spec-review",
        "code-review",
        "validate",
        "deliver",
        "context-solve",
        "issue-solve",
    }
)
CODE_PHASES = frozenset({"implementation", "code-review"})
# The Protocol copy the installer places in the project and the configuration binds, granted in
# place like any other project file.
PROTOCOL_PATHS = (
    ".concorde/protocol/principles.md",
    ".concorde/protocol/kinds/module.md",
)


@dataclass(frozen=True)
class ContextSnapshot:
    serialized: str

    @property
    def value(self) -> dict:
        from ..spec.typed_data import decode

        return decode(self.serialized)

    @property
    def id(self) -> str:
        return self.value["context_id"]


def _protocol(repository: RepositoryCore) -> list[dict]:
    protocol = []
    for path in PROTOCOL_PATHS:
        raw = repository.protocol_assets[path]
        protocol.append({"path": path, "digest": digest(raw)})
    return protocol


def _implementation_entries(repository: SpecRepository, target) -> list[dict]:
    """The Module's declared listing entries; declarations only, never contents."""
    try:
        entities = repository.entity_files(target)
    except SpecError:
        entities = {}
    result = []
    for entry in target.files:
        entity = entities.get(entry)
        result.append(
            {
                "path": entry,
                "entity_id": entity.id if entity else None,
                "pending": bool(entity and entry in entity.pending),
                "directory": is_directory_entry(entry),
            }
        )
    return result


def _implementation_files(repository: SpecRepository, target) -> list[dict]:
    """File names of the Module's implementation context: existing bound files plus pending files."""
    try:
        entities = repository.entity_files(target)
    except SpecError:
        entities = {}
    names: dict[str, dict] = {}
    for path in repository.implementation_files(target):
        entry = most_specific(entities, path)
        names[path] = {
            "path": path,
            "entity_id": entities[entry].id if entry else None,
            "pending": False,
        }
    for entry, entity in entities.items():
        if (
            entry in entity.pending
            and not is_directory_entry(entry)
            and entry not in names
        ):
            names[entry] = {"path": entry, "entity_id": entity.id, "pending": True}
    return [names[path] for path in sorted(names)]


def _implementation_artifacts(repository: SpecRepository, target) -> list[dict]:
    return [
        {"id": path, "path": path, "digest": digest(read_file(repository.root, path))}
        for path in repository.implementation_files(target)
    ]


def _external_references(repository: SpecRepository, target) -> list[dict]:
    """The Module's external references with one tree digest each; bytes are granted, never embedded."""
    missing = repository.missing_external_references(target)
    if missing:
        raise SpecError(
            f"external reference is not checked out: {', '.join(missing)}",
            "invalid_reference",
            target.id,
        )
    return repository.external_reference_records(target)


def reference_grants(records: list[dict]) -> tuple[str, ...]:
    """The read-only authority roots for a snapshot's external references."""
    return tuple(dict.fromkeys(entry_base(item["path"]) for item in records))


def materialize_references(
    repository: SpecRepository, destination: Path, records: list[dict]
) -> None:
    """Copy a snapshot's external references into a capsule at their project-relative paths.

    Only the readable files that the entry digest covers are copied, so a capsule receives the
    same bytes the snapshot identifies and none of the excluded media.
    """
    from ..spec.typed_data import checked_path

    for item in records:
        for path in expand_entry(
            repository.root, item["path"], skipped_suffixes=REFERENCE_SKIPPED_SUFFIXES
        ):
            copy = checked_path(destination, path)
            copy.parent.mkdir(parents=True, exist_ok=True)
            copy.write_bytes(read_file(repository.root, path))


def _index_documents(value: dict) -> list[dict]:
    """Complete paired source records for the selected Module."""
    return value["spec_resolution"]["sources"]


def context_grants(value: dict) -> tuple[str, ...]:
    """The read-only paths a context index grants: every listed document and the Protocol files.

    Every grant is project-relative: selected Spec members and the installed Protocol copy.
    Bodies are never embedded; source identity and inclusion remain byte-bound.
    """
    return tuple(
        sorted(
            {
                *(item["path"] for item in value["protocol"]),
                *(item["path"] for item in _index_documents(value)),
            }
        )
    )


def context_documents(
    repository: RepositoryCore,
    value: dict,
    *,
    candidate_repository: RepositoryCore | None = None,
) -> dict[str, bytes]:
    """The exact bytes of every granted context file, keyed by path and verified by digest.

    A capsule receives these bytes at the same paths; a project workspace is granted the paths in
    place, and this verification proves they still hold the frozen bytes. A candidate repository
    supplies the bytes of documents it overrides for deterministic validation.
    """
    (candidate_repository or repository).validate_source_records(
        _index_documents(value)
    )
    expected = {
        item["path"]: item["digest"]
        for item in (*value["protocol"], *_index_documents(value))
    }
    result: dict[str, bytes] = {}
    for path, expected_digest in expected.items():
        if path in repository.protocol_assets:
            raw = repository.protocol_assets[path]
        else:
            source = (
                candidate_repository
                if candidate_repository is not None
                and candidate_repository.source_is_overridden(path)
                else repository
            )
            raw = source.source_bytes(path)
        if digest(raw) != expected_digest:
            raise SpecError(f"granted context file changed: {path}", "stale_context")
        result[path] = raw
    return result


def materialize_documents(destination: Path, documents: dict[str, bytes]) -> None:
    """Copy granted context files into a capsule at their project-relative paths, byte for byte."""
    from ..spec.typed_data import checked_path

    for path, raw in documents.items():
        copy = checked_path(destination, path)
        copy.parent.mkdir(parents=True, exist_ok=True)
        copy.write_bytes(raw)


@timed("context.resolve")
def resolve_context(
    repository: SpecRepository,
    target_id: str,
    *,
    phase: str = "context-solve",
    task: str = "Understand this Spec",
    focus_id: str | None = None,
    constraints: tuple[str, ...] = (),
    instructions: str = "",
    stage_inputs: tuple[dict, ...] = (),
    workspace: dict | None = None,
    agent: WorkerProfile | None = None,
) -> ContextSnapshot:
    if phase not in PHASES:
        raise SpecError("unsupported context phase", "invalid_phase")
    if not isinstance(task, str) or not task.strip():
        raise SpecError("task intent is required", "invalid_input")
    if agent is not None:
        contract = agent.contract
        if contract.phase != phase or (
            phase in CODE_PHASES and "implementation" not in contract.effects.reads
        ):
            raise SpecError(
                "context phase exceeds the selected worker's contract",
                "permission_denied",
            )
        try:
            # Policy previews can omit not-yet-authored prerequisites; launches require them all.
            validate_worker_artifacts(agent, stage_inputs, require_all=False)
        except ValueError as error:
            raise SpecError(str(error), "incompatible_handoff") from error
    target = repository.select(target_id, focus_id)
    from ..spec.typed_data import validate_typed

    for item in stage_inputs:
        if phase != "tasks" and item.get("type_id") in {
            "concorde-task-identity-constraints",
            "concorde-task-scope-feedback",
        }:
            raise SpecError(
                "task-control stage inputs require the tasks phase",
                "incompatible_handoff",
            )
        if item.get("type_id") not in {
            "concorde-plan-artifact",
            "concorde-task-identity-constraints",
            "concorde-implementation-task",
            "concorde-task-scope-feedback",
            "concorde-issue-selection",
            "concorde-issue-context",
            "concorde-issue-intent",
            "concorde-review-result",
        }:
            raise SpecError("unknown stage input type", "incompatible_handoff")
        validate_typed(item, item["type_id"])
    resolution = repository.spec_context(focus_id or target.id).value
    # No ancestry, participant inventory, code locator, or co-referencing entity's remaining body.
    from .change_worktree import workspace_context

    manifest = {
        "schema_version": 6,
        "target_id": target.id,
        "kind": target.kind,
        "focus_id": focus_id,
        "phase": phase,
        "task": task,
        "constraints": list(constraints),
        "protocol_binding": repository.config["protocol"],
        "protocol": _protocol(repository),
        "spec_resolution": resolution,
        "instructions": instructions,
        "stage_inputs": list(stage_inputs),
        "implementation_entries": _implementation_entries(repository, target),
        "implementation_files": _implementation_files(repository, target),
        "implementation_artifacts": _implementation_artifacts(repository, target)
        if phase in CODE_PHASES
        else [],
        "external_references": _external_references(repository, target),
        "workspace": workspace
        if workspace is not None
        else workspace_context(repository.root, target_id=target.id, task=task),
    }
    return ContextSnapshot(canonical({**manifest, "context_id": digest(manifest)}))


def _stale_on_resolution_error(check):
    """A formerly admitted selection becoming invalid is stale evidence, never a new grant."""
    from functools import wraps

    @wraps(check)
    def checked(*args, **kwargs):
        try:
            return check(*args, **kwargs)
        except SpecError as error:
            if error.code == "stale_context":
                raise
            raise SpecError(
                f"admitted context selection changed: {error}", "stale_context"
            ) from error
        except (ValueError, OSError) as error:
            raise SpecError(
                f"admitted context selection changed: {error}", "stale_context"
            ) from error

    return checked


@_stale_on_resolution_error
@timed("context.recheck")
def recheck_context(
    repository: SpecRepository,
    snapshot: ContextSnapshot,
    *,
    check_implementation: bool = True,
) -> None:
    value = snapshot.value
    declared = value.pop("context_id")
    if digest(value) != declared:
        raise SpecError("context snapshot identity has changed", "stale_context")
    _recheck_workspace(
        repository.root, value["workspace"], value["target_id"], value["task"]
    )
    current = SpecRepository(
        repository.root,
        repository.package_root,
        registry_bytes=repository.registry_bytes
        if repository.document_overrides
        else None,
        document_overrides=repository.document_overrides,
    )
    target = current.select(value["target_id"], value["focus_id"])
    if current.config["protocol"] != value["protocol_binding"]:
        raise SpecError("context Protocol binding has changed", "stale_context")
    if (
        current.spec_context(value["focus_id"] or target.id).value
        != value["spec_resolution"]
    ):
        raise SpecError(
            "context ownership, references, provenance or bytes changed",
            "stale_context",
        )
    if _implementation_entries(current, target) != value["implementation_entries"]:
        raise SpecError(
            "listed implementation entries or their entities changed", "stale_context"
        )
    if (
        check_implementation
        and _implementation_files(current, target) != value["implementation_files"]
    ):
        raise SpecError("implementation file names changed", "stale_context")
    if (
        check_implementation
        and value["phase"] in CODE_PHASES
        and _implementation_artifacts(current, target)
        != value["implementation_artifacts"]
    ):
        raise SpecError(
            "implementation input membership or bytes changed", "stale_context"
        )
    if _external_references(current, target) != value["external_references"]:
        raise SpecError("external references or their bytes changed", "stale_context")


def _recheck_workspace(
    root: Path, observed: dict, target_id: str | None = None, task: str | None = None
) -> None:
    from .change_worktree import workspace_context

    current = workspace_context(root, target_id=target_id, task=task)
    # Other worktrees may advance while this stage runs. Their inventory is an
    # explicitly timestamp-free observation, never an authority grant. This
    # invocation's own identity and lifecycle boundary must remain unchanged.
    for key in observed.keys() - {"active_worktrees"}:
        if current[key] != observed[key]:
            raise SpecError(
                "current worktree identity or lifecycle changed", "stale_context"
            )


def assess_result(snapshot: ContextSnapshot, assessment: dict) -> dict:
    """Validate a task-specific judgment; no code or external document lookup occurs here."""
    from ..spec.issue_shapes import BLOCKER
    from ..spec.schema import validate

    validate(
        assessment,
        {
            "type": "object",
            "additionalProperties": False,
            "required": ["context_id", "outcome", "answer", "blockers"],
            "properties": {
                "context_id": {"const": snapshot.id},
                "outcome": {
                    "enum": [
                        "sufficient",
                        "spec_incomplete",
                        "unsupported",
                        "conflicting",
                    ]
                },
                "answer": {"type": "string", "minLength": 1},
                "blockers": {"type": "array", "items": BLOCKER},
            },
        },
    )
    if (assessment["outcome"] == "spec_incomplete" and not assessment["blockers"]) or (
        assessment["outcome"] == "sufficient" and assessment["blockers"]
    ):
        raise SpecError(
            "assessment outcome contradicts its Issue blockers", "invalid_assessment"
        )
    return {
        "type_id": "concorde-context-assessment",
        "schema_version": 1,
        "data": {"target_id": snapshot.value["target_id"], **assessment},
    }
