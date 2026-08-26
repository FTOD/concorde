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
            json.dumps({"profile_version": 1, "specification_root": "specs/example", "root_module_id": "module.example"}) + "\n",
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
    design_path = root / "design.md"
    if not design_path.exists():
        design_path.write_text(
            "# Feature Design: Fixture\n\n**Design status**: Accepted fixture baseline.\n",
            encoding="utf-8",
        )
    feature_ids = []
    for candidate in sorted((specification_root / "features").glob("*/spec.md")):
        match = re.search(r"^id:\s*(\S+)", candidate.read_text(encoding="utf-8"), re.MULTILINE)
        if match:
            feature_ids.append(match.group(1))
    feature_lines = "\n".join(f"  - {identifier}" for identifier in feature_ids)
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
""",
        encoding="utf-8",
    )
    return root


def tree_hashes(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }
