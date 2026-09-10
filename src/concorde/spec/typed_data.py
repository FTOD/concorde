"""Versioned JSON values admitted at capability and leaf data boundaries.

Schemas are ordinary JSON Schema objects. Validation uses the standard library so
configuration and admission work before the managed graph runtime is installed.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path, PurePosixPath
from typing import Any

from .wire_shapes import ARTIFACT, PATH, STRING, array, obj, typed_schema


class TypedDataError(ValueError):
    def __init__(self, code: str, field: str, message: str):
        super().__init__(message)
        self.code, self.field = code, field

    def to_dict(self) -> dict[str, str]:
        return {"code": self.code, "field": self.field, "message": str(self)}


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def decode(text: str) -> Any:
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError(f"duplicate JSON field: {key}")
            result[key] = value
        return result

    def constant(value):
        raise ValueError(f"non-JSON numeric constant: {value}")

    try:
        return json.loads(text, object_pairs_hook=pairs, parse_constant=constant)
    except (ValueError, TypeError, RecursionError) as error:
        raise TypedDataError("invalid_json", "", str(error)) from error


REFLECTION_ID = {**STRING, "pattern": r"^R-[0-9]{3,}$"}
COMMIT = {**STRING, "pattern": r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$"}
# Capability identities and their paired context/result type IDs are declared by ``contracts``;
# this mapping is populated from it at the end of this module.
CAPABILITY_CONTRACTS: dict[str, tuple[str, str]] = {}


DATA_SCHEMAS = {
    "concorde-capability-configuration": obj({"integration": {"enum": ["codex", "claude"]},
                                            "enforcement": {"enum": ["native"]}}),
    "concorde-reflection-investigation-result": obj({
        "findings": array(obj({
            "reflection_id": REFLECTION_ID, "verified_commit": COMMIT,
            "observed_state": {"enum": ["reproduced", "not-reproduced"]},
            "verification": STRING, "analysis": STRING, "resolution": STRING,
            "intervention_rationale": STRING,
            "human_intervention": {"enum": ["required", "not-required"]},
            "route": {"enum": ["fast-loop", "plan", "dismiss", "blocked"]},
            "effort": {"enum": ["small", "medium", "large"]}, "files": array(PATH, unique=True),
            "steps": STRING, "validation": STRING, "risks": STRING,
            "protocol_change": {"type": "boolean"},
        })),
    }),
}


def _pointer(field: str, key: Any) -> str:
    return field + "/" + str(key).replace("~", "~0").replace("/", "~1")


def check_schema(value: Any, schema: dict, field: str = "") -> None:
    if "anyOf" in schema:
        for option in schema["anyOf"]:
            try:
                check_schema(value, option, field)
                return
            except TypedDataError:
                pass
        raise TypedDataError("invalid_field", field, "value does not match an admitted alternative")
    if "$ref" in schema:
        return check_schema(value, DATA_SCHEMAS[schema["$ref"]], field)
    types = {"object": dict, "array": list, "string": str, "integer": int, "boolean": bool, "null": type(None)}
    expected = schema.get("type")
    if expected and type(value) is not types[expected]:
        raise TypedDataError("invalid_field", field, f"expected {expected}")
    if "const" in schema and (value != schema["const"] or type(value) is not type(schema["const"])):
        raise TypedDataError("invalid_field", field, f"expected {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        raise TypedDataError("invalid_field", field, "unsupported value")
    if expected == "object" and schema.get("format") == "typed-task":
        if not isinstance(value, dict) or value.get("type_id") not in {item[0] for item in CAPABILITY_CONTRACTS.values()}:
            raise TypedDataError("unknown_type", field, "expected a capability task input")
        validate_typed(value, field=field)
    elif expected == "object":
        properties = schema.get("properties", {})
        for key in value.keys() - properties.keys():
            raise TypedDataError("invalid_field", _pointer(field, key), "unknown field")
        for key in schema.get("required", ()):
            if key not in value:
                raise TypedDataError("invalid_field", _pointer(field, key), "required field is missing")
        for key, item in value.items():
            check_schema(item, properties[key], _pointer(field, key))
    elif expected == "array":
        if len(value) < schema.get("minItems", 0):
            raise TypedDataError("invalid_field", field, "too few items")
        if schema.get("uniqueItems") and len({canonical(item) for item in value}) != len(value):
            raise TypedDataError("invalid_field", field, "items must be unique")
        for index, item in enumerate(value):
            check_schema(item, schema["items"], _pointer(field, index))
        if schema["items"] == ARTIFACT:
            for key in ("id", "path"):
                if len({item[key] for item in value}) != len(value):
                    raise TypedDataError("invalid_field", field, f"artifact {key} values must be unique")
    elif expected == "string":
        if schema.get("minLength") and not value.strip():
            raise TypedDataError("invalid_field", field, "string must not be empty")
        if "pattern" in schema and re.fullmatch(schema["pattern"], value) is None:
            raise TypedDataError("invalid_field", field, "invalid string format")
        if schema.get("format") == "project-path":
            safe_path(value, field)


def safe_path(value: str, field: str = "") -> str:
    if (not isinstance(value, str) or not value or "\\" in value or ":" in value
            or any(ord(character) < 32 or ord(character) == 127 for character in value) or value.startswith("/")
            or any(part in {"", ".", ".."} for part in value.split("/"))
            or PurePosixPath(value).as_posix() != value):
        raise TypedDataError("invalid_field", field, "expected a canonical project-relative POSIX path")
    return value


def checked_path(project: Path, relative: str, field: str = "") -> Path:
    safe_path(relative, field)
    path = project
    for component in relative.split("/"):
        path = path / component
        if path.is_symlink():
            raise TypedDataError("invalid_field", field, "symlink paths are forbidden")
    return path


def typed(type_id: str, data: dict) -> dict:
    return validate_typed({"type_id": type_id, "schema_version": 1, "data": data})


def validate_typed(value: Any, expected: str | None = None, field: str = "") -> dict:
    if not isinstance(value, dict):
        raise TypedDataError("invalid_field", field, "expected a TypedValue object")
    type_id = value.get("type_id")
    if not isinstance(type_id, str) or type_id not in DATA_SCHEMAS:
        raise TypedDataError("unknown_type", _pointer(field, "type_id"), "unknown data type")
    if expected is not None and type_id != expected:
        raise TypedDataError("incompatible_handoff", _pointer(field, "type_id"), f"expected {expected}")
    if type(value.get("schema_version")) is not int or value["schema_version"] != 1:
        raise TypedDataError("unsupported_version", _pointer(field, "schema_version"), f"{type_id} requires schema_version 1")
    check_schema(value, typed_schema(type_id), field)
    result = copy.deepcopy(value)
    data = result["data"]
    if type_id == "concorde-main-request":
        action = data.setdefault("action", "ask")
        if action in {"ask", "design-topology"}:
            if "task" not in data:
                raise TypedDataError("invalid_field", field + "/data/task", "task is required")
            if "topology_proposal" in data or "application" in data:
                raise TypedDataError("invalid_field", field + "/data", "proposal fields are invalid for this action")
            data.setdefault("constraints", [])
        elif action == "accept-topology":
            if "topology_proposal" not in data:
                raise TypedDataError("invalid_field", field + "/data/topology_proposal", "accept-topology requires the design proposal")
            if "application" in data:
                raise TypedDataError("invalid_field", field + "/data/application", "application is only valid for apply-topology")
            forbidden = {"task", "target_id", "focus_id", "constraints"} & data.keys()
            if forbidden:
                raise TypedDataError("invalid_field", field + "/data", f"accept-topology forbids {sorted(forbidden)}")
        else:
            if "application" not in data:
                raise TypedDataError("invalid_field", field + "/data/application", "apply-topology requires the exact application")
            if "topology_proposal" in data:
                raise TypedDataError("invalid_field", field + "/data/topology_proposal", "use the proposal embedded in application")
            forbidden = {"task", "target_id", "focus_id", "constraints"} & data.keys()
            if forbidden:
                raise TypedDataError("invalid_field", field + "/data", f"apply-topology forbids {sorted(forbidden)}")
        if "focus_id" in data and "target_id" not in data:
            raise TypedDataError("invalid_field", field + "/data/focus_id", "focus hint requires target hint")
    return result


def artifact(project: Path, identifier: str, relative: str) -> dict:
    path = checked_path(project, relative)
    if not path.is_file():
        raise TypedDataError("stale_reference", "", f"artifact does not exist: {relative}")
    return {"id": identifier, "path": relative, "digest": "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()}


def verify_artifacts(project: Path, value: Any, field: str = "") -> None:
    if isinstance(value, dict):
        if set(value) == {"id", "path", "digest"}:
            check_schema(value, ARTIFACT, field)
            if artifact(project, value["id"], value["path"]) != value:
                raise TypedDataError("stale_reference", field, f"artifact bytes changed: {value['path']}")
        else:
            for key, item in value.items():
                verify_artifacts(project, item, _pointer(field, key))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            verify_artifacts(project, item, _pointer(field, index))


def json_schema(type_id: str) -> dict:
    """Export a self-contained Draft 2020-12 schema for tooling and documentation."""
    def expand(value):
        if isinstance(value, dict):
            if "$ref" in value:
                return {"$ref": "#/$defs/" + value["$ref"]}
            if value.get("format") == "typed-task":
                return {"anyOf": [expand(typed_schema(item[0])) for item in CAPABILITY_CONTRACTS.values()]}
            return {key: expand(item) for key, item in value.items() if key != "format"}
        if isinstance(value, list):
            return [expand(item) for item in value]
        return value
    definitions = {}
    pending = [type_id]
    def references(value):
        if isinstance(value, dict):
            if "$ref" in value:
                yield value["$ref"].split("/")[-1]
            for item in value.values():
                yield from references(item)
        elif isinstance(value, list):
            for item in value:
                yield from references(item)
    while pending:
        name = pending.pop()
        if name not in definitions:
            definitions[name] = expand(DATA_SCHEMAS[name])
            pending.extend(references(definitions[name]))
    return {"$schema": "https://json-schema.org/draft/2020-12/schema",
            **expand(typed_schema(type_id)), "$defs": definitions}

# Every registered capability entry point and its wire schemas are declared by ``contracts``;
# the two shapes above are the host-owned values that no single capability owns.
from .contracts import contracts as _capability_contracts, schemas as _capability_schemas
DATA_SCHEMAS.update(_capability_schemas())
CAPABILITY_CONTRACTS.update(_capability_contracts())
