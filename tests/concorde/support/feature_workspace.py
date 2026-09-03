"""Profile 7 feature-workspace fixtures shared by unit and integration tests."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


def write_selection(project_root: Path, feature_path: str) -> Path:
    path = project_root / ".concorde" / "feature.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"feature_path": feature_path}) + "\n", encoding="utf-8")
    return path


def _feature_document(relative: str, feature_id: str, module_id: str) -> str:
    slug = feature_id.rsplit(".", 1)[-1]
    interface_id = f"contract.example.{slug}"
    return f"""---
id: {feature_id}
kind: feature
module: {module_id}
related_features: []
interfaces:
  provided:
    - {interface_id}
  required: []
evidence_status: unknown
---

# Feature Design: {slug.replace('-', ' ').title()}

## Outcome and Scope

The fixture provides the observable {slug} outcome and no unrelated behavior.

## Architecture Zoom

| Entity | Role |
|---|---|
| `entity.example.runtime` | Realizes the fixture outcome. |

## Interfaces

### `{interface_id}` — Fixture interface

**Consumer**: fixture maintainer

**Direction**: bidirectional

**Entry points**: `entity.example.runtime`

**Inputs**: A request naming the fixture outcome.

**Outputs**: An observable success result.

**Obligations**: The consumer supplies a request and the provider returns one deterministic result.

**Failures**: Invalid requests produce a named failure without mutating durable sources.

**Compatibility**: The preserved interface ID remains stable for this fixture profile.

**Implementing entities**: `entity.example.runtime`

## Usage Scenarios

1. A maintainer invokes `entity.example.runtime` and observes the result.

## Requirements

- **FR-001**: The fixture outcome is observable through `{interface_id}`.
- **FR-002**: Failure leaves durable architecture and feature design unchanged.

## Edge Cases

- An empty request produces the named invalid-request failure.
"""


def _root_architecture(feature_ids: list[str]) -> str:
    feature_lines = "\n".join(f"  - {identifier}" for identifier in feature_ids) or "  []"
    feature_rows = "\n".join(f"| `{identifier}` | Fixture capability. |" for identifier in feature_ids) or "| None | No features yet. |"
    return f"""---
id: module.example
kind: module
parent: null
modules: []
features:
{feature_lines}
diagrams:
  - source: diagrams/system-overview.json
    kind: architecture
    output: generated/architecture/example-system-overview.html
---

# Architecture: Example

## Responsibility

Provide deterministic Profile 7 fixtures.

## Boundary

Own fixture orchestration and exclude external product behavior.

## Entities

| Entity ID | Type | Definition | Locator |
|---|---|---|---|
| `entity.example.maintainer` | external-system | The human consumer of fixture behavior. | `external:fixture-maintainer` |
| `entity.example.runtime` | program | The conceptual executable that realizes fixture outcomes. | `concept:example.runtime` |

## Relationships

| Source | Predicate | Target | Description |
|---|---|---|---|
| `entity.example.maintainer` | calls | `entity.example.runtime` | The maintainer invokes the fixture runtime. |
| `module.example` | owns_entity | `entity.example.runtime` | The module owns the runtime boundary. |

## Interactions

| Interaction ID | Trigger | Steps | Result | Interfaces |
|---|---|---|---|---|
| `interaction.example.invoke` | A maintainer requests a fixture outcome. | `entity.example.maintainer` calls `entity.example.runtime`. | The runtime returns an observable result. | None |

## Modules

None.

## Features

| Feature ID | Outcome |
|---|---|
{feature_rows}

## Decisions

- [System overview](diagrams/system-overview.json) projects the fixture entities and relationships.
- Fixtures keep implementation entities conceptual unless locator validation itself is under test.
"""


def _root_system_overview() -> str:
    return json.dumps(
        {
            "schema_version": 1,
            "diagram_type": "architecture",
            "meta": {
                "title": "Example System Overview",
                "output": "../../../generated/architecture/example-system-overview.html",
                "quality_profile": "showcase",
                "legend": {"mode": "hidden"},
            },
            "components": [
                {"id": "maintainer", "type": "external", "label": "Maintainer"},
                {"id": "runtime", "type": "backend", "label": "Runtime"},
            ],
            "connections": [
                {"id": "maintainer-calls-runtime", "from": "maintainer", "to": "runtime", "label": "calls"}
            ],
        },
        separators=(",", ":"),
    ) + "\n"


def create_feature_file(
    project_root: Path,
    relative: str = "specs/example/features/001-deliver.md",
    feature_id: str = "feature.example.deliver",
    module_id: str = "module.example",
) -> Path:
    config = project_root / ".concorde" / "config.json"
    config.parent.mkdir(parents=True, exist_ok=True)
    if not config.exists():
        config.write_text(json.dumps({"profile_version": 7, "specification_root": "specs/example", "root_module_id": "module.example"}) + "\n", encoding="utf-8")
    feature = project_root / relative
    feature.parent.mkdir(parents=True, exist_ok=True)
    if not feature.exists():
        feature.write_text(_feature_document(relative, feature_id, module_id), encoding="utf-8")
    specification_root = project_root / "specs/example"
    feature_ids: list[str] = []
    for candidate in sorted((specification_root / "features").glob("*.md")):
        match = re.search(r"^id:\s*(\S+)", candidate.read_text(encoding="utf-8"), re.MULTILINE)
        if match:
            feature_ids.append(match.group(1))
    (specification_root / "architecture.md").write_text(_root_architecture(feature_ids), encoding="utf-8")
    diagram = specification_root / "diagrams/system-overview.json"
    diagram.parent.mkdir(parents=True, exist_ok=True)
    diagram.write_text(_root_system_overview(), encoding="utf-8")
    return feature


def write_accepted_feature(project_root: Path, relative: str, feature_id: str, module_id: str = "module.example") -> Path:
    """Create a delivered direct feature with no temporal attempt."""
    feature = create_feature_file(project_root, relative, feature_id, module_id)
    attempt = attempt_path(feature)
    if attempt.exists() and attempt.is_dir():
        for path in sorted(attempt.rglob("*"), reverse=True):
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                path.rmdir()
        attempt.rmdir()
    return feature


def attempt_path(feature_path: Path) -> Path:
    match = re.search(r"^id:\s*(feature\.[a-z0-9]+(?:[.-][a-z0-9]+)*)\s*$", feature_path.read_text(encoding="utf-8"), re.MULTILINE)
    if match is None:
        raise AssertionError(f"fixture feature has no canonical stable ID: {feature_path}")
    project_root = next(
        (parent for parent in feature_path.parents if (parent / ".concorde/config.json").is_file()),
        None,
    )
    if project_root is None:
        raise AssertionError(f"fixture feature is not inside a Concorde project: {feature_path}")
    return project_root / ".concorde" / "attempts" / match.group(1)


def write_complete_attempt(feature_path: Path, task_ids: tuple[str, ...] = ("T001",)) -> Path:
    attempt = attempt_path(feature_path)
    attempt.mkdir(parents=True, exist_ok=True)
    (attempt / "tasks.md").write_text("# Tasks\n\n" + "\n".join(f"- [X] {identifier} Complete fixture work" for identifier in task_ids) + "\n", encoding="utf-8")
    evidence = "# Validation\n\n## Attempt Evidence\n\n" + "\n\n".join(f"### {identifier} — Fixture evidence\n\n- **Outcome**: passed\n- **Check**: deterministic fixture check.\n" for identifier in task_ids) + "\n"
    (attempt / "validation.md").write_text(evidence, encoding="utf-8")
    return attempt


def tree_hashes(root: Path) -> dict[str, str]:
    return {path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(root.rglob("*")) if path.is_file()}


REFLECTION_BUCKETS = ("pending", "planned", "needs-comments")


def reflection_bucket_for(entry: dict[str, str]) -> str:
    """Mirror the runtime bucket rule: triage state alone decides the folder."""
    if entry.get("Triage", "pending") == "pending":
        return "pending"
    return "planned" if entry.get("Human Intervention") == "not-required" else "needs-comments"


def write_reflection_collection(
    project_root: Path, entries: list[dict[str, str]], *, bucket: str | None = None
) -> Path:
    """Write a per-file reflection collection.

    The folder follows the runtime bucket rule unless an entry carries a ``bucket`` key or the
    ``bucket`` argument forces every entry into one (possibly wrong) folder.
    """
    directory = project_root / ".concorde" / "reflections"
    directory.mkdir(parents=True, exist_ok=True)
    for existing in [*directory.glob("R-*.md"), *(path for name in REFLECTION_BUCKETS for path in (directory / name).glob("R-*.md"))]:
        existing.unlink()
    high_water = max((int(entry["id"][2:]) for entry in entries), default=0)
    (directory / "index.json").write_text(
        json.dumps({"high_water": f"R-{high_water:03d}", "schema_version": 1}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    for entry in entries:
        identifier = entry["id"]
        title = entry.get("title", "Fixture problem")
        metadata = [
            "---",
            f"id: {identifier}",
            f"title: {title}",
            f"phase: {entry['Phase']}",
            f"date: {entry['Date']}",
            f"feature: {entry['Feature']}",
            f"kind: {entry['Kind']}",
            f"concerns: {entry['Concerns']}",
            f"status: {entry['Status']}",
            f"triage: {entry.get('Triage', 'pending')}",
        ]
        if entry.get("Human Intervention"):
            metadata.append(f"human_intervention: {entry['Human Intervention']}")
        if entry.get("Note"):
            metadata.append(f"resolution_note: {entry['Note']}")
        metadata.append("---")
        occurrences = "\n".join(f"- {item}" for item in entry.get("occurrences", []))
        body = "\n".join(metadata) + f"""

# {identifier} · {title}

## Context

{entry['Context']}

## Expected

{entry['Expected']}

## Observed

{entry['Observed']}

## Impact

{entry['Impact']}

## Evidence

{entry['Evidence']}

## Triage Analysis

{entry.get('Triage Analysis', '')}

## Proposed Resolution

{entry.get('Proposed Resolution', '')}

## Intervention Rationale

{entry.get('Intervention Rationale', '')}

## User Comments

{entry.get('User Comments', '')}

## Occurrences

{occurrences}
"""
        target = directory / (entry.get("bucket") or bucket or reflection_bucket_for(entry)) / f"{identifier}.md"
        target.parent.mkdir(exist_ok=True)
        target.write_text(body.rstrip() + "\n", encoding="utf-8")
    return directory


def reflection_entry(identifier: str, feature: str = "feature.example.deliver", status: str = "open", **overrides: str) -> dict[str, str]:
    entry = {
        "id": identifier,
        "title": f"Fixture problem {identifier}",
        "Phase": "implement",
        "Date": "2026-08-28",
        "Feature": feature,
        "Kind": "tooling",
        "Concerns": "specs/example/architecture.md",
        "Context": "The fixture command was run while preparing the selected feature.",
        "Expected": "The documented command succeeds.",
        "Observed": "The command failed.",
        "Impact": "Planning used a bounded fallback and retained the failure for triage.",
        "Evidence": "`specs/example/architecture.md` and the recorded fixture command.",
        "Status": status,
    }
    if status != "open":
        entry["Note"] = "Decided by the maintainer."
    entry.update(overrides)
    return entry
