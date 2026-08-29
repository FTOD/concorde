"""Feature-workspace fixtures shared by unit and integration tests."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


def write_selection(project_root: Path, feature_directory: str) -> Path:
    path = project_root / ".specify" / "feature.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"feature_directory": feature_directory}) + "\n", encoding="utf-8")
    return path


def create_feature_root(
    project_root: Path,
    relative: str = "specs/example/features/001-deliver",
    feature_id: str = "feature.example.deliver",
    module_id: str = "module.example",
) -> Path:
    config = project_root / ".concorde" / "config.json"
    config.parent.mkdir(parents=True, exist_ok=True)
    if not config.exists():
        config.write_text(
            json.dumps({"profile_version": 4, "specification_root": "specs/example", "root_module_id": "module.example"}) + "\n",
            encoding="utf-8",
        )
    specification_root = project_root / "specs" / "example"
    specification_root.mkdir(parents=True, exist_ok=True)
    architecture = specification_root / "architecture" / "diagrams" / "level-view.json"
    architecture.parent.mkdir(parents=True, exist_ok=True)
    if not architecture.exists():
        architecture.write_text('{"schema_version":1,"diagram_type":"architecture","meta":{"title":"Example","legend":{"mode":"hidden"},"views":[]},"components":[],"connections":[]}\n', encoding="utf-8")
    contract = specification_root / "architecture" / "contracts" / "workflow" / "contract.md"
    contract.parent.mkdir(parents=True, exist_ok=True)
    if not contract.exists():
        contract.write_text(
            """---
id: contract.example.workflow
kind: contract
module: module.example
role: provided
flow: bidirectional
counterparties:
  - external.user
representation:
  kind: standard
  format: Fixture
  version: "1"
  definition: https://example.invalid/fixture
features: []
evidence_status: unknown
---
# Fixture Contract
## Purpose
Fixture.
## Information
Fixture.
## Obligations
Fixture.
## Failure Semantics
Fixture.
## Compatibility
Fixture.
## Evidence
Unknown.
""",
            encoding="utf-8",
        )
    root = project_root / relative
    root.mkdir(parents=True, exist_ok=True)
    design_path = root / "design.md"
    if not design_path.exists():
        design_path.write_text(
            f"""---
id: {feature_id}
kind: feature
module: {module_id}
refines: []
scenarios:
  - scenario.example.deliver
contracts:
  provided:
    - contract.example.workflow
  required: []
evidence_status: unknown
canonical_design: {relative}/design.md
---

# Deliver

Observable delivery behavior. Scenarios below are representative examples.

## Outcome

The fixture delivers its observable outcome.

## Requirements

- **FR-001**: Delivery is observable through the workflow contract.
- **FR-002**: Delivery never mutates maintained sources.
""",
            encoding="utf-8",
        )
    implementation_path = root / "implementation.md"
    if not implementation_path.exists():
        implementation_path.write_text(FEATURE_IMPLEMENTATION_PLACEHOLDER, encoding="utf-8")
    abstract_path = root / "abstract.md"
    if not abstract_path.exists():
        abstract_path.write_text(FEATURE_ABSTRACT_FIXTURE, encoding="utf-8")
    module_design = specification_root / "design.md"
    if not module_design.exists():
        module_design.write_text(MODULE_DESIGN_REFERENCE.format(name="Example"), encoding="utf-8")
    feature_ids = []
    for candidate in sorted((specification_root / "features").glob("*/design.md")):
        match = re.search(r"^id:\s*(\S+)", candidate.read_text(encoding="utf-8"), re.MULTILINE)
        if match:
            feature_ids.append(match.group(1))
    feature_lines = "\n".join(f"  - {identifier}" for identifier in feature_ids)
    feature_rows = "\n".join(
        f"| `{identifier}` | Fixture outcome. | `features/{identifier.rsplit('.', 1)[-1]}` |" for identifier in feature_ids
    )
    (specification_root / "module.md").write_text(
        f"""---
id: module.example
kind: module
parent: null
children: []
features:
{feature_lines}
contracts:
  provided:
    - contract.example.workflow
  required: []
---
# Example

## Responsibility

Provide fixtures.

## Boundary

Fixture boundary.

## Structure

The level view is [level-view.json](architecture/diagrams/level-view.json).

## Features

| Feature ID | Outcome | Specification |
|---|---|---|
{feature_rows}

## Contracts

| Contract ID | Role | Flow | Counterparty |
|---|---|---|---|
| `contract.example.workflow` | provided | bidirectional | external.user |

## Submodules

None.

## Representative Scenario

A user delivers the fixture workflow through the workflow contract.

## Design Rationale

Fixtures stay minimal; see the [design reference](design.md).
""",
        encoding="utf-8",
    )
    return root


FEATURE_IMPLEMENTATION_PLACEHOLDER = """# Feature Implementation: Fixture

**Realization status**: No implementation realization has been accepted yet.

## Realization Overview

No implementation realization has been accepted yet.

## Module and Feature Collaboration

No implementation realization has been accepted yet.

## Scenario Realization

No implementation realization has been accepted yet.

## Durable Implementation Decisions

No implementation realization has been accepted yet.

## Traceability and Evidence

No implementation realization has been accepted yet.

## Known Limitations

No implementation realization has been accepted yet.
"""


FEATURE_ABSTRACT_FIXTURE = """# Feature Abstract: Deliver

`feature.example.deliver` · specified at `module.example` · one minute.

## Purpose

Deliver the fixture outcome for the example maintainer.

## Functionality

The feature delivers one observable outcome through the workflow contract and does nothing else.

## Structure

The level view is [level-view.json](../../architecture/diagrams/level-view.json).

```text
maintainer ──▶ example module ──▶ workflow contract
```

## Logic

1. The maintainer invokes the workflow.
2. The module delivers the outcome.

**Rules the implementation must keep**

- Delivery is observable and never mutates maintained sources (FR-001, FR-002).

## Read Next

- [design.md](design.md), [implementation.md](implementation.md), and the module summary [module.md](../../module.md).
"""


MODULE_DESIGN_REFERENCE = """# Design Reference: {name}

## Implementation Notes

No implementation detail or design rationale has been recorded for this module yet.

## Design Rationale

Not recorded yet.

## Alternatives Considered

Not recorded yet.

## Decision Log

- (empty)
"""


def write_accepted_root(project_root: Path, relative: str, feature_id: str, module_id: str = "module.example") -> Path:
    """Create a feature root whose implementation.md is accepted and that has no attempt."""
    root = create_feature_root(project_root, relative, feature_id, module_id)
    (root / "implementation.md").write_text(
        "# Feature Implementation: Fixture\n\n**Realization status**: Accepted fixture milestone.\n\n"
        "## Realization Overview\n\nAccepted.\n\n## Module and Feature Collaboration\n\nAccepted.\n\n"
        "## Scenario Realization\n\nAccepted.\n\n## Durable Implementation Decisions\n\nAccepted.\n\n"
        "## Traceability and Evidence\n\nAccepted.\n\n## Known Limitations\n\nNone recorded.\n",
        encoding="utf-8",
    )
    return root


def tree_hashes(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def write_reflection_log(project_root: Path, entries: list[dict[str, str]], specification_root: str = "specs/example") -> Path:
    """Write the project reflection log from entry dicts (keys are the grammar's labels; ``id`` and ``title`` name the entry)."""
    order = ("Phase", "Date", "Feature", "Kind", "Concerns", "Expected", "Observed", "Effect", "Action", "Improvement", "Status", "Note")
    blocks = ["# Reflections: Example\n\nFixture log.\n"]
    for entry in entries:
        lines = [f"### {entry['id']} · {entry.get('title', 'Fixture problem')}", ""]
        for label in order:
            if label in entry:
                lines.append(f"- **{label}**: {entry[label]}")
        for occurrence in entry.get("occurrences", []):
            if "- **Occurrences**:" not in lines:
                lines.append("- **Occurrences**:")
            lines.append(f"  - {occurrence}")
        blocks.append("\n".join(lines) + "\n")
    path = project_root / specification_root / "reflections.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(blocks), encoding="utf-8")
    return path


def reflection_entry(identifier: str, feature: str = "feature.example.deliver", status: str = "open", **overrides: str) -> dict[str, str]:
    entry = {
        "id": identifier,
        "title": f"Fixture problem {identifier}",
        "Phase": "implement",
        "Date": "2026-08-28",
        "Feature": feature,
        "Kind": "tooling",
        "Concerns": "contract.example.workflow",
        "Expected": "The documented command succeeds.",
        "Observed": "The command failed.",
        "Effect": "worked-around",
        "Action": "Used the fallback.",
        "Improvement": "Fix the command.",
        "Status": status,
    }
    if status != "open":
        entry["Note"] = "Decided by the maintainer."
    entry.update(overrides)
    return entry
