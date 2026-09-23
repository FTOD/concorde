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

# Version of a resolved SpecContext record; 2 records the selecting relation of every source.
CONTEXT_SCHEMA = 2
# One relation that selected a context source. ``owns``, ``contains`` and ``uses`` name a Module;
# ``includes`` also states whether it included a Module or one document; ``shares`` names another
# Module that binds a file in a code-writing reader's ImplementationScope, with those files.
SELECTION_REASON = {
    "anyOf": [
        obj({"relation": {"enum": ["owns", "contains", "uses"]}, "id": STRING}),
        obj(
            {
                "relation": {"const": "includes"},
                "kind": {"enum": ["module", "document"]},
                "id": STRING,
            }
        ),
        obj(
            {
                "relation": {"const": "shares"},
                "id": STRING,
                "files": array(PATH, unique=True),
            }
        ),
    ]
}

ISSUE_RESULT_TYPES = frozenset(
    {
        "concorde-agent-stage-result",
        "concorde-review-stage-result",
        "concorde-review-result",
    }
)
# Stage contexts embed the context snapshot; version 5 carries snapshot 7, whose Spec context
# records the selecting relation of every source.
STAGE_CONTEXT_TYPES = frozenset(
    {
        "concorde-agent-stage-context",
        "concorde-review-stage-context",
    }
)


def type_version(type_id: str) -> int:
    # Explicit-target review and current-evidence repair replace the former entry contracts.
    # Never reinterpret a version-1 request as one of these new requests.
    if type_id in {
        "concorde-spec-review-request",
        "concorde-code-review-request",
        "concorde-tasks-request",
        "concorde-operation-configuration",
    }:
        return 2
    # Issue decisions no longer include the automatic-authoring `specify` selector.
    if type_id == "concorde-agent-stage-result":
        return 3
    if type_id == "concorde-context-snapshot":
        return 7
    if type_id == "concorde-issues-response":
        return 2
    # Version 3 adds the explicit `run_in_primary` opt-in.
    if type_id in {"concorde-init-request", "concorde-configure-request"}:
        return 3
    if type_id == "concorde-configure-response":
        return 2
    if type_id.endswith("-response") and type_id not in {
        "concorde-init-response",
        "concorde-configure-response",
        "concorde-issues-response",
    }:
        return 3
    if type_id in STAGE_CONTEXT_TYPES:
        return 5
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
