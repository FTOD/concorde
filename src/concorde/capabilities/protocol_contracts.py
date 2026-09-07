"""Profile 8 Operation registry and versioned JSON contracts.

Public names are paired Operations. Internal Skills describe only one host-bound agent role.
Per-capability request/response contracts are owned by the top-level ``capabilities/`` package
(one module per capability); ``schemas()`` collects them lazily so this module never imports that
package at module-load time. The internal (non-capability) data types below — topology
design/proposal/application, discovery context, context snapshots, review internals — are not
owned by any one capability and stay defined directly here.
"""
from __future__ import annotations

from .contract_shapes import ARTIFACT, DIGEST, GAP, MAIN_OUTCOMES, NULLABLE_ID, PATH, ROUTE, STRING, WORKSPACE_CONTEXT, array, obj, typed_schema

DOCUMENT_CHANGE = obj({"path": PATH, "content": {"type": "string"}})
TASK_ITEM = obj({"id": STRING, "target_id": STRING, "description": STRING,
                 "acceptance": STRING, "complete": {"type": "boolean"}})
WORKER_OUTCOMES = {"enum": ["completed", "spec_incomplete", "unsupported", "conflicting", "failed"]}
FOCUS = obj({"id": STRING, "title": STRING, "document": PATH})
DIAGRAM = obj({"source": PATH, "kind": STRING, "title": STRING})
CHECK = obj({"id": STRING, "target_id": STRING, "argv": {**array(STRING), "minItems": 1},
             "timeout_seconds": {"type": "integer", "minimum": 1, "maximum": 3600},
             "inputs": array(PATH, unique=True)}, ("inputs",))
TARGET_DESCRIPTOR = obj({"id": STRING, "kind": {"enum": ["domain", "service", "module"]},
    "title": STRING, "documents": {**array(PATH, unique=True), "minItems": 1},
    "scope_parent": NULLABLE_ID, "component_parent": NULLABLE_ID,
    "participates_in": array(STRING, unique=True), "implementation": array(PATH, unique=True),
    "features": array(FOCUS), "apis": array(FOCUS), "checks": array(STRING, unique=True),
    "diagrams": array(DIAGRAM)})
REGISTRY = obj({"schema_version": {"const": 1}, "project_id": STRING,
    "entry_target": STRING, "targets": {**array(TARGET_DESCRIPTOR), "minItems": 1},
    "checks": array(CHECK)})
SPEC_TASK = obj({"target_id": STRING, "task": STRING})
PROPOSAL_FILE = obj({"path": PATH, "before_digest": {"anyOf": [DIGEST, {"type": "null"}]},
                     "content": {"type": "string"}})

AGENT_OPERATIONS = {
    "concorde-specify": ("specify", "concorde-spec-author"),
    "concorde-plan": ("plan", "concorde-planner"),
    "concorde-tasks": ("tasks", "concorde-task-author"),
    "concorde-implement": ("implementation", "concorde-implementation-worker"),
    "concorde-context-solve": ("context-solve", "concorde-context-assessor"),
}
TARGET_AGENT_STAGES = {"concorde-read-target": ("ask", "concorde-reader")}
REVIEW_STAGES = {"spec": ("spec-review", "concorde-spec-reviewer"),
                 "code": ("code-review", "concorde-code-reviewer")}
MAIN_OPERATION = "concorde-main"
GLOBAL_OPERATIONS = (MAIN_OPERATION, "concorde-dev-loop", "concorde-reflections-triage")
DETERMINISTIC_OPERATIONS = ("concorde-init", "concorde-configure", "concorde-validate", "concorde-deliver")
LIFECYCLE_OPERATIONS = DETERMINISTIC_OPERATIONS
INTERNAL_OPERATIONS = ("concorde-specify", "concorde-review", "concorde-context-solve",
                       "concorde-plan", "concorde-tasks", "concorde-implement")
PUBLIC_OPERATIONS = tuple(sorted(GLOBAL_OPERATIONS + LIFECYCLE_OPERATIONS))
OPERATIONS = tuple(sorted((*GLOBAL_OPERATIONS, *LIFECYCLE_OPERATIONS, *INTERNAL_OPERATIONS)))
assert set(PUBLIC_OPERATIONS) | set(INTERNAL_OPERATIONS) == set(OPERATIONS), "Operation classes must partition OPERATIONS"
assert not (set(PUBLIC_OPERATIONS) & set(INTERNAL_OPERATIONS)), "Operation classes must be disjoint"
assert len(OPERATIONS) == len(set(OPERATIONS)), "OPERATIONS must not contain duplicates"
MAIN_ROUTED_OPERATIONS = frozenset({MAIN_OPERATION, "concorde-dev-loop"})
# Capabilities whose module declares a nonempty USES (it composes other capabilities in-process).
COMPOSITE_OPERATIONS = ("concorde-dev-loop", "concorde-reflections-triage")
INTERNAL_SKILLS = tuple(sorted({"concorde-coordinator", *(role for _, role in AGENT_OPERATIONS.values()),
                                *(role for _, role in REVIEW_STAGES.values()),
                                *(role for _, role in TARGET_AGENT_STAGES.values())}))
INTERNAL_DATA_TYPES = (
    "concorde-agent-stage-context",
    "concorde-agent-stage-result",
    "concorde-review-input",
    "concorde-review-stage-context",
    "concorde-review-stage-result",
    "concorde-review-result",
    "concorde-context-snapshot",
    "concorde-discovery-context",
    "concorde-main-stage-context",
    "concorde-main-stage-result",
    "concorde-main-worker-result",
    "concorde-topology-author-context",
    "concorde-topology-author-result",
    "concorde-topology-application",
    "concorde-topology-design",
    "concorde-topology-proposal",
)


def dependencies(operation: str) -> tuple[str, ...]:
    if operation == MAIN_OPERATION:
        result = ("concorde-coordinator", "concorde-reader", "concorde-spec-author")
    elif operation == "concorde-plan":
        result = ("concorde-context-assessor", "concorde-planner")
    elif operation == "concorde-review":
        result = tuple(role for _, role in REVIEW_STAGES.values())
    elif operation == "concorde-dev-loop":
        result = tuple("concorde-"+x for x in ("specify","review","plan","tasks","implement","validate"))
    elif operation == "concorde-reflections-triage":
        result = ("concorde-implementation-worker", "concorde-dev-loop")
    else:
        result = (AGENT_OPERATIONS[operation][1],) if operation in AGENT_OPERATIONS else ()
    return (("concorde-coordinator", *result)
            if operation in MAIN_ROUTED_OPERATIONS and operation != MAIN_OPERATION else result)


def contracts() -> dict[str, tuple[str, str]]:
    return {name: (f"{name}-request", f"{name}-response") for name in OPERATIONS}


def exported_types() -> tuple[str, ...]:
    return tuple(f"{operation}-{suffix}" for operation in OPERATIONS
                 for suffix in ("request", "response")) + INTERNAL_DATA_TYPES


_CAPABILITY_INVENTORY_MODULE_NAME = "_concorde_capabilities_inventory"


def load_capability_inventory():
    """Load the repository-root ``capabilities`` package by file path, under a private
    internal module name distinct from the plain ``capabilities`` name.

    A name lookup (``import capabilities``, relying on ``sys.path`` search order) is not safe
    here: test discovery (``unittest discover -s tests/concorde``) treats that directory as a
    search root and, walking it, imports ``tests/concorde/capabilities/__init__.py`` as a
    top-level module named ``capabilities`` — an unrelated test package that happens to share
    this name. Registering our own package under the plain name too would then break that
    discovery walk's own later imports of ``capabilities.unit``/``capabilities.integration`` in
    the same process. Resolving by file path under a private name avoids the collision in both
    directions.
    """

    import importlib.util
    import sys
    from pathlib import Path

    cached = sys.modules.get(_CAPABILITY_INVENTORY_MODULE_NAME)
    if cached is not None:
        return cached
    package_root = Path(__file__).resolve().parents[3]
    init_path = package_root / "capabilities" / "__init__.py"
    spec = importlib.util.spec_from_file_location(
        _CAPABILITY_INVENTORY_MODULE_NAME, init_path,
        submodule_search_locations=[str(package_root / "capabilities")],
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[_CAPABILITY_INVENTORY_MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


def _capability_schemas() -> dict:
    """Collect every capability module's own REQUEST/RESPONSE (proposal section 6.2).

    Imported lazily, and only here, so this module never depends on the top-level
    ``capabilities`` package at import time (avoiding any import-order cycle with it).
    """

    import importlib

    capability_inventory = load_capability_inventory()
    result = {}
    for name in capability_inventory.CAPABILITIES:
        module = importlib.import_module(f"{capability_inventory.__name__}.{name}")
        result[f"{module.EXTERNAL_NAME}-request"] = module.REQUEST
        result[f"{module.EXTERNAL_NAME}-response"] = module.RESPONSE
    return result


def schemas() -> dict:
    result = {}
    document_ref = obj({"document_id": STRING, "path": PATH, "digest": DIGEST,
        "targets": {**array(STRING, unique=True), "minItems": 1},
        "main_visible": {"type": "boolean"}})
    document = obj({**document_ref["properties"], "content": {"type": "string"}})
    protocol_document = obj({"path": PATH, "digest": DIGEST, "content": {"type": "string"}})
    result["concorde-project-proposal"] = obj({"action": {"enum": ["initialize"]},
        "base_digest": {"anyOf": [DIGEST, {"type": "null"}]}, "files": array(PROPOSAL_FILE)})
    result["concorde-plan-artifact"] = obj({"plan": STRING})
    result["concorde-implementation-task"] = obj({"plan": STRING, "tasks": array(TASK_ITEM)})
    result["concorde-reflection-selection"] = obj({"head": STRING, "records": array(obj({"id":STRING,"path":PATH,"digest":DIGEST,"content":STRING}))})
    stage_input = {"anyOf":[typed_schema(name) for name in ("concorde-plan-artifact","concorde-implementation-task","concorde-reflection-selection")]}
    result["concorde-context-snapshot"] = obj({"context_id": DIGEST, "schema_version": {"const": 1},
        "target_id": STRING, "kind": {"enum": ["domain", "service", "module"]}, "focus_id": NULLABLE_ID,
        "phase": STRING, "task": STRING, "constraints": array(STRING),
        "protocol_binding": obj({"version": STRING, "digest": DIGEST}),
        "protocol": array(protocol_document),
        "document_order": array(PATH, unique=True), "target_spec": array(document),
        "shared_specs": array(document), "instructions": {"type": "string"},
        "stage_inputs": array(stage_input), "implementation_artifacts": array(ARTIFACT),
        "workspace": WORKSPACE_CONTEXT})
    result["concorde-agent-stage-context"] = obj({"snapshot": typed_schema("concorde-context-snapshot"),
        "change_id": NULLABLE_ID, "expected_artifacts": array(PATH)})
    revision = obj({"spec_digest": DIGEST,
        "implementation_digest": {"anyOf": [DIGEST, {"type": "null"}]},
        "baseline": NULLABLE_ID, "head": NULLABLE_ID})
    result["concorde-review-input"] = obj({"review_mode": {"enum": ["spec", "code"]},
        "input_digest": DIGEST, "revision": revision,
        "changes": array(obj({"path": PATH, "patch": {"type": "string"}}))})
    result["concorde-review-stage-context"] = obj({"snapshot": typed_schema("concorde-context-snapshot"),
        "review": typed_schema("concorde-review-input")})
    review_fields = {"context_id": DIGEST, "input_digest": DIGEST,
        "review_mode": {"enum": ["spec", "code"]},
        "status": {"enum": ["no_findings", "findings", "incomplete"]},
        "representative_tasks": array(STRING, unique=True),
        "findings": array(obj({"id": STRING, "severity": {"enum": ["blocking", "advisory"]},
            "target_id": STRING, "document": PATH, "contract": STRING,
            "location": obj({"path": PATH, "line": {"anyOf": [
                {"type": "integer", "minimum": 1}, {"type": "null"}]}}),
            "problem": STRING, "affected_task": STRING})),
        "gaps": array(GAP), "answer": STRING}
    result["concorde-review-stage-result"] = obj(review_fields)
    result["concorde-review-result"] = obj({**review_fields,
        "context_id": {"anyOf": [DIGEST, {"type": "null"}]},
        "status": {"enum": ["no_findings", "findings", "incomplete", "skipped", "not_run"]},
        "target_id": STRING, "focus_id": NULLABLE_ID, "revision": revision,
        "semantic_completeness": {"const": "not_proven"}})
    result["concorde-agent-stage-result"] = obj({"context_id": DIGEST,
        "outcome": {"enum": ["completed", "sufficient", "spec_incomplete", "unsupported", "conflicting", "failed"]},
        "answer": {"type": "string"}, "gaps": array(GAP), "documents": array(DOCUMENT_CHANGE),
        "plan": {"type": "string"}, "tasks": array(TASK_ITEM),
        "reflection_findings": array(obj({"reflection_id":STRING,"verified_commit":STRING,
          "observed_state":{"enum":["reproduced","not-reproduced"]},"verification":STRING,"analysis":STRING,"resolution":STRING,
          "intervention_rationale":STRING,"human_intervention":{"enum":["required","not-required"]},
          "route":{"enum":["fast-loop","plan","dismiss","blocked"]},"effort":{"enum":["small","medium","large"]},
          "files":array(PATH,unique=True),"steps":STRING,"validation":STRING,"risks":STRING,"protocol_change":{"type":"boolean"}}))}, ("reflection_findings",))
    result["concorde-main-worker-result"] = obj({"target_id": STRING, "focus_id": NULLABLE_ID,
        "context_id": DIGEST, "outcome": WORKER_OUTCOMES, "answer": {"type": "string"},
        "gaps": array(GAP)})
    result["concorde-topology-design"] = obj({"summary": STRING, "registry": REGISTRY,
        "spec_tasks": {**array(SPEC_TASK), "minItems": 1},
        "migration_constraints": array(STRING), "acceptance": {**array(STRING), "minItems": 1}})
    result["concorde-topology-proposal"] = obj({"proposal_id": DIGEST,
        "base_registry_digest": DIGEST, "protocol_binding": obj({"version": STRING, "digest": DIGEST}),
        "context_id": DIGEST, "discovered_targets": {**array(STRING, unique=True), "minItems": 1},
        "task": STRING, "constraints": array(STRING), "target_hint": NULLABLE_ID,
        "focus_hint": NULLABLE_ID, "design": typed_schema("concorde-topology-design"),
        "workspace": WORKSPACE_CONTEXT})
    result["concorde-topology-application"] = obj({"application_id": DIGEST,
        "topology_proposal": typed_schema("concorde-topology-proposal"),
        "base_registry_digest": DIGEST, "protocol_binding": obj({"version": STRING, "digest": DIGEST}),
        "files": {**array(PROPOSAL_FILE), "minItems": 1}})
    discovery_target = obj({"target_id": STRING, "kind": {"enum": ["domain", "service"]},
                            "document_order": array(PATH, unique=True),
                            "target_spec": array(document), "shared_specs": array(document)})
    result["concorde-discovery-context"] = obj({"context_id": DIGEST, "schema_version": {"const": 1},
        "operation": {"enum": sorted(MAIN_ROUTED_OPERATIONS)}, "phase": {"enum": ["route", "synthesize"]},
        "action": {"enum": ["route", "ask", "design-topology"]},
        "task": STRING, "constraints": array(STRING), "target_hint": NULLABLE_ID,
        "focus_hint": NULLABLE_ID, "protocol_binding": obj({"version": STRING, "digest": DIGEST}),
        "protocol": array(protocol_document), "topology": {"anyOf": [REGISTRY, {"type": "null"}]},
        "targets": array(discovery_target),
        "instructions": {"type": "string"},
        "worker_results": array(typed_schema("concorde-main-worker-result")),
        "workspace": WORKSPACE_CONTEXT})
    result["concorde-main-stage-context"] = obj({
        "snapshot": typed_schema("concorde-discovery-context")})
    result["concorde-main-stage-result"] = obj({"context_id": DIGEST, "outcome": MAIN_OUTCOMES,
        "answer": {"type": "string"}, "expand_targets": array(STRING, unique=True),
        "routes": array(ROUTE), "gaps": array(GAP),
        "topology_design": {"anyOf": [typed_schema("concorde-topology-design"), {"type": "null"}]}})
    result["concorde-topology-author-context"] = obj({"context_id": DIGEST,
        "base_registry_digest": DIGEST, "target": TARGET_DESCRIPTOR, "task": STRING,
        "protocol_binding": obj({"version": STRING, "digest": DIGEST}),
        "protocol": array(protocol_document),
        "candidate_document_references": array(obj({"path": PATH,
            "targets": {**array(STRING, unique=True), "minItems": 1}})),
        "current_document_order": array(PATH, unique=True),
        "target_spec": array(document), "shared_specs": array(document),
        "instructions": {"type": "string"}, "workspace": WORKSPACE_CONTEXT})
    result["concorde-topology-author-result"] = obj({"context_id": DIGEST, "target_id": STRING,
        "outcome": WORKER_OUTCOMES, "answer": {"type": "string"}, "gaps": array(GAP),
        "documents": array(DOCUMENT_CHANGE)})
    result.update(_capability_schemas())
    return result
