"""Module contracts with four mandatory parts and entity-listed implementation files (Profile 10).

Module composition, dependency and file listing are independent relations. Resolving a Module
never reads a collaborator's body or a listed file's contents; scenarios, requirements and
entities are parsed from the Module's own registered documents.
"""
from __future__ import annotations

import hashlib
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..host.typed_data import canonical, decode, checked_path, safe_path
from ..frontmatter import parse_document
from .schema import ContractError, admit, validate


PROFILE_VERSION = 10
PROTOCOL_VERSION = "3.0.0"
REGISTRY_SCHEMA = 3
KINDS = frozenset({"module"})
SPEC_KINDS = frozenset({"module"})
IDENTITY = re.compile(r"^[a-z][a-z0-9]*(?:[.-][a-z0-9-]+)*$")
CONTRACT_BLOCK = re.compile(r"^```concorde-contract\s*\n(.*?)^```\s*$", re.M | re.S)
DEPENDENCIES_BLOCK = re.compile(r"^```concorde-dependencies\s*\n(.*?)^```\s*$", re.M | re.S)
DOCUMENT_BLOCK = re.compile(r"^```concorde-document\s*\n(.*?)^```\s*$", re.M | re.S)
ENTITIES_BLOCK = re.compile(r"^```concorde-entities\s*\n(.*?)^```\s*$", re.M | re.S)
HEADING = re.compile(r"^(#{1,6})[ \t]+(.*?)[ \t]*#*[ \t]*$")
SCENARIO_HEADING = re.compile(r"^(scenario\.[a-z0-9]+(?:[.-][a-z0-9-]+)*)[ \t]+[—–-][ \t]+(\S.*)$")
LIST_ITEM = re.compile(r"^[ \t]*(?:[-*+]|\d+[.)])[ \t]+(.*)$")
STEP = re.compile(r"^(GIVEN|WHEN|THEN|AND|BUT)[ \t]+(\S.*)$")
REQUIREMENT = re.compile(r"^(req\.[a-z0-9]+(?:[.-][a-z0-9-]+)*)[ \t]*:[ \t]+(\S.*)$")
SHALL = re.compile(r"\bSHALL(?: NOT)?\b")
MANDATORY_SECTIONS = ("Purpose", "Scenarios", "Entities", "Architecture")
CONTROL_PREFIXES = (".concorde/", ".git/", ".agents/", ".claude/", ".codex/", "generated/")
STEP_ORDER = {"GIVEN": 0, "WHEN": 1, "THEN": 2}


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


def walk_lines(body: str) -> list[tuple[int, str, str]]:
    """Classify every line as prose, fence-open, fenced or fence-close (1-based line numbers)."""
    result = []
    fence = None
    for number, line in enumerate(body.splitlines(), 1):
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
        if marker:
            token = marker.group(1)
            if fence is None:
                fence = token
                result.append((number, "fence-open", line))
                continue
            if token[0] == fence[0] and len(token) >= len(fence) and not line[marker.end():].strip():
                fence = None
                result.append((number, "fence-close", line))
                continue
        result.append((number, "fenced" if fence is not None else "prose", line))
    return result


def prose(body: str) -> str:
    """The document text outside code fences, used for heading and definition rules."""
    return "\n".join(line for _, kind, line in walk_lines(body) if kind == "prose")


@dataclass(frozen=True)
class SpecTarget:
    id: str
    kind: str
    title: str
    documents: tuple[str, ...]
    parent: str | None
    uses: tuple[str, ...]
    files: tuple[str, ...]
    checks: tuple[str, ...]

    @property
    def primary_document(self) -> str:
        """A Module's reading entry is explicit within its complete collection."""
        return next(path for path in self.documents if Path(path).name == "module.md")


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


@dataclass(frozen=True)
class Requirement:
    id: str
    text: str
    owner: str
    document: str
    line: int
    scenario_id: str | None


@dataclass(frozen=True)
class Scenario:
    id: str
    title: str
    owner: str
    document: str
    line: int
    steps: tuple[tuple[str, str], ...]
    requirements: tuple[str, ...]


@dataclass(frozen=True)
class SpecEntity:
    id: str
    title: str
    kind: str
    responsibility: str
    files: tuple[str, ...]
    pending: tuple[str, ...]
    target_id: str | None
    owner: str
    document: str


@dataclass(frozen=True)
class ModuleDefinitions:
    """Every scenario, requirement and entity a Module's own documents define."""

    scenarios: tuple[Scenario, ...]
    requirements: tuple[Requirement, ...]
    entities: tuple[SpecEntity, ...]


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
            raise SpecError("Profile 10 (four-part Module) is required; older profiles need explicit migration", "unsupported_profile")
        if set(self.config) != {"profile_version", "registry", "protocol", "capability_configuration"}:
            raise SpecError("configuration fields must be profile_version, registry, protocol, capability_configuration")
        self.registry_path = safe_path(self.config["registry"])
        self.registry_bytes = (bytes(registry_bytes) if registry_bytes is not None
                               else read_file(self.root, self.registry_path))
        self.document_overrides = {safe_path(path): bytes(content)
                                   for path, content in (document_overrides or {}).items()}
        self.registry = decode(self.registry_bytes.decode())
        if (set(self.registry) != {"schema_version", "project_id", "entry_target", "targets", "checks"}
                or self.registry["schema_version"] != REGISTRY_SCHEMA):
            raise SpecError("unsupported Spec registry schema")
        self.project_id = identifier(self.registry["project_id"])
        self.targets: dict[str, SpecTarget] = {}
        self.file_users: dict[str, tuple[str, ...]] = {}
        self.checks: dict[str, dict] = {}
        self.document_targets: dict[str, list[str]] = {}
        self._document_cache: dict[str, SpecDocument] = {}
        self._definition_cache: dict[str, ModuleDefinitions] = {}
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
        fields = {"id", "kind", "title", "documents", "parent", "uses", "files", "checks"}
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
                self.document_targets.setdefault(path, []).append(target_id)
            files = strings(raw["files"], "files")
            if list(files) != sorted(files):
                raise SpecError(f"target {target_id} files must be sorted")
            self.targets[target_id] = SpecTarget(target_id, raw["kind"], raw["title"], documents,
                raw["parent"], strings(raw["uses"], "uses"), files, strings(raw["checks"], "checks"))
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
        users: dict[str, list[str]] = {}
        for target in self.targets.values():
            for path in target.files:
                safe_path(path)
                if path.startswith(CONTROL_PREFIXES) or path in self.document_targets:
                    raise SpecError(f"listed file cannot be a control, generated or project Spec file: {path}")
                candidate = checked_path(self.root, path)
                if candidate.exists() and not candidate.is_file():
                    raise SpecError(f"entities list explicit files, not directories: {path}")
                users.setdefault(path, []).append(target.id)
        self.file_users = {path: tuple(owners) for path, owners in users.items()}
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
        target = self.targets[target_id]
        if focus_id is not None:
            try:
                scenarios = {scenario.id for scenario in self.definitions(target).scenarios}
            except SpecError as error:
                raise SpecError(f"scenario focus cannot be resolved: {error}", "invalid_focus") from error
            if focus_id not in scenarios:
                raise SpecError("scenario focus must belong to the selected target", "invalid_focus")
        return target

    def documents(self, target: SpecTarget) -> tuple[SpecDocument, ...]:
        return tuple(self.document(path) for path in target.documents)

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

    def definitions(self, target: SpecTarget) -> ModuleDefinitions:
        """Parse the scenarios, requirements and entities the Module's own documents define."""
        if target.id in self._definition_cache:
            return self._definition_cache[target.id]
        scenarios: list[Scenario] = []
        requirements: list[Requirement] = []
        entities: list[SpecEntity] = []
        seen: dict[str, str] = {}
        for document in self.documents(target):
            shared = len(document.targets) > 1
            document_scenarios, document_requirements = _parse_scenarios(document, target.id)
            if shared and (document_scenarios or document_requirements):
                raise SpecError(f"a shared document cannot define scenarios or requirements: {document.path}")
            for scenario in document_scenarios:
                if scenario.id in seen:
                    raise SpecError(f"duplicate scenario definition: {scenario.id} ({seen[scenario.id]}, {document.path})")
                seen[scenario.id] = document.path
            for requirement in document_requirements:
                if requirement.id in seen:
                    raise SpecError(f"duplicate requirement definition: {requirement.id} ({seen[requirement.id]}, {document.path})")
                seen[requirement.id] = document.path
            scenarios.extend(document_scenarios)
            requirements.extend(document_requirements)
            document_entities = _parse_entities(document, target.id)
            if shared and document_entities:
                raise SpecError(f"a shared document cannot declare entities: {document.path}")
            for entity in document_entities:
                if entity.id in seen:
                    raise SpecError(f"duplicate entity definition: {entity.id} ({seen[entity.id]}, {document.path})")
                seen[entity.id] = document.path
            entities.extend(document_entities)
        titles: dict[str, str] = {}
        files: dict[str, str] = {}
        related = {child.id for child in self.children(target)} | set(target.uses)
        represented: dict[str, str] = {}
        for entity in entities:
            if entity.title in titles:
                raise SpecError(f"entity titles must be unique within a Module: {entity.title!r} ({titles[entity.title]}, {entity.id})")
            titles[entity.title] = entity.id
            for path in entity.files:
                if path in files:
                    raise SpecError(f"file is listed by two entities of {target.id}: {path} ({files[path]}, {entity.id})")
                files[path] = entity.id
            if entity.target_id is not None:
                if entity.target_id not in related:
                    raise SpecError(f"entity {entity.id} names {entity.target_id}, which is not a child or used Module of {target.id}")
                if entity.target_id in represented:
                    raise SpecError(f"Module {entity.target_id} is represented by two entities of {target.id}: {represented[entity.target_id]}, {entity.id}")
                represented[entity.target_id] = entity.id
        result = ModuleDefinitions(tuple(scenarios), tuple(requirements), tuple(entities))
        self._definition_cache[target.id] = result
        return result

    def entities(self, target: SpecTarget) -> tuple[SpecEntity, ...]:
        return self.definitions(target).entities

    def scenarios(self, target: SpecTarget) -> tuple[Scenario, ...]:
        return self.definitions(target).scenarios

    def entity_files(self, target: SpecTarget) -> dict[str, SpecEntity]:
        """Exact declared files of the Module's entities, keyed by path."""
        return {path: entity for entity in self.entities(target) for path in entity.files}

    def children(self, target: SpecTarget) -> tuple[SpecTarget, ...]:
        return tuple(t for t in self.targets.values() if t.parent == target.id)

    def descendants(self, target: SpecTarget) -> tuple[SpecTarget, ...]:
        result = []
        for child in self.children(target):
            result.extend((child, *self.descendants(child)))
        return tuple(result)

    def implementation_paths(self, target: SpecTarget) -> tuple[str, ...]:
        """Exact registered file authority, including files yet to be authored."""
        return target.files

    def implementation_files(self, target: SpecTarget) -> tuple[str, ...]:
        return tuple(path for path in target.files if checked_path(self.root, path).is_file())

    def missing_files(self, target: SpecTarget) -> tuple[str, ...]:
        return tuple(path for path in target.files if not checked_path(self.root, path).is_file())

    def affected_modules(self, paths: tuple[str, ...] | list[str]) -> tuple[SpecTarget, ...]:
        """Reverse lookup for changed listed files; no Spec bodies read."""
        users = {user for path in paths for user in self.file_users.get(path, ())}
        return tuple(target for target in self.targets.values() if target.id in users)


def _logical_lines(body: str) -> list[tuple[int, str, str]]:
    """Join lazy continuation lines onto their list item so wrapped steps stay one item."""
    result: list[tuple[int, str, str]] = []
    previous_item = False
    for number, kind, line in walk_lines(body):
        if kind != "prose":
            result.append((number, kind, line))
            previous_item = False
            continue
        continuation = (previous_item and line[:1] in (" ", "\t") and line.strip()
                        and not LIST_ITEM.match(line) and not HEADING.match(line))
        if continuation:
            last_number, last_kind, last_line = result[-1]
            result[-1] = (last_number, last_kind, last_line.rstrip() + " " + line.strip())
            continue
        result.append((number, kind, line))
        previous_item = bool(LIST_ITEM.match(line))
    return result


def _parse_scenarios(document: SpecDocument, owner: str) -> tuple[list[Scenario], list[Requirement]]:
    """Scenario sections and requirement items of one single-owner document."""
    scenarios: list[Scenario] = []
    requirements: list[Requirement] = []
    current: dict | None = None

    def close() -> None:
        nonlocal current
        if current is None:
            return
        keywords = [keyword for keyword, _ in current["steps"]]
        if "WHEN" not in keywords or "THEN" not in keywords:
            raise SpecError(f"scenario {current['id']} needs at least one WHEN and one THEN step: {document.path}")
        scenarios.append(Scenario(current["id"], current["title"], owner, document.path, current["line"],
                                  tuple(current["steps"]), tuple(current["requirements"])))
        current = None

    for number, kind, line in _logical_lines(document.body):
        if kind != "prose":
            continue
        heading = HEADING.match(line)
        if heading:
            close()
            text = heading.group(2)
            scenario = SCENARIO_HEADING.match(text)
            if scenario:
                if not 2 <= len(heading.group(1)) <= 5:
                    raise SpecError(f"scenario headings use levels 2 to 5: {document.path}:{number}")
                current = {"id": identifier(scenario.group(1)), "title": scenario.group(2).strip(),
                           "line": number, "steps": [], "requirements": [], "phase": None}
            elif text.startswith("scenario."):
                raise SpecError(f"malformed scenario heading: {document.path}:{number}")
            continue
        item = LIST_ITEM.match(line)
        if not item:
            continue
        text = item.group(1).strip()
        requirement = REQUIREMENT.match(text)
        if requirement:
            if not SHALL.search(requirement.group(2)):
                raise SpecError(f"requirement {requirement.group(1)} must contain SHALL or SHALL NOT: {document.path}:{number}")
            record = Requirement(identifier(requirement.group(1)), requirement.group(2).strip(), owner,
                                 document.path, number, current["id"] if current else None)
            requirements.append(record)
            if current is not None:
                current["requirements"].append(record.id)
            continue
        if text.startswith("req."):
            raise SpecError(f"malformed requirement item: {document.path}:{number}")
        if current is None:
            continue
        step = STEP.match(text)
        if not step:
            raise SpecError(f"scenario {current['id']} contains a list item that is neither a step nor a requirement: {document.path}:{number}")
        keyword = step.group(1)
        if keyword in {"AND", "BUT"}:
            if current["phase"] is None:
                raise SpecError(f"scenario {current['id']} cannot start with {keyword}: {document.path}:{number}")
        else:
            previous = current["phase"]
            if previous is None and keyword == "THEN":
                raise SpecError(f"scenario {current['id']} cannot start with THEN: {document.path}:{number}")
            if previous is not None and STEP_ORDER[keyword] <= STEP_ORDER[previous]:
                raise SpecError(f"scenario {current['id']} steps must follow GIVEN, WHEN, THEN order: {document.path}:{number}")
            current["phase"] = keyword
        current["steps"].append((keyword, step.group(2).strip()))
    close()
    return scenarios, requirements


def _parse_entities(document: SpecDocument, owner: str) -> list[SpecEntity]:
    entities: list[SpecEntity] = []
    required = {"id", "title", "kind", "responsibility"}
    optional = {"files", "pending", "target_id"}
    for match in ENTITIES_BLOCK.finditer(document.body):
        values = decode(match.group(1))
        if not isinstance(values, list) or not values:
            raise SpecError(f"concorde-entities must be a nonempty JSON array: {document.path}")
        for value in values:
            if not isinstance(value, dict) or not required <= set(value) or set(value) - required - optional:
                raise SpecError(f"entity requires id/title/kind/responsibility and only files/pending/target_id: {document.path}")
            entity_id = identifier(value["id"])
            for key in ("title", "kind", "responsibility"):
                if not isinstance(value[key], str) or not value[key].strip():
                    raise SpecError(f"entity {entity_id} {key} must be a nonempty string: {document.path}")
            files = strings(value["files"], f"entity {entity_id} files", nonempty=True) if "files" in value else ()
            for path in files:
                safe_path(path)
                if path.startswith(CONTROL_PREFIXES):
                    raise SpecError(f"entity {entity_id} lists a control or generated file: {path}")
            pending = strings(value["pending"], f"entity {entity_id} pending") if "pending" in value else ()
            if set(pending) - set(files):
                raise SpecError(f"entity {entity_id} pending files must also be listed in files: {document.path}")
            target_id = None
            if "target_id" in value:
                target_id = identifier(value["target_id"])
                if files:
                    raise SpecError(f"entity {entity_id} stands for {target_id} and cannot list files: {document.path}")
            entities.append(SpecEntity(entity_id, value["title"].strip(), value["kind"].strip(),
                                       value["responsibility"].strip(), files, pending, target_id,
                                       owner, document.path))
    return entities
