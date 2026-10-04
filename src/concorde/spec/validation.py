"""Every decidable check of Spec Protocol 16 (``protocol/checks.md``), reported as findings.

A finding's ``rule_id`` is the check identity (``CHK.*``). A few tool findings keep a
``CONCORDE-*`` identity: link fragments, scenario coverage and unreadable sources. Passing these checks establishes structural conformance only; it never
establishes that the Spec is sufficient or that the implementation conforms.
"""

from __future__ import annotations

import json
import posixpath
import subprocess
import unicodedata
from collections import Counter
from pathlib import Path

from .content_model import MODULE_OPTIONAL, metadata_path
from .content_repository import DocumentUnitRepository, strictness
from .errors import system_cause
from .glossary import misaddressed_links, plain_definition
from .model import Finding, ToolResult
from .repository import SpecRepository
from .repository_base import (
    GENERATED_PREFIXES,
    INSTALL_RECORD,
    SpecError,
    bound_by,
    control_path,
    covers,
    digest,
    entry_base,
    entry_exists,
    installed_files,
    is_directory_entry,
    overlaps,
    read_file,
)
from .style import style_problems
from .syntax import (
    LINK,
    NODE_PREFIXES,
    DiagramError,
    diagram_model,
    explained,
    link_target,
    one_sentence,
    term_uses,
    test_declarations,
)
from .typed_data import TypedDataError
from .verification import DeclarationError, scan_declarations

REMEDIATION = {
    "CHK.registry.mirror": "Regenerate the registry's mirrored fields with `concorde.py registry --write`.",
    "CHK.binds.unbound": "Add the file to a realization's entries of the Module it realizes.",
    "CHK.binds.exists": (
        "Create the file before binding it, or remove the entry; a realization binds only "
        "paths that exist."
    ),
    "CHK.binds.installed": (
        "Replace the directory entry by the exact paths of the Module's own files in it; an "
        "installed file is bound only by its exact path."
    ),
    "CHK.context.reconciled": "Select the defining document through uses, contains or an includes with a reason, or remove the relation.",
    "CHK.contrasts.required": "Declare a contrasts relation with a reason between the two nodes.",
    "CHK.term.unlinked": (
        "Link the term where the document first uses it, or rephrase a word that only looks "
        "like the term."
    ),
    "CHK.style.sentence-length": (
        "Split the sentence into shorter sentences of one fact each, or move its conditions or "
        "items into a list; see the Protocol's Sentence style."
    ),
    "CHK.style.semicolon": "Write separate sentences or a list instead of the semicolon.",
    "CHK.style.one-obligation": (
        "Write one sentence for each obligation, each with one requirement keyword."
    ),
    "CHK.concept.local": (
        "Remove the glossary entry and explain the word in its owner's own document where it is "
        "first used, or move the entry to the Module that declares the glossary when it is a core "
        "term."
    ),
}


def _finding(
    check: str,
    source: str,
    message: str,
    *,
    line: int | None = None,
    subject: str | None = None,
) -> Finding:
    return Finding(
        check,
        strictness(check),
        source,
        message,
        REMEDIATION.get(
            check, "Repair the declaration so the Spec graph is well formed."
        ),
        line=line,
        subject_id=subject,
    )


def normalize_title(value: str) -> str:
    """Name normalization of CHK.contrasts.required: NFKC, casefold, one space per separator run."""
    import re

    text = unicodedata.normalize("NFKC", value).casefold()
    return re.sub(r"[\s_-]+", " ", text).strip()


class Checks:
    """One pass over a loaded graph, collecting findings per check family."""

    def __init__(self, repository: DocumentUnitRepository):
        self.repository = repository
        self.findings: list[Finding] = []
        self.entries = {
            module.entry: module.id for module in repository.declarations.values()
        }

    def add(self, check: str, source: str, message: str, **keys) -> None:
        self.findings.append(_finding(check, source, message, **keys))

    def run(self) -> list[Finding]:
        for family in (
            self.registry,
            self.glossary,
            self.terms,
            self.nodes,
            self.module_relations,
            self.metadata_relations,
            self.bindings,
            self.external,
            self.participation,
            self.views,
            self.reconciliation,
            self.links,
            self.evidence,
            self.style,
        ):
            family()
        return self.findings

    # --- registry ------------------------------------------------------------------------

    def registry(self) -> None:
        repository = self.repository
        fields = (
            "id",
            "title",
            "entry",
            "owns",
            "contains",
            "uses",
            "includes",
            "participates",
        )
        for record in repository.records:
            module = repository.declarations.get(record["id"])
            if module is None or module.block is None:
                continue
            expected = fields + tuple(
                name for name in MODULE_OPTIONAL if name in module.block
            )
            if set(record) != set(expected):
                self.add(
                    "CHK.registry.mirror",
                    repository.registry_path,
                    f"registry record {record['id']} must have exactly the fields "
                    f"{list(expected)}",
                    subject=record["id"],
                )
                continue
            differing = [
                name
                for name in expected[1:]
                if name != "entry" and record.get(name) != module.block.get(name)
            ]
            if differing:
                self.add(
                    "CHK.registry.mirror",
                    repository.registry_path,
                    f"registry record {record['id']} differs from its entry's module block in "
                    + ", ".join(differing),
                    subject=record["id"],
                )

    # --- documents -----------------------------------------------------------------------

    # --- the glossary and term links -----------------------------------------------------

    def glossary(self) -> None:
        """CHK.glossary.declared for a project that names concepts without a glossary, and
        CHK.concept.definition and CHK.node.meaning for every entry."""
        repository = self.repository
        if repository.glossary_path is None:
            named = sorted(
                {item["concept"] for item in repository.mentions}
                | {
                    identity
                    for module in repository.declarations.values()
                    for kind in ("contains", "uses")
                    for item in module.relations(kind)
                    for identity in item.get("relies_on", ())
                    if identity.startswith("concept.")
                }
                | {
                    relation["target"]
                    for relation in repository.metadata_relations
                    if str(relation.get("target", "")).startswith("concept.")
                }
            )
            if named and not any(
                module.glossary for module in repository.declarations.values()
            ):
                self.add(
                    "CHK.glossary.declared",
                    repository.registry_path,
                    "the Specs name concepts but no Module declares a glossary: "
                    + ", ".join(named[:10])
                    + (f" and {len(named) - 10} more" if len(named) > 10 else ""),
                )
            return
        path = repository.glossary_path
        for concept in repository.concept_nodes.values():
            if concept.definition is not None and not one_sentence(
                plain_definition(concept.definition)
            ):
                self.add(
                    "CHK.concept.definition",
                    path,
                    f"the definition of concept {concept.id} must be one nonempty sentence",
                    subject=concept.id,
                )
            owner = repository.declarations[concept.owner]
            unit = repository.units.get(concept.document)
            anchor = (
                repository.readings[concept.document].anchors.get(concept.anchor)
                if concept.document in repository.readings
                else None
            )
            if (
                concept.document not in owner.owns
                or unit is None
                or unit.role != "module"
                or anchor is None
                or not anchor.text.strip()
            ):
                reason = (
                    f"{concept.document} is not a document {concept.owner} owns"
                    if concept.document not in owner.owns
                    else f"{concept.document} is not a module-role document"
                    if unit is None or unit.role != "module"
                    else f"{concept.document} has no anchor {concept.anchor!r}"
                    if anchor is None
                    else f"the anchor at {concept.document}:{anchor.line} has no prose "
                    "before the next heading or anchor group (anchors explained by the same prose "
                    "go together on one line, since a blank line between them starts a new group)"
                )
                self.add(
                    "CHK.node.meaning",
                    path,
                    f"concept {concept.id} explanation {concept.explanation!r} must resolve to "
                    f"nonempty prose in a module document its owner owns: {reason}",
                    subject=concept.id,
                )
            for identity in concept.mentions:
                if identity not in repository.concept_nodes:
                    self.add(
                        "CHK.term.link",
                        path,
                        f"the definition of {concept.id} links #{identity}, which is no "
                        "concept of the glossary",
                        subject=concept.id,
                    )
            for target in misaddressed_links(concept.definition or ""):
                self.add(
                    "CHK.term.link",
                    path,
                    f"the definition of {concept.id} links {target}; a term link inside a "
                    "definition addresses another entry by fragment alone, "
                    f"#{target.split('#', 1)[1]}",
                    subject=concept.id,
                )

    def terms(self) -> None:
        """CHK.term.link for every term link in reading, and CHK.term.unlinked."""
        repository = self.repository
        linked: dict[str, set[str]] = {}
        for item in repository.mentions:
            if repository.glossary_path is None:
                break
            if (
                item["path"] != repository.glossary_path
                or item["concept"] not in repository.concept_nodes
            ):
                self.add(
                    "CHK.term.link",
                    item["document"],
                    f"term link {item['href']} must address the glossary "
                    f"{repository.glossary_path} and name one of its concepts"
                    + (
                        ""
                        if item["concept"] in repository.concept_nodes
                        else f"; {item['concept']} is no concept of the glossary"
                    ),
                    line=item["line"],
                    subject=item["concept"],
                )
                continue
            linked.setdefault(item["document"], set()).add(item["concept"])
        if repository.glossary_path is None:
            return
        titles = {
            concept.id: concept.title
            for concept in repository.concept_nodes.values()
            if concept.title.strip()
        }
        module_titles = [module.title for module in repository.declarations.values()]
        for path, reading in repository.readings.items():
            own = linked.get(path, set())
            uses = term_uses(reading.text, titles, module_titles)
            relative = posixpath.relpath(
                repository.glossary_path, posixpath.dirname(path) or "."
            )
            for identity, (line, _, _) in sorted(
                uses.items(), key=lambda item: item[1]
            ):
                if identity in own:
                    continue
                concept = repository.concept_nodes[identity]
                self.add(
                    "CHK.term.unlinked",
                    path,
                    f"uses the term {concept.title!r} without linking it; link its first use "
                    f"as [{concept.title}]({relative}#{concept.id})",
                    line=line,
                    subject=concept.id,
                )
        self.local_concepts()

    def local_concepts(self) -> None:
        """CHK.concept.local: a concept the glossary's declaring Module does not own is used by
        some Module other than its owner, through a term link in reading, a `relies_on`, a
        `relates`, or a link or relation of a concept that other Module owns."""
        repository = self.repository
        declaring = {
            module.id
            for module in repository.declarations.values()
            if module.glossary == repository.glossary_path
        }
        users: dict[str, set[str]] = {}
        for item in repository.mentions:
            users.setdefault(item["concept"], set()).add(item["owner"])
        for module in repository.declarations.values():
            for kind in ("contains", "uses"):
                for item in module.relations(kind):
                    for identity in item.get("relies_on", ()):
                        users.setdefault(identity, set()).add(module.id)
        for relation in repository.metadata_relations:
            users.setdefault(str(relation.get("target", "")), set()).add(
                relation["owner"]
            )
        for concept in repository.concept_nodes.values():
            reached = (
                set(concept.mentions)
                | set(concept.narrows)
                | ({concept.supersedes} if concept.supersedes else set())
                | {str(item.get("target")) for item in concept.contrasts}
                | {str(item.get("target")) for item in concept.relates}
            )
            for identity in reached:
                users.setdefault(identity, set()).add(concept.owner)
        for concept in sorted(repository.concept_nodes.values(), key=lambda c: c.id):
            if concept.owner in declaring or users.get(concept.id, set()) - {
                concept.owner
            }:
                continue
            self.add(
                "CHK.concept.local",
                repository.glossary_path,
                f"concept {concept.id} ({concept.title!r}) is used by no Module other than its "
                f"owner {concept.owner}",
                subject=concept.id,
            )

    def ancestors(self, module_id: str) -> set[str]:
        result, current = set(), self.repository.modules[module_id].parent
        while current is not None and current not in result:
            result.add(current)
            current = self.repository.modules[current].parent
        return result

    # --- nodes -----------------------------------------------------------------------------

    def nodes(self) -> None:
        repository = self.repository
        titles: dict[str, list[str]] = {}
        for module in repository.declarations.values():
            titles.setdefault(module.title, []).append(module.id)
        for title, owners in titles.items():
            if len(owners) > 1:
                self.add(
                    "CHK.node.title",
                    repository.registry_path,
                    f"Module title {title!r} is not unique: {', '.join(owners)}",
                )
        terms: dict[str, list[str]] = {}
        for concept in repository.concept_nodes.values():
            terms.setdefault(normalize_title(concept.title), []).append(concept.id)
        for identities in terms.values():
            if len(identities) > 1:
                self.add(
                    "CHK.node.title",
                    repository.glossary_path or repository.registry_path,
                    f"concepts {', '.join(identities)} share one title; a term has one "
                    "meaning in the project, so give each meaning its own title",
                    subject=identities[0],
                )
        local: dict[tuple[str, str], list[str]] = {}
        for concept in repository.concept_nodes.values():
            local.setdefault((concept.owner, concept.title), []).append(concept.id)
        for node in repository.realization_nodes.values():
            local.setdefault((node.owner, node.title), []).append(node.id)
            unit = repository.units[node.document]
            anchor_name = node.meaning[1:] if node.meaning.startswith("#") else None
            anchor = repository.readings[node.document].anchors.get(anchor_name or "")
            if anchor_name is None or anchor is None or not anchor.text.strip():
                reason = ""
                if anchor is not None:
                    # The usual slip: anchors meant to share one explanation separated by blank
                    # lines, which makes each its own group and leaves all but the last empty.
                    reason = (
                        f"; the anchor at {node.document}:{anchor.line} has no prose before the "
                        "next heading or anchor group (anchors explained by the same prose go "
                        "together on one line, since a blank line between them starts a new group)"
                    )
                self.add(
                    "CHK.node.meaning",
                    unit.metadata.path,
                    f"{node.id} meaning {node.meaning!r} must be a local anchor resolving to "
                    f"nonempty prose in its document{reason}",
                    subject=node.id,
                )
        for (owner, title), identities in local.items():
            if len(identities) > 1 and any(
                identity in repository.realization_nodes for identity in identities
            ):
                self.add(
                    "CHK.node.title",
                    repository.modules[owner].primary_document,
                    f"title {title!r} is shared by {', '.join(identities)} of {owner}",
                    subject=identities[0],
                )
        for path, reading in repository.readings.items():
            reported: set[tuple[str, ...]] = set()
            for anchor in reading.anchors.values():
                if anchor.group in reported:
                    continue
                reported.add(anchor.group)
                if not explained(anchor):
                    self.add(
                        "CHK.node.explained",
                        path,
                        f"anchor {', '.join(anchor.group)} has no explanatory prose",
                        line=anchor.line,
                    )

    # --- Module-level relations ---------------------------------------------------------

    def module_relations(self) -> None:
        repository = self.repository
        roots = [
            target.id for target in repository.modules.values() if target.parent is None
        ]
        if len(roots) != 1:
            self.add(
                "CHK.contains.root",
                repository.registry_path,
                f"exactly one Module should have no parent; found {roots}",
            )
        for module in repository.declarations.values():
            source = metadata_path(module.entry)
            used = Counter(item["target"] for item in module.uses)
            for target, count in used.items():
                if target == module.id:
                    self.add(
                        "CHK.uses.no-self",
                        source,
                        f"{module.id} uses itself",
                        subject=module.id,
                    )
                if count > 1:
                    self.add(
                        "CHK.uses.unique",
                        source,
                        f"{module.id} uses {target} more than once",
                        subject=module.id,
                    )
            for kind in ("contains", "uses"):
                for item in module.relations(kind):
                    self.meaning(module, item, kind)
                    if "relies_on" in item:
                        self.relies_on(module, item, kind)
            for item in module.participates:
                self.meaning(module, item, "participates")
            self.includes(module)

    def meaning(self, module, item: dict, kind: str) -> None:
        meaning = item.get("meaning")
        valid = isinstance(meaning, str) and "#" in meaning
        if valid:
            location = meaning.split("#", 1)[0]
            valid = (
                not location or location in module.owns
            ) and self.repository.meaning_text(module.id, meaning)
        if not valid:
            self.add(
                "CHK.relation.meaning",
                metadata_path(module.entry),
                f"{kind} {item.get('target') or item.get('contract')} meaning {meaning!r} must "
                "resolve to nonempty prose in a document the Module owns",
                subject=module.id,
            )

    def relies_on(self, module, item: dict, kind: str) -> None:
        repository = self.repository
        target = item["target"]
        for identity in item["relies_on"]:
            node = repository.nodes.get(identity)
            if (
                node is None
                or node.owner != target
                or node.type not in {"requirement", "scenario", "contract", "concept"}
            ):
                self.add(
                    "CHK.relies-on.owned",
                    metadata_path(module.entry),
                    f"{kind} {target} relies_on {identity}, which is not a requirement, scenario, "
                    f"contract or concept owned by {target}",
                    subject=module.id,
                )
        meaning = item.get("meaning")
        if not isinstance(meaning, str) or "#" not in meaning:
            return
        location, anchor = meaning.split("#", 1)
        path = location or module.entry
        found = repository.readings.get(path, None)
        region = found.anchors.get(anchor) if found else None
        if region is None:
            return
        for match in LINK.finditer(region.raw):
            linked = link_target(path, match.group(2))
            if linked is None:
                continue
            node = repository.nodes.get(linked[1])
            # A term link names a word, not a relied-upon promise: it grants its definition.
            if (
                node is not None
                and node.type != "concept"
                and node.owner == target
                and linked[1] not in item["relies_on"]
            ):
                self.add(
                    "CHK.relies-on.linked",
                    path,
                    f"the {kind} explanation links {linked[1]} of {target}, which relies_on does not list",
                    line=region.line,
                    subject=module.id,
                )

    def includes(self, module) -> None:
        repository = self.repository
        source = metadata_path(module.entry)
        pairs = Counter((item["kind"], item["target"]) for item in module.includes)
        for (kind, target), count in pairs.items():
            if count > 1:
                self.add(
                    "CHK.includes.unique",
                    source,
                    f"{module.id} includes {kind} {target} more than once",
                    subject=module.id,
                )
        for item in module.includes:
            kind, target = item["kind"], item["target"]
            if (kind == "module" and target == module.id) or (
                kind == "document"
                and repository._identity_paths.get(target) in module.owns
            ):
                self.add(
                    "CHK.includes.no-self",
                    source,
                    f"{module.id} includes itself or a document it owns: {target}",
                    subject=module.id,
                )
                continue
            if kind == "external":
                continue
            selected = set(repository.selection({**item, "kind": kind}))
            others = set(module.owns)
            for relation in (*module.contains, *module.uses):
                others.update(repository.selection({**relation, "kind": "module"}))
            for other in module.includes:
                if other is not item and other["kind"] in {"module", "document"}:
                    others.update(repository.selection(other))
            if selected and selected <= others:
                self.add(
                    "CHK.includes.redundant",
                    source,
                    f"{module.id} includes {kind} {target}, whose documents are already selected",
                    subject=module.id,
                )

    # --- metadata relations ------------------------------------------------------------

    def metadata_relations(self) -> None:
        """Endpoints, sites and uniqueness of every relates, and of every relation a glossary
        entry declares."""
        repository = self.repository
        concepts = repository.concept_nodes
        permitted = {
            "narrows": {"concept"},
            "supersedes": {"concept"},
            "contrasts": {"concept", "module"},
            "relates": {"concept", "realization", "module"},
        }
        relates: Counter = Counter()
        contrasts: Counter = Counter()
        narrows: dict[str, set[str]] = {}
        for relation in repository.metadata_relations:
            path = relation["document"]
            source_meta = metadata_path(path)
            if not isinstance(relation.get("source"), str) or not isinstance(
                relation.get("target"), str
            ):
                continue
            source, target = relation["source"], relation["target"]
            source_type = self.node_type(source)
            if (
                source_type not in {"realization", "module"}
                or self.node_type(target) not in permitted["relates"]
            ):
                self.add(
                    "CHK.relation.endpoints",
                    source_meta,
                    f"relates {source} -> {target} in document metadata needs a realization "
                    "or Module source and a concept, realization or Module target"
                    + (
                        "; a concept's relates is declared in its glossary entry"
                        if source_type == "concept"
                        else ""
                    ),
                )
                continue
            local = (
                repository.nodes[source].document == path
                if source in repository.nodes
                else source == relation["owner"]
            )
            if not local:
                self.add(
                    "CHK.relates.source",
                    source_meta,
                    f"relates source {source} is not defined by this document nor its "
                    "owning Module",
                )
            if isinstance(relation.get("verb"), str):
                relates[(source, relation["verb"].strip(), target)] += 1
        glossary = repository.glossary_path or repository.registry_path
        for relation in repository.glossary_relations():
            kind, source, target = (
                relation["type"],
                relation["source"],
                relation["target"],
            )
            if self.node_type(target) not in permitted[kind]:
                self.add(
                    "CHK.relation.endpoints",
                    glossary,
                    f"{kind} {source} -> {target} needs a "
                    f"{'/'.join(sorted(permitted[kind]))} target",
                    subject=source,
                )
                continue
            if kind == "relates" and isinstance(relation.get("verb"), str):
                relates[(source, relation["verb"].strip(), target)] += 1
            elif kind == "contrasts":
                contrasts[frozenset((source, target))] += 1
            elif kind == "supersedes":
                concept = concepts.get(source)
                if concept is None or concept.retired is None:
                    self.add(
                        "CHK.concept.retired",
                        glossary,
                        f"{source} supersedes another concept but is not retired",
                        subject=source,
                    )
            elif kind == "narrows":
                narrows.setdefault(source, set()).add(target)
        for (source, verb, target), count in relates.items():
            if count > 1:
                self.add(
                    "CHK.relates.verb",
                    repository.definer(source) if source not in concepts else glossary,
                    f"relates ({source}, {verb}, {target}) is declared more than once",
                )
        for pair, count in contrasts.items():
            if count > 1:
                self.add(
                    "CHK.contrasts.once",
                    glossary,
                    f"contrasts between {' and '.join(sorted(pair))} is declared more than once",
                )
        for start in narrows:
            stack, seen = list(narrows[start]), set()
            while stack:
                current = stack.pop()
                if current == start:
                    self.add(
                        "CHK.narrows.acyclic",
                        glossary,
                        f"narrows relates {start} to itself",
                        subject=start,
                    )
                    break
                if current not in seen:
                    seen.add(current)
                    stack.extend(narrows.get(current, ()))
        self.collisions(contrasts)

    def node_type(self, identity: str) -> str | None:
        if identity in self.repository.declarations:
            return "module"
        node = self.repository.nodes.get(identity)
        return node.type if node else None

    def collisions(self, contrasts: Counter) -> None:
        """CHK.contrasts.required: a concept and a Module other than its owner, same title."""
        repository = self.repository
        modules: dict[str, list[str]] = {}
        for module in repository.declarations.values():
            modules.setdefault(normalize_title(module.title), []).append(module.id)
        for concept in repository.concept_nodes.values():
            for module in modules.get(normalize_title(concept.title), ()):
                if module == concept.owner:
                    continue
                if frozenset((concept.id, module)) not in contrasts:
                    self.add(
                        "CHK.contrasts.required",
                        repository.glossary_path or repository.registry_path,
                        f"{concept.id} and {module} have equal normalized titles and no "
                        "contrasts",
                        subject=concept.id,
                    )

    # --- realizations ----------------------------------------------------------------

    def bindings(self) -> None:
        repository = self.repository
        # The glossary is a Spec source like a document member: never bound, never unbound.
        members = set(repository.source_documents) | (
            {repository.glossary_path} if repository.glossary_path else set()
        )
        outputs = generated_outputs(repository.root)
        installed = installed_files(repository.root)
        for module in repository.declarations.values():
            listed: Counter = Counter()
            for realization in repository.realizations(repository.modules[module.id]):
                source = metadata_path(realization.document)
                listed.update(realization.entries)
                for entry in realization.entries:
                    base = entry_base(entry)
                    held = sorted(
                        path
                        for path in installed
                        if is_directory_entry(entry) and covers(entry, path)
                    )
                    if held:
                        self.add(
                            "CHK.binds.installed",
                            source,
                            f"{realization.id} binds the directory {entry}, which holds the "
                            f"installed file(s) {', '.join(held)} that the installation record "
                            f"{INSTALL_RECORD} lists as the installer's own",
                            subject=realization.id,
                        )
                    if (
                        entry in members
                        or control_path(base)
                        or generated(base, outputs)
                        or (
                            is_directory_entry(entry)
                            and any(covers(entry, m) for m in members)
                        )
                    ):
                        self.add(
                            "CHK.binds.no-spec",
                            source,
                            f"{realization.id} binds {entry}, a document member, generated output "
                            "or control record, or a directory containing a document member",
                            subject=realization.id,
                        )
                    if not entry_exists(repository.root, entry):
                        kind = "directory" if is_directory_entry(entry) else "file"
                        self.add(
                            "CHK.binds.exists",
                            source,
                            f"{realization.id} binds {entry}, which is not an existing {kind}",
                            subject=realization.id,
                        )
            for entry, count in listed.items():
                if count > 1:
                    self.add(
                        "CHK.binds.disjoint",
                        metadata_path(module.entry),
                        f"several realizations of {module.id} list {entry}",
                        subject=module.id,
                    )
        self.unbound(members, outputs)

    def unbound(self, members: set[str], outputs: set[str]) -> None:
        repository = self.repository
        tracked = version_controlled(repository.root)
        if tracked is None:
            return
        files, links = tracked
        external = [
            entry
            for target in repository.modules.values()
            for entry in repository.external_inclusions(target)
        ]
        entries = [
            entry for module in repository.modules.values() for entry in module.files
        ]
        for path in files:
            if (
                path in members
                or control_path(path)
                or generated(path, outputs)
                or any(covers(link + "/", path) or path == link for link in links)
                or any(covers(entry, path) for entry in external)
                or build_path(path)
            ):
                continue
            if not (repository.root / path).is_file():
                continue
            if not any(bound_by(entry, path) for entry in entries):
                self.add(
                    "CHK.binds.unbound",
                    path,
                    "no Module's realization binds this version-controlled file",
                )

    def external(self) -> None:
        repository = self.repository
        tracked = version_controlled(repository.root)
        members = set(repository.source_documents)
        entries = [
            entry for target in repository.modules.values() for entry in target.files
        ]
        for module in repository.declarations.values():
            source = metadata_path(module.entry)
            for entry in repository.external_inclusions(repository.modules[module.id]):
                if not entry_exists(repository.root, entry):
                    self.add(
                        "CHK.external.exists",
                        source,
                        f"external material {entry} of {module.id} does not exist; check out or "
                        "vendor it (scripts/development/init-references.py for submodules)",
                        subject=module.id,
                    )
                elif tracked is not None:
                    files, links = tracked
                    base = entry_base(entry)
                    if not any(
                        base == link
                        or base.startswith(link + "/")
                        or covers(link + "/", base)
                        for link in links
                    ) and not any(covers(entry, path) for path in files):
                        self.add(
                            "CHK.external.exists",
                            source,
                            f"external material {entry} is not tracked by version control",
                            subject=module.id,
                        )
                if any(overlaps(entry, member) for member in members) or any(
                    overlaps(entry, bound) for bound in entries
                ):
                    self.add(
                        "CHK.external.no-overlap",
                        source,
                        f"external material {entry} overlaps a document member or realization entry",
                        subject=module.id,
                    )

    # --- contracts --------------------------------------------------------------------

    def participation(self) -> None:
        repository = self.repository
        declared = []
        for module in repository.declarations.values():
            source = metadata_path(module.entry)
            keys = Counter(
                (item["contract"], item["peer"], item["role"])
                for item in module.participates
            )
            for key, count in keys.items():
                if count > 1:
                    self.add(
                        "CHK.participates.unique",
                        source,
                        f"{module.id} participates in {key[0]} with peer {key[1]} as {key[2]} more than once",
                        subject=module.id,
                    )
            for item in module.participates:
                contract = repository.contract_nodes.get(item["contract"])
                if contract is None or contract["version"] != item["version"]:
                    self.add(
                        "CHK.participates.version",
                        source,
                        f"{module.id} participates in {item['contract']} version {item['version']}, "
                        + (
                            "which is not a defined contract"
                            if contract is None
                            else f"but its current version is {contract['version']}"
                        ),
                        subject=module.id,
                    )
                if (
                    item["peer"] != "external"
                    and item["peer"] not in repository.declarations
                ):
                    self.add(
                        "CHK.relation.endpoints",
                        source,
                        f"participation peer {item['peer']} is not a registered Module",
                        subject=module.id,
                    )
                declared.append((module.id, item))
        for owner, item in declared:
            if (
                item["peer"] == "external"
                or item["peer"] not in repository.declarations
            ):
                continue
            if not any(
                other_owner == item["peer"]
                and other["peer"] == owner
                and other["contract"] == item["contract"]
                and other["version"] == item["version"]
                and other["role"] != item["role"]
                for other_owner, other in declared
            ):
                self.add(
                    "CHK.participates.complementary",
                    metadata_path(repository.declarations[owner].entry),
                    f"{owner} participates in {item['contract']} with {item['peer']}, which declares "
                    "no complementary participation",
                    subject=owner,
                )

    # --- views --------------------------------------------------------------------------

    def views(self) -> None:
        repository = self.repository
        for path, reading in repository.readings.items():
            unit = repository.units[path]
            for line, language, info, body in reading.diagrams:
                if language == "mermaid":
                    self.add(
                        "CHK.view.marked",
                        path,
                        "a Mermaid block is not part of reading; rewrite it as a checked `d2` "
                        "block or a `d2 illustrative` block",
                        line=line,
                    )
                    continue
                if "illustrative" in info:
                    continue
                if unit.role != "module":
                    self.add(
                        "CHK.view.marked",
                        path,
                        "a checked D2 diagram lies only in `module` reading; mark this one "
                        "`d2 illustrative`",
                        line=line,
                    )
                    continue
                self.diagram(path, unit.owner, line, body)

    def resolve_label(self, owner: str, label: str) -> list[str]:
        repository = self.repository
        text = label.strip()
        # In a Module's own reading its title names the Module, even when one of its concepts
        # shares the title; that concept is drawn with the qualified form.
        if (
            owner in repository.declarations
            and repository.declarations[owner].title == text
        ):
            return [owner]
        matches = [
            node.id
            for node in (
                *repository.concept_nodes.values(),
                *repository.realization_nodes.values(),
            )
            if node.owner == owner and node.title == text
        ]
        matches += [
            module.id
            for module in repository.declarations.values()
            if module.title == text
        ]
        if " / " in text:
            module_title, node_title = (part.strip() for part in text.split(" / ", 1))
            for module in repository.declarations.values():
                if module.title != module_title:
                    continue
                matches += [
                    node.id
                    for node in (
                        *repository.concept_nodes.values(),
                        *repository.realization_nodes.values(),
                    )
                    if node.owner == module.id and node.title == node_title
                ]
        return list(dict.fromkeys(matches))

    def resolve_file(self, realization: str, label: str) -> list[str]:
        """Bound entries of a realization that a file shape's label names."""
        node = self.repository.realization_nodes[realization]
        text = label.strip()
        return [
            entry
            for entry in node.entries
            if entry == text or entry.endswith("/" + text.lstrip("/"))
        ]

    def diagram(self, path: str, owner: str, line: int, body: str) -> None:
        """CHK.view.subset, nodes, nesting and edges for one checked D2 diagram."""
        repository = self.repository
        declarations = repository.declarations
        try:
            shapes, edges = diagram_model(body)
        except DiagramError as error:
            self.add(
                "CHK.view.subset",
                path,
                f"checked D2 diagram leaves the semantic subset: {error.message}",
                line=line + (error.line or 0),
            )
            return
        # Every shape resolves to ("module" | "concept" | "realization", id) or ("file", entry).
        resolved: dict[tuple[str, ...], tuple[str, str]] = {}
        for shape in sorted(shapes, key=lambda item: len(item.path)):
            at = line + shape.line
            parent = resolved.get(shape.path[:-1])
            if parent and parent[0] == "realization":
                entries = self.resolve_file(parent[1], shape.label)
                if len(entries) != 1:
                    self.add(
                        "CHK.view.nodes",
                        path,
                        f"file shape {shape.label!r} inside realization {parent[1]} names "
                        + (
                            "no entry it binds"
                            if not entries
                            else f"several entries it binds: {entries}"
                        ),
                        line=at,
                    )
                    continue
                resolved[shape.path] = ("file", entries[0])
                continue
            matches = self.resolve_label(owner, shape.label)
            if len(matches) != 1:
                self.add(
                    "CHK.view.nodes",
                    path,
                    f"diagram shape {shape.label!r} resolves to "
                    + (
                        "no node or Module"
                        if not matches
                        else f"several nodes: {matches}"
                    ),
                    line=at,
                )
                continue
            identity = matches[0]
            kind = (
                "module"
                if identity in declarations
                else "concept"
                if identity in repository.concept_nodes
                else "realization"
            )
            resolved[shape.path] = (kind, identity)
            if parent is None:
                continue
            outer_kind, outer = parent
            if outer_kind == "module" and kind == "module":
                if identity not in {
                    item["target"] for item in declarations[outer].contains
                }:
                    self.add(
                        "CHK.view.nesting",
                        path,
                        f"{identity} is drawn inside {outer}, which declares no contains of it",
                        line=at,
                    )
            elif outer_kind == "module":
                node = repository.concept_nodes.get(
                    identity
                ) or repository.realization_nodes.get(identity)
                if node.owner != outer:
                    self.add(
                        "CHK.view.nesting",
                        path,
                        f"{identity} is drawn inside {outer} but is owned by {node.owner}",
                        line=at,
                    )
            else:
                self.add(
                    "CHK.view.nesting",
                    path,
                    f"{identity} is drawn inside the {outer_kind} {outer}; only a Module holds "
                    "Modules and nodes, and only a realization holds files",
                    line=at,
                )
        uses = {
            (module.id, item["target"])
            for module in declarations.values()
            for item in module.uses
        }
        relates = {
            (relation["source"], relation["target"])
            for relation in (
                *repository.metadata_relations,
                *repository.glossary_relations(),
            )
            if relation["type"] == "relates"
        }
        for edge in edges:
            at = line + edge.line
            ends = [resolved.get(edge.source), resolved.get(edge.target)]
            if None in ends:
                continue
            (first_kind, first), (second_kind, second) = ends
            if "file" in (first_kind, second_kind):
                self.add(
                    "CHK.view.edges",
                    path,
                    f"edge {first} -> {second} touches a file shape, which asserts only its binding",
                    line=at,
                )
            elif first_kind == second_kind == "module" and edge.label is None:
                if (first, second) not in uses:
                    self.add(
                        "CHK.view.edges",
                        path,
                        f"edge {first} -> {second} between Modules matches no declared uses",
                        line=at,
                    )
            else:
                if edge.label is None:
                    self.add(
                        "CHK.view.edges",
                        path,
                        f"edge {first} -> {second} touches a node and needs the verb of its "
                        "relates as label",
                        line=at,
                    )
                if (first, second) not in relates:
                    self.add(
                        "CHK.view.edges",
                        path,
                        f"edge {first} -> {second} matches no declared relates",
                        line=at,
                    )

    # --- reconciliation -----------------------------------------------------------------

    def reconciliation(self) -> None:
        repository = self.repository
        for module in repository.declarations.values():
            target = repository.modules[module.id]
            context = set(repository._context_paths(target))
            owned = set(module.owns)
            requires: list[tuple[str, str, str]] = []
            # A relates to a realization or a Module requires its defining document; a relation
            # to a concept grants the definition itself and requires nothing.
            for relation in repository.metadata_relations:
                if (
                    relation["document"] in owned
                    and relation["type"] == "relates"
                    and not str(relation.get("target", "")).startswith("concept.")
                    and relation.get("target") not in repository.concept_nodes
                ):
                    requires.append(
                        (relation["target"], relation["document"], relation["type"])
                    )
            for relation in repository.glossary_relations():
                if (
                    relation["owner"] == module.id
                    and relation["type"] == "relates"
                    and relation["target"] not in repository.concept_nodes
                ):
                    requires.append(
                        (relation["target"], relation["document"], relation["type"])
                    )
            for item in module.participates:
                if item["contract"] in repository.contract_nodes:
                    requires.append((item["contract"], module.entry, "participates"))
            for identity, source, kind in requires:
                if identity in repository.declarations:
                    satisfied = bool(
                        context & set(repository.declarations[identity].owns)
                    )
                else:
                    definer = repository.definer(identity)
                    satisfied = definer is None or definer in context
                if not satisfied:
                    self.add(
                        "CHK.context.reconciled",
                        source,
                        f"{module.id} declares {kind} {identity}, whose defining document is not "
                        "in its Spec context",
                        subject=module.id,
                    )

    # --- links ------------------------------------------------------------------------------

    def links(self) -> None:
        repository = self.repository
        for path, reading in repository.readings.items():
            for line, href in reading.links:
                linked = link_target(path, href)
                if linked is None:
                    continue
                target_path, fragment = linked
                # A concept fragment is a term link, which CHK.term.link checks.
                if not fragment.startswith(NODE_PREFIXES) or fragment.startswith(
                    "concept."
                ):
                    continue
                definer = repository.definer(fragment)
                if definer is None or definer != target_path:
                    self.add(
                        "CONCORDE-LINK-001",
                        path,
                        f"link {href} addresses #{fragment}, "
                        + (
                            f"which is defined in {definer}"
                            if definer
                            else "which names no definition"
                        ),
                        line=line,
                        subject=fragment,
                    )

    # --- evidence ------------------------------------------------------------------------

    def evidence(self) -> None:
        repository = self.repository
        for path, reading in repository.readings.items():
            for line in test_declarations(reading.text):
                self.add(
                    "CHK.evidence.no-spec-coverage",
                    path,
                    "reading content contains test-declaration syntax outside a fence",
                    line=line,
                )
        listed: dict[str, set[str]] = {}
        realized: set[str] = set()
        for target in repository.modules.values():
            if target.files:
                realized.add(target.id)
            for file in repository.bound_files(target):
                listed.setdefault(file, set()).add(target.id)
        problems: list[DeclarationError] = []
        declarations = scan_declarations(repository.root, listed, problems)
        for problem in problems:
            self.findings.append(
                Finding(
                    "CONCORDE-COVERAGE-003",
                    "error",
                    problem.path,
                    str(problem),
                    "Repair the test file so its scenario declarations can be read.",
                    line=problem.line,
                )
            )
        scenarios = repository.scenario_nodes
        covered: set[str] = set()
        for declaration in declarations:
            scenario = scenarios.get(declaration.scenario_id)
            if scenario is None:
                self.add(
                    "CHK.verifies.resolves",
                    declaration.path,
                    f"test {declaration.name} declares unknown scenario {declaration.scenario_id}",
                    line=declaration.line,
                    subject=declaration.scenario_id,
                )
                continue
            # Tests and scenarios are many-to-many: a declaration counts wherever the test
            # file is bound, since the file's owner only decides who may change it.
            covered.add(scenario.id)
        for scenario in sorted(scenarios.values(), key=lambda item: item.id):
            if scenario.id not in covered and scenario.owner in realized:
                self.findings.append(
                    Finding(
                        "CONCORDE-COVERAGE-001",
                        "warning",
                        scenario.document,
                        f"no test declares that it verifies {scenario.id}",
                        f"Declare {scenario.id} in the tests that exercise this scenario.",
                        line=scenario.line,
                        subject_id=scenario.id,
                    )
                )

    # --- style -------------------------------------------------------------------------------

    def style(self) -> None:
        """The style checks over the reading of every document and every concept definition."""
        repository = self.repository
        for path, reading in sorted(repository.readings.items()):
            for problem in style_problems(reading.text):
                self.add(problem.check, path, problem.message, line=problem.line)
        if repository.glossary_path is None:
            return
        for concept in sorted(
            repository.concept_nodes.values(), key=lambda item: item.id
        ):
            for problem in style_problems(concept.definition or ""):
                self.add(
                    problem.check,
                    repository.glossary_path,
                    f"the definition of concept {concept.id}: {problem.message}",
                    subject=concept.id,
                )


def generated_outputs(root: Path) -> set[str]:
    """Outputs the build records in generated/build-manifest.json."""
    try:
        manifest = json.loads(read_file(root, "generated/build-manifest.json").decode())
        return {
            item["path"] if isinstance(item, dict) else item
            for item in manifest.get("outputs", [])
        }
    except (SpecError, OSError, ValueError, KeyError, TypeError):
        return set()


def generated(path: str, outputs: set[str]) -> bool:
    return path.startswith(GENERATED_PREFIXES) or path in outputs


def build_path(path: str) -> bool:
    parts = path.split("/")
    return parts[0] in {"build", "dist"} or any(
        part in {"node_modules", "__pycache__"} for part in parts
    )


def version_controlled(
    root: Path, *, untracked: bool = False
) -> tuple[list[str], list[str]] | None:
    """The files Git tracks in the work tree rooted at ``root``, and its submodule paths.

    Untracked files are not version-controlled yet; they are checked once they are added.
    ``untracked`` also lists the untracked files Git does not ignore, which are about to be.
    """
    try:
        top = subprocess.run(
            ("git", "rev-parse", "--show-toplevel"),
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        if top.returncode != 0 or Path(top.stdout.strip()).resolve() != root.resolve():
            return None
        listing = subprocess.run(
            (
                "git",
                "ls-files",
                "-z",
                "--cached",
                *(("--others", "--exclude-standard") if untracked else ()),
            ),
            cwd=root,
            capture_output=True,
            check=True,
        )
        stages = subprocess.run(
            ("git", "ls-files", "-z", "-s"), cwd=root, capture_output=True, check=True
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    links = [
        entry.split("\t", 1)[1]
        for entry in stages.stdout.decode("utf-8", "replace").split("\0")
        if entry.startswith("160000 ") and "\t" in entry
    ]
    files = sorted(
        {
            path
            for path in listing.stdout.decode("utf-8", "replace").split("\0")
            if path and path not in links
        }
    )
    return files, links


def spec_findings(repository: DocumentUnitRepository) -> list[Finding]:
    """Every Protocol check over a loaded graph: load findings first, then each check family."""
    return [*repository.load_findings, *Checks(repository).run()]


DEPENDENCY_CHECKS = frozenset(
    {
        "CHK.relation.meaning",
        "CHK.relies-on.owned",
        "CHK.relies-on.linked",
        "CHK.uses.no-self",
        "CHK.uses.unique",
        "CHK.context.reconciled",
    }
)
MISSING_PROMISES = "missing local dependency promises: "


def definition_ids(repository: DocumentUnitRepository) -> set[str]:
    """Every Module and scenario identity a reflection may be attributed to."""
    return set(repository.modules) | set(repository.scenario_nodes)


def validate_repository(
    root: str | Path,
    target_id: str | None = None,
    package_root: Path | None = None,
    *,
    registry_bytes: bytes | None = None,
    document_overrides: dict[str, bytes] | None = None,
) -> ToolResult:
    """Validate the project's Specs and report every finding one run can establish.

    Only a configuration, registry or Protocol binding that cannot be read ends the run early,
    with one ``CONCORDE-SOURCE-008`` error. A ``target_id`` that names no registered Module is a
    caller error and raises ``SpecError`` with ``unknown_target``; any other exception is a defect
    of the validator and propagates unchanged.
    """
    findings: list[Finding] = []
    artifacts: list[str] = []
    inputs: list[tuple[str, str]] = []
    load_error: SpecError | None = None
    try:
        repository = SpecRepository(
            root,
            package_root,
            registry_bytes=registry_bytes,
            document_overrides=document_overrides,
            _defer_document_admission=True,
        )
        config_digest = digest(read_file(repository.root, ".concorde/config.json"))
    except (SpecError, TypedDataError, OSError, UnicodeError) as problem:
        repository = None
        load_error = (
            problem
            if isinstance(problem, SpecError)
            else SpecError(
                "the configuration, registry or Protocol binding cannot be read",
                "missing_source",
                causes=[system_cause(problem)],
            )
        )
        findings.append(
            Finding(
                "CONCORDE-SOURCE-008",
                "error",
                load_error.path or ".concorde/config.json",
                str(load_error),
                f"{load_error.remediation} (why: {load_error.reason})",
                line=load_error.line,
                subject_id=load_error.subject,
            )
        )
    if repository is not None:
        if target_id and target_id != ".":
            repository.module(target_id)
        for target in repository.modules.values():
            artifacts.extend(
                member
                for member in target.sources
                if member in repository.source_documents
            )
        # Every registered document member as read, admitted or not, so that an invalid result
        # pins the bytes of the documents that failed admission too.
        for member, raw in sorted(repository.member_bytes.items()):
            inputs.append((member, digest(raw) if raw is not None else "absent"))
        if repository.glossary_bytes is not None:
            artifacts.append(repository.glossary_path)
            inputs.append((repository.glossary_path, digest(repository.glossary_bytes)))
        findings.extend(spec_findings(repository))
        inputs.append((".concorde/config.json", config_digest))
        inputs.append((repository.registry_path, digest(repository.registry_bytes)))
        inputs.append(("protocol", repository.config["protocol"]["digest"]))
    counts = Counter(f.strictness for f in findings)
    return ToolResult(
        "spec-validation",
        target_id or ".",
        "invalid" if counts["error"] else "success",
        tuple(sorted(set(artifacts))),
        tuple(findings),
        {
            "summary": {
                "errors": counts["error"],
                "warnings": counts["warning"],
                "infos": counts["info"],
            },
            "source_digest": digest(sorted(inputs)),
            "claims": [
                "Protocol 16 structural checks (protocol/checks.md)",
                "registry mirror of the entries' module blocks",
                "stable-identity link fragments",
                "scenario verification declarations and coverage",
            ],
            "semantic_completeness": "not_proven",
            **({"load_error": load_error.record()} if load_error is not None else {}),
        },
    )


__all__ = [
    "Checks",
    "DiagramError",
    "definition_ids",
    "diagram_model",
    "normalize_title",
    "spec_findings",
    "validate_repository",
    "version_controlled",
]
