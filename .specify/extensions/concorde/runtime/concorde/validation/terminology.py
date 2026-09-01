"""Level-local terminology declarations and bounded ontology inheritance."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any

from ..model import Finding, SourceDocument


INHERITED_ONLY = "No local terminology. This level uses inherited terminology unchanged."
HEADERS = ("Term", "Meaning", "Relationships")
_HEADING = re.compile(r"^## Terminology\s*$", re.MULTILINE)
_NEXT_HEADING = re.compile(r"^## ", re.MULTILINE)
_SEPARATOR = re.compile(r"^:?-{3,}:?$")
_TERM_CELL = re.compile(r"^`([^`\n]+)`(?:\s*<br\s*/?>\s*Aliases:\s*(.+))?$", re.IGNORECASE)
_RELATIONSHIP = re.compile(r"^`([^`\n]+)`\s*→\s*`([^`\n]+)`$")
_PUNCTUATION = re.compile(r"[^\w]+", re.UNICODE)


@dataclass(frozen=True)
class ConceptRelationship:
    predicate: str
    target: str


@dataclass(frozen=True)
class Concept:
    preferred: str
    normalized: str
    meaning: str
    aliases: tuple[str, ...]
    relationships: tuple[ConceptRelationship, ...]
    defining_level: str

    @property
    def identity(self) -> str:
        return f"{self.defining_level}#{self.normalized}"

    @property
    def expressions(self) -> tuple[str, ...]:
        return (self.preferred, *self.aliases)


@dataclass(frozen=True)
class TerminologyDeclaration:
    level_id: str
    level_kind: str
    source: str
    inherited_only: bool
    concepts: tuple[Concept, ...]


@dataclass(frozen=True)
class _Level:
    identifier: str
    kind: str
    path: str
    body: str
    metadata: dict[str, Any]


def normalize_expression(value: str) -> str:
    """Return the Profile 1 comparison form without linguistic guessing."""
    normalized = unicodedata.normalize("NFKC", value).casefold().replace("_", " ")
    return " ".join(_PUNCTUATION.sub(" ", normalized).split())


def _finding(rule: str, level: _Level, message: str, remediation: str) -> Finding:
    return Finding(rule, "error", level.path, message, remediation, subject_id=level.identifier)


def _split_row(line: str) -> tuple[str, ...] | None:
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return None
    inner = stripped[1:-1]
    cells = re.split(r"(?<!\\)\|", inner)
    return tuple(cell.strip().replace(r"\|", "|") for cell in cells)


def _section(body: str) -> tuple[str | None, str | None]:
    matches = list(_HEADING.finditer(body))
    if not matches:
        return None, "missing"
    if len(matches) != 1:
        return None, "multiple"
    start = matches[0].end()
    following = _NEXT_HEADING.search(body, start)
    return body[start : following.start() if following else len(body)].strip(), None


def _parse_term_cell(cell: str) -> tuple[str, tuple[str, ...]] | None:
    match = _TERM_CELL.fullmatch(cell.strip())
    if not match or not match.group(1).strip():
        return None
    preferred = match.group(1).strip()
    raw_aliases = match.group(2)
    if raw_aliases is None:
        return preferred, ()
    aliases = tuple(item.strip() for item in re.findall(r"`([^`\n]+)`", raw_aliases) if item.strip())
    residue = re.sub(r"`[^`\n]+`", "", raw_aliases)
    if not aliases or residue.replace(",", "").strip():
        return None
    return preferred, aliases


def _parse_relationships(cell: str) -> tuple[ConceptRelationship, ...] | None:
    value = cell.strip()
    if value == "None":
        return ()
    relationships: list[ConceptRelationship] = []
    for expression in value.split(";"):
        match = _RELATIONSHIP.fullmatch(expression.strip())
        if not match or not match.group(1).strip() or not match.group(2).strip():
            return None
        relationships.append(ConceptRelationship(match.group(1).strip(), match.group(2).strip()))
    return tuple(relationships) if relationships else None


def parse_declaration(level: _Level) -> tuple[TerminologyDeclaration | None, list[Finding]]:
    section, problem = _section(level.body)
    if problem == "missing":
        return None, [
            _finding(
                "CONCORDE-ONTOLOGY-001",
                level,
                "The design has no ## Terminology section.",
                "Add the standard local terminology table or the exact inherited-only declaration.",
            )
        ]
    if problem == "multiple":
        return None, [
            _finding(
                "CONCORDE-ONTOLOGY-002",
                level,
                "The design declares ## Terminology more than once.",
                "Keep exactly one terminology section at this level.",
            )
        ]
    assert section is not None
    if section == INHERITED_ONLY:
        return TerminologyDeclaration(level.identifier, level.kind, level.path, True, ()), []

    lines = [line for line in section.splitlines() if line.strip()]
    if len(lines) < 3:
        return None, [
            _finding(
                "CONCORDE-ONTOLOGY-002",
                level,
                "The terminology section has neither the inherited-only declaration nor a complete table.",
                "Use the exact Term, Meaning, Relationships table profile.",
            )
        ]
    header = _split_row(lines[0])
    separator = _split_row(lines[1])
    if header != HEADERS or separator is None or len(separator) != 3 or not all(_SEPARATOR.fullmatch(cell) for cell in separator):
        return None, [
            _finding(
                "CONCORDE-ONTOLOGY-002",
                level,
                "The terminology table must use the exact ordered headers Term, Meaning, Relationships.",
                "Replace the header and separator with the Profile 1 table shape.",
            )
        ]

    concepts: list[Concept] = []
    findings: list[Finding] = []
    for line in lines[2:]:
        cells = _split_row(line)
        if cells is None or len(cells) != 3:
            findings.append(
                _finding(
                    "CONCORDE-ONTOLOGY-002",
                    level,
                    "A terminology row does not contain exactly three Markdown table cells.",
                    "Use one Term, Meaning, and Relationships cell per row.",
                )
            )
            continue
        term = _parse_term_cell(cells[0])
        relationships = _parse_relationships(cells[2])
        if term is None or relationships is None:
            findings.append(
                _finding(
                    "CONCORDE-ONTOLOGY-002",
                    level,
                    "A terminology row does not follow the backticked term, alias, or relationship grammar.",
                    "Use one backticked preferred term, optional backticked aliases, and `predicate` → `Target term` relationships or None.",
                )
            )
            continue
        preferred, aliases = term
        meaning = cells[1].strip()
        if not meaning:
            findings.append(
                _finding(
                    "CONCORDE-ONTOLOGY-006",
                    level,
                    f"Term '{preferred}' has no meaning.",
                    "Add a non-circular meaning sufficient for a reader who knows ancestor levels.",
                )
            )
        concepts.append(
            Concept(
                preferred=preferred,
                normalized=normalize_expression(preferred),
                meaning=meaning,
                aliases=aliases,
                relationships=relationships,
                defining_level=level.identifier,
            )
        )
    if not concepts and not findings:
        findings.append(
            _finding(
                "CONCORDE-ONTOLOGY-002",
                level,
                "The terminology table has no concept rows.",
                "Add at least one local concept or use the exact inherited-only declaration.",
            )
        )

    local: dict[str, Concept] = {}
    reported: set[str] = set()
    for concept in concepts:
        for expression in concept.expressions:
            normalized = normalize_expression(expression)
            if not normalized:
                findings.append(
                    _finding(
                        "CONCORDE-ONTOLOGY-006",
                        level,
                        "A preferred term or alias normalizes to an empty expression.",
                        "Use at least one letter or number in every preferred term and alias.",
                    )
                )
            elif normalized in local and normalized not in reported:
                findings.append(
                    _finding(
                        "CONCORDE-ONTOLOGY-003",
                        level,
                        f"Local expression '{expression}' duplicates concept '{local[normalized].preferred}' after normalization.",
                        "Keep one local concept identity and declare true alternate expressions as aliases on that row.",
                    )
                )
                reported.add(normalized)
            else:
                local[normalized] = concept
    return TerminologyDeclaration(level.identifier, level.kind, level.path, False, tuple(concepts)), findings


def _levels(package: Any) -> dict[str, _Level]:
    result: dict[str, _Level] = {}
    for module in package.documents("module"):
        path = (PurePosixPath(module.path).parent / "design.md").as_posix()
        body = package.auxiliary.get(path)
        if isinstance(body, str):
            result[module.identifier] = _Level(module.identifier, "module", path, body, dict(module.metadata))
    for feature in package.documents("feature"):
        kind = "sub-feature" if feature.metadata.get("parent_feature") else "feature"
        result[feature.identifier] = _Level(feature.identifier, kind, feature.path, feature.body, dict(feature.metadata))
    return result


def _module_chain(module_id: str | None, levels: dict[str, _Level]) -> tuple[str, ...]:
    chain: list[str] = []
    visiting: set[str] = set()
    current = module_id
    while isinstance(current, str) and current in levels and current not in visiting:
        visiting.add(current)
        level = levels[current]
        if level.kind != "module":
            break
        chain.append(current)
        parent = level.metadata.get("parent")
        current = parent if isinstance(parent, str) else None
    return tuple(reversed(chain))


def _ancestors(level: _Level, levels: dict[str, _Level]) -> tuple[str, ...]:
    if level.kind == "module":
        parent = level.metadata.get("parent")
        return _module_chain(parent if isinstance(parent, str) else None, levels)
    provider = level.metadata.get("module")
    result = list(_module_chain(provider if isinstance(provider, str) else None, levels))
    parent = level.metadata.get("parent_feature")
    if level.kind == "sub-feature" and isinstance(parent, str) and parent in levels:
        result.append(parent)
    return tuple(result)


def _expression_index(declarations: list[TerminologyDeclaration]) -> dict[str, list[Concept]]:
    index: dict[str, list[Concept]] = {}
    for declaration in declarations:
        for concept in declaration.concepts:
            for expression in concept.expressions:
                index.setdefault(normalize_expression(expression), []).append(concept)
    return index


def validate_terminology(package: Any) -> list[Finding]:
    """Validate every module/feature local ontology against its bounded ancestors."""
    levels = _levels(package)
    declarations: dict[str, TerminologyDeclaration] = {}
    findings: list[Finding] = []
    for identifier in sorted(levels):
        declaration, parsed = parse_declaration(levels[identifier])
        findings.extend(parsed)
        if declaration is not None:
            declarations[identifier] = declaration

    for identifier in sorted(declarations):
        level = levels[identifier]
        declaration = declarations[identifier]
        ancestor_declarations = [
            declarations[ancestor]
            for ancestor in _ancestors(level, levels)
            if ancestor in declarations
        ]
        inherited = _expression_index(ancestor_declarations)
        local = _expression_index([declaration])

        reported_redefinitions: set[str] = set()
        for expression, concepts in local.items():
            if expression not in inherited or expression in reported_redefinitions:
                continue
            inherited_levels = sorted({concept.defining_level for concept in inherited[expression]})
            findings.append(
                _finding(
                    "CONCORDE-ONTOLOGY-004",
                    level,
                    f"Local expression '{concepts[0].preferred}' redefines inherited terminology from {', '.join(inherited_levels)}.",
                    "Use the inherited concept unchanged, or introduce a distinct qualified preferred term and relate it explicitly.",
                )
            )
            reported_redefinitions.add(expression)

        visible = {key: list(value) for key, value in inherited.items()}
        for expression, concepts in local.items():
            visible.setdefault(expression, []).extend(concepts)
        for concept in declaration.concepts:
            for relationship in concept.relationships:
                target = normalize_expression(relationship.target)
                matches = visible.get(target, [])
                identities = sorted({item.identity for item in matches})
                if not matches:
                    findings.append(
                        _finding(
                            "CONCORDE-ONTOLOGY-005",
                            level,
                            f"Relationship target '{relationship.target}' from term '{concept.preferred}' does not resolve locally or through the permitted ancestor chain.",
                            "Define the target locally, correct the expression, or reference a preferred term or alias from an ancestor.",
                        )
                    )
                elif len(identities) > 1:
                    findings.append(
                        _finding(
                            "CONCORDE-ONTOLOGY-005",
                            level,
                            f"Relationship target '{relationship.target}' from term '{concept.preferred}' is ambiguous across {', '.join(identities)}.",
                            "Remove the conflicting alias/redefinition or use one unambiguous preferred term.",
                        )
                    )
    return findings
