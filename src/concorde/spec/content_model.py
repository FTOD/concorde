"""Protocol 7 document-unit primitives, not yet wired into the active Profile 13 runtime.

A registered reading document and its deterministic metadata companion are one owned unit.
Reading is a subset of content, not a summary generated from an inventory. Machine records point
at local readable meaning instead of copying it. This module admits one unit, not a project:
registry-wide identity, composition, binding and context checks remain a separate responsibility.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from .repository import HEADING, IDENTITY, check_entry, digest, read_file, walk_lines
from .typed_data import decode, safe_path

METADATA_VERSION = 1
READING_SECTIONS = ("Purpose", "Usage", "Design", "Relationships")
RETIRED_FENCES = frozenset({"concorde-document", "concorde-entities", "concorde-dependencies",
                           "concorde-contract-binding"})
_OLD_PARTS = frozenset({"Usage & Contract", "Architecture & Realization"})
_HTML_ANCHOR = re.compile(r'^\s*<a id="([^"]+)"></a>\s*$')
_HEADING_ANCHOR = re.compile(r"\s+\{#([^{}]+)\}\s*$")
_DEFINITION = re.compile(r"^((?:req|scenario)\.[a-z0-9]+(?:[.-][a-z0-9-]+)*)\s+[—–-]\s+\S")


class ContentModelError(ValueError):
    """A source-local admission error; never a claim about semantic completeness."""

    def __init__(self, path: str, message: str):
        self.path = path
        super().__init__(f"{path}: {message}")


def metadata_path(reading_path: str) -> str:
    """Exact companion name; never inspect a directory or follow a prose link."""
    safe_path(reading_path)
    if not reading_path.endswith(".md") or reading_path.startswith((".concorde/", ".git/")):
        raise ContentModelError(reading_path, "reading source must be durable Markdown")
    return reading_path + ".json"


def _identity(value: Any, path: str) -> str:
    if not isinstance(value, str) or not IDENTITY.fullmatch(value):
        raise ContentModelError(path, f"invalid stable identity: {value!r}")
    return value


def _object(value: Any, required: set[str], optional: set[str], path: str) -> dict:
    if not isinstance(value, dict) or not required <= value.keys() or value.keys() - required - optional:
        raise ContentModelError(path, f"expected fields {sorted(required)}, optional {sorted(optional)}")
    return value


def _text(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContentModelError(path, "expected nonempty text")
    return value


def _array(value: Any, path: str) -> list:
    if not isinstance(value, list):
        raise ContentModelError(path, "expected an array")
    return value


def _entries(value: Any, path: str, *, nonempty: bool = False) -> tuple[str, ...]:
    values = _array(value, path)
    if nonempty and not values:
        raise ContentModelError(path, "expected a nonempty entry array")
    result = []
    for entry in values:
        try:
            check_entry(entry)
        except (TypeError, ValueError, AttributeError) as error:
            raise ContentModelError(path, f"invalid implementation entry: {entry!r}") from error
        if entry in result:
            raise ContentModelError(path, f"duplicate implementation entry: {entry}")
        result.append(entry)
    return tuple(result)


@dataclass(frozen=True)
class SourceMember:
    path: str
    role: Literal["reading", "metadata"]
    content: bytes

    @property
    def digest(self) -> str:
        return digest(self.content)


@dataclass(frozen=True)
class ReadingMeaning:
    """A local readable explanation. Its text is derived from the reading source, never stored twice."""

    anchor: str
    text: str
    line: int


@dataclass(frozen=True)
class DocumentUnit:
    document_id: str
    owner: str
    reading: SourceMember
    metadata: SourceMember
    meanings: tuple[ReadingMeaning, ...]

    @property
    def declarations(self) -> dict:
        # A caller cannot mutate the admitted bytes or another caller's declaration view.
        return decode(self.metadata.content.decode("utf-8"))

    @property
    def sources(self) -> tuple[SourceMember, ...]:
        return tuple(sorted((self.reading, self.metadata), key=lambda member: member.path))

    @property
    def identity(self) -> str:
        """Bind identity, ownership, member roles, paths and exact bytes, including metadata edits."""
        return digest({"document_id": self.document_id, "owner": self.owner,
                       "sources": [{"path": s.path, "role": s.role, "digest": s.digest}
                                   for s in self.sources]})

    def meaning(self, reference: str) -> ReadingMeaning:
        if not isinstance(reference, str) or not reference.startswith("#"):
            raise ContentModelError(self.metadata.path, "meaning must be a local reading anchor")
        anchor = reference[1:]
        _identity(anchor, self.metadata.path)
        for meaning in self.meanings:
            if meaning.anchor == anchor:
                if not meaning.text.strip():
                    raise ContentModelError(self.reading.path, f"empty reading meaning: {reference}")
                return meaning
        raise ContentModelError(self.reading.path, f"missing reading meaning: {reference}")


def reading_meanings(text: str, path: str) -> tuple[ReadingMeaning, ...]:
    """Resolve explicit reading anchors outside fences, with bounded local section bodies.

    A heading anchor extends to the next heading at the same or a higher level. A standalone
    anchor extends to the next heading. Either ends at the next explicit anchor, so an empty
    explanation cannot borrow a later declaration's text. Fenced examples create no anchors.
    """
    lines = walk_lines(text)
    headings: dict[int, int] = {}
    anchors: list[tuple[str, int, int | None]] = []
    seen: set[str] = set()
    for number, kind, line in lines:
        if kind != "prose":
            continue
        heading = HEADING.match(line)
        explicit = _HEADING_ANCHOR.search(heading.group(2)) if heading else None
        definition = _DEFINITION.match(heading.group(2)) if heading else None
        html = _HTML_ANCHOR.fullmatch(line)
        if heading:
            headings[number] = len(heading.group(1))
        # A requirement/scenario heading cannot be redirected to a different definition ID.
        if explicit and definition and explicit.group(1) != definition.group(1):
            raise ContentModelError(path, f"definition anchor differs from its identity at line {number}")
        anchor = (explicit.group(1) if explicit else definition.group(1) if definition
                  else html.group(1) if html else None)
        if anchor is None:
            continue
        _identity(anchor, path)
        if anchor in seen:
            raise ContentModelError(path, f"duplicate reading anchor: {anchor}")
        seen.add(anchor)
        anchors.append((anchor, number, len(heading.group(1)) if heading else None))
    result = []
    for index, (anchor, start, level) in enumerate(anchors):
        next_anchor = anchors[index + 1][1] if index + 1 < len(anchors) else len(lines) + 1
        end = min([next_anchor, *(number for number, next_level in headings.items()
                                 if number > start and (level is None or next_level <= level))])
        # Only readable text can supply the meaning. A bare code block or heading is not prose.
        body = "\n".join(line for number, kind, line in lines
                         if start < number < end and kind == "prose" and number not in headings)
        result.append(ReadingMeaning(anchor, body.strip(), start))
    return tuple(result)


def reading_problems(text: str, *, primary: bool) -> tuple[str, ...]:
    """Reading structure and forbidden inventory fences, not semantic sufficiency or site layout."""
    lines = walk_lines(text)
    headings = [(number, len(m.group(1)), m.group(2)) for number, kind, line in lines
                if kind == "prose" and (m := HEADING.match(line))]
    problems = []
    for _, kind, line in lines:
        if kind == "fence-open":
            language = re.sub(r"^ {0,3}(?:`{3,}|~{3,})\s*", "", line).strip()
            if language in RETIRED_FENCES:
                problems.append(f"{language} is metadata, not a reading block")
    if any(title in _OLD_PARTS for _, _, title in headings):
        problems.append("retired two-part headings require explicit migration")
    if primary:
        top = [(number, title) for number, level, title in headings if level == 2]
        if [title for _, title in top[:4]] != list(READING_SECTIONS) or any(
                sum(title == required for _, _, title in headings) != 1 for required in READING_SECTIONS):
            problems.append("reading entry must start with unique level-2 Purpose, Usage, Design, Relationships")
        if any(title == "Entities" for _, _, title in headings):
            problems.append("explain entity meaning in Design or Relationships, not an Entities inventory chapter")
        for number, title in top:
            if title not in READING_SECTIONS:
                continue
            end = next((n for n, level, _ in headings if n > number and level <= 2), len(lines) + 1)
            section = [(kind, line) for n, kind, line in lines if number < n < end]
            if not any(kind == "prose" and line.strip() and not HEADING.match(line)
                       and not _HTML_ANCHOR.fullmatch(line)
                       and not re.match(r"\s*(?:\||[-*+] |\d+[.)] )", line) for kind, line in section):
                problems.append(f"{title} requires explanatory prose")
            if title == "Purpose" and any(kind != "prose" or HEADING.match(line)
                    or re.match(r"\s*(?:\||[-*+] |\d+[.)] )", line) for kind, line in section):
                problems.append("Purpose must be plain prose without headings, lists, tables or fences")
    return tuple(problems)


def admit_document_unit(reading_path: str, reading: bytes, metadata: bytes, *,
                        expected_owner: str, primary: bool = False) -> DocumentUnit:
    """Admit an explicitly supplied pair without reading any file or following any link.

    Safe filesystem access, registry-wide uniqueness, expected provider sets, interface pairing,
    file existence and diagram entity resolution are checked by the project-level caller.
    """
    sidecar = metadata_path(reading_path)
    if not isinstance(reading, bytes) or not isinstance(metadata, bytes):
        raise ContentModelError(reading_path, "source members must be exact bytes")
    try:
        text = reading.decode("utf-8")
    except UnicodeError as error:
        raise ContentModelError(reading_path, f"invalid UTF-8: {error}") from error
    try:
        value = decode(metadata.decode("utf-8"))
    except (ValueError, UnicodeError) as error:
        raise ContentModelError(sidecar, f"invalid UTF-8 or JSON: {error}") from error
    if not text.strip():
        raise ContentModelError(reading_path, "reading source must not be empty")
    problems = reading_problems(text, primary=primary)
    if problems:
        raise ContentModelError(reading_path, "; ".join(problems))
    _object(value, {"schema_version", "document", "entities", "dependencies", "bindings"}, set(), sidecar)
    if type(value["schema_version"]) is not int or value["schema_version"] != METADATA_VERSION:
        raise ContentModelError(sidecar, "unsupported document metadata version")
    document = _object(value["document"], {"id", "owner"}, set(), sidecar)
    document_id = _identity(document["id"], sidecar)
    owner = _identity(document["owner"], sidecar)
    if owner != expected_owner:
        raise ContentModelError(sidecar, "document owner differs from registration")
    if document_id == owner:
        raise ContentModelError(sidecar, "document identity collides with Module identity")
    unit = DocumentUnit(document_id, owner, SourceMember(reading_path, "reading", reading),
                        SourceMember(sidecar, "metadata", metadata), reading_meanings(text, reading_path))
    entity_ids: set[str] = set()
    entity_titles: set[str] = set()
    entity_targets: set[str] = set()
    bound_entries: set[str] = set()
    for entity in _array(value["entities"], sidecar):
        _object(entity, {"id", "title", "kind", "meaning"}, {"files", "pending", "target_id"}, sidecar)
        entity_id = _identity(entity["id"], sidecar)
        title = _text(entity["title"], sidecar)
        _text(entity["kind"], sidecar)
        if entity_id in entity_ids or entity_id in {document_id, owner} or entity_id.startswith(("req.", "scenario.")):
            raise ContentModelError(sidecar, f"duplicate or conflicting entity identity: {entity_id}")
        if title in entity_titles:
            raise ContentModelError(sidecar, f"duplicate entity title: {title}")
        entity_ids.add(entity_id)
        entity_titles.add(title)
        if entity["meaning"] != "#" + entity_id:
            raise ContentModelError(sidecar, "entity meaning must use its stable identity anchor")
        unit.meaning(entity["meaning"])
        files = _entries(entity.get("files", []), sidecar, nonempty="files" in entity)
        pending = _entries(entity.get("pending", []), sidecar)
        if set(pending) - set(files):
            raise ContentModelError(sidecar, "pending entries must be a subset of the entity's files")
        if set(files) & bound_entries:
            raise ContentModelError(sidecar, "an implementation entry is listed by two entities")
        bound_entries.update(files)
        for entry in files:
            if entry in {reading_path, sidecar} or (entry.endswith("/") and reading_path.startswith(entry)):
                raise ContentModelError(sidecar, "implementation entry cannot bind either document member")
        if "target_id" in entity:
            target = _identity(entity["target_id"], sidecar)
            if "files" in entity or "pending" in entity or target == owner or target in entity_targets:
                raise ContentModelError(sidecar, "Module entity must be a unique non-self provider without file bindings")
            entity_targets.add(target)
    providers: set[str] = set()
    for dependency in _array(value["dependencies"], sidecar):
        _object(dependency, {"target_id", "meaning"}, set(), sidecar)
        target = _identity(dependency["target_id"], sidecar)
        if target == owner or target in providers:
            raise ContentModelError(sidecar, "duplicate or self dependency declaration")
        providers.add(target)
        unit.meaning(dependency["meaning"])
    participants: set[tuple[str, str, str]] = set()
    for binding in _array(value["bindings"], sidecar):
        _object(binding, {"id", "version", "role", "peer", "meaning"}, set(), sidecar)
        contract = _identity(binding["id"], sidecar)
        if type(binding["version"]) is not int or binding["version"] < 1:
            raise ContentModelError(sidecar, "contract version must be a positive integer")
        if not isinstance(binding["role"], str) or binding["role"] not in {"provided", "required"}:
            raise ContentModelError(sidecar, "binding role must be provided or required")
        peer = _text(binding["peer"], sidecar)
        if peer.startswith("external:"):
            _text(peer[len("external:"):], sidecar)
        else:
            _identity(peer, sidecar)
            if peer == owner:
                raise ContentModelError(sidecar, "binding peer cannot be the participant itself")
        key = (contract, binding["role"], peer)
        if key in participants:
            raise ContentModelError(sidecar, "duplicate participant/peer/role binding")
        participants.add(key)
        unit.meaning(binding["meaning"])
    return unit


def load_document_unit(root: Path, reading_path: str, *, expected_owner: str,
                       primary: bool = False) -> DocumentUnit:
    """Read exactly the explicitly selected pair, rejecting missing members and symlink aliases."""
    sidecar = metadata_path(reading_path)
    return admit_document_unit(reading_path, read_file(root, reading_path), read_file(root, sidecar),
                               expected_owner=expected_owner, primary=primary)
