"""Deterministic checks establish structure/contract evidence, never semantic completeness."""
from __future__ import annotations

import json
import posixpath
import re
from collections import Counter
from pathlib import Path

from ..model import Finding, ToolResult
from .repository import SpecError, SpecRepository, digest, read_file
from ..host.typed_data import safe_path


def ontology_findings(repository: SpecRepository, target_id: str | None = None) -> tuple[Finding, ...]:
    findings = []
    for target in repository.targets.values():
        if target.kind != "domain" or target_id is not None and target.id != target_id:
            continue
        try:
            main = repository.document(target.primary_document)
            prose = []
            fence = None
            for line in main.body.splitlines():
                marker = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
                if marker:
                    token = marker.group(1)
                    if fence is None:
                        fence = token
                    elif token[0] == fence[0] and len(token) >= len(fence) and not line[marker.end():].strip():
                        fence = None
                    continue
                if fence is None:
                    prose.append(line)
            if not re.search(r"^## Ontology\s*$", "\n".join(prose), re.M):
                raise SpecError("Domain main Spec requires an Ontology section; content completeness still needs review")
        except (ValueError, OSError, KeyError, TypeError) as problem:
            findings.append(Finding("CONCORDE-ONTOLOGY-001", "error", target.primary_document,
                str(problem), "Define the Domain's Ontology in its registered local main Spec.", subject_id=target.id))
    return tuple(findings)


def diagram_findings(repository: SpecRepository, target_id: str | None = None) -> tuple[Finding, ...]:
    findings = []
    for target in repository.targets.values():
        if target_id is not None and target.id != target_id:
            continue
        for declaration in target.diagrams:
            path = declaration["source"]
            try:
                raw = repository.document_overrides.get(path)
                if raw is None:
                    raw = read_file(repository.root, path)
                diagram = json.loads(raw)
                if not isinstance(diagram, dict) or not isinstance(diagram.get("meta"), dict):
                    raise SpecError("diagram must be an object with metadata")
                if diagram.get("diagram_type") != declaration["kind"] or diagram["meta"].get("title") != declaration["title"]:
                    raise SpecError("declared diagram kind/title differs from its source")
                if declaration.get("recipe") == "system-overview" and diagram["meta"].get("quality_profile") != "showcase":
                    raise SpecError("System overview sources must request Archify showcase validation")
                output = diagram["meta"].get("output")
                if not isinstance(output, str) or not output:
                    raise SpecError("diagram metadata must name its generated HTML output")
                output = safe_path(posixpath.normpath(posixpath.join(posixpath.dirname(path), output)))
                if not output.startswith("generated/diagrams/") or not output.endswith(".html"):
                    raise SpecError("diagram output must be HTML beneath generated/diagrams/")
            except (ValueError, OSError, KeyError, TypeError) as problem:
                findings.append(Finding("CONCORDE-DIAGRAM-001", "error", path, str(problem),
                    "Reconcile the registered diagram source, recipe and generated output.", subject_id=target.id))
    return tuple(findings)


def document_context_findings(repository: SpecRepository) -> tuple[Finding, ...]:
    """Validate physical Spec truth identities, memberships, and main visibility."""

    findings = []
    identifiers: dict[str, str] = {}
    reserved_ids = set(repository.targets) | set(repository.focus)
    for path in repository.document_targets:
        try:
            document = repository.document(path)
        except (ValueError, OSError, KeyError, TypeError) as problem:
            findings.append(Finding(
                "CONCORDE-DOCUMENT-001", "error", path,
                f"invalid Spec document context declaration: {problem}",
                "Add exactly one valid concorde-document block whose target set matches the registry.",
            ))
            continue
        previous = identifiers.get(document.document_id)
        if document.document_id in reserved_ids:
            findings.append(Finding(
                "CONCORDE-DOCUMENT-002", "error", path,
                f"document identity {document.document_id} collides with a target, Feature, or API",
                "Use one globally unique stable document ID.",
                subject_id=document.document_id,
            ))
        elif previous is not None and previous != path:
            findings.append(Finding(
                "CONCORDE-DOCUMENT-002", "error", path,
                f"document identity {document.document_id} is also declared by {previous}",
                "Give every physical Spec truth one globally unique stable document ID.",
                subject_id=document.document_id,
            ))
        else:
            identifiers[document.document_id] = path
    return tuple(findings)


def domain_participant_findings(repository: SpecRepository,
                                domain_id: str | None = None) -> tuple[Finding, ...]:
    """Compare machine-readable Domain routing declarations with registry scope participation."""

    findings = []
    domains = [target for target in repository.targets.values()
               if target.kind == "domain" and (domain_id is None or target.id == domain_id)]

    def finding(rule_id: str, domain, source: str, message: str, remediation: str):
        findings.append(Finding(rule_id, "error", source, message, remediation,
                                subject_id=domain.id))

    def participates_at_or_below(component, domain) -> bool:
        for scope_id in component.participates_in:
            current = repository.targets[scope_id]
            while True:
                if current.id == domain.id:
                    return True
                if current.scope_parent is None:
                    break
                current = repository.targets[current.scope_parent]
        return False

    for domain in domains:
        try:
            declarations = repository.participants(domain)
        except (ValueError, OSError, KeyError, TypeError) as problem:
            finding(
                "CONCORDE-PARTICIPANT-001",
                domain,
                domain.primary_document,
                f"invalid Domain participant declaration: {problem}",
                "Repair the concorde-participants JSON block using the exact declared fields.",
            )
            continue
        by_target: dict[str, list[dict]] = {}
        for declaration in declarations:
            by_target.setdefault(declaration["target_id"], []).append(declaration)
        for target_id, items in by_target.items():
            if len(items) > 1:
                finding(
                    "CONCORDE-PARTICIPANT-002",
                    domain,
                    items[1]["source"],
                    f"Domain {domain.id} declares participant {target_id} more than once",
                    "Keep exactly one local declaration for this participant in the Domain collection.",
                )
            component = repository.targets.get(target_id)
            if component is None:
                finding(
                    "CONCORDE-PARTICIPANT-003",
                    domain,
                    items[0]["source"],
                    f"Domain {domain.id} declares unknown participant {target_id}",
                    "Register the component through an accepted topology change or remove the declaration.",
                )
                continue
            if (component.kind != items[0]["kind"] or component.kind == "domain"
                    or not participates_at_or_below(component, domain)):
                finding(
                    "CONCORDE-PARTICIPANT-003",
                    domain,
                    items[0]["source"],
                    f"Domain {domain.id} participant {target_id} has the wrong kind or no scope participation",
                    "Match the registered component kind and a direct or nested participates_in relation.",
                )
        required = sorted(component.id for component in repository.targets.values()
                          if domain.id in component.participates_in)
        for target_id in required:
            if target_id not in by_target:
                finding(
                    "CONCORDE-PARTICIPANT-004",
                    domain,
                    domain.primary_document,
                    f"Domain {domain.id} is missing its direct participant {target_id}",
                    "Declare its stable target ID, kind, Domain-local responsibility, selection condition, "
                    "and relied-upon promises in a concorde-participants block.",
                )
    return tuple(findings)


def validate_repository(root: str | Path, target_id: str | None = None,
                        package_root: Path | None = None, *, registry_bytes: bytes | None = None,
                        document_overrides: dict[str, bytes] | None = None) -> ToolResult:
    findings = []
    artifacts = []
    inputs = []
    def error(code, path, message):
        findings.append(Finding(code, "error", path, message, "Reconcile the registered Spec and retry."))
    try:
        repository = SpecRepository(root, package_root, registry_bytes=registry_bytes,
                                    document_overrides=document_overrides)
        if target_id and target_id != ".":
            repository.select(target_id)
        provided = {}
        required = []
        for target in repository.targets.values():
            try:
                documents = repository.documents(target)
                artifacts.extend(doc.path for doc in documents)
                inputs.extend((doc.path, doc.digest) for doc in documents)
                for focus in (*target.features, *target.apis):
                    body = next(doc.body for doc in documents if doc.path == focus["document"])
                    if focus["id"] not in body:
                        error("CONCORDE-FOCUS-001", focus["document"], f"missing local definition for {focus['id']}")
                for contract in repository.contracts(target):
                    key = (contract["id"], contract["version"])
                    if contract["role"] == "provided":
                        if key in provided:
                            error("CONCORDE-CONTRACT-001", contract["source"], f"duplicate provider for {key}")
                        provided[key] = contract
                    else:
                        required.append(contract)
                for declaration in target.diagrams:
                    raw = repository.document_overrides.get(declaration["source"])
                    if raw is None:
                        raw = read_file(repository.root, declaration["source"])
                    inputs.append((declaration["source"], digest(raw)))
                    artifacts.append(declaration["source"])
            except (ValueError, OSError) as problem:
                error("CONCORDE-SPEC-001", target.primary_document, str(problem))
        for contract in required:
            if contract["peer"].startswith("external:"):
                continue
            provider = provided.get((contract["id"], contract["version"]))
            if not provider or provider["owner"] != contract["peer"]:
                error("CONCORDE-CONTRACT-002", contract["source"], f"missing named provider for {contract['id']}")
            elif provider["schema"] != contract["schema"]:
                # The first version admits exact shared wire schemas, with independent perspective prose.
                error("CONCORDE-CONTRACT-003", contract["source"], f"incompatible shared wire schema for {contract['id']}")
        findings.extend(document_context_findings(repository))
        findings.extend(ontology_findings(repository))
        findings.extend(diagram_findings(repository))
        findings.extend(domain_participant_findings(repository))
        if (repository.root/".concorde/reflections").exists():
            from ..reflections.scoped_triage import queue_module
            queue=queue_module(repository.package_root)
            _,index,parsed,_,raw=queue._load_reflections(repository.root,required=True)
            # Reflection parsing is independent of the candidate overlay, but attribution must be
            # checked against the repository instance being validated rather than the on-disk
            # registry that the compatibility queue helper happens to load.
            ids = {target.id for target in repository.targets.values()}
            ids.update(repository.focus)
            for entry in parsed.entries:
                if entry.feature not in ids:
                    error("CONCORDE-REFLECT-004",entry.path,"Reflection attribution must be a registered target, Feature or API")
            inputs.extend((p,digest(b)) for p,b in raw.items())
            inputs.append(("reflection-index",digest(index)))
        if (repository.root/"concorde.json").is_file():
            from ..host.package_validation import validate_package
            findings.extend(validate_package(repository.root))
        inputs.append((".concorde/config.json",digest(read_file(repository.root,".concorde/config.json"))))
        inputs.append((repository.registry_path, digest(repository.registry_bytes)))
        inputs.append(("protocol", repository.config["protocol"]["digest"]))
    except (ValueError, OSError, KeyError, TypeError) as problem:
        error("CONCORDE-SOURCE-008", ".concorde/config.json", str(problem))
    counts = Counter(f.severity for f in findings)
    return ToolResult("validate", target_id or ".", "invalid" if findings else "success",
        tuple(sorted(set(artifacts))), tuple(findings), {"summary": {
            "errors": counts["error"], "warnings": 0, "infos": 0}, "source_digest": digest(sorted(inputs)),
            "claims": ["registry structure", "Spec document identity/membership/main visibility",
                       "local focus definitions", "contract examples", "shared wire schema equality",
                       "Domain participant routing declarations", "Domain ontology.md main Spec and System overview declarations"],
            "semantic_completeness": "not_proven"})
