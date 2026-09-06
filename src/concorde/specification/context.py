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


def resolve_context(repository: SpecRepository, target_id: str, *, phase: str = "ask",
                    task: str = "Understand this Spec", focus_id: str | None = None,
                    constraints: tuple[str, ...] = (), instructions: str = "",
                    stage_inputs: tuple[dict, ...] = ()) -> ContextSnapshot:
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
    documents = [{"path": doc.path, "digest": doc.digest, "content": doc.content}
                 for doc in repository.documents(target)]
    protocol = []
    for path in ("protocol/principles.md", f"protocol/kinds/{target.kind}.md"):
        raw = repository.protocol_assets[path]
        protocol.append({"path": path, "digest": digest(raw), "content": raw.decode()})
    # No scope ancestry, component ancestry, participating targets, code locators, or provider bodies.
    manifest = {"schema_version": 1, "target_id": target.id, "kind": target.kind,
        "focus_id": focus_id, "phase": phase, "task": task, "constraints": list(constraints),
        "protocol_binding": repository.config["protocol"], "protocol": protocol,
        "documents": documents, "instructions": instructions, "stage_inputs": list(stage_inputs),
        "implementation_artifacts": [{"id": path, "path": path,
            "digest": digest(read_file(repository.root, path))} for path in repository.implementation_files(target)]
            if phase == "implementation" else []}
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
        "protocol_binding": value["protocol_binding"],
        "protocol": [{"path": item["path"], "digest": item["digest"]}
                     for item in value["protocol"]],
        "documents": [{"path": item["path"], "digest": item["digest"]}
                      for item in value["documents"]],
    }


def resolve_discovery_context(repository: SpecRepository, target_ids: tuple[str, ...], *,
                              operation: str, phase: str, task: str,
                              target_hint: str | None = None,
                              focus_hint: str | None = None,
                              constraints: tuple[str, ...] = (), instructions: str = "",
                              worker_results: tuple[dict, ...] = ()) -> DiscoveryContext:
    """Resolve the main agent's explicit, append-only Domain/Service discovery context."""

    if phase not in DISCOVERY_PHASES:
        raise SpecError("unsupported discovery phase", "invalid_phase")
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
    admitted_kinds = set()
    module_documents = {path for candidate in repository.targets.values()
                        if candidate.kind == "module" for path in candidate.documents}
    for target_id in target_ids:
        target = repository.select(target_id)
        if target.kind not in DISCOVERY_KINDS:
            raise SpecError(
                f"main discovery cannot read {target.kind} Spec {target.id}",
                "permission_denied",
                target.id,
            )
        shared_with_module = sorted(set(target.documents) & module_documents)
        if shared_with_module:
            raise SpecError(
                f"main discovery target shares Module Spec members: {shared_with_module}",
                "permission_denied",
                target.id,
            )
        admitted_kinds.add(target.kind)
        targets.append({
            "target_id": target.id,
            "kind": target.kind,
            "documents": [{"path": doc.path, "digest": doc.digest, "content": doc.content}
                          for doc in repository.documents(target)],
        })
    protocol_paths = ["protocol/principles.md"] + [
        f"protocol/kinds/{kind}.md" for kind in ("domain", "service") if kind in admitted_kinds
    ]
    protocol = []
    for path in protocol_paths:
        raw = repository.protocol_assets[path]
        protocol.append({"path": path, "digest": digest(raw), "content": raw.decode()})
    manifest = {
        "schema_version": 1,
        "operation": operation,
        "phase": phase,
        "task": task,
        "constraints": list(constraints),
        "target_hint": target_hint,
        "focus_hint": focus_hint,
        "protocol_binding": repository.config["protocol"],
        "protocol": protocol,
        "targets": targets,
        "instructions": instructions,
        "worker_results": admitted_results,
    }
    return DiscoveryContext(canonical({**manifest, "context_id": digest(manifest)}))


def recheck_context(repository: SpecRepository, snapshot: ContextSnapshot, *, check_implementation: bool = True) -> None:
    value = snapshot.value
    declared = value.pop("context_id")
    if digest(value) != declared:
        raise SpecError("context snapshot identity has changed", "stale_context")
    current = SpecRepository(repository.root, repository.package_root)
    target = current.select(value["target_id"], value["focus_id"])
    if list(target.documents) != [item["path"] for item in value["documents"]]:
        raise SpecError("context document membership has changed", "stale_context")
    if current.config["protocol"] != value["protocol_binding"]:
        raise SpecError("context Protocol binding has changed", "stale_context")
    for item in value["documents"]:
        if digest(read_file(current.root, item["path"])) != item["digest"]:
            raise SpecError(f"context document has changed: {item['path']}", "stale_context")
    if check_implementation and value["phase"] == "implementation":
        current_artifacts = [{"id": path, "path": path, "digest": digest(read_file(current.root, path))}
                             for path in current.implementation_files(target)]
        if current_artifacts != value["implementation_artifacts"]:
            raise SpecError("implementation input membership or bytes changed", "stale_context")


def recheck_discovery_context(repository: SpecRepository, snapshot: DiscoveryContext) -> None:
    """Re-resolve every admitted Domain/Service and reject any changed discovery input."""

    value = snapshot.value
    current = SpecRepository(repository.root, repository.package_root)
    resolved = resolve_discovery_context(
        current,
        tuple(item["target_id"] for item in value["targets"]),
        operation=value["operation"],
        phase=value["phase"],
        task=value["task"],
        target_hint=value["target_hint"],
        focus_hint=value["focus_hint"],
        constraints=tuple(value["constraints"]),
        instructions=value["instructions"],
        worker_results=tuple(value["worker_results"]),
    )
    if resolved.serialized != snapshot.serialized:
        raise SpecError("Domain/Service discovery context changed", "stale_context")


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
