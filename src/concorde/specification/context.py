"""Immutable cognitive inputs, separate from host-only execution grants."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..capabilities.operation_data import canonical
from .repository import SpecError, SpecRepository, digest, read_file


PHASES = frozenset({"ask", "specify", "plan", "tasks", "implementation", "validate", "deliver", "context-solve"})
DISCOVERY_PHASES = frozenset({"route", "synthesize"})
DISCOVERY_KINDS = frozenset({"domain", "service"})


@dataclass(frozen=True)
class ContextSnapshot:
    serialized: str

    @property
    def value(self) -> dict:
        from ..capabilities.operation_data import decode
        return decode(self.serialized)

    @property
    def id(self) -> str:
        return self.value["context_id"]


@dataclass(frozen=True)
class DiscoveryContext:
    """Append-only Domain/Service cognition for the main routing agent."""

    serialized: str

    @property
    def value(self) -> dict:
        from ..capabilities.operation_data import decode
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
        from ..capabilities.operation_data import decode
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


def resolve_context(repository: SpecRepository, target_id: str, *, phase: str = "ask",
                    task: str = "Understand this Spec", focus_id: str | None = None,
                    constraints: tuple[str, ...] = (), instructions: str = "",
                    stage_inputs: tuple[dict, ...] = (), workspace: dict | None = None) -> ContextSnapshot:
    if phase not in PHASES:
        raise SpecError("unsupported context phase", "invalid_phase")
    if not isinstance(task, str) or not task.strip():
        raise SpecError("task intent is required", "invalid_input")
    target = repository.select(target_id, focus_id)
    from ..capabilities.operation_data import validate_typed
    for item in stage_inputs:
        if item.get("type_id") not in {"concorde-plan-artifact","concorde-implementation-task","concorde-reflection-selection"}:
            raise SpecError("unknown stage input type", "incompatible_handoff")
        validate_typed(item, item["type_id"])
    document_order, target_spec, shared_specs = _spec_sections(repository.documents(target))
    protocol = []
    for path in ("protocol/principles.md", f"protocol/kinds/{target.kind}.md"):
        raw = repository.protocol_assets[path]
        protocol.append({"path": path, "digest": digest(raw), "content": raw.decode()})
    # No ancestry, participant inventory, code locator, or co-referencing entity's remaining body.
    from ..capabilities.change_worktree import workspace_context
    manifest = {"schema_version": 1, "target_id": target.id, "kind": target.kind,
        "focus_id": focus_id, "phase": phase, "task": task, "constraints": list(constraints),
        "protocol_binding": repository.config["protocol"], "protocol": protocol,
        "document_order": document_order, "target_spec": target_spec,
        "shared_specs": shared_specs, "instructions": instructions,
        "stage_inputs": list(stage_inputs),
        "implementation_artifacts": [{"id": path, "path": path,
            "digest": digest(read_file(repository.root, path))} for path in repository.implementation_files(target)]
            if phase == "implementation" else [],
        "workspace": workspace if workspace is not None else workspace_context(repository.root)}
    return ContextSnapshot(canonical({**manifest, "context_id": digest(manifest)}))


def public_context_manifest(snapshot: ContextSnapshot) -> dict:
    """Return reproducibility metadata without exposing cognitive document bodies."""

    value = snapshot.value
    return {
        "schema_version": 1,
        "context_id": value["context_id"],
        "target_id": value["target_id"],
        "kind": value["kind"],
        "focus_id": value["focus_id"],
        "phase": value["phase"],
        "workspace": value["workspace"],
        "protocol_binding": value["protocol_binding"],
        "protocol": [{"path": item["path"], "digest": item["digest"]}
                     for item in value["protocol"]],
        "document_order": value["document_order"],
        "target_spec": [{key: item[key] for key in
                         ("document_id", "path", "digest", "targets", "main_visible")}
                        for item in value["target_spec"]],
        "shared_specs": [{key: item[key] for key in
                          ("document_id", "path", "digest", "targets", "main_visible")}
                         for item in value["shared_specs"]],
    }


def resolve_discovery_context(repository: SpecRepository, target_ids: tuple[str, ...], *,
                              operation: str, phase: str, task: str,
                              action: str = "route",
                              target_hint: str | None = None,
                              focus_hint: str | None = None,
                              constraints: tuple[str, ...] = (), instructions: str = "",
                              worker_results: tuple[dict, ...] = (),
                              workspace: dict | None = None) -> DiscoveryContext:
    """Resolve the main agent's explicit, append-only Domain/Service discovery context."""

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
    from ..capabilities.operation_data import validate_typed
    admitted_results = []
    for item in worker_results:
        admitted_results.append(validate_typed(item, "concorde-main-worker-result"))
    targets = []
    for target_id in target_ids:
        target = repository.select(target_id)
        if target.kind not in DISCOVERY_KINDS:
            raise SpecError(
                f"main discovery cannot read {target.kind} Spec {target.id}",
                "permission_denied",
                target.id,
            )
        document_order, target_spec, shared_specs = _spec_sections(
            repository.documents(target), main_only=True)
        targets.append({
            "target_id": target.id,
            "kind": target.kind,
            "document_order": document_order,
            "target_spec": target_spec,
            "shared_specs": shared_specs,
        })
    # Main understands every global kind contract while remaining unable to read Module instances.
    protocol_paths = ["protocol/principles.md", *(f"protocol/kinds/{kind}.md"
                      for kind in ("domain", "service", "module"))]
    protocol = []
    for path in protocol_paths:
        raw = repository.protocol_assets[path]
        protocol.append({"path": path, "digest": digest(raw), "content": raw.decode()})
    from ..capabilities.change_worktree import workspace_context
    manifest = {
        "schema_version": 1,
        "operation": operation,
        "phase": phase,
        "action": action,
        "task": task,
        "constraints": list(constraints),
        "target_hint": target_hint,
        "focus_hint": focus_hint,
        "protocol_binding": repository.config["protocol"],
        "protocol": protocol,
        # Exact topology metadata is admitted only for explicit architecture design. Ordinary
        # routing learns business ownership from Domain/Service Specs and sees no code locators.
        "topology": repository.registry if action == "design-topology" else None,
        "targets": targets,
        "instructions": instructions,
        "worker_results": admitted_results,
        "workspace": workspace if workspace is not None else workspace_context(repository.root),
    }
    return DiscoveryContext(canonical({**manifest, "context_id": digest(manifest)}))


def resolve_topology_author_context(repository: SpecRepository, target: dict, *, task: str,
                                    instructions: str,
                                    candidate_document_references: tuple[dict, ...] = (),
                                    workspace: dict | None = None) -> TopologyAuthorContext:
    """Build a private authoring context without exposing the target body to main."""

    if target.get("kind") not in {"domain", "service", "module"}:
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
    protocol = []
    for path in ("protocol/principles.md", f"protocol/kinds/{target['kind']}.md"):
        raw = repository.protocol_assets[path]
        protocol.append({"path": path, "digest": digest(raw), "content": raw.decode()})
    from ..capabilities.change_worktree import workspace_context
    manifest = {
        "base_registry_digest": digest(repository.registry_bytes),
        "target": target,
        "task": task,
        "protocol_binding": repository.config["protocol"],
        "protocol": protocol,
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
        raise SpecError("context document membership, classification, or bytes changed", "stale_context")
    if check_implementation and value["phase"] == "implementation":
        current_artifacts = [{"id": path, "path": path, "digest": digest(read_file(current.root, path))}
                             for path in current.implementation_files(target)]
        if current_artifacts != value["implementation_artifacts"]:
            raise SpecError("implementation input membership or bytes changed", "stale_context")


def recheck_discovery_context(repository: SpecRepository, snapshot: DiscoveryContext) -> None:
    """Re-resolve every admitted Domain/Service and reject any changed discovery input."""

    value = snapshot.value
    _recheck_workspace(repository.root, value["workspace"])
    current = SpecRepository(repository.root, repository.package_root)
    resolved = resolve_discovery_context(
        current,
        tuple(item["target_id"] for item in value["targets"]),
        operation=value["operation"],
        phase=value["phase"],
        task=value["task"],
        action=value["action"],
        target_hint=value["target_hint"],
        focus_hint=value["focus_hint"],
        constraints=tuple(value["constraints"]),
        instructions=value["instructions"],
        worker_results=tuple(value["worker_results"]),
        workspace=value["workspace"],
    )
    if resolved.serialized != snapshot.serialized:
        raise SpecError("Domain/Service discovery context changed", "stale_context")


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
    from ..capabilities.change_worktree import workspace_context
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
