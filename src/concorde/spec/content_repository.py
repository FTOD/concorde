"""Protocol 11 Spec graph loader and the repository API every consumer reads.

The registry says which Modules exist and where each entry is. Every declaration is read from the
entries' ``module`` blocks and from the registered documents: the registry's mirrored fields are
never trusted for the graph, only compared with it by ``CHK.registry.mirror``. Documents are
registered through ``owns`` and never discovered from the filesystem or from links.

Loading collects problems as findings instead of stopping at the first one, so ``validate`` can
report every problem. A repository opened for runtime use (the default) refuses a Spec whose
structure cannot support a trustworthy boundary: an unreadable or unowned document, a broken
entry, an unknown relation target or a composition cycle.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .content_model import (
    DocumentUnit,
    SourceMember,
    declaration_problems,
    envelope_problems,
    metadata_path,
)
from .model import Finding
from .repository_base import (
    REFERENCE_SKIPPED_SUFFIXES,
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
from .typed_data import canonical, check_schema, checked_path, decode, safe_path
from .wire_shapes import CONTEXT_SCHEMA

# A query naming a Module accepts its identity or its registered record.
ModuleRef = str | Module

WARNING_CHECKS = frozenset(
    {
        "CHK.node.explained",
        "CHK.contains.root",
        "CHK.includes.redundant",
        "CHK.imports.owner",
    }
)


def severity(check: str) -> str:
    return "warning" if check in WARNING_CHECKS else "error"


def unit_resolution_schema() -> dict:
    """Closed paired-source resolution shape shared by all worker envelopes; roles never trim it."""
    from .contracts import REFERENCE, TARGET_DESCRIPTOR
    from .wire_shapes import DIGEST, PATH, SELECTION_REASON, STRING, array, obj

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
    return obj(
        {
            "schema_version": {"const": CONTEXT_SCHEMA},
            "query_id": STRING,
            "query_kind": {"enum": ["module", "scenario"]},
            "module_id": STRING,
            "shares": {"type": "boolean"},
            "reading_entry": PATH,
            "documents": array(PATH, unique=True),
            "references": array(REFERENCE, unique=True),
            "registration": TARGET_DESCRIPTOR,
            "sources": array(source, unique=True),
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


class DocumentUnitRepository:
    """The loaded Protocol 11 graph of one project checkout."""

    def __init__(
        self,
        project_root: Path | str,
        *,
        registry_path: str = ".concorde/specs.json",
        registry_bytes: bytes | None = None,
        document_overrides: dict[str, bytes] | None = None,
        configured_checks: list | None = None,
        _defer_document_admission: bool = False,
    ):
        root = Path(project_root)
        if root.is_symlink() or not root.is_dir():
            raise SpecError("project root must be a real directory")
        self.root = root.resolve()
        self.registry_path = safe_path(registry_path)
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
                    "source overrides must contain exact bytes", "invalid_proposal"
                )
            self.document_overrides[safe_path(path)] = raw
        self.protocol_assets: dict[str, bytes] = getattr(self, "protocol_assets", {})
        self._load = _Load()
        self.declarations: dict[str, ModuleDeclaration] = {}
        self.modules: dict[str, Module] = {}
        self.document_targets: dict[str, list[str]] = {}
        self.units: dict[str, DocumentUnit] = {}
        self.readings: dict[str, Reading] = {}
        self.nodes: dict[str, NodeRef] = {}
        self.concept_nodes: dict[str, Concept] = {}
        self.realization_nodes: dict[str, Realization] = {}
        self.requirement_nodes: dict[str, Requirement] = {}
        self.scenario_nodes: dict[str, Scenario] = {}
        self.contract_nodes: dict[str, dict] = {}
        self.imports: list[dict] = []
        self.metadata_relations: list[dict] = []
        self.checks: dict[str, dict] = {}
        self._identity_paths: dict[str, str] = {}
        self._reference_digest_cache: dict[str, str] = {}
        self._context_cache: dict[tuple[str, bool], dict[str, list[dict]]] = {}
        self._registry()
        self._documents()
        self._targets(configured_checks or [])
        if self.document_overrides.keys() - self.source_documents.keys():
            raise SpecError(
                "source override is outside registered documents", "permission_denied"
            )
        if self._load.fatal and not _defer_document_admission:
            first = self._load.fatal[0]
            raise SpecError(
                f"{first.rule_id}: {first.source}: {first.message}",
                _error_code(first.rule_id),
                first.source,
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
    ) -> None:
        finding = Finding(
            check,
            severity(check),
            source,
            message,
            remediation,
            line=line,
            subject_id=subject,
        )
        self._load.findings.append(finding)
        if fatal:
            self._load.fatal.append(finding)

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
                f"registry is not JSON: {error}", "unsupported_profile"
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
                "(Protocol 11); migrate explicitly",
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
            owner = (
                (metadata.get("document") or {}).get("owner")
                if isinstance(metadata, dict)
                else None
            )
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
            items = block.get(name) if block else None
            if not isinstance(items, list):
                return ()
            return tuple(
                item
                for item in items
                if isinstance(item, dict)
                and required <= item.keys()
                and not item.keys() - required - optional
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
                    )
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
        definitions = {
            row.term: row for row in (reading.terminology or []) if row.href is None
        }
        for record in value.get("defines", []):
            if not isinstance(record, dict) or not is_identity(record.get("id")):
                continue
            kind = record.get("type")
            title = record.get("title") if isinstance(record.get("title"), str) else ""
            meaning = (
                record.get("meaning") if isinstance(record.get("meaning"), str) else ""
            )
            if kind == "concept":
                row = definitions.get(title)
                if not self._register(
                    NodeRef(record["id"], "concept", owner, path, title)
                ):
                    continue
                self.concept_nodes[record["id"]] = Concept(
                    record["id"],
                    title,
                    owner,
                    path,
                    meaning,
                    row.definition if row else None,
                    record.get("retired")
                    if isinstance(record.get("retired"), dict)
                    else None,
                    record.get("external_conflict"),
                )
                if role != "module":
                    self._problem(
                        "CHK.defines.role",
                        unit.metadata.path,
                        f"concept {record['id']} is defined in an implementation document",
                        subject=record["id"],
                    )
            elif kind == "realization":
                entries = record.get("entries")
                entries = (
                    tuple(x for x in entries if isinstance(x, str))
                    if isinstance(entries, list)
                    else ()
                )
                pending = record.get("pending", [])
                pending = (
                    tuple(x for x in pending if isinstance(x, str))
                    if isinstance(pending, list)
                    else ()
                )
                if not self._register(
                    NodeRef(record["id"], "realization", owner, path, title)
                ):
                    continue
                self.realization_nodes[record["id"]] = Realization(
                    record["id"], title, owner, path, meaning, entries, pending
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

        for row in reading.terminology or []:
            if row.href is None:
                continue
            target = link_target(path, row.href)
            self.imports.append(
                {
                    "document": path,
                    "owner": owner,
                    "line": row.line,
                    "href": row.href,
                    "path": target[0] if target else None,
                    "concept": target[1] if target else None,
                    "definition": row.definition,
                }
            )
        for record in value.get("relations", []):
            if isinstance(record, dict) and record.get("type") in {
                "narrows",
                "supersedes",
                "contrasts",
                "relates",
            }:
                self.metadata_relations.append(
                    {**record, "document": path, "owner": owner}
                )

    def _targets(self, configured_checks: list) -> None:
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
        for check in configured_checks:
            self.checks[check["id"]] = check
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
                    check["id"]
                    for check in configured_checks
                    if check.get("module") == module.id
                ),
                tuple(
                    dict.fromkeys(
                        (item["kind"], item["target"])
                        for item in module.includes
                        if item["kind"] in {"module", "document", "external"}
                    )
                ),
                module.entry,
            )

    # --- identities and documents --------------------------------------------------------

    @property
    def root_module(self) -> str:
        """The root Module: the one Module no other Module contains (the first one if several)."""
        roots = [module.id for module in self.modules.values() if module.parent is None]
        return roots[0] if roots else next(iter(self.modules))

    def document_path(self, document_id: str) -> str:
        if document_id not in self._identity_paths:
            raise SpecError(f"unknown document: {document_id}", "invalid_target")
        return self._identity_paths[document_id]

    def unit(self, path: str) -> DocumentUnit:
        if path not in self.document_targets:
            raise SpecError(
                f"unregistered reading document: {path}", "permission_denied"
            )
        if path not in self.units:
            raise SpecError(
                f"document cannot be admitted: {path}", "invalid_spec", path
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
                f"unregistered document source: {path}", "permission_denied"
            )
        self.unit(reading)
        # Return current bytes, not cached bytes: materialization must detect changes after freeze.
        return self._raw(path)

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
                    "duplicate or unregistered context source", "invalid_context"
                )
            unit = self.unit(reading)
            role = "reading" if path == reading else "metadata"
            if (
                record.get("document_id") != unit.document_id
                or record.get("owner") != unit.owner
                or record.get("role") != role
            ):
                raise SpecError(
                    "context member role, identity or owner differs from its document",
                    "invalid_context",
                )
            reasons = record.get("reasons")
            if reading in provenance and provenance[reading] != reasons:
                raise SpecError(
                    "document members have inconsistent selection provenance",
                    "invalid_context",
                )
            provenance[reading] = reasons
            seen.add(path)
            selected.add(reading)
        if seen != {
            member for path in selected for member in (path, metadata_path(path))
        }:
            raise SpecError(
                "context cannot grant a reading-only or metadata-only document",
                "invalid_context",
            )

    # --- Modules and composition ---------------------------------------------------------

    def _resolve(self, module: ModuleRef) -> Module:
        identity = module.id if isinstance(module, Module) else module
        if identity not in self.modules:
            raise SpecError(f"unknown Spec target: {identity}", "unknown_target")
        return self.modules[identity]

    def module(self, module_id: str, scenario: str | None = None) -> Module:
        """One registered Module; ``scenario``, when given, must be a scenario it owns."""
        module = self._resolve(module_id)
        if scenario is not None:
            node = self.scenario_nodes.get(scenario)
            if node is None or node.owner != module.id:
                raise SpecError(
                    "scenario focus must belong to the selected target", "invalid_focus"
                )
        return module

    def module_declaration(self, module_id: str) -> ModuleDeclaration:
        if module_id not in self.declarations:
            raise SpecError(f"unknown Spec target: {module_id}", "unknown_target")
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
            f"unsupported or unknown context identity: {query_id}",
            "invalid_target",
            query_id,
        )

    def _context_paths(
        self, module: ModuleRef, shares: bool = False
    ) -> dict[str, list[dict]]:
        """Spec(M) with every relation that selected each document (one level, never recursive).

        With ``shares``, the owned documents of every other Module binding a file in M's
        ImplementationScope are added with a ``shares`` reason (Protocol shared-file rule).
        """
        target = self._resolve(module)
        key = (target.id, shares)
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
        if shares:
            for other, files in self.shared_files(target).items():
                add(
                    self.modules[other].documents,
                    {"relation": "shares", "id": other, "files": list(files)},
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

    def spec_context(self, query_id: str, *, shares: bool = False) -> SpecContext:
        """``SpecContext`` of a Module, or of a scenario's owner, with its source records.

        ``shares`` adds the shared-file readers a code-writing task needs (see ``shared_files``);
        it is recorded in the context, so it is part of the context identity.
        """
        target, kind = self._query(query_id)
        sources = [
            record
            for path, reasons in self._context_paths(target, shares).items()
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
                    "shares": shares,
                    "reading_entry": target.primary_document,
                    "documents": list(target.documents),
                    "references": descriptor["references"],
                    "registration": descriptor,
                    "sources": sorted(sources, key=lambda s: s["path"]),
                }
            )
        )
        check_schema(context.value, unit_resolution_schema())
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
            registry_path=self.registry_path,
            registry_bytes=self._registry_override,
            document_overrides=self.document_overrides,
            configured_checks=list(self.checks.values()),
        )

    def recheck_context(self, context: SpecContext) -> None:
        value = context.value
        try:
            current = self.fresh().spec_context(
                value["query_id"], shares=value["shares"]
            )
            if current.serialized != context.serialized:
                raise SpecError(
                    "context declarations, member roles or source bytes changed",
                    "stale_context",
                )
        except (ValueError, OSError, KeyError) as error:
            if isinstance(error, SpecError) and error.code == "stale_context":
                raise
            raise SpecError(
                f"document context is stale: {error}", "stale_context"
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
        """ImplementationContext(M): names of existing bound files and of pending exact entries."""
        target = self._resolve(module)
        names = set(self.bound_files(target))
        for realization in self.realizations(target):
            names.update(
                entry for entry in realization.pending if not is_directory_entry(entry)
            )
        return tuple(sorted(names))

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

    def external_files(self, entry: str) -> tuple[str, ...]:
        """Existing readable files below one external entry, media and archives excluded."""
        return tuple(
            expand_entry(self.root, entry, skipped_suffixes=REFERENCE_SKIPPED_SUFFIXES)
        )

    def external_digest(self, entry: str) -> str:
        """One digest per entry over its readable files' paths and bytes; cached per repository."""
        if entry not in self._reference_digest_cache:
            self._reference_digest_cache[entry] = digest(
                [
                    (path, digest(read_file(self.root, path)))
                    for path in self.external_files(entry)
                ]
            )
        return self._reference_digest_cache[entry]

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
        """SpecScope(M): both members of every document M owns, including the entry."""
        return tuple(
            sorted(
                member
                for path in self._resolve(module).documents
                for member in (path, metadata_path(path))
            )
        )

    def implementation_scope(self, module: ModuleRef) -> tuple[str, ...]:
        """ImplementationScope(M): M's realization entries, pending entries included.

        A directory entry covers every present and future file below it under the exclusion
        rule; use ``BoundarySets.writable`` or ``bound_by`` to test one path.
        """
        return tuple(self._resolve(module).files)

    def boundary_sets(self, module: ModuleRef):
        """The five boundary sets of one Module (see ``boundaries``)."""
        from .boundaries import BoundarySets

        target = self._resolve(module)
        return BoundarySets(
            target.id,
            self.spec_context(target.id).paths,
            self.external_context(target),
            self.implementation_context(target),
            self.spec_scope(target),
            self.implementation_scope(target),
        )

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
            raise SpecError(f"unknown document: {document_id}", "invalid_target")
        path = self._identity_paths[document_id]
        return tuple(
            sorted(
                module.id
                for module in self.modules.values()
                if path in self._context_paths(module)
            )
        )

    def referenced_by(self, identity: str) -> tuple[dict, ...]:
        """``referenced-by``: declarations that depend on a concept, requirement, scenario or
        contract.

        Inverts ``relies_on``, ``imports``, ``narrows``, ``supersedes``, ``relates`` and
        ``participates``. Each record names the relation, the declaring Module and the
        declaring document.
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
        for item in self.imports:
            if item["concept"] == identity:
                result.append(
                    {
                        "relation": "imports",
                        "module": item["owner"],
                        "document": item["document"],
                    }
                )
        for relation in self.metadata_relations:
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
                for mine in target.files
                for theirs in other.files
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
                f"unknown scenario: {scenario_id}", "invalid_target", scenario_id
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
        for path in paths:
            concerned.update(self.implemented_by(path))
        return tuple(sorted(concerned))

    # --- checks ----------------------------------------------------------------------------

    def validate(self) -> None:
        """Run every check; raise on the first error. Establishes structure, never sufficiency."""
        from .validation import spec_findings

        errors = [item for item in spec_findings(self) if item.severity == "error"]
        if errors:
            first = errors[0]
            raise SpecError(f"{first.rule_id}: {first.source}: {first.message}")


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
    "unit_resolution_schema",
]
