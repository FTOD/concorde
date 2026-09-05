"""Dependency-free shapes shared by Operation schema declarations."""

def obj(properties: dict, optional: tuple[str, ...] = ()) -> dict:
    return {"type": "object", "properties": properties,
            "required": [key for key in properties if key not in optional], "additionalProperties": False}

def array(items: dict, *, unique: bool = False) -> dict:
    return {"type": "array", "items": items, **({"uniqueItems": True} if unique else {})}

STRING = {"type": "string", "minLength": 1}
PATH = {**STRING, "format": "project-path"}
DIGEST = {**STRING, "pattern": r"^sha256:[0-9a-f]{64}$"}
ARTIFACT = obj({"id": STRING, "path": PATH, "digest": DIGEST})

def typed_schema(type_id: str) -> dict:
    return obj({"type_id": {"const": type_id}, "schema_version": {"type": "integer", "const": 1},
                "data": {"$ref": type_id}})
