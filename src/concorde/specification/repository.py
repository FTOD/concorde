"""Explicit Profile 8 registry. Loading a target never follows another Spec."""
from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..capabilities.operation_data import canonical, decode, checked_path, safe_path
from ..frontmatter import parse_document
from .schema import ContractError, admit, validate


PROFILE_VERSION = 8
PROTOCOL_VERSION = "1.0.0"
KINDS = frozenset({"domain", "service", "module"})
IDENTITY = re.compile(r"^[a-z][a-z0-9]*(?:[.-][a-z0-9-]+)*$")
CONTRACT_BLOCK = re.compile(r"^```concorde-contract\s*\n(.*?)^```\s*$", re.M | re.S)


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
    scope_parent: str | None
    component_parent: str | None
    participates_in: tuple[str, ...]
    implementation: tuple[str, ...]
    features: tuple[dict, ...]
    apis: tuple[dict, ...]
    checks: tuple[str, ...]
    diagrams: tuple[dict, ...]


@dataclass(frozen=True)
class SpecDocument:
    path: str
    content: str
    digest: str
    metadata: dict
    body: str


class SpecRepository:
    def __init__(self, project_root: Path | str, package_root: Path | str | None = None):
        root = Path(project_root)
        if root.is_symlink() or not root.is_dir():
            raise SpecError("project root must be a real directory")
        self.root = root.resolve()
        self.package_root = Path(package_root).resolve() if package_root else Path(__file__).resolve().parents[3]
        self.config = decode(read_file(self.root, ".concorde/config.json").decode())
        if self.config.get("profile_version") != PROFILE_VERSION:
            raise SpecError("Profile 8 is required; run the explicit Profile 7 migration first", "migration_required")
        if set(self.config) != {"profile_version", "registry", "protocol", "operation_configuration"}:
            raise SpecError("Profile 8 configuration fields must be profile_version, registry, protocol, operation_configuration")
        self.registry_path = safe_path(self.config["registry"])
        self.registry_bytes = read_file(self.root, self.registry_path)
        self.registry = decode(self.registry_bytes.decode())
        if set(self.registry) != {"schema_version", "project_id", "entry_target", "targets", "checks"} or self.registry["schema_version"] != 1:
            raise SpecError("unsupported Spec registry schema")
        self.project_id = identifier(self.registry["project_id"])
        self.targets: dict[str, SpecTarget] = {}
        self.focus: dict[str, tuple[str, str, dict]] = {}
        self.checks: dict[str, dict] = {}
        self._load_registry()
        self.entry_target = self.registry["entry_target"]
        if self.entry_target not in self.targets:
            raise SpecError("entry_target must name one registered target")
        self.protocol_manifest, self.protocol_assets = self._protocol()

    def _protocol(self) -> tuple[dict, dict[str, bytes]]:
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
        required = {"protocol/principles.md", *(f"protocol/kinds/{kind}.md" for kind in KINDS)}
        if not required.issubset(assets):
            raise SpecError("Protocol manifest is missing global principles or kind definitions")
        return manifest, assets

    def _load_registry(self) -> None:
        if not isinstance(self.registry["targets"], list) or not self.registry["targets"]:
            raise SpecError("registry requires targets")
        paths: dict[str, str] = {}
        fields = {"id", "kind", "title", "documents", "scope_parent", "component_parent",
                  "participates_in", "implementation", "features", "apis", "checks", "diagrams"}
        for raw in self.registry["targets"]:
            if not isinstance(raw, dict) or set(raw) != fields:
                raise SpecError(f"target fields must be {sorted(fields)}")
            target_id = identifier(raw["id"])
            if target_id in self.targets or raw["kind"] not in KINDS:
                raise SpecError(f"duplicate target or unknown kind: {target_id}")
            if not isinstance(raw["title"], str) or not raw["title"].strip():
                raise SpecError(f"target {target_id} requires a title")
            documents = strings(raw["documents"], "documents", nonempty=True)
            for path in documents:
                safe_path(path)
                if not path.endswith(".md") or path.startswith((".concorde/", ".git/")):
                    raise SpecError(f"Spec documents must be durable Markdown: {path}")
                paths[path] = target_id
            implementation = strings(raw["implementation"], "implementation")
            for path in implementation:
                safe_path(path)
                if path.startswith((".concorde", ".git", ".agents", ".claude", ".codex")):
                    raise SpecError(f"implementation grant cannot include control or agent configuration: {path}")
            if raw["kind"] == "domain" and (implementation or raw["component_parent"] is not None or raw["participates_in"]):
                raise SpecError("Domain scopes have no component parent, code ownership, or scope participation")
            if raw["kind"] != "domain" and raw["scope_parent"] is not None:
                raise SpecError("component parents and Domain scope parents are independent")
            if raw["kind"] == "module" and raw["features"]:
                raise SpecError("Modules declare APIs directly, not Features")
            if raw["kind"] != "module" and raw["apis"]:
                raise SpecError("Service/Domain use cases belong in Features; boundary schemas belong in contracts")
            for focus_kind in ("features", "apis"):
                if not isinstance(raw[focus_kind], list):
                    raise SpecError(f"{focus_kind} must be an array")
                for item in raw[focus_kind]:
                    if not isinstance(item, dict) or set(item) != {"id", "title", "document"}:
                        raise SpecError("Feature/API entries require id, title, document")
                    focus_id = identifier(item["id"])
                    if focus_id in self.focus or item["document"] not in documents:
                        raise SpecError(f"duplicate or nonlocal Feature/API: {focus_id}")
                    self.focus[focus_id] = (target_id, focus_kind, item)
            self.targets[target_id] = SpecTarget(target_id, raw["kind"], raw["title"], documents,
                raw["scope_parent"], raw["component_parent"], strings(raw["participates_in"], "participates_in"),
                implementation, tuple(raw["features"]), tuple(raw["apis"]), strings(raw["checks"], "checks"), tuple(raw["diagrams"]))
        if set(self.targets)&set(self.focus):raise SpecError("target and Feature/API IDs share one namespace")
        grants=[(t.id,p) for t in self.targets.values() for p in t.implementation]
        for index,(owner,path) in enumerate(grants):
            for peer,other in grants[index+1:]:
                if path==other or path.startswith(other+"/") or other.startswith(path+"/"):
                    raise SpecError(f"implementation ownership overlaps: {owner} and {peer}")
        for target in self.targets.values():
            for field, kind in (("scope_parent", "domain"), ("component_parent", "component")):
                parent = getattr(target, field)
                if parent is not None:
                    if parent not in self.targets or (self.targets[parent].kind == "domain") != (kind == "domain"):
                        raise SpecError(f"invalid {field} for {target.id}")
                seen = {target.id}
                while parent is not None:
                    if parent in seen:
                        raise SpecError(f"cycle in {field}: {target.id}")
                    seen.add(parent)
                    parent = getattr(self.targets[parent], field)
            for scope in target.participates_in:
                if scope not in self.targets or self.targets[scope].kind != "domain":
                    raise SpecError(f"unknown participating Domain: {scope}")
            for path in target.implementation:
                if any(p == path or p.startswith(path + "/") for p in paths):
                    raise SpecError(f"implementation grant includes a Spec document: {path}")
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

    def select(self, target_id: str, focus_id: str | None = None) -> SpecTarget:
        if target_id not in self.targets:
            raise SpecError(f"unknown Spec target: {target_id}", "unknown_target")
        if focus_id is not None and (focus_id not in self.focus or self.focus[focus_id][0] != target_id):
            raise SpecError("Feature/API focus must belong to the selected target", "invalid_focus")
        return self.targets[target_id]

    def documents(self, target: SpecTarget) -> tuple[SpecDocument, ...]:
        result = []
        for path in target.documents:
            raw = read_file(self.root, path)
            text = raw.decode("utf-8")
            metadata, body = parse_document(text, path) if text.startswith("---\n") else ({}, text)
            if not body.strip():
                raise SpecError(f"empty Spec document: {path}")
            result.append(SpecDocument(path, text, digest(raw), metadata, body))
        return tuple(result)

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

    def implementation_files(self, target: SpecTarget) -> tuple[str, ...]:
        result = []
        for relative in target.implementation:
            path = checked_path(self.root, relative)
            candidates = sorted(path.rglob("*")) if path.is_dir() else [path]
            for item in candidates:
                if item.is_symlink():
                    raise SpecError(f"implementation scope contains a symlink: {item}")
                if item.is_file() and not any(part in {"__pycache__", ".venv", "node_modules", ".git"} for part in item.parts):
                    result.append(item.relative_to(self.root).as_posix())
        return tuple(sorted(set(result)))
