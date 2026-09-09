"""Module contracts and reusable, file-bound Implementation Specs (Profile 9).

Module composition, dependency and implementation reuse are independent relations.
Resolving a Module never reads a collaborator's or an Implementation Spec's body.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..host.typed_data import canonical, decode, checked_path, safe_path
from ..frontmatter import parse_document
from .schema import ContractError, admit, validate


PROFILE_VERSION = 9
PROTOCOL_VERSION = "2.1.0"
KINDS = frozenset({"module"})
SPEC_KINDS = frozenset({"module", "implementation"})
IDENTITY = re.compile(r"^[a-z][a-z0-9]*(?:[.-][a-z0-9-]+)*$")
CONTRACT_BLOCK = re.compile(r"^```concorde-contract\s*\n(.*?)^```\s*$", re.M | re.S)
DEPENDENCIES_BLOCK = re.compile(r"^```concorde-dependencies\s*\n(.*?)^```\s*$", re.M | re.S)
DOCUMENT_BLOCK = re.compile(r"^```concorde-document\s*\n(.*?)^```\s*$", re.M | re.S)


class SpecError(ValueError):
    def __init__(self, message: str, code: str = "invalid_spec", field: str = ""):
        self.code, self.field = code, field
        super().__init__(message)


def digest(value: bytes | Any) -> str:
    data = value if isinstance(value, bytes) else canonical(value).encode()
    return "sha256:" + hashlib.sha256(data).hexdigest()


def read_file(root: Path, relative: str) -> bytes:
    """Read regular files only; reject path aliases and every symlink component."""
    path = checked_path(root, relative)
    if not path.is_file():
        raise SpecError(f"required regular file is missing: {relative}", "missing_source", relative)
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    with os.fdopen(descriptor, "rb") as stream:
        return stream.read()


def strings(value: Any, label: str, *, nonempty: bool = False) -> tuple[str, ...]:
    if (not isinstance(value, list) or any(not isinstance(x, str) or not x.strip() for x in value)
            or len(set(value)) != len(value) or (nonempty and not value)):
        raise SpecError(f"{label} must be a {'nonempty ' if nonempty else ''}unique string array")
    return tuple(value)


def identifier(value: Any) -> str:
    if not isinstance(value, str) or not IDENTITY.fullmatch(value):
        raise SpecError(f"invalid stable identity: {value!r}")
    return value


@dataclass(frozen=True)
class SpecTarget:
    id: str
    kind: str
    title: str
    documents: tuple[str, ...]
    parent: str | None
    uses: tuple[str, ...]
    implementations: tuple[str, ...]
    features: tuple[dict, ...]
    interfaces: tuple[dict, ...]
    checks: tuple[str, ...]
    diagrams: tuple[dict, ...]

    @property
    def primary_document(self) -> str:
        """A Module's reading entry is explicit within its complete collection."""
        return next(path for path in self.documents if Path(path).name == "module.md")


@dataclass(frozen=True)
class ImplementationSpec:
    id: str
    title: str
    documents: tuple[str, ...]
    files: tuple[str, ...]

    @property
    def kind(self) -> str:
        return "implementation"

    @property
    def primary_document(self) -> str:
        return self.documents[0]


@dataclass(frozen=True)
class SpecDocument:
    path: str
    content: str
    digest: str
    document_id: str
    targets: tuple[str, ...]
    main_visible: bool
    metadata: dict
    body: str


class SpecRepository:
    def __init__(self, project_root: Path | str, package_root: Path | str | None = None, *,
                 registry_bytes: bytes | None = None,
                 document_overrides: dict[str, bytes] | None = None):
        root = Path(project_root)
        if root.is_symlink() or not root.is_dir():
            raise SpecError("project root must be a real directory")
        self.root = root.resolve()
        self.package_root = Path(package_root).resolve() if package_root else Path(__file__).resolve().parents[3]
        self.config = decode(read_file(self.root, ".concorde/config.json").decode())
        if self.config.get("profile_version") != PROFILE_VERSION:
            raise SpecError("Profile 9 (Module/Implementation) is required; older profiles need explicit migration", "unsupported_profile")
        if set(self.config) != {"profile_version", "registry", "protocol", "capability_configuration"}:
            raise SpecError("configuration fields must be profile_version, registry, protocol, capability_configuration")
        self.registry_path = safe_path(self.config["registry"])
        self.registry_bytes = (bytes(registry_bytes) if registry_bytes is not None
                               else read_file(self.root, self.registry_path))
        self.document_overrides = {safe_path(path): bytes(content)
                                   for path, content in (document_overrides or {}).items()}
        self.registry = decode(self.registry_bytes.decode())
        if set(self.registry) != {"schema_version", "project_id", "entry_target", "targets", "implementations", "checks"} or self.registry["schema_version"] != 2:
            raise SpecError("unsupported Spec registry schema")
        self.project_id = identifier(self.registry["project_id"])
        self.targets: dict[str, SpecTarget] = {}
        self.implementations: dict[str, ImplementationSpec] = {}
        self.implementation_users: dict[str, tuple[str, ...]] = {}
        self.file_implementations: dict[str, str] = {}
        self.focus: dict[str, tuple[str, str, dict]] = {}
        self.checks: dict[str, dict] = {}
        self.document_targets: dict[str, list[str]] = {}
        self.diagram_targets: dict[str, list[str]] = {}
        self._document_cache: dict[str, SpecDocument] = {}
        self._load_registry()
        self.entry_target = self.registry["entry_target"]
        if self.entry_target not in self.targets:
            raise SpecError("entry_target must name one registered target")
        self.protocol_manifest, self.protocol_assets = self._protocol()

    def _protocol(self) -> tuple[dict, dict[str, bytes]]:
        from ..host.build import BuildError, verify_fresh

        try:
            verify_fresh(self.package_root)
        except BuildError as error:
            raise SpecError(str(error), error.code) from error
        raw = read_file(self.package_root, "protocol/manifest.json")
        manifest = decode(raw.decode())
        binding = {"version": manifest.get("version"), "digest": digest(raw)}
        if self.config["protocol"] != binding or binding["version"] != PROTOCOL_VERSION:
            raise SpecError("project Protocol binding does not match the installed assets", "protocol_mismatch")
        assets = {}
        for item in manifest["assets"]:
            content = read_file(self.package_root, item["path"])
            if digest(content) != item["digest"]:
                raise SpecError(f"Protocol asset has changed: {item['path']}", "protocol_mismatch")
            assets[item["path"]] = content
        required = {"generated/protocol/principles.md", *(f"generated/protocol/kinds/{kind}.md" for kind in SPEC_KINDS)}
        if not required.issubset(assets):
            raise SpecError("Protocol manifest is missing global principles or kind definitions")
        return manifest, assets

    def _load_registry(self) -> None:
        if not isinstance(self.registry["targets"], list) or not self.registry["targets"]:
            raise SpecError("registry requires targets")
        paths: set[str] = set()
        fields = {"id", "kind", "title", "documents", "parent", "uses",
                  "implementations", "features", "interfaces", "checks", "diagrams"}
        for raw in self.registry["targets"]:
            if not isinstance(raw, dict) or set(raw) != fields:
                raise SpecError(f"target fields must be {sorted(fields)}")
            target_id = identifier(raw["id"])
            if target_id in self.targets or not isinstance(raw["kind"], str) or raw["kind"] not in KINDS:
                raise SpecError(f"duplicate target or unknown kind: {target_id}")
            if not isinstance(raw["title"], str) or not raw["title"].strip():
                raise SpecError(f"target {target_id} requires a title")
            documents = strings(raw["documents"], "documents", nonempty=True)
            if sum(Path(p).name == "module.md" for p in documents) != 1:
                raise SpecError(f"Module {target_id} must register exactly one module.md reading entry")
            for path in documents:
                safe_path(path)
                if not path.endswith(".md") or path.startswith((".concorde/", ".git/")):
                    raise SpecError(f"Spec documents must be durable Markdown: {path}")
                paths.add(path)
                self.document_targets.setdefault(path, []).append(target_id)
            implementations = strings(raw["implementations"], "implementations")
            for implementation_id in implementations:
                identifier(implementation_id)
            if not isinstance(raw["diagrams"], list):
                raise SpecError("diagrams must be an array")
            diagram_sources = set()
            for diagram in raw["diagrams"]:
                if (not isinstance(diagram, dict) or not {"source", "kind", "title"} <= set(diagram)
                        or set(diagram) - {"source", "kind", "title", "recipe"}):
                    raise SpecError("diagram declarations require source/kind/title and optional recipe")
                source = safe_path(diagram["source"])
                if (not source.endswith(".json") or source.startswith((".concorde/", ".git/", "generated/"))
                        or source in diagram_sources):
                    raise SpecError(f"diagram sources must be unique durable JSON: {source}")
                if (diagram["kind"] not in {"architecture", "workflow", "sequence", "dataflow", "lifecycle"}
                        or not isinstance(diagram["title"], str) or not diagram["title"].strip()):
                    raise SpecError(f"invalid diagram kind/title: {source}")
                if "recipe" in diagram and (diagram["recipe"] != "system-overview" or diagram["kind"] != "architecture"):
                    raise SpecError("system-overview is an architecture recipe")
                diagram_sources.add(source)
                paths.add(source)
                self.diagram_targets.setdefault(source, []).append(target_id)
            for focus_kind in ("features", "interfaces"):
                if not isinstance(raw[focus_kind], list):
                    raise SpecError(f"{focus_kind} must be an array")
                for item in raw[focus_kind]:
                    if not isinstance(item, dict) or set(item) != {"id", "title", "document"}:
                        raise SpecError("Feature/interface entries require id, title, document")
                    if not isinstance(item["title"], str) or not item["title"].strip():
                        raise SpecError("Feature/interface entries require a nonempty title")
                    focus_id = identifier(item["id"])
                    if focus_id in self.focus or item["document"] not in documents:
                        raise SpecError(f"duplicate or nonlocal Feature/API: {focus_id}")
                    self.focus[focus_id] = (target_id, focus_kind, item)
            self.targets[target_id] = SpecTarget(target_id, raw["kind"], raw["title"], documents,
                raw["parent"], strings(raw["uses"], "uses"), implementations,
                tuple(raw["features"]), tuple(raw["interfaces"]), strings(raw["checks"], "checks"), tuple(raw["diagrams"]))
        if set(self.targets) & set(self.focus):
            raise SpecError("Module and Feature/interface IDs share one namespace")
        for target in self.targets.values():
            if self.document_targets[target.primary_document] != [target.id]:
                raise SpecError(f"Module reading entry must belong only to its Module: {target.primary_document}")
            parent = target.parent
            seen = {target.id}
            while parent is not None:
                if not isinstance(parent, str) or parent not in self.targets:
                    raise SpecError(f"unknown parent for {target.id}")
                if parent in seen:
                    raise SpecError(f"cycle in Module composition: {target.id}")
                seen.add(parent)
                parent = self.targets[parent].parent
            for peer in target.uses:
                if peer not in self.targets or peer == target.id:
                    raise SpecError(f"unknown or self dependency for {target.id}: {peer}")
        # A shared capability is a sibling, never a child owned by one of its consumers.
        for provider in self.targets.values():
            consumers = [t for t in self.targets.values() if provider.id in t.uses]
            if len(consumers) > 1 and any(t.parent != provider.parent for t in consumers):
                raise SpecError(f"shared Module {provider.id} and its consumers must be siblings")
        self._load_implementations(paths)
        for raw in self.registry["checks"]:
            if not isinstance(raw, dict) or not {"id", "target_id", "argv", "timeout_seconds"}.issubset(raw) or set(raw) - {"id", "target_id", "argv", "timeout_seconds", "inputs"}:
                raise SpecError("check requires id, target_id, argv, timeout_seconds")
            key = identifier(raw["id"])
            if key in self.checks or raw["target_id"] not in self.targets:
                raise SpecError(f"duplicate or unowned check: {key}")
            if not isinstance(raw["argv"], list) or not raw["argv"] or any(not isinstance(x, str) or not x for x in raw["argv"]):
                raise SpecError("check argv must be a nonempty array of strings")
            if type(raw["timeout_seconds"]) is not int or not 1 <= raw["timeout_seconds"] <= 3600:
                raise SpecError("check timeout must be 1..3600 seconds")
            for path in strings(raw.get("inputs", []), "check inputs"):
                safe_path(path)
            self.checks[key] = raw
        for target in self.targets.values():
            if any(k not in self.checks or self.checks[k]["target_id"] != target.id for k in target.checks):
                raise SpecError(f"target {target.id} references a missing or foreign check")

    def _load_implementations(self, module_paths: set[str]) -> None:
        values = self.registry["implementations"]
        if not isinstance(values, list):
            raise SpecError("implementations must be an array")
        reserved = set(self.targets) | set(self.focus)
        for raw in values:
            if not isinstance(raw, dict) or set(raw) != {"id", "title", "documents", "files"}:
                raise SpecError("Implementation Spec requires id/title/documents/files")
            key = identifier(raw["id"])
            if key in reserved or key in self.implementations:
                raise SpecError(f"duplicate Implementation Spec identity: {key}")
            if not isinstance(raw["title"], str) or not raw["title"].strip():
                raise SpecError(f"Implementation Spec {key} requires a title")
            documents = strings(raw["documents"], "implementation documents", nonempty=True)
            files = strings(raw["files"], "implementation files", nonempty=True)
            for path in documents:
                safe_path(path)
                if (not path.endswith(".md") or path.startswith((".concorde/", ".git/"))
                        or path in module_paths or path in self.document_targets):
                    raise SpecError(f"Implementation Spec document must have one owner and cannot be Module context: {path}")
                self.document_targets[path] = [key]
            self.implementations[key] = ImplementationSpec(key, raw["title"], documents, files)
        for implementation in self.implementations.values():
            for path in implementation.files:
                safe_path(path)
                if (path.startswith((".concorde/", ".git/", ".agents/", ".claude/", ".codex/", "generated/"))
                        or path in self.document_targets or path in module_paths):
                    raise SpecError(f"implementation binding cannot include control, generated or project Spec files: {path}")
                if path in self.file_implementations:
                    raise SpecError(f"implementation file has multiple owners: {path}")
                candidate = checked_path(self.root, path)
                if candidate.exists() and not candidate.is_file():
                    raise SpecError(f"Implementation Specs bind explicit files, not directories: {path}")
                self.file_implementations[path] = implementation.id
            self.implementation_users[implementation.id] = tuple(
                t.id for t in self.targets.values() if implementation.id in t.implementations)
        for target in self.targets.values():
            for key in target.implementations:
                if key not in self.implementations:
                    raise SpecError(f"Module {target.id} references unknown Implementation Spec {key}")

    def select(self, target_id: str, focus_id: str | None = None) -> SpecTarget:
        if target_id not in self.targets:
            raise SpecError(f"unknown Spec target: {target_id}", "unknown_target")
        if focus_id is not None and (focus_id not in self.focus or self.focus[focus_id][0] != target_id):
            raise SpecError("Feature/API focus must belong to the selected target", "invalid_focus")
        return self.targets[target_id]

    def documents(self, target: SpecTarget) -> tuple[SpecDocument, ...]:
        return tuple(self.document(path) for path in target.documents)

    def diagram_sources(self, target: SpecTarget) -> list[dict]:
        """Only explicitly registered diagram bytes enter a target's reproducible context."""
        result = []
        for declaration in target.diagrams:
            path = declaration["source"]
            raw = self.document_overrides.get(path)
            if raw is None:
                raw = read_file(self.root, path)
            result.append({"path": path, "digest": digest(raw), "content": raw.decode("utf-8"),
                           "declaration": declaration})
        return result

    def document(self, path: str) -> SpecDocument:
        """Read one declared Spec truth and verify its registry reference set."""

        if path not in self.document_targets:
            raise SpecError(f"unregistered Spec document: {path}")
        if path in self._document_cache:
            return self._document_cache[path]
        raw = self.document_overrides.get(path)
        if raw is None:
            raw = read_file(self.root, path)
        text = raw.decode("utf-8")
        metadata, body = parse_document(text, path) if text.startswith("---\n") else ({}, text)
        if not body.strip():
            raise SpecError(f"empty Spec document: {path}")
        blocks = tuple(DOCUMENT_BLOCK.finditer(body))
        if len(blocks) != 1:
            raise SpecError(f"Spec document requires exactly one concorde-document block: {path}")
        value = decode(blocks[0].group(1))
        if not isinstance(value, dict) or set(value) != {"id", "targets", "main_visible"}:
            raise SpecError(f"concorde-document requires id/targets/main_visible: {path}")
        document_id = identifier(value["id"])
        targets = strings(value["targets"], "document targets", nonempty=True)
        if type(value["main_visible"]) is not bool:
            raise SpecError(f"document main_visible must be boolean: {path}")
        expected = tuple(self.document_targets[path])
        if set(targets) != set(expected) or len(targets) != len(expected):
            raise SpecError(
                f"document target declaration differs from registry membership: {path}"
            )
        document = SpecDocument(path, text, digest(raw), document_id, targets,
                                value["main_visible"], metadata, body)
        self._document_cache[path] = document
        return document

    def contracts(self, target: SpecTarget) -> tuple[dict, ...]:
        contracts = []
        for document in self.documents(target):
            for match in CONTRACT_BLOCK.finditer(document.body):
                value = decode(match.group(1))
                if set(value) != {"id", "version", "role", "peer", "schema", "semantics", "example"}:
                    raise SpecError(f"contract requires id/version/role/peer/schema/semantics/example: {document.path}")
                identifier(value["id"])
                if type(value["version"]) is not int or value["version"] < 1 or value["role"] not in {"provided", "required"}:
                    raise SpecError("invalid contract version or role")
                if not isinstance(value["semantics"], str) or not value["semantics"].strip():
                    raise SpecError("contract semantics must be local and nonempty")
                if not isinstance(value["peer"], str) or not value["peer"]:
                    raise SpecError("contract peer must be a target ID or external:name")
                admit(value["schema"])
                validate(value["example"], value["schema"])
                contracts.append({**value, "source": document.path, "owner": target.id})
        return tuple(contracts)

    def dependencies(self, target: SpecTarget) -> tuple[dict, ...]:
        """Read the Module's own relied-upon promises, without following a dependency."""
        dependencies = []
        fields = {"target_id", "responsibility", "selection_condition",
                  "relied_upon_promises"}
        for document in self.documents(target):
            matches = tuple(DEPENDENCIES_BLOCK.finditer(document.body))
            for match in matches:
                values = decode(match.group(1))
                if not isinstance(values, list) or not values:
                    raise SpecError(
                        f"concorde-dependencies must be a nonempty JSON array: {document.path}"
                    )
                for value in values:
                    if not isinstance(value, dict) or set(value) != fields:
                        raise SpecError(
                            "dependency requires target_id/responsibility/selection_condition/"
                            f"relied_upon_promises: {document.path}"
                        )
                    target_id = identifier(value["target_id"])
                    for key in ("responsibility", "selection_condition"):
                        if not isinstance(value[key], str) or not value[key].strip():
                            raise SpecError(
                                f"dependency {key} must be nonempty: {document.path}"
                            )
                    promises = strings(
                        value["relied_upon_promises"],
                        "relied_upon_promises",
                        nonempty=True,
                    )
                    dependencies.append({
                        **value,
                        "target_id": target_id,
                        "relied_upon_promises": promises,
                        "source": document.path,
                        "owner": target.id,
                    })
        return tuple(dependencies)

    def children(self, target: SpecTarget) -> tuple[SpecTarget, ...]:
        return tuple(t for t in self.targets.values() if t.parent == target.id)

    def descendants(self, target: SpecTarget) -> tuple[SpecTarget, ...]:
        result = []
        for child in self.children(target):
            result.extend((child, *self.descendants(child)))
        return tuple(result)

    def implementation_specs(self, target: SpecTarget) -> tuple[ImplementationSpec, ...]:
        return tuple(self.implementations[key] for key in target.implementations)

    def implementation_paths(self, target: SpecTarget) -> tuple[str, ...]:
        """Exact declared file authority, including files yet to be authored."""
        return tuple(sorted({path for spec in self.implementation_specs(target) for path in spec.files}))

    def implementation_documents(self, target: SpecTarget) -> tuple[SpecDocument, ...]:
        return tuple(self.document(path) for spec in self.implementation_specs(target)
                     for path in spec.documents)

    def affected_modules(self, paths: tuple[str, ...] | list[str]) -> tuple[SpecTarget, ...]:
        """Reverse lookup for changed code or Implementation Spec documents; no Spec bodies read."""
        implementation_ids = {self.file_implementations[path] for path in paths
                              if path in self.file_implementations}
        for path in paths:
            implementation_ids.update(key for key in self.document_targets.get(path, ())
                                      if key in self.implementations)
        users = {user for key in implementation_ids for user in self.implementation_users[key]}
        return tuple(target for target in self.targets.values() if target.id in users)

    def implementation_files(self, target: SpecTarget) -> tuple[str, ...]:
        return tuple(path for path in self.implementation_paths(target)
                     if checked_path(self.root, path).is_file())
