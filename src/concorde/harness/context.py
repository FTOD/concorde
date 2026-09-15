"""Immutable cognitive inputs, separate from host-only execution grants."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from .agent_model import Mode, validate_mode_artifacts

from ..spec.typed_data import canonical
from ..spec.repository import (REFERENCE_SKIPPED_SUFFIXES, SpecError, SpecRepository, digest, entry_base,
                               expand_entry, is_directory_entry, most_specific, read_file)


PHASES = frozenset({"ask", "specify", "plan", "tasks", "implementation", "spec-review", "code-review",
                    "validate", "deliver", "context-solve"})
CODE_PHASES = frozenset({"implementation", "code-review"})
DISCOVERY_PHASES = frozenset({"route"})
DISCOVERY_KINDS = frozenset({"module"})
# The Protocol copy the installer places in the project and the configuration binds, granted in
# place like any other project file.
PROTOCOL_PATHS = (".concorde/protocol/principles.md", ".concorde/protocol/kinds/module.md")


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


@dataclass(frozen=True)
class DiscoveryContext:
    """Complete Module contexts for global reasoning, with each source indexed and granted once."""

    serialized: str

    @property
    def value(self) -> dict:
        from ..spec.typed_data import decode
        return decode(self.serialized)

    @property
    def id(self) -> str:
        return self.value["context_id"]


@dataclass(frozen=True)
class TopologyAuthorContext:
    """One provisional or existing target, private to its fresh Spec author."""

    serialized: str

    @property
    def value(self) -> dict:
        from ..spec.typed_data import decode
        return decode(self.serialized)

    @property
    def id(self) -> str:
        return self.value["context_id"]


def _protocol(repository: SpecRepository) -> list[dict]:
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
        result.append({"path": entry, "entity_id": entity.id if entity else None,
                       "pending": bool(entity and entry in entity.pending),
                       "directory": is_directory_entry(entry)})
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
        names[path] = {"path": path, "entity_id": entities[entry].id if entry else None, "pending": False}
    for entry, entity in entities.items():
        if entry in entity.pending and not is_directory_entry(entry) and entry not in names:
            names[entry] = {"path": entry, "entity_id": entity.id, "pending": True}
    return [names[path] for path in sorted(names)]


def _implementation_artifacts(repository: SpecRepository, target) -> list[dict]:
    return [{"id": path, "path": path, "digest": digest(read_file(repository.root, path))}
            for path in repository.implementation_files(target)]


def _external_references(repository: SpecRepository, target) -> list[dict]:
    """The Module's external references with one tree digest each; bytes are granted, never embedded."""
    missing = repository.missing_external_references(target)
    if missing:
        raise SpecError(f"external reference is not checked out: {', '.join(missing)}", "invalid_reference", target.id)
    return repository.external_reference_records(target)


def reference_grants(records: list[dict]) -> tuple[str, ...]:
    """The read-only authority roots for a snapshot's external references."""
    return tuple(dict.fromkeys(entry_base(item["path"]) for item in records))


def materialize_references(repository: SpecRepository, destination: Path, records: list[dict]) -> None:
    """Copy a snapshot's external references into a capsule at their project-relative paths.

    Only the readable files that the entry digest covers are copied, so a capsule receives the
    same bytes the snapshot identifies and none of the excluded media.
    """
    from ..spec.typed_data import checked_path
    for item in records:
        for path in expand_entry(repository.root, item["path"], skipped_suffixes=REFERENCE_SKIPPED_SUFFIXES):
            copy = checked_path(destination, path)
            copy.parent.mkdir(parents=True, exist_ok=True)
            copy.write_bytes(read_file(repository.root, path))


def _index_documents(value: dict) -> list[dict]:
    """The document records of a context index, whichever of the three context kinds it is."""
    return value["spec_resolution"]["sources"] if "spec_resolution" in value else value["documents"]


def context_grants(value: dict) -> tuple[str, ...]:
    """The read-only paths a context index grants: every listed document and the Protocol files.

    Accepts a context snapshot or a topology author context (both carry ``spec_resolution``) or a
    discovery context (which carries the deduplicated ``documents`` pool). Every grant is a
    project-relative path: Spec documents where they live and the installed Protocol copy under
    ``.concorde/protocol/``. The bodies are never embedded (Protocol, Context index and grant).
    """
    return tuple(sorted({*(item["path"] for item in value["protocol"]),
                         *(item["path"] for item in _index_documents(value))}))


def context_documents(repository: SpecRepository, value: dict, *,
                      candidate_repository: SpecRepository | None = None) -> dict[str, bytes]:
    """The exact bytes of every granted context file, keyed by path and verified by digest.

    A capsule receives these bytes at the same paths; a project workspace is granted the paths in
    place, and this verification proves they still hold the frozen bytes. A candidate repository
    supplies the bytes of documents it overrides, as topology authoring does.
    """
    expected = {item["path"]: item["digest"] for item in (*value["protocol"], *_index_documents(value))}
    result: dict[str, bytes] = {}
    for path, expected_digest in expected.items():
        if path in repository.protocol_assets:
            raw = repository.protocol_assets[path]
        else:
            source = (candidate_repository if candidate_repository is not None
                      and path in candidate_repository.document_overrides else repository)
            source.document(path)
            raw = source.document_overrides.get(path)
            if raw is None:
                raw = read_file(source.root, path)
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


def resolve_context(repository: SpecRepository, target_id: str, *, phase: str = "ask",
                    task: str = "Understand this Spec", focus_id: str | None = None,
                    constraints: tuple[str, ...] = (), instructions: str = "",
                    stage_inputs: tuple[dict, ...] = (), workspace: dict | None = None,
                    mode: Mode | None = None) -> ContextSnapshot:
    if phase not in PHASES:
        raise SpecError("unsupported context phase", "invalid_phase")
    if not isinstance(task, str) or not task.strip():
        raise SpecError("task intent is required", "invalid_input")
    if mode is not None:
        if mode.phase != phase or (phase in CODE_PHASES and "implementation" not in mode.constraints.effects.reads):
            raise SpecError("context phase exceeds the selected mode", "permission_denied")
        try:
            # Policy previews can omit not-yet-authored prerequisites; launches require them all.
            validate_mode_artifacts(mode, stage_inputs, require_all=False)
        except ValueError as error:
            raise SpecError(str(error), "incompatible_handoff") from error
    target = repository.select(target_id, focus_id)
    from ..spec.typed_data import validate_typed
    for item in stage_inputs:
        if phase != "tasks" and item.get("type_id") in {
                "concorde-task-identity-constraints", "concorde-task-scope-feedback"}:
            raise SpecError("task-control stage inputs require the tasks phase", "incompatible_handoff")
        if item.get("type_id") not in {"concorde-plan-artifact","concorde-task-identity-constraints","concorde-implementation-task","concorde-task-scope-feedback",
                                       "concorde-reflection-selection","concorde-review-result"}:
            raise SpecError("unknown stage input type", "incompatible_handoff")
        validate_typed(item, item["type_id"])
    resolution = repository.spec_context(focus_id or target.id).value
    # No ancestry, participant inventory, code locator, or co-referencing entity's remaining body.
    from .change_worktree import workspace_context
    manifest = {"schema_version": 4, "target_id": target.id, "kind": target.kind,
        "focus_id": focus_id, "phase": phase, "task": task, "constraints": list(constraints),
        "protocol_binding": repository.config["protocol"], "protocol": _protocol(repository),
        "spec_resolution": resolution, "instructions": instructions,
        "stage_inputs": list(stage_inputs),
        "implementation_entries": _implementation_entries(repository, target),
        "implementation_files": _implementation_files(repository, target),
        "implementation_artifacts": _implementation_artifacts(repository, target) if phase in CODE_PHASES else [],
        "external_references": _external_references(repository, target),
        "workspace": workspace if workspace is not None else workspace_context(repository.root)}
    return ContextSnapshot(canonical({**manifest, "context_id": digest(manifest)}))


def resolve_discovery_context(repository: SpecRepository, target_ids: tuple[str, ...], *,
                              capability: str, phase: str, task: str,
                              action: str = "route",
                              target_hint: str | None = None,
                              focus_hint: str | None = None,
                              constraints: tuple[str, ...] = (), instructions: str = "",
                              workspace: dict | None = None, mode: Mode | None = None) -> DiscoveryContext:
    """Resolve complete selected Module contexts without model interpretation or summaries.

    Target sections retain document membership. Sorted source pools carry each physical file's
    complete bytes once, including shared and non-main documents. Relationships never implicitly
    select another Module's collection.
    """

    if mode is not None and (mode.phase != phase or mode.action != action
            or "implementation" in mode.constraints.effects.reads):
        raise SpecError("discovery selection exceeds the selected mode", "permission_denied")
    if phase not in DISCOVERY_PHASES:
        raise SpecError("unsupported discovery phase", "invalid_phase")
    if action not in {"route", "ask", "design-topology"}:
        raise SpecError("unsupported main action", "invalid_input")
    if not isinstance(task, str) or not task.strip():
        raise SpecError("task intent is required", "invalid_input")
    if not target_ids or len(set(target_ids)) != len(target_ids):
        raise SpecError("discovery requires nonempty unique ordered targets", "invalid_context")
    if focus_hint is not None and target_hint is None:
        raise SpecError("a focus hint requires a target hint", "invalid_focus")
    if target_hint is not None:
        repository.select(target_hint, focus_hint)
    targets = []
    documents = {}
    for target_id in target_ids:
        target = repository.select(target_id)
        if target.kind not in DISCOVERY_KINDS:
            raise SpecError(
                f"main discovery cannot read {target.kind} Spec {target.id}",
                "permission_denied",
                target.id,
            )
        resolution = repository.spec_context(target.id).value
        for source in resolution["sources"]:
            documents[source["path"]] = {key: value for key, value in source.items() if key != "reasons"}
        resolution["sources"] = [{key: value for key, value in source.items() if key != "content"}
                                 for source in resolution["sources"]]
        targets.append({"target_id": target.id, "kind": target.kind, "spec_resolution": resolution})
    # File contents are deliberately absent from non-code cognition.
    from .change_worktree import workspace_context
    manifest = {
        "schema_version": 3,
        "capability": capability,
        "phase": phase,
        "action": action,
        "task": task,
        "constraints": list(constraints),
        "target_hint": target_hint,
        "focus_hint": focus_hint,
        "protocol_binding": repository.config["protocol"],
        "protocol": _protocol(repository),
        # Exact topology metadata is admitted only for explicit architecture design. Ordinary
        # routing learns business ownership from Module Specs and sees no code locators.
        "topology": repository.registry if action == "design-topology" else None,
        "targets": targets,
        "documents": [documents[path] for path in sorted(documents)],
        "instructions": instructions,
        "workspace": workspace if workspace is not None else workspace_context(repository.root),
    }
    return DiscoveryContext(canonical({**manifest, "context_id": digest(manifest)}))


def resolve_topology_author_context(repository: SpecRepository, target: dict, *, task: str,
                                    instructions: str,
                                    candidate_document_references: tuple[dict, ...] = (),
                                    workspace: dict | None = None,
                                    candidate_repository: SpecRepository | None = None) -> TopologyAuthorContext:
    """Build a private authoring context without exposing the target body to main."""

    if target.get("kind") != "module":
        raise SpecError("topology target has an unsupported kind", "invalid_spec")
    if not isinstance(task, str) or not task.strip():
        raise SpecError("topology Spec task is required", "invalid_input")
    # Freeze every currently available candidate-owned source and every explicit reference.
    # New owned paths have no preexisting bytes; the author must propose their complete bodies.
    from ..spec.repository import SpecTarget
    owned = tuple(path for path in target["documents"] if path in repository.document_targets)
    descriptor = SpecTarget(target["id"], "module", target["title"], owned, target["parent"],
        tuple(target["uses"]), tuple(target["files"]), tuple(target["checks"]),
        tuple((r["kind"], r["path"] if r["kind"] == "external" else r["id"]) for r in target["references"]))
    selection = candidate_repository or repository
    paths = selection._context_paths(descriptor)
    sources = []
    for path, reasons in paths.items():
        source_repository = selection if path in selection.document_overrides else repository
        if path not in source_repository.document_targets and path in target["documents"]:
            continue
        document = source_repository.document(path)
        sources.append({"document_id": document.document_id, "path": path, "owner": document.owner,
            "digest": document.digest, "main_visible": document.main_visible, "reasons": reasons})
    # The reading entry comes from the accepted descriptor: a new Module's module.md may not exist yet.
    reading_entry = next(path for path in target["documents"] if Path(path).name == "module.md")
    resolution = {"query_id": target["id"], "query_kind": "module", "module_id": target["id"],
        "reading_entry": reading_entry, "documents": list(target["documents"]),
        "references": target["references"], "sources": sources}
    from .change_worktree import workspace_context
    manifest = {
        "base_registry_digest": digest(repository.registry_bytes),
        "target": target,
        "task": task,
        "protocol_binding": repository.config["protocol"],
        "protocol": _protocol(repository),
        "candidate_references": target["references"],
        "spec_resolution": resolution,
        "instructions": instructions,
        "workspace": workspace if workspace is not None else workspace_context(repository.root),
    }
    return TopologyAuthorContext(canonical({**manifest, "context_id": digest(manifest)}))


def _stale_on_resolution_error(check):
    """A formerly admitted selection becoming invalid is stale evidence, never a new grant."""
    from functools import wraps

    @wraps(check)
    def checked(*args, **kwargs):
        try:
            return check(*args, **kwargs)
        except (ValueError, OSError) as error:
            if isinstance(error, SpecError) and error.code == "stale_context":
                raise
            raise SpecError(f"admitted context selection changed: {error}", "stale_context") from error
    return checked


@_stale_on_resolution_error
def recheck_context(repository: SpecRepository, snapshot: ContextSnapshot, *, check_implementation: bool = True) -> None:
    value = snapshot.value
    declared = value.pop("context_id")
    if digest(value) != declared:
        raise SpecError("context snapshot identity has changed", "stale_context")
    _recheck_workspace(repository.root, value["workspace"])
    current = SpecRepository(repository.root, repository.package_root,
        registry_bytes=repository.registry_bytes if repository.document_overrides else None,
        document_overrides=repository.document_overrides)
    target = current.select(value["target_id"], value["focus_id"])
    if current.config["protocol"] != value["protocol_binding"]:
        raise SpecError("context Protocol binding has changed", "stale_context")
    if current.spec_context(value["focus_id"] or target.id).value != value["spec_resolution"]:
        raise SpecError("context ownership, references, provenance or bytes changed", "stale_context")
    if _implementation_entries(current, target) != value["implementation_entries"]:
        raise SpecError("listed implementation entries or their entities changed", "stale_context")
    if check_implementation and _implementation_files(current, target) != value["implementation_files"]:
        raise SpecError("implementation file names changed", "stale_context")
    if check_implementation and value["phase"] in CODE_PHASES:
        if _implementation_artifacts(current, target) != value["implementation_artifacts"]:
            raise SpecError("implementation input membership or bytes changed", "stale_context")
    if _external_references(current, target) != value["external_references"]:
        raise SpecError("external references or their bytes changed", "stale_context")


@_stale_on_resolution_error
def recheck_discovery_context(repository: SpecRepository, snapshot: DiscoveryContext) -> None:
    """Re-resolve every admitted Module and reject any changed discovery input."""

    value = snapshot.value
    _recheck_workspace(repository.root, value["workspace"])
    current = SpecRepository(repository.root, repository.package_root)
    resolved = resolve_discovery_context(
        current,
        tuple(item["target_id"] for item in value["targets"]),
        capability=value["capability"],
        phase=value["phase"],
        task=value["task"],
        action=value["action"],
        target_hint=value["target_hint"],
        focus_hint=value["focus_hint"],
        constraints=tuple(value["constraints"]),
        instructions=value["instructions"],
        workspace=value["workspace"],
    )
    if resolved.serialized != snapshot.serialized:
        raise SpecError("Module discovery context changed", "stale_context")


@_stale_on_resolution_error
def recheck_topology_author_context(repository: SpecRepository, snapshot: TopologyAuthorContext, *,
                                   candidate_repository: SpecRepository | None = None) -> None:
    value = snapshot.value
    _recheck_workspace(repository.root, value["workspace"])
    current = SpecRepository(repository.root, repository.package_root)
    resolved = resolve_topology_author_context(
        current,
        value["target"],
        task=value["task"],
        instructions=value["instructions"],
        candidate_document_references=(),
        candidate_repository=candidate_repository,
        workspace=value["workspace"],
    )
    if resolved.serialized != snapshot.serialized:
        raise SpecError("topology author context changed", "stale_context")


def _recheck_workspace(root: Path, observed: dict) -> None:
    from .change_worktree import workspace_context
    current = workspace_context(root)
    # Other worktrees may advance while this stage runs. Their inventory is an
    # explicitly timestamp-free observation, never an authority grant. This
    # invocation's own identity and lifecycle boundary must remain unchanged.
    for key in observed.keys() - {"active_worktrees"}:
        if current[key] != observed[key]:
            raise SpecError("current worktree identity or lifecycle changed", "stale_context")


def assess_result(snapshot: ContextSnapshot, assessment: dict) -> dict:
    """Validate a task-specific judgment; no code or external document lookup occurs here."""
    from ..spec.schema import validate
    validate(assessment, {"type": "object", "additionalProperties": False,
        "required": ["context_id", "outcome", "answer", "gaps"], "properties": {
            "context_id": {"const": snapshot.id},
            "outcome": {"enum": ["sufficient", "spec_incomplete", "unsupported", "conflicting"]},
            "answer": {"type": "string", "minLength": 1},
            "gaps": {"type": "array", "items": {"type": "object", "additionalProperties": False,
                "required": ["question", "blocked_step", "needed_contract"], "properties": {
                    key: {"type": "string", "minLength": 1} for key in ("question", "blocked_step", "needed_contract")}}}}})
    if (assessment["outcome"] == "spec_incomplete") != bool(assessment["gaps"]):
        raise SpecError("only Spec incomplete has nonempty structured gaps", "invalid_assessment")
    return {"type_id": "concorde-context-assessment", "schema_version": 1,
            "data": {"target_id": snapshot.value["target_id"], **assessment}}
