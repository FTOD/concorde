"""Safe deterministic discovery for Concorde Source Profile 7."""

from __future__ import annotations

import json
import posixpath
import re
from collections import defaultdict
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

from ..diagnostics import digest_sources
from ..frontmatter import FrontMatterError, parse_document
from ..reflections.reflections import BUCKETS, index_path, reflection_number
from ..model import (
    MODULE_DIAGRAMS_DIRECTORY,
    ArchitectureEntity,
    ArchitecturePackage,
    EntityRelationship,
    Feature,
    FeatureInterface,
    FeatureRelation,
    Interaction,
    Module,
    SourceDocument,
)


class RepositoryError(ValueError):
    pass


FEATURE_BASENAME = re.compile(r"^\d{3,}-[a-z0-9]+(?:-[a-z0-9]+)*$")
FEATURE_ID = re.compile(r"^feature\.[a-z0-9]+(?:[.-][a-z0-9]+)*$")
MODULE_DIRECTORY = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
STABLE_ID = re.compile(r"(?:module|feature|entity|interaction|interface|contract)\.[a-z0-9][a-z0-9.-]*")
DIAGRAM_KINDS = frozenset({"architecture", "workflow", "sequence", "dataflow", "lifecycle"})
PROFILE_VERSION = 7

_TABLE_SEPARATOR = re.compile(r"^:?-{3,}:?$")
_BOLD_FIELD = re.compile(r"^\s*(?:[-*]\s+)?\*\*([^*]+)\*\*\s*:\s*(.*)$")


def safe_relative_path(value: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise RepositoryError("path must be a non-empty project-relative POSIX path")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise RepositoryError(f"unsafe project-relative path: {value}")
    if len(path.parts[0]) >= 2 and path.parts[0][1] == ":":
        raise RepositoryError(f"absolute drive path is not permitted: {value}")
    return path.as_posix()


def _module_local_parts(relative: str, specification_root: str) -> tuple[str, ...]:
    path = PurePosixPath(safe_relative_path(relative))
    root = PurePosixPath(safe_relative_path(specification_root))
    try:
        return path.relative_to(root).parts
    except ValueError as error:
        raise RepositoryError(f"source escapes configured specification root: {relative}") from error


def classify_module_architecture_path(relative: str, specification_root: str) -> str:
    """Return the canonical module directory for one ``architecture.md`` path."""
    parts = _module_local_parts(relative, specification_root)
    if not parts or parts[-1] != "architecture.md":
        raise RepositoryError(f"module source must be architecture.md: {relative}")
    prefix = parts[:-1]
    if prefix:
        if len(prefix) % 2 or any(prefix[index] != "modules" for index in range(0, len(prefix), 2)):
            raise RepositoryError(
                f"child module must be recursively placed at modules/<name>/architecture.md: {relative}"
            )
        if any(not MODULE_DIRECTORY.fullmatch(prefix[index]) for index in range(1, len(prefix), 2)):
            raise RepositoryError(f"module directory must use a lowercase kebab-case name: {relative}")
    return (PurePosixPath(specification_root).joinpath(*prefix)).as_posix()


def classify_feature_path(relative: str, specification_root: str) -> tuple[str, str]:
    """Classify a direct Profile 7 feature and return ``("feature", module-directory)``."""
    parts = _module_local_parts(relative, specification_root)
    feature_indexes = [index for index, part in enumerate(parts) if part == "features"]
    if len(feature_indexes) != 1:
        raise RepositoryError(f"feature file has invalid features/ placement: {relative}")
    index = feature_indexes[0]
    if len(parts) != index + 2:
        raise RepositoryError(
            f"feature must be one direct file at <module>/features/<NNN-name>.md: {relative}"
        )
    filename = parts[index + 1]
    path = PurePosixPath(filename)
    if path.suffix != ".md" or not FEATURE_BASENAME.fullmatch(path.stem):
        raise RepositoryError(f"feature filename must use <NNN>-<name>.md: {relative}")
    prefix = parts[:index]
    if prefix:
        if len(prefix) % 2 or any(prefix[offset] != "modules" for offset in range(0, len(prefix), 2)):
            raise RepositoryError(f"feature provider is not a canonical recursive module: {relative}")
        if any(not MODULE_DIRECTORY.fullmatch(prefix[offset]) for offset in range(1, len(prefix), 2)):
            raise RepositoryError(f"module directory must use a lowercase kebab-case name: {relative}")
    module_directory = PurePosixPath(specification_root).joinpath(*prefix).as_posix()
    return "feature", module_directory


def attempt_directory_for_feature_id(feature_id: str) -> str:
    """Derive one confined project-control attempt path from an exact stable feature ID."""
    if not isinstance(feature_id, str) or not FEATURE_ID.fullmatch(feature_id):
        raise RepositoryError(
            "attempt identity must be one lowercase qualified feature.* stable ID"
        )
    return (PurePosixPath(".concorde") / "attempts" / feature_id).as_posix()


def _section(body: str, heading: str) -> str:
    match = re.search(
        rf"^## {re.escape(heading)}\s*$\n(.*?)(?=^## |\Z)",
        body,
        re.MULTILINE | re.DOTALL,
    )
    return match.group(1).strip() if match else ""


def _table_rows(section: str) -> tuple[tuple[str, ...], list[tuple[str, ...]]]:
    lines = [line.strip() for line in section.splitlines() if line.strip()]
    for index in range(len(lines) - 1):
        header = _split_table_row(lines[index])
        separator = _split_table_row(lines[index + 1])
        if not header or not separator or len(header) != len(separator):
            continue
        if not all(_TABLE_SEPARATOR.fullmatch(cell.replace(" ", "")) for cell in separator):
            continue
        rows: list[tuple[str, ...]] = []
        for line in lines[index + 2 :]:
            cells = _split_table_row(line)
            if cells is None:
                break
            if len(cells) == len(header):
                rows.append(cells)
        return tuple(cell.strip() for cell in header), rows
    return (), []


def _split_table_row(line: str) -> tuple[str, ...] | None:
    if not line.startswith("|") or not line.endswith("|"):
        return None
    cells = re.split(r"(?<!\\)\|", line[1:-1])
    return tuple(cell.strip().replace(r"\|", "|") for cell in cells)


def _plain(value: str) -> str:
    return re.sub(r"^`|`$", "", value.strip())


def _values(value: str) -> tuple[str, ...]:
    if not value or value.strip().lower() in {"none", "n/a", "[]"}:
        return ()
    backticked = re.findall(r"`([^`]+)`", value)
    if backticked:
        return tuple(dict.fromkeys(item.strip() for item in backticked if item.strip()))
    pieces = re.split(r"(?:<br\s*/?>|[,;]|\n|\s+→\s+)", value, flags=re.IGNORECASE)
    return tuple(dict.fromkeys(item.strip(" -*0123456789.\t") for item in pieces if item.strip(" -*0123456789.\t")))


def _steps(value: str) -> tuple[str, ...]:
    pieces = re.split(r"(?:<br\s*/?>|\n|\s+→\s+)", value, flags=re.IGNORECASE)
    return tuple(item.strip(" -*0123456789.\t") for item in pieces if item.strip(" -*0123456789.\t"))


def _h3_blocks(section: str) -> list[tuple[str, str]]:
    matches = list(re.finditer(r"^###\s+(.+?)\s*$", section, re.MULTILINE))
    return [
        (match.group(1).strip(), section[match.end() : matches[index + 1].start() if index + 1 < len(matches) else len(section)].strip())
        for index, match in enumerate(matches)
    ]


def _fields(block: str) -> dict[str, str]:
    result: dict[str, list[str]] = {}
    current: str | None = None
    for line in block.splitlines():
        match = _BOLD_FIELD.match(line)
        if match:
            current = re.sub(r"[^a-z0-9]+", "_", match.group(1).casefold()).strip("_")
            result.setdefault(current, [])
            if match.group(2).strip():
                result[current].append(match.group(2).strip())
        elif current is not None and line.strip():
            result[current].append(line.strip())
    return {key: "\n".join(value).strip() for key, value in result.items()}


def _field(fields: dict[str, str], *names: str) -> str:
    return next((fields[name] for name in names if fields.get(name)), "")


def _stable_id(text: str, prefix: str) -> str | None:
    for candidate in STABLE_ID.findall(text):
        if candidate.startswith(prefix + ".") or prefix == "interface" and candidate.startswith("contract."):
            return candidate
    return None


def _parse_entities(source: SourceDocument) -> list[ArchitectureEntity]:
    headers, rows = _table_rows(_section(source.body, "Entities"))
    index = {re.sub(r"[^a-z0-9]+", "_", item.casefold()).strip("_"): offset for offset, item in enumerate(headers)}
    id_index = index.get("entity_id", index.get("entity"))
    type_index = index.get("type")
    definition_index = index.get("definition")
    locator_index = index.get("locator")
    roles_index = index.get("roles")
    if None in {id_index, type_index, definition_index, locator_index}:
        return []
    return [
        ArchitectureEntity(
            identifier=_plain(row[id_index]),
            entity_type=_plain(row[type_index]),
            definition=row[definition_index].strip(),
            locator=_plain(row[locator_index]),
            owner=source.identifier,
            roles=_values(row[roles_index]) if roles_index is not None else (),
            source=source.path,
        )
        for row in rows
    ]


def _parse_relationships(source: SourceDocument) -> list[EntityRelationship]:
    headers, rows = _table_rows(_section(source.body, "Relationships"))
    index = {re.sub(r"[^a-z0-9]+", "_", item.casefold()).strip("_"): offset for offset, item in enumerate(headers)}
    required = [index.get(name) for name in ("source", "predicate", "target", "description")]
    if any(item is None for item in required):
        return []
    source_index, predicate_index, target_index, description_index = required
    interface_index = index.get("interface")
    return [
        EntityRelationship(
            source_entity=_plain(row[source_index]),
            predicate=_plain(row[predicate_index]),
            target_entity=_plain(row[target_index]),
            description=row[description_index].strip(),
            owner=source.identifier,
            interface=(
                _plain(row[interface_index])
                if interface_index is not None and _plain(row[interface_index]).lower() not in {"", "none", "n/a"}
                else None
            ),
            source=source.path,
        )
        for row in rows
    ]


def _parse_interactions(source: SourceDocument) -> list[Interaction]:
    section = _section(source.body, "Interactions")
    headers, rows = _table_rows(section)
    index = {re.sub(r"[^a-z0-9]+", "_", item.casefold()).strip("_"): offset for offset, item in enumerate(headers)}
    id_index = index.get("interaction_id", index.get("interaction"))
    if id_index is not None and all(name in index for name in ("trigger", "steps", "result")):
        return [
            Interaction(
                identifier=_plain(row[id_index]),
                trigger=row[index["trigger"]].strip(),
                steps=_steps(row[index["steps"]]),
                result=row[index["result"]].strip(),
                owner=source.identifier,
                interfaces=_values(row[index["interfaces"]]) if "interfaces" in index else (),
                source=source.path,
            )
            for row in rows
        ]
    interactions: list[Interaction] = []
    for heading, block in _h3_blocks(section):
        identifier = _stable_id(heading, "interaction")
        if not identifier:
            continue
        fields = _fields(block)
        interactions.append(
            Interaction(
                identifier=identifier,
                trigger=_field(fields, "trigger"),
                steps=_steps(_field(fields, "steps")),
                result=_field(fields, "result"),
                owner=source.identifier,
                interfaces=_values(_field(fields, "interfaces", "interface")),
                source=source.path,
            )
        )
    return interactions


def _parse_related_features(value: Any) -> tuple[FeatureRelation, ...]:
    """Parse ``related_features`` entries into typed relations.

    A plain string means ``relates_to``; a mapping with exactly the string keys ``id`` and
    ``relation`` carries its own declared relation. Anything else is skipped here and left for
    CONCORDE-FEATURE-003 to report.
    """
    if not isinstance(value, list):
        return ()
    relations: list[FeatureRelation] = []
    for item in value:
        if isinstance(item, str):
            relations.append(FeatureRelation(target=item, relation="relates_to"))
        elif (
            isinstance(item, dict)
            and set(item) == {"id", "relation"}
            and isinstance(item.get("id"), str)
            and isinstance(item.get("relation"), str)
        ):
            relations.append(FeatureRelation(target=item["id"], relation=item["relation"]))
    return tuple(relations)


def _parse_zoom(source: SourceDocument) -> tuple[str, ...]:
    headers, rows = _table_rows(_section(source.body, "Architecture Zoom"))
    index = {re.sub(r"[^a-z0-9]+", "_", item.casefold()).strip("_"): offset for offset, item in enumerate(headers)}
    entity_index = index.get("entity_id", index.get("entity"))
    if entity_index is None:
        return ()
    return tuple(_plain(row[entity_index]) for row in rows)


def architecture_zoom_rows(source: SourceDocument) -> list[dict[str, str]]:
    """Expose normalized zoom rows to validation without reparsing in every rule module."""
    headers, rows = _table_rows(_section(source.body, "Architecture Zoom"))
    keys = [re.sub(r"[^a-z0-9]+", "_", item.casefold()).strip("_") for item in headers]
    return [{key: _plain(value) for key, value in zip(keys, row)} for row in rows]


def _parse_interfaces(source: SourceDocument) -> list[FeatureInterface]:
    result: list[FeatureInterface] = []
    interface_sets = source.metadata.get("interfaces") if isinstance(source.metadata.get("interfaces"), dict) else {}
    provided = set(interface_sets.get("provided", [])) if isinstance(interface_sets.get("provided"), list) else set()
    required = set(interface_sets.get("required", [])) if isinstance(interface_sets.get("required"), list) else set()
    for heading, block in _h3_blocks(_section(source.body, "Interfaces")):
        identifier = _stable_id(heading, "interface")
        if not identifier:
            continue
        fields = _fields(block)
        result.append(
            FeatureInterface(
                identifier=identifier,
                owner=source.identifier,
                consumer=_field(fields, "consumer", "consumers"),
                direction=_field(fields, "direction"),
                entry_points=_values(_field(fields, "entry_points", "entry_point")),
                inputs=_field(fields, "inputs", "input"),
                outputs=_field(fields, "outputs", "output"),
                obligations=_field(fields, "obligations", "provider_and_consumer_obligations"),
                failures=_field(fields, "failures", "failure_behavior", "failure_semantics"),
                compatibility=_field(fields, "compatibility"),
                implementing_entities=_values(
                    _field(fields, "implementing_entities", "implementing_entity", "implementation_entities")
                ),
                example=_field(fields, "example", "examples") or None,
                role="provided" if identifier in provided else "required" if identifier in required else "undeclared",
                provider=_plain(_field(fields, "provider")) or None,
                source=source.path,
            )
        )
    return result


def _checked_diagram(relative: str, value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise RepositoryError(f"{relative}: an architecture diagram must be a JSON object")
    if value.get("diagram_type") not in DIAGRAM_KINDS:
        raise RepositoryError(f"{relative}: diagram_type must be one of {', '.join(sorted(DIAGRAM_KINDS))}")
    meta = value.get("meta")
    if not isinstance(meta, dict) or not isinstance(meta.get("title"), str) or not meta["title"].strip():
        raise RepositoryError(f"{relative}: diagram meta.title is required")
    output = meta.get("output")
    if output is not None:
        if not isinstance(output, str) or not output:
            raise RepositoryError(f"{relative}: diagram meta.output must be a non-empty string when present")
        resolved = posixpath.normpath((PurePosixPath(relative).parent / output).as_posix())
        safe_relative_path(resolved)
    return value


class ProjectRepository:
    def __init__(self, project_root: str | Path):
        self.project_root = Path(project_root).resolve()

    def resolve(self, relative: str) -> Path:
        safe = safe_relative_path(relative)
        candidate = self.project_root / safe
        resolved = candidate.resolve(strict=False)
        try:
            resolved.relative_to(self.project_root)
        except ValueError as error:
            raise RepositoryError(f"path escapes project root: {relative}") from error
        return candidate

    def load_config(self) -> dict[str, Any]:
        path = self.resolve(".concorde/config.json")
        if path.is_symlink() or path.parent.is_symlink():
            raise RepositoryError(".concorde/config.json: project control configuration may not use symlinks")
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise RepositoryError(f"cannot read .concorde/config.json: {error}") from error
        if value.get("profile_version") != PROFILE_VERSION:
            raise RepositoryError(f"unsupported Concorde source profile; expected profile_version {PROFILE_VERSION}")
        specification_root = value.get("specification_root")
        if not isinstance(specification_root, str):
            raise RepositoryError("specification_root is required")
        value["specification_root"] = safe_relative_path(specification_root)
        if not isinstance(value.get("root_module_id"), str) or not value["root_module_id"]:
            raise RepositoryError("root_module_id is required")
        return value

    def _checked_source_path(self, path: Path, root: Path) -> str:
        relative = path.relative_to(self.project_root).as_posix()
        current = path
        while current != root.parent:
            if current.is_symlink():
                raise RepositoryError(f"source path may not contain a symlink: {relative}")
            if current == root:
                break
            current = current.parent
        return relative

    def _markdown_paths(self, specification_root: str) -> list[Path]:
        root = self.resolve(specification_root)
        if not root.is_dir() or root.is_symlink():
            raise RepositoryError(f"specification root does not exist or is unsafe: {specification_root}")
        architecture = root / "architecture.md"
        if not architecture.is_file() or architecture.is_symlink():
            raise RepositoryError(f"root module architecture is missing: {specification_root}/architecture.md")
        candidates: set[Path] = set()
        for path in sorted(root.rglob("architecture.md")):
            relative = self._checked_source_path(path, root)
            try:
                classify_module_architecture_path(relative, specification_root)
            except RepositoryError:
                if path == architecture:
                    raise
                continue
            candidates.add(path)
        for path in sorted(root.rglob("*.md")):
            if path.parent.name != "features" or path.is_symlink():
                continue
            try:
                relative = self._checked_source_path(path, root)
                classify_feature_path(relative, specification_root)
            except RepositoryError:
                continue
            candidates.add(path)
        return sorted(candidates, key=lambda item: item.relative_to(self.project_root).as_posix())

    def _load_diagrams(self, modules: Iterable[SourceDocument]) -> dict[str, dict[str, Any]]:
        diagrams: dict[str, dict[str, Any]] = {}
        for module in modules:
            module_dir = PurePosixPath(module.path).parent
            directory = self.resolve((module_dir / MODULE_DIAGRAMS_DIRECTORY).as_posix())
            if directory.is_symlink():
                raise RepositoryError(f"{module_dir}/diagrams: the module diagram directory may not be a symlink")
            declared: set[str] = set()
            declarations = module.metadata.get("diagrams", [])
            if not isinstance(declarations, list) or not all(isinstance(item, dict) for item in declarations):
                raise RepositoryError(f"{module.path}: diagrams must be a list of mappings")
            for declaration in declarations:
                raw = declaration.get("source")
                if not isinstance(raw, str):
                    raise RepositoryError(f"{module.path}: every diagram declaration requires source")
                safe = safe_relative_path(raw)
                candidate = PurePosixPath(safe)
                if candidate.parent != module_dir / MODULE_DIAGRAMS_DIRECTORY:
                    candidate = module_dir / candidate
                if candidate.parent != module_dir / MODULE_DIAGRAMS_DIRECTORY:
                    raise RepositoryError(f"{module.path}: diagram sources must be directly below the module's diagrams/")
                declared.add(candidate.as_posix())
                kind = declaration.get("kind")
                if kind is not None and kind not in DIAGRAM_KINDS:
                    raise RepositoryError(f"{module.path}: unsupported diagram kind '{kind}'")
            candidates = set(declared)
            if directory.is_dir():
                candidates.update(path.relative_to(self.project_root).as_posix() for path in directory.glob("*.json"))
            for relative in sorted(candidates):
                path = self.resolve(relative)
                if path.is_symlink() or not path.is_file():
                    raise RepositoryError(f"{relative}: declared architecture diagram is missing or unsafe")
                try:
                    value = json.loads(path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError) as error:
                    raise RepositoryError(f"{relative}: invalid architecture diagram JSON: {error}") from error
                diagrams[relative] = _checked_diagram(relative, value)
        return diagrams

    def load(self) -> ArchitecturePackage:
        config = self.load_config()
        specification_root = config["specification_root"]
        sources: list[SourceDocument] = []
        for path in self._markdown_paths(specification_root):
            relative = path.relative_to(self.project_root).as_posix()
            try:
                metadata, body = parse_document(path.read_text(encoding="utf-8"), relative)
            except (OSError, UnicodeError, FrontMatterError) as error:
                raise RepositoryError(str(error)) from error
            kind = metadata.get("kind")
            identifier = metadata.get("id")
            expected_kind = "module" if path.name == "architecture.md" else "feature"
            if kind != expected_kind:
                raise RepositoryError(f"{relative}: kind must be {expected_kind}")
            if not isinstance(identifier, str) or not identifier:
                raise RepositoryError(f"{relative}: missing stable id")
            sources.append(SourceDocument(relative, kind, identifier, metadata, body))

        diagrams = self._load_diagrams(source for source in sources if source.kind == "module")
        by_id: dict[str, list[SourceDocument]] = defaultdict(list)
        for source in sources:
            by_id[source.identifier].append(source)

        entity_lists: dict[str, list[ArchitectureEntity]] = defaultdict(list)
        interaction_lists: dict[str, list[Interaction]] = defaultdict(list)
        interface_lists: dict[str, list[FeatureInterface]] = defaultdict(list)
        required_interface_declarations: list[FeatureInterface] = []
        relationships: list[EntityRelationship] = []
        modules: dict[str, Module] = {}
        features: dict[str, Feature] = {}
        for source in sources:
            if source.kind == "module":
                entities = _parse_entities(source)
                relations = _parse_relationships(source)
                interactions = _parse_interactions(source)
                for entity in entities:
                    entity_lists[entity.identifier].append(entity)
                for interaction in interactions:
                    interaction_lists[interaction.identifier].append(interaction)
                relationships.extend(relations)
                modules.setdefault(
                    source.identifier,
                    Module(
                        identifier=source.identifier,
                        parent=source.metadata.get("parent") if isinstance(source.metadata.get("parent"), str) else None,
                        path=source.path,
                        responsibility=_section(source.body, "Responsibility"),
                        boundary=_section(source.body, "Boundary"),
                        modules=tuple(source.metadata.get("modules", [])) if isinstance(source.metadata.get("modules"), list) else (),
                        features=tuple(source.metadata.get("features", [])) if isinstance(source.metadata.get("features"), list) else (),
                        entities=tuple(entity.identifier for entity in entities),
                        relationships=tuple(relations),
                        interactions=tuple(interaction.identifier for interaction in interactions),
                        diagrams=tuple(sorted(path for path in diagrams if PurePosixPath(path).parent == PurePosixPath(source.path).parent / "diagrams")),
                    ),
                )
            else:
                interfaces = _parse_interfaces(source)
                for interface in interfaces:
                    if interface.role == "provided":
                        interface_lists[interface.identifier].append(interface)
                    elif interface.role == "required":
                        required_interface_declarations.append(interface)
                interface_sets = source.metadata.get("interfaces") if isinstance(source.metadata.get("interfaces"), dict) else {}
                relations = _parse_related_features(source.metadata.get("related_features", []))
                features.setdefault(
                    source.identifier,
                    Feature(
                        identifier=source.identifier,
                        module=str(source.metadata.get("module", "")),
                        path=source.path,
                        outcome=_section(source.body, "Outcome and Scope") or _section(source.body, "Outcome"),
                        related_features=tuple(relation.target for relation in relations),
                        provided_interfaces=tuple(interface_sets.get("provided", [])) if isinstance(interface_sets.get("provided"), list) else (),
                        required_interfaces=tuple(interface_sets.get("required", [])) if isinstance(interface_sets.get("required"), list) else (),
                        architecture_zoom=_parse_zoom(source),
                        relations=relations,
                    ),
                )

        auxiliary: dict[str, str] = {}
        artifacts = [source.path for source in sources] + list(diagrams)
        reflection_directory = self.project_root / ".concorde" / "reflections"
        if reflection_directory.is_symlink():
            raise RepositoryError(".concorde/reflections: project reflection state may not be a symlink")
        if reflection_directory.exists() and not reflection_directory.is_dir():
            raise RepositoryError(".concorde/reflections: project reflection state must be a real directory")
        reflection_index = self.project_root / index_path()
        if reflection_index.is_symlink():
            raise RepositoryError(f"{index_path()}: the reflection allocation index may not be a symlink")
        if reflection_index.exists() and not reflection_index.is_file():
            raise RepositoryError(f"{index_path()}: the reflection allocation index must be one real file")
        if reflection_index.is_file():
            relative = reflection_index.relative_to(self.project_root).as_posix()
            auxiliary[relative] = reflection_index.read_text(encoding="utf-8")
            artifacts.append(relative)
        if reflection_directory.is_dir():
            # Bucketed documents are canonical; flat documents directly under the collection root
            # are still loaded so validation can report them as misplaced.
            candidates = list(reflection_directory.glob("R-*.md"))
            for bucket in BUCKETS:
                bucket_directory = reflection_directory / bucket
                if bucket_directory.is_symlink():
                    raise RepositoryError(
                        f".concorde/reflections/{bucket}: reflection buckets may not be symlinks"
                    )
                if bucket_directory.exists() and not bucket_directory.is_dir():
                    raise RepositoryError(
                        f".concorde/reflections/{bucket}: reflection buckets must be real directories"
                    )
                if bucket_directory.is_dir():
                    candidates.extend(bucket_directory.glob("R-*.md"))
            for reflection in sorted(candidates):
                if reflection.is_symlink():
                    raise RepositoryError(
                        f"{reflection.relative_to(self.project_root).as_posix()}: reflection documents may not be symlinks"
                    )
                if not reflection.is_file():
                    raise RepositoryError(
                        f"{reflection.relative_to(self.project_root).as_posix()}: reflection documents must be real files"
                    )
                if reflection_number(reflection.stem) is None:
                    continue
                relative = reflection.relative_to(self.project_root).as_posix()
                auxiliary[relative] = reflection.read_text(encoding="utf-8")
                artifacts.append(relative)
        attempts_root = self.project_root / ".concorde" / "attempts"
        if attempts_root.is_symlink():
            raise RepositoryError(".concorde/attempts: the project attempt root may not be a symlink")
        for feature in (source for source in sources if source.kind == "feature"):
            if not FEATURE_ID.fullmatch(feature.identifier):
                continue
            attempt = self.project_root / attempt_directory_for_feature_id(feature.identifier)
            if not attempt.is_dir() or attempt.is_symlink():
                continue
            for path in sorted(attempt.rglob("*")):
                if path.is_symlink():
                    continue
                if path.is_file():
                    relative = path.relative_to(self.project_root).as_posix()
                    auxiliary[relative] = path.read_text(encoding="utf-8", errors="replace")

        receipts: dict[str, Any] = {}
        receipts_root = self.project_root / ".concorde" / "receipts"
        if receipts_root.is_dir() and not receipts_root.is_symlink():
            for path in sorted(receipts_root.glob("*.json")):
                relative = path.relative_to(self.project_root).as_posix()
                try:
                    value = json.loads(path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError) as error:
                    raise RepositoryError(f"{relative}: invalid freshness receipt JSON: {error}") from error
                if not isinstance(value, dict):
                    raise RepositoryError(f"{relative}: freshness receipt must be a JSON object")
                receipts[relative] = value

        entity_declarations = {key: tuple(value) for key, value in sorted(entity_lists.items())}
        interaction_declarations = {key: tuple(value) for key, value in sorted(interaction_lists.items())}
        interface_declarations = {key: tuple(value) for key, value in sorted(interface_lists.items())}
        return ArchitecturePackage(
            project_root=self.project_root,
            specification_root=specification_root,
            root_module_id=config["root_module_id"],
            profile_version=config["profile_version"],
            sources=tuple(sources),
            views=diagrams,
            diagrams=diagrams,
            by_id={key: tuple(value) for key, value in sorted(by_id.items())},
            source_digest=digest_sources(self.project_root, artifacts),
            auxiliary=auxiliary,
            receipts=receipts,
            modules=modules,
            features=features,
            entities={key: values[0] for key, values in entity_declarations.items()},
            entities_by_id=entity_declarations,
            relationships=tuple(relationships),
            interactions={key: values[0] for key, values in interaction_declarations.items()},
            interactions_by_id=interaction_declarations,
            interfaces={key: values[0] for key, values in interface_declarations.items()},
            interfaces_by_id=interface_declarations,
            required_interface_declarations=tuple(required_interface_declarations),
        )

    def stage_and_promote(self, files: dict[str, str]) -> list[str]:
        """Write a complete initialization proposal with rollback on promotion failure."""
        resolved = {safe_relative_path(path): self.resolve(path) for path in files}
        conflicts = [path for path, target in resolved.items() if target.exists()]
        if conflicts:
            raise RepositoryError("target files already exist: " + ", ".join(sorted(conflicts)))
        staged: list[tuple[Path, Path]] = []
        promoted: list[Path] = []
        try:
            for relative, target in sorted(resolved.items()):
                target.parent.mkdir(parents=True, exist_ok=True)
                temporary = target.with_name(f".{target.name}.concorde-stage")
                temporary.write_text(files[relative], encoding="utf-8", newline="\n")
                staged.append((temporary, target))
            for temporary, target in staged:
                temporary.replace(target)
                promoted.append(target)
        except OSError:
            for temporary, _ in staged:
                temporary.unlink(missing_ok=True)
            for target in reversed(promoted):
                target.unlink(missing_ok=True)
            raise
        return sorted(resolved)
