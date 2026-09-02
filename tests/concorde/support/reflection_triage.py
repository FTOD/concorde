"""Fixtures for the installed reflection-triage workflow."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from tests.concorde.support.feature_workspace import (
    create_feature_file,
    reflection_entry,
    write_reflection_log,
)
from tests.concorde.support.paths import REPOSITORY_ROOT


CANONICAL_ASSETS = REPOSITORY_ROOT / "agent-assets" / "reflections"
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
    create_feature_file(root)
    entries = [reflection_entry(f"R-{number:03d}") for number in range(1, entry_count + 1)]
    log = write_reflection_log(root, entries)
    write_high_water(log, entry_count)
    write_config(root)
    return root


def write_high_water(log: Path, number: int) -> Path:
    body = log.read_text(encoding="utf-8")
    marker = f"<!-- concorde-reflection-high-water: R-{number:03d} -->"
    lines = body.splitlines(keepends=True)
    insertion = 1 if lines else 0
    ending = "\r\n" if lines and lines[0].endswith("\r\n") else "\n"
    lines[insertion:insertion] = [ending, marker + ending]
    log.write_text("".join(lines), encoding="utf-8", newline="")
    return log


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
    effort: str = "small",
    commit: str | None = None,
    recorded_under: str = "feature.example.deliver",
    implement_in: str = "specs/example/features/001-deliver.md",
    implement_in_id: str = "feature.example.deliver",
) -> Path:
    path = root / ".concorde" / "reflections" / "plans" / f"{identifier}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"""---
id: {identifier}
title: Fixture plan {identifier}
route: {route}
status: {status}
recorded_under: {recorded_under}
implement_in: {implement_in}
implement_in_id: {implement_in_id}
touches_docsite: false
effort: {effort}
files:
  - src/example.py
{f'commit: {commit}' if commit else ''}
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


def git(root: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(root), *arguments],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def initialize_git(root: Path) -> str:
    git(root, "init", "-b", "main")
    git(root, "config", "user.email", "fixture@example.invalid")
    git(root, "config", "user.name", "Fixture")
    source = root / "src/example.py"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("VALUE = 1\n", encoding="utf-8")
    git(root, "add", ".")
    git(root, "commit", "-m", "fixture baseline")
    return git(root, "rev-parse", "HEAD")


def commit_change(root: Path, value: int = 2) -> str:
    source = root / "src/example.py"
    source.write_text(f"VALUE = {value}\n", encoding="utf-8")
    git(root, "add", "src/example.py")
    git(root, "commit", "-m", f"fixture change {value}")
    return git(root, "rev-parse", "HEAD")
