"""Dependency-free shapes shared by capability schema declarations."""

def obj(properties: dict, optional: tuple[str, ...] = ()) -> dict:
    return {"type": "object", "properties": properties,
            "required": [key for key in properties if key not in optional], "additionalProperties": False}

def array(items: dict, *, unique: bool = False) -> dict:
    return {"type": "array", "items": items, **({"uniqueItems": True} if unique else {})}

STRING = {"type": "string", "minLength": 1}
PATH = {**STRING, "format": "project-path"}
DIGEST = {**STRING, "pattern": r"^sha256:[0-9a-f]{64}$"}
ARTIFACT = obj({"id": STRING, "path": PATH, "digest": DIGEST})

VERSION_TWO_TYPES = frozenset({"concorde-context-snapshot", "concorde-discovery-context",
    "concorde-agent-stage-context", "concorde-main-stage-context", "concorde-review-stage-context",
    "concorde-topology-author-context"})

def type_version(type_id: str) -> int:
    return 2 if type_id in VERSION_TWO_TYPES else 1

def typed_schema(type_id: str) -> dict:
    return obj({"type_id": {"const": type_id}, "schema_version": {"type": "integer", "const": type_version(type_id)},
                "data": {"$ref": type_id}})
