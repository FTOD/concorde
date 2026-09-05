"""Deterministic checks establish structure/contract evidence, never semantic completeness."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from ..model import Finding, ToolResult
from .repository import SpecError, SpecRepository, digest, read_file


def validate_repository(root: str | Path, target_id: str | None = None,
                        package_root: Path | None = None) -> ToolResult:
    findings = []
    artifacts = []
    inputs = []
    def error(code, path, message):
        findings.append(Finding(code, "error", path, message, "Reconcile the registered Spec and retry."))
    try:
        repository = SpecRepository(root, package_root)
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
                    if set(declaration) != {"source", "kind", "title"}:
                        raise SpecError("diagram declarations require source, kind, title")
                    raw = read_file(repository.root, declaration["source"])
                    diagram=json.loads(raw)
                    if diagram.get("diagram_type") != declaration["kind"] or diagram.get("meta",{}).get("title") != declaration["title"]:
                        raise SpecError("declared diagram kind/title differs from its source")
                    inputs.append((declaration["source"], digest(raw)))
                    artifacts.append(declaration["source"])
            except (ValueError, OSError) as problem:
                error("CONCORDE-SPEC-001", target.documents[0], str(problem))
        for contract in required:
            if contract["peer"].startswith("external:"):
                continue
            provider = provided.get((contract["id"], contract["version"]))
            if not provider or provider["owner"] != contract["peer"]:
                error("CONCORDE-CONTRACT-002", contract["source"], f"missing named provider for {contract['id']}")
            elif provider["schema"] != contract["schema"]:
                # The first version admits exact shared wire schemas, with independent perspective prose.
                error("CONCORDE-CONTRACT-003", contract["source"], f"incompatible shared wire schema for {contract['id']}")
        if (repository.root/".concorde/reflections").exists():
            from ..reflections.scoped_triage import queue_module
            queue=queue_module(repository.package_root)
            _,index,parsed,ids,raw=queue._load_reflections(repository.root,required=True)
            for entry in parsed.entries:
                if entry.feature not in ids:
                    error("CONCORDE-REFLECT-004",entry.path,"Reflection attribution must be a registered target, Feature or API")
            inputs.extend((p,digest(b)) for p,b in raw.items())
            inputs.append(("reflection-index",digest(index)))
        if (repository.root/"concorde.json").is_file():
            from ..capabilities.profile8_validation import validate_package
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
            "claims": ["registry structure", "local focus definitions", "contract examples", "shared wire schema equality"],
            "semantic_completeness": "not_proven"})
