"""Explicit, read-only Protocol 6 -> 7 conversion planning.

This is an offline migration primitive, not a fallback parser or runtime compatibility path.
It preserves declarations and readable promises and reports editorial work still required. It
never claims that reordering sections completes the semantic rewrite or activates a new profile.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from .content_model import ContentModelError, DocumentUnit, admit_document_unit
from .repository_base import HEADING, SpecDocument, _parse_definitions, digest, read_file, walk_lines
from .typed_data import decode, safe_path
from .validation import _section_ranges, _fences_in_range
from .repository_base import LIST_ITEM

MANDATORY_SECTIONS = ("Usage & Contract", "Architecture & Realization")
USAGE_SECTIONS = ("Purpose", "Usage", "Requirements", "Scenarios")
ARCHITECTURE_SECTIONS = ("Design", "Entities", "Relationships")

def _part_subsections(sections, part: str):
    """Direct level-3 subsections of a level-2 reading part, retaining duplicates."""
    parent = next((s for s in sections if s[0] == part and s[1] == 2), None)
    if parent is None:
        return []
    return [s for s in sections if s[1] == 3 and parent[2] < s[2] <= parent[3]]
def legacy_reading_problems(body: str, *, primary: bool = False) -> list[str]:
    """Check reader-part syntax, not whether prose supplies sufficient domain meaning."""
    sections, lines = _section_ranges(body)
    parts = [s for s in sections if s[0] in MANDATORY_SECTIONS]
    expected = list(MANDATORY_SECTIONS) if primary else [p for p in MANDATORY_SECTIONS
                                                       if any(s[0] == p for s in parts)]
    problems = []
    if not parts or [s[0] for s in parts] != expected or any(s[1] != 2 for s in parts):
        problems.append("Spec requires Usage & Contract and Architecture & Realization as unique "
                        "level-2 reading parts in order (a companion may contain only one)")
    # Titles and navigation may precede the parts, but substantive headings cannot escape them.
    first = min((s[2] for s in parts), default=0)
    if any((s[1] <= 2 and s[0] not in MANDATORY_SECTIONS and s[2] > first)
           or (s[1] >= 2 and s[2] < first) for s in sections):
        problems.append("substantive sections must be nested inside a reader-oriented part")
    for number, kind, line in lines:
        if kind == "fence-open" and line.strip() == "```concorde-entities":
            if not any(s[0] == MANDATORY_SECTIONS[1] and s[1] == 2 and s[2] < number <= s[3]
                       for s in parts):
                problems.append("entity declarations belong in Architecture & Realization")
    if not primary:
        return problems
    for part, required in ((MANDATORY_SECTIONS[0], USAGE_SECTIONS),
                           (MANDATORY_SECTIONS[1], ARCHITECTURE_SECTIONS)):
        subsections = _part_subsections(sections, part)
        parent = next((s for s in sections if s[0] == part and s[1] == 2), None)
        named = [s for s in sections if parent and parent[2] < s[2] <= parent[3] and s[0] in required]
        found = [s[0] for s in named]
        if found != list(required) or any(s[1] != 3 for s in named):
            problems.append(f"{part} requires {', '.join(required)} exactly once, in order, "
                            f"as direct level-3 subsections; found {found}")
            continue
        for section in subsections:
            name, _, start, end = section
            content = [(kind, line) for n, kind, line in lines if start < n <= end]
            if name in {"Purpose", "Usage", "Design"}:
                if not any(kind == "prose" and line.strip() and not HEADING.match(line)
                           and not LIST_ITEM.match(line) and not line.lstrip().startswith("|")
                           for kind, line in content):
                    problems.append(f"the {name} section must contain explanatory prose")
            if name == "Purpose" and any(kind != "prose" or HEADING.match(line)
                    or LIST_ITEM.match(line) or line.lstrip().startswith("|") for kind, line in content):
                problems.append("the Purpose section must contain plain prose only, without headings, fences, lists or tables")
            if name == "Entities" and not _fences_in_range(lines, start, end, "concorde-entities"):
                problems.append("the Entities subsection must declare at least one concorde-entities block")
            if name == "Relationships" and not _fences_in_range(lines, start, end, "mermaid"):
                problems.append("the Relationships subsection must contain a Mermaid flowchart fence")
    return problems

_MOVED_BLOCKS = frozenset({"concorde-document", "concorde-entities", "concorde-dependencies",
                            "concorde-contract-binding", "concorde-capabilities", "concorde-agents"})
_PARTS = frozenset({"Usage & Contract", "Architecture & Realization"})


@dataclass(frozen=True)
class PreservedMeaning:
    category: str
    identity: str
    field: str
    text: str


@dataclass(frozen=True)
class DocumentMigration:
    unit: DocumentUnit
    before_digest: str
    preserved_meanings: tuple[PreservedMeaning, ...]
    legacy_main_visible: bool
    editorial_notes: tuple[str, ...]

    @property
    def report(self) -> dict:
        return {"document_id": self.unit.document_id, "owner": self.unit.owner,
                "reading_path": self.unit.reading.path, "metadata_path": self.unit.metadata.path,
                "before_digest": self.before_digest, "after_identity": self.unit.identity,
                "preserved_meanings": len(self.preserved_meanings),
                "legacy_main_visible": self.legacy_main_visible,
                "editorial_notes": list(self.editorial_notes),
                "semantic_rewrite": "not_completed", "applied": False}


def _blocks(text: str) -> list[tuple[int, int, str, str]]:
    """Closed outer fences as source-line slices. Example fences never become declarations."""
    result = []
    current = None
    payload: list[str] = []
    for number, kind, line in walk_lines(text):
        if kind == "fence-open":
            current = (number - 1, re.sub(r"^ {0,3}(?:`{3,}|~{3,})\s*", "", line).strip())
            payload = []
        elif kind == "fenced" and current is not None:
            payload.append(line)
        elif kind == "fence-close" and current is not None:
            result.append((current[0], number, current[1], "\n".join(payload)))
            current = None
    if current is not None:
        raise ValueError("cannot migrate an unclosed fence")
    return result


def _promote(text: str) -> str:
    """Remove only one obsolete nesting level outside fences."""
    return "\n".join(line[1:] if kind == "prose" and (match := HEADING.match(line))
                     and len(match.group(1)) >= 3 else line for _, kind, line in walk_lines(text))


def _layout(text: str, primary: bool) -> str:
    lines = text.splitlines()
    walked = walk_lines(text)

    def part(kind: str, line: str) -> str | None:
        heading = HEADING.match(line) if kind == "prose" else None
        return (heading.group(2) if heading and len(heading.group(1)) == 2
                and heading.group(2) in _PARTS else None)

    if not primary:
        # The old architecture wrapper has a real, linkable content boundary. Retain that
        # boundary under Design; do not flatten prose and Flow sections into the preceding case.
        return "\n".join(
            ("" if part(kind, line) == "Usage & Contract"
             else "## Design" if part(kind, line) == "Architecture & Realization"
             else line) for _, kind, line in walked).strip() + "\n"
    sections = []
    for number, kind, line in walked:
        match = HEADING.match(line) if kind == "prose" else None
        if match and len(match.group(1)) == 3:
            sections.append((number - 1, match.group(2)))
    if not sections:
        raise ValueError("reading entry has no source sections")
    by_name = {}
    original_order = []
    for index, (start, name) in enumerate(sections):
        end = sections[index + 1][0] if index + 1 < len(sections) else len(lines)
        body = lines[start + 1:end]
        # Remove the obsolete wrapper only when it is a real outer heading, not example text.
        body = [line for _, kind, line in walk_lines("\n".join(body))
                if part(kind, line) is None]
        if name in by_name:
            raise ValueError(f"duplicate source section cannot be migrated implicitly: {name}")
        by_name[name] = "\n".join(body).strip()
        original_order.append(name)
    required = {"Purpose", "Usage", "Design", "Entities", "Relationships"}
    if not required <= by_name.keys():
        raise ValueError(f"missing source sections: {sorted(required - by_name.keys())}")
    before = "\n".join(line for _, kind, line in walk_lines("\n".join(lines[:sections[0][0]]))
                       if part(kind, line) is None).strip()
    by_name["Design"] = by_name["Design"] + "\n\n" + by_name.pop("Entities")
    order = ["Purpose", "Usage", "Design", "Relationships"]
    order.extend(name for name in original_order if name not in {*order, "Entities"})
    return before + "\n\n" + "\n\n".join("## " + name + "\n\n" + _promote(by_name[name])
                                               for name in order) + "\n"


def _definition_signature(path: str, text: str, owner: str, document_id: str) -> tuple:
    document = SpecDocument(path, text, digest(text.encode()), document_id, owner, {}, text)
    scenarios, requirements = _parse_definitions(document, owner)
    return (sorted((s.id, s.title, s.steps) for s in scenarios),
            sorted((r.id, r.title, r.statement) for r in requirements))


def plan_document_migration(path: str, raw: bytes, *, expected_owner: str,
                            primary: bool = False) -> DocumentMigration:
    """Return an admitted new pair and preservation evidence, without modifying any source.

    Only the explicitly supplied document is read. Relocation of local links, collection-level
    consistency and semantic editing are the caller's responsibility before atomic activation.
    """
    source = raw.decode("utf-8")
    problems = legacy_reading_problems(source, primary=primary)
    if problems:
        raise ContentModelError(path, "invalid migration source: " + "; ".join(problems))
    blocks = _blocks(source)
    headers = [decode(payload) for _, _, name, payload in blocks if name == "concorde-document"]
    if len(headers) != 1 or not isinstance(headers[0], dict) or set(headers[0]) != {"id", "owner", "main_visible"}:
        raise ContentModelError(path, "migration requires one explicit legacy document declaration")
    header = headers[0]
    if header["owner"] != expected_owner or type(header["main_visible"]) is not bool:
        raise ContentModelError(path, "legacy document owner or visibility is invalid")
    metadata = {"schema_version": 1, "document": {k: header[k] for k in ("id", "owner")},
                "entities": [], "dependencies": [], "bindings": []}
    retained = []
    replacements = []
    local_index = 0

    def remember(category: str, identity: str, field: str, value: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ContentModelError(path, f"empty legacy {category} {field}")
        retained.append(PreservedMeaning(category, identity, field, value))
        return value

    for start, end, name, payload in blocks:
        if name not in _MOVED_BLOCKS:
            continue
        value = decode(payload)
        prose = []
        if name in {"concorde-capabilities", "concorde-agents"}:
            key = name.replace("concorde-", "concorde.", 1)
            if key in metadata.get("extensions", {}):
                raise ContentModelError(path, "duplicate profile inventory cannot be migrated implicitly")
            metadata.setdefault("extensions", {})[key] = value
            prose.append("The associated metadata records the machine-checked implementation inventory. "
                         "Its behavioral responsibilities must be explained in this reading collection.")
        elif name == "concorde-entities":
            if not isinstance(value, list) or not value:
                raise ContentModelError(path, "legacy entity declaration must be a nonempty array")
            for entity in value:
                required = {"id", "title", "kind", "responsibility"}
                if not isinstance(entity, dict) or not required <= entity.keys() or entity.keys() - required - {"files", "pending", "target_id"}:
                    raise ContentModelError(path, "unknown legacy entity fields cannot be discarded")
                identity = entity["id"]
                metadata["entities"].append({k: v for k, v in entity.items() if k != "responsibility"} |
                                            {"meaning": "#" + identity})
                prose.append(f'<a id="{identity}"></a>\n\n**{entity["title"]}.** '
                             + remember("entity", identity, "responsibility", entity["responsibility"]))
        elif name == "concorde-dependencies":
            if not isinstance(value, list) or not value:
                raise ContentModelError(path, "legacy dependencies must be a nonempty array")
            for dependency in value:
                if not isinstance(dependency, dict) or set(dependency) != {"target_id", "responsibility", "selection_condition", "relied_upon_promises"}:
                    raise ContentModelError(path, "unknown legacy dependency fields cannot be discarded")
                identity = dependency["target_id"]
                local_index += 1
                anchor = f"agreement.{header['id']}.{local_index}"
                metadata["dependencies"].append({"target_id": identity, "meaning": "#" + anchor})
                paragraphs = [f'<a id="{anchor}"></a>',
                              "**Provider responsibility.** " + remember("dependency", identity, "responsibility", dependency["responsibility"]),
                              "**When this applies.** " + remember("dependency", identity, "selection_condition", dependency["selection_condition"])]
                promises = dependency["relied_upon_promises"]
                if not isinstance(promises, list) or not promises:
                    raise ContentModelError(path, "legacy dependency must contain relied-upon promises")
                paragraphs.extend("**Relied-upon promise.** " + remember("dependency", identity, "relied_upon_promises", p)
                                  for p in promises)
                prose.append("\n\n".join(paragraphs))
        elif name == "concorde-contract-binding":
            fields = {"id", "version", "role", "peer", "selection_condition", "relied_upon_guarantees", "obligations"}
            if not isinstance(value, dict) or set(value) != fields:
                raise ContentModelError(path, "unknown legacy binding fields cannot be discarded")
            identity = value["id"]
            local_index += 1
            anchor = f"participation.{header['id']}.{local_index}"
            metadata["bindings"].append({k: value[k] for k in ("id", "version", "role", "peer")} |
                                        {"meaning": "#" + anchor})
            paragraphs = [f'<a id="{anchor}"></a>',
                          f'**Interface participation.** This Module has the {value["role"]} role for '
                          f'`{identity}` version {value["version"]} with `{value["peer"]}`.',
                          "**When this applies.** " + remember("binding", identity, "selection_condition", value["selection_condition"])]
            for field, label in (("relied_upon_guarantees", "Relied-upon guarantee"), ("obligations", "Local obligation")):
                values = value[field]
                if not isinstance(values, list) or not values:
                    raise ContentModelError(path, f"legacy binding must contain {field}")
                paragraphs.extend(f"**{label}.** " + remember("binding", identity, field, p) for p in values)
            prose.append("\n\n".join(paragraphs))
        replacements.append((start, end, "\n\n".join(prose)))
    lines = source.splitlines()
    for start, end, replacement in reversed(replacements):
        lines[start:end] = replacement.splitlines()
    reading = _layout("\n".join(lines), primary)
    unit = admit_document_unit(path, reading.encode(), (json.dumps(metadata, indent=2) + "\n").encode(),
                               expected_owner=expected_owner, primary=primary)
    # A mechanical conversion may reorganize location, never alter a requirement or scenario.
    if _definition_signature(path, source, expected_owner, header["id"]) != _definition_signature(path, reading, expected_owner, header["id"]):
        raise ContentModelError(path, "conversion changed a requirement or scenario; manual migration required")
    before_contracts = [payload for _, _, name, payload in blocks if name == "concorde-contract"]
    after_contracts = [payload for _, _, name, payload in _blocks(reading) if name == "concorde-contract"]
    if sorted(before_contracts) != sorted(after_contracts):
        raise ContentModelError(path, "conversion changed a canonical contract")
    if any(item.text not in reading for item in retained):
        raise ContentModelError(path, "conversion lost readable meaning")
    notes = ["Review narrative quality and remove obsolete inventory-oriented introductions; mechanical preservation is not semantic rewriting."]
    if re.search(r"Usage & Contract|Architecture & Realization|two[- ]part|Profile 13|6\.0\.0", reading):
        notes.append("Reconcile prose that still describes the previous Protocol/profile or its reading parts.")
    if re.search(r"#(?:usage--contract|architecture--realization|entities)\b", reading):
        notes.append("Reconcile links to removed reading headings against the complete migrated page inventory.")
    for _, _, name, _ in blocks:
        if name.startswith("concorde-") and name not in _MOVED_BLOCKS | {"concorde-contract"}:
            notes.append(f"Classify the profile-specific {name} declaration and migrate its reader/metadata representation explicitly.")
    if not header["main_visible"]:
        notes.append("Preserve the former hidden-page preference in publisher configuration, never as Protocol reading membership.")
    return DocumentMigration(unit, digest(raw), tuple(retained), header["main_visible"], tuple(dict.fromkeys(notes)))


def preview_registered_migration(root: Path, registry_path: str = ".concorde/specs.json") -> dict:
    """Read an explicit legacy registry and report conversions, without writing a candidate.

    This deliberately does not construct the active SpecRepository: after activation its old
    profile must be rejected, while an explicit migration tool must still inspect old source.
    Source registration is bounded here; this preview does not claim project-level conformance.
    """
    if root.is_symlink() or not root.is_dir():
        raise ContentModelError(str(root), "project root must be a real directory, not a symlink")
    registry_raw = read_file(root, registry_path)
    registry = decode(registry_raw.decode("utf-8"))
    if not isinstance(registry, dict) or type(registry.get("schema_version")) is not int or registry["schema_version"] != 4:
        raise ContentModelError(registry_path, "explicit migration expects legacy registry schema 4")
    targets = registry.get("targets")
    if not isinstance(targets, list) or not targets:
        raise ContentModelError(registry_path, "registry must declare a nonempty target array")
    paths: dict[str, str] = {}
    identities: set[str] = set()
    for target in targets:
        if not isinstance(target, dict) or not isinstance(target.get("id"), str):
            raise ContentModelError(registry_path, "target must have an explicit identity")
        if target["id"] in identities:
            raise ContentModelError(registry_path, "duplicate target identity")
        identities.add(target["id"])
        documents = target.get("documents")
        if not isinstance(documents, list) or not documents or any(not isinstance(p, str) for p in documents):
            raise ContentModelError(registry_path, "target must register explicit document paths")
        if sum(Path(path).name == "module.md" for path in documents) != 1:
            raise ContentModelError(registry_path, "target must register exactly one module.md")
        for path in documents:
            safe_path(path)
            if path in paths:
                raise ContentModelError(registry_path, f"duplicate document registration: {path}")
            paths[path] = target["id"]
    converted, errors = [], []
    for path, owner in sorted(paths.items()):
        try:
            plan = plan_document_migration(path, read_file(root, path), expected_owner=owner,
                                           primary=Path(path).name == "module.md")
            converted.append(plan.report)
        except (ValueError, OSError) as error:
            errors.append({"path": path, "owner": owner, "message": str(error)})
    return {"schema_version": 1, "action": "preview-protocol-7-migration",
            "registry_path": registry_path, "registry_digest": digest(registry_raw),
            "registered_documents": len(paths), "converted_documents": len(converted),
            "status": "blocked" if errors else "conversion_preview",
            "ready_to_apply": False, "applied": False, "semantic_rewrite": "not_completed",
            "preserved_meanings": sum(item["preserved_meanings"] for item in converted),
            "documents": converted, "errors": errors}


def main() -> int:
    """A read-only developer command; stdout is a preview report, never an application artifact."""
    import argparse
    parser = argparse.ArgumentParser(description="Preview the current checkout's Protocol 7 conversion without writes")
    parser.parse_args()
    try:
        report = preview_registered_migration(Path.cwd())
    except (ValueError, OSError) as error:
        print(json.dumps({"status": "blocked", "applied": False, "ready_to_apply": False,
                          "errors": [{"message": str(error)}]}, sort_keys=True))
        return 1
    print(json.dumps(report, indent=2, sort_keys=True))
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
