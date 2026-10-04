"""Protocol 16 Spec graph loader and the repository API every consumer reads.

The registry says which Modules exist and where each entry is. Every declaration is read from the
entries' ``module`` blocks, from the registered documents and from the project glossary the root
Module declares: the registry's mirrored fields are never trusted for the graph, only compared with
it by ``CHK.registry.mirror``. Documents are registered through ``owns`` and never discovered from
the filesystem or from links.

Loading collects problems as findings instead of stopping at the first one, so ``validate`` can
report every problem. A repository opened for runtime use (the default) refuses a Spec whose
structure cannot support a trustworthy boundary: an unreadable or unowned document, a broken
entry, an unknown relation target or a composition cycle.
"""

from __future__ import annotations

import copy

from dataclasses import dataclass, field
from pathlib import Path

from .content_model import (
    DocumentUnit,
    SourceMember,
    declaration_problems,
    envelope_problems,
    metadata_path,
)
from .errors import from_finding, system_cause
from .glossary import concept as glossary_concept
from .glossary import problems as glossary_problems
from .model import Finding
from .repository_base import (
    REFERENCE_SKIPPED_SUFFIXES,
    REGISTRY_PATH,
    REGISTRY_SCHEMA,
    Concept,
    Module,
    ModuleDefinitions,
    Realization,
    Requirement,
    Scenario,
    SpecContext,
    SpecDocument,
    SpecError,
    bound_by,
    unbindable,
    digest,
    entry_exists,
    expand_entry,
    identifier,
    is_directory_entry,
    is_identity,
    most_specific,
    read_file,
    reference_record,
)
from .syntax import Reading, parse_reading
from .typed_data import (
    DIGEST,
    PATH,
    STRING,
    array,
    canonical,
    check_schema,
    checked_path,
    decode,
    obj,
    safe_path,
)

# A query naming a Module accepts its identity or its registered record.
ModuleRef = str | Module

WARNING_CHECKS = frozenset(
    {
        "CHK.node.explained",
        "CHK.contains.root",
        "CHK.includes.redundant",
        "CHK.term.unlinked",
        "CHK.concept.local",
        "CHK.style.sentence-length",
        "CHK.style.semicolon",
        "CHK.style.one-obligation",
    }
)


def strictness(check: str) -> str:
    """A check's strictness: ``warning`` when a violation does not block structural
    conformance, ``error`` when it does."""
    return "warning" if check in WARNING_CHECKS else "error"


# Version of a resolved Spec context record; 4 adds the selected glossary entries (``terms``).
CONTEXT_SCHEMA = 4
NULLABLE_ID = {"anyOf": [STRING, {"type": "null"}]}
LISTING_ENTRY = {**STRING, "pattern": r"^[^/](?:[^/]*/)*[^/]*$"}
# One relation that selected a context source: ``owns``, ``contains`` and ``uses`` name a Module;
# ``includes`` also states whether it included a Module or one document.
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
    ]
}
# One declaration that selected a glossary entry: the Module owning it, a document or concept that
# mentions it, a Module relying on it, or a concept or node relating to it.
TERM_REASON = obj(
    {
        "relation": {
            "enum": [
                "owns",
                "mentions",
                "relies_on",
                "relates",
                "narrows",
                "supersedes",
            ]
        },
        "id": STRING,
    }
)
REFERENCE = {
    "anyOf": [
        obj({"kind": {"enum": ["module", "document"]}, "id": STRING}),
        obj({"kind": {"const": "external"}, "path": LISTING_ENTRY}),
    ]
}
# A Module's descriptor, as ``SpecRepository.module`` returns it.
TARGET_DESCRIPTOR = obj(
    {
        "id": STRING,
        "kind": {"const": "module"},
        "title": STRING,
        "documents": {**array(PATH, unique=True), "minItems": 1},
        "references": array(REFERENCE, unique=True),
        "parent": NULLABLE_ID,
        "uses": array(STRING, unique=True),
        "files": array(LISTING_ENTRY, unique=True),
    }
)


def context_record_schema() -> dict:
    """The closed schema of a Spec context record (``SpecContext.value``)."""
    source = obj(
        {
            "document_id": STRING,
            "owner": STRING,
            "path": PATH,
            "digest": DIGEST,
            "role": {"enum": ["reading", "metadata"]},
            "reasons": array(SELECTION_REASON, unique=True),
        }
    )
    term = obj(
        {
            # The glossary entry exactly as written; its shape is CHK.glossary.schema's.
            "entry": {"type": "object", "additionalProperties": {}},
            "reasons": {**array(TERM_REASON, unique=True), "minItems": 1},
        }
    )
    return obj(
        {
            "schema_version": {"const": CONTEXT_SCHEMA},
            "query_id": STRING,
            "query_kind": {"enum": ["module", "scenario"]},
            "module_id": STRING,
            "reading_entry": PATH,
            "documents": array(PATH, unique=True),
            "references": array(REFERENCE, unique=True),
            "registration": TARGET_DESCRIPTOR,
            "sources": array(source, unique=True),
            "terms": array(term, unique=True),
        }
    )


@dataclass(frozen=True)
class ModuleDeclaration:
    """A Module's own declarations: its entry's ``module`` block, well-formed parts only."""

    id: str
    title: str
    entry: str
    owns: tuple[str, ...]
    contains: tuple[dict, ...]
    uses: tuple[dict, ...]
    includes: tuple[dict, ...]
    participates: tuple[dict, ...]
    block: dict | None
    record: dict
    glossary: str | None = None

    def relations(self, kind: str) -> tuple[dict, ...]:
        return getattr(self, kind)


@dataclass(frozen=True)
class NodeRef:
    """One declared node: its type, owner and defining document."""

    id: str
    type: str
    owner: str
    document: str
    title: str
    line: int | None = None


@dataclass
class _Load:
    findings: list[Finding] = field(default_factory=list)
    fatal: list[Finding] = field(default_factory=list)
    # The error behind a finding, by the finding's identity, kept as its cause.
    causes: dict[int, SpecError] = field(default_factory=dict)


class DocumentUnitRepository:
    """The loaded Protocol 16 graph of one project checkout."""

    def __init__(
        self,
        project_root: Path | str,
        *,
        registry_bytes: bytes | None = None,
        document_overrides: dict[str, bytes] | None = None,
        _defer_document_admission: bool = False,
    ):
        root = Path(project_root)
        if root.is_symlink() or not root.is_dir():
            raise SpecError(
                f"the project root {root} is not a real directory",
                "unsafe_path",
                path=str(root),
                reason="Spec tooling loads a project only from a real directory",
                remediation="pass the real path of the project's worktree",
            )
        self.root = root.resolve()
        self.registry_path = REGISTRY_PATH
        self._registry_override = (
            bytes(registry_bytes) if registry_bytes is not None else None
        )
        self.registry_bytes = (
            self._registry_override
            if self._registry_override is not None
            else read_file(self.root, self.registry_path)
        )
        self._draft_admission = _defer_document_admission
        self.document_overrides: dict[str, bytes] = {}
        for path, raw in (document_overrides or {}).items():
            if not isinstance(raw, bytes):
                raise SpecError(
                    f"the source override of {path} is a {type(raw).__name__}, not bytes",
                    "invalid_proposal",
                    path=str(path),
                    reason="a source override replaces a document's exact bytes",
                )
            self.document_overrides[safe_path(path)] = raw
        self.protocol_assets: dict[str, bytes] = getattr(self, "protocol_assets", {})
        self._load = _Load()
        self.declarations: dict[str, ModuleDeclaration] = {}
        self.modules: dict[str, Module] = {}
        self.document_targets: dict[str, list[str]] = {}
        self.units: dict[str, DocumentUnit] = {}
        # Every registered document member's bytes as read, admitted or not; None when unreadable.
        self.member_bytes: dict[str, bytes | None] = {}
        self.readings: dict[str, Reading] = {}
        self.nodes: dict[str, NodeRef] = {}
        self.concept_nodes: dict[str, Concept] = {}
        self.realization_nodes: dict[str, Realization] = {}
        self.requirement_nodes: dict[str, Requirement] = {}
        self.scenario_nodes: dict[str, Scenario] = {}
        self.contract_nodes: dict[str, dict] = {}
        self.mentions: list[dict] = []
        self.metadata_relations: list[dict] = []
        self.glossary_path: str | None = None
        self.glossary_bytes: bytes | None = None
        self.glossary_value: dict | None = None
        self.glossary_entries: dict[str, dict] = {}
        self._terms_cache: dict[str, dict[str, list[dict]]] = {}
        self._identity_paths: dict[str, str] = {}
        self._external_cache: dict[str, tuple[tuple[str, ...], str]] = {}
        self._context_cache: dict[str, dict[str, list[dict]]] = {}
        self._registry()
        self._documents()
        self._entries()
        self._targets()
        self._glossary()
        outside = sorted(
            self.document_overrides.keys()
            - self.source_documents.keys()
            - {self.glossary_path}
        )
        if outside:
            raise SpecError(
                "source overrides name paths that are no registered document member and not "
                "the glossary: " + ", ".join(outside),
                "permission_denied",
                path=outside[0],
                reason="an override may only replace the bytes of a registered Spec document or "
                "of the project glossary",
            )
        if self._load.fatal and not _defer_document_admission:
            fatal = self._load.fatal
            first = fatal[0]
            raise SpecError(
                f"the Specs of {self.root} cannot be loaded: {len(fatal)} fatal "
                f"problem(s), each a cause; the first is {first.rule_id} at "
                f"{first.source}: {first.message}",
                _error_code(first.rule_id),
                path=first.source or None,
                reason="a registry, entry or document structure that breaks these checks "
                "cannot support a trustworthy boundary, so the repository is refused",
                remediation="repair every cause, then run `concorde spec-validation`",
                causes=[self._finding_cause(item) for item in fatal],
            )

    # --- loading ------------------------------------------------------------------------

    @property
    def load_findings(self) -> tuple[Finding, ...]:
        return tuple(self._load.findings)

    def _problem(
        self,
        check: str,
        source: str,
        message: str,
        *,
        line: int | None = None,
        subject: str | None = None,
        fatal: bool = False,
        remediation: str = "Repair the declaration so the Spec graph is well formed.",
        cause: BaseException | None = None,
    ) -> None:
        finding = Finding(
            check,
            strictness(check),
            source,
            message,
            remediation,
            line=line,
            subject_id=subject,
        )
        self._load.findings.append(finding)
        if fatal:
            self._load.fatal.append(finding)
        if cause is not None:
            self._load.causes[id(finding)] = _as_cause(cause)

    def _finding_cause(self, finding: Finding) -> SpecError:
        """A fatal finding as a cause of the load error, with the error behind it, if any, as its
        own cause."""
        error = from_finding(finding, _error_code(finding.rule_id))
        underlying = self._load.causes.get(id(finding))
        if underlying is not None:
            error.causes = (underlying,)
        return error

    def _raw(self, path: str) -> bytes:
        return (
            self.document_overrides[path]
            if path in self.document_overrides
            else read_file(self.root, path)
        )

    def _registry(self) -> None:
        try:
            value = decode(self.registry_bytes.decode("utf-8"))
        except (ValueError, UnicodeError) as error:
            raise SpecError(
                f"registry is not JSON: {error}",
                "unsupported_profile",
                path=self.registry_path,
                reason="the Spec registry is a strict JSON document",
                remediation="repair the JSON syntax of the registry, or restore it from Git",
                causes=[_as_cause(error, path=self.registry_path)],
            ) from error
        if (
            not isinstance(value, dict)
            or set(value) != {"schema_version", "modules"}
            or type(value["schema_version"]) is not int
            or value["schema_version"] != REGISTRY_SCHEMA
            or not isinstance(value["modules"], list)
            or not value["modules"]
        ):
            raise SpecError(
                'the Spec registry must be {"schema_version": 3, "modules": [...]} '
                "(Protocol 16); migrate explicitly",
                "unsupported_profile",
            )
        self.registry = value
        self.records: list[dict] = []
        seen: set[str] = set()
        for record in value["modules"]:
            if (
                not isinstance(record, dict)
                or not is_identity(record.get("id"))
                or not isinstance(record.get("entry"), str)
            ):
                self._problem(
                    "CHK.registry.mirror",
                    self.registry_path,
                    f"registry record needs a Module identity and an entry path: {record!r}"[
                        :300
                    ],
                    fatal=True,
                )
                continue
            if record["id"] in seen:
                self._problem(
                    "CHK.registry.mirror",
                    self.registry_path,
                    f"the registry lists Module {record['id']} more than once",
                    subject=record["id"],
                    fatal=True,
                )
                continue
            seen.add(record["id"])
            self.records.append(record)
        for record in self.records:
            self._module(record)
        for path, owners in self.document_targets.items():
            if len(owners) > 1:
                self._problem(
                    "CHK.owns.unique",
                    path,
                    f"document is owned by several Modules: {', '.join(owners)}",
                    fatal=True,
                )

    def _module(self, record: dict) -> None:
        module_id, entry = record["id"], record["entry"]
        try:
            safe_path(entry)
            valid_entry = (
                entry.endswith("module.md") and entry.split("/")[-1] == "module.md"
            )
        except ValueError:
            valid_entry = False
        if not valid_entry:
            self._problem(
                "CHK.document.entry",
                self.registry_path,
                f"Module {module_id} entry must be a reading path ending in module.md: {entry!r}",
                subject=module_id,
                fatal=True,
            )
            return
        block = None
        try:
            metadata = decode(self._raw(metadata_path(entry)).decode("utf-8"))
            block = metadata.get("module") if isinstance(metadata, dict) else None
            document = metadata.get("document") if isinstance(metadata, dict) else None
            owner = document.get("owner") if isinstance(document, dict) else None
            if owner != module_id:
                self._problem(
                    "CHK.registry.mirror",
                    self.registry_path,
                    f"registry record {module_id} names entry {entry}, whose owner is {owner!r}",
                    subject=module_id,
                    fatal=True,
                )
        except (SpecError, ValueError, UnicodeError, OSError) as error:
            self._problem(
                "CHK.document.pair",
                metadata_path(entry),
                f"entry metadata of {module_id} cannot be read: {error}",
                subject=module_id,
                fatal=True,
                cause=error,
            )
        if not isinstance(block, dict):
            block = None
        title = (
            block.get("title")
            if block
            and isinstance(block.get("title"), str)
            and block.get("title").strip()
            else record.get("title")
            if isinstance(record.get("title"), str)
            else module_id
        )
        owns_raw = block.get("owns") if block else None
        owns: list[str] = []
        if isinstance(owns_raw, list):
            for path in owns_raw:
                if not isinstance(path, str):
                    continue
                try:
                    safe_path(path)
                    if not path.endswith(".md"):
                        raise ValueError(path)
                except ValueError:
                    self._problem(
                        "CHK.document.path",
                        metadata_path(entry),
                        f"owned reading path is not a canonical Markdown path: {path!r}",
                        subject=module_id,
                        fatal=True,
                    )
                    continue
                if path not in owns:
                    owns.append(path)
        if entry not in owns:
            if block is not None:
                self._problem(
                    "CHK.document.entry",
                    metadata_path(entry),
                    f"owns of {module_id} must include its entry {entry}",
                    subject=module_id,
                    fatal=True,
                )
            owns.insert(0, entry)

        def relations(name: str, required: set[str], optional: set[str] = frozenset()):
            # A malformed item, which validation reports against the schema, declares nothing;
            # an identity that is no string (``target``, ``kind``, ``contract``) is malformed.
            items = block.get(name) if block else None
            if not isinstance(items, list):
                return ()
            return tuple(
                item
                for item in items
                if isinstance(item, dict)
                and required <= item.keys()
                and not item.keys() - required - optional
                and all(
                    isinstance(item[key], str)
                    for key in ("target", "kind", "contract")
                    if key in required
                )
            )

        declaration = ModuleDeclaration(
            module_id,
            title,
            entry,
            tuple(owns),
            relations("contains", {"target", "meaning"}, {"relies_on"}),
            relations("uses", {"target", "meaning"}, {"relies_on"}),
            relations("includes", {"kind", "target", "reason"}),
            relations(
                "participates", {"contract", "version", "role", "peer", "meaning"}
            ),
            block,
            record,
            block.get("glossary")
            if block and isinstance(block.get("glossary"), str)
            else None,
        )
        self.declarations[module_id] = declaration
        for path in owns:
            self.document_targets.setdefault(path, []).append(module_id)

    @property
    def source_documents(self) -> dict[str, str]:
        return {
            member: path
            for path in self.document_targets
            for member in (path, metadata_path(path))
        }

    def _documents(self) -> None:
        physical: dict[tuple[int, int], str] = {}
        for path in sorted(self.document_targets):
            owner = self.document_targets[path][0]
            members = (path, metadata_path(path))
            raw: dict[str, bytes] = {}
            for member in members:
                try:
                    if member not in self.document_overrides:
                        candidate = checked_path(self.root, member)
                        if candidate.is_file():
                            stat = candidate.stat()
                            key = (stat.st_dev, stat.st_ino)
                            if key in physical:
                                self._problem(
                                    "CHK.document.path",
                                    member,
                                    f"physical alias of {physical[key]}",
                                    fatal=True,
                                )
                            physical[key] = member
                    raw[member] = self._raw(member)
                except (SpecError, OSError, ValueError) as error:
                    self._problem(
                        "CHK.document.path"
                        if "symlink" in str(error)
                        else "CHK.document.pair",
                        member,
                        f"document member cannot be read: {error}",
                        subject=owner,
                        fatal=True,
                        cause=error,
                    )
            self.member_bytes.update({member: raw.get(member) for member in members})
            if len(raw) != 2:
                continue
            try:
                text = raw[path].decode("utf-8")
                if not text.strip():
                    raise UnicodeError("reading member is empty")
            except UnicodeError as error:
                self._problem(
                    "CHK.document.pair",
                    path,
                    f"reading must be nonempty UTF-8 Markdown: {error}",
                    subject=owner,
                    fatal=True,
                    cause=error,
                )
                continue
            try:
                value = decode(raw[members[1]].decode("utf-8"))
            except (ValueError, UnicodeError) as error:
                self._problem(
                    "CHK.document.schema",
                    members[1],
                    f"metadata is not UTF-8 JSON with unique keys: {error}",
                    subject=owner,
                    fatal=True,
                    cause=error,
                )
                continue
            entry = self.declarations[owner].entry == path
            envelope = envelope_problems(value, entry=entry)
            for check, message in envelope:
                self._problem(check, members[1], message, subject=owner, fatal=True)
            if envelope:
                continue
            document = value["document"]
            if document["owner"] != owner:
                self._problem(
                    "CHK.document.pair"
                    if document["owner"] in self.declarations
                    else "CHK.node.owner",
                    members[1],
                    f"document owner {document['owner']} differs from its registered owner {owner}",
                    subject=owner,
                    fatal=True,
                )
                continue
            if entry and document["role"] != "module":
                self._problem(
                    "CHK.document.entry",
                    members[1],
                    "the entry module.md has role module",
                    subject=owner,
                    fatal=True,
                )
            identity = document["id"]
            if identity in self._identity_paths or identity in self.declarations:
                self._problem(
                    "CHK.node.id",
                    members[1],
                    f"document identity {identity} is not unique",
                    subject=identity,
                    fatal=True,
                )
                continue
            for check, message in declaration_problems(value):
                self._problem(check, members[1], message, subject=identity)
            unit = DocumentUnit(
                identity,
                owner,
                document["role"],
                SourceMember(path, "reading", raw[path]),
                SourceMember(members[1], "metadata", raw[members[1]]),
                value,
            )
            self.units[path] = unit
            self._identity_paths[identity] = path
            reading = parse_reading(text)
            self.readings[path] = reading
            for problem in reading.problems:
                self._problem(problem.check, path, problem.message, line=problem.line)
            self._declarations(unit, reading)

    def _entries(self) -> None:
        """CHK.document.entry for a Module owning several module-role module.md documents."""
        for module in self.declarations.values():
            entries = [
                path
                for path in module.owns
                if path in self.units
                and self.units[path].role == "module"
                and path.split("/")[-1] == "module.md"
            ]
            if len(entries) > 1:
                self._problem(
                    "CHK.document.entry",
                    metadata_path(module.entry),
                    f"Module {module.id} owns several module-role module.md documents: "
                    f"{entries}",
                    subject=module.id,
                    fatal=True,
                )

    def _register(self, node: NodeRef) -> bool:
        previous = self.nodes.get(node.id)
        if (
            previous is None
            and node.id not in self.declarations
            and node.id not in self._identity_paths
        ):
            self.nodes[node.id] = node
            return True
        if previous is not None and previous.type == node.type:
            self._problem(
                "CHK.defines.once",
                node.document,
                f"{node.type} {node.id} is also defined in {previous.document}",
                line=node.line,
                subject=node.id,
            )
        else:
            self._problem(
                "CHK.node.id",
                node.document,
                f"identity {node.id} is already used by "
                + (
                    f"a {previous.type} in {previous.document}"
                    if previous
                    else "a Module or document"
                ),
                line=node.line,
                subject=node.id,
            )
        return False

    def _declarations(self, unit: DocumentUnit, reading: Reading) -> None:
        path, owner, role = unit.reading.path, unit.owner, unit.role
        value = unit.value
        for record in value.get("defines", []):
            if not isinstance(record, dict) or not is_identity(record.get("id")):
                continue
            kind = record.get("type")
            title = record.get("title") if isinstance(record.get("title"), str) else ""
            meaning = (
                record.get("meaning") if isinstance(record.get("meaning"), str) else ""
            )
            if kind == "realization":
                entries = record.get("entries")
                entries = (
                    tuple(x for x in entries if isinstance(x, str))
                    if isinstance(entries, list)
                    else ()
                )
                if not self._register(
                    NodeRef(record["id"], "realization", owner, path, title)
                ):
                    continue
                self.realization_nodes[record["id"]] = Realization(
                    record["id"], title, owner, path, meaning, entries
                )
        for identity, title, line, statement in reading.requirements:
            if self._register(
                NodeRef(identity, "requirement", owner, path, title, line)
            ):
                self.requirement_nodes[identity] = Requirement(
                    identity, title, statement, owner, path, line
                )
                if role != "implementation":
                    self._problem(
                        "CHK.defines.role",
                        path,
                        f"requirement {identity} is defined in a module document",
                        line=line,
                        subject=identity,
                    )
        for identity, title, line, steps in reading.scenarios:
            if self._register(NodeRef(identity, "scenario", owner, path, title, line)):
                self.scenario_nodes[identity] = Scenario(
                    identity, title, owner, path, line, steps
                )
                if role != "implementation":
                    self._problem(
                        "CHK.defines.role",
                        path,
                        f"scenario {identity} is defined in a module document",
                        line=line,
                        subject=identity,
                    )
        from .syntax import contract_problems

        for line, body in reading.contracts:
            contract, problems = contract_problems(body)
            for message in problems:
                self._problem("CHK.contract.fence", path, message, line=line)
            if not isinstance(contract, dict) or not is_identity(contract.get("id")):
                continue
            title = contract["id"]
            if self._register(
                NodeRef(contract["id"], "contract", owner, path, title, line)
            ):
                self.contract_nodes[contract["id"]] = {
                    **contract,
                    "source": path,
                    "owner": owner,
                    "line": line,
                }
                if role != "implementation":
                    self._problem(
                        "CHK.defines.role",
                        path,
                        f"contract {contract['id']} is defined in a module document",
                        line=line,
                        subject=contract["id"],
                    )
        from .syntax import link_target

        # Every link whose fragment is a concept identity is a term link (``mentions``); whether
        # it addresses the glossary is ``CHK.term.link``'s question, once the glossary is known.
        for line, href in reading.links:
            target = link_target(path, href)
            if target is None or not target[1].startswith("concept."):
                continue
            self.mentions.append(
                {
                    "document": path,
                    "owner": owner,
                    "line": line,
                    "href": href,
                    "path": target[0],
                    "concept": target[1],
                }
            )
        for record in value.get("relations", []):
            if isinstance(record, dict) and record.get("type") == "relates":
                self.metadata_relations.append(
                    {**record, "document": path, "owner": owner}
                )

    def _targets(self) -> None:
        parents: dict[str, list[str]] = {}
        for module in self.declarations.values():
            for item in module.contains:
                parents.setdefault(item["target"], []).append(module.id)
            for kind in ("contains", "uses"):
                for item in module.relations(kind):
                    if item["target"] not in self.declarations:
                        self._problem(
                            "CHK.relation.endpoints",
                            metadata_path(module.entry),
                            f"{kind} target {item['target']} is not a registered Module",
                            subject=module.id,
                            fatal=True,
                        )
            for item in module.includes:
                if item["kind"] == "module" and item["target"] not in self.declarations:
                    self._problem(
                        "CHK.relation.endpoints",
                        metadata_path(module.entry),
                        f"includes Module {item['target']} is not registered",
                        subject=module.id,
                        fatal=True,
                    )
                if (
                    item["kind"] == "document"
                    and item["target"] not in self._identity_paths
                ):
                    self._problem(
                        "CHK.relation.endpoints",
                        metadata_path(module.entry),
                        f"includes document {item['target']} is not registered",
                        subject=module.id,
                        fatal=True,
                    )
        for child, owners in parents.items():
            if len(set(owners)) > 1:
                self._problem(
                    "CHK.contains.single-parent",
                    metadata_path(self.declarations[owners[1]].entry),
                    f"Module {child} is contained by several parents: {', '.join(sorted(set(owners)))}",
                    subject=child,
                    fatal=True,
                )
        for module_id in self.declarations:
            seen = {module_id}
            current = module_id
            while parents.get(current):
                current = parents[current][0]
                if current in seen:
                    self._problem(
                        "CHK.contains.acyclic",
                        metadata_path(self.declarations[module_id].entry),
                        f"composition cycle through {module_id}",
                        subject=module_id,
                        fatal=True,
                    )
                    break
                seen.add(current)
        for module in self.declarations.values():
            realizations = [
                item
                for item in self.realization_nodes.values()
                if item.owner == module.id
            ]
            files = sorted({entry for item in realizations for entry in item.entries})
            parent = parents.get(module.id, [None])[0]
            self.modules[module.id] = Module(
                module.id,
                "module",
                module.title,
                module.owns,
                parent,
                tuple(dict.fromkeys(item["target"] for item in module.uses)),
                tuple(files),
                tuple(
                    dict.fromkeys(
                        (item["kind"], item["target"])
                        for item in module.includes
                        if item["kind"] in {"module", "document", "external"}
                    )
                ),
                module.entry,
            )

    def _glossary(self) -> None:
        """Load the glossary the root Module declares: its concepts and their relations."""
        declarers = [module for module in self.declarations.values() if module.glossary]
        if not declarers:
            return
        first = declarers[0]
        for other in declarers[1:]:
            self._problem(
                "CHK.glossary.declared",
                metadata_path(other.entry),
                f"{other.id} declares a glossary ({other.glossary}) although "
                f"{first.id} already declares {first.glossary}; a project has one glossary",
                subject=other.id,
            )
        for module in declarers:
            parent = (
                self.modules[module.id].parent if module.id in self.modules else None
            )
            if parent is not None:
                self._problem(
                    "CHK.glossary.declared",
                    metadata_path(module.entry),
                    f"{module.id} declares the glossary but is contained by {parent}; only a "
                    "Module without a parent declares it",
                    subject=module.id,
                )
        path = first.glossary
        try:
            safe_path(path)
        except ValueError:
            return  # CHK.glossary.declared reports the malformed path from the module block
        self.glossary_path = path
        try:
            raw = self._raw(path)
        except (SpecError, OSError, ValueError) as error:
            self._problem(
                "CHK.glossary.declared",
                metadata_path(first.entry),
                f"the glossary {path} that {first.id} declares cannot be read: {error}",
                subject=first.id,
            )
            return
        self.glossary_bytes = raw
        try:
            value = decode(raw.decode("utf-8"))
        except (ValueError, UnicodeError) as error:
            self._problem(
                "CHK.glossary.schema",
                path,
                f"the glossary is not UTF-8 JSON with unique keys: {error}",
            )
            return
        self.glossary_value = value
        for check, message, subject in glossary_problems(value):
            self._problem(check, path, message, subject=subject)
        items = value.get("concepts") if isinstance(value, dict) else None
        for entry in items if isinstance(items, list) else ():
            if not isinstance(entry, dict) or not is_identity(entry.get("id")):
                continue
            identity = entry["id"]
            if identity in self.glossary_entries:
                self._problem(
                    "CHK.node.id",
                    path,
                    f"the glossary lists concept {identity} more than once",
                    subject=identity,
                )
                continue
            node = glossary_concept(entry, path)
            if node.owner not in self.declarations:
                self._problem(
                    "CHK.node.owner",
                    path,
                    f"concept {identity} names owner {node.owner!r}, which is no registered "
                    "Module",
                    subject=identity,
                    fatal=True,
                )
                continue
            if not self._register(
                NodeRef(identity, "concept", node.owner, node.document, node.title)
            ):
                continue
            self.glossary_entries[identity] = entry
            self.concept_nodes[identity] = node

    def glossary_relations(self) -> list[dict]:
        """Every relation a glossary entry declares, as records naming their declaring concept."""
        result = []
        for concept in self.concept_nodes.values():
            base = {"document": concept.source, "owner": concept.owner}
            for target in concept.narrows:
                result.append(
                    {"type": "narrows", "source": concept.id, "target": target, **base}
                )
            if concept.supersedes is not None:
                result.append(
                    {
                        "type": "supersedes",
                        "source": concept.id,
                        "target": concept.supersedes,
                        **base,
                    }
                )
            for item in concept.contrasts:
                result.append(
                    {
                        "type": "contrasts",
                        "source": concept.id,
                        "target": item["target"],
                        "reason": item.get("reason"),
                        **base,
                    }
                )
            for item in concept.relates:
                result.append(
                    {
                        "type": "relates",
                        "source": concept.id,
                        "target": item["target"],
                        "verb": item.get("verb"),
                        **base,
                    }
                )
        return result

    # --- identities and documents --------------------------------------------------------

    @property
    def root_module(self) -> str:
        """The root Module: the one Module no other Module contains (the first one if several)."""
        roots = [module.id for module in self.modules.values() if module.parent is None]
        return roots[0] if roots else next(iter(self.modules))

    def document_path(self, document_id: str) -> str:
        if document_id not in self._identity_paths:
            raise SpecError(
                f"{document_id} names no registered Spec document",
                "invalid_target",
                subject=document_id,
            )
        return self._identity_paths[document_id]

    def unit(self, path: str) -> DocumentUnit:
        if path not in self.document_targets:
            raise SpecError(
                f"{path} is not the reading document of any registered Spec document",
                "permission_denied",
                path=path,
                reason="only registered Spec documents are admitted",
            )
        if path not in self.units:
            problems = [
                item
                for item in self._load.findings
                if item.source in (path, metadata_path(path))
            ]
            raise SpecError(
                f"the document {path} cannot be admitted"
                + (f"; {len(problems)} problem(s), each a cause" if problems else ""),
                "invalid_spec",
                path=path,
                causes=[from_finding(item) for item in problems],
            )
        return self.units[path]

    def document(self, path: str) -> SpecDocument:
        unit = self.unit(path)
        text = unit.reading.content.decode("utf-8")
        return SpecDocument(
            path,
            text,
            unit.reading.digest,
            unit.document_id,
            unit.owner,
            unit.declarations,
            text,
        )

    def documents(self, module: ModuleRef) -> tuple[SpecDocument, ...]:
        """The documents a Module owns, entry first."""
        return tuple(self.document(path) for path in self._resolve(module).documents)

    def reading(self, path: str) -> Reading:
        self.unit(path)
        return self.readings[path]

    def source_bytes(self, path: str) -> bytes:
        reading = self.source_documents.get(path)
        if reading is None:
            raise SpecError(
                f"{path} is not a member of any registered Spec document",
                "permission_denied",
                path=path,
                reason="only registered Spec document members are served as sources",
            )
        self.unit(reading)
        # Return current bytes, not cached bytes: materialization must detect changes after freeze.
        return self._raw(path)

    def loaded_bytes(self, path: str) -> bytes:
        """The bytes of a registered document member or of the glossary as this repository loaded
        them, overrides included: the snapshot every query answers from."""
        if path == self.glossary_path and self.glossary_bytes is not None:
            return self.glossary_bytes
        raw = self.member_bytes.get(path)
        if raw is None:
            raise SpecError(
                f"{path} is no loaded member of a registered Spec document and not the glossary",
                "permission_denied",
                path=path,
                reason="a repository answers only from the sources it loaded",
            )
        return raw

    def source_is_overridden(self, path: str) -> bool:
        reading = self.source_documents.get(path)
        return reading is not None and (
            reading in self.document_overrides
            or metadata_path(reading) in self.document_overrides
        )

    def source_records(self, path: str, reasons: list[dict]) -> list[dict]:
        unit = self.unit(path)
        return [
            {
                "document_id": unit.document_id,
                "owner": unit.owner,
                "path": member.path,
                "role": member.role,
                "digest": member.digest,
                "reasons": reasons,
            }
            for member in unit.sources
        ]

    def validate_source_records(self, records: list[dict]) -> None:
        """A granted document contains both members exactly once with consistent identity/owner."""
        seen: set[str] = set()
        selected: set[str] = set()
        provenance: dict[str, object] = {}
        for record in records:
            path = record["path"]
            reading = self.source_documents.get(path)
            if reading is None or path in seen:
                raise SpecError(
                    f"the context lists {path} "
                    + (
                        "twice"
                        if path in seen
                        else "although it is no registered document member"
                    ),
                    "invalid_context",
                    path=path,
                )
            unit = self.unit(reading)
            role = "reading" if path == reading else "metadata"
            if (
                record.get("document_id") != unit.document_id
                or record.get("owner") != unit.owner
                or record.get("role") != role
            ):
                raise SpecError(
                    f"the context record of {path} says role {record.get('role')!r}, document "
                    f"{record.get('document_id')!r}, owner {record.get('owner')!r}; the document "
                    f"has role {role!r}, identity {unit.document_id!r}, owner {unit.owner!r}",
                    "invalid_context",
                    path=path,
                )
            reasons = record.get("reasons")
            if reading in provenance and provenance[reading] != reasons:
                raise SpecError(
                    f"the two members of {reading} carry different selection reasons: "
                    f"{provenance[reading]!r} and {reasons!r}"[:400],
                    "invalid_context",
                    path=path,
                )
            provenance[reading] = reasons
            seen.add(path)
            selected.add(reading)
        expected = {
            member for path in selected for member in (path, metadata_path(path))
        }
        if seen != expected:
            missing = sorted(expected - seen)
            raise SpecError(
                "the context grants a document without its other member: "
                + ", ".join(missing),
                "invalid_context",
                path=missing[0] if missing else None,
                reason="a document is granted with both its reading and its metadata, never "
                "one of them alone",
            )

    # --- Modules and composition ---------------------------------------------------------

    def _resolve(self, module: ModuleRef) -> Module:
        identity = module.id if isinstance(module, Module) else module
        if identity not in self.modules:
            raise SpecError(
                f"{identity} is not a registered Module; registered: "
                + ", ".join(sorted(self.modules)),
                "unknown_target",
                subject=str(identity),
                path=self.registry_path,
            )
        return self.modules[identity]

    def module(self, module_id: str, scenario: str | None = None) -> Module:
        """One registered Module; ``scenario``, when given, must be a scenario it owns."""
        module = self._resolve(module_id)
        if scenario is not None:
            node = self.scenario_nodes.get(scenario)
            if node is None or node.owner != module.id:
                raise SpecError(
                    f"the focus {scenario} "
                    + (
                        "is no declared scenario"
                        if node is None
                        else f"belongs to {node.owner}, not to {module.id}"
                    ),
                    "invalid_focus",
                    subject=scenario,
                )
        return module

    def module_declaration(self, module_id: str) -> ModuleDeclaration:
        if module_id not in self.declarations:
            raise SpecError(
                f"{module_id} is not a declared Module; declared: "
                + ", ".join(sorted(self.declarations)),
                "unknown_target",
                subject=module_id,
            )
        return self.declarations[module_id]

    def contained(self, module: ModuleRef) -> tuple[Module, ...]:
        """The Modules this Module ``contains``, in registry order."""
        parent = self._resolve(module).id
        return tuple(item for item in self.modules.values() if item.parent == parent)

    def definer(self, identity: str) -> str | None:
        """The document defining a node, or None for an unknown identity."""
        node = self.nodes.get(identity)
        return node.document if node else None

    def selection(self, relation: dict) -> tuple[str, ...]:
        """The documents one ``contains``, ``uses`` or ``includes`` declaration selects."""
        kind = relation.get("kind", "module")
        target = relation["target"]
        if kind == "document":
            path = self._identity_paths.get(target)
            return (path,) if path else ()
        if kind == "external" or target not in self.declarations:
            return ()
        module = self.declarations[target]
        if kind == "module" and "relies_on" in relation:
            selected = [module.entry]
            for identity in relation["relies_on"]:
                node = self.nodes.get(identity)
                if (
                    node is not None
                    and node.owner == target
                    and node.document not in selected
                ):
                    selected.append(node.document)
            return tuple(selected)
        return tuple(module.owns)

    # --- read sets: SpecContext ----------------------------------------------------------

    def _query(self, query_id: str) -> tuple[Module, str]:
        if query_id in self.modules:
            return self.modules[query_id], "module"
        scenario = self.scenario_nodes.get(query_id)
        if scenario is not None:
            return self.modules[scenario.owner], "scenario"
        raise SpecError(
            f"{query_id} names neither a registered Module nor a declared scenario",
            "invalid_target",
            subject=query_id,
            reason="a context is computed for a Module or for the owner of a scenario",
        )

    def _context_paths(self, module: ModuleRef) -> dict[str, list[dict]]:
        """Spec(M) with every relation that selected each document (one level, never recursive).

        A file shared with another Module adds no document: binding a writing task to every
        binding Module is the caller's decision.
        """
        target = self._resolve(module)
        key = target.id
        if key in self._context_cache:
            return {
                path: list(reasons)
                for path, reasons in self._context_cache[key].items()
            }
        declaration = self.declarations[target.id]
        paths: dict[str, list[dict]] = {}

        def add(documents, reason) -> None:
            for path in documents:
                reasons = paths.setdefault(path, [])
                if reason not in reasons:
                    reasons.append(reason)

        add(declaration.owns, {"relation": "owns", "id": target.id})
        for kind in ("contains", "uses"):
            for item in declaration.relations(kind):
                add(
                    self.selection({**item, "kind": "module"}),
                    {"relation": kind, "id": item["target"]},
                )
        for item in declaration.includes:
            if item["kind"] in {"module", "document"}:
                add(
                    self.selection({"kind": item["kind"], "target": item["target"]}),
                    {
                        "relation": "includes",
                        "kind": item["kind"],
                        "id": item["target"],
                    },
                )
        result = {
            path: sorted(
                paths[path],
                key=lambda reason: (
                    reason["relation"],
                    reason.get("kind", ""),
                    reason["id"],
                ),
            )
            for path in sorted(paths)
            if path in self.document_targets
        }
        self._context_cache[key] = result
        return {path: list(reasons) for path, reasons in result.items()}

    def terms(self, module: ModuleRef) -> dict[str, list[dict]]:
        """``Terms(M)`` with every declaration that selected each concept (Protocol term selection).

        The seeds are M's own concepts, the concepts the documents of ``Spec(M)`` mention or
        relate to, and the concepts M's ``relies_on`` names; the closure follows the mentions,
        narrows, supersedes and concept-targeted relates of every selected entry. The closure
        stays inside the glossary and never adds a document.
        """
        target = self._resolve(module)
        if target.id in self._terms_cache:
            return {
                key: list(value) for key, value in self._terms_cache[target.id].items()
            }
        concepts = self.concept_nodes
        selected: dict[str, list[dict]] = {}
        queue: list[str] = []

        def add(identity: str, relation: str, source: str) -> None:
            if identity not in concepts:
                return
            reasons = selected.setdefault(identity, [])
            reason = {"relation": relation, "id": source}
            if reason not in reasons:
                reasons.append(reason)
            if len(reasons) == 1:
                queue.append(identity)

        for concept in concepts.values():
            if concept.owner == target.id:
                add(concept.id, "owns", target.id)
        paths = set(self._context_paths(target))
        for item in self.mentions:
            if item["document"] in paths:
                add(
                    item["concept"],
                    "mentions",
                    self.units[item["document"]].document_id,
                )
        for relation in self.metadata_relations:
            if relation["document"] in paths and isinstance(
                relation.get("target"), str
            ):
                add(relation["target"], "relates", relation["source"])
        declaration = self.declarations[target.id]
        for kind in ("contains", "uses"):
            for item in declaration.relations(kind):
                for identity in item.get("relies_on", ()):
                    add(identity, "relies_on", item["target"])
        while queue:
            concept = concepts[queue.pop(0)]
            for identity in concept.mentions:
                add(identity, "mentions", concept.id)
            for identity in concept.narrows:
                add(identity, "narrows", concept.id)
            if concept.supersedes is not None:
                add(concept.supersedes, "supersedes", concept.id)
            for item in concept.relates:
                add(item["target"], "relates", concept.id)
        result = {
            identity: sorted(
                selected[identity],
                key=lambda reason: (reason["relation"], reason["id"]),
            )
            for identity in sorted(selected)
        }
        self._terms_cache[target.id] = result
        return {key: list(value) for key, value in result.items()}

    def term_records(self, module: ModuleRef) -> list[dict]:
        """The selected glossary entries of a Module, whole, with their selecting declarations."""
        return [
            {
                "entry": copy.deepcopy(self.glossary_entries[identity]),
                "reasons": reasons,
            }
            for identity, reasons in self.terms(module).items()
        ]

    def spec_context(self, query_id: str) -> SpecContext:
        """``SpecContext`` of a Module, or of a scenario's owner, with its source and term
        records."""
        target, kind = self._query(query_id)
        sources = [
            record
            for path, reasons in self._context_paths(target).items()
            for record in self.source_records(path, reasons)
        ]
        descriptor = target.descriptor()
        context = SpecContext(
            canonical(
                {
                    "schema_version": CONTEXT_SCHEMA,
                    "query_id": query_id,
                    "query_kind": kind,
                    "module_id": target.id,
                    "reading_entry": target.primary_document,
                    "documents": list(target.documents),
                    "references": descriptor["references"],
                    "registration": descriptor,
                    "sources": sorted(sources, key=lambda s: s["path"]),
                    "terms": self.term_records(target),
                }
            )
        )
        check_schema(context.value, context_record_schema())
        return context

    def context_identities(self) -> dict[str, str]:
        return {
            module.id: digest(self.spec_context(module.id).value)
            for module in self.modules.values()
        }

    def affected_contexts(self, candidate) -> tuple[str, ...]:
        before, after = self.context_identities(), candidate.context_identities()
        return tuple(
            sorted(
                identity
                for identity in before.keys() | after.keys()
                if before.get(identity) != after.get(identity)
            )
        )

    def fresh(self):
        return type(self)(
            self.root,
            registry_bytes=self._registry_override,
            document_overrides=self.document_overrides,
        )

    def recheck_context(self, context: SpecContext) -> None:
        value = context.value
        try:
            current = self.fresh().spec_context(value["query_id"])
            if current.serialized != context.serialized:
                before = {item["path"]: item["digest"] for item in value["sources"]}
                after = {
                    item["path"]: item["digest"] for item in current.value["sources"]
                }
                changed = sorted(
                    path
                    for path in before.keys() | after.keys()
                    if before.get(path) != after.get(path)
                )
                old_terms = {
                    item["entry"]["id"]: item for item in value.get("terms", [])
                }
                new_terms = {
                    item["entry"]["id"]: item for item in current.value["terms"]
                }
                terms = sorted(
                    identity
                    for identity in old_terms.keys() | new_terms.keys()
                    if old_terms.get(identity) != new_terms.get(identity)
                )
                details = []
                if changed:
                    details.append(
                        "changed, added or removed sources: " + ", ".join(changed)
                    )
                if terms:
                    details.append(
                        "changed, added or removed glossary entries: "
                        + ", ".join(terms)
                    )
                raise SpecError(
                    f"the context of {value['query_id']} changed since it was computed: "
                    + (
                        "; ".join(details)
                        if details
                        else "its declarations or member roles changed"
                    ),
                    "stale_context",
                    subject=value["query_id"],
                )
        except (ValueError, OSError, KeyError) as error:
            if isinstance(error, SpecError) and error.code == "stale_context":
                raise
            raise SpecError(
                f"the context of {value.get('query_id')} can no longer be computed",
                "stale_context",
                subject=value.get("query_id"),
                causes=[error if isinstance(error, SpecError) else system_cause(error)],
            ) from error

    def context_bytes(self, context: SpecContext) -> dict[str, bytes]:
        self.recheck_context(context)
        self.validate_source_records(context.value["sources"])
        result = {}
        for record in context.value["sources"]:
            raw = self.source_bytes(record["path"])
            if digest(raw) != record["digest"]:
                raise SpecError(
                    "source changed during materialization", "stale_context"
                )
            result[record["path"]] = raw
        return result

    # --- read sets: ImplementationContext and ExternalContext ----------------------------

    def implementation_context(self, module: ModuleRef) -> tuple[str, ...]:
        """ImplementationContext(M): names of the files M's realizations bind."""
        return self.bound_files(module)

    def bound_files(self, module: ModuleRef) -> tuple[str, ...]:
        """Existing regular files the Module's entries bind, directory entries expanded."""
        return tuple(
            sorted(
                {
                    path
                    for entry in self._resolve(module).files
                    for path in expand_entry(self.root, entry)
                }
            )
        )

    def external_inclusions(self, module: ModuleRef) -> tuple[str, ...]:
        """The Module's ``includes`` of kind ``external``, in declaration order."""
        return tuple(
            value
            for kind, value in self._resolve(module).references
            if kind == "external"
        )

    def _external(self, entry: str) -> tuple[tuple[str, ...], str]:
        """The files of one external entry and their digest, read together once per repository,
        so that the listing and the digest describe the same moment."""
        if entry not in self._external_cache:
            files = tuple(
                expand_entry(
                    self.root, entry, skipped_suffixes=REFERENCE_SKIPPED_SUFFIXES
                )
            )
            self._external_cache[entry] = (
                files,
                digest([(path, digest(read_file(self.root, path))) for path in files]),
            )
        return self._external_cache[entry]

    def external_files(self, entry: str) -> tuple[str, ...]:
        """Existing readable files below one external entry, media and archives excluded."""
        return self._external(entry)[0]

    def external_digest(self, entry: str) -> str:
        """One digest per entry over its readable files' paths and bytes; cached per repository."""
        return self._external(entry)[1]

    def external_context(self, module: ModuleRef) -> tuple:
        """ExternalContext(M): only M's own external inclusions; a selected Module brings none."""
        from .boundaries import ExternalEntry

        result = []
        for entry in self.external_inclusions(module):
            exists = entry_exists(self.root, entry)
            result.append(
                ExternalEntry(
                    entry,
                    is_directory_entry(entry),
                    self.external_files(entry) if exists else (),
                    self.external_digest(entry) if exists else digest([]),
                    exists,
                )
            )
        return tuple(result)

    # --- write sets ------------------------------------------------------------------------

    def spec_scope(self, module: ModuleRef) -> tuple[str, ...]:
        """SpecScope(M) as files: both members of every document M owns, including the entry,
        and the glossary, whose entries M owns or adds. Which entries of the glossary a task may
        change is held by entry: see ``glossary.ownership_violations``."""
        members = {
            member
            for path in self._resolve(module).documents
            for member in (path, metadata_path(path))
        }
        if self.glossary_path is not None:
            members.add(self.glossary_path)
        return tuple(sorted(members))

    def implementation_scope(self, module: ModuleRef) -> tuple[str, ...]:
        """ImplementationScope(M): M's realization entries.

        A directory entry covers every present and future file below it under the exclusion
        rule; use ``BoundarySets.writable`` or ``bound_by`` to test one path. An entry under
        ``.concorde/`` or ``generated/`` binds nothing and is left out (validation reports it).
        """
        return tuple(
            entry for entry in self._resolve(module).files if not unbindable(entry)
        )

    def boundary_sets(self, module: ModuleRef):
        """The boundary sets of one Module (see ``boundaries``)."""
        from .boundaries import BoundarySets

        target = self._resolve(module)
        return BoundarySets(
            target.id,
            self.spec_context(target.id).paths,
            self.external_context(target),
            self.implementation_context(target),
            self.spec_scope(target),
            self.implementation_scope(target),
            self.project_implementation(),
            self.project_specification(),
        )

    def project_implementation(self) -> tuple[str, ...]:
        """ProjectImplementation: every Module's realization entries and external material."""
        paths: dict[str, None] = {}
        for identity in sorted(self.modules):
            target = self.modules[identity]
            for entry in self.implementation_context(target):
                paths[entry] = None
            for external in self.external_context(target):
                paths[external.path] = None
        return tuple(paths)

    def project_specification(self) -> tuple[str, ...]:
        """ProjectSpecification: both members of every Module's documents, and the glossary."""
        paths = {
            path for identity in self.modules for path in self.spec_scope(identity)
        }
        return tuple(sorted(paths))

    def missing_entries(self, module: ModuleRef) -> tuple[str, ...]:
        """Entries whose file or directory does not exist yet."""
        return tuple(
            entry
            for entry in self._resolve(module).files
            if not entry_exists(self.root, entry)
        )

    def realization_entries(self, module: ModuleRef) -> dict[str, Realization]:
        """Declared entries of the Module's realizations, keyed by entry (exact file or directory)."""
        return {
            entry: realization
            for realization in self.realizations(module)
            for entry in realization.entries
        }

    def realization_for_path(self, module: ModuleRef, path: str) -> Realization | None:
        """The realization whose most specific entry covers a concrete file path, if any."""
        entries = self.realization_entries(module)
        entry = most_specific(entries, path)
        return entries[entry] if entry is not None else None

    # --- definitions ---------------------------------------------------------------------

    def definitions(self, module: ModuleRef) -> ModuleDefinitions:
        owner = self._resolve(module).id
        return ModuleDefinitions(
            tuple(x for x in self.scenario_nodes.values() if x.owner == owner),
            tuple(x for x in self.requirement_nodes.values() if x.owner == owner),
            tuple(x for x in self.concept_nodes.values() if x.owner == owner),
            tuple(x for x in self.realization_nodes.values() if x.owner == owner),
            tuple(x for x in self.contract_nodes.values() if x["owner"] == owner),
        )

    def scenarios(self, module: ModuleRef) -> tuple[Scenario, ...]:
        return self.definitions(module).scenarios

    def requirements(self, module: ModuleRef) -> tuple[Requirement, ...]:
        return self.definitions(module).requirements

    def concepts(self, module: ModuleRef) -> tuple[Concept, ...]:
        return self.definitions(module).concepts

    def realizations(self, module: ModuleRef) -> tuple[Realization, ...]:
        return self.definitions(module).realizations

    def contracts(self, module: ModuleRef) -> tuple[dict, ...]:
        return tuple(
            {key: value for key, value in item.items() if key != "line"}
            for item in self.definitions(module).contracts
        )

    def participations(self, module: ModuleRef) -> tuple[dict, ...]:
        owner = self._resolve(module).id
        return tuple(
            {**item, "owner": owner} for item in self.declarations[owner].participates
        )

    def explanation_text(self, concept: Concept) -> str | None:
        """The prose a concept's explanation reference resolves to, or None."""
        owner = self.declarations.get(concept.owner)
        if (
            owner is None
            or concept.document not in owner.owns
            or concept.document not in self.readings
        ):
            return None
        found = self.readings[concept.document].anchors.get(concept.anchor)
        return found.text if found else None

    def meaning_text(self, module_id: str, meaning: str) -> str | None:
        """The prose a Module relation's ``meaning`` anchor resolves to, or None."""
        module = self.declarations[module_id]
        if not isinstance(meaning, str) or "#" not in meaning:
            return None
        location, anchor = meaning.split("#", 1)
        path = location or module.entry
        if path not in module.owns or path not in self.readings:
            return None
        found = self.readings[path].anchors.get(anchor)
        return found.text if found else None

    # --- derived indexes and impact --------------------------------------------------------

    def selected_by(self, document_id: str) -> tuple[str, ...]:
        """``selected-by``: the Modules whose SpecContext contains a document."""
        if document_id not in self._identity_paths:
            raise SpecError(
                f"{document_id} names no registered Spec document",
                "invalid_target",
                subject=document_id,
            )
        path = self._identity_paths[document_id]
        return tuple(
            sorted(
                module.id
                for module in self.modules.values()
                if path in self._context_paths(module)
            )
        )

    def term_selected_by(self, concept_id: str) -> tuple[str, ...]:
        """``selected-by`` for a definition: the Modules whose ``Terms`` hold a concept."""
        return tuple(
            sorted(
                module.id
                for module in self.modules.values()
                if concept_id in self.terms(module)
            )
        )

    def referenced_by(self, identity: str) -> tuple[dict, ...]:
        """``referenced-by``: declarations that depend on a concept, requirement, scenario or
        contract.

        Inverts ``relies_on``, ``mentions``, ``narrows``, ``supersedes``, ``relates`` and
        ``participates``. Each record names the relation, the declaring Module and the
        declaring document (the glossary, for a relation a concept's entry declares).
        """
        result = []
        for module in self.declarations.values():
            for kind in ("contains", "uses"):
                for item in module.relations(kind):
                    if identity in item.get("relies_on", ()):
                        result.append(
                            {
                                "relation": "relies_on",
                                "module": module.id,
                                "document": module.entry,
                            }
                        )
            for item in module.participates:
                if item["contract"] == identity:
                    result.append(
                        {
                            "relation": "participates",
                            "module": module.id,
                            "document": module.entry,
                        }
                    )
        for item in self.mentions:
            if item["concept"] == identity:
                result.append(
                    {
                        "relation": "mentions",
                        "module": item["owner"],
                        "document": item["document"],
                    }
                )
        for concept in self.concept_nodes.values():
            if identity in concept.mentions:
                result.append(
                    {
                        "relation": "mentions",
                        "module": concept.owner,
                        "document": concept.source,
                    }
                )
        for relation in (*self.metadata_relations, *self.glossary_relations()):
            if (
                relation["type"] in {"narrows", "supersedes", "relates"}
                and relation.get("target") == identity
            ):
                result.append(
                    {
                        "relation": relation["type"],
                        "module": relation["owner"],
                        "document": relation["document"],
                    }
                )
        return tuple(
            sorted(
                {tuple(sorted(item.items())): item for item in result}.values(),
                key=lambda item: (item["module"], item["relation"], item["document"]),
            )
        )

    def implemented_by(self, path: str) -> tuple[str, ...]:
        """``implemented-by``: Modules whose realizations bind a path or list it as an entry."""
        return tuple(
            module.id
            for module in self.modules.values()
            if any(entry == path or bound_by(entry, path) for entry in module.files)
        )

    def shared_files(self, module: ModuleRef) -> dict[str, tuple[str, ...]]:
        """Every other Module binding a file in M's ImplementationScope, with those files.

        Computed from entries alone: an exact entry both bind, an exact entry one binds below
        the other's directory, or the inner of two nested directory entries. A task writing one
        of these files concerns the other Module too (Protocol shared-file rule).
        """
        target = self._resolve(module)
        result: dict[str, tuple[str, ...]] = {}
        for other in self.modules.values():
            if other.id == target.id:
                continue
            shared = {
                path
                for mine in self.implementation_scope(target)
                for theirs in self.implementation_scope(other)
                if (path := _shared_path(mine, theirs)) is not None
            }
            if shared:
                result[other.id] = tuple(sorted(shared))
        return result

    def coverage(self, module: ModuleRef) -> dict[str, tuple]:
        """``covered-by`` for every scenario of the Module: the tests that declare it."""
        from .verification import scan_declarations

        paths = sorted(
            {
                path
                for other in self.modules.values()
                for path in self.bound_files(other)
            }
        )
        declared: dict[str, list] = {
            scenario.id: [] for scenario in self.scenarios(module)
        }
        for declaration in scan_declarations(self.root, paths):
            if declaration.scenario_id in declared:
                declared[declaration.scenario_id].append(declaration)
        return {scenario_id: tuple(items) for scenario_id, items in declared.items()}

    def covered_by(self, scenario_id: str) -> tuple:
        """``covered-by``: the verification declarations, read from bound tests, naming a
        scenario."""
        scenario = self.scenario_nodes.get(scenario_id)
        if scenario is None:
            raise SpecError(
                f"{scenario_id} is no declared scenario",
                "invalid_target",
                subject=scenario_id,
            )
        return self.coverage(scenario.owner)[scenario_id]

    def impact(self, *, documents=(), nodes=(), paths=()) -> tuple[str, ...]:
        """Every Module a write concerns: readers of written documents, dependants of written
        nodes and contracts, and binders of written files (Boundaries, impact of a write)."""
        concerned: set[str] = set()
        for document_id in documents:
            concerned.update(self.selected_by(document_id))
        for identity in nodes:
            concerned.update(item["module"] for item in self.referenced_by(identity))
            if identity in self.concept_nodes:
                concerned.update(self.term_selected_by(identity))
        for path in paths:
            concerned.update(self.implemented_by(path))
        return tuple(sorted(concerned))

    # --- checks ----------------------------------------------------------------------------

    def validate(self) -> None:
        """Run every check; raise on the first error. Establishes structure, never sufficiency."""
        from .validation import spec_findings

        errors = [item for item in spec_findings(self) if item.strictness == "error"]
        if errors:
            first = errors[0]
            raise SpecError(
                f"{len(errors)} structural error(s), each a cause; the first is "
                f"{first.rule_id} at {first.source}: {first.message}",
                path=first.source or None,
                causes=[from_finding(item) for item in errors],
            )


RepositoryCore = DocumentUnitRepository


def _shared_path(first: str, second: str) -> str | None:
    """The path two realization entries both bind, or None (see ``shared_files``)."""
    if first == second:
        return first
    if is_directory_entry(first) and bound_by(first, second):
        return second
    if is_directory_entry(second) and bound_by(second, first):
        return first
    return None


def _as_cause(error: BaseException, **location) -> SpecError:
    """An error caught while loading as a cause: a Spec tooling error as it is, an operating
    system error as ``system_error``, text that is not UTF-8 as ``invalid_spec`` and any other
    undecodable value as ``invalid_json``."""
    if isinstance(error, SpecError):
        return error
    if isinstance(error, OSError):
        return system_cause(error, **location)
    return SpecError(
        f"{type(error).__name__}: {error}",
        "invalid_spec" if isinstance(error, UnicodeError) else "invalid_json",
        path=location.get("path"),
    )


def _error_code(check: str) -> str:
    if check in {"CHK.owns.unique", "CHK.document.pair", "CHK.document.entry"}:
        return "invalid_owner" if check == "CHK.owns.unique" else "invalid_spec"
    if check == "CHK.document.path":
        return "unsafe_path"
    return "invalid_spec"


__all__ = [
    "DocumentUnitRepository",
    "ModuleDeclaration",
    "ModuleRef",
    "NodeRef",
    "RepositoryCore",
    "identifier",
    "reference_record",
    "context_record_schema",
]
