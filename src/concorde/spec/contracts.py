"""Profile 11 capability registry and versioned JSON contracts.

Public global and lifecycle capabilities are each paired with exactly one skill. Internal Skills
describe only one host-bound agent role. Per-capability request/response contracts are owned by
the top-level ``capabilities/`` package
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
CHECK = obj({"id": STRING, "target_id": STRING, "argv": {**array(STRING), "minItems": 1},
             "timeout_seconds": {"type": "integer", "minimum": 1, "maximum": 3600},
             "inputs": array(PATH, unique=True)}, ("inputs",))
LISTING_ENTRY = {**STRING, "pattern": r"^[^/](?:[^/]*/)*[^/]*$"}
TARGET_DESCRIPTOR = obj({"id": STRING, "kind": {"const": "module"},
    "title": STRING, "documents": {**array(PATH, unique=True), "minItems": 1},
    "parent": NULLABLE_ID, "uses": array(STRING, unique=True),
    "files": array(LISTING_ENTRY, unique=True), "checks": array(STRING, unique=True)})
IMPLEMENTATION_FILE = obj({"path": PATH, "entity_id": NULLABLE_ID, "pending": {"type": "boolean"}})
IMPLEMENTATION_ENTRY = obj({"path": LISTING_ENTRY, "entity_id": NULLABLE_ID, "pending": {"type": "boolean"},
                            "directory": {"type": "boolean"}})
REGISTRY = obj({"schema_version": {"const": 3}, "project_id": STRING,
    "entry_target": STRING, "targets": {**array(TARGET_DESCRIPTOR), "minItems": 1},
    "checks": array(CHECK)})
SPEC_TASK = obj({"target_id": STRING, "task": STRING})
PROPOSAL_FILE = obj({"path": PATH, "before_digest": {"anyOf": [DIGEST, {"type": "null"}]},
                     "content": {"type": "string"}})

STAGE_ROLES = {
    "concorde-specify": ("specify", "concorde-spec-engineer"),
    "concorde-plan": ("plan", "concorde-spec-engineer"),
    "concorde-tasks": ("tasks", "concorde-spec-engineer"),
    "concorde-implement": ("implementation", "concorde-programmer"),
    "concorde-context-solve": ("context-solve", "concorde-spec-engineer"),
}
REVIEW_STAGES = {"spec": ("spec-review", "concorde-spec-engineer"),
                 "code": ("code-review", "concorde-programmer")}
MAIN_CAPABILITY = "concorde-main"
GLOBAL_CAPABILITIES = (MAIN_CAPABILITY, "concorde-dev-loop", "concorde-reflections-triage", "concorde-review")
LIFECYCLE_CAPABILITIES = ("concorde-init", "concorde-configure", "concorde-validate", "concorde-deliver")
STAGE_CAPABILITIES = ("concorde-specify", "concorde-context-solve",
                       "concorde-plan", "concorde-tasks", "concorde-implement")
SKILL_NAMES = tuple(sorted(GLOBAL_CAPABILITIES + LIFECYCLE_CAPABILITIES))
CAPABILITY_NAMES = tuple(sorted((*GLOBAL_CAPABILITIES, *LIFECYCLE_CAPABILITIES, *STAGE_CAPABILITIES)))
assert set(SKILL_NAMES) | set(STAGE_CAPABILITIES) == set(CAPABILITY_NAMES), "capability classes must partition CAPABILITY_NAMES"
assert not (set(SKILL_NAMES) & set(STAGE_CAPABILITIES)), "capability classes must be disjoint"
assert len(CAPABILITY_NAMES) == len(set(CAPABILITY_NAMES)), "CAPABILITY_NAMES must not contain duplicates"
MAIN_ROUTED_CAPABILITIES = frozenset({MAIN_CAPABILITY, "concorde-dev-loop", "concorde-review"})
# Capabilities whose module declares a nonempty USES (it composes other capabilities in-process).
COMPOSITE_CAPABILITIES = ("concorde-dev-loop", "concorde-reflections-triage")
INTERNAL_SKILLS = tuple(sorted({"concorde-coordinator", *(role for _, role in STAGE_ROLES.values()),
                                *(role for _, role in REVIEW_STAGES.values())}))
INTERNAL_DATA_TYPES = (
    "concorde-agent-task",
    "concorde-agent-answer",
    "concorde-agent-interruption",
    "concorde-agent-loop-context",
    "concorde-agent-loop-step",
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
    "concorde-topology-author-context",
    "concorde-topology-author-result",
    "concorde-topology-application",
    "concorde-topology-design",
    "concorde-topology-proposal",
)


def dependencies(capability: str) -> tuple[str, ...]:
    if capability == MAIN_CAPABILITY:
        result = ("concorde-coordinator", "concorde-spec-engineer")
    elif capability == "concorde-plan":
        result = ("concorde-spec-engineer",)
    elif capability == "concorde-review":
        result = tuple(role for _, role in REVIEW_STAGES.values())
    elif capability == "concorde-dev-loop":
        result = tuple("concorde-"+x for x in ("specify","review","plan","tasks","implement","validate"))
    elif capability == "concorde-reflections-triage":
        result = ("concorde-programmer", "concorde-dev-loop")
    else:
        result = (STAGE_ROLES[capability][1],) if capability in STAGE_ROLES else ()
    return (("concorde-coordinator", *result)
            if capability in MAIN_ROUTED_CAPABILITIES and capability != MAIN_CAPABILITY else result)


def contracts() -> dict[str, tuple[str, str]]:
    return {name: (f"{name}-request", f"{name}-response") for name in CAPABILITY_NAMES}


def exported_types() -> tuple[str, ...]:
    return tuple(f"{capability}-{suffix}" for capability in CAPABILITY_NAMES
                 for suffix in ("request", "response")) + INTERNAL_DATA_TYPES


def load_capability_inventory():
    """Import the repository-root ``capabilities`` package normally.

    ``tests/concorde`` holds one flat package per Module and none of them is named
    ``capabilities``, so test discovery (``unittest discover -s tests/concorde``) no longer risks
    registering an unrelated test package under the plain ``capabilities`` name. A plain import
    is therefore safe here.
    """

    import sys
    from pathlib import Path

    package_root = Path(__file__).resolve().parents[3]
    if str(package_root) not in sys.path:
        sys.path.insert(0, str(package_root))
    import capabilities

    return capabilities


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
    outcomes = {"enum": ["completed", "spec_incomplete", "waiting", "cancelled", "failed", "limit_exhausted", "rejected"]}
    interruption = obj({"gaps": array(obj(GAP["properties"])), "decision": NULLABLE_ID})
    result["concorde-agent-task"] = obj({"task": STRING, "target_id": STRING})
    result["concorde-agent-answer"] = obj({"answer": STRING})
    result["concorde-agent-interruption"] = interruption
    details = {"anyOf": [typed_schema("concorde-agent-interruption"), {"type": "null"}]}
    feedback = obj({"invocation_id": STRING, "parent_id": NULLABLE_ID, "agent_id": STRING,
        "outcome": outcomes, "value_json": NULLABLE_ID, "error": NULLABLE_ID, "details": details})
    child = obj({"agent_id": STRING, "input_type": STRING, "result_type": STRING,
        "input_schema_json": STRING, "result_schema_json": STRING})
    result["concorde-agent-loop-context"] = obj({"invocation_id": STRING,
        "parent_id": NULLABLE_ID, "agent_id": STRING, "input_json": STRING,
        "context_json": STRING, "feedback": array(feedback), "children": array(child),
        "result_schema_json": STRING})
    result["concorde-agent-loop-step"] = obj({"source": {"enum": ["code-driven", "model-driven"]},
        "action": {"enum": ["delegate", "complete"]}, "agent_id": NULLABLE_ID,
        "value_json": NULLABLE_ID, "outcome": outcomes, "details": details})
    document_ref = obj({"document_id": STRING, "path": PATH, "digest": DIGEST,
        "targets": {**array(STRING, unique=True), "minItems": 1},
        "main_visible": {"type": "boolean"}})
    document = obj({**document_ref["properties"], "content": {"type": "string"}})
    protocol_document = obj({"path": PATH, "digest": DIGEST, "content": {"type": "string"}})
    result["concorde-project-proposal"] = obj({"action": {"enum": ["initialize"]},
        "base_digest": {"anyOf": [DIGEST, {"type": "null"}]}, "files": array(PROPOSAL_FILE)})
    result["concorde-plan-artifact"] = obj({"plan": STRING})
    result["concorde-implementation-task"] = obj({"plan": STRING, "tasks": array(TASK_ITEM)})
    result["concorde-task-scope-feedback"] = obj({"tasks_digest": DIGEST,
        "reason": {"const": "implementation_boundary"}})
    result["concorde-reflection-selection"] = obj({"head": STRING, "records": array(obj({"id":STRING,"path":PATH,"digest":DIGEST,"content":STRING}))})
    stage_input = {"anyOf":[typed_schema(name) for name in ("concorde-plan-artifact","concorde-implementation-task","concorde-task-scope-feedback","concorde-reflection-selection","concorde-review-result")]}
    result["concorde-context-snapshot"] = obj({"context_id": DIGEST, "schema_version": {"const": 3},
        "target_id": STRING, "kind": {"const": "module"}, "focus_id": NULLABLE_ID,
        "phase": STRING, "task": STRING, "constraints": array(STRING),
        "protocol_binding": obj({"version": STRING, "digest": DIGEST}),
        "protocol": array(protocol_document),
        "document_order": array(PATH, unique=True), "target_spec": array(document),
        "shared_specs": array(document), "instructions": {"type": "string"},
        "stage_inputs": array(stage_input),
        "implementation_entries": array(IMPLEMENTATION_ENTRY),
        "implementation_files": array(IMPLEMENTATION_FILE),
        "implementation_artifacts": array(ARTIFACT),
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
    discovery_target = obj({"target_id": STRING, "kind": {"const": "module"},
                            "document_order": array(PATH, unique=True),
                            "target_spec": array(document_ref), "shared_specs": array(document_ref)})
    result["concorde-discovery-context"] = obj({"context_id": DIGEST, "schema_version": {"const": 2},
        "capability": {"enum": sorted(MAIN_ROUTED_CAPABILITIES)}, "phase": {"const": "route"},
        "action": {"enum": ["route", "ask", "design-topology"]},
        "task": STRING, "constraints": array(STRING), "target_hint": NULLABLE_ID,
        "focus_hint": NULLABLE_ID, "protocol_binding": obj({"version": STRING, "digest": DIGEST}),
        "protocol": array(protocol_document), "topology": {"anyOf": [REGISTRY, {"type": "null"}]},
        "targets": array(discovery_target),
        "documents": array(document),
        "instructions": {"type": "string"},
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
