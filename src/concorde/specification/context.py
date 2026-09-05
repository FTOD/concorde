"""Immutable cognitive inputs, separate from host-only execution grants."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..capabilities.operation_data import canonical
from .repository import SpecError, SpecRepository, digest, read_file


PHASES = frozenset({"ask", "specify", "plan", "tasks", "implementation", "validate", "deliver", "context-solve"})


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
