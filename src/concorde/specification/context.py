"""Immutable cognitive inputs, separate from host-only execution grants."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..host.typed_data import canonical
from .repository import SpecError, SpecRepository, digest, read_file


PHASES = frozenset({"ask", "specify", "plan", "tasks", "implementation", "spec-review", "code-review",
                    "validate", "deliver", "context-solve"})
CODE_PHASES = frozenset({"implementation", "code-review"})
DISCOVERY_PHASES = frozenset({"route"})
DISCOVERY_KINDS = frozenset({"module"})
PROTOCOL_PATHS = ("generated/protocol/principles.md", "generated/protocol/kinds/module.md")


@dataclass(frozen=True)
class ContextSnapshot:
    serialized: str

    @property
    def value(self) -> dict:
        from ..host.typed_data import decode
        return decode(self.serialized)

    @property
    def id(self) -> str:
        return self.value["context_id"]


@dataclass(frozen=True)
class DiscoveryContext:
    """Complete Module contexts for global reasoning, with each source body included once."""

    serialized: str

    @property
    def value(self) -> dict:
        from ..host.typed_data import decode
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
        from ..host.typed_data import decode
        return decode(self.serialized)

    @property
    def id(self) -> str:
        return self.value["context_id"]


def _document_value(document, *, content: bool = True) -> dict:
    value = {
        "document_id": document.document_id,
        "path": document.path,
        "digest": document.digest,
        "targets": list(document.targets),
        "main_visible": document.main_visible,
    }
    if content:
        value["content"] = document.content
    return value


def _spec_sections(documents, *, references: dict[str, tuple[str, ...]] | None = None,
                   main_only: bool = False) -> tuple[list[str], list[dict], list[dict]]:
    selected = [document for document in documents
                if not main_only or document.main_visible]
    order = [document.path for document in selected]
    target_spec = []
    shared_specs = []
    for document in selected:
        targets = references.get(document.path, document.targets) if references else document.targets
        section = shared_specs if len(targets) > 1 else target_spec
        section.append(_document_value(document))
    return order, target_spec, shared_specs


def _protocol(repository: SpecRepository) -> list[dict]:
    protocol = []
    for path in PROTOCOL_PATHS:
        raw = repository.protocol_assets[path]
        protocol.append({"path": path, "digest": digest(raw), "content": raw.decode()})
    return protocol


def _implementation_files(repository: SpecRepository, target) -> list[dict]:
    """File names of the Module's implementation context; declarations only, never contents."""
    try:
        entities = repository.entity_files(target)
    except SpecError:
        entities = {}
    result = []
    for path in target.files:
        entity = entities.get(path)
        result.append({"path": path, "entity_id": entity.id if entity else None,
                       "pending": bool(entity and path in entity.pending)})
    return result


def _implementation_artifacts(repository: SpecRepository, target) -> list[dict]:
    return [{"id": path, "path": path, "digest": digest(read_file(repository.root, path))}
            for path in repository.implementation_files(target)]


def resolve_context(repository: SpecRepository, target_id: str, *, phase: str = "ask",
                    task: str = "Understand this Spec", focus_id: str | None = None,
                    constraints: tuple[str, ...] = (), instructions: str = "",
                    stage_inputs: tuple[dict, ...] = (), workspace: dict | None = None) -> ContextSnapshot:
    if phase not in PHASES:
        raise SpecError("unsupported context phase", "invalid_phase")
    if not isinstance(task, str) or not task.strip():
        raise SpecError("task intent is required", "invalid_input")
    target = repository.select(target_id, focus_id)
    from ..host.typed_data import validate_typed
    for item in stage_inputs:
        if item.get("type_id") not in {"concorde-plan-artifact","concorde-implementation-task",
                                       "concorde-reflection-selection","concorde-review-result"}:
            raise SpecError("unknown stage input type", "incompatible_handoff")
        validate_typed(item, item["type_id"])
    document_order, target_spec, shared_specs = _spec_sections(repository.documents(target))
    # No ancestry, participant inventory, code locator, or co-referencing entity's remaining body.
    from ..host.change_worktree import workspace_context
    manifest = {"schema_version": 2, "target_id": target.id, "kind": target.kind,
        "focus_id": focus_id, "phase": phase, "task": task, "constraints": list(constraints),
        "protocol_binding": repository.config["protocol"], "protocol": _protocol(repository),
        "document_order": document_order, "target_spec": target_spec,
        "shared_specs": shared_specs, "instructions": instructions,
        "stage_inputs": list(stage_inputs),
        "implementation_files": _implementation_files(repository, target),
        "implementation_artifacts": _implementation_artifacts(repository, target) if phase in CODE_PHASES else [],
        "workspace": workspace if workspace is not None else workspace_context(repository.root)}
    return ContextSnapshot(canonical({**manifest, "context_id": digest(manifest)}))


def resolve_discovery_context(repository: SpecRepository, target_ids: tuple[str, ...], *,
                              capability: str, phase: str, task: str,
                              action: str = "route",
                              target_hint: str | None = None,
                              focus_hint: str | None = None,
                              constraints: tuple[str, ...] = (), instructions: str = "",
                              workspace: dict | None = None) -> DiscoveryContext:
    """Resolve complete selected Module contexts without model interpretation or summaries.

    Target sections retain document membership. Sorted source pools carry each physical file's
    complete bytes once, including shared and non-main documents. Relationships never implicitly
    select another Module's collection.
    """

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
        document_order, target_spec, shared_specs = _spec_sections(
            repository.documents(target))
        for document in (*target_spec, *shared_specs):
            documents[document["path"]] = document
        targets.append({
            "target_id": target.id,
            "kind": target.kind,
            "document_order": document_order,
            "target_spec": [{key: value for key, value in document.items() if key != "content"}
                            for document in target_spec],
            "shared_specs": [{key: value for key, value in document.items() if key != "content"}
                             for document in shared_specs],
        })
    # File contents are deliberately absent from non-code cognition.
    from ..host.change_worktree import workspace_context
    manifest = {
        "schema_version": 2,
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
                                    workspace: dict | None = None) -> TopologyAuthorContext:
    """Build a private authoring context without exposing the target body to main."""

    if target.get("kind") != "module":
        raise SpecError("topology target has an unsupported kind", "invalid_spec")
    if not isinstance(task, str) or not task.strip():
        raise SpecError("topology Spec task is required", "invalid_input")
    references = {item["path"]: tuple(item["targets"])
                  for item in candidate_document_references}
    current_paths = []
    if target["id"] in repository.targets:
        current = repository.targets[target["id"]]
        current_paths.extend(current.documents)
    for path in target["documents"]:
        if path in repository.document_targets and path not in current_paths:
            current_paths.append(path)
    current_documents = [repository.document(path) for path in current_paths]
    current_document_order, target_spec, shared_specs = _spec_sections(
        current_documents, references=references)
    from ..host.change_worktree import workspace_context
    manifest = {
        "base_registry_digest": digest(repository.registry_bytes),
        "target": target,
        "task": task,
        "protocol_binding": repository.config["protocol"],
        "protocol": _protocol(repository),
        "candidate_document_references": list(candidate_document_references),
        "current_document_order": current_document_order,
        "target_spec": target_spec,
        "shared_specs": shared_specs,
        "instructions": instructions,
        "workspace": workspace if workspace is not None else workspace_context(repository.root),
    }
    return TopologyAuthorContext(canonical({**manifest, "context_id": digest(manifest)}))


def recheck_context(repository: SpecRepository, snapshot: ContextSnapshot, *, check_implementation: bool = True) -> None:
    value = snapshot.value
    declared = value.pop("context_id")
    if digest(value) != declared:
        raise SpecError("context snapshot identity has changed", "stale_context")
    _recheck_workspace(repository.root, value["workspace"])
    current = SpecRepository(repository.root, repository.package_root)
    target = current.select(value["target_id"], value["focus_id"])
    if current.config["protocol"] != value["protocol_binding"]:
        raise SpecError("context Protocol binding has changed", "stale_context")
    document_order, target_spec, shared_specs = _spec_sections(current.documents(target))
    if (document_order != value["document_order"] or target_spec != value["target_spec"]
            or shared_specs != value["shared_specs"]):
        raise SpecError("context document membership, classification, declarations or bytes changed", "stale_context")
    if _implementation_files(current, target) != value["implementation_files"]:
        raise SpecError("listed implementation files or their entities changed", "stale_context")
    if check_implementation and value["phase"] in CODE_PHASES:
        if _implementation_artifacts(current, target) != value["implementation_artifacts"]:
            raise SpecError("implementation input membership or bytes changed", "stale_context")


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


def recheck_topology_author_context(repository: SpecRepository, snapshot: TopologyAuthorContext) -> None:
    value = snapshot.value
    _recheck_workspace(repository.root, value["workspace"])
    current = SpecRepository(repository.root, repository.package_root)
    resolved = resolve_topology_author_context(
        current,
        value["target"],
        task=value["task"],
        instructions=value["instructions"],
        candidate_document_references=tuple(value["candidate_document_references"]),
        workspace=value["workspace"],
    )
    if resolved.serialized != snapshot.serialized:
        raise SpecError("topology author context changed", "stale_context")


def _recheck_workspace(root: Path, observed: dict) -> None:
    from ..host.change_worktree import workspace_context
    current = workspace_context(root)
    # Other worktrees may advance while this stage runs. Their inventory is an
    # explicitly timestamp-free observation, never an authority grant. This
    # invocation's own identity and lifecycle boundary must remain unchanged.
    for key in observed.keys() - {"active_worktrees"}:
        if current[key] != observed[key]:
            raise SpecError("current worktree identity or lifecycle changed", "stale_context")


def assess_result(snapshot: ContextSnapshot, assessment: dict) -> dict:
    """Validate a task-specific judgment; no code or external document lookup occurs here."""
    from .schema import validate
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
