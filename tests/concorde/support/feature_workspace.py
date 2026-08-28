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
            json.dumps({"profile_version": 2, "specification_root": "specs/example", "root_module_id": "module.example"}) + "\n",
            encoding="utf-8",
        )
    specification_root = project_root / "specs" / "example"
    specification_root.mkdir(parents=True, exist_ok=True)
    architecture = specification_root / "architecture.json"
    if not architecture.exists():
        architecture.write_text('{"schema_version":1,"diagram_type":"architecture","meta":{"views":[]},"components":[],"connections":[]}\n', encoding="utf-8")
    contract = specification_root / "contracts" / "workflow" / "contract.md"
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
    spec_path = root / "spec.md"
    if not spec_path.exists():
        spec_path.write_text(
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
architecture_view: specs/example/architecture.json
evidence_status: unknown
canonical_spec: {relative}/spec.md
---

# Deliver

Observable delivery behavior. Scenarios below are representative examples.
""",
            encoding="utf-8",
        )
    implementation_path = root / "implementation.md"
    if not implementation_path.exists():
        implementation_path.write_text(
            "# Feature Implementation: Fixture\n\n**Realization status**: Accepted fixture baseline.\n",
            encoding="utf-8",
        )
    module_design = specification_root / "design.md"
    if not module_design.exists():
        module_design.write_text(MODULE_DESIGN_REFERENCE.format(name="Example"), encoding="utf-8")
    feature_ids = []
    for candidate in sorted((specification_root / "features").glob("*/spec.md")):
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
view: specs/example/architecture.json
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

The level view is [architecture.json](architecture.json).

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


def write_hardened_root(project_root: Path, relative: str, feature_id: str, module_id: str = "module.example") -> Path:
    """Create a feature root whose implementation.md is already hardened and that has no attempt."""
    root = create_feature_root(project_root, relative, feature_id, module_id)
    (root / "implementation.md").write_text(
        "# Feature Implementation: Fixture\n\n**Realization status**: Hardened fixture milestone.\n\n"
        "## Realization Overview\n\nHardened.\n\n## Module and Feature Collaboration\n\nHardened.\n\n"
        "## Scenario Realization\n\nHardened.\n\n## Durable Implementation Decisions\n\nHardened.\n\n"
        "## Traceability and Evidence\n\nHardened.\n\n## Known Limitations\n\nNone recorded.\n",
        encoding="utf-8",
    )
    return root


def tree_hashes(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }
