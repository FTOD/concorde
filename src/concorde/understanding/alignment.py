"""Read-only, evidence-qualified Concorde and Understand Anything alignment."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping

from ..diagnostics import digest_sources, finding_key
from ..model import ArchitecturePackage, Finding, ToolResult
from ..projection import feature_summary
from .repository import ProjectRepository, RepositoryError, safe_relative_path


ALIGNMENT_SCHEMA_VERSION = 1
UA_REPOSITORY = "https://github.com/Egonex-AI/Understand-Anything"
UA_REVISION = "ba450c43425f3de6d43daf76526950ad8ca93536"

UA_NODE_TYPES = (
    "file", "function", "class", "module", "concept",
    "config", "document", "service", "table", "endpoint", "pipeline", "schema", "resource",
    "domain", "flow", "step",
    "article", "entity", "topic", "claim", "source",
    "page", "screen", "component", "componentSet", "instance", "token",
)

UA_EDGE_TYPES = (
    "imports", "exports", "contains", "inherits", "implements",
    "calls", "subscribes", "publishes", "middleware",
    "reads_from", "writes_to", "transforms", "validates",
    "depends_on", "tested_by", "configures", "related", "similar_to",
    "deploys", "serves", "provisions", "triggers", "migrates", "documents", "routes", "defines_schema",
    "contains_flow", "flow_step", "cross_domain",
    "cites", "contradicts", "builds_on", "exemplifies", "categorized_under", "authored_by",
    "instance_of", "variant_of", "uses_token",
)

ALIGNMENT_STATUSES = frozenset({"unknown", "partial", "verified", "disagrees"})
ALIGNMENT_BASES = frozenset({
    "stable-id",
    "source-path",
    "contract",
    "executable-evidence",
    "deterministic-finding",
    "candidate-only",
})

FRESHNESS_STATES = frozenset({"absent", "current", "unknown", "stale"})

_ENTITY_ADAPTER_TYPES = {
    "module": "module",
    "package": "module",
    "program": "concept",
    "directory": "file",
    "file": "file",
    "script": "file",
    "class": "class",
    "function": "function",
    "interface": "endpoint",
    "data-store": "table",
    "schema": "schema",
    "configuration": "config",
    "test": "file",
    "test-surface": "file",
    "external-system": "service",
    "concept": "concept",
    "service": "service",
    "resource": "resource",
    "pipeline": "pipeline",
    "endpoint": "endpoint",
    "document": "document",
}

_RELATION_ADAPTER_TYPES = {
    "imports": "imports",
    "exports": "exports",
    "contains": "contains",
    "declares": "contains",
    "calls": "calls",
    "implements": "implements",
    "reads": "reads_from",
    "reads_from": "reads_from",
    "writes": "writes_to",
    "writes_to": "writes_to",
    "transforms": "transforms",
    "validates": "validates",
    "depends-on": "depends_on",
    "depends_on": "depends_on",
    "requires": "depends_on",
    "tested_by": "tested_by",
    "configures": "configures",
    "provides": "serves",
    "exposes": "serves",
    "serves": "serves",
    "triggers": "triggers",
    "documents": "documents",
    "routes": "routes",
    "related": "related",
    "uses": "depends_on",
}

_H1 = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)


def _finding(
    rule_id: str,
    source: str,
    message: str,
    remediation: str,
    *,
    severity: str = "error",
    subject_id: str | None = None,
) -> Finding:
    return Finding(rule_id, severity, source, message, remediation, subject_id=subject_id)


def _ordered(findings: Iterable[Finding]) -> tuple[Finding, ...]:
    return tuple(sorted(findings, key=finding_key))


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _is_string_list(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def _has_string_fields(value: Mapping[str, Any], names: Iterable[str]) -> bool:
    return all(isinstance(value.get(name), str) for name in names)


def _safe_input_file(project_root: str | Path, relative: str, label: str) -> tuple[Path | None, tuple[Finding, ...]]:
    root = Path(project_root).resolve()
    source = relative if isinstance(relative, str) and relative else ".concorde/config.json"
    try:
        safe = safe_relative_path(relative)
    except RepositoryError as error:
        return None, (_finding(
            "CONCORDE-ALIGN-002",
            ".concorde/config.json",
            f"{label} path is unsafe: {error}",
            f"Pass one project-relative non-symlink {label} JSON path.",
        ),)
    candidate = root.joinpath(*PurePosixPath(safe).parts)
    current = root
    for part in PurePosixPath(safe).parts:
        current = current / part
        if current.is_symlink():
            return None, (_finding(
                "CONCORDE-ALIGN-002",
                safe,
                f"{label} path may not contain a symlink.",
                f"Use one real project-relative {label} JSON file.",
            ),)
    try:
        candidate.resolve(strict=False).relative_to(root)
    except ValueError:
        return None, (_finding(
            "CONCORDE-ALIGN-002",
            source,
            f"{label} path escapes the project root.",
            f"Pass one confined project-relative {label} path.",
        ),)
    if not candidate.is_file():
        return None, (_finding(
            "CONCORDE-ALIGN-002",
            safe,
            f"{label} file does not exist.",
            f"Generate or restore the {label} JSON file, then retry.",
        ),)
    return candidate, ()


def _read_json(project_root: str | Path, relative: str, label: str) -> tuple[dict[str, Any] | None, tuple[Finding, ...]]:
    path, findings = _safe_input_file(project_root, relative, label)
    if path is None:
        return None, findings
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        return None, (_finding(
            "CONCORDE-ALIGN-002",
            relative,
            f"Cannot read {label} JSON: {error}",
            f"Provide valid UTF-8 JSON for the {label}.",
        ),)
    if not isinstance(value, dict):
        return None, (_finding(
            "CONCORDE-ALIGN-003",
            relative,
            f"{label} must be a JSON object.",
            f"Regenerate the {label} using its schema-1 object representation.",
        ),)
    return value, ()


def _validate_node(node: Any, index: int, source: str) -> list[Finding]:
    findings: list[Finding] = []
    if not isinstance(node, dict):
        return [_finding(
            "CONCORDE-ALIGN-003", source, f"nodes[{index}] must be an object.",
            "Regenerate the graph with the pinned GraphNode shape.",
        )]
    required_strings = ("id", "type", "name", "summary", "complexity")
    if not _has_string_fields(node, required_strings) or not node.get("id"):
        findings.append(_finding(
            "CONCORDE-ALIGN-003", source,
            f"nodes[{index}] is missing a required string field.",
            "Provide id, type, name, summary, tags, and complexity.",
        ))
        return findings
    if node["type"] not in UA_NODE_TYPES:
        findings.append(_finding(
            "CONCORDE-ALIGN-003", source,
            f"nodes[{index}] uses unsupported pinned node type '{node['type']}'.",
            f"Use one canonical type from Understand Anything revision {UA_REVISION}.",
            subject_id=node["id"],
        ))
    if not _is_string_list(node.get("tags")):
        findings.append(_finding(
            "CONCORDE-ALIGN-003", source, f"nodes[{index}].tags must be a string array.",
            "Regenerate the node with explicit tags, using [] when empty.", subject_id=node["id"],
        ))
    if node["complexity"] not in {"simple", "moderate", "complex"}:
        findings.append(_finding(
            "CONCORDE-ALIGN-003", source,
            f"nodes[{index}] uses unsupported complexity '{node['complexity']}'.",
            "Use simple, moderate, or complex.", subject_id=node["id"],
        ))
    for optional in ("filePath", "languageNotes"):
        if optional in node and not isinstance(node[optional], str):
            findings.append(_finding(
                "CONCORDE-ALIGN-003", source, f"nodes[{index}].{optional} must be a string.",
                "Correct or omit the optional field.", subject_id=node["id"],
            ))
    if "lineRange" in node:
        line_range = node["lineRange"]
        if not isinstance(line_range, list) or len(line_range) != 2 or not all(_is_number(item) for item in line_range):
            findings.append(_finding(
                "CONCORDE-ALIGN-003", source, f"nodes[{index}].lineRange must contain two numbers.",
                "Correct or omit the optional line range.", subject_id=node["id"],
            ))
    for optional in ("domainMeta", "knowledgeMeta", "figmaMeta"):
        if optional in node and not isinstance(node[optional], dict):
            findings.append(_finding(
                "CONCORDE-ALIGN-003", source, f"nodes[{index}].{optional} must be an object.",
                "Correct or omit the optional metadata object.", subject_id=node["id"],
            ))
    return findings


def _validate_edge(edge: Any, index: int, source: str, node_ids: set[str]) -> list[Finding]:
    findings: list[Finding] = []
    if not isinstance(edge, dict):
        return [_finding(
            "CONCORDE-ALIGN-003", source, f"edges[{index}] must be an object.",
            "Regenerate the graph with the pinned GraphEdge shape.",
        )]
    if not _has_string_fields(edge, ("source", "target", "type", "direction")):
        findings.append(_finding(
            "CONCORDE-ALIGN-003", source, f"edges[{index}] is missing a required string field.",
            "Provide source, target, type, direction, and weight.",
        ))
        return findings
    if edge["type"] not in UA_EDGE_TYPES:
        findings.append(_finding(
            "CONCORDE-ALIGN-003", source,
            f"edges[{index}] uses unsupported pinned edge type '{edge['type']}'.",
            f"Use one canonical type from Understand Anything revision {UA_REVISION}.",
        ))
    if edge["direction"] not in {"forward", "backward", "bidirectional"}:
        findings.append(_finding(
            "CONCORDE-ALIGN-003", source,
            f"edges[{index}] uses unsupported direction '{edge['direction']}'.",
            "Use forward, backward, or bidirectional.",
        ))
    weight = edge.get("weight")
    if not _is_number(weight) or not 0 <= weight <= 1:
        findings.append(_finding(
            "CONCORDE-ALIGN-003", source, f"edges[{index}].weight must be a number from 0 to 1.",
            "Correct the weight without coercion.",
        ))
    if "description" in edge and not isinstance(edge["description"], str):
        findings.append(_finding(
            "CONCORDE-ALIGN-003", source, f"edges[{index}].description must be a string.",
            "Correct or omit the optional description.",
        ))
    for endpoint in ("source", "target"):
        if edge[endpoint] not in node_ids:
            findings.append(_finding(
                "CONCORDE-ALIGN-004", source,
                f"edges[{index}].{endpoint} '{edge[endpoint]}' does not resolve to a graph node.",
                "Correct the directed edge endpoint or restore its node.",
                subject_id=edge[endpoint],
            ))
    return findings


def _validate_group(
    value: Any,
    index: int,
    source: str,
    node_ids: set[str],
    *,
    layer: bool,
) -> list[Finding]:
    label = "layers" if layer else "tour"
    required = ("id", "name", "description") if layer else ("title", "description")
    if not isinstance(value, dict):
        return [_finding(
            "CONCORDE-ALIGN-003", source, f"{label}[{index}] must be an object.",
            f"Regenerate the graph with the pinned {label} shape.",
        )]
    findings: list[Finding] = []
    if not _has_string_fields(value, required) or not _is_string_list(value.get("nodeIds")):
        findings.append(_finding(
            "CONCORDE-ALIGN-003", source, f"{label}[{index}] is missing required fields.",
            f"Provide the pinned {label} fields and a nodeIds string array.",
        ))
        return findings
    if not layer and not _is_number(value.get("order")):
        findings.append(_finding(
            "CONCORDE-ALIGN-003", source, f"tour[{index}].order must be a number.",
            "Provide a numeric tour order.",
        ))
    for node_id in value["nodeIds"]:
        if node_id not in node_ids:
            findings.append(_finding(
                "CONCORDE-ALIGN-004", source,
                f"{label}[{index}] node '{node_id}' does not resolve to a graph node.",
                "Correct the grouping reference or restore its node.",
                subject_id=node_id,
            ))
    return findings


def validate_knowledge_graph(
    value: Any,
    source: str,
) -> tuple[dict[str, Any] | None, tuple[Finding, ...]]:
    """Validate the exact pinned formal graph without normalizing or mutating it."""
    if not isinstance(value, dict):
        return None, (_finding(
            "CONCORDE-ALIGN-003", source, "Knowledge graph must be a JSON object.",
            "Generate a graph matching the pinned formal model.",
        ),)
    findings: list[Finding] = []
    if not isinstance(value.get("version"), str) or not value.get("version"):
        findings.append(_finding(
            "CONCORDE-ALIGN-003", source, "Knowledge graph version is missing.",
            "Provide the upstream graph version.",
        ))
    if "kind" in value and value["kind"] not in {"codebase", "knowledge", "design"}:
        findings.append(_finding(
            "CONCORDE-ALIGN-003", source, f"Knowledge graph kind '{value['kind']}' is unsupported.",
            "Use codebase, knowledge, design, or omit kind.",
        ))
    project = value.get("project")
    if not isinstance(project, dict):
        findings.append(_finding(
            "CONCORDE-ALIGN-003", source, "Knowledge graph project metadata is missing.",
            "Provide the pinned ProjectMeta object.",
        ))
    else:
        if not _has_string_fields(project, ("name", "description", "analyzedAt", "gitCommitHash")):
            findings.append(_finding(
                "CONCORDE-ALIGN-003", source, "Knowledge graph project metadata is incomplete.",
                "Provide name, languages, frameworks, description, analyzedAt, and gitCommitHash.",
            ))
        elif not project["gitCommitHash"]:
            findings.append(_finding(
                "CONCORDE-ALIGN-003", source, "Knowledge graph implementation revision is missing.",
                "Generate the graph with a non-empty project.gitCommitHash.",
            ))
        for field in ("languages", "frameworks"):
            if not _is_string_list(project.get(field)):
                findings.append(_finding(
                    "CONCORDE-ALIGN-003", source, f"Knowledge graph project.{field} must be a string array.",
                    f"Provide explicit project.{field}, using [] when empty.",
                ))

    collections: dict[str, list[Any]] = {}
    for name in ("nodes", "edges", "layers", "tour"):
        collection = value.get(name)
        if not isinstance(collection, list):
            findings.append(_finding(
                "CONCORDE-ALIGN-003", source, f"Knowledge graph {name} must be an array.",
                f"Provide explicit {name}, using [] when empty.",
            ))
        else:
            collections[name] = collection

    nodes = collections.get("nodes", [])
    for index, node in enumerate(nodes):
        findings.extend(_validate_node(node, index, source))
    node_ids = [node.get("id") for node in nodes if isinstance(node, dict) and isinstance(node.get("id"), str)]
    duplicates = sorted(identifier for identifier in set(node_ids) if node_ids.count(identifier) > 1)
    for identifier in duplicates:
        findings.append(_finding(
            "CONCORDE-ALIGN-004", source, f"Knowledge graph node ID '{identifier}' is duplicated.",
            "Keep every upstream graph node ID unique.", subject_id=identifier,
        ))
    node_id_set = set(node_ids)
    for index, edge in enumerate(collections.get("edges", [])):
        findings.extend(_validate_edge(edge, index, source, node_id_set))
    layer_ids: list[str] = []
    for index, layer in enumerate(collections.get("layers", [])):
        findings.extend(_validate_group(layer, index, source, node_id_set, layer=True))
        if isinstance(layer, dict) and isinstance(layer.get("id"), str):
            layer_ids.append(layer["id"])
    for identifier in sorted(item for item in set(layer_ids) if layer_ids.count(item) > 1):
        findings.append(_finding(
            "CONCORDE-ALIGN-004", source, f"Knowledge graph layer ID '{identifier}' is duplicated.",
            "Keep every layer ID unique.", subject_id=identifier,
        ))
    for index, step in enumerate(collections.get("tour", [])):
        findings.extend(_validate_group(step, index, source, node_id_set, layer=False))

    ordered = _ordered(findings)
    return (None, ordered) if any(item.severity == "error" for item in ordered) else (value, ordered)


def load_knowledge_graph(
    project_root: str | Path,
    relative: str,
) -> tuple[dict[str, Any] | None, tuple[Finding, ...]]:
    value, findings = _read_json(project_root, relative, "Understand Anything knowledge graph")
    if value is None:
        return None, findings
    return validate_knowledge_graph(value, relative)


def _record_shape_findings(record: Any, index: int, source: str) -> list[Finding]:
    required = {
        "subject_id", "status", "basis", "implementation_node_ids",
        "evidence_node_ids", "finding_ids", "rationale",
    }
    if not isinstance(record, dict):
        return [_finding(
            "CONCORDE-ALIGN-007", source, f"records[{index}] must be an object.",
            "Use one schema-1 alignment record.",
        )]
    if set(record) != required:
        return [_finding(
            "CONCORDE-ALIGN-007", source,
            f"records[{index}] fields differ from the schema-1 alignment record.",
            "Provide only subject_id, status, basis, implementation_node_ids, evidence_node_ids, finding_ids, and rationale.",
        )]
    findings: list[Finding] = []
    if not isinstance(record["subject_id"], str) or not record["subject_id"]:
        findings.append(_finding(
            "CONCORDE-ALIGN-007", source, f"records[{index}].subject_id must be non-empty.",
            "Reference one Concorde stable subject ID.",
        ))
    if record["status"] not in ALIGNMENT_STATUSES:
        findings.append(_finding(
            "CONCORDE-ALIGN-007", source, f"records[{index}] status '{record['status']}' is unsupported.",
            "Use unknown, partial, verified, or disagrees.",
        ))
    if record["basis"] not in ALIGNMENT_BASES:
        findings.append(_finding(
            "CONCORDE-ALIGN-007", source, f"records[{index}] basis '{record['basis']}' is unsupported.",
            "Use one explicit schema-1 evidence basis.",
        ))
    for field in ("implementation_node_ids", "evidence_node_ids", "finding_ids"):
        values = record[field]
        if not _is_string_list(values) or len(values) != len(set(values)) or any(not item for item in values):
            findings.append(_finding(
                "CONCORDE-ALIGN-007", source, f"records[{index}].{field} must contain unique non-empty strings.",
                f"Correct the explicit {field} list, using [] when empty.",
            ))
    if not isinstance(record["rationale"], str) or not record["rationale"].strip():
        findings.append(_finding(
            "CONCORDE-ALIGN-007", source, f"records[{index}].rationale must be non-empty.",
            "Explain the bounded explicit alignment claim.",
        ))
    return findings


def validate_alignment_input(
    value: Any,
    subject_ids: set[str],
    node_ids: set[str],
    source: str,
) -> tuple[dict[str, dict[str, Any]], tuple[Finding, ...]]:
    """Validate explicit claims without interpreting names, paths, or adapter types."""
    if not isinstance(value, dict):
        return {}, (_finding(
            "CONCORDE-ALIGN-007", source, "Alignment input must be a JSON object.",
            "Provide one schema-1 alignment input.",
        ),)
    findings: list[Finding] = []
    if set(value) != {"schema_version", "implementation_revision", "records"}:
        findings.append(_finding(
            "CONCORDE-ALIGN-007", source, "Alignment input fields differ from schema 1.",
            "Provide only schema_version, implementation_revision, and records.",
        ))
    if value.get("schema_version") != ALIGNMENT_SCHEMA_VERSION:
        findings.append(_finding(
            "CONCORDE-ALIGN-007", source,
            f"Alignment input schema version '{value.get('schema_version')}' is unsupported.",
            f"Use schema_version {ALIGNMENT_SCHEMA_VERSION}.",
        ))
    revision = value.get("implementation_revision")
    if not isinstance(revision, str) or not revision:
        findings.append(_finding(
            "CONCORDE-ALIGN-007", source, "Alignment input implementation_revision is missing.",
            "Bind every claim set to the exact graph implementation revision.",
        ))
    raw_records = value.get("records")
    if not isinstance(raw_records, list):
        findings.append(_finding(
            "CONCORDE-ALIGN-007", source, "Alignment input records must be an array.",
            "Provide explicit records, using [] when no claims exist.",
        ))
        raw_records = []
    records: dict[str, dict[str, Any]] = {}
    for index, record in enumerate(raw_records):
        record_findings = _record_shape_findings(record, index, source)
        findings.extend(record_findings)
        if record_findings or not isinstance(record, dict):
            continue
        subject_id = record["subject_id"]
        if subject_id in records:
            findings.append(_finding(
                "CONCORDE-ALIGN-009", source, f"Alignment subject '{subject_id}' is claimed more than once.",
                "Keep one explicit claim per Concorde subject.", subject_id=subject_id,
            ))
        elif subject_id not in subject_ids:
            findings.append(_finding(
                "CONCORDE-ALIGN-009", source, f"Alignment subject '{subject_id}' does not resolve.",
                "Reference one current Profile 7 module, entity, feature, or interface ID.", subject_id=subject_id,
            ))
        else:
            records[subject_id] = record
        for field in ("implementation_node_ids", "evidence_node_ids"):
            for node_id in record[field]:
                if node_id not in node_ids:
                    findings.append(_finding(
                        "CONCORDE-ALIGN-009", source,
                        f"Alignment {field} node '{node_id}' does not resolve in the supplied graph.",
                        "Correct the explicit node reference or regenerate the graph.", subject_id=subject_id,
                    ))
    ordered = _ordered(findings)
    return ({}, ordered) if any(item.severity == "error" for item in ordered) else (records, ordered)


def load_alignment_input(
    project_root: str | Path,
    relative: str,
    subject_ids: set[str],
    node_ids: set[str],
) -> tuple[dict[str, dict[str, Any]], str | None, tuple[Finding, ...]]:
    value, findings = _read_json(project_root, relative, "alignment input")
    if value is None:
        return {}, None, findings
    records, validation_findings = validate_alignment_input(value, subject_ids, node_ids, relative)
    revision = value.get("implementation_revision") if isinstance(value.get("implementation_revision"), str) else None
    return records, revision, _ordered((*findings, *validation_findings))


def qualify_alignment(
    subject_id: str,
    claim: Mapping[str, Any] | None,
    freshness: str,
    implementation_revision: str | None,
    source: str = ".concorde/config.json",
) -> tuple[dict[str, Any], tuple[Finding, ...]]:
    """Compute a conservative effective state for one already validated explicit claim."""
    if freshness not in FRESHNESS_STATES:
        raise ValueError(f"unsupported freshness state: {freshness}")
    if claim is None:
        return {
            "subject_id": subject_id,
            "status": "unknown",
            "requested_status": None,
            "basis": None,
            "implementation_revision": implementation_revision,
            "freshness": freshness,
            "implementation_node_ids": [],
            "evidence_node_ids": [],
            "finding_ids": [],
            "rationale": "No explicit alignment claim was supplied.",
        }, ()

    requested = str(claim["status"])
    basis = str(claim["basis"])
    implementation_nodes = sorted(set(claim["implementation_node_ids"]))
    evidence_nodes = sorted(set(claim["evidence_node_ids"]))
    finding_ids = sorted(set(claim["finding_ids"]))
    effective = requested
    reason: str | None = None
    if freshness != "current":
        effective = "unknown"
        reason = f"Evidence freshness is {freshness}."
    elif basis == "candidate-only":
        effective = "unknown"
        reason = "Candidate-only mapping cannot establish agreement or disagreement."
    elif requested in {"partial", "verified"} and not implementation_nodes:
        effective = "unknown"
        reason = f"Requested {requested} status has no implementation node."
    elif requested == "verified" and (basis != "executable-evidence" or not evidence_nodes):
        effective = "unknown"
        reason = "Verified status requires executable-evidence basis and at least one evidence node."
    elif requested == "disagrees" and (basis != "deterministic-finding" or not finding_ids):
        effective = "unknown"
        reason = "Disagrees status requires deterministic-finding basis and at least one finding ID."

    findings: tuple[Finding, ...] = ()
    rationale = str(claim["rationale"])
    if reason:
        rationale = f"{rationale} Effective status is unknown: {reason}"
        findings = (_finding(
            "CONCORDE-ALIGN-010",
            source,
            f"Alignment claim for '{subject_id}' was reduced from {requested} to unknown: {reason}",
            "Refresh or strengthen the explicit evidence before claiming agreement or disagreement.",
            severity="warning",
            subject_id=subject_id,
        ),)
    return {
        "subject_id": subject_id,
        "status": effective,
        "requested_status": requested,
        "basis": basis,
        "implementation_revision": implementation_revision,
        "freshness": freshness,
        "implementation_node_ids": implementation_nodes,
        "evidence_node_ids": evidence_nodes,
        "finding_ids": finding_ids,
        "rationale": rationale,
    }, findings


def _title(body: str, fallback: str) -> str:
    match = _H1.search(body)
    if not match:
        return fallback
    return re.sub(r"^(?:Architecture|Feature Design):\s*", "", match.group(1)).strip()


def _subject(
    identifier: str,
    kind: str,
    profile_kind: str,
    adapter_type: str,
    name: str,
    description: str,
    module_id: str | None,
    feature_id: str | None,
    declaring_feature_ids: Iterable[str],
    source_paths: Iterable[str],
) -> dict[str, Any]:
    paths = sorted(set(source_paths))
    return {
        "id": identifier,
        "kind": kind,
        "profile_kind": profile_kind,
        "adapter_type": adapter_type if adapter_type in UA_NODE_TYPES else "concept",
        "name": name,
        "description": " ".join(description.split()),
        "module_id": module_id,
        "feature_id": feature_id,
        "declaring_feature_ids": sorted(set(declaring_feature_ids)),
        "source_path": paths[0],
        "source_paths": paths,
    }


def _all_subjects(package: ArchitecturePackage) -> dict[str, dict[str, Any]]:
    subjects: dict[str, dict[str, Any]] = {}
    for identifier, module in package.modules.items():
        source = package.by_id[identifier][0]
        subjects[identifier] = _subject(
            identifier, "module", "module", "module", _title(source.body, identifier),
            module.responsibility, identifier, None, (), (source.path,),
        )
    for identifier, entity in package.entities.items():
        subjects[identifier] = _subject(
            identifier, "entity", entity.entity_type,
            _ENTITY_ADAPTER_TYPES.get(entity.entity_type, "concept"),
            identifier.rsplit(".", 1)[-1], entity.definition, entity.owner, None, (), (entity.source,),
        )
    for identifier, feature in package.features.items():
        source = package.by_id[identifier][0]
        summary = feature_summary(package, source)
        subjects[identifier] = _subject(
            identifier, "feature", "feature", "concept", summary["title"], feature.outcome,
            feature.module, identifier, (), (feature.path,),
        )

    required_by_id: dict[str, list[Any]] = defaultdict(list)
    for declaration in package.required_interface_declarations:
        required_by_id[declaration.identifier].append(declaration)
    interface_ids = sorted(set(package.interfaces) | set(required_by_id))
    for identifier in interface_ids:
        provided = package.interfaces.get(identifier)
        required = required_by_id.get(identifier, [])
        if provided is not None:
            owner_feature = package.features.get(provided.owner)
            module_id = owner_feature.module if owner_feature else None
            feature_id = provided.owner
            source_paths = [provided.source, *(item.source for item in required)]
            description = provided.direction or provided.outputs
        else:
            first = sorted(required, key=lambda item: (item.source, item.owner))[0]
            owner_feature = package.features.get(first.owner)
            module_id = owner_feature.module if owner_feature else None
            feature_id = None
            source_paths = [item.source for item in required]
            description = first.direction or first.outputs
        subjects[identifier] = _subject(
            identifier, "interface", "interface", "endpoint", identifier, description,
            module_id, feature_id, (item.owner for item in required), source_paths,
        )
    return subjects


def _target_subject_ids(
    package: ArchitecturePackage,
    subjects: Mapping[str, Mapping[str, Any]],
    target: str,
) -> set[str]:
    selected: set[str] = {target}
    if target in package.modules:
        module = package.modules[target]
        selected.update(module.modules)
        selected.update(module.entities)
        selected.update(module.features)
        feature_ids = set(module.features)
        for interface_id, subject in subjects.items():
            if subject["kind"] != "interface":
                continue
            owners = {subject.get("feature_id"), *subject.get("declaring_feature_ids", [])}
            if feature_ids.intersection(item for item in owners if item):
                selected.add(interface_id)
    elif target in package.features:
        feature = package.features[target]
        selected.add(feature.module)
        selected.update(feature.related_features)
        selected.update(feature.architecture_zoom)
        selected.update(feature.provided_interfaces)
        selected.update(feature.required_interfaces)
    elif target in package.entities:
        entity = package.entities[target]
        selected.add(entity.owner)
        for relation in package.relationships:
            if target in {relation.source_entity, relation.target_entity}:
                selected.update((relation.source_entity, relation.target_entity))
        for feature in package.features.values():
            if target in feature.architecture_zoom:
                selected.add(feature.identifier)
                selected.update(feature.provided_interfaces)
    elif target in subjects and subjects[target]["kind"] == "interface":
        subject = subjects[target]
        feature_ids = {
            item for item in (subject.get("feature_id"), *subject.get("declaring_feature_ids", [])) if item
        }
        selected.update(feature_ids)
        for feature_id in feature_ids:
            feature = package.features.get(feature_id)
            if feature:
                selected.add(feature.module)
        interfaces = []
        if target in package.interfaces:
            interfaces.append(package.interfaces[target])
        interfaces.extend(item for item in package.required_interface_declarations if item.identifier == target)
        for interface in interfaces:
            selected.update(interface.implementing_entities)
    else:
        raise KeyError(target)
    return {identifier for identifier in selected if identifier in subjects}


def _adapter_edge_type(predicate: str) -> str:
    return _RELATION_ADAPTER_TYPES.get(predicate.casefold().replace(" ", "_"), "related")


def _relation(
    source_id: str,
    predicate: str,
    target_id: str,
    description: str,
    interface_id: str | None = None,
) -> dict[str, Any]:
    return {
        "source_id": source_id,
        "target_id": target_id,
        "predicate": predicate,
        "adapter_edge_type": _adapter_edge_type(predicate),
        "description": description,
        "interface_id": interface_id,
    }


def _all_relations(package: ArchitecturePackage) -> list[dict[str, Any]]:
    relations = [
        _relation(
            item.source_entity, item.predicate, item.target_entity, item.description, item.interface
        )
        for item in package.relationships
    ]
    for module in package.modules.values():
        relations.extend(
            _relation(module.identifier, "contains", child, "Module contains one immediate child module.")
            for child in module.modules
        )
        relations.extend(
            _relation(module.identifier, "declares", entity, "Module declares one architecture entity.")
            for entity in module.entities
        )
        relations.extend(
            _relation(module.identifier, "provides", feature, "Module provides one level-local feature.")
            for feature in module.features
        )
    for feature in package.features.values():
        relations.extend(
            _relation(feature.identifier, "provides", interface, "Feature provides this interface.", interface)
            for interface in feature.provided_interfaces
        )
        relations.extend(
            _relation(feature.identifier, "requires", interface, "Feature requires this interface.", interface)
            for interface in feature.required_interfaces
        )
        relations.extend(
            _relation(feature.identifier, "uses", entity, "Feature Architecture Zoom uses this entity.")
            for entity in feature.architecture_zoom
        )
        relations.extend(
            _relation(
                feature.identifier, relation.relation, relation.target,
                "Feature declares a bounded related feature.",
            )
            for relation in feature.relations
        )
    unique = {
        (
            item["source_id"], item["predicate"], item["target_id"], item["description"],
            item["interface_id"], item["adapter_edge_type"],
        ): item
        for item in relations
    }
    return [unique[key] for key in sorted(unique, key=lambda item: tuple("" if value is None else value for value in item))]


def project_specification(package: ArchitecturePackage, target: str) -> dict[str, Any]:
    """Project one bounded Profile 7 target without changing its semantic identities."""
    subjects = _all_subjects(package)
    selected_ids = _target_subject_ids(package, subjects, target)
    selected_subjects = [subjects[identifier] for identifier in sorted(selected_ids)]
    relationships = [
        item for item in _all_relations(package)
        if item["source_id"] in selected_ids and item["target_id"] in selected_ids
    ]
    selected_interfaces = {item["id"] for item in selected_subjects if item["kind"] == "interface"}
    selected_modules = {item["id"] for item in selected_subjects if item["kind"] == "module"}
    interactions = []
    for identifier, interaction in sorted(package.interactions.items()):
        if interaction.owner not in selected_modules:
            continue
        if interaction.interfaces and not selected_interfaces.intersection(interaction.interfaces):
            continue
        interactions.append({
            "id": identifier,
            "trigger": interaction.trigger,
            "steps": list(interaction.steps),
            "result": interaction.result,
            "interfaces": list(interaction.interfaces),
            "source_path": interaction.source,
        })
    return {
        "subjects": selected_subjects,
        "relationships": relationships,
        "interactions": interactions,
    }


def _specification_digest(package: ArchitecturePackage) -> str:
    paths = [source.path for source in package.sources]
    paths.extend(package.diagrams)
    return digest_sources(package.project_root, paths)


def _alignment_summary(records: Iterable[Mapping[str, Any]]) -> dict[str, int]:
    summary = {status: 0 for status in ("unknown", "partial", "verified", "disagrees")}
    for record in records:
        summary[str(record["status"])] += 1
    return summary


def _subject_artifacts(projection: Mapping[str, Any]) -> tuple[str, ...]:
    paths: set[str] = set()
    for subject in projection["subjects"]:
        paths.update(subject["source_paths"])
    for interaction in projection["interactions"]:
        paths.add(interaction["source_path"])
    return tuple(sorted(paths))


def _safe_display_path(relative: str | None) -> str | None:
    if not isinstance(relative, str) or not relative:
        return None
    try:
        return safe_relative_path(relative)
    except RepositoryError:
        return None


def _freshness(
    graph_revision: str,
    alignment_revision: str | None,
    expected_revision: str | None,
    alignment_supplied: bool,
    source: str,
) -> tuple[str, tuple[Finding, ...]]:
    if expected_revision is None:
        return "unknown", ()
    revisions = [graph_revision, expected_revision]
    if alignment_supplied:
        revisions.append(alignment_revision or "")
    if len(set(revisions)) == 1:
        return "current", ()
    observed = ", ".join(repr(item) for item in revisions)
    return "stale", (_finding(
        "CONCORDE-ALIGN-008",
        source,
        f"Graph, alignment, and expected implementation revisions do not agree: {observed}.",
        "Regenerate the graph/sidecar at the expected revision or omit the stale claim.",
        severity="warning",
    ),)


def _bounded_implementation(
    graph: Mapping[str, Any] | None,
    records: Iterable[Mapping[str, Any]],
    query: str | None,
) -> dict[str, Any]:
    if graph is None:
        return {
            "project": None,
            "nodes": [],
            "edges": [],
            "layers": [],
            "tour": [],
            "counts": {
                "total_nodes": 0,
                "returned_nodes": 0,
                "total_edges": 0,
                "returned_edges": 0,
            },
        }
    selected_ids: set[str] = set()
    for record in records:
        selected_ids.update(record["implementation_node_ids"])
        selected_ids.update(record["evidence_node_ids"])
    normalized_query = query.casefold().strip() if isinstance(query, str) else ""
    if normalized_query:
        for node in graph["nodes"]:
            searchable = " ".join([
                str(node.get("id", "")),
                str(node.get("type", "")),
                str(node.get("name", "")),
                str(node.get("filePath", "")),
                str(node.get("summary", "")),
                " ".join(str(item) for item in node.get("tags", [])),
            ]).casefold()
            if normalized_query in searchable:
                selected_ids.add(node["id"])
    one_hop_ids = set(selected_ids)
    for edge in graph["edges"]:
        if edge["source"] in selected_ids or edge["target"] in selected_ids:
            one_hop_ids.update((edge["source"], edge["target"]))
    nodes = sorted(
        (node for node in graph["nodes"] if node["id"] in one_hop_ids),
        key=lambda item: item["id"],
    )
    returned_ids = {node["id"] for node in nodes}
    edges = sorted(
        (
            edge for edge in graph["edges"]
            if edge["source"] in returned_ids and edge["target"] in returned_ids
        ),
        key=lambda item: (
            item["source"], item["target"], item["type"], item["direction"],
            str(item.get("description", "")), item["weight"],
        ),
    )
    layers = []
    for layer in sorted(graph["layers"], key=lambda item: item["id"]):
        node_ids = [node_id for node_id in layer["nodeIds"] if node_id in returned_ids]
        if node_ids:
            layers.append({**layer, "nodeIds": node_ids})
    tour = []
    for step in sorted(graph["tour"], key=lambda item: (item["order"], item["title"], item["description"])):
        node_ids = [node_id for node_id in step["nodeIds"] if node_id in returned_ids]
        if node_ids:
            tour.append({**step, "nodeIds": node_ids})
    return {
        "project": graph["project"],
        "nodes": nodes,
        "edges": edges,
        "layers": layers,
        "tour": tour,
        "counts": {
            "total_nodes": len(graph["nodes"]),
            "returned_nodes": len(nodes),
            "total_edges": len(graph["edges"]),
            "returned_edges": len(edges),
        },
    }


def _subject_matches(subject: Mapping[str, Any], query: str) -> bool:
    searchable = " ".join([
        str(subject["id"]),
        str(subject["profile_kind"]),
        str(subject["adapter_type"]),
        str(subject["name"]),
        str(subject["description"]),
        " ".join(subject["source_paths"]),
    ]).casefold()
    return query in searchable


def _interaction_matches(interaction: Mapping[str, Any], query: str) -> bool:
    searchable = " ".join([
        str(interaction["id"]),
        str(interaction["trigger"]),
        " ".join(interaction["steps"]),
        str(interaction["result"]),
        " ".join(interaction["interfaces"]),
        str(interaction["source_path"]),
    ]).casefold()
    return query in searchable


def _filter_projection(
    specification: Mapping[str, Any],
    records: Iterable[Mapping[str, Any]],
    query: str | None,
    statuses: tuple[str, ...],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    normalized_query = query.casefold().strip() if isinstance(query, str) else ""
    by_subject = {record["subject_id"]: dict(record) for record in records}
    subjects = []
    for subject in specification["subjects"]:
        record = by_subject[subject["id"]]
        if normalized_query and not _subject_matches(subject, normalized_query):
            continue
        if statuses and record["status"] not in statuses:
            continue
        subjects.append(subject)
    selected_ids = {subject["id"] for subject in subjects}
    relationships = [
        relation for relation in specification["relationships"]
        if relation["source_id"] in selected_ids and relation["target_id"] in selected_ids
    ]
    selected_paths = {
        path for subject in subjects for path in subject["source_paths"]
    }
    interactions = []
    for interaction in specification["interactions"]:
        if interaction["source_path"] not in selected_paths:
            continue
        if normalized_query and not _interaction_matches(interaction, normalized_query):
            continue
        interactions.append(interaction)
    filtered_records = [by_subject[subject["id"]] for subject in subjects]
    return {
        "subjects": subjects,
        "relationships": relationships,
        "interactions": interactions,
    }, filtered_records


def explore_alignment(
    project_root: str | Path,
    target: str | None = None,
    *,
    graph_path: str | None = None,
    alignment_path: str | None = None,
    expected_revision: str | None = None,
    query: str | None = None,
    statuses: Iterable[str] = (),
) -> ToolResult:
    """Return one deterministic read-only specification/alignment exploration result."""
    from .validate import validate_project

    root = Path(project_root).resolve()
    validation = validate_project(root)
    tool_target = target or "."
    if validation.status != "success":
        return ToolResult(
            "explore",
            tool_target,
            "invalid",
            validation.artifacts,
            validation.findings,
            {"source_digest": validation.result.get("source_digest")},
        )
    try:
        package = ProjectRepository(root).load()
    except RepositoryError as error:
        return ToolResult(
            "explore",
            tool_target,
            "invalid",
            findings=(_finding(
                "CONCORDE-ALIGN-001",
                ".concorde/config.json",
                f"Cannot load the validated Profile 7 package: {error}",
                "Correct project configuration and retry.",
            ),),
        )
    resolved_target = target or package.root_module_id
    requested_statuses = tuple(sorted(set(statuses)))
    invalid_statuses = sorted(set(requested_statuses) - ALIGNMENT_STATUSES)
    if invalid_statuses:
        return ToolResult(
            "explore",
            resolved_target,
            "invalid",
            findings=(_finding(
                "CONCORDE-ALIGN-001",
                ".concorde/config.json",
                "Unsupported alignment status filter: " + ", ".join(invalid_statuses) + ".",
                "Filter by unknown, partial, verified, or disagrees.",
            ),),
        )
    try:
        specification = project_specification(package, resolved_target)
    except KeyError:
        return ToolResult(
            "explore",
            resolved_target,
            "invalid",
            tuple(source.path for source in package.sources),
            (_finding(
                "CONCORDE-ALIGN-001",
                ".concorde/config.json",
                f"Alignment target '{resolved_target}' does not resolve to one module, entity, feature, or interface.",
                "Pass one current Profile 7 stable subject ID.",
                subject_id=resolved_target,
            ),),
            {"source_digest": _specification_digest(package)},
        )

    source_digest = _specification_digest(package)
    findings: list[Finding] = []
    graph: dict[str, Any] | None = None
    claims: dict[str, dict[str, Any]] = {}
    graph_revision: str | None = None
    alignment_revision: str | None = None
    freshness = "absent"
    if graph_path is None:
        if alignment_path is None:
            findings.append(_finding(
                "CONCORDE-ALIGN-005",
                ".concorde/config.json",
                "No Understand Anything graph was supplied; implementation alignment remains unknown.",
                "Pass --graph and an explicit --alignment sidecar to qualify implementation evidence.",
                severity="info",
                subject_id=resolved_target,
            ))
        else:
            findings.append(_finding(
                "CONCORDE-ALIGN-006",
                _safe_display_path(alignment_path) or ".concorde/config.json",
                "An alignment sidecar cannot be evaluated without an Understand Anything graph.",
                "Pass the graph that owns every referenced implementation/evidence node.",
            ))
    else:
        graph, graph_findings = load_knowledge_graph(root, graph_path)
        findings.extend(graph_findings)
        freshness = "unknown"
        if graph is not None:
            graph_revision = graph["project"]["gitCommitHash"]
            if alignment_path is None:
                findings.append(_finding(
                    "CONCORDE-ALIGN-006",
                    _safe_display_path(graph_path) or ".concorde/config.json",
                    "No explicit alignment sidecar was supplied; implementation subjects remain unmapped.",
                    "Pass --alignment to qualify explicit specification-to-implementation claims.",
                    severity="info",
                    subject_id=resolved_target,
                ))
            else:
                all_subject_ids = set(_all_subjects(package))
                node_ids = {node["id"] for node in graph["nodes"]}
                claims, alignment_revision, alignment_findings = load_alignment_input(
                    root, alignment_path, all_subject_ids, node_ids
                )
                findings.extend(alignment_findings)
            freshness, freshness_findings = _freshness(
                graph_revision,
                alignment_revision,
                expected_revision,
                alignment_path is not None,
                _safe_display_path(alignment_path or graph_path) or ".concorde/config.json",
            )
            findings.extend(freshness_findings)

    record_revision = alignment_revision or graph_revision
    records: list[dict[str, Any]] = []
    for subject in specification["subjects"]:
        record, qualification_findings = qualify_alignment(
            subject["id"],
            claims.get(subject["id"]),
            freshness,
            record_revision,
            _safe_display_path(alignment_path) or ".concorde/config.json",
        )
        records.append(record)
        findings.extend(qualification_findings)
    specification, records = _filter_projection(
        specification, records, query, requested_statuses
    )

    result = {
        "alignment_schema_version": ALIGNMENT_SCHEMA_VERSION,
        "source_profile": package.profile_version,
        "source_digest": source_digest,
        "target": resolved_target,
        "query": query,
        "status_filter": list(requested_statuses),
        "provenance": {
            "concorde_source_digest": source_digest,
            "upstream_repository": UA_REPOSITORY,
            "upstream_revision": UA_REVISION,
            "graph_path": _safe_display_path(graph_path),
            "graph_version": graph.get("version") if graph is not None else None,
            "graph_kind": graph.get("kind") if graph is not None else None,
            "analyzed_at": graph["project"].get("analyzedAt") if graph is not None else None,
            "implementation_revision": graph_revision,
            "expected_revision": expected_revision,
            "freshness": freshness,
        },
        "specification": specification,
        "implementation": _bounded_implementation(graph, records, query),
        "alignment": {
            "records": records,
            "summary": _alignment_summary(records),
        },
    }
    status = "invalid" if any(item.severity == "error" for item in findings) else "success"
    artifacts = list(_subject_artifacts(specification))
    for relative in (graph_path, alignment_path):
        if isinstance(relative, str) and relative:
            try:
                artifacts.append(safe_relative_path(relative))
            except RepositoryError:
                pass
    return ToolResult(
        "explore",
        resolved_target,
        status,
        tuple(sorted(set(artifacts))),
        _ordered(findings),
        result,
    )
