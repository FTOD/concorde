"""Versioned JSON values admitted at Operation and leaf data boundaries.

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


class OperationDataError(ValueError):
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
        raise OperationDataError("invalid_json", "", str(error)) from error


def obj(properties: dict, optional: tuple[str, ...] = ()) -> dict:
    return {"type": "object", "properties": properties,
            "required": [key for key in properties if key not in optional],
            "additionalProperties": False}


def array(items: dict, *, unique: bool = False) -> dict:
    return {"type": "array", "items": items, **({"uniqueItems": True} if unique else {})}


STRING = {"type": "string", "minLength": 1}
PATH = {**STRING, "format": "project-path"}
DIGEST = {**STRING, "pattern": r"^sha256:[0-9a-f]{64}$"}
FEATURE_ID = {**STRING, "pattern": r"^feature\.[a-z0-9]+(?:[.-][a-z0-9-]+)*$"}
REFLECTION_ID = {**STRING, "pattern": r"^R-[0-9]{3,}$"}
COMMIT = {**STRING, "pattern": r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$"}
CONSTRAINTS = array(STRING)
ARTIFACT = obj({"id": STRING, "path": PATH, "digest": DIGEST})
TASK = {"feature_path": PATH, "request": STRING, "constraints": CONSTRAINTS}
SELECTION = {"feature_id": FEATURE_ID, "feature_path": PATH, "attempt_dir": PATH,
             "source_digest": DIGEST, "artifacts": array(ARTIFACT, unique=True)}
ACTIONS = {"enum": ["status", "investigate", "implement", "merge", "close"]}
OPERATION_CONTRACTS = {
    "concorde-plan": ("concorde-plan-context", "concorde-plan-result"),
    "concorde-standard-dev-loop": ("concorde-standard-dev-loop-context", "concorde-standard-dev-loop-result"),
    "concorde-reflections-triage": ("concorde-reflections-triage-context", "concorde-reflections-triage-result"),
}


def typed_schema(type_id: str) -> dict:
    return obj({"type_id": {"const": type_id}, "schema_version": {"type": "integer", "const": 1},
                "data": {"$ref": type_id}})


DATA_SCHEMAS = {
    "concorde-operation-configuration": obj({"integration": {"enum": ["codex", "claude"]},
                                            "enforcement": {"enum": ["native", "outer"]}}),
    "concorde-plan-context": obj({**TASK, "source_artifacts": array(ARTIFACT, unique=True)}, ("constraints", "source_artifacts")),
    "concorde-standard-dev-loop-context": obj(TASK, ("constraints",)),
    "concorde-plan-author-context": obj({"task": typed_schema("concorde-plan-context"),
                                        "planning_context": typed_schema("concorde-planning-context")}),
    "concorde-planning-context": obj({
        "feature_id": FEATURE_ID, "feature_path": PATH, "module_id": STRING,
        "module_architecture": ARTIFACT, "attempt_dir": PATH, "source_digest": DIGEST,
        "owned_artifacts": array(ARTIFACT, unique=True),
        "provider_features": array(obj({"feature_id": FEATURE_ID, "artifact": ARTIFACT,
                                         "interface_ids": {**array(STRING, unique=True), "minItems": 1}}), unique=True),
        "denied_paths": array(PATH, unique=True),
    }),
    "concorde-plan-result": obj(SELECTION),
    "concorde-standard-dev-loop-result": obj({
        "feature_id": FEATURE_ID, "feature_path": PATH,
        "completed_capabilities": {"const": ["concorde-specify", "concorde-plan", "concorde-tasks",
                                               "concorde-implement", "concorde-validate", "concorde-deliver"]},
        "delivery": obj({"status": {"const": "delivered"}, "attempt_dir": PATH,
                          "retained_source_digest": DIGEST}),
    }),
    "concorde-reflections-triage-context": obj({
        "action": ACTIONS, "reflection_ids": array(REFLECTION_ID, unique=True),
        "route": {"enum": ["fast-loop", "plan"]}, **TASK,
    }, ("route", "feature_path", "request", "constraints")),
    "concorde-reflections-triage-result": obj({
        "action": ACTIONS, "reflection_ids": array(REFLECTION_ID, unique=True),
        "dispositions": array(obj({"reflection_id": REFLECTION_ID,
                                   "outcome": {"enum": ["inspected", "planned", "implemented", "merged", "closed", "needs-comments"]}})),
        "plan_result": typed_schema("concorde-plan-result"),
    }, ("plan_result",)),
}

# Leaf adapters have fixed identities too; their results are derived from verified
# workspace state, never by parsing an agent's narrative completion output.
for _name in ("specify", "tasks", "implement", "validate", "deliver", "analyze", "fast-loop"):
    DATA_SCHEMAS[f"concorde-{_name}-context"] = obj({
        "task": {"type": "object", "format": "typed-task"}, **SELECTION,
        "source_artifacts": array(ARTIFACT, unique=True),
    }, ("source_artifacts",))
    DATA_SCHEMAS[f"concorde-{_name}-result"] = obj(SELECTION)
DATA_SCHEMAS["concorde-specify-context"] = obj({"task": {"type": "object", "format": "typed-task"}, "feature_path": PATH})
DATA_SCHEMAS["concorde-analyze-context"] = obj({
    "task": typed_schema("concorde-reflections-triage-context"), **SELECTION,
    "head": COMMIT, "verified_on": {**STRING, "pattern": r"^\d{4}-\d{2}-\d{2}$"},
    "reflections": array(obj({"reflection_id": REFLECTION_ID, "document": ARTIFACT, "plan": ARTIFACT}, ("plan",))),
})
DATA_SCHEMAS["concorde-reflection-investigation-result"] = obj({
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
})


def _pointer(field: str, key: Any) -> str:
    return field + "/" + str(key).replace("~", "~0").replace("/", "~1")


def check_schema(value: Any, schema: dict, field: str = "") -> None:
    if "$ref" in schema:
        return check_schema(value, DATA_SCHEMAS[schema["$ref"]], field)
    types = {"object": dict, "array": list, "string": str, "integer": int, "boolean": bool}
    expected = schema.get("type")
    if expected and type(value) is not types[expected]:
        raise OperationDataError("invalid_field", field, f"expected {expected}")
    if "const" in schema and (value != schema["const"] or type(value) is not type(schema["const"])):
        raise OperationDataError("invalid_field", field, f"expected {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        raise OperationDataError("invalid_field", field, "unsupported value")
    if expected == "object" and schema.get("format") == "typed-task":
        if not isinstance(value, dict) or value.get("type_id") not in {item[0] for item in OPERATION_CONTRACTS.values()}:
            raise OperationDataError("unknown_type", field, "expected an Operation task input")
        validate_typed(value, field=field)
    elif expected == "object":
        properties = schema.get("properties", {})
        for key in value.keys() - properties.keys():
            raise OperationDataError("invalid_field", _pointer(field, key), "unknown field")
        for key in schema.get("required", ()):
            if key not in value:
                raise OperationDataError("invalid_field", _pointer(field, key), "required field is missing")
        for key, item in value.items():
            check_schema(item, properties[key], _pointer(field, key))
    elif expected == "array":
        if len(value) < schema.get("minItems", 0):
            raise OperationDataError("invalid_field", field, "too few items")
        if schema.get("uniqueItems") and len({canonical(item) for item in value}) != len(value):
            raise OperationDataError("invalid_field", field, "items must be unique")
        for index, item in enumerate(value):
            check_schema(item, schema["items"], _pointer(field, index))
        if schema["items"] == ARTIFACT:
            for key in ("id", "path"):
                if len({item[key] for item in value}) != len(value):
                    raise OperationDataError("invalid_field", field, f"artifact {key} values must be unique")
    elif expected == "string":
        if schema.get("minLength") and not value.strip():
            raise OperationDataError("invalid_field", field, "string must not be empty")
        if "pattern" in schema and re.fullmatch(schema["pattern"], value) is None:
            raise OperationDataError("invalid_field", field, "invalid string format")
        if schema.get("format") == "project-path":
            safe_path(value, field)


def safe_path(value: str, field: str = "") -> str:
    if (not isinstance(value, str) or not value or "\\" in value or ":" in value
            or any(ord(character) < 32 or ord(character) == 127 for character in value) or value.startswith("/")
            or any(part in {"", ".", ".."} for part in value.split("/"))
            or PurePosixPath(value).as_posix() != value):
        raise OperationDataError("invalid_field", field, "expected a canonical project-relative POSIX path")
    return value


def checked_path(project: Path, relative: str, field: str = "") -> Path:
    safe_path(relative, field)
    path = project
    for component in relative.split("/"):
        path = path / component
        if path.is_symlink():
            raise OperationDataError("invalid_field", field, "symlink paths are forbidden")
    return path


def typed(type_id: str, data: dict) -> dict:
    return validate_typed({"type_id": type_id, "schema_version": 1, "data": data})


def validate_typed(value: Any, expected: str | None = None, field: str = "") -> dict:
    if not isinstance(value, dict):
        raise OperationDataError("invalid_field", field, "expected a TypedValue object")
    type_id = value.get("type_id")
    if not isinstance(type_id, str) or type_id not in DATA_SCHEMAS:
        raise OperationDataError("unknown_type", _pointer(field, "type_id"), "unknown data type")
    if expected is not None and type_id != expected:
        raise OperationDataError("incompatible_handoff", _pointer(field, "type_id"), f"expected {expected}")
    if type(value.get("schema_version")) is not int or value["schema_version"] != 1:
        raise OperationDataError("unsupported_version", _pointer(field, "schema_version"), f"{type_id} requires schema_version 1")
    check_schema(value, typed_schema(type_id), field)
    result = copy.deepcopy(value)
    data = result["data"]
    if type_id in {"concorde-plan-context", "concorde-standard-dev-loop-context"}:
        data.setdefault("constraints", [])
    if type_id == "concorde-plan-context":
        data.setdefault("source_artifacts", [])
    if type_id == "concorde-reflections-triage-context":
        action = data["action"]
        if action != "status" and not data["reflection_ids"]:
            raise OperationDataError("invalid_field", field + "/data/reflection_ids", "this action requires an explicit nonempty selection")
        required = {"route"} if action == "implement" else set()
        forbidden = set() if action == "implement" else {"route"}
        if action in {"status", "close"}:
            forbidden.update(TASK)
        else:
            required.update(("feature_path", "request"))
            data.setdefault("constraints", [])
        for key in required - data.keys():
            raise OperationDataError("invalid_field", _pointer(field + "/data", key), f"required for {action}")
        for key in forbidden & data.keys():
            raise OperationDataError("invalid_field", _pointer(field + "/data", key), f"forbidden for {action}")
    if type_id == "concorde-reflections-triage-result":
        ids = [item["reflection_id"] for item in data["dispositions"]]
        if ids != data["reflection_ids"]:
            raise OperationDataError("incompatible_handoff", field + "/data/dispositions", "dispositions must match the exact selected IDs in order")
    if "feature_id" in data and "attempt_dir" in data:
        if data["attempt_dir"] != f".concorde/attempts/{data['feature_id']}":
            raise OperationDataError("workspace_mismatch", field + "/data/attempt_dir", "attempt does not belong to selected feature")
    return result


def artifact(project: Path, identifier: str, relative: str) -> dict:
    path = checked_path(project, relative)
    if not path.is_file():
        raise OperationDataError("stale_reference", "", f"artifact does not exist: {relative}")
    return {"id": identifier, "path": relative, "digest": "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()}


def verify_artifacts(project: Path, value: Any, field: str = "") -> None:
    if isinstance(value, dict):
        if set(value) == {"id", "path", "digest"}:
            check_schema(value, ARTIFACT, field)
            if artifact(project, value["id"], value["path"]) != value:
                raise OperationDataError("stale_reference", field, f"artifact bytes changed: {value['path']}")
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
                return {"anyOf": [expand(typed_schema(item[0])) for item in OPERATION_CONTRACTS.values()]}
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
