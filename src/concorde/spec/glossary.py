"""Protocol 15 project glossary: the one file of concept entries (``protocol/format.md#glossary``).

The root Module's ``module`` block declares the glossary's path. Each entry is one concept: its
identity, title, owning Module, one-sentence definition and the reference to its explanation in a
document of the owner, plus the relations whose source is the concept. This module checks the
file's shape, reads its entries and compares two revisions entry by entry, which is how a harness
holds a task to the entries its bound Modules own. Nothing here reads a file.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from .repository_base import Concept, is_identity
from .typed_data import decode

GLOSSARY_SCHEMA = 1
ENTRY_REQUIRED = frozenset({"id", "title", "owner", "definition", "explanation"})
ENTRY_OPTIONAL = frozenset(
    {"retired", "external_conflict", "narrows", "supersedes", "contrasts", "relates"}
)
# A term link inside a definition addresses another entry of the same file by fragment alone.
DEFINITION_LINK = re.compile(r"\[([^\]]*)\]\((#[^\s)]*)\)")


def _is_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def definition_links(definition: str) -> list[str]:
    """The fragments of every link in a definition, without the leading ``#``."""
    return [match.group(2)[1:] for match in DEFINITION_LINK.finditer(definition)]


def plain_definition(definition: str) -> str:
    """A definition with its term links reduced to their text, as a reader without links sees it."""
    return DEFINITION_LINK.sub(lambda match: match.group(1), definition)


def problems(value: Any) -> list[tuple[str, str, str | None]]:
    """Every shape problem of a decoded glossary as (check, message, subject)."""
    if not isinstance(value, dict) or set(value) != {"schema_version", "concepts"}:
        return [
            (
                "CHK.glossary.schema",
                'the glossary must be an object with exactly "schema_version" and "concepts"',
                None,
            )
        ]
    found: list[tuple[str, str, str | None]] = []
    if (
        type(value["schema_version"]) is not int
        or value["schema_version"] != GLOSSARY_SCHEMA
    ):
        found.append(
            (
                "CHK.glossary.schema",
                f"the glossary schema_version must be the integer {GLOSSARY_SCHEMA}",
                None,
            )
        )
    entries = value["concepts"]
    if not isinstance(entries, list):
        return found + [("CHK.glossary.schema", "concepts must be an array", None)]
    identities = [entry.get("id") for entry in entries if isinstance(entry, dict)]
    if all(isinstance(item, str) for item in identities) and identities != sorted(
        identities
    ):
        found.append(
            (
                "CHK.glossary.schema",
                "the glossary's concepts are sorted by id, so that concurrent additions rarely "
                "touch the same lines",
                None,
            )
        )
    for entry in entries:
        found.extend(entry_problems(entry))
    return found


def entry_problems(entry: Any) -> list[tuple[str, str, str | None]]:
    """Shape problems of one glossary entry."""
    if not isinstance(entry, dict):
        return [("CHK.glossary.schema", "a glossary entry must be an object", None)]
    identity = entry.get("id")
    subject = identity if isinstance(identity, str) else None
    found: list[tuple[str, str, str | None]] = []
    missing = ENTRY_REQUIRED - entry.keys()
    unknown = entry.keys() - ENTRY_REQUIRED - ENTRY_OPTIONAL
    if missing or unknown:
        found.append(
            (
                "CHK.glossary.schema",
                f"glossary entry {identity!r}: missing fields {sorted(missing)}, unknown "
                f"fields {sorted(unknown)}",
                subject,
            )
        )
    if not is_identity(identity) or not str(identity).startswith("concept."):
        found.append(
            (
                "CHK.node.id",
                f"glossary entry identity {identity!r} must be a stable identity beginning "
                "concept.",
                subject,
            )
        )
    if "title" in entry and not _is_text(entry["title"]):
        found.append(
            ("CHK.node.title", f"concept {identity} requires a nonempty title", subject)
        )
    if "owner" in entry and not is_identity(entry["owner"]):
        found.append(
            (
                "CHK.glossary.schema",
                f"concept {identity} owner must be a Module identity",
                subject,
            )
        )
    if "definition" in entry and not isinstance(entry["definition"], str):
        found.append(
            (
                "CHK.concept.definition",
                f"concept {identity} definition must be a sentence",
                subject,
            )
        )
    explanation = entry.get("explanation")
    if "explanation" in entry and (
        not isinstance(explanation, str)
        or explanation.count("#") != 1
        or not explanation.split("#")[0]
        or not explanation.split("#")[1]
    ):
        found.append(
            (
                "CHK.node.meaning",
                f"concept {identity} explanation must be <reading path>#<anchor>, not "
                f"{explanation!r}",
                subject,
            )
        )
    if "retired" in entry and (
        not isinstance(entry["retired"], dict)
        or set(entry["retired"]) != {"reason"}
        or not _is_text(entry["retired"].get("reason"))
    ):
        found.append(
            (
                "CHK.concept.retired",
                f"concept {identity} retired requires exactly a nonempty reason",
                subject,
            )
        )
    if "external_conflict" in entry and not _is_text(entry["external_conflict"]):
        found.append(
            (
                "CHK.glossary.schema",
                f"concept {identity} external_conflict must be prose",
                subject,
            )
        )
    if "narrows" in entry and (
        not isinstance(entry["narrows"], list)
        or not entry["narrows"]
        or any(not is_identity(item) for item in entry["narrows"])
        or len(set(map(str, entry["narrows"]))) != len(entry["narrows"])
    ):
        found.append(
            (
                "CHK.glossary.schema",
                f"concept {identity} narrows must be a nonempty array of distinct identities",
                subject,
            )
        )
    if "supersedes" in entry and not is_identity(entry["supersedes"]):
        found.append(
            (
                "CHK.glossary.schema",
                f"concept {identity} supersedes must be one concept identity",
                subject,
            )
        )
    for name, fields, text in (
        ("contrasts", {"target", "reason"}, "reason"),
        ("relates", {"verb", "target"}, "verb"),
    ):
        if name not in entry:
            continue
        items = entry[name]
        if not isinstance(items, list) or not items:
            found.append(
                (
                    "CHK.glossary.schema",
                    f"concept {identity} {name} must be a nonempty array",
                    subject,
                )
            )
            continue
        for item in items:
            if not isinstance(item, dict) or set(item) != fields:
                found.append(
                    (
                        "CHK.glossary.schema",
                        f"concept {identity} {name} entries have exactly {sorted(fields)}",
                        subject,
                    )
                )
                continue
            if not is_identity(item["target"]):
                found.append(
                    (
                        "CHK.relation.endpoints",
                        f"concept {identity} {name} target is not an identity",
                        subject,
                    )
                )
            if not _is_text(item[text]):
                found.append(
                    (
                        "CHK.relates.verb"
                        if name == "relates"
                        else "CHK.contrasts.once",
                        f"concept {identity} {name} requires a nonempty {text}",
                        subject,
                    )
                )
    return found


def concept(entry: dict, glossary_path: str) -> Concept:
    """A well-formed enough entry as the concept node the repository serves."""
    explanation = (
        entry.get("explanation") if isinstance(entry.get("explanation"), str) else ""
    )
    document, _, anchor = explanation.partition("#")
    definition = (
        entry.get("definition") if isinstance(entry.get("definition"), str) else None
    )
    return Concept(
        entry["id"],
        entry.get("title") if isinstance(entry.get("title"), str) else "",
        entry.get("owner") if isinstance(entry.get("owner"), str) else "",
        document,
        anchor,
        definition,
        entry.get("retired") if isinstance(entry.get("retired"), dict) else None,
        entry.get("external_conflict")
        if isinstance(entry.get("external_conflict"), str)
        else None,
        glossary_path,
        tuple(item for item in entry.get("narrows", ()) if isinstance(item, str))
        if isinstance(entry.get("narrows"), list)
        else (),
        entry.get("supersedes") if isinstance(entry.get("supersedes"), str) else None,
        tuple(
            item
            for item in entry.get("contrasts", ())
            if isinstance(item, dict) and isinstance(item.get("target"), str)
        )
        if isinstance(entry.get("contrasts"), list)
        else (),
        tuple(
            item
            for item in entry.get("relates", ())
            if isinstance(item, dict) and isinstance(item.get("target"), str)
        )
        if isinstance(entry.get("relates"), list)
        else (),
        tuple(definition_links(definition)) if definition else (),
    )


def entries(raw: bytes) -> dict[str, dict]:
    """The entries of one glossary revision by identity; malformed entries are skipped."""
    value = decode(raw.decode("utf-8"))
    items = value.get("concepts") if isinstance(value, dict) else None
    if not isinstance(items, list):
        raise ValueError("the glossary has no concepts array")
    return {
        item["id"]: item
        for item in items
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }


@dataclass(frozen=True)
class EntryChange:
    """One entry that differs between two glossary revisions, with its owner in each."""

    id: str
    before: str | None
    after: str | None

    @property
    def owners(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys(x for x in (self.before, self.after) if x))


def changed_entries(before: bytes | None, after: bytes | None) -> list[EntryChange]:
    """Every entry added, removed or changed between two revisions of the glossary.

    A missing revision has no entries; an unreadable one raises ``ValueError``, since a harness
    cannot hold a task to its entries without reading them.
    """
    old = entries(before) if before is not None else {}
    new = entries(after) if after is not None else {}
    changes = []
    for identity in sorted(old.keys() | new.keys()):
        if old.get(identity) == new.get(identity):
            continue

        def owner(item):
            return item.get("owner") if isinstance(item, dict) else None

        changes.append(
            EntryChange(identity, owner(old.get(identity)), owner(new.get(identity)))
        )
    return changes


def ownership_violations(
    before: bytes | None, after: bytes | None, modules
) -> list[str]:
    """Entries a task bound to ``modules`` changed although another Module owns them.

    Each violation names the entry and the owners it had before and after the change, so the
    reader can tell an edit of a foreign entry from an entry moved to or from another owner.
    """
    allowed = set(modules)
    violations = []
    for change in changed_entries(before, after):
        foreign = [owner for owner in change.owners if owner not in allowed]
        if foreign or not change.owners:
            violations.append(
                f"{change.id} (owner before: {change.before or 'none'}, after: "
                f"{change.after or 'none'})"
            )
    return violations


__all__ = [
    "DEFINITION_LINK",
    "EntryChange",
    "GLOSSARY_SCHEMA",
    "changed_entries",
    "concept",
    "definition_links",
    "entries",
    "entry_problems",
    "ownership_violations",
    "plain_definition",
    "problems",
]
