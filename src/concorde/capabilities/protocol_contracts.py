"""Profile 8 Operation registry and versioned JSON contracts.

Public names are paired Operations. Internal Skills describe only one host-bound agent role.
"""
from __future__ import annotations

from .wire_shapes import obj, array, STRING, PATH, DIGEST, ARTIFACT, typed_schema


TASK_FIELDS = {"target_id": STRING, "task": STRING, "focus_id": STRING,
               "constraints": array(STRING), "change_id": STRING}
TASK_OPTIONAL = ("focus_id", "constraints", "change_id")
NULLABLE_ID = {"anyOf": [STRING, {"type": "null"}]}
GAP = obj({"question": STRING, "blocked_step": STRING, "needed_contract": STRING,
           "target_id": STRING, "context_id": DIGEST}, ("target_id", "context_id"))
DOCUMENT_CHANGE = obj({"path": PATH, "content": {"type": "string"}})
TASK_ITEM = obj({"id": STRING, "target_id": STRING, "description": STRING,
                 "acceptance": STRING, "complete": {"type": "boolean"}})
CHECK_RESULT = obj({"check_id": STRING, "target_id": STRING,
    "status": {"enum": ["passed", "failed", "timeout"]}, "exit_code": {"type": "integer"},
    "source_digest": DIGEST, "log_digest": DIGEST})
ROUTE = obj({"target_id": STRING, "focus_id": NULLABLE_ID, "task": STRING,
             "constraints": array(STRING)})
WORKER_OUTCOMES = {"enum": ["completed", "spec_incomplete", "unsupported", "conflicting", "failed"]}
MAIN_OUTCOMES = {"enum": ["expand", "routed", "completed", "spec_incomplete",
                          "unsupported", "conflicting", "failed", "described",
                          "topology_proposed", "topology_prepared", "topology_applied"]}
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
    "concorde-clarify": ("specify", "concorde-spec-author"),
    "concorde-constitution": ("specify", "concorde-spec-author"),
    "concorde-checklist": ("plan", "concorde-planner"),
    "concorde-plan": ("plan", "concorde-planner"),
    "concorde-tasks": ("tasks", "concorde-task-author"),
    "concorde-implement": ("implementation", "concorde-implementation-worker"),
    "concorde-converge": ("implementation", "concorde-implementation-worker"),
    "concorde-analyze": ("context-solve", "concorde-context-assessor"),
    "concorde-context-solve": ("context-solve", "concorde-context-assessor"),
}
TARGET_AGENT_STAGES = {"concorde-read-target": ("ask", "concorde-reader")}
DETERMINISTIC_OPERATIONS = ("concorde-resolve-context", "concorde-context", "concorde-init",
    "concorde-configure", "concorde-migrate", "concorde-validate", "concorde-deliver", "concorde-taskstoissues")
COMPOSITE_OPERATIONS = ("concorde-standard-dev-loop", "concorde-fast-loop", "concorde-reflections-triage")
MAIN_OPERATION = "concorde-main"
OPERATIONS = tuple(sorted((MAIN_OPERATION, *AGENT_OPERATIONS, *DETERMINISTIC_OPERATIONS, *COMPOSITE_OPERATIONS)))
MAIN_ROUTED_OPERATIONS = frozenset({"concorde-analyze", MAIN_OPERATION, "concorde-checklist",
    "concorde-clarify", "concorde-constitution", "concorde-context-solve", "concorde-fast-loop",
    "concorde-plan", "concorde-specify", "concorde-standard-dev-loop"})
INTERNAL_SKILLS = tuple(sorted({"concorde-coordinator", *(role for _, role in AGENT_OPERATIONS.values()),
                                *(role for _, role in TARGET_AGENT_STAGES.values())}))
INTERNAL_DATA_TYPES = (
    "concorde-agent-stage-context",
    "concorde-agent-stage-result",
    "concorde-context-manifest",
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
    elif operation == "concorde-standard-dev-loop":
        result = tuple("concorde-"+x for x in ("specify","plan","tasks","implement","validate","deliver"))
    elif operation == "concorde-fast-loop":
        result = tuple("concorde-"+x for x in ("plan","tasks","implement","validate","deliver"))
    elif operation == "concorde-reflections-triage":
        result = ("concorde-implementation-worker", "concorde-standard-dev-loop")
    else:
        result = (AGENT_OPERATIONS[operation][1],) if operation in AGENT_OPERATIONS else ()
    return (("concorde-coordinator", *result)
            if operation in MAIN_ROUTED_OPERATIONS and operation != MAIN_OPERATION else result)


def contracts() -> dict[str, tuple[str, str]]:
    return {name: (f"{name}-request", f"{name}-response") for name in OPERATIONS}


def exported_types() -> tuple[str, ...]:
    return tuple(f"{operation}-{suffix}" for operation in OPERATIONS
                 for suffix in ("request", "response")) + INTERNAL_DATA_TYPES


def schemas() -> dict:
    result = {}
    for name in OPERATIONS:
        result[f"{name}-request"] = obj(TASK_FIELDS, TASK_OPTIONAL)
        result[f"{name}-response"] = obj({
            "target_id": STRING, "focus_id": NULLABLE_ID, "change_id": NULLABLE_ID,
            "context_id": {"anyOf": [DIGEST, {"type": "null"}]},
            "outcome": {"enum": ["completed", "spec_incomplete", "unsupported", "conflicting", "failed", "described", "delivered"]},
            "answer": {"type": "string"}, "artifacts": array(ARTIFACT), "gaps": array(GAP),
            "checks": array(CHECK_RESULT), "completed_operations": array(STRING)})
    for name in MAIN_ROUTED_OPERATIONS:
        result[f"{name}-request"] = obj(TASK_FIELDS, ("target_id", *TASK_OPTIONAL))
    result["concorde-main-request"] = obj({"action": {"enum": ["ask", "design-topology", "accept-topology", "apply-topology"]},
        "task": STRING, "target_id": STRING, "focus_id": STRING, "constraints": array(STRING),
        "topology_proposal": typed_schema("concorde-topology-proposal"),
        "application": ARTIFACT},
        ("action", "task", "target_id", "focus_id", "constraints", "topology_proposal", "application"))
    result["concorde-main-response"] = obj({
        "action": {"enum": ["ask", "design-topology", "accept-topology", "apply-topology"]},
        "entry_target": STRING, "context_id": {"anyOf": [DIGEST, {"type": "null"}]}, "outcome": MAIN_OUTCOMES,
        "answer": {"type": "string"}, "discovered_targets": array(STRING, unique=True),
        "routes": array(ROUTE), "worker_results": array(typed_schema("concorde-main-worker-result")),
        "topology_proposal": {"anyOf": [typed_schema("concorde-topology-proposal"), {"type": "null"}]},
        "application": {"anyOf": [ARTIFACT, {"type": "null"}]},
        "files": array(PATH, unique=True), "gaps": array(GAP), "completed_operations": array(STRING)})
    for name in ("concorde-context", "concorde-resolve-context"):
        result[f"{name}-request"] = obj({**TASK_FIELDS, "phase": {"enum": ["ask", "specify", "plan", "tasks", "implementation", "validate", "deliver", "context-solve"]}}, (*TASK_OPTIONAL, "phase"))
        result[f"{name}-response"] = obj({"manifest": typed_schema("concorde-context-manifest")})
    config = typed_schema("concorde-operation-configuration")
    proposal_file = obj({"path": PATH, "before_digest": {"anyOf": [DIGEST, {"type": "null"}]}, "content": {"type": "string"}})
    result["concorde-project-proposal"] = obj({"action": {"enum": ["initialize", "migrate"]},
        "base_digest": {"anyOf": [DIGEST, {"type": "null"}]}, "files": array(proposal_file)})
    # Proposed registry is transported as exact JSON text and decoded/validated by the registry service.
    result["concorde-init-request"] = obj({"action": {"enum": ["propose", "apply"]},
        "name": STRING, "target_id": STRING, "configuration": config,
        "proposal": typed_schema("concorde-project-proposal")}, ("name", "target_id", "configuration", "proposal"))
    result["concorde-migrate-request"] = obj({"action": {"enum": ["propose", "apply"]},
        "registry_json": STRING, "documents": array(DOCUMENT_CHANGE), "configuration": config,
        "proposal": typed_schema("concorde-project-proposal")}, ("registry_json", "documents", "configuration", "proposal"))
    result["concorde-configure-request"] = obj({"configuration": config})
    for name in ("concorde-init", "concorde-migrate"):
        result[f"{name}-response"] = obj({"status": {"enum": ["proposed", "applied"]},
            "proposal": {"anyOf": [typed_schema("concorde-project-proposal"), {"type": "null"}]}, "files": array(PATH)})
    result["concorde-configure-response"] = obj({"configuration": config, "status": {"const": "applied"}})
    result["concorde-validate-request"] = obj({**TASK_FIELDS, "run_checks": {"type": "boolean"}}, (*TASK_OPTIONAL, "run_checks"))
    result["concorde-reflections-triage-request"] = obj({**TASK_FIELDS,
        "action": {"enum": ["status", "investigate", "implement", "merge", "close"]},
        "reflection_ids": array(STRING, unique=True)}, (*TASK_OPTIONAL, "task"))
    document_ref = obj({"path": PATH, "digest": DIGEST})
    document = obj({"path": PATH, "digest": DIGEST, "content": {"type": "string"}})
    result["concorde-plan-artifact"] = obj({"plan": STRING})
    result["concorde-implementation-task"] = obj({"plan": STRING, "tasks": array(TASK_ITEM)})
    result["concorde-reflection-selection"] = obj({"head": STRING, "records": array(obj({"id":STRING,"path":PATH,"digest":DIGEST,"content":STRING}))})
    stage_input = {"anyOf":[typed_schema(name) for name in ("concorde-plan-artifact","concorde-implementation-task","concorde-reflection-selection")]}
    result["concorde-reflections-triage-response"]["properties"]["reflections"] = array(obj({"id":STRING,"target_id":STRING,"status":STRING,"triage":STRING,"bucket":STRING,"plan_status":NULLABLE_ID,"verification":NULLABLE_ID}))
    result["concorde-context-snapshot"] = obj({"context_id": DIGEST, "schema_version": {"const": 1},
        "target_id": STRING, "kind": {"enum": ["domain", "service", "module"]}, "focus_id": NULLABLE_ID,
        "phase": STRING, "task": STRING, "constraints": array(STRING),
        "protocol_binding": obj({"version": STRING, "digest": DIGEST}),
        "protocol": array(document), "documents": array(document), "instructions": {"type": "string"},
        "stage_inputs": array(stage_input), "implementation_artifacts": array(ARTIFACT)})
    result["concorde-context-manifest"] = obj({"schema_version": {"const": 1},
        "context_id": DIGEST, "target_id": STRING,
        "kind": {"enum": ["domain", "service", "module"]}, "focus_id": NULLABLE_ID,
        "phase": STRING, "protocol_binding": obj({"version": STRING, "digest": DIGEST}),
        "protocol": array(document_ref), "documents": array(document_ref)})
    result["concorde-agent-stage-context"] = obj({"snapshot": typed_schema("concorde-context-snapshot"),
        "change_id": NULLABLE_ID, "expected_artifacts": array(PATH)})
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
        "focus_hint": NULLABLE_ID, "design": typed_schema("concorde-topology-design")})
    result["concorde-topology-application"] = obj({"application_id": DIGEST,
        "topology_proposal": typed_schema("concorde-topology-proposal"),
        "base_registry_digest": DIGEST, "protocol_binding": obj({"version": STRING, "digest": DIGEST}),
        "files": {**array(PROPOSAL_FILE), "minItems": 1}})
    discovery_target = obj({"target_id": STRING, "kind": {"enum": ["domain", "service"]},
                            "documents": array(document)})
    result["concorde-discovery-context"] = obj({"context_id": DIGEST, "schema_version": {"const": 1},
        "operation": {"enum": sorted(MAIN_ROUTED_OPERATIONS)}, "phase": {"enum": ["route", "synthesize"]},
        "action": {"enum": ["route", "ask", "design-topology"]},
        "task": STRING, "constraints": array(STRING), "target_hint": NULLABLE_ID,
        "focus_hint": NULLABLE_ID, "protocol_binding": obj({"version": STRING, "digest": DIGEST}),
        "protocol": array(document), "topology": {"anyOf": [REGISTRY, {"type": "null"}]},
        "targets": array(discovery_target),
        "instructions": {"type": "string"},
        "worker_results": array(typed_schema("concorde-main-worker-result"))})
    result["concorde-main-stage-context"] = obj({
        "snapshot": typed_schema("concorde-discovery-context")})
    result["concorde-main-stage-result"] = obj({"context_id": DIGEST, "outcome": MAIN_OUTCOMES,
        "answer": {"type": "string"}, "expand_targets": array(STRING, unique=True),
        "routes": array(ROUTE), "gaps": array(GAP),
        "topology_design": {"anyOf": [typed_schema("concorde-topology-design"), {"type": "null"}]}})
    result["concorde-topology-author-context"] = obj({"context_id": DIGEST,
        "base_registry_digest": DIGEST, "target": TARGET_DESCRIPTOR, "task": STRING,
        "protocol_binding": obj({"version": STRING, "digest": DIGEST}),
        "protocol": array(document), "current_documents": array(document),
        "instructions": {"type": "string"}})
    result["concorde-topology-author-result"] = obj({"context_id": DIGEST, "target_id": STRING,
        "outcome": WORKER_OUTCOMES, "answer": {"type": "string"}, "gaps": array(GAP),
        "documents": array(DOCUMENT_CHANGE)})
    return result
