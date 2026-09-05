"""Offline JSON Schema subset used by published Concorde contracts.

Unsupported assertion keywords fail schema admission. References are local only.
This is deliberately an advertised subset, never a claim of full JSON Schema support.
"""
from __future__ import annotations

import json
import math
import re
from typing import Any


class ContractError(ValueError):
    def __init__(self, message: str, field: str = ""):
        self.field = field
        super().__init__(f"{field or '/'}: {message}")


KEYWORDS = frozenset({"$schema", "$id", "$defs", "$ref", "title", "description", "examples",
    "default", "type", "properties", "required", "additionalProperties", "items", "minItems",
    "maxItems", "uniqueItems", "minLength", "maxLength", "pattern", "minimum", "maximum",
    "enum", "const", "anyOf", "oneOf", "allOf", "format"})
TYPES = {"object", "array", "string", "integer", "number", "boolean", "null"}


def pointer(base: str, key: Any) -> str:
    return base + "/" + str(key).replace("~", "~0").replace("/", "~1")


def admit(schema: Any, root: dict | None = None) -> None:
    if type(schema) is bool:
        return
    if not isinstance(schema, dict):
        raise ContractError("schema must be an object or boolean")
    root = schema if root is None else root
    if set(schema) - KEYWORDS:
        raise ContractError(f"unsupported schema keywords: {sorted(set(schema) - KEYWORDS)}")
    if "type" in schema:
        kinds = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
        if not kinds or any(kind not in TYPES for kind in kinds):
            raise ContractError("unsupported schema type")
    if "$ref" in schema:
        ref = schema["$ref"]
        if not isinstance(ref, str) or not ref.startswith("#/$defs/") or "/" in ref[8:]:
            raise ContractError("only direct local $defs references are supported")
        if ref[8:] not in root.get("$defs", {}):
            raise ContractError(f"unresolved schema reference: {ref}")
    for name in ("properties", "$defs"):
        if name in schema:
            if not isinstance(schema[name], dict):
                raise ContractError(f"{name} must be an object")
            for child in schema[name].values():
                admit(child, root)
    for name in ("items", "additionalProperties"):
        if name in schema:
            admit(schema[name], root)
    for name in ("anyOf", "oneOf", "allOf"):
        if name in schema:
            if not isinstance(schema[name], list) or not schema[name]:
                raise ContractError(f"{name} must contain schemas")
            for child in schema[name]:
                admit(child, root)
    if "required" in schema and (not isinstance(schema["required"], list)
            or any(not isinstance(k, str) for k in schema["required"])
            or len(set(schema["required"])) != len(schema["required"])):
        raise ContractError("required must be a unique string array")
    for key in ("minItems", "maxItems", "minLength", "maxLength"):
        if key in schema and (type(schema[key]) is not int or schema[key] < 0):
            raise ContractError(f"{key} must be a nonnegative integer")
    for key in ("minimum", "maximum"):
        if key in schema and (type(schema[key]) not in {int, float} or not math.isfinite(schema[key])):
            raise ContractError(f"{key} must be a finite number")
    if "uniqueItems" in schema and type(schema["uniqueItems"]) is not bool:
        raise ContractError("uniqueItems must be boolean")
    if "enum" in schema and (not isinstance(schema["enum"], list) or not schema["enum"]):
        raise ContractError("enum must be a nonempty array")
    for low, high in (("minItems","maxItems"),("minLength","maxLength"),("minimum","maximum")):
        if low in schema and high in schema and schema[low] > schema[high]:
            raise ContractError(f"{low} exceeds {high}")
    if "pattern" in schema:
        try:
            re.compile(schema["pattern"])
        except (TypeError, re.error) as error:
            raise ContractError("invalid pattern") from error
    if "format" in schema and schema["format"] != "project-path":
        raise ContractError("only the project-path format is supported")


def validate(value: Any, schema: Any, field: str = "", *, root: dict | None = None,
             depth: int = 0) -> None:
    if depth > 100:
        raise ContractError("schema/value nesting limit exceeded", field)
    if schema is True:
        return
    if schema is False:
        raise ContractError("value is forbidden", field)
    root = schema if root is None else root
    def child(item, rule, path=field):
        validate(item, rule, path, root=root, depth=depth + 1)
    if "$ref" in schema:
        child(value, root["$defs"][schema["$ref"][8:]])
    for name in ("anyOf", "oneOf", "allOf"):
        if name in schema:
            successes = 0
            for option in schema[name]:
                try:
                    child(value, option)
                    successes += 1
                except ContractError:
                    pass
            if ((name == "anyOf" and successes == 0) or (name == "oneOf" and successes != 1)
                    or (name == "allOf" and successes != len(schema[name]))):
                raise ContractError(f"value does not satisfy {name}", field)
    def equal(first, second):
        return type(first) is type(second) and first == second
    if "const" in schema and not equal(value, schema["const"]):
        raise ContractError("unexpected constant", field)
    if "enum" in schema and not any(equal(value, option) for option in schema["enum"]):
        raise ContractError("unsupported value", field)
    actual = {dict: "object", list: "array", str: "string", int: "integer",
              float: "number", bool: "boolean", type(None): "null"}.get(type(value))
    types = schema.get("type", list(TYPES))
    types = [types] if isinstance(types, str) else types
    if actual not in types and not (actual == "integer" and "number" in types):
        raise ContractError(f"expected {types}", field)
    if actual == "object":
        for key in schema.get("required", []):
            if key not in value:
                raise ContractError("required field is missing", pointer(field, key))
        for key, item in value.items():
            rule = schema.get("properties", {}).get(key, schema.get("additionalProperties", True))
            child(item, rule, pointer(field, key))
    if actual == "array":
        if not schema.get("minItems", 0) <= len(value) <= schema.get("maxItems", math.inf):
            raise ContractError("invalid array length", field)
        if schema.get("uniqueItems") and len({json.dumps(x, sort_keys=True) for x in value}) != len(value):
            raise ContractError("duplicate array items", field)
        for index, item in enumerate(value):
            child(item, schema.get("items", True), pointer(field, index))
    if actual == "string":
        if schema.get("format") == "project-path":
            from ..capabilities.operation_data import safe_path
            safe_path(value, field)
        if not schema.get("minLength", 0) <= len(value) <= schema.get("maxLength", math.inf):
            raise ContractError("invalid string length", field)
        if "pattern" in schema and re.search(schema["pattern"], value) is None:
            raise ContractError("string does not match pattern", field)
    if actual in {"integer", "number"}:
        if not math.isfinite(value) or not schema.get("minimum", -math.inf) <= value <= schema.get("maximum", math.inf):
            raise ContractError("number is outside the admitted range", field)
