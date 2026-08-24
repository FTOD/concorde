"""Feature-workspace fixtures shared by unit and integration tests."""

from __future__ import annotations

import hashlib
import json
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
    return root


def tree_hashes(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }
