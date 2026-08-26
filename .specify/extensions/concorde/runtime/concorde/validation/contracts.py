"""Contract representation and deterministic example conformance adapters."""

from __future__ import annotations

import json
import tomllib
from pathlib import Path
from typing import Any

from ..frontmatter import FrontMatterError, parse_document
from ..model import Finding, SourceDocument
from ..repository import ProjectRepository, RepositoryError, safe_relative_path


def _matches_schema(value: Any, schema: dict[str, Any], location: str = "$") -> str | None:
    expected = schema.get("type")
    type_map = {
        "object": dict,
        "array": list,
        "string": str,
        "integer": int,
        "number": (int, float),
        "boolean": bool,
        "null": type(None),
    }
    if expected in type_map and (not isinstance(value, type_map[expected]) or expected in {"integer", "number"} and isinstance(value, bool)):
        return f"{location} must be {expected}"
    if "const" in schema and value != schema["const"]:
        return f"{location} must equal the declared const"
    if "enum" in schema and value not in schema["enum"]:
        return f"{location} is not in the declared enum"
    if isinstance(value, dict):
        required = schema.get("required", [])
        missing = [key for key in required if key not in value]
        if missing:
            return f"{location} is missing required fields: {', '.join(missing)}"
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            extra = sorted(set(value) - set(properties))
            if extra:
                return f"{location} has undeclared fields: {', '.join(extra)}"
        for key, child_schema in properties.items():
            if key in value and isinstance(child_schema, dict):
                mismatch = _matches_schema(value[key], child_schema, f"{location}.{key}")
                if mismatch:
                    return mismatch
    if isinstance(value, list) and isinstance(schema.get("items"), dict):
        for index, item in enumerate(value):
            mismatch = _matches_schema(item, schema["items"], f"{location}[{index}]")
            if mismatch:
                return mismatch
    return None


def _parse_example(path: Path) -> Any:
    if path.suffix == ".json":
        return json.loads(path.read_text(encoding="utf-8"))
    if path.suffix == ".toml":
        return tomllib.loads(path.read_text(encoding="utf-8"))
    if path.suffix in {".yaml", ".yml"}:
        metadata, _ = parse_document(f"---\n{path.read_text(encoding='utf-8')}\n---\n", path.as_posix())
        return metadata
    raise ValueError(f"unsupported example format '{path.suffix or '<none>'}'")


def _finding(source: SourceDocument, rule: str, message: str, remediation: str) -> Finding:
    return Finding(rule, "error", source.path, message, remediation, subject_id=source.identifier)


def validate_contracts(package: Any) -> list[Finding]:
    findings: list[Finding] = []
    repository = ProjectRepository(package.project_root)
    for source in package.documents("contract"):
        representation = source.metadata.get("representation", {})
        if not isinstance(representation, dict) or representation.get("kind") != "custom":
            continue
        definition = representation.get("definition")
        examples = source.metadata.get("examples") or representation.get("examples") or representation.get("example")
        if isinstance(examples, str):
            examples = [examples]
        if not isinstance(definition, str) or not isinstance(examples, list) or not examples:
            continue
        try:
            definition_path = repository.resolve(safe_relative_path(definition))
            schema = json.loads(definition_path.read_text(encoding="utf-8"))
        except (RepositoryError, OSError, json.JSONDecodeError) as error:
            findings.append(_finding(source, "CONCORDE-CONFORMANCE-002", f"Custom definition cannot be evaluated: {error}", "Use a safe checked-in JSON Schema definition supported by Profile 1."))
            continue
        if not isinstance(schema, dict):
            findings.append(_finding(source, "CONCORDE-CONFORMANCE-002", "Custom definition is not a JSON object schema.", "Use a supported deterministic JSON Schema object."))
            continue
        for relative in examples:
            try:
                example_path = repository.resolve(safe_relative_path(relative))
                value = _parse_example(example_path)
                mismatch = _matches_schema(value, schema)
            except (RepositoryError, OSError, ValueError, json.JSONDecodeError, tomllib.TOMLDecodeError, FrontMatterError) as error:
                findings.append(_finding(source, "CONCORDE-CONFORMANCE-002", f"Example '{relative}' uses an unsupported or unreadable adapter: {error}", "Use JSON, TOML, or constrained YAML and a safe checked-in example."))
                continue
            if mismatch:
                findings.append(_finding(source, "CONCORDE-CONFORMANCE-001", f"Example '{relative}' does not conform: {mismatch}.", "Update the example and implementation together with the normative custom schema."))
    return findings
