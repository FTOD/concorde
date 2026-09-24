"""Every decidable check of Spec Protocol 12 (``protocol/checks.md``), reported as findings.

A finding's ``rule_id`` is the check identity (``CHK.*``). A few tool findings keep a
``CONCORDE-*`` identity: link fragments, scenario coverage, configured check inputs, Issue records
and package validation. Passing these checks establishes structural conformance only; it never
establishes that the Spec is sufficient or that the implementation conforms.
"""

from __future__ import annotations

import json
import subprocess
import unicodedata
from collections import Counter
from pathlib import Path

from .content_model import metadata_path
from .content_repository import DocumentUnitRepository, severity
from .model import Finding, ToolResult
from .repository import SpecRepository
from .repository_base import (
    GENERATED_PREFIXES,
    SpecError,
    bound_by,
    check_input_error,
    check_input_members,
    control_path,
    covers,
    digest,
    entry_base,
    entry_exists,
    is_directory_entry,
    overlaps,
    read_file,
)
from .syntax import (
    LINK,
    NODE_PREFIXES,
    DiagramError,
    diagram_type,
    entry_section_problems,
    explained,
    first_line,
    first_section,
    flowchart_model,
    link_target,
    one_sentence,
    test_declarations,
    UndirectedEdgeError,
)
from .typed_data import TypedDataError
from .verification import DeclarationError, scan_declarations

REMEDIATION = {
    "CHK.registry.mirror": "Regenerate the registry's mirrored fields with `concorde.py registry --write`.",
    "CHK.binds.unbound": "Add the file to a realization's entries of the Module it realizes.",
    "CHK.context.reconciled": "Select the defining document through uses, contains or an includes with a reason, or remove the relation.",
    "CHK.contrasts.required": "Declare a contrasts relation with a reason between the two nodes.",
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
        severity(check),
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
            self.documents,
            self.terminology,
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
            if set(record) != set(fields):
                self.add(
                    "CHK.registry.mirror",
                    repository.registry_path,
                    f"registry record {record['id']} must have exactly the fields {list(fields)}",
                    subject=record["id"],
                )
                continue
            differing = [
                name
                for name in fields[1:]
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

    def documents(self) -> None:
        repository = self.repository
        for module in repository.declarations.values():
            entries = [
                path
                for path in module.owns
                if path in repository.units
                and repository.units[path].role == "module"
                and path.split("/")[-1] == "module.md"
            ]
            if len(entries) > 1:
                self.add(
                    "CHK.document.entry",
                    metadata_path(module.entry),
                    f"Module {module.id} owns several module-role module.md documents: {entries}",
                    subject=module.id,
                )
            if module.entry in repository.readings:
                for problem in entry_section_problems(
                    repository.readings[module.entry].text
                ):
                    self.add(
                        problem.check, module.entry, problem.message, line=problem.line
                    )
        for path, unit in repository.units.items():
            reading = repository.readings[path]
            if unit.role != "module" or path in self.entries:
                continue
            defines_concepts = any(
                concept.document == path
                for concept in repository.concept_nodes.values()
            )
            imports = any(item["document"] == path for item in repository.imports)
            if (
                defines_concepts or imports or reading.terminology is not None
            ) and first_section(reading.text) != "Terminology":
                if defines_concepts or imports:
                    self.add(
                        "CHK.document.topic-terminology",
                        path,
                        "a module topic that defines or imports a concept starts with ## Terminology",
                    )

    # --- terminology ---------------------------------------------------------------------

    def terminology(self) -> None:
        repository = self.repository
        for path, unit in repository.units.items():
            reading = repository.readings[path]
            rows = reading.terminology or []
            defined = {
                concept.title: concept
                for concept in repository.concept_nodes.values()
                if concept.document == path
            }
            titles = Counter(row.term for row in rows if row.href is None)
            for row in rows:
                if row.href is not None:
                    continue
                if unit.role != "module":
                    self.add(
                        "CHK.terminology.rows",
                        path,
                        f"only module documents define concepts in Terminology: {row.term}",
                        line=row.line,
                    )
                elif row.term not in defined:
                    self.add(
                        "CHK.terminology.rows",
                        path,
                        f"Terminology row {row.term!r} is neither a concept this document defines "
                        "nor an import link",
                        line=row.line,
                    )
            for title, concept in defined.items():
                if titles[title] != 1:
                    self.add(
                        "CHK.concept.definition",
                        path,
                        f"concept {concept.id} needs exactly one defining Terminology row titled "
                        f"{title!r}; found {titles[title]}",
                        subject=concept.id,
                    )
                elif not concept.definition or not one_sentence(concept.definition):
                    self.add(
                        "CHK.concept.definition",
                        path,
                        f"the definition of concept {concept.id} must be one nonempty sentence",
                        subject=concept.id,
                    )
        seen: set[tuple[str, str]] = set()
        for item in repository.imports:
            path, line = item["document"], item["line"]
            unit = repository.units[path]
            concept = repository.concept_nodes.get(item["concept"] or "")
            if unit.role != "module":
                self.add(
                    "CHK.terminology.import-row",
                    path,
                    "only module documents import concepts",
                    line=line,
                )
                continue
            if item["definition"].strip():
                self.add(
                    "CHK.terminology.import-row",
                    path,
                    f"import row {item['href']} must leave Definition empty",
                    line=line,
                )
            if (
                concept is None
                or item["path"] != concept.document
                or item["path"] == path
            ):
                self.add(
                    "CHK.terminology.import-row",
                    path,
                    f"import row {item['href']} must link to a concept identity in its defining "
                    "document",
                    line=line,
                )
                continue
            key = (path, concept.id)
            if key in seen:
                self.add(
                    "CHK.terminology.rows",
                    path,
                    f"concept {concept.id} is imported twice",
                    line=line,
                )
            seen.add(key)
            if concept.owner == item["owner"]:
                self.add(
                    "CHK.imports.foreign",
                    path,
                    f"concept {concept.id} is owned by this document's own Module",
                    line=line,
                    subject=concept.id,
                )
            elif (
                concept.owner not in repository.modules[item["owner"]].uses
                and concept.owner not in self.ancestors(item["owner"])
                and item["owner"] not in self.ancestors(concept.owner)
            ):
                self.add(
                    "CHK.imports.owner",
                    path,
                    f"imported concept {concept.id} belongs to {concept.owner}, which "
                    f"{item['owner']} neither uses, descends from nor contains transitively",
                    line=line,
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
        local: dict[tuple[str, str], list[str]] = {}
        for node in (
            *repository.concept_nodes.values(),
            *repository.realization_nodes.values(),
        ):
            local.setdefault((node.owner, node.title), []).append(node.id)
            unit = repository.units[node.document]
            anchor_name = node.meaning[1:] if node.meaning.startswith("#") else None
            anchor = repository.readings[node.document].anchors.get(anchor_name or "")
            if anchor_name is None or anchor is None or not anchor.text.strip():
                self.add(
                    "CHK.node.meaning",
                    unit.metadata.path,
                    f"{node.id} meaning {node.meaning!r} must be a local anchor resolving to "
                    "nonempty prose in its document",
                    subject=node.id,
                )
        for (owner, title), identities in local.items():
            if len(identities) > 1:
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
            if (
                node is not None
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
        repository = self.repository
        concepts = repository.concept_nodes
        permitted = {
            "narrows": ({"concept"}, {"concept"}),
            "supersedes": ({"concept"}, {"concept"}),
            "contrasts": ({"concept"}, {"concept", "module"}),
            "relates": (
                {"concept", "realization", "module"},
                {"concept", "realization", "module"},
            ),
        }
        relates: Counter = Counter()
        contrasts: Counter = Counter()
        supersedes: Counter = Counter()
        narrows: dict[str, set[str]] = {}
        for relation in repository.metadata_relations:
            kind, path = relation["type"], relation["document"]
            source_meta = metadata_path(path)
            if not isinstance(relation.get("source"), str) or not isinstance(
                relation.get("target"), str
            ):
                continue
            source_type = self.node_type(relation["source"])
            target_type = self.node_type(relation["target"])
            sources, targets = permitted[kind]
            if source_type not in sources or target_type not in targets:
                self.add(
                    "CHK.relation.endpoints",
                    source_meta,
                    f"{kind} {relation['source']} -> {relation['target']} needs a "
                    f"{'/'.join(sorted(sources))} source and a {'/'.join(sorted(targets))} target",
                )
                continue
            local = (
                repository.nodes[relation["source"]].document == path
                if relation["source"] in repository.nodes
                else kind == "relates" and relation["source"] == relation["owner"]
            )
            if not local:
                self.add(
                    "CHK.relates.source" if kind == "relates" else "CHK.relation.site",
                    source_meta,
                    f"{kind} source {relation['source']} is not defined by this document"
                    + (" nor its owning Module" if kind == "relates" else ""),
                )
            if kind == "relates" and isinstance(relation.get("verb"), str):
                relates[
                    (relation["source"], relation["verb"].strip(), relation["target"])
                ] += 1
            elif kind == "contrasts":
                contrasts[frozenset((relation["source"], relation["target"]))] += 1
            elif kind == "supersedes":
                supersedes[relation["source"]] += 1
                concept = concepts.get(relation["source"])
                if concept is None or concept.retired is None:
                    self.add(
                        "CHK.concept.retired",
                        source_meta,
                        f"{relation['source']} supersedes another concept but is not retired",
                    )
            elif kind == "narrows":
                narrows.setdefault(relation["source"], set()).add(relation["target"])
        for (source, verb, target), count in relates.items():
            if count > 1:
                self.add(
                    "CHK.relates.verb",
                    repository.definer(source) or repository.registry_path,
                    f"relates ({source}, {verb}, {target}) is declared more than once",
                )
        for pair, count in contrasts.items():
            if count > 1:
                self.add(
                    "CHK.contrasts.once",
                    repository.definer(sorted(pair)[0]) or repository.registry_path,
                    f"contrasts between {' and '.join(sorted(pair))} is declared more than once",
                )
        for source, count in supersedes.items():
            if count > 1:
                self.add(
                    "CHK.concept.retired",
                    repository.definer(source) or repository.registry_path,
                    f"{source} supersedes more than one concept",
                )
        for start in narrows:
            stack, seen = list(narrows[start]), set()
            while stack:
                current = stack.pop()
                if current == start:
                    self.add(
                        "CHK.narrows.acyclic",
                        repository.definer(start) or repository.registry_path,
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
        repository = self.repository
        named: dict[str, list[tuple[str, str]]] = {}
        for concept in repository.concept_nodes.values():
            named.setdefault(normalize_title(concept.title), []).append(
                (concept.id, concept.owner)
            )
        for module in repository.declarations.values():
            named.setdefault(normalize_title(module.title), []).append(
                (module.id, module.id)
            )
        for items in named.values():
            for index, (first, first_owner) in enumerate(items):
                for second, second_owner in items[index + 1 :]:
                    if first_owner == second_owner:
                        continue
                    if (
                        first in repository.declarations
                        and second in repository.declarations
                    ):
                        continue
                    if frozenset((first, second)) not in contrasts:
                        self.add(
                            "CHK.contrasts.required",
                            repository.definer(first)
                            or repository.definer(second)
                            or repository.registry_path,
                            f"{first} and {second} have equal normalized titles and no contrasts",
                            subject=first,
                        )

    # --- realizations ----------------------------------------------------------------

    def bindings(self) -> None:
        repository = self.repository
        members = set(repository.source_documents)
        outputs = generated_outputs(repository.root)
        for module in repository.declarations.values():
            listed: Counter = Counter()
            for realization in repository.realizations(repository.modules[module.id]):
                source = metadata_path(realization.document)
                listed.update(realization.entries)
                for entry in realization.pending:
                    if entry not in realization.entries:
                        self.add(
                            "CHK.binds.pending-subset",
                            source,
                            f"{realization.id} pending entry {entry} is not one of its entries",
                            subject=realization.id,
                        )
                    elif entry_exists(repository.root, entry):
                        self.add(
                            "CHK.binds.pending-subset",
                            source,
                            f"{realization.id} still marks {entry} pending although it exists",
                            subject=realization.id,
                        )
                for entry in realization.entries:
                    base = entry_base(entry)
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
                    if entry in realization.pending:
                        continue
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
        relates = {
            (relation["source"], relation["target"])
            for relation in repository.metadata_relations
            if relation["type"] == "relates"
        }
        for module in repository.declarations.values():
            for item in module.uses:
                relates.add(("uses", module.id, item["target"]))
            for item in module.contains:
                relates.add(("contains", module.id, item["target"]))
        for path, reading in repository.readings.items():
            unit = repository.units[path]
            for line, info, body in reading.mermaid:
                kind = diagram_type(body)
                if "illustrative" in info:
                    continue
                if kind not in {"flowchart", "graph"}:
                    self.add(
                        "CHK.view.marked",
                        path,
                        "a Mermaid block that is not a flowchart is marked illustrative",
                        line=line,
                    )
                    continue
                if unit.role != "module":
                    continue
                self.flowchart(path, unit.owner, line, body, relates)

    def resolve_label(self, owner: str, label: str) -> list[str]:
        repository = self.repository
        text = first_line(label)
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

    def flowchart(
        self, path: str, owner: str, line: int, body: str, relates: set
    ) -> None:
        try:
            nodes, edges = flowchart_model(body)
        except UndirectedEdgeError as error:
            self.add(
                "CHK.view.edges",
                path,
                f"checked flowchart edge must point in one declared direction: {error}",
                line=line,
            )
            return
        except DiagramError as error:
            self.add(
                "CHK.view.nodes",
                path,
                f"checked flowchart is unreadable: {error}",
                line=line,
            )
            return
        resolved: dict[str, str] = {}
        for node_id, label in nodes.items():
            matches = self.resolve_label(owner, label)
            if len(matches) != 1:
                self.add(
                    "CHK.view.nodes",
                    path,
                    f"flowchart node {first_line(label)!r} resolves to "
                    + (
                        "no node or Module"
                        if not matches
                        else f"several nodes: {matches}"
                    ),
                    line=line,
                )
                continue
            resolved[node_id] = matches[0]
        for source, label, target in edges:
            if label is None:
                self.add(
                    "CHK.view.edges",
                    path,
                    f"flowchart edge {source} -> {target} has no label",
                    line=line,
                )
            if source not in resolved or target not in resolved:
                continue
            first, second = resolved[source], resolved[target]
            if (
                (first, second) not in relates
                and ("uses", first, second) not in relates
                and ("contains", first, second) not in relates
            ):
                self.add(
                    "CHK.view.edges",
                    path,
                    f"flowchart edge {first} -> {second} matches no declared relates, uses or contains",
                    line=line,
                )

    # --- reconciliation -----------------------------------------------------------------

    def reconciliation(self) -> None:
        repository = self.repository
        for module in repository.declarations.values():
            target = repository.modules[module.id]
            context = set(repository._context_paths(target))
            owned = set(module.owns)
            requires: list[tuple[str, str, str]] = []
            for item in repository.imports:
                if (
                    item["document"] in owned
                    and item["concept"] in repository.concept_nodes
                ):
                    requires.append((item["concept"], item["document"], "imports"))
            for relation in repository.metadata_relations:
                if relation["document"] in owned and relation["type"] in {
                    "narrows",
                    "supersedes",
                    "relates",
                }:
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
                if not fragment.startswith(NODE_PREFIXES):
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
            covered.add(scenario.id)
            if scenario.owner not in listed.get(declaration.path, set()):
                self.findings.append(
                    Finding(
                        "CONCORDE-COVERAGE-002",
                        "warning",
                        declaration.path,
                        f"test {declaration.name} verifies {scenario.id}, but {scenario.owner} "
                        "does not bind this file",
                        "Bind the test to a realization of the scenario's Module.",
                        line=declaration.line,
                        subject_id=scenario.id,
                    )
                )
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


def generated_outputs(root: Path) -> set[str]:
    """Outputs the build records in generated/build-manifest.json (e.g. under .pi/)."""
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


def check_input_findings(
    repository: SpecRepository, inputs: list[tuple[str, str]] | None = None
) -> tuple[Finding, ...]:
    """Preflight every configured required input without executing checks or reading content."""
    findings = []
    for check_id, check in sorted(repository.checks.items()):
        for relative in check.get("inputs", []):
            try:
                state = check_input_members(repository.root, relative)
            except (SpecError, TypedDataError, OSError) as problem:
                error = check_input_error(check, relative, problem)
                findings.append(
                    Finding(
                        "CONCORDE-CHECK-001",
                        "error",
                        error.field,
                        f"{error.code}: {error}",
                        "Restore the required input or reconcile the configured check; do not skip missing inputs.",
                        subject_id=check_id,
                    )
                )
                state = (error.code, error.field, str(error))
            if inputs is not None:
                inputs.append((f"check-input:{check_id}:{relative}", digest(state)))
    return tuple(findings)


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
        findings.append(
            Finding(
                "CONCORDE-SOURCE-008",
                "error",
                ".concorde/config.json",
                str(problem),
                "Reconcile the project configuration, registry and Protocol binding and retry.",
            )
        )
    if repository is not None:
        if target_id and target_id != ".":
            repository.module(target_id)
        findings.extend(check_input_findings(repository, inputs))
        for target in repository.modules.values():
            artifacts.extend(
                member
                for member in target.sources
                if member in repository.source_documents
            )
        for path, unit in sorted(repository.units.items()):
            inputs.extend((member.path, member.digest) for member in unit.sources)
        findings.extend(spec_findings(repository))
        inputs.append((".concorde/config.json", config_digest))
        inputs.append((repository.registry_path, digest(repository.registry_bytes)))
        inputs.append(("protocol", repository.config["protocol"]["digest"]))
    counts = Counter(f.severity for f in findings)
    return ToolResult(
        "validate",
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
                "Protocol 12 structural checks (protocol/checks.md)",
                "registry mirror of the entries' module blocks",
                "configured check input availability and path safety",
                "stable-identity link fragments",
                "scenario verification declarations and coverage",
            ],
            "semantic_completeness": "not_proven",
        },
    )


__all__ = [
    "Checks",
    "DiagramError",
    "check_input_findings",
    "definition_ids",
    "flowchart_model",
    "normalize_title",
    "spec_findings",
    "validate_repository",
    "version_controlled",
]
