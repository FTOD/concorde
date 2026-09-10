"""Deterministic checks establish structure/contract evidence, never semantic completeness."""
from __future__ import annotations

import os
import re
from collections import Counter
from pathlib import Path

from .model import Finding, ToolResult
from .repository import (HEADING, LIST_ITEM, MANDATORY_SECTIONS, ENTITIES_BLOCK, SKIPPED_DIRECTORIES,
                         SKIPPED_SUFFIXES, SpecError, SpecRepository, SpecTarget, digest, entry_exists,
                         is_directory_entry, read_file, walk_lines)
from .typed_data import checked_path


DIAGRAM_KEYWORDS = ("flowchart", "graph", "subgraph", "end", "classDef", "class", "style",
                    "linkStyle", "direction", "click", "accTitle", "accDescr")
EDGE = re.compile(r"(?P<op>x--x|o--o|<-->|-->|---|-\.->|-\.-|==>|===|--x|--o|<--|<==)"
                  r"(?:[ \t]*\|(?P<label>[^|]*)\|)?")
INLINE_EDGE = re.compile(r"--[ \t]+(?P<label>[^-]+?)[ \t]+-->|-\.[ \t]+(?P<label2>[^.]+?)[ \t]+\.->"
                         r"|==[ \t]+(?P<label3>[^=]+?)[ \t]+==>")
NODE = re.compile(r"(?P<id>[A-Za-z0-9_]+)(?::::\w+)?")
OPENERS = ("(((", "[[", "[(", "((", "{{", "[/", "[\\", "[", "(", "{", ">")
CLOSERS = (")))", "]]", ")]", "))", "}}", "/]", "\\]", "]", ")", "}")


class DiagramError(ValueError):
    pass


def _first_line(label: str) -> str:
    text = label.strip()
    if len(text) >= 2 and text[0] == '"' and text[-1] == '"':
        text = text[1:-1]
    text = re.split(r"<br\s*/?>", text)[0]
    return text.strip()


def _scan_node(line: str, position: int) -> tuple[str, str | None, int]:
    match = NODE.match(line, position)
    if not match:
        raise DiagramError(f"cannot interpret diagram text near {line[position:position + 20]!r}")
    node_id = match.group("id")
    position = match.end()
    rest = line[position:]
    for opener in OPENERS:
        if rest.startswith(opener):
            inner_start = position + len(opener)
            if line[inner_start:inner_start + 1] == '"':
                end = line.find('"', inner_start + 1)
                if end < 0:
                    raise DiagramError("unterminated quoted node label")
                label = line[inner_start + 1:end]
                after = end + 1
            else:
                closer_index = min((line.find(c, inner_start) for c in CLOSERS
                                    if line.find(c, inner_start) >= 0), default=-1)
                if closer_index < 0:
                    raise DiagramError("unterminated node label")
                label = line[inner_start:closer_index]
                after = closer_index
            for closer in CLOSERS:
                if line.startswith(closer, after):
                    after += len(closer)
                    break
            else:
                raise DiagramError("node shape is not closed")
            if line.startswith(":::", after):
                after = re.compile(r":::\w+").match(line, after).end()
            return node_id, label, after
    return node_id, None, position


def flowchart_model(text: str) -> tuple[dict[str, str], list[tuple[str, str | None, str]]]:
    """Node labels and labeled edges of one Mermaid flowchart; raises DiagramError when unreadable."""
    nodes: dict[str, str] = {}
    edges: list[tuple[str, str | None, str]] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("%%"):
            continue
        head = re.split(r"[\s:]", line, 1)[0]
        if head in DIAGRAM_KEYWORDS:
            continue
        position = 0
        groups: list[list[str]] = []
        pending_edges: list[str | None] = []
        current: list[str] = []
        while position < len(line):
            while position < len(line) and line[position] in " \t":
                position += 1
            if position >= len(line):
                break
            if line.startswith("&", position):
                position += 1
                continue
            inline = INLINE_EDGE.match(line, position)
            if inline:
                label = inline.group("label") or inline.group("label2") or inline.group("label3")
                groups.append(current)
                current = []
                pending_edges.append(label.strip() if label and label.strip() else None)
                position = inline.end()
                continue
            edge = EDGE.match(line, position)
            if edge:
                label = edge.group("label")
                groups.append(current)
                current = []
                pending_edges.append(label.strip() if label and label.strip() else None)
                position = edge.end()
                continue
            node_id, label, position = _scan_node(line, position)
            if label is not None:
                nodes[node_id] = label
            else:
                nodes.setdefault(node_id, node_id)
            current.append(node_id)
        groups.append(current)
        if len(groups) != len(pending_edges) + 1 or any(not group for group in groups):
            raise DiagramError(f"cannot interpret diagram line: {raw.strip()!r}")
        for index, label in enumerate(pending_edges):
            for source in groups[index]:
                for target in groups[index + 1]:
                    edges.append((source, label, target))
    return nodes, edges


def _section_ranges(body: str) -> tuple[list[tuple[str, int, int, int]], list[tuple[int, str, str]]]:
    """Heading sections of prose as (text, level, start line, end line) with the walked lines."""
    lines = walk_lines(body)
    headings = []
    for number, kind, line in lines:
        if kind != "prose":
            continue
        match = HEADING.match(line)
        if match:
            headings.append((match.group(2).strip(), len(match.group(1)), number))
    total = lines[-1][0] if lines else 0
    sections = []
    for index, (text, level, start) in enumerate(headings):
        end = total
        for later_text, later_level, later_start in headings[index + 1:]:
            if later_level <= level:
                end = later_start - 1
                break
        sections.append((text, level, start, end))
    return sections, lines


def _architecture_fences(body: str) -> list[str]:
    sections, lines = _section_ranges(body)
    fences: list[str] = []
    for text, level, start, end in sections:
        if text != "Architecture" or level > 3:
            continue
        current: list[str] | None = None
        for number, kind, line in lines:
            if number < start or number > end:
                continue
            if kind == "fence-open":
                current = [] if re.match(r"^ {0,3}(?:`{3,}|~{3,})\s*mermaid\s*$", line) else None
            elif kind == "fenced" and current is not None:
                current.append(line)
            elif kind == "fence-close" and current is not None:
                fences.append("\n".join(current))
                current = None
    return fences


def module_findings(repository: SpecRepository, target_id: str | None = None) -> tuple[Finding, ...]:
    """Check the four mandatory sections of every reading entry, not semantic sufficiency."""
    findings = []
    for target in repository.targets.values():
        if target_id is not None and target.id != target_id:
            continue
        path = target.primary_document
        try:
            document = repository.document(path)
        except (ValueError, OSError, KeyError, TypeError) as problem:
            findings.append(Finding("CONCORDE-MODULE-001", "error", path, str(problem),
                "Register a readable module.md reading entry.", subject_id=target.id))
            continue
        problems = []
        sections, lines = _section_ranges(document.body)
        mandatory = [(text, level, start, end) for text, level, start, end in sections
                     if text in MANDATORY_SECTIONS and level <= 3]
        names = [text for text, *_ in mandatory]
        if names != list(MANDATORY_SECTIONS):
            problems.append("module.md must contain the headings Purpose, Scenarios, Entities and Architecture "
                            f"(level 1-3) exactly once each and in that order; found {names}")
        else:
            purpose = mandatory[0]
            purpose_lines = [(number, kind, line) for number, kind, line in lines
                             if purpose[2] < number <= purpose[3]]
            if not any(kind == "prose" and line.strip() for _, kind, line in purpose_lines):
                problems.append("the Purpose section must contain prose")
            if any(kind != "prose" for _, kind, _ in purpose_lines):
                problems.append("the Purpose section must not contain fenced blocks")
            if any(kind == "prose" and (LIST_ITEM.match(line) or line.lstrip().startswith("|"))
                   for _, kind, line in purpose_lines):
                problems.append("the Purpose section must not contain lists or tables")
            if not ENTITIES_BLOCK.search(document.body):
                problems.append("module.md must declare at least one concorde-entities block")
            if not _architecture_fences(document.body):
                problems.append("the Architecture section must contain a Mermaid flowchart fence")
        for problem in problems:
            findings.append(Finding("CONCORDE-MODULE-001", "error", path, problem,
                "Give the reading entry its Purpose, Scenarios, Entities and Architecture sections.",
                subject_id=target.id))
    return tuple(findings)


def definition_findings(repository: SpecRepository, target_id: str | None = None) -> tuple[Finding, ...]:
    """Parse scenarios, requirements and entities; check listings, identities and diagrams."""
    findings = []
    identities: dict[str, tuple[str, str]] = {}
    for target in repository.targets.values():
        identities.setdefault(target.id, ("Module", target.primary_document))
    for target in repository.targets.values():
        if target_id is not None and target.id != target_id:
            continue
        try:
            definitions = repository.definitions(target)
        except (ValueError, OSError, KeyError, TypeError) as problem:
            findings.append(Finding("CONCORDE-DEFINITION-001", "error", target.primary_document, str(problem),
                "Repair the scenario, requirement or entity definitions of this Module's documents.",
                subject_id=target.id))
            continue
        for kind, items in (("scenario", definitions.scenarios), ("requirement", definitions.requirements),
                            ("entity", definitions.entities)):
            for item in items:
                previous = identities.get(item.id)
                if previous is not None and previous != (kind, item.document):
                    findings.append(Finding("CONCORDE-IDENTITY-001", "error", item.document,
                        f"{kind} identity {item.id} is also used by a {previous[0]} in {previous[1]}",
                        "Give every Module, document, scenario, requirement and entity a unique stable ID.",
                        subject_id=item.id))
                else:
                    identities[item.id] = (kind, item.document)
        entity_files = repository.entity_files(target)
        declared = tuple(sorted(entity_files))
        if declared != target.files:
            findings.append(Finding("CONCORDE-ENTITY-003", "error", target.primary_document,
                f"registry files for {target.id} differ from the union of its entity files: "
                f"registry has {sorted(set(target.files) - set(declared))} extra and lacks {sorted(set(declared) - set(target.files))}",
                "Keep the registry files of a Module equal to the sorted union of its entity files.",
                subject_id=target.id))
        represented = {entity.target_id for entity in definitions.entities if entity.target_id}
        expected = {child.id for child in repository.children(target)} | set(target.uses)
        for missing in sorted(expected - represented):
            findings.append(Finding("CONCORDE-ENTITY-004", "error", target.primary_document,
                f"child or used Module {missing} has no entity with that target_id in {target.id}",
                "Declare an entity with target_id for every child and used Module.",
                subject_id=target.id))
        for entry, entity in sorted(entity_files.items()):
            exists = entry_exists(repository.root, entry)
            kind = "directory" if is_directory_entry(entry) else "file"
            if not exists and entry not in entity.pending:
                findings.append(Finding("CONCORDE-ENTITY-002", "error", entity.document,
                    f"entity {entity.id} lists {entry}, a {kind} that does not exist and is not marked pending",
                    f"Create the {kind} or mark it pending.", subject_id=entity.id))
            elif exists and entry in entity.pending:
                findings.append(Finding("CONCORDE-ENTITY-005", "warning", entity.document,
                    f"entity {entity.id} still marks {entry} pending although the {kind} exists",
                    "Delivery confirms created files and removes the marker.", subject_id=entity.id))
        findings.extend(architecture_findings(repository, target, definitions.entities))
    return tuple(findings)


def architecture_findings(repository: SpecRepository, target: SpecTarget, entities) -> tuple[Finding, ...]:
    findings = []
    path = target.primary_document
    try:
        fences = _architecture_fences(repository.document(path).body)
    except (ValueError, OSError):
        return ()
    flowcharts = [fence for fence in fences if re.match(r"^\s*(flowchart|graph)\b", fence)]
    if not flowcharts:
        return ()
    labels: set[str] = set()
    for fence in flowcharts:
        try:
            nodes, edges = flowchart_model(fence)
        except DiagramError as problem:
            findings.append(Finding("CONCORDE-ARCHITECTURE-002", "error", path, str(problem),
                "Use the Mermaid flowchart node and labeled edge forms the Protocol defines.", subject_id=target.id))
            continue
        labels.update(_first_line(label) for label in nodes.values())
        for source, label, destination in edges:
            if label is None:
                findings.append(Finding("CONCORDE-ARCHITECTURE-002", "error", path,
                    f"relationship {source} -> {destination} has no label",
                    "Label every edge with its relationship verb.", subject_id=target.id))
    titles = {entity.title for entity in entities}
    if labels != titles:
        findings.append(Finding("CONCORDE-ARCHITECTURE-001", "error", path,
            f"diagram nodes differ from entity titles: diagram-only {sorted(labels - titles)}, entities-only {sorted(titles - labels)}",
            "Make the Architecture flowchart nodes exactly the declared entity titles.", subject_id=target.id))
    return tuple(findings)


def unlisted_file_findings(repository: SpecRepository) -> tuple[Finding, ...]:
    """Warn about regular files under listed roots that no Module's entries cover."""
    roots = sorted({entry.split("/", 1)[0] for entry in repository.file_users if "/" in entry})
    findings = []
    for root_name in roots:
        base = repository.root / root_name
        if base.is_symlink() or not base.is_dir():
            continue
        for directory, names, files in os.walk(base):
            names[:] = sorted(name for name in names if name not in SKIPPED_DIRECTORIES
                              and not name.startswith(".") and not (Path(directory) / name).is_symlink())
            for name in sorted(files):
                if name.startswith(".") or name.endswith(SKIPPED_SUFFIXES):
                    continue
                relative = (Path(directory) / name).relative_to(repository.root).as_posix()
                if relative in repository.document_targets or repository.listing_users(relative):
                    continue
                findings.append(Finding("CONCORDE-ENTITY-006", "warning", relative,
                    "no Module entity lists this file", "List the file under the entity it realizes, or leave it unlisted deliberately."))
    return tuple(findings)


def document_context_findings(repository: SpecRepository) -> tuple[Finding, ...]:
    """Validate physical Spec truth identities, memberships, and main visibility."""

    findings = []
    identifiers: dict[str, str] = {}
    reserved_ids = set(repository.targets)
    for path in repository.document_targets:
        try:
            document = repository.document(path)
        except (ValueError, OSError, KeyError, TypeError) as problem:
            findings.append(Finding(
                "CONCORDE-DOCUMENT-001", "error", path,
                f"invalid Spec document context declaration: {problem}",
                "Add exactly one valid concorde-document block whose target set matches the registry.",
            ))
            continue
        previous = identifiers.get(document.document_id)
        if document.document_id in reserved_ids:
            findings.append(Finding(
                "CONCORDE-DOCUMENT-002", "error", path,
                f"document identity {document.document_id} collides with a Module identity",
                "Use one globally unique stable document ID.",
                subject_id=document.document_id,
            ))
        elif previous is not None and previous != path:
            findings.append(Finding(
                "CONCORDE-DOCUMENT-002", "error", path,
                f"document identity {document.document_id} is also declared by {previous}",
                "Give every physical Spec truth one globally unique stable document ID.",
                subject_id=document.document_id,
            ))
        else:
            identifiers[document.document_id] = path
    return tuple(findings)


def module_dependency_findings(repository: SpecRepository,
                               target_id: str | None = None) -> tuple[Finding, ...]:
    """Match local relied-upon promises to Module dependencies and direct children."""
    findings = []
    for target in repository.targets.values():
        if target_id is not None and target.id != target_id:
            continue
        try:
            declarations = repository.dependencies(target)
            seen = set()
            expected = set(target.uses) | {child.id for child in repository.children(target)}
            for declaration in declarations:
                peer = declaration["target_id"]
                if peer in seen:
                    raise SpecError(f"duplicate dependency declaration: {peer}")
                if peer not in expected:
                    raise SpecError(f"dependency is not a declared use or direct submodule: {peer}")
                seen.add(peer)
            missing = expected - seen
            if missing:
                raise SpecError("missing local dependency promises: " + ", ".join(sorted(missing)))
        except (ValueError, OSError, KeyError, TypeError) as problem:
            findings.append(Finding("CONCORDE-DEPENDENCY-001", "error", target.primary_document,
                str(problem), "Declare each direct dependency's responsibility, selection condition and relied-upon promises locally.",
                subject_id=target.id))
    return tuple(findings)


def definition_ids(repository: SpecRepository) -> set[str]:
    """Every Module and scenario identity a reflection may be attributed to."""
    ids = set(repository.targets)
    for target in repository.targets.values():
        try:
            ids.update(scenario.id for scenario in repository.scenarios(target))
        except (ValueError, OSError, KeyError, TypeError):
            continue
    return ids


def validate_repository(root: str | Path, target_id: str | None = None,
                        package_root: Path | None = None, *, registry_bytes: bytes | None = None,
                        document_overrides: dict[str, bytes] | None = None) -> ToolResult:
    findings = []
    artifacts = []
    inputs = []
    def error(code, path, message):
        findings.append(Finding(code, "error", path, message, "Reconcile the registered Spec and retry."))
    try:
        repository = SpecRepository(root, package_root, registry_bytes=registry_bytes,
                                    document_overrides=document_overrides)
        if target_id and target_id != ".":
            repository.select(target_id)
        provided = {}
        required = []
        for target in repository.targets.values():
            try:
                documents = repository.documents(target)
                artifacts.extend(doc.path for doc in documents)
                inputs.extend((doc.path, doc.digest) for doc in documents)
                for contract in repository.contracts(target):
                    key = (contract["id"], contract["version"])
                    if contract["role"] == "provided":
                        if key in provided:
                            error("CONCORDE-CONTRACT-001", contract["source"], f"duplicate provider for {key}")
                        provided[key] = contract
                    else:
                        required.append(contract)
            except (ValueError, OSError) as problem:
                error("CONCORDE-SPEC-001", target.primary_document, str(problem))
        for contract in required:
            if contract["peer"].startswith("external:"):
                continue
            provider = provided.get((contract["id"], contract["version"]))
            if not provider or provider["owner"] != contract["peer"]:
                error("CONCORDE-CONTRACT-002", contract["source"], f"missing named provider for {contract['id']}")
            elif provider["schema"] != contract["schema"]:
                # The first version admits exact shared wire schemas, with independent perspective prose.
                error("CONCORDE-CONTRACT-003", contract["source"], f"incompatible shared wire schema for {contract['id']}")
        findings.extend(document_context_findings(repository))
        findings.extend(module_findings(repository))
        findings.extend(definition_findings(repository))
        findings.extend(module_dependency_findings(repository))
        findings.extend(unlisted_file_findings(repository))
        if (repository.root/".concorde/reflections").exists():
            from ..reflections.scoped_triage import queue_module
            queue=queue_module(repository.package_root)
            _,index,parsed,_,raw=queue._load_reflections(repository.root,required=True)
            # Reflection parsing is independent of the candidate overlay, but attribution must be
            # checked against the repository instance being validated rather than the on-disk
            # registry that the compatibility queue helper happens to load.
            ids = definition_ids(repository)
            for entry in parsed.entries:
                if entry.feature not in ids:
                    error("CONCORDE-REFLECT-004",entry.path,"Reflection attribution must be a registered Module or scenario")
            inputs.extend((p,digest(b)) for p,b in raw.items())
            inputs.append(("reflection-index",digest(index)))
        if (repository.root/"concorde.json").is_file():
            from ..distribution.package_validation import validate_package
            findings.extend(validate_package(repository.root))
        inputs.append((".concorde/config.json",digest(read_file(repository.root,".concorde/config.json"))))
        inputs.append((repository.registry_path, digest(repository.registry_bytes)))
        inputs.append(("protocol", repository.config["protocol"]["digest"]))
    except (ValueError, OSError, KeyError, TypeError) as problem:
        error("CONCORDE-SOURCE-008", ".concorde/config.json", str(problem))
    counts = Counter(f.severity for f in findings)
    return ToolResult("validate", target_id or ".", "invalid" if counts["error"] else "success",
        tuple(sorted(set(artifacts))), tuple(findings), {"summary": {
            "errors": counts["error"], "warnings": counts["warning"], "infos": counts["info"]},
            "source_digest": digest(sorted(inputs)),
            "claims": ["registry structure", "Spec document identity/membership/main visibility",
                       "four mandatory Module sections", "scenario, requirement and entity syntax",
                       "entity file listings and registry files", "architecture diagram entities and labeled edges",
                       "contract examples", "shared wire schema equality", "Module dependency promises"],
            "semantic_completeness": "not_proven"})
