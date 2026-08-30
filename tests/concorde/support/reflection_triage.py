"""Fixtures for the installed reflection-triage workflow."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from tests.concorde.support.feature_workspace import (
    create_feature_root,
    reflection_entry,
    write_reflection_log,
)
from tests.concorde.support.paths import REPOSITORY_ROOT


CANONICAL_ASSETS = REPOSITORY_ROOT / "extensions" / "concorde" / "agent-assets" / "reflections"
DEFAULT_CONFIG = {
    "schema_version": 1,
    "order": "newest-first",
    "investigators": 1,
    "implementers": 2,
    "require_approval": False,
    "skip": [],
    "plans_dir": ".concorde/reflections/plans",
    "worktrees_dir": ".concorde/reflections/worktrees",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_hashes(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): sha256(path)
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def create_triage_project(root: Path, *, entry_count: int = 3) -> Path:
    """Create a minimal Concorde project with open reflections and shared config."""
    create_feature_root(root)
    entries = [reflection_entry(f"R-{number:03d}") for number in range(1, entry_count + 1)]
    write_reflection_log(root, entries)
    write_config(root)
    return root


def write_config(root: Path, **overrides: object) -> Path:
    value = {**DEFAULT_CONFIG, **overrides}
    path = root / ".concorde" / "reflections" / "config.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def write_plan(
    root: Path,
    identifier: str,
    *,
    route: str = "fast-loop",
    status: str = "proposed",
    implement_in: str = "specs/example/features/001-deliver",
) -> Path:
    path = root / ".concorde" / "reflections" / "plans" / f"{identifier}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"""---
id: {identifier}
title: Fixture plan {identifier}
route: {route}
status: {status}
recorded_under: feature.example.deliver
implement_in: {implement_in}
implement_in_id: feature.example.deliver
touches_docsite: false
effort: small
files:
  - src/example.py
---
## Problem

Fixture problem.

## Change

Apply the fixture change.

## Validation

`python -m unittest fixture`

## Risks and out of scope

Keep unrelated files untouched.
""",
        encoding="utf-8",
    )
    return path
