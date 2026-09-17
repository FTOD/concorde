"""Protocol-8 document-unit source backend.

This backend is not an alternate capability entry or a profile auto-detector. The bound SpecRepository adds installed Protocol admission to these shared source operations. Protocol binding,
worker wire envelopes and lifecycle activation remain the host's separate admission boundary.
"""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from .content_model import (
    DocumentUnit,
    admit_document_unit,
    json_declarations,
    metadata_identity,
    metadata_path,
)
from .repository_base import (
    ModuleDefinitions,
    SpecDocument,
    SpecEntity,
    SpecError,
    RepositoryCore,
    SpecResolution,
    SpecTarget,
    _parse_definitions,
    covers,
    digest,
    entry_exists,
    identifier,
    read_file,
)
from .typed_data import canonical, check_schema, checked_path, decode, safe_path


def unit_resolution_schema() -> dict:
    """Closed paired-source resolution shape shared by all worker envelopes; roles never trim it."""
    from .contracts import REFERENCE, TARGET_DESCRIPTOR
    from .wire_shapes import DIGEST, PATH, STRING, array, obj

    reason = obj({"kind": {"enum": ["owned", "module", "document"]}, "id": STRING})
    source = obj(
        {
            "document_id": STRING,
            "owner": STRING,
            "path": PATH,
            "digest": DIGEST,
            "role": {"enum": ["reading", "metadata"]},
            "reasons": array(reason, unique=True),
        }
    )
    return obj(
        {
            "schema_version": {"const": 1},
            "query_id": STRING,
            "query_kind": {"enum": ["module", "scenario"]},
            "module_id": STRING,
            "reading_entry": PATH,
            "documents": array(PATH, unique=True),
            "references": array(REFERENCE, unique=True),
            "registration": TARGET_DESCRIPTOR,
            "sources": array(source, unique=True),
        }
    )


class DocumentUnitRepository(RepositoryCore):
    """Explicit new-format source backend; no Protocol-6 fallback and no worker launch authority."""

    def __init__(
        self,
        project_root: Path | str,
        *,
        registry_path: str = ".concorde/specs.json",
        registry_bytes: bytes | None = None,
        document_overrides: dict[str, bytes] | None = None,
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
        self.registry = decode(self.registry_bytes.decode("utf-8"))
        fields = {"schema_version", "project_id", "entry_target", "targets", "checks"}
        if (
            not isinstance(self.registry, dict)
            or set(self.registry) != fields
            or type(self.registry["schema_version"]) is not int
            or self.registry["schema_version"] != 5
        ):
            raise SpecError(
                "document-unit backend requires registry schema 5; migrate explicitly",
                "unsupported_profile",
            )
        self.project_id = identifier(self.registry["project_id"])
        self.targets: dict[str, SpecTarget] = {}
        self.file_users: dict[str, tuple[str, ...]] = {}
        self.checks: dict[str, dict] = {}
        self.document_targets: dict[str, list[str]] = {}
        self._document_cache: dict[str, SpecDocument] = {}
        self._definition_cache: dict[str, ModuleDefinitions] = {}
        self._reference_digest_cache: dict[str, str] = {}
        self._unit_cache: dict[str, DocumentUnit] = {}
        self._draft_admission = _defer_document_admission
        self.document_overrides = {}
        for path, raw in (document_overrides or {}).items():
            if not isinstance(raw, bytes):
                raise SpecError(
                    "source overrides must contain exact bytes", "invalid_proposal"
                )
            self.document_overrides[safe_path(path)] = raw
        # Structural admission has no inline-document or Protocol-version reads.
        self._load_registry()
        self.entry_target = self.registry["entry_target"]
        if self.entry_target not in self.targets:
            raise SpecError("entry_target must name a registered Module")
        self.source_documents = {
            member: path
            for path in self.document_targets
            for member in (path, metadata_path(path))
        }
        if self.document_overrides.keys() - self.source_documents.keys():
            raise SpecError(
                "source override is outside registered document units",
                "permission_denied",
            )
        for target in self.targets.values():
            for entry in target.files:
                if any(covers(entry, member) for member in self.source_documents):
                    raise SpecError(
                        f"implementation entry cannot bind a document-unit member: {entry}"
                    )
            for kind, entry in target.references:
                if kind == "external" and any(
                    covers(entry, member) for member in self.source_documents
                ):
                    raise SpecError(
                        f"external reference cannot include a document-unit member: {entry}"
                    )
        if not _defer_document_admission:
            self._document_index()
            for target in self.targets.values():
                self._context_paths(target)
        # Source materialization can reuse the host helper without introducing an unbound Protocol.
        # This is empty deliberately; the backend does not implement host Protocol installation.
        self.protocol_assets: dict[str, bytes] = {}

    def _raw(self, path: str) -> bytes:
        return (
            self.document_overrides[path]
            if path in self.document_overrides
            else read_file(self.root, path)
        )

    def _document_index(self) -> dict[str, str]:
        if hasattr(self, "_identity_paths"):
            return dict(self._identity_paths)
        index = {}
        physical: dict[tuple[int, int], str] = {}
        for path, owners in self.document_targets.items():
            # Verify availability without reading unselected human bodies. An overlay supplies
            # a new member explicitly; it never repairs a missing partner by directory discovery.
            missing = [
                member
                for member in (path, metadata_path(path))
                if member not in self.document_overrides
                and not checked_path(self.root, member).is_file()
            ]
            if missing:
                if self._draft_admission:
                    continue
                raise SpecError(
                    f"required document-unit member is missing: {missing[0]}",
                    "missing_source",
                    missing[0],
                )
            for member in (path, metadata_path(path)):
                if member not in self.document_overrides:
                    stat = checked_path(self.root, member).stat()
                    key = (stat.st_dev, stat.st_ino)
                    if key in physical:
                        raise SpecError(
                            f"physical source alias: {member} and {physical[key]}",
                            "invalid_owner",
                        )
                    physical[key] = member
            expected_owner = owners[0]
            if self._draft_admission and not self.source_is_overridden(path):
                expected_owner = decode(self._raw(metadata_path(path)).decode())[
                    "document"
                ]["owner"]
            identity, _ = metadata_identity(
                metadata_path(path),
                self._raw(metadata_path(path)),
                expected_owner=expected_owner,
            )
            if identity in index or identity in self.targets:
                raise SpecError(
                    f"duplicate document identity: {identity}", "invalid_owner", path
                )
            index[identity] = path
        self._identity_paths = dict(index)
        return index

    def unit(self, path: str) -> DocumentUnit:
        if path not in self.document_targets:
            raise SpecError(
                f"unregistered reading document: {path}", "permission_denied"
            )
        if path not in self._unit_cache:
            owner = self.document_targets[path][0]
            unit = admit_document_unit(
                path,
                self._raw(path),
                self._raw(metadata_path(path)),
                expected_owner=owner,
                primary=path == self.targets[owner].primary_document,
            )
            admitted_index = getattr(self, "_identity_paths", None)
            if (
                admitted_index is not None
                and admitted_index.get(unit.document_id) != path
            ):
                raise SpecError(
                    f"document identity changed after admission: {path}",
                    "stale_context",
                )
            self._unit_cache[path] = unit
        return self._unit_cache[path]

    def document(self, path: str) -> SpecDocument:
        """Reading view for shared Markdown parsers; source roles are represented separately."""
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

    def source_bytes(self, path: str) -> bytes:
        reading = self.source_documents.get(path)
        if reading is None:
            raise SpecError(
                f"unregistered document-unit source: {path}", "permission_denied"
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
        """A granted unit must contain both roles exactly once with consistent identity/owner."""
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
                    "context member role, identity or owner differs from its unit",
                    "invalid_context",
                )
            reasons = record.get("reasons")
            if reading in provenance and provenance[reading] != reasons:
                raise SpecError(
                    "document-unit members have inconsistent inclusion provenance",
                    "invalid_context",
                )
            provenance[reading] = reasons
            seen.add(path)
            selected.add(reading)
        if seen != {
            member for path in selected for member in (path, metadata_path(path))
        }:
            raise SpecError(
                "context cannot grant a reading-only or metadata-only document unit",
                "invalid_context",
            )

    def spec_files(self, entity_id: str) -> tuple[str, ...]:
        target, _ = self._query(entity_id)
        return tuple(
            sorted(
                member
                for path in self._context_paths(target)
                for member in (path, metadata_path(path))
            )
        )

    def spec_context(self, entity_id: str) -> SpecResolution:
        target, kind = self._query(entity_id)
        sources = [
            record
            for path, reasons in self._context_paths(target).items()
            for record in self.source_records(path, reasons)
        ]
        references = [
            {"kind": "external", "path": i} if k == "external" else {"kind": k, "id": i}
            for k, i in target.references
        ]
        resolution = SpecResolution(
            canonical(
                {
                    "schema_version": 1,
                    "query_id": entity_id,
                    "query_kind": kind,
                    "module_id": target.id,
                    "reading_entry": target.primary_document,
                    "documents": list(target.documents),
                    "references": references,
                    "registration": {**asdict(target), "references": references},
                    "sources": sorted(sources, key=lambda s: s["path"]),
                }
            )
        )
        check_schema(resolution.value, unit_resolution_schema())
        return resolution

    def _contracts_in_documents(self, documents) -> tuple[dict, ...]:
        from .schema import admit, validate

        contracts = []
        for document in documents:
            for value in json_declarations(
                document.body, "concorde-contract", document.path
            ):
                if not isinstance(value, dict) or set(value) != {
                    "id",
                    "version",
                    "schema",
                    "semantics",
                    "example",
                }:
                    raise SpecError(
                        "canonical contract requires id/version/schema/semantics/example"
                    )
                identifier(value["id"])
                if type(value["version"]) is not int or value["version"] < 1:
                    raise SpecError("contract version must be a positive integer")
                if (
                    not isinstance(value["semantics"], str)
                    or not value["semantics"].strip()
                ):
                    raise SpecError("canonical contract semantics must be nonempty")
                admit(value["schema"])
                validate(value["example"], value["schema"])
                contracts.append(
                    {**value, "source": document.path, "owner": document.owner}
                )
        return tuple(contracts)

    def context_contracts(self, target: SpecTarget) -> tuple[dict, ...]:
        return self._contracts_in_documents(
            self.document(path) for path in self._context_paths(target)
        )

    def definitions(self, target: SpecTarget) -> ModuleDefinitions:
        if target.id in self._definition_cache:
            return self._definition_cache[target.id]
        scenarios, requirements, entities = [], [], []
        for path in target.documents:
            unit = self.unit(path)
            local_scenarios, local_requirements = _parse_definitions(
                self.document(path), target.id
            )
            scenarios.extend(local_scenarios)
            requirements.extend(local_requirements)
            for entity in unit.declarations["entities"]:
                entities.append(
                    SpecEntity(
                        entity["id"],
                        entity["title"],
                        entity["kind"],
                        unit.meaning(entity["meaning"]).text,
                        tuple(entity.get("files", [])),
                        tuple(entity.get("pending", [])),
                        entity.get("target_id"),
                        target.id,
                        path,
                    )
                )
        identities, titles, entries, providers = set(), set(), set(), set()
        for item in (*scenarios, *requirements, *entities):
            if item.id in identities:
                raise SpecError(f"duplicate owned definition: {item.id}")
            identities.add(item.id)
        related = set(target.uses) | {child.id for child in self.children(target)}
        for entity in entities:
            if entity.title in titles or entries.intersection(entity.files):
                raise SpecError(
                    "duplicate entity title or implementation entry across owned documents"
                )
            titles.add(entity.title)
            entries.update(entity.files)
            if entity.target_id:
                if entity.target_id not in related or entity.target_id in providers:
                    raise SpecError(
                        "Module entity must name exactly one declared child or used provider"
                    )
                providers.add(entity.target_id)
        result = ModuleDefinitions(
            tuple(scenarios), tuple(requirements), tuple(entities)
        )
        self._definition_cache[target.id] = result
        return result

    def _check_implementation_listing(self, target: SpecTarget) -> None:
        if set(self.entity_files(target)) != set(target.files):
            raise SpecError(
                f"entity implementation entries differ from registration: {target.id}",
                "invalid_spec",
            )

    def implementation_entries(self, target: SpecTarget) -> tuple[str, ...]:
        self._check_implementation_listing(target)
        return super().implementation_entries(target)

    def implementation_paths(self, target: SpecTarget) -> tuple[str, ...]:
        self._check_implementation_listing(target)
        return super().implementation_paths(target)

    def implementation_files(self, target: SpecTarget) -> tuple[str, ...]:
        self._check_implementation_listing(target)
        return super().implementation_files(target)

    def dependencies(self, target: SpecTarget) -> tuple[dict, ...]:
        return self._declarations(target, "dependencies")

    def contract_bindings(self, target: SpecTarget) -> tuple[dict, ...]:
        return self._declarations(target, "bindings")

    def _declarations(self, target: SpecTarget, field: str) -> tuple[dict, ...]:
        return tuple(
            {
                **entry,
                "explanation": self.unit(path).meaning(entry["meaning"]).text,
                "source": path,
                "owner": target.id,
            }
            for path in target.documents
            for entry in self.unit(path).declarations[field]
        )

    def fresh(self) -> DocumentUnitRepository:
        return DocumentUnitRepository(
            self.root,
            registry_path=self.registry_path,
            registry_bytes=self._registry_override,
            document_overrides=self.document_overrides,
        )

    def recheck_resolution(self, resolution: SpecResolution) -> None:
        try:
            current = self.fresh().spec_context(resolution.value["query_id"])
            if current.serialized != resolution.serialized:
                raise SpecError(
                    "context declarations, member roles or source bytes changed",
                    "stale_context",
                )
        except (ValueError, OSError, KeyError) as error:
            raise SpecError(
                f"document-unit context is stale: {error}", "stale_context"
            ) from error

    def context_bytes(self, resolution: SpecResolution) -> dict[str, bytes]:
        self.recheck_resolution(resolution)
        self.validate_source_records(resolution.value["sources"])
        result = {}
        for record in resolution.value["sources"]:
            raw = self.source_bytes(record["path"])
            if digest(raw) != record["digest"]:
                raise SpecError(
                    "source changed during materialization", "stale_context"
                )
            result[record["path"]] = raw
        return result

    def validate(self) -> None:
        """Cross-unit invariants. Raises on errors; does not establish semantic completeness."""
        from .validation import (
            LINK,
            _fences_in_range,
            _first_line,
            _section_ranges,
            flowchart_model,
            link_findings,
        )
        from urllib.parse import unquote, urlsplit
        import posixpath

        identities = set(self.targets) | set(self._document_index())
        contracts, bindings = {}, []
        for target in self.targets.values():
            definitions = self.definitions(target)
            for item in (
                *definitions.scenarios,
                *definitions.requirements,
                *definitions.entities,
            ):
                if item.id in identities:
                    raise SpecError(f"identity is defined more than once: {item.id}")
                identities.add(item.id)
            for contract in self.contracts(target):
                if contract["id"] in identities:
                    raise SpecError(
                        f"identity is defined more than once: {contract['id']}"
                    )
                identities.add(contract["id"])
                contracts[contract["id"]] = contract
            if set(self.entity_files(target)) != set(target.files):
                raise SpecError(
                    f"entity implementation entries differ from registration: {target.id}"
                )
            expected = set(target.uses) | {child.id for child in self.children(target)}
            if {
                entity.target_id for entity in definitions.entities if entity.target_id
            } != expected:
                raise SpecError(f"missing child or dependency entity: {target.id}")
            dependencies = self.dependencies(target)
            if (
                len(dependencies) != len(expected)
                or {d["target_id"] for d in dependencies} != expected
            ):
                raise SpecError(
                    f"local dependency explanations differ from registered providers: {target.id}"
                )
            for entity in definitions.entities:
                for entry in entity.files:
                    if (
                        not entry_exists(self.root, entry)
                        and entry not in entity.pending
                    ):
                        raise SpecError(
                            f"implementation entry is missing and not pending: {entry}"
                        )
            if self.missing_external_references(target):
                raise SpecError(f"external references are missing: {target.id}")
            local_bindings = self.contract_bindings(target)
            bindings.extend(local_bindings)
            included = set(self._context_paths(target))
            for declaration in (*dependencies, *local_bindings):
                for match in LINK.finditer(declaration["explanation"]):
                    url = urlsplit(match.group(1))
                    if url.scheme or url.netloc or url.path.startswith("/"):
                        continue
                    path = (
                        posixpath.normpath(
                            posixpath.join(
                                posixpath.dirname(declaration["source"]),
                                unquote(url.path),
                            )
                        )
                        if url.path
                        else declaration["source"]
                    )
                    if path not in included:
                        raise SpecError(
                            f"local agreement relies on an excluded definition: {path}"
                        )
            sections, lines = _section_ranges(
                self.document(target.primary_document).body
            )
            relationships = next(
                s for s in sections if s[0] == "Relationships" and s[1] == 2
            )
            fences = _fences_in_range(
                lines, relationships[2], relationships[3], "mermaid"
            )
            if not fences:
                raise SpecError(f"Relationships requires a flowchart: {target.id}")
            for fence in fences:
                if not fence.lstrip().startswith(("flowchart ", "graph ")):
                    raise SpecError("relationship diagram must be a Mermaid flowchart")
                nodes, edges = flowchart_model(fence)
                if not nodes or not {
                    _first_line(label) for label in nodes.values()
                } <= {e.title for e in definitions.entities}:
                    raise SpecError(
                        "relationship diagram contains unknown or no local entities"
                    )
                if any(label is None for _, label, _ in edges):
                    raise SpecError("relationship edges must be labeled")
        seen = set()
        for binding in bindings:
            key = (binding["owner"], binding["id"], binding["role"], binding["peer"])
            if key in seen:
                raise SpecError(
                    "duplicate participant/peer/role binding across owned documents"
                )
            seen.add(key)
            definition = contracts.get(binding["id"])
            if (
                definition is None
                or definition["version"] != binding["version"]
                or definition["source"]
                not in self._context_paths(self.targets[binding["owner"]])
            ):
                raise SpecError(
                    "canonical definition/version is absent from participant context"
                )
            if binding["peer"].startswith("external:"):
                continue
            if not any(
                peer["owner"] == binding["peer"]
                and peer["peer"] == binding["owner"]
                and peer["id"] == binding["id"]
                and peer["version"] == binding["version"]
                and peer["role"] != binding["role"]
                for peer in bindings
            ):
                raise SpecError("missing complementary participant binding")
        problems = link_findings(self)
        if problems:
            raise SpecError("; ".join(problem.message for problem in problems))
