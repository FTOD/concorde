"""Typed values, the registered-schema dialect and schema checking, with the standard library only.

A typed value is ``{type_id, schema_version, data}``. The part that owns a type registers it here,
when its code loads, with one version and the schema of its ``data``; the Kernel registers no type
of any part. A registered schema embeds a whole typed value of another type with
``{"$ref": "<type_id>"}``, resolved when a value is checked, so neither owner imports the other.

A record whose own contract defines its representation, such as a workspace binding, a run result
or an error link, carries no envelope and is checked with ``validate`` against a *contract schema*:
the same dialect, which may also keep local ``$defs`` referred to as ``{"$ref": "#/$defs/<name>"}``
so that a recursive record can be described. A registered schema never uses them. Every refusal is
a ``KernelError`` (``specs/concorde/kernel/contracts.md#typed-values``).
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
import re
from pathlib import Path, PurePosixPath
from typing import Any

from .refusal import KernelError

# The keywords of the registered dialect; a contract schema may also use ``$defs``.
KEYWORDS = frozenset(
    {
        "title",
        "description",
        "examples",
        "default",
        "type",
        "properties",
        "required",
        "additionalProperties",
        "items",
        "minItems",
        "maxItems",
        "uniqueItems",
        "minLength",
        "maxLength",
        "pattern",
        "minimum",
        "maximum",
        "enum",
        "const",
        "anyOf",
        "format",
        "$ref",
    }
)
TYPES = ("object", "array", "string", "integer", "number", "boolean", "null")
MAX_DEPTH = 100
LOCAL = "#/$defs/"
DIGEST_PATTERN = r"^sha256:[0-9a-f]{64}$"


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
DIGEST = {**STRING, "pattern": DIGEST_PATTERN}
ARTIFACT = obj({"id": STRING, "path": PATH, "digest": DIGEST})


def pointer(field: str, key: Any) -> str:
    """The JSON pointer of ``key`` below ``field``."""
    return field + "/" + str(key).replace("~", "~0").replace("/", "~1")


# --- JSON text and digests -----------------------------------------------------------------


def canonical(value: Any) -> str:
    """The canonical JSON text of ``value``: sorted keys, no spaces, no non-finite numbers."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value: bytes | Any) -> str:
    """``sha256:`` and the hexadecimal digest of ``value``'s bytes, or of its canonical JSON."""
    data = value if isinstance(value, bytes) else canonical(value).encode()
    return "sha256:" + hashlib.sha256(data).hexdigest()


def decode(text: str) -> Any:
    """The JSON value of ``text``, refusing duplicate fields and non-JSON numeric constants."""

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
        raise KernelError(
            "invalid_json", f"the text is no JSON value: {error}"
        ) from error


# --- schema admission ----------------------------------------------------------------------


def _refuse_schema(field: str, message: str) -> KernelError:
    return KernelError("invalid_input", message, field=field)


def admit(schema: Any, *, contract: bool = False) -> None:
    """Refuse with ``invalid_input`` a schema outside the registered dialect, or, with
    ``contract``, outside the contract-schema dialect, which adds local ``$defs``."""
    _admit(schema, schema, "", 0, contract)


def _admit(schema: Any, root: Any, field: str, depth: int, contract: bool) -> None:
    if depth > MAX_DEPTH:
        raise _refuse_schema(field, f"the schema nests deeper than {MAX_DEPTH} levels")
    if type(schema) is bool:
        return
    if not isinstance(schema, dict):
        raise _refuse_schema(field, "a schema is an object or a boolean")
    allowed = KEYWORDS | {"$defs"} if contract else KEYWORDS
    unknown = sorted(set(schema) - allowed)
    if unknown:
        raise _refuse_schema(
            field,
            f"the schema uses {unknown}, which the "
            + ("contract-schema" if contract else "registered")
            + " dialect does not check",
        )
    if "type" in schema and schema["type"] not in TYPES:
        raise _refuse_schema(
            field, f"type must name one of {list(TYPES)}, not {schema['type']!r}"
        )
    if "$ref" in schema:
        _admit_reference(schema, root, field, contract)

    def child(value, key):
        _admit(value, root, pointer(field, key), depth + 1, contract)

    for name in ("properties", "$defs"):
        if name in schema:
            if not isinstance(schema[name], dict):
                raise _refuse_schema(pointer(field, name), f"{name} must be an object")
            for key, value in schema[name].items():
                child(value, f"{name}/{key}")
    for name in ("items", "additionalProperties"):
        if name in schema:
            child(schema[name], name)
    if "anyOf" in schema:
        if not isinstance(schema["anyOf"], list) or not schema["anyOf"]:
            raise _refuse_schema(pointer(field, "anyOf"), "anyOf must list schemas")
        for index, value in enumerate(schema["anyOf"]):
            child(value, f"anyOf/{index}")
    required = schema.get("required", [])
    if (
        not isinstance(required, list)
        or any(not isinstance(key, str) for key in required)
        or len(set(required)) != len(required)
    ):
        raise _refuse_schema(field, "required must be an array of distinct strings")
    for key in ("minItems", "maxItems", "minLength", "maxLength"):
        if key in schema and (type(schema[key]) is not int or schema[key] < 0):
            raise _refuse_schema(field, f"{key} must be a nonnegative integer")
    for key in ("minimum", "maximum"):
        if key in schema and (
            type(schema[key]) not in (int, float) or not math.isfinite(schema[key])
        ):
            raise _refuse_schema(field, f"{key} must be a finite number")
    for low, high in (
        ("minItems", "maxItems"),
        ("minLength", "maxLength"),
        ("minimum", "maximum"),
    ):
        if low in schema and high in schema and schema[low] > schema[high]:
            raise _refuse_schema(field, f"{low} exceeds {high}")
    if "uniqueItems" in schema and type(schema["uniqueItems"]) is not bool:
        raise _refuse_schema(field, "uniqueItems must be a boolean")
    if "enum" in schema and (
        not isinstance(schema["enum"], list) or not schema["enum"]
    ):
        raise _refuse_schema(field, "enum must be a nonempty array")
    if "pattern" in schema:
        try:
            re.compile(schema["pattern"])
        except (TypeError, re.error) as error:
            raise _refuse_schema(
                field, f"pattern is no regular expression: {error}"
            ) from None
    if "format" in schema and schema["format"] != "project-path":
        raise _refuse_schema(field, "the one format is project-path")


def _admit_reference(schema: dict, root: Any, field: str, contract: bool) -> None:
    reference = schema["$ref"]
    if (
        not isinstance(reference, str)
        or not reference.strip()
        or reference != reference.strip()
    ):
        raise _refuse_schema(field, "$ref must name a type identity")
    if reference.startswith("#"):
        name = reference[len(LOCAL) :]
        if not contract or not reference.startswith(LOCAL) or not name or "/" in name:
            raise _refuse_schema(
                field,
                f"$ref {reference!r} is no bare type identity"
                + (", nor a reference #/$defs/<name>" if contract else ""),
            )
        if not isinstance(root, dict) or name not in root.get("$defs", {}):
            raise _refuse_schema(field, f"$ref {reference!r} names no entry of $defs")
    elif not contract and set(schema) != {"$ref"}:
        raise _refuse_schema(field, "a $ref embedding a typed value stands alone")


# --- typed value registration --------------------------------------------------------------

# type_id -> (schema_version, data schema). Owners fill it through ``register``.
_TYPES: dict[str, tuple[int, dict]] = {}


def register(type_id: str, version: int, schema: dict) -> None:
    """Register ``type_id`` at ``version`` with the schema of its ``data``.

    Registering the same identity again with the same version and an equal schema changes nothing;
    another version or schema is refused with ``duplicate_type`` and keeps the first registration.
    """
    if (
        not isinstance(type_id, str)
        or not type_id.strip()
        or type_id != type_id.strip()
    ):
        raise KernelError(
            "invalid_input", "a type identity is a nonblank name", field="type_id"
        )
    if type(version) is not int or version < 1:
        raise KernelError(
            "invalid_input",
            f"the version of {type_id} must be a positive integer, not {version!r}",
            field="schema_version",
        )
    if not isinstance(schema, dict):
        raise KernelError("invalid_input", f"the schema of {type_id} must be an object")
    try:
        admit(schema)
    except KernelError as error:
        raise KernelError(
            "invalid_input",
            f"the schema of {type_id} is outside the registered dialect at "
            f"{error.field or 'its top'}: {error}",
            field=error.field,
        ) from None
    existing = _TYPES.get(type_id)
    if existing is not None:
        if existing == (version, schema):
            return
        raise KernelError(
            "duplicate_type",
            f"{type_id} is already registered at version {existing[0]} with another version or "
            "schema; the existing registration stays in force",
            field="type_id",
        )
    _TYPES[type_id] = (version, copy.deepcopy(schema))


def _registration(type_id: Any, field: str = "") -> tuple[int, dict]:
    try:
        return _TYPES[type_id]
    except (KeyError, TypeError):
        raise KernelError(
            "unknown_type", f"no type {type_id!r} is registered", field=field
        ) from None


def type_version(type_id: str) -> int:
    """The registered version of ``type_id``."""
    return _registration(type_id)[0]


def data_schema(type_id: str) -> dict:
    """A copy of the registered schema of the ``data`` of ``type_id``."""
    return copy.deepcopy(_registration(type_id)[1])


def typed_schema(type_id: str) -> dict:
    """A schema embedding a whole typed value of ``type_id``, resolved when a value is checked."""
    return {"$ref": type_id}


# --- checking ------------------------------------------------------------------------------


def _equal(first: Any, second: Any) -> bool:
    """JSON equality: numbers compare by value, and a boolean equals only a boolean."""
    numbers = (int, float)
    if type(first) in numbers and type(second) in numbers:
        return first == second
    return type(first) is type(second) and first == second


def _invalid(field: str, message: str) -> KernelError:
    return KernelError("invalid_field", message, field=field)


_PYTHON = {
    "object": (dict,),
    "array": (list,),
    "string": (str,),
    "integer": (int,),
    # Integers are numbers; booleans are neither.
    "number": (int, float),
    "boolean": (bool,),
    "null": (type(None),),
}


def check_schema(value: Any, schema: Any, field: str = "", *, root: Any = None) -> None:
    """Check ``value`` against an admitted ``schema`` as JSON Schema does for these keywords.

    ``root`` is the contract schema whose ``$defs`` local references name; it defaults to
    ``schema`` itself.
    """
    _check(value, schema, field, schema if root is None else root, 0)


def _check(value: Any, schema: Any, field: str, root: Any, depth: int) -> None:
    if depth > MAX_DEPTH:
        raise _invalid(field, f"the value nests deeper than {MAX_DEPTH} levels")
    if schema is True:
        return
    if schema is False:
        raise _invalid(field, "no value is admitted here")
    if "anyOf" in schema:
        failures = []
        for option in schema["anyOf"]:
            try:
                _check(value, option, field, root, depth + 1)
                break
            except KernelError as error:
                failures.append(error)
        else:
            raise KernelError(
                "invalid_field",
                "the value matches none of the admitted alternatives: "
                + "; ".join(f"{item.field or '/'}: {item}" for item in failures),
                field=field,
                causes=failures,
            )
    if "$ref" in schema:
        reference = schema["$ref"]
        if reference.startswith(LOCAL):
            _check(
                value, root["$defs"][reference[len(LOCAL) :]], field, root, depth + 1
            )
        else:
            _check_typed(value, reference, field, depth + 1)
    expected = schema.get("type")
    if expected and type(value) not in _PYTHON[expected]:
        raise _invalid(field, f"expected {expected}, found {_kind(value)}")
    if "const" in schema and not _equal(value, schema["const"]):
        raise _invalid(field, f"expected {schema['const']!r}, found {_short(value)}")
    if "enum" in schema and not any(_equal(value, item) for item in schema["enum"]):
        raise _invalid(field, f"{_short(value)} is none of {schema['enum']!r}")
    # Like JSON Schema, each keyword applies to the kind of value it constrains, whether the
    # schema names a type or not.
    if isinstance(value, dict):
        properties = schema.get("properties", {})
        # Keys that properties do not name are checked against additionalProperties, which
        # admits any value when absent: an object is closed only by additionalProperties false.
        extra = schema.get("additionalProperties", True)
        if extra is False:
            for key in sorted(value.keys() - properties.keys()):
                raise _invalid(pointer(field, key), "the field is not admitted")
        for key in schema.get("required", ()):
            if key not in value:
                raise _invalid(pointer(field, key), "the required field is missing")
        for key, item in value.items():
            _check(
                item, properties.get(key, extra), pointer(field, key), root, depth + 1
            )
    elif isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            raise _invalid(field, f"at least {schema['minItems']} items are required")
        if len(value) > schema.get("maxItems", len(value)):
            raise _invalid(field, f"at most {schema['maxItems']} items are admitted")
        if schema.get("uniqueItems") and len(
            {canonical(item) for item in value}
        ) != len(value):
            raise _invalid(field, "the items must be distinct")
        for index, item in enumerate(value):
            _check(
                item, schema.get("items", True), pointer(field, index), root, depth + 1
            )
        if schema.get("items") == ARTIFACT:
            for key in ("id", "path"):
                if len({item[key] for item in value}) != len(value):
                    raise _invalid(
                        field, f"the artifacts' {key} values must be distinct"
                    )
    elif isinstance(value, str):
        if schema.get("minLength") and not value.strip():
            raise _invalid(field, "the string must not be blank")
        if (
            not schema.get("minLength", 0)
            <= len(value)
            <= schema.get("maxLength", len(value))
        ):
            raise _invalid(
                field, f"the string's length {len(value)} is outside its bounds"
            )
        if "pattern" in schema and re.search(schema["pattern"], value) is None:
            raise _invalid(field, f"{_short(value)} does not match {schema['pattern']}")
        if schema.get("format") == "project-path":
            safe_path(value, field)
    elif type(value) in (int, float):
        if not math.isfinite(value) or not schema.get(
            "minimum", value
        ) <= value <= schema.get("maximum", value):
            raise _invalid(field, f"the number {value!r} is outside its admitted range")


def _kind(value: Any) -> str:
    for name, kinds in _PYTHON.items():
        if type(value) in kinds and not (name == "number" and type(value) is int):
            return name
    return type(value).__name__


def _short(value: Any) -> str:
    text = json.dumps(value, ensure_ascii=False, default=repr)
    return text if len(text) <= 80 else text[:77] + "..."


def _check_typed(value: Any, type_id: str, field: str, depth: int) -> None:
    """Check ``value`` as a whole typed value of ``type_id``, as registered now."""
    version, schema = _registration(type_id, field)
    if not isinstance(value, dict):
        raise _invalid(
            field, f"expected a typed value of {type_id}, found {_kind(value)}"
        )
    for key in sorted(value.keys() - {"type_id", "schema_version", "data"}):
        raise _invalid(pointer(field, key), "a typed value has no such field")
    for key in ("type_id", "schema_version", "data"):
        if key not in value:
            raise _invalid(pointer(field, key), "the required field is missing")
    if value["type_id"] != type_id:
        raise KernelError(
            "incompatible_handoff",
            f"expected a value of {type_id}, found {_short(value['type_id'])}",
            field=pointer(field, "type_id"),
        )
    if type(value["schema_version"]) is not int or value["schema_version"] != version:
        raise KernelError(
            "unsupported_version",
            f"{type_id} is registered at schema_version {version}, not "
            f"{_short(value['schema_version'])}",
            field=pointer(field, "schema_version"),
        )
    _check(value["data"], schema, pointer(field, "data"), schema, depth + 1)


# Contract schemas already admitted, by identity, kept alive so that an identity is never reused.
_ADMITTED: dict[int, Any] = {}


def validate(value: Any, schema: Any, field: str = "") -> None:
    """Check a record against its own contract's schema, which may keep local ``$defs``.

    The schema is admitted the first time it is used (``invalid_input``); a value that breaks it
    is refused with ``invalid_field``, or the typed-value codes for an embedded typed value.
    """
    if _ADMITTED.get(id(schema)) is not schema:
        admit(schema, contract=True)
        if len(_ADMITTED) > 4096:
            _ADMITTED.clear()
        _ADMITTED[id(schema)] = schema
    _check(value, schema, field, schema, 0)


def typed(type_id: str, data: Any) -> dict:
    """A checked typed value of ``type_id`` holding ``data``."""
    return validate_typed(
        {"type_id": type_id, "schema_version": type_version(type_id), "data": data}
    )


def validate_typed(value: Any, expected: str | None = None, field: str = "") -> dict:
    """A checked copy of the typed value ``value``, of the type ``expected`` when it is named."""
    if not isinstance(value, dict):
        raise _invalid(field, f"expected a typed value, found {_kind(value)}")
    type_id = value.get("type_id")
    if not isinstance(type_id, str) or type_id not in _TYPES:
        raise KernelError(
            "unknown_type",
            f"no type {type_id!r} is registered",
            field=pointer(field, "type_id"),
        )
    if expected is not None and type_id != expected:
        raise KernelError(
            "incompatible_handoff",
            f"expected a value of {expected}, found one of {type_id}",
            field=pointer(field, "type_id"),
        )
    _check_typed(value, type_id, field, 0)
    return copy.deepcopy(value)


# --- paths and artifacts -------------------------------------------------------------------


def safe_path(value: Any, field: str = "") -> str:
    """``value`` when it is a canonical project-relative POSIX path, else ``invalid_field``."""
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
        raise _invalid(
            field, f"{_short(value)} is no canonical project-relative POSIX path"
        )
    return value


def checked_path(project: Path, relative: str, field: str = "") -> Path:
    """The file ``relative`` names below ``project``, refusing a symbolic link on the way."""
    safe_path(relative, field)
    path = Path(project)
    for component in relative.split("/"):
        path = path / component
        if path.is_symlink():
            raise _invalid(field, f"{relative} passes through the symbolic link {path}")
    return path


def artifact(root: Path, identifier: str, relative: str) -> dict:
    """``{id, path, digest}`` of a file below ``root``; the caller chooses the root."""
    path = checked_path(root, relative)
    if not path.is_file():
        raise KernelError(
            "stale_reference", f"the artifact {relative} does not exist", field=relative
        )
    return {"id": identifier, "path": relative, "digest": digest(path.read_bytes())}


def verify_artifacts(root: Path, value: Any, field: str = "") -> None:
    """Refuse with ``stale_reference`` an artifact in ``value`` whose bytes changed."""
    if isinstance(value, dict):
        if set(value) == {"id", "path", "digest"}:
            check_schema(value, ARTIFACT, field)
            if artifact(root, value["id"], value["path"]) != value:
                raise KernelError(
                    "stale_reference",
                    f"the bytes of the artifact {value['path']} changed",
                    field=field,
                )
        else:
            for key, item in value.items():
                verify_artifacts(root, item, pointer(field, key))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            verify_artifacts(root, item, pointer(field, index))


__all__ = [
    "ARTIFACT",
    "DIGEST",
    "DIGEST_PATTERN",
    "KEYWORDS",
    "PATH",
    "STRING",
    "admit",
    "array",
    "artifact",
    "canonical",
    "check_schema",
    "checked_path",
    "data_schema",
    "decode",
    "digest",
    "obj",
    "pointer",
    "register",
    "safe_path",
    "type_version",
    "typed",
    "typed_schema",
    "validate",
    "validate_typed",
    "verify_artifacts",
]
