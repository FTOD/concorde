"""Protocol 12 document metadata (schema 3): closed shapes of every declaration record.

A registered reading document and its ``.md.json`` companion are one document. This module checks
the companion's shape and returns every problem it finds, attributed to a check identity; the
project-level loader decides what a problem means for the graph. Nothing here reads a file.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from .repository_base import IDENTITY, METADATA_SCHEMA, SpecError, digest, is_identity
from .typed_data import safe_path

TOP_FIELDS = {"schema_version", "document", "defines", "relations"}
MODULE_FIELDS = ("title", "owns", "contains", "uses", "includes", "participates")
RELATION_TYPES = (
    "owns",
    "defines",
    "contains",
    "uses",
    "includes",
    "binds",
    "imports",
    "narrows",
    "supersedes",
    "contrasts",
    "relates",
    "participates",
    "verifies",
)
METADATA_RELATIONS = {
    "narrows": {"type", "source", "target"},
    "supersedes": {"type", "source", "target"},
    "contrasts": {"type", "source", "target", "reason"},
    "relates": {"type", "source", "verb", "target"},
}


def metadata_path(reading_path: str) -> str:
    """Exact companion name; never inspect a directory or follow a prose link."""
    safe_path(reading_path)
    if not reading_path.endswith(".md"):
        raise SpecError(
            f"reading source must be Markdown: {reading_path}",
            "invalid_spec",
            reading_path,
        )
    return reading_path + ".json"


@dataclass(frozen=True)
class SourceMember:
    path: str
    role: Literal["reading", "metadata"]
    content: bytes

    @property
    def digest(self) -> str:
        return digest(self.content)


@dataclass(frozen=True)
class DocumentUnit:
    """One registered document: both members, its identity, owner and role."""

    document_id: str
    owner: str
    role: str | None
    reading: SourceMember
    metadata: SourceMember
    value: Any

    @property
    def declarations(self) -> Any:
        from .typed_data import decode

        # A caller cannot mutate the admitted bytes or another caller's declaration view.
        return decode(self.metadata.content.decode("utf-8"))

    @property
    def sources(self) -> tuple[SourceMember, ...]:
        return tuple(
            sorted((self.reading, self.metadata), key=lambda member: member.path)
        )


def _is_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _shape(
    value: Any, required: set[str], optional: set[str] = frozenset()
) -> str | None:
    if not isinstance(value, dict):
        return "expected an object"
    missing = required - value.keys()
    unknown = value.keys() - required - optional
    if missing or unknown:
        return f"missing fields {sorted(missing)}, unknown fields {sorted(unknown)}"
    return None


def _path_list(value: Any, *, nonempty: bool) -> str | None:
    if not isinstance(value, list) or (nonempty and not value):
        return "expected a " + ("nonempty " if nonempty else "") + "array of paths"
    if len(set(map(str, value))) != len(value):
        return "paths must be unique"
    for entry in value:
        if not isinstance(entry, str) or entry == "/" or entry.endswith("//"):
            return f"invalid path literal: {entry!r}"
        try:
            safe_path(entry[:-1] if entry.endswith("/") else entry)
        except ValueError:
            return f"invalid path literal: {entry!r}"
    return None


def metadata_problems(value: Any, *, entry: bool) -> list[tuple[str, str]]:
    """Every schema-3 problem of one metadata member as (check identity, message)."""
    return envelope_problems(value, entry=entry) + declaration_problems(value)


def envelope_problems(value: Any, *, entry: bool) -> list[tuple[str, str]]:
    """Problems of the metadata envelope: top-level fields, version, document record, module block presence.

    An envelope problem makes the document's identity, owner or role untrustworthy.
    """
    problems: list[tuple[str, str]] = []
    if not isinstance(value, dict):
        return [("CHK.document.schema", "metadata must be a JSON object")]
    unknown = value.keys() - TOP_FIELDS - {"module", "extensions"}
    missing = TOP_FIELDS - value.keys()
    if unknown or missing:
        problems.append(
            (
                "CHK.document.schema",
                f"metadata fields: missing {sorted(missing)}, unknown {sorted(unknown)}",
            )
        )
    if (
        type(value.get("schema_version")) is not int
        or value.get("schema_version") != METADATA_SCHEMA
    ):
        problems.append(("CHK.document.schema", "schema_version must be the integer 3"))
    document = value.get("document")
    shape = _shape(document, {"id", "owner", "role"})
    if shape:
        problems.append(("CHK.document.schema", f"document: {shape}"))
    if isinstance(document, dict):
        if "role" not in document or document.get("role") not in {
            "module",
            "implementation",
        }:
            problems.append(
                (
                    "CHK.document.role",
                    "document.role must be exactly module or implementation",
                )
            )
        for key in ("id", "owner"):
            if key in document and not is_identity(document[key]):
                problems.append(
                    ("CHK.node.id", f"document.{key} is not a stable identity")
                )
    if entry and "module" not in value:
        problems.append(
            ("CHK.document.entry", "the entry's metadata requires the module block")
        )
    if not entry and "module" in value:
        problems.append(
            ("CHK.document.entry", "only the entry's metadata has a module block")
        )
    for name in ("defines", "relations"):
        if name in value and not isinstance(value[name], list):
            problems.append(("CHK.document.schema", f"{name} must be an array"))
    return problems


def declaration_problems(value: Any) -> list[tuple[str, str]]:
    """Problems of the declaration records: the module block, defines, relations and extensions."""
    if not isinstance(value, dict):
        return []
    problems: list[tuple[str, str]] = []
    if "module" in value:
        problems.extend(module_block_problems(value["module"]))
    for record in (
        value.get("defines", []) if isinstance(value.get("defines"), list) else []
    ):
        problems.extend(define_problems(record))
    for record in (
        value.get("relations", []) if isinstance(value.get("relations"), list) else []
    ):
        problems.extend(relation_problems(record))
    if "extensions" in value:
        extensions = value["extensions"]
        if not isinstance(extensions, dict) or any(
            not is_identity(k) for k in extensions
        ):
            problems.append(
                (
                    "CHK.document.schema",
                    "extensions must be an object keyed by stable names",
                )
            )
    return problems


def define_problems(record: Any) -> list[tuple[str, str]]:
    if not isinstance(record, dict):
        return [("CHK.document.schema", "a defines record must be an object")]
    kind = record.get("type")
    if kind not in {"concept", "realization"}:
        return [
            (
                "CHK.node.type",
                f"defines record type must be concept or realization: {kind!r}",
            )
        ]
    problems = []
    if kind == "concept":
        shape = _shape(
            record, {"id", "type", "title", "meaning"}, {"retired", "external_conflict"}
        )
    else:
        shape = _shape(
            record, {"id", "type", "title", "meaning", "entries"}, {"pending"}
        )
    if shape:
        problems.append(
            ("CHK.document.schema", f"{kind} {record.get('id')!r}: {shape}")
        )
    if not is_identity(record.get("id")):
        problems.append(
            ("CHK.node.id", f"invalid {kind} identity: {record.get('id')!r}")
        )
    if "title" in record and not _is_text(record["title"]):
        problems.append(
            ("CHK.node.title", f"{kind} {record.get('id')} requires a nonempty title")
        )
    if "meaning" in record and not isinstance(record["meaning"], str):
        problems.append(
            ("CHK.node.meaning", f"{kind} {record.get('id')} meaning must be an anchor")
        )
    if kind == "concept":
        if "retired" in record and (
            _shape(record["retired"], {"reason"})
            or not _is_text(record["retired"].get("reason"))
        ):
            problems.append(
                (
                    "CHK.concept.retired",
                    f"concept {record.get('id')} retired requires a nonempty reason",
                )
            )
        if "external_conflict" in record and not _is_text(record["external_conflict"]):
            problems.append(
                (
                    "CHK.document.schema",
                    f"concept {record.get('id')} external_conflict must be prose",
                )
            )
    else:
        entries = _path_list(record.get("entries"), nonempty=True)
        if entries:
            problems.append(
                (
                    "CHK.document.schema",
                    f"realization {record.get('id')} entries: {entries}",
                )
            )
        if "pending" in record:
            pending = _path_list(record["pending"], nonempty=False)
            if pending:
                problems.append(
                    (
                        "CHK.document.schema",
                        f"realization {record.get('id')} pending: {pending}",
                    )
                )
    return problems


def relation_problems(record: Any) -> list[tuple[str, str]]:
    if not isinstance(record, dict):
        return [("CHK.document.schema", "a relations record must be an object")]
    kind = record.get("type")
    if kind not in RELATION_TYPES:
        return [("CHK.relation.type", f"unregistered relation type: {kind!r}")]
    if kind not in METADATA_RELATIONS:
        return [
            (
                "CHK.relation.site",
                f"a {kind} relation is not declared in document metadata",
            )
        ]
    shape = _shape(record, METADATA_RELATIONS[kind])
    if shape:
        return [("CHK.document.schema", f"{kind} relation: {shape}")]
    problems = []
    for key in ("source", "target"):
        if not is_identity(record[key]):
            problems.append(
                ("CHK.relation.endpoints", f"{kind} {key} is not a stable identity")
            )
    if kind == "relates" and not _is_text(record["verb"]):
        problems.append(("CHK.relates.verb", "relates requires a nonempty verb"))
    if kind == "contrasts" and not _is_text(record["reason"]):
        problems.append(("CHK.contrasts.once", "contrasts requires a nonempty reason"))
    return problems


def module_block_problems(block: Any) -> list[tuple[str, str]]:
    shape = _shape(block, set(MODULE_FIELDS))
    if shape:
        return [("CHK.document.schema", f"module block: {shape}")]
    problems = []
    if not _is_text(block["title"]):
        problems.append(
            ("CHK.node.title", "the module block requires a nonempty title")
        )
    owns = block["owns"]
    if (
        not isinstance(owns, list)
        or not owns
        or any(not isinstance(path, str) for path in owns)
        or len(set(owns)) != len(owns)
    ):
        problems.append(
            (
                "CHK.document.schema",
                "owns must be a nonempty array of unique reading paths",
            )
        )
    for name in ("contains", "uses"):
        items = block[name]
        if not isinstance(items, list):
            problems.append(("CHK.document.schema", f"{name} must be an array"))
            continue
        for item in items:
            shape = _shape(item, {"target", "meaning"}, {"relies_on"})
            if shape:
                problems.append(("CHK.document.schema", f"{name} entry: {shape}"))
                continue
            if not is_identity(item["target"]):
                problems.append(
                    ("CHK.relation.endpoints", f"{name} target is not an identity")
                )
            if not isinstance(item["meaning"], str):
                problems.append(
                    ("CHK.relation.meaning", f"{name} meaning must be an anchor")
                )
            if "relies_on" in item and (
                not isinstance(item["relies_on"], list)
                or not item["relies_on"]
                or any(not is_identity(x) for x in item["relies_on"])
                or len(set(map(str, item["relies_on"]))) != len(item["relies_on"])
            ):
                problems.append(
                    (
                        "CHK.document.schema",
                        f"{name} relies_on must be a nonempty array of identities",
                    )
                )
    if not isinstance(block["includes"], list):
        problems.append(("CHK.document.schema", "includes must be an array"))
    else:
        for item in block["includes"]:
            shape = _shape(item, {"kind", "target", "reason"})
            if shape:
                problems.append(("CHK.document.schema", f"includes entry: {shape}"))
                continue
            if item["kind"] not in {"module", "document", "external"}:
                problems.append(
                    (
                        "CHK.document.schema",
                        f"includes kind must be module, document or external: {item['kind']!r}",
                    )
                )
            elif item["kind"] == "external":
                if _path_list([item["target"]], nonempty=True):
                    problems.append(
                        (
                            "CHK.relation.endpoints",
                            f"external include target is not a path: {item['target']!r}",
                        )
                    )
            elif not is_identity(item["target"]):
                problems.append(
                    ("CHK.relation.endpoints", "includes target is not an identity")
                )
            if not _is_text(item["reason"]):
                problems.append(
                    (
                        "CHK.includes.reason",
                        f"includes {item['target']!r} requires a nonempty reason",
                    )
                )
    if not isinstance(block["participates"], list):
        problems.append(("CHK.document.schema", "participates must be an array"))
    else:
        for item in block["participates"]:
            shape = _shape(item, {"contract", "version", "role", "peer", "meaning"})
            if shape:
                problems.append(("CHK.document.schema", f"participates entry: {shape}"))
                continue
            if type(item["version"]) is not int or item["version"] < 1:
                problems.append(
                    (
                        "CHK.participates.version",
                        "participation version must be a positive integer",
                    )
                )
            if item["role"] not in {"provided", "required"}:
                problems.append(
                    (
                        "CHK.document.schema",
                        "participation role must be provided or required",
                    )
                )
            if item["peer"] != "external" and not is_identity(item["peer"]):
                problems.append(
                    (
                        "CHK.relation.endpoints",
                        "participation peer must be a Module or external",
                    )
                )
            if not is_identity(item["contract"]):
                problems.append(
                    (
                        "CHK.relation.endpoints",
                        "participation contract is not an identity",
                    )
                )
            if not isinstance(item["meaning"], str):
                problems.append(
                    ("CHK.relation.meaning", "participation meaning must be an anchor")
                )
    return problems


__all__ = [
    "DocumentUnit",
    "IDENTITY",
    "METADATA_RELATIONS",
    "MODULE_FIELDS",
    "RELATION_TYPES",
    "SourceMember",
    "metadata_path",
    "metadata_problems",
]
