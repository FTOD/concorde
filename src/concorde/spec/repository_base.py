"""Shared Module identities, Markdown grammar and deterministic registry/file operations.

Module composition, dependency and file listing are independent relations. Resolving a Module
never reads a collaborator's body or a listed file's contents; requirements, scenarios and
entities are parsed from the Module's own registered documents. Scenario verification is read
from the tests the Module lists, never from its Spec.
"""

from __future__ import annotations

import hashlib
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .typed_data import canonical, decode, checked_path, safe_path
from .frontmatter import parse_document
from .schema import ContractError, admit, validate


PROFILE_VERSION = 14
PROTOCOL_VERSION = "9.0.0"
REGISTRY_SCHEMA = 5
KINDS = frozenset({"module"})
SPEC_KINDS = frozenset({"module"})
IDENTITY = re.compile(r"^[a-z][a-z0-9]*(?:[.-][a-z0-9-]+)*$")
CONTRACT_BLOCK = re.compile(r"^```concorde-contract\s*\n(.*?)^```\s*$", re.M | re.S)
HEADING = re.compile(r"^(#{1,6})[ \t]+(.*?)[ \t]*#*[ \t]*$")
SCENARIO_HEADING = re.compile(
    r"^(scenario\.[a-z0-9]+(?:[.-][a-z0-9-]+)*)[ \t]+[—–-][ \t]+(\S.*)$"
)
LIST_ITEM = re.compile(r"^[ \t]*(?:[-*+]|\d+[.)])[ \t]+(.*)$")
STEP = re.compile(r"^(GIVEN|WHEN|THEN|AND|BUT)[ \t]+(\S.*)$")
REQUIREMENT_HEADING = re.compile(
    r"^(req\.[a-z0-9]+(?:[.-][a-z0-9-]+)*)[ \t]+[—–-][ \t]+(\S.*)$"
)
REQUIREMENT_ITEM = re.compile(r"^req\.[a-z0-9.-]+[ \t]*:")
SHALL = re.compile(r"\bSHALL(?: NOT)?\b")
ANCHOR_PREFIXES = ("scenario.", "req.", "entity.", "contract.")
CONTROL_PREFIXES = (
    ".concorde/",
    ".git/",
    ".agents/",
    ".claude/",
    ".codex/",
    "generated/",
)
SKIPPED_DIRECTORIES = frozenset(
    {"node_modules", "__pycache__", ".venv", "build", "dist"}
)
SKIPPED_SUFFIXES = (".pyc", ".log")
# External reference material (Protocol 5.1 ``references`` of kind ``external``) is expanded and
# digested as text: media and archives are excluded by suffix so a vendored documentation or
# source tree costs its readable bytes, not its images.
REFERENCE_SKIPPED_SUFFIXES = (
    *SKIPPED_SUFFIXES,
    ".gif",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".svg",
    ".mp4",
    ".webm",
    ".ico",
    ".woff",
    ".woff2",
    ".ttf",
    ".otf",
    ".pdf",
    ".zip",
    ".gz",
    ".tar",
    ".tgz",
    ".bz2",
    ".xz",
    ".7z",
    ".jar",
    ".whl",
    ".so",
    ".dylib",
    ".dll",
)
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
        raise SpecError(
            f"required regular file is missing: {relative}", "missing_source", relative
        )
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    with os.fdopen(descriptor, "rb") as stream:
        return stream.read()


def strings(value: Any, label: str, *, nonempty: bool = False) -> tuple[str, ...]:
    if (
        not isinstance(value, list)
        or any(not isinstance(x, str) or not x.strip() for x in value)
        or len(set(value)) != len(value)
        or (nonempty and not value)
    ):
        raise SpecError(
            f"{label} must be a {'nonempty ' if nonempty else ''}unique string array"
        )
    return tuple(value)


def identifier(value: Any) -> str:
    if not isinstance(value, str) or not IDENTITY.fullmatch(value):
        raise SpecError(f"invalid stable identity: {value!r}")
    return value


def is_directory_entry(entry: str) -> bool:
    """A listing entry with a trailing slash binds every regular file below the directory."""
    return entry.endswith("/")


def entry_base(entry: str) -> str:
    return entry[:-1] if entry.endswith("/") else entry


def check_entry(entry: str) -> str:
    """Validate the spelling of one listing entry and return its base path."""
    if not isinstance(entry, str) or entry.endswith("//") or entry == "/":
        raise SpecError(f"invalid listing entry: {entry!r}")
    base = entry_base(entry)
    safe_path(base)
    if (base + "/").startswith(CONTROL_PREFIXES):
        raise SpecError(f"listed entry cannot be a control or generated path: {entry}")
    return base


def covers(entry: str, path: str) -> bool:
    """Whether a listing entry binds the given concrete file path."""
    return path.startswith(entry) if is_directory_entry(entry) else path == entry


def most_specific(entries, path: str) -> str | None:
    """The entry that owns a covered path: an exact file first, then the longest directory."""
    matches = [entry for entry in entries if covers(entry, path)]
    if not matches:
        return None
    return max(matches, key=lambda entry: (not is_directory_entry(entry), len(entry)))


def skipped_path(relative: str) -> bool:
    """Whether the directory walk excludes this path, expressed below a listed directory."""
    return any(
        part in SKIPPED_DIRECTORIES or part.startswith(".")
        for part in relative.split("/")
    ) or relative.endswith(SKIPPED_SUFFIXES)


def bound_by(entry: str, path: str) -> bool:
    """Whether one listing entry binds a concrete file path, applying directory exclusions."""
    return covers(entry, path) and (
        not is_directory_entry(entry) or not skipped_path(path[len(entry) :])
    )


def entry_exists(root: Path, entry: str) -> bool:
    candidate = checked_path(root, entry_base(entry))
    return candidate.is_dir() if is_directory_entry(entry) else candidate.is_file()


def expand_entry(
    root: Path, entry: str, *, skipped_suffixes: tuple[str, ...] = SKIPPED_SUFFIXES
) -> list[str]:
    """Existing regular files bound by one entry, skipping excluded directories and files."""
    if not is_directory_entry(entry):
        return [entry] if checked_path(root, entry).is_file() else []
    directory = checked_path(root, entry_base(entry))
    if directory.is_symlink() or not directory.is_dir():
        return []
    result = []
    for current, names, files in os.walk(directory):
        names[:] = sorted(
            name
            for name in names
            if name not in SKIPPED_DIRECTORIES
            and not name.startswith(".")
            and not (Path(current) / name).is_symlink()
        )
        for name in sorted(files):
            if name.startswith(".") or name.endswith(skipped_suffixes):
                continue
            candidate = Path(current) / name
            if candidate.is_symlink() or not candidate.is_file():
                continue
            result.append(candidate.relative_to(root).as_posix())
    return sorted(result)


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
            if (
                token[0] == fence[0]
                and len(token) >= len(fence)
                and not line[marker.end() :].strip()
            ):
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
    references: tuple[tuple[str, str], ...] = ()

    @property
    def sources(self) -> tuple[str, ...]:
        return tuple(
            member for path in self.documents for member in (path, path + ".json")
        )

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
    owner: str
    metadata: dict
    body: str


@dataclass(frozen=True)
class SpecResolution:
    """Canonical immutable resolution; decoding cannot mutate the repository snapshot."""

    serialized: str

    @property
    def value(self) -> dict:
        return decode(self.serialized)

    def __getattr__(self, name):
        value = self.value
        if name in value:
            return value[name]
        raise AttributeError(name)


@dataclass(frozen=True)
class Requirement:
    """One Module-level promise: a heading section whose statement holds one SHALL sentence."""

    id: str
    title: str
    statement: str
    owner: str
    document: str
    line: int


@dataclass(frozen=True)
class Scenario:
    """One concrete, testable situation: a heading section whose list items are all steps."""

    id: str
    title: str
    owner: str
    document: str
    line: int
    steps: tuple[tuple[str, str], ...]


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

    @property
    def anchors(self) -> dict[str, str]:
        """Every addressable identity of the Module mapped to the document that defines it."""
        return {
            item.id: item.document
            for group in (self.scenarios, self.requirements, self.entities)
            for item in group
        }


class RepositoryCore:
    root: Path
    package_root: Path
    config: dict
    registry_path: str
    registry_bytes: bytes
    registry: dict
    document_overrides: dict[str, bytes]
    targets: dict[str, SpecTarget]
    document_targets: dict[str, list[str]]
    file_users: dict[str, tuple[str, ...]]
    checks: dict[str, dict]
    _definition_cache: dict[str, ModuleDefinitions]
    _reference_digest_cache: dict[str, str]
    _identity_paths: dict[str, str]
    protocol_assets: dict[str, bytes]

    def _protocol(self) -> tuple[dict, dict[str, bytes]]:
        """Admit the Protocol copy the installer placed under .concorde/protocol/, as the configuration binds it.

        The copy is what agents are granted as project files. The binding must name exactly that
        copy and the installed package must carry the same manifest: an updated installation is
        rejected until the developer accepts it explicitly (configure with ``accept_protocol``),
        never adopted silently.
        """
        from ..distribution.build import BuildError, verify_fresh
        from ..distribution.project_defaults import (
            PROTOCOL_DIR,
            PROTOCOL_MANIFEST_PATH,
            protocol_asset_path,
        )

        try:
            verify_fresh(self.package_root)
        except BuildError as error:
            raise SpecError(str(error), error.code) from error
        try:
            raw = read_file(self.root, PROTOCOL_MANIFEST_PATH)
        except (SpecError, OSError) as error:
            raise SpecError(
                "project has no Protocol copy under .concorde/protocol; run the installer",
                "protocol_mismatch",
            ) from error
        manifest = decode(raw.decode())
        binding = {"version": manifest.get("version"), "digest": digest(raw)}
        if self.config["protocol"] != binding or binding["version"] != PROTOCOL_VERSION:
            raise SpecError(
                "project Protocol binding does not match the installed Protocol copy; accept it "
                "explicitly with concorde-configure",
                "protocol_mismatch",
            )
        if read_file(self.package_root, "protocol/manifest.json") != raw:
            raise SpecError(
                "installed package Protocol differs from the project's Protocol copy; reinstall",
                "protocol_mismatch",
            )
        assets = {}
        for item in manifest["assets"]:
            path = protocol_asset_path(item["path"])
            try:
                content = read_file(self.root, path)
            except (SpecError, OSError) as error:
                raise SpecError(
                    f"installed Protocol asset is missing: {path}", "protocol_mismatch"
                ) from error
            if digest(content) != item["digest"]:
                raise SpecError(
                    f"installed Protocol asset has changed: {path}", "protocol_mismatch"
                )
            assets[path] = content
        required = {
            f"{PROTOCOL_DIR}/principles.md",
            *(f"{PROTOCOL_DIR}/kinds/{kind}.md" for kind in SPEC_KINDS),
        }
        if not required.issubset(assets):
            raise SpecError(
                "Protocol manifest is missing global principles or kind definitions"
            )
        return manifest, assets

    def _load_registry(self) -> None:
        if (
            not isinstance(self.registry["targets"], list)
            or not self.registry["targets"]
        ):
            raise SpecError("registry requires targets")
        fields = {
            "id",
            "kind",
            "title",
            "documents",
            "references",
            "parent",
            "uses",
            "files",
            "checks",
        }
        for raw in self.registry["targets"]:
            if not isinstance(raw, dict) or set(raw) != fields:
                raise SpecError(f"target fields must be {sorted(fields)}")
            target_id = identifier(raw["id"])
            if (
                target_id in self.targets
                or not isinstance(raw["kind"], str)
                or raw["kind"] not in KINDS
            ):
                raise SpecError(f"duplicate target or unknown kind: {target_id}")
            if not isinstance(raw["title"], str) or not raw["title"].strip():
                raise SpecError(f"target {target_id} requires a title")
            documents = strings(raw["documents"], "documents", nonempty=True)
            if sum(Path(p).name == "module.md" for p in documents) != 1:
                raise SpecError(
                    f"Module {target_id} must register exactly one module.md reading entry"
                )
            for path in documents:
                safe_path(path)
                if not path.endswith(".md") or path.startswith((".concorde/", ".git/")):
                    raise SpecError(f"Spec documents must be durable Markdown: {path}")
                self.document_targets.setdefault(path, []).append(target_id)
                if len(self.document_targets[path]) != 1:
                    raise SpecError(
                        f"document must have exactly one owner: {path}",
                        "invalid_owner",
                        path,
                    )
            references = raw["references"]
            if not isinstance(references, list):
                raise SpecError(
                    "references must be an explicit array",
                    "invalid_reference",
                    target_id,
                )
            pairs = []
            for reference in references:
                if isinstance(reference, dict) and reference.get("kind") == "external":
                    # Protocol 5.1: vendored material the Module reads but does not own, a
                    # project-relative file or directory prefix, granted as files and never injected.
                    if set(reference) != {"kind", "path"}:
                        raise SpecError(
                            "external reference requires kind and path",
                            "invalid_reference",
                            target_id,
                        )
                    check_entry(reference["path"])
                    pair = ("external", reference["path"])
                elif (
                    not isinstance(reference, dict)
                    or set(reference) != {"kind", "id"}
                    or not isinstance(reference["kind"], str)
                    or reference["kind"] not in {"module", "document"}
                ):
                    raise SpecError(
                        "reference requires kind module|document and id, or kind external and path",
                        "invalid_reference",
                        target_id,
                    )
                else:
                    pair = (reference["kind"], identifier(reference["id"]))
                if pair in pairs or pair == ("module", target_id):
                    raise SpecError(
                        "duplicate or self reference", "invalid_reference", target_id
                    )
                pairs.append(pair)
            files = strings(raw["files"], "files")
            if list(files) != sorted(files):
                raise SpecError(f"target {target_id} files must be sorted")
            for kind, entry in pairs:
                if kind == "external" and any(
                    covers(listed, entry_base(entry))
                    or covers(entry, listed)
                    or listed == entry
                    for listed in files
                ):
                    raise SpecError(
                        f"external reference overlaps the implementation files of {target_id}: {entry}",
                        "invalid_reference",
                        target_id,
                    )
            self.targets[target_id] = SpecTarget(
                target_id,
                raw["kind"],
                raw["title"],
                documents,
                raw["parent"],
                strings(raw["uses"], "uses"),
                files,
                strings(raw["checks"], "checks"),
                tuple(pairs),
            )
        for target in self.targets.values():
            if self.document_targets[target.primary_document] != [target.id]:
                raise SpecError(
                    f"Module reading entry must belong only to its Module: {target.primary_document}"
                )
            for kind, entry in target.references:
                if kind == "external" and (
                    entry in self.document_targets
                    or (
                        is_directory_entry(entry)
                        and any(
                            covers(entry, document)
                            for document in self.document_targets
                        )
                    )
                ):
                    raise SpecError(
                        f"external reference cannot be or contain a project Spec document: {entry}",
                        "invalid_reference",
                        target.id,
                    )
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
                    raise SpecError(
                        f"unknown or self dependency for {target.id}: {peer}"
                    )
        # A shared capability is a sibling, never a child owned by one of its consumers.
        for provider in self.targets.values():
            consumers = [t for t in self.targets.values() if provider.id in t.uses]
            if len(consumers) > 1 and any(
                t.parent != provider.parent for t in consumers
            ):
                raise SpecError(
                    f"shared Module {provider.id} and its consumers must be siblings"
                )
        users: dict[str, list[str]] = {}
        for target in self.targets.values():
            for entry in target.files:
                base = check_entry(entry)
                if is_directory_entry(entry):
                    if any(
                        covers(entry, document) for document in self.document_targets
                    ):
                        raise SpecError(
                            f"a listed directory cannot contain a project Spec document: {entry}"
                        )
                    candidate = checked_path(self.root, base)
                    if candidate.exists() and not candidate.is_dir():
                        raise SpecError(
                            f"listed directory entry is not a directory: {entry}"
                        )
                else:
                    if entry in self.document_targets:
                        raise SpecError(
                            f"listed file cannot be a project Spec document: {entry}"
                        )
                    candidate = checked_path(self.root, entry)
                    if candidate.exists() and not candidate.is_file():
                        raise SpecError(
                            f"listed file entry is not a regular file; use a trailing slash for a directory: {entry}"
                        )
                users.setdefault(entry, []).append(target.id)
        self.file_users = {entry: tuple(owners) for entry, owners in users.items()}
        for raw in self.registry["checks"]:
            if (
                not isinstance(raw, dict)
                or not {"id", "target_id", "argv", "timeout_seconds"}.issubset(raw)
                or set(raw) - {"id", "target_id", "argv", "timeout_seconds", "inputs"}
            ):
                raise SpecError("check requires id, target_id, argv, timeout_seconds")
            key = identifier(raw["id"])
            if key in self.checks or raw["target_id"] not in self.targets:
                raise SpecError(f"duplicate or unowned check: {key}")
            if (
                not isinstance(raw["argv"], list)
                or not raw["argv"]
                or any(not isinstance(x, str) or not x for x in raw["argv"])
            ):
                raise SpecError("check argv must be a nonempty array of strings")
            if (
                type(raw["timeout_seconds"]) is not int
                or not 1 <= raw["timeout_seconds"] <= 3600
            ):
                raise SpecError("check timeout must be 1..3600 seconds")
            for path in strings(raw.get("inputs", []), "check inputs"):
                safe_path(path)
            self.checks[key] = raw
        for target in self.targets.values():
            if any(
                k not in self.checks or self.checks[k]["target_id"] != target.id
                for k in target.checks
            ):
                raise SpecError(
                    f"target {target.id} references a missing or foreign check"
                )

    def select(self, target_id: str, focus_id: str | None = None) -> SpecTarget:
        if target_id not in self.targets:
            raise SpecError(f"unknown Spec target: {target_id}", "unknown_target")
        target = self.targets[target_id]
        if focus_id is not None:
            try:
                scenarios = {
                    scenario.id for scenario in self.definitions(target).scenarios
                }
            except SpecError as error:
                raise SpecError(
                    f"scenario focus cannot be resolved: {error}", "invalid_focus"
                ) from error
            if focus_id not in scenarios:
                raise SpecError(
                    "scenario focus must belong to the selected target", "invalid_focus"
                )
        return target

    def unit(self, path: str):
        raise NotImplementedError("document-unit source backend required")

    def documents(self, target: SpecTarget) -> tuple[SpecDocument, ...]:
        return tuple(self.document(path) for path in target.documents)

    def _document_index(self) -> dict[str, str]:
        raise NotImplementedError("document-unit source backend required")

    def _query(self, query_id: str) -> tuple[SpecTarget, str]:
        if query_id in self.targets:
            return self.targets[query_id], "module"
        if query_id.startswith("scenario."):
            # Resolve heading declarations only. Entity, dependency and interface parsers must
            # not turn a locator query into a read of unrelated Module behavioral definitions.
            import io

            matches = []
            for path, owners in self.document_targets.items():
                stream = (
                    io.BytesIO(self.document_overrides[path])
                    if path in self.document_overrides
                    else os.fdopen(
                        os.open(
                            checked_path(self.root, path),
                            os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
                        ),
                        "rb",
                    )
                )
                fence = None
                with stream:
                    for raw in stream:
                        marker = re.match(rb"^ {0,3}(`{3,}|~{3,})", raw)
                        if marker:
                            token = marker.group(1)
                            if fence is None:
                                fence = token
                            elif (
                                token[0] == fence[0]
                                and len(token) >= len(fence)
                                and not raw[marker.end() :].strip()
                            ):
                                fence = None
                            continue
                        if fence is not None or not raw.startswith(b"#"):
                            continue
                        heading = HEADING.match(raw.decode("utf-8").rstrip("\r\n"))
                        scenario = (
                            SCENARIO_HEADING.match(heading.group(2))
                            if heading and 2 <= len(heading.group(1)) <= 5
                            else None
                        )
                        if scenario and scenario.group(1) == query_id:
                            matches.append(owners[0])
            if len(matches) == 1:
                return self.targets[matches[0]], "scenario"
        raise SpecError(
            f"unsupported or unknown context identity: {query_id}",
            "invalid_target",
            query_id,
        )

    def _context_paths(self, target: SpecTarget) -> dict[str, list[dict]]:
        index = self._document_index()
        paths = {
            path: [{"kind": "owned", "id": target.id}] for path in target.documents
        }
        for kind, identity in target.references:
            if kind == "external":
                continue  # granted as files by the development tool, never included in Spec context
            if kind == "module":
                if identity not in self.targets or identity == target.id:
                    raise SpecError(
                        f"unknown or self Module reference: {identity}",
                        "invalid_reference",
                        target.id,
                    )
                selected = self.targets[identity].documents
            else:
                if identity not in index:
                    raise SpecError(
                        f"unknown document reference: {identity}",
                        "invalid_reference",
                        target.id,
                    )
                selected = (index[identity],)
                if selected[0] in target.documents:
                    raise SpecError(
                        f"self document reference: {identity}",
                        "invalid_reference",
                        target.id,
                    )
            for path in selected:
                paths.setdefault(path, []).append({"kind": kind, "id": identity})
        return {
            path: sorted(paths[path], key=lambda reason: (reason["kind"], reason["id"]))
            for path in sorted(paths)
        }

    def spec_files(self, entity_id: str) -> tuple[str, ...]:
        raise NotImplementedError("document-unit source backend required")

    def source_bytes(self, path: str) -> bytes:
        raise NotImplementedError("document-unit source backend required")

    def source_is_overridden(self, path: str) -> bool:
        raise NotImplementedError("document-unit source backend required")

    def source_records(self, path: str, reasons: list[dict]) -> list[dict]:
        raise NotImplementedError("document-unit source backend required")

    def validate_source_records(self, records: list[dict]) -> None:
        raise NotImplementedError("document-unit source backend required")

    def spec_context(self, entity_id: str) -> SpecResolution:
        raise NotImplementedError("document-unit source backend required")

    def context_users(self, document_id: str) -> tuple[str, ...]:
        index = self._document_index()
        if document_id not in index:
            raise SpecError(f"unknown document: {document_id}", "invalid_target")
        return tuple(
            sorted(
                t.id
                for t in self.targets.values()
                if index[document_id] in self._context_paths(t)
            )
        )

    def context_identities(self) -> dict[str, str]:
        return {
            target.id: digest(self.spec_context(target.id).value)
            for target in self.targets.values()
        }

    def affected_contexts(self, candidate: RepositoryCore) -> tuple[str, ...]:
        before, after = self.context_identities(), candidate.context_identities()
        return tuple(
            sorted(
                identity
                for identity in before.keys() | after.keys()
                if before.get(identity) != after.get(identity)
            )
        )

    def document(self, path: str) -> SpecDocument:
        raise NotImplementedError("document-unit source backend required")

    def contracts(self, target: SpecTarget) -> tuple[dict, ...]:
        return self._contracts_in_documents(self.documents(target))

    def _contracts_in_documents(self, documents) -> tuple[dict, ...]:
        raise NotImplementedError("document-unit source backend required")

    def context_contracts(self, target: SpecTarget) -> tuple[dict, ...]:
        raise NotImplementedError("document-unit source backend required")

    def contract_bindings(self, target: SpecTarget) -> tuple[dict, ...]:
        raise NotImplementedError("document-unit source backend required")

    def dependencies(self, target: SpecTarget) -> tuple[dict, ...]:
        raise NotImplementedError("document-unit source backend required")

    def definitions(self, target: SpecTarget) -> ModuleDefinitions:
        raise NotImplementedError("document-unit source backend required")

    def entities(self, target: SpecTarget) -> tuple[SpecEntity, ...]:
        return self.definitions(target).entities

    def scenarios(self, target: SpecTarget) -> tuple[Scenario, ...]:
        return self.definitions(target).scenarios

    def requirements(self, target: SpecTarget) -> tuple[Requirement, ...]:
        return self.definitions(target).requirements

    def verifications(self, target: SpecTarget):
        """Scenario declarations read from the test files the Module's entities bind."""
        from .verification import scan_declarations

        return scan_declarations(self.root, self.implementation_files(target))

    def scenario_verifications(self, target: SpecTarget) -> dict[str, tuple]:
        """Every scenario of the Module mapped to the test declarations that name it, project-wide."""
        from .verification import scan_declarations

        paths = sorted(
            {
                path
                for other in self.targets.values()
                for path in self.implementation_files(other)
            }
        )
        declared: dict[str, list] = {
            scenario.id: [] for scenario in self.scenarios(target)
        }
        for declaration in scan_declarations(self.root, paths):
            if declaration.scenario_id in declared:
                declared[declaration.scenario_id].append(declaration)
        return {scenario_id: tuple(items) for scenario_id, items in declared.items()}

    def entity_files(self, target: SpecTarget) -> dict[str, SpecEntity]:
        """Declared listing entries of the Module's entities, keyed by entry (exact file or directory)."""
        return {
            entry: entity for entity in self.entities(target) for entry in entity.files
        }

    def external_references(self, target: SpecTarget) -> tuple[str, ...]:
        """The Module's ``external`` references in declaration order: exact files or directory prefixes."""
        return tuple(value for kind, value in target.references if kind == "external")

    def external_reference_paths(self, target: SpecTarget) -> tuple[str, ...]:
        """External reference authority roots without trailing slashes, for read-only permissions."""
        return tuple(
            dict.fromkeys(
                entry_base(entry) for entry in self.external_references(target)
            )
        )

    def external_reference_files(self, entry: str) -> tuple[str, ...]:
        """Existing readable files below one external reference entry, media and archives excluded."""
        return tuple(
            expand_entry(self.root, entry, skipped_suffixes=REFERENCE_SKIPPED_SUFFIXES)
        )

    def external_reference_digest(self, entry: str) -> str:
        """One digest per entry over its readable files' paths and bytes; cached per repository."""
        if entry not in self._reference_digest_cache:
            self._reference_digest_cache[entry] = digest(
                [
                    (path, digest(read_file(self.root, path)))
                    for path in self.external_reference_files(entry)
                ]
            )
        return self._reference_digest_cache[entry]

    def external_reference_records(self, target: SpecTarget) -> list[dict]:
        """The snapshot form of the Module's external references: entry, kind and tree digest."""
        return [
            {
                "path": entry,
                "directory": is_directory_entry(entry),
                "digest": self.external_reference_digest(entry),
            }
            for entry in self.external_references(target)
        ]

    def missing_external_references(self, target: SpecTarget) -> tuple[str, ...]:
        """External reference entries whose file or directory does not exist; references are never pending."""
        return tuple(
            entry
            for entry in self.external_references(target)
            if not entry_exists(self.root, entry)
        )

    def entity_for_path(self, target: SpecTarget, path: str) -> SpecEntity | None:
        """The entity whose most specific entry covers a concrete file path, if any."""
        entries = self.entity_files(target)
        entry = most_specific(entries, path)
        return entries[entry] if entry is not None else None

    def listing_users(self, path: str) -> tuple[str, ...]:
        """Modules whose listings cover a concrete file path."""
        return tuple(
            dict.fromkeys(
                user
                for entry, users in self.file_users.items()
                if covers(entry, path)
                for user in users
            )
        )

    def children(self, target: SpecTarget) -> tuple[SpecTarget, ...]:
        return tuple(t for t in self.targets.values() if t.parent == target.id)

    def descendants(self, target: SpecTarget) -> tuple[SpecTarget, ...]:
        result = []
        for child in self.children(target):
            result.extend((child, *self.descendants(child)))
        return tuple(result)

    def implementation_entries(self, target: SpecTarget) -> tuple[str, ...]:
        """The registered listing entries, exact files and directory prefixes, including pending ones."""
        return target.files

    def implementation_paths(self, target: SpecTarget) -> tuple[str, ...]:
        """Registered file authority roots without trailing slashes, for permissions and history."""
        return tuple(dict.fromkeys(entry_base(entry) for entry in target.files))

    def implementation_files(self, target: SpecTarget) -> tuple[str, ...]:
        """Existing regular files the Module's entries bind, directory prefixes expanded."""
        return tuple(
            sorted(
                {
                    path
                    for entry in target.files
                    for path in expand_entry(self.root, entry)
                }
            )
        )

    def missing_entries(self, target: SpecTarget) -> tuple[str, ...]:
        """Entries whose file or directory does not exist yet."""
        return tuple(
            entry for entry in target.files if not entry_exists(self.root, entry)
        )

    def covering_modules(self, target: SpecTarget) -> tuple[SpecTarget, ...]:
        """Modules whose entries cover this Module's own entries or the files those entries bind."""
        return self.affected_modules(
            (*target.files, *self.implementation_files(target))
        )

    def affected_modules(
        self, paths: tuple[str, ...] | list[str]
    ) -> tuple[SpecTarget, ...]:
        """Reverse lookup for changed files or entries; no Spec bodies read."""
        users = set()
        for path in paths:
            users.update(self.file_users.get(path, ()))
            users.update(self.listing_users(path))
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
        continuation = (
            previous_item
            and line[:1] in (" ", "\t")
            and line.strip()
            and not LIST_ITEM.match(line)
            and not HEADING.match(line)
        )
        if continuation:
            last_number, last_kind, last_line = result[-1]
            result[-1] = (
                last_number,
                last_kind,
                last_line.rstrip() + " " + line.strip(),
            )
            continue
        result.append((number, kind, line))
        previous_item = bool(LIST_ITEM.match(line))
    return result


def _paragraph_end(lines, index: int) -> int:
    """Index just past the prose paragraph that starts at ``index`` in the walked lines."""
    while index < len(lines) and lines[index][1] == "prose" and lines[index][2].strip():
        index += 1
    return index


def _parse_definitions(
    document: SpecDocument, owner: str
) -> tuple[list[Scenario], list[Requirement]]:
    """Scenario and requirement sections of one single-owner document.

    A scenario section holds steps only. A requirement section holds its statement, the first
    prose paragraph after the heading, with exactly one SHALL or SHALL NOT; anything after the
    statement is explanatory prose. Neither section may contain a nested heading.
    """
    scenarios: list[Scenario] = []
    requirements: list[Requirement] = []
    lines = _logical_lines(document.body)
    current: dict | None = None

    def close() -> None:
        nonlocal current
        if current is None:
            return
        if current["kind"] == "scenario":
            keywords = [keyword for keyword, _ in current["steps"]]
            if "WHEN" not in keywords or "THEN" not in keywords:
                raise SpecError(
                    f"scenario {current['id']} needs at least one WHEN and one THEN step: {document.path}"
                )
            scenarios.append(
                Scenario(
                    current["id"],
                    current["title"],
                    owner,
                    document.path,
                    current["line"],
                    tuple(current["steps"]),
                )
            )
        else:
            statement = current["statement"]
            if statement is None:
                raise SpecError(
                    f"requirement {current['id']} has no statement paragraph: {document.path}:{current['line']}"
                )
            requirements.append(
                Requirement(
                    current["id"],
                    current["title"],
                    statement,
                    owner,
                    document.path,
                    current["line"],
                )
            )
        current = None

    index = 0
    while index < len(lines):
        number, kind, line = lines[index]
        if kind != "prose":
            if (
                current is not None
                and current["kind"] == "requirement"
                and current["statement"] is None
            ):
                raise SpecError(
                    f"requirement {current['id']} must state its SHALL sentence before any fenced block: {document.path}:{number}"
                )
            index += 1
            continue
        heading = HEADING.match(line)
        if heading:
            close()
            text = heading.group(2)
            scenario = SCENARIO_HEADING.match(text)
            requirement = REQUIREMENT_HEADING.match(text)
            if scenario or requirement:
                if not 2 <= len(heading.group(1)) <= 5:
                    raise SpecError(
                        f"scenario and requirement headings use levels 2 to 5: {document.path}:{number}"
                    )
            if scenario:
                current = {
                    "kind": "scenario",
                    "id": identifier(scenario.group(1)),
                    "title": scenario.group(2).strip(),
                    "line": number,
                    "steps": [],
                    "phase": None,
                }
            elif requirement:
                current = {
                    "kind": "requirement",
                    "id": identifier(requirement.group(1)),
                    "title": requirement.group(2).strip(),
                    "line": number,
                    "statement": None,
                }
            elif text.startswith("scenario."):
                raise SpecError(f"malformed scenario heading: {document.path}:{number}")
            elif text.startswith("req."):
                raise SpecError(
                    f"malformed requirement heading: {document.path}:{number}"
                )
            index += 1
            continue
        item = LIST_ITEM.match(line)
        if item and REQUIREMENT_ITEM.match(item.group(1).strip()):
            raise SpecError(
                "a requirement is a heading section (### req.id — Title), not a list item: "
                f"{document.path}:{number}"
            )
        if current is None:
            index += 1
            continue
        if current["kind"] == "requirement":
            if current["statement"] is None and line.strip():
                if item:
                    raise SpecError(
                        f"requirement {current['id']} must state its SHALL sentence before any list: {document.path}:{number}"
                    )
                end = _paragraph_end(lines, index)
                statement = " ".join(entry[2].strip() for entry in lines[index:end])
                if len(SHALL.findall(statement)) != 1:
                    raise SpecError(
                        f"requirement {current['id']} statement must contain SHALL or SHALL NOT exactly once: {document.path}:{number}"
                    )
                current["statement"] = statement
                index = end
                continue
            index += 1
            continue
        if not item:
            index += 1
            continue
        text = item.group(1).strip()
        step = STEP.match(text)
        if not step:
            raise SpecError(
                f"scenario {current['id']} contains a list item that is not a GIVEN/WHEN/THEN/AND/BUT step: {document.path}:{number}"
            )
        keyword = step.group(1)
        if keyword in {"AND", "BUT"}:
            if current["phase"] is None:
                raise SpecError(
                    f"scenario {current['id']} cannot start with {keyword}: {document.path}:{number}"
                )
        else:
            previous = current["phase"]
            if previous is None and keyword == "THEN":
                raise SpecError(
                    f"scenario {current['id']} cannot start with THEN: {document.path}:{number}"
                )
            if previous is not None and STEP_ORDER[keyword] <= STEP_ORDER[previous]:
                raise SpecError(
                    f"scenario {current['id']} steps must follow GIVEN, WHEN, THEN order: {document.path}:{number}"
                )
            current["phase"] = keyword
        current["steps"].append((keyword, step.group(2).strip()))
        index += 1
    close()
    return scenarios, requirements
