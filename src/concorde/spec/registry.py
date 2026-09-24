"""Project-level regeneration of the registry's mirrored fields from the Module entries.

The registry lists which Modules exist and mirrors each entry's ``module`` block. A task bound to
one Module may change its own block but never the registry, so the mirror can go stale; this step
reconciles it: every field of the entry's ``module`` block, the title included. It never adds or
removes a Module and never changes a record's ``id`` or ``entry``: those are deliberate registry
edits.
"""

from __future__ import annotations

import json
from pathlib import Path

from .changes import apply_files, file_change
from .content_model import MODULE_FIELDS, metadata_path
from .model import Finding, ToolResult
from .errors import system_cause
from .repository_base import SpecError, decode, read_file

MIRRORED = MODULE_FIELDS
RECORD_FIELDS = (
    "id",
    "title",
    "entry",
    *(name for name in MIRRORED if name != "title"),
)


def _registry_path(root: Path) -> str:
    config = decode(read_file(root, ".concorde/config.json").decode("utf-8"))
    if not isinstance(config, dict) or not isinstance(config.get("registry"), str):
        found = config.get("registry") if isinstance(config, dict) else config
        raise SpecError(
            f"the configuration names no registry path; its registry field is {found!r}",
            "invalid_spec",
            "/registry",
            path=".concorde/config.json",
            reason="the configuration's registry field is the project-relative path of the "
            "Spec registry",
        )
    return config["registry"]


def mirrored_registry(
    root: Path, registry_path: str | None = None
) -> tuple[dict, list[str]]:
    """The regenerated registry value and the identities of the records that differed."""
    root = Path(root)
    registry_path = registry_path or _registry_path(root)
    registry = decode(read_file(root, registry_path).decode("utf-8"))
    if (
        not isinstance(registry, dict)
        or set(registry) != {"schema_version", "modules"}
        or registry.get("schema_version") != 3
        or not isinstance(registry.get("modules"), list)
    ):
        shape = (
            f"its fields are {sorted(registry)} and schema_version is "
            f"{registry.get('schema_version')!r}"
            if isinstance(registry, dict)
            else f"it is a JSON {type(registry).__name__}"
        )
        raise SpecError(
            'the registry must be {"schema_version": 3, "modules": [...]}, but '
            + shape,
            "unsupported_profile",
            path=registry_path,
        )
    records, stale = [], []
    for record in registry["modules"]:
        if (
            not isinstance(record, dict)
            or not {"id", "title", "entry"} <= record.keys()
        ):
            raise SpecError(
                f"registry record needs id, title and entry: {record!r}"[:300],
                "invalid_spec",
                path=registry_path,
                reason="every registry record names its Module's id, title and entry",
            )
        entry = record["entry"]
        try:
            metadata = decode(read_file(root, metadata_path(entry)).decode("utf-8"))
        except (SpecError, ValueError, OSError, UnicodeError) as error:
            raise SpecError(
                f"the metadata of {record['id']}'s entry cannot be read: {error}",
                "missing_source",
                path=metadata_path(entry),
                subject=record["id"],
                causes=[error if isinstance(error, SpecError) else system_cause(error)],
            ) from error
        block = metadata.get("module") if isinstance(metadata, dict) else None
        if not isinstance(block, dict) or not set(MIRRORED) <= block.keys():
            missing = sorted(set(MIRRORED) - set(block or {}))
            raise SpecError(
                f"the metadata of {record['id']}'s entry has no complete module block; "
                f"missing: {', '.join(missing)}",
                "invalid_spec",
                path=metadata_path(entry),
                subject=record["id"],
                reason="the registry mirrors each entry's module block, so the entry "
                "must declare every mirrored field",
            )
        regenerated = {
            "id": record["id"],
            "title": block["title"],
            "entry": entry,
            **{name: block[name] for name in RECORD_FIELDS[3:]},
        }
        if regenerated != record or list(record) != list(RECORD_FIELDS):
            stale.append(record["id"])
        records.append(regenerated)
    return {"schema_version": 3, "modules": records}, stale


def serialize(registry: dict) -> str:
    return json.dumps(registry, indent=2, ensure_ascii=False) + "\n"


def registry_command(root: str | Path, *, write: bool) -> ToolResult:
    """``registry --write`` rewrites the mirrored fields; ``registry --check`` only reports."""
    root = Path(root)
    try:
        registry_path = _registry_path(root)
        value, stale = mirrored_registry(root, registry_path)
    except SpecError as error:
        return ToolResult("registry", ".", "failed", error=error)
    except (ValueError, OSError) as error:
        return ToolResult(
            "registry",
            ".",
            "failed",
            error=SpecError(
                f"the registry cannot be read: {error}",
                "missing_source",
                path=".concorde/specs.json",
                causes=[system_cause(error)],
            ),
        )
    content = serialize(value)
    current = read_file(root, registry_path).decode("utf-8")
    if write:
        if content == current:
            return ToolResult("registry", ".", "unchanged", artifacts=(registry_path,))
        change = file_change(root, registry_path, content)
        apply_files(root, [change], {registry_path})
        return ToolResult(
            "registry",
            ".",
            "success",
            artifacts=(registry_path,),
            result={"regenerated": stale},
        )
    findings = tuple(
        Finding(
            "CHK.registry.mirror",
            "error",
            registry_path,
            f"registry record {identity} differs from its entry's module block",
            "Run `concorde.py registry --write`.",
            subject_id=identity,
        )
        for identity in stale
    )
    return ToolResult(
        "registry",
        ".",
        "invalid" if findings else "success",
        artifacts=(registry_path,),
        findings=findings,
        result={"stale": stale},
    )
