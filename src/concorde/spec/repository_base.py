"""Shared constants, value types and path helpers of the Protocol 13 Spec tooling.

The Spec graph is loaded by ``content_repository``; this module holds what every part of the
tooling shares: identities, errors, safe file reads, realization-entry path rules and the
immutable records a loaded graph is made of.
"""

from __future__ import annotations

import hashlib
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# These helpers also remain available through the repository facade.
from .errors import SpecError as SpecError
from .errors import system_cause
from .frontmatter import parse_document as parse_document
from .schema import ContractError as ContractError
from .schema import admit as admit
from .schema import validate as validate
from .typed_data import canonical, checked_path, decode

PROFILE_VERSION = 17
PROTOCOL_VERSION = "13.0.0"
REGISTRY_SCHEMA = 3
METADATA_SCHEMA = 3
# The installed Protocol copy the configuration binds; the installer places it there.
PROTOCOL_DIR = ".concorde/protocol"
PROTOCOL_MANIFEST_PATH = PROTOCOL_DIR + "/manifest.json"
RENDERED_PROTOCOL_PREFIX = "generated/protocol/"
IDENTITY = re.compile(r"^[a-z][a-z0-9]*(?:[.-][a-z0-9-]+)*$")
HEADING = re.compile(r"^(#{1,6})[ \t]+(.*?)[ \t]*#*[ \t]*$")
# Everything under these prefixes is a project-control record or generated output, owned by the
# tool that writes it and never bound by a Module.
CONTROL_PREFIXES = (".concorde/", ".git/")
GENERATED_PREFIXES = ("generated/",)
SKIPPED_DIRECTORIES = frozenset(
    {"node_modules", "__pycache__", ".venv", "build", "dist"}
)
SKIPPED_SUFFIXES = (".pyc", ".log")
# External material is expanded and digested as text: media and archives are excluded by suffix
# so a vendored documentation or source tree costs its readable bytes, not its images.
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


def digest(value: bytes | Any) -> str:
    data = value if isinstance(value, bytes) else canonical(value).encode()
    return "sha256:" + hashlib.sha256(data).hexdigest()


def protocol_asset_path(asset_path: str) -> str:
    """Where a rendered Protocol asset lives in a project: ``generated/protocol/<name>`` is
    installed as ``.concorde/protocol/<name>``."""
    if not asset_path.startswith(RENDERED_PROTOCOL_PREFIX):
        raise SpecError(
            f"the Protocol manifest lists {asset_path}, which is not under "
            f"{RENDERED_PROTOCOL_PREFIX}",
            "protocol_mismatch",
            path=asset_path,
            reason="every Protocol asset is rendered under "
            f"{RENDERED_PROTOCOL_PREFIX} and installed under {PROTOCOL_DIR}/",
        )
    return PROTOCOL_DIR + "/" + asset_path[len(RENDERED_PROTOCOL_PREFIX) :]


def read_file(root: Path, relative: str) -> bytes:
    """Read regular files only; reject path aliases and every symlink component.

    The caller chooses the worktree ``root``; Spec tooling never redirects a path elsewhere.
    """
    path = checked_path(root, relative)
    if not path.is_file():
        state = (
            "a directory"
            if path.is_dir()
            else "missing"
            if not path.exists()
            else ("not a regular file")
        )
        raise SpecError(
            f"the required file {relative} is {state} in {root}",
            "missing_source",
            path=relative,
        )
    try:
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        with os.fdopen(descriptor, "rb") as stream:
            return stream.read()
    except OSError as error:
        raise SpecError(
            f"the required file {relative} cannot be read in {root}",
            "missing_source",
            path=relative,
            causes=[system_cause(error, path=relative)],
        ) from error


def check_input_error(check: dict, relative: str, error: Exception) -> SpecError:
    """Attribute input admission/read failures without changing their error identifier."""
    return SpecError(
        f"configured check {check['id']} (Module {check['module']}) input {relative}: {error}",
        getattr(error, "code", "invalid_spec"),
        path=relative,
        subject=check["id"],
        reason=getattr(error, "reason", None)
        or "a configured check's inputs are canonical project-relative paths of regular "
        "files or directories",
        causes=[error] if isinstance(error, SpecError) else [system_cause(error)],
    )


def check_input_members(root: Path, relative: str) -> tuple[str, ...]:
    """Required check files, using the same exclusions for preflight and revision hashing.

    Unlike pending realization entries, every explicit input must exist. Directory inputs may be
    empty, but symlinks (even excluded members) cannot alias another source.
    """
    path = checked_path(root, relative, relative)
    if not path.exists():
        raise SpecError(
            f"the check input {relative} does not exist",
            "missing_source",
            path=relative,
            reason="every declared input of a configured check must exist, because the "
            "check's result is bound to the digest of its inputs",
        )
    if path.is_file():
        return (relative,)
    if not path.is_dir():
        raise SpecError(
            f"the check input {relative} is neither a regular file nor a directory",
            "unsafe_path",
            path=relative,
        )
    members = []
    for member in sorted(path.rglob("*")):
        name = member.relative_to(root).as_posix()
        if member.is_symlink():
            raise SpecError(
                f"the check input {relative} contains the symbolic link {name}",
                "unsafe_path",
                path=name,
                reason="a symbolic link inside a check input could make the input's digest "
                "cover another file than the one the check reads",
            )
        if member.is_dir():
            continue
        if not member.is_file():
            raise SpecError(
                f"the check input {relative} contains {name}, which is not a regular file",
                "unsafe_path",
                path=name,
            )
        if "__pycache__" not in member.parts and member.suffix not in {".pyc", ".pyo"}:
            members.append(name)
    return tuple(members)


def strings(value: Any, label: str, *, nonempty: bool = False) -> tuple[str, ...]:
    if (
        not isinstance(value, list)
        or any(not isinstance(x, str) or not x.strip() for x in value)
        or len(set(value)) != len(value)
        or (nonempty and not value)
    ):
        raise SpecError(
            f"{label} must be a {'nonempty ' if nonempty else ''}array of distinct nonblank "
            f"strings, not {value!r}"[:300],
            "invalid_spec",
            label,
        )
    return tuple(value)


def identifier(value: Any) -> str:
    if not isinstance(value, str) or not IDENTITY.fullmatch(value):
        raise SpecError(
            f"{value!r} is not a stable identity",
            "invalid_spec",
            reason="a stable identity is a kind prefix and lowercase dotted words, such as "
            "module.payments or scenario.payments.retry",
        )
    return value


def is_identity(value: Any) -> bool:
    return isinstance(value, str) and bool(IDENTITY.fullmatch(value))


def is_directory_entry(entry: str) -> bool:
    """A realization entry with a trailing slash binds every regular file below the directory."""
    return entry.endswith("/")


def entry_base(entry: str) -> str:
    return entry[:-1] if entry.endswith("/") else entry


def control_path(path: str) -> bool:
    """Project-control records: everything under ``.concorde/`` (and the version control store)."""
    return (path if path.endswith("/") else path + "/").startswith(CONTROL_PREFIXES)


def covers(entry: str, path: str) -> bool:
    """Whether an entry covers the given concrete path (no exclusion rule applied)."""
    return path.startswith(entry) if is_directory_entry(entry) else path == entry


def overlaps(first: str, second: str) -> bool:
    """Whether two path literals (files or ``/`` directories) share any path."""
    return (
        covers(first, entry_base(second))
        or covers(second, entry_base(first))
        or (first == second)
    )


def most_specific(entries, path: str) -> str | None:
    """The entry that owns a covered path: an exact file first, then the longest directory."""
    matches = [entry for entry in entries if covers(entry, path)]
    if not matches:
        return None
    return max(matches, key=lambda entry: (not is_directory_entry(entry), len(entry)))


def skipped_path(relative: str) -> bool:
    """The deterministic exclusion rule applied below a bound directory.

    Directories named in ``SKIPPED_DIRECTORIES``, every dot-directory and dot-file, and files with
    a suffix in ``SKIPPED_SUFFIXES`` are never bound by a directory entry. Bind such a file with
    an exact entry when it is part of a realization.
    """
    return any(
        part in SKIPPED_DIRECTORIES or part.startswith(".")
        for part in relative.split("/")
    ) or relative.endswith(SKIPPED_SUFFIXES)


def bound_by(entry: str, path: str) -> bool:
    """Whether one realization entry binds a concrete file path, applying directory exclusions."""
    return covers(entry, path) and (
        not is_directory_entry(entry) or not skipped_path(path[len(entry) :])
    )


def entry_exists(root: Path, entry: str) -> bool:
    try:
        candidate = checked_path(root, entry_base(entry))
    except ValueError:
        return False
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
class Module:
    """One registered Module in the shape every consumer reads.

    Every field is derived from the Module's entry declarations: ``documents`` from ``owns``,
    ``parent`` from the ``contains`` that names it, ``uses`` from its ``uses`` targets, ``files``
    from its realizations' entries, ``references`` from its ``includes`` and ``checks`` from the
    project configuration.
    """

    id: str
    kind: str
    title: str
    documents: tuple[str, ...]
    parent: str | None
    uses: tuple[str, ...]
    files: tuple[str, ...]
    checks: tuple[str, ...]
    references: tuple[tuple[str, str], ...] = ()
    entry: str = ""

    @property
    def sources(self) -> tuple[str, ...]:
        return tuple(
            member for path in self.documents for member in (path, path + ".json")
        )

    @property
    def primary_document(self) -> str:
        """The Module's entry reading path."""
        if self.entry:
            return self.entry
        return next(path for path in self.documents if Path(path).name == "module.md")

    def descriptor(self) -> dict:
        """The registration record carried in context resolutions."""
        return {
            "id": self.id,
            "kind": self.kind,
            "title": self.title,
            "documents": list(self.documents),
            "references": [
                reference_record(kind, value) for kind, value in self.references
            ],
            "parent": self.parent,
            "uses": list(self.uses),
            "files": list(self.files),
            "checks": list(self.checks),
        }


def reference_record(kind: str, value: str) -> dict:
    return (
        {"kind": "external", "path": value}
        if kind == "external"
        else {
            "kind": kind,
            "id": value,
        }
    )


@dataclass(frozen=True)
class SpecDocument:
    path: str
    content: str
    digest: str
    document_id: str
    owner: str
    metadata: dict
    body: str

    @property
    def role(self) -> str | None:
        document = (
            self.metadata.get("document") if isinstance(self.metadata, dict) else None
        )
        return document.get("role") if isinstance(document, dict) else None


@dataclass(frozen=True)
class SpecContext:
    """A resolved ``SpecContext`` with its source records, canonical and immutable.

    Decoding cannot mutate the repository snapshot. ``paths`` is the Protocol set itself: both
    members of every selected document; ``value["sources"]`` carries each member's identity,
    digest and the relations that selected it.
    """

    serialized: str

    @property
    def value(self) -> dict:
        return decode(self.serialized)

    @property
    def paths(self) -> tuple[str, ...]:
        return tuple(sorted(source["path"] for source in self.value["sources"]))

    def __getattr__(self, name):
        value = self.value
        if name in value:
            return value[name]
        raise AttributeError(name)


@dataclass(frozen=True)
class Requirement:
    """One Module-wide obligation: a heading section whose statement holds one SHALL sentence."""

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
class Concept:
    """One named meaning, declared in a module document's metadata and defined by a table row."""

    id: str
    title: str
    owner: str
    document: str
    meaning: str
    definition: str | None
    retired: dict | None = None
    external_conflict: str | None = None


@dataclass(frozen=True)
class Realization:
    """A binding of exact paths or directory prefixes to the owning Module."""

    id: str
    title: str
    owner: str
    document: str
    meaning: str
    entries: tuple[str, ...]
    pending: tuple[str, ...]

    @property
    def files(self) -> tuple[str, ...]:
        return self.entries


@dataclass(frozen=True)
class ModuleDefinitions:
    """Every node a Module's own documents define."""

    scenarios: tuple[Scenario, ...]
    requirements: tuple[Requirement, ...]
    concepts: tuple[Concept, ...]
    realizations: tuple[Realization, ...]
    contracts: tuple[dict, ...] = ()

    @property
    def anchors(self) -> dict[str, str]:
        """Every node identity of the Module mapped to the document that defines it."""
        result = {
            item.id: item.document
            for group in (
                self.scenarios,
                self.requirements,
                self.concepts,
                self.realizations,
            )
            for item in group
        }
        result.update({item["id"]: item["source"] for item in self.contracts})
        return result
