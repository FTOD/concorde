"""Topology design responses, proposal admission and the design inspection they share."""

from __future__ import annotations

import copy
import json

from ..distribution.build import load_model_instructions
from ..harness.change_worktree import workspace_context
from ..harness.context import resolve_discovery_context
from ..harness.host import OperationHost
from ..spec.contracts import DISCOVERY_NODES, MAIN_OPERATION
from ..spec.repository import SpecError, SpecRepository, digest
from ..spec.typed_data import typed, validate_typed
from ..spec.validation import module_dependency_findings


def run_topology_design(main) -> dict:
    _, decision = main.discover_routes()
    return topology_response(main, decision)


def topology_response(main, decision):
    if main.host.mode == "describe-policy":
        return main.main_response("described")
    if decision is None or decision["outcome"] != "topology_proposed":
        if decision is None:
            raise SpecError(
                "topology design returned worker routes", "invalid_completion"
            )
        return main.main_response(
            decision["outcome"], decision["answer"], blockers=decision["blockers"]
        )
    inspect_topology_design(
        main.repository,
        decision["topology_design"],
        tuple(main.discovered),
    )
    if main.last_snapshot is None:
        raise SpecError(
            "topology design has no admitted discovery snapshot",
            "invalid_completion",
        )
    payload = {
        "base_registry_digest": digest(main.repository.registry_bytes),
        "protocol_binding": main.repository.config["protocol"],
        "context_id": main.last_context,
        "discovered_targets": list(main.discovered),
        "task": main.task["task"],
        "constraints": main.task.get("constraints", []),
        "target_hint": main.task.get("target_id"),
        "focus_hint": main.task.get("focus_id"),
        "design": decision["topology_design"],
        "workspace": main.last_snapshot.value["workspace"],
    }
    proposal = typed(
        "concorde-topology-proposal",
        {
            "proposal_id": digest(payload),
            **payload,
        },
    )
    main.completed.append("concorde-topology-designer-design")
    return main.main_response(
        "topology_proposed", decision["answer"], topology_proposal=proposal
    )


def inspect_topology_design(
    repository: SpecRepository, design_value: dict, discovered_targets: tuple[str, ...]
) -> tuple[dict, dict, bytes, dict[str, dict], dict[str, dict], dict[str, str]]:
    """Validate everything knowable before target-local document authoring."""

    design = validate_typed(design_value, "concorde-topology-design")["data"]
    candidate = copy.deepcopy(design["registry"])
    if candidate["project_id"] != repository.registry["project_id"]:
        raise SpecError(
            "topology design cannot replace project identity", "invalid_proposal"
        )
    candidate_bytes = (json.dumps(candidate, indent=2, sort_keys=True) + "\n").encode()
    # This validates IDs, parentage, ownership, focus/check references and entry selection without
    # opening the candidate document paths. Their existence/content is validated after authoring.
    try:
        SpecRepository(
            repository.root,
            repository.package_root,
            registry_bytes=candidate_bytes,
            _defer_document_admission=True,
        )
    except SpecError as error:
        raise SpecError(
            "topology candidate registry is invalid: " + str(error),
            "invalid_proposal",
            error.field,
        ) from error
    current_targets = {item["id"]: item for item in repository.registry["targets"]}
    candidate_targets = {item["id"]: item for item in candidate["targets"]}
    tasks = {item["target_id"]: item["task"] for item in design["spec_tasks"]}
    if len(tasks) != len(design["spec_tasks"]):
        raise SpecError(
            "topology design contains duplicate Spec tasks", "invalid_proposal"
        )
    if any(target_id not in candidate_targets for target_id in tasks):
        raise SpecError(
            "topology Spec task names a removed or unknown target", "invalid_proposal"
        )
    changed = {
        target_id
        for target_id, target in candidate_targets.items()
        if current_targets.get(target_id) != target
    }
    changed.update(set(current_targets) - set(candidate_targets))
    current_document_references: dict[str, set[str]] = {}
    candidate_document_references: dict[str, set[str]] = {}
    for target_id, target in current_targets.items():
        for path in target["documents"]:
            current_document_references.setdefault(path, set()).add(target_id)
    for target_id, target in candidate_targets.items():
        for path in target["documents"]:
            candidate_document_references.setdefault(path, set()).add(target_id)
    changed_memberships = {
        path
        for path in set(current_document_references)
        | set(candidate_document_references)
        if current_document_references.get(path, set())
        != candidate_document_references.get(path, set())
    }
    affected_document_targets = set()
    for path in changed_memberships:
        affected_document_targets.update(current_document_references.get(path, set()))
        affected_document_targets.update(candidate_document_references.get(path, set()))
    missing_document_tasks = sorted(
        target_id
        for target_id in affected_document_targets
        if target_id in candidate_targets and target_id not in tasks
    )
    if missing_document_tasks:
        raise SpecError(
            f"changed document ownership requires every retained owner task: {missing_document_tasks}",
            "invalid_proposal",
        )

    def relations(targets):
        result = {
            (target_id, peer)
            for target_id, target in targets.items()
            for peer in target["uses"]
        }
        result.update(
            (target["parent"], target_id)
            for target_id, target in targets.items()
            if target["parent"] is not None
        )
        return result

    affected_modules = {
        owner for owner, _ in relations(current_targets) ^ relations(candidate_targets)
    }
    affected_modules.update(
        finding.subject_id
        for finding in module_dependency_findings(repository)
        if finding.subject_id is not None
    )
    # A Module whose listed files change must rewrite its own entity declarations, and every
    # Module that lists a file whose listing set changed is affected by that shared change.
    current_file_users: dict[str, set[str]] = {}
    candidate_file_users: dict[str, set[str]] = {}
    for target_id, target in current_targets.items():
        for path in target["files"]:
            current_file_users.setdefault(path, set()).add(target_id)
    for target_id, target in candidate_targets.items():
        for path in target["files"]:
            candidate_file_users.setdefault(path, set()).add(target_id)
    affected_modules.update(
        target_id
        for target_id, target in candidate_targets.items()
        if list(current_targets.get(target_id, {}).get("files", []))
        != list(target["files"])
    )
    for path in set(current_file_users) | set(candidate_file_users):
        if current_file_users.get(path, set()) != candidate_file_users.get(path, set()):
            affected_modules.update(current_file_users.get(path, set()))
            affected_modules.update(candidate_file_users.get(path, set()))
    missing_dependency_tasks = sorted(
        target_id
        for target_id in affected_modules
        if target_id in candidate_targets and target_id not in tasks
    )
    if missing_dependency_tasks:
        raise SpecError(
            f"changed dependencies or shared file listings require Module tasks: {missing_dependency_tasks}",
            "invalid_proposal",
        )
    discovered = set(discovered_targets)
    unread_existing = sorted(
        target_id
        for target_id in (changed | tasks.keys())
        if target_id in current_targets
        and current_targets[target_id]["kind"] == "module"
        and target_id not in discovered
    )
    if unread_existing:
        raise SpecError(
            f"topology design did not admit affected Module Specs: {unread_existing}",
            "invalid_proposal",
        )
    missing_tasks = sorted((changed & candidate_targets.keys()) - tasks.keys())
    if missing_tasks:
        raise SpecError(
            f"changed topology targets require local Spec tasks: {missing_tasks}",
            "invalid_proposal",
        )
    if candidate == repository.registry and not tasks:
        raise SpecError("topology proposal contains no change", "invalid_proposal")
    return design, candidate, candidate_bytes, current_targets, candidate_targets, tasks


def validate_topology_proposal(
    host: OperationHost, proposal: dict
) -> tuple[SpecRepository, dict]:
    value = validate_typed(proposal, "concorde-topology-proposal")
    data = value["data"]
    identity = {key: item for key, item in data.items() if key != "proposal_id"}
    if digest(identity) != data["proposal_id"]:
        raise SpecError("topology proposal identity is invalid", "invalid_proposal")
    repository = SpecRepository(host.project_root, host.package_root)
    if digest(repository.registry_bytes) != data["base_registry_digest"]:
        raise SpecError("topology proposal registry base changed", "stale_proposal")
    if repository.config["protocol"] != data["protocol_binding"]:
        raise SpecError("topology proposal Protocol binding changed", "stale_proposal")
    prompt = load_model_instructions(
        host.package_root, DISCOVERY_NODES["design-topology"]
    )
    snapshot = resolve_discovery_context(
        repository,
        tuple(data["discovered_targets"]),
        operation=MAIN_OPERATION,
        phase="route",
        action="design-topology",
        task=data["task"],
        target_hint=data["target_hint"],
        focus_hint=data["focus_hint"],
        constraints=tuple(data["constraints"]),
        instructions=prompt.body,
        workspace=data["workspace"],
    )
    if snapshot.id != data["context_id"]:
        raise SpecError("topology proposal discovery context changed", "stale_proposal")
    return repository, value


def main_topology_response(
    action: str,
    repository: SpecRepository,
    proposal: dict,
    *,
    outcome: str,
    answer: str,
    application=None,
    files=(),
    blockers=(),
    completed=(),
) -> dict:
    data = proposal["data"]
    design = data["design"]["data"]
    return typed(
        "concorde-main-response",
        {
            "action": action,
            "entry_target": design["registry"]["entry_target"],
            "context_id": data["context_id"],
            "outcome": outcome,
            "answer": answer,
            "discovered_targets": data["discovered_targets"],
            "routes": [],
            "topology_proposal": proposal if action == "accept-topology" else None,
            "application": application,
            "files": list(files),
            "blockers": list(blockers),
            "completed_operations": list(completed),
            "workspace": workspace_context(repository.root),
        },
    )
