"""Dependency-free shapes shared by operation schema declarations."""


def obj(properties: dict, optional: tuple[str, ...] = ()) -> dict:
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

ISSUE_RESULT_TYPES = frozenset(
    {
        "concorde-agent-stage-result",
        "concorde-main-stage-result",
        "concorde-review-stage-result",
        "concorde-topology-author-result",
        "concorde-review-result",
    }
)
VERSION_FOUR_TYPES = frozenset(
    {
        "concorde-agent-stage-context",
        "concorde-main-stage-context",
        "concorde-review-stage-context",
        "concorde-topology-author-context",
    }
)


def type_version(type_id: str) -> int:
    if type_id == "concorde-context-snapshot":
        return 6
    if type_id == "concorde-discovery-context":
        return 6
    if type_id == "concorde-main-stage-context":
        return 5
    if type_id == "concorde-issues-response":
        return 2
    if type_id in {
        "concorde-init-request",
        "concorde-configure-request",
        "concorde-configure-response",
    }:
        return 2
    if type_id.endswith("-response") and type_id not in {
        "concorde-init-response",
        "concorde-configure-response",
        "concorde-issues-response",
    }:
        return 3
    if type_id in VERSION_FOUR_TYPES:
        return 4
    if type_id in ISSUE_RESULT_TYPES:
        return 2
    return 1


def typed_schema(type_id: str) -> dict:
    return obj(
        {
            "type_id": {"const": type_id},
            "schema_version": {"type": "integer", "const": type_version(type_id)},
            "data": {"$ref": type_id},
        }
    )
