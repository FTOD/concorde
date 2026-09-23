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
        raise SpecError(
            "configuration names no registry path",
            "invalid_spec",
            ".concorde/config.json",
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
        raise SpecError(
            'the registry must be {"schema_version": 3, "modules": [...]}',
            "unsupported_profile",
            registry_path,
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
                registry_path,
            )
        entry = record["entry"]
        try:
            metadata = decode(read_file(root, metadata_path(entry)).decode("utf-8"))
        except (SpecError, ValueError, OSError, UnicodeError) as error:
            raise SpecError(
                f"entry of {record['id']} cannot be read: {error}",
                "missing_source",
                entry,
            ) from error
        block = metadata.get("module") if isinstance(metadata, dict) else None
        if not isinstance(block, dict) or not set(MIRRORED) <= block.keys():
            raise SpecError(
                f"entry of {record['id']} has no complete module block",
                "invalid_spec",
                entry,
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
    except (SpecError, ValueError, OSError) as error:
        return ToolResult(
            "registry",
            ".",
            "failed",
            findings=(
                Finding(
                    "CONCORDE-REGISTRY-001",
                    "error",
                    getattr(error, "field", "") or ".concorde/specs.json",
                    str(error),
                    "Repair the registry or the entry it names; nothing was written.",
                ),
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
