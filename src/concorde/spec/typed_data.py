"""Versioned JSON values that Concorde's Modules exchange.

Every typed value is ``{type_id, schema_version, data}``. The owner of a type registers it here
with its version and the schema of its ``data``; Spec tooling registers only its own types and
imports no owner. A schema names another registered type with ``typed_schema(type_id)``, which is
resolved when a value is checked, so an owner never imports the owner of a type it embeds. Checking
uses the standard library only.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path, PurePosixPath
from typing import Any

from . import schema as _subset


class TypedDataError(ValueError):
    def __init__(self, code: str, field: str, message: str):
        super().__init__(message)
        self.code, self.field = code, field

    def to_dict(self) -> dict[str, str]:
        return {"code": self.code, "field": self.field, "message": str(self)}


# --- shared building blocks ----------------------------------------------------------------


def obj(properties: dict, optional: tuple[str, ...] = ()) -> dict:
    """A closed object whose listed properties are required unless named in ``optional``."""
    return {
        "type": "object",
        "properties": properties,
        "required": [key for key in properties if key not in optional],
        "additionalProperties": False,
    }


def array(items: dict, *, unique: bool = False) -> dict:
    return {
        "type": "array",
        "items": items,
        **({"uniqueItems": True} if unique else {}),
    }


STRING = {"type": "string", "minLength": 1}
PATH = {**STRING, "format": "project-path"}
DIGEST = {**STRING, "pattern": r"^sha256:[0-9a-f]{64}$"}
ARTIFACT = obj({"id": STRING, "path": PATH, "digest": DIGEST})


# --- registration --------------------------------------------------------------------------

# type_id -> (schema_version, data schema). Owners fill it through ``register``.
_TYPES: dict[str, tuple[int, dict]] = {}
# The Python module whose code registered each type.


def _admissible(value: Any) -> Any:
    """The schema with every registered-type reference replaced by ``true`` for the subset check."""
    if isinstance(value, dict):
        if "$ref" in value:
            reference = value["$ref"]
            if (
                set(value) != {"$ref"}
                or not isinstance(reference, str)
                or not reference.strip()
                or reference.startswith("#")
            ):
                raise TypedDataError(
                    "invalid_input",
                    "",
                    "a registered schema refers to other types only through typed_schema()",
                )
            return True
        return {key: _admissible(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_admissible(item) for item in value]
    return value


def register(type_id: str, version: int, schema: dict) -> None:
    """Register ``type_id`` at ``version`` with the schema of its ``data``.

    Registering the same identity again with the same version and an equal schema changes nothing;
    another version or schema fails with ``duplicate_type`` and keeps the first registration.
    """
    if (
        not isinstance(type_id, str)
        or not type_id.strip()
        or type_id != type_id.strip()
    ):
        raise TypedDataError(
            "invalid_input", "type_id", "type_id must be a nonblank name"
        )
    if type(version) is not int or version < 1:
        raise TypedDataError(
            "invalid_input", "schema_version", "version must be a positive integer"
        )
    if not isinstance(schema, dict):
        raise TypedDataError("invalid_input", type_id, "schema must be an object")
    try:
        _subset.admit(_admissible(schema))
    except _subset.ContractError as error:
        raise TypedDataError(
            "invalid_input", type_id, f"schema is not admitted: {error}"
        ) from error
    existing = _TYPES.get(type_id)
    if existing is not None:
        if existing == (version, schema):
            return
        raise TypedDataError(
            "duplicate_type",
            type_id,
            f"{type_id} is already registered with another version or schema",
        )
    _TYPES[type_id] = (version, copy.deepcopy(schema))


def _registration(type_id: str, field: str = "") -> tuple[int, dict]:
    try:
        return _TYPES[type_id]
    except (KeyError, TypeError):
        raise TypedDataError(
            "unknown_type", field, f"unknown data type: {type_id!r}"
        ) from None


def type_version(type_id: str) -> int:
    """The registered schema version of ``type_id``."""
    return _registration(type_id)[0]


def data_schema(type_id: str) -> dict:
    """A copy of the registered schema of the ``data`` of ``type_id``."""
    return copy.deepcopy(_registration(type_id)[1])


def typed_schema(type_id: str) -> dict:
    """A schema fragment matching a whole typed value of ``type_id``, resolved at check time."""
    return {"$ref": type_id}


def _whole(type_id: str, field: str = "") -> dict:
    version, schema = _registration(type_id, field)
    return obj(
        {
            "type_id": {"const": type_id},
            "schema_version": {"type": "integer", "const": version},
            "data": schema,
        }
    )


# --- checking ------------------------------------------------------------------------------


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
        raise TypedDataError(
            "invalid_field", field, "value does not match an admitted alternative"
        )
    if "$ref" in schema:
        return check_schema(value, _whole(schema["$ref"], field), field)
    types = {
        "object": dict,
        "array": list,
        "string": str,
        "integer": int,
        "boolean": bool,
        "null": type(None),
    }
    expected = schema.get("type")
    if expected and type(value) is not types[expected]:
        raise TypedDataError("invalid_field", field, f"expected {expected}")
    if "const" in schema and (
        value != schema["const"] or type(value) is not type(schema["const"])
    ):
        raise TypedDataError("invalid_field", field, f"expected {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        raise TypedDataError("invalid_field", field, "unsupported value")
    if expected == "object":
        properties = schema.get("properties", {})
        # A schema-valued additionalProperties admits a keyed map whose values share one schema.
        extra = schema.get("additionalProperties")
        if not isinstance(extra, dict):
            for key in value.keys() - properties.keys():
                raise TypedDataError(
                    "invalid_field", _pointer(field, key), "unknown field"
                )
        for key in schema.get("required", ()):
            if key not in value:
                raise TypedDataError(
                    "invalid_field", _pointer(field, key), "required field is missing"
                )
        for key, item in value.items():
            check_schema(item, properties.get(key, extra), _pointer(field, key))
    elif expected == "array":
        if len(value) < schema.get("minItems", 0):
            raise TypedDataError("invalid_field", field, "too few items")
        if schema.get("uniqueItems") and len(
            {canonical(item) for item in value}
        ) != len(value):
            raise TypedDataError("invalid_field", field, "items must be unique")
        for index, item in enumerate(value):
            check_schema(item, schema["items"], _pointer(field, index))
        if schema["items"] == ARTIFACT:
            for key in ("id", "path"):
                if len({item[key] for item in value}) != len(value):
                    raise TypedDataError(
                        "invalid_field", field, f"artifact {key} values must be unique"
                    )
    elif expected == "string":
        if schema.get("minLength") and not value.strip():
            raise TypedDataError("invalid_field", field, "string must not be empty")
        if "pattern" in schema and re.fullmatch(schema["pattern"], value) is None:
            raise TypedDataError("invalid_field", field, "invalid string format")
        if schema.get("format") == "project-path":
            safe_path(value, field)


def safe_path(value: str, field: str = "") -> str:
    if (
        not isinstance(value, str)
        or not value
        or "\\" in value
        or ":" in value
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
        or value.startswith("/")
        or any(part in {"", ".", ".."} for part in value.split("/"))
        or PurePosixPath(value).as_posix() != value
    ):
        raise TypedDataError(
            "invalid_field", field, "expected a canonical project-relative POSIX path"
        )
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
    return validate_typed(
        {"type_id": type_id, "schema_version": type_version(type_id), "data": data}
    )


def validate_typed(value: Any, expected: str | None = None, field: str = "") -> dict:
    if not isinstance(value, dict):
        raise TypedDataError("invalid_field", field, "expected a TypedValue object")
    type_id = value.get("type_id")
    if not isinstance(type_id, str) or type_id not in _TYPES:
        raise TypedDataError(
            "unknown_type", _pointer(field, "type_id"), "unknown data type"
        )
    if expected is not None and type_id != expected:
        raise TypedDataError(
            "incompatible_handoff", _pointer(field, "type_id"), f"expected {expected}"
        )
    version = type_version(type_id)
    if (
        type(value.get("schema_version")) is not int
        or value["schema_version"] != version
    ):
        raise TypedDataError(
            "unsupported_version",
            _pointer(field, "schema_version"),
            f"{type_id} requires schema_version {version}",
        )
    check_schema(value, _whole(type_id, field), field)
    return copy.deepcopy(value)


def artifact(root: Path, identifier: str, relative: str) -> dict:
    """``{id, path, digest}`` of a file below ``root``; the caller chooses the worktree."""
    path = checked_path(root, relative)
    if not path.is_file():
        raise TypedDataError(
            "stale_reference", "", f"artifact does not exist: {relative}"
        )
    return {
        "id": identifier,
        "path": relative,
        "digest": "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def verify_artifacts(root: Path, value: Any, field: str = "") -> None:
    if isinstance(value, dict):
        if set(value) == {"id", "path", "digest"}:
            check_schema(value, ARTIFACT, field)
            if artifact(root, value["id"], value["path"]) != value:
                raise TypedDataError(
                    "stale_reference", field, f"artifact bytes changed: {value['path']}"
                )
        else:
            for key, item in value.items():
                verify_artifacts(root, item, _pointer(field, key))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            verify_artifacts(root, item, _pointer(field, index))
