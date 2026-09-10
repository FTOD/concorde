"""Fixtures for the installed reflection-triage workflow."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

from tests.concorde.support.paths import REPOSITORY_ROOT, RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))

# The initialized Module the fixture reflections and plans are attributed to. A reflection may name
# only a registered Module or scenario; the initialization stub declares no scenario of its own.
MODULE_ID = "module.example"
MODULE_DOCUMENT = "specs/project/module.md"
CONCERNED_FILE = "src/example.py"

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
        ]
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


def reflection_entry(identifier: str, feature: str = MODULE_ID, status: str = "open", **overrides: str) -> dict[str, str]:
    entry = {
        "id": identifier,
        "title": f"Fixture problem {identifier}",
        "Phase": "implement",
        "Date": "2026-08-28",
        "Feature": feature,
        "Kind": "tooling",
        "Concerns": CONCERNED_FILE,
        "Context": "The fixture command was run while preparing the selected Module.",
        "Expected": "The documented command succeeds.",
        "Observed": "The command failed.",
        "Impact": "Planning used a bounded fallback and retained the failure for triage.",
        "Evidence": f"`{CONCERNED_FILE}` and the recorded fixture command.",
        "Status": status,
    }
    if status != "open":
        entry["Note"] = "Decided by the developer."
    entry.update(overrides)
    return entry


DEFAULT_CONFIG = {
    "schema_version": 1,
    "order": "newest-first",
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


def initialize_project(root: Path) -> Path:
    """Apply a real Profile 11 initialization proposal, the only supported project shape."""
    from concorde.spec.initialize import apply_project_proposal, project_proposal
    from concorde.spec.typed_data import typed

    configuration = typed("concorde-capability-configuration",
                          {"integration": "claude", "enforcement": "native"})
    apply_project_proposal(root, REPOSITORY_ROOT,
                           project_proposal(root, REPOSITORY_ROOT, "Example", configuration, MODULE_ID))
    source = root / CONCERNED_FILE
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("VALUE = 1\n", encoding="utf-8")
    return root


def create_triage_project(root: Path, *, entry_count: int = 3) -> Path:
    """Create a minimal initialized Concorde project with open reflections and shared config."""
    initialize_project(root)
    entries = [reflection_entry(f"R-{number:03d}") for number in range(1, entry_count + 1)]
    collection = write_reflection_collection(root, entries)
    write_high_water(collection, entry_count)
    write_config(root)
    return root


def write_high_water(collection: Path, number: int) -> Path:
    index = collection / "index.json"
    index.write_text(
        json.dumps({"high_water": f"R-{number:03d}", "schema_version": 1}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return index


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
    recorded_under: str = MODULE_ID,
    implement_in: str = MODULE_DOCUMENT,
    implement_in_id: str = MODULE_ID,
    verified: str | None = None,
    verified_commit: str | None = None,
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
{f'verified: {verified}' if verified else ''}
{f'verified_commit: {verified_commit}' if verified_commit else ''}
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
    source = root / CONCERNED_FILE
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("VALUE = 1\n", encoding="utf-8")
    git(root, "add", ".")
    git(root, "commit", "-m", "fixture baseline")
    return git(root, "rev-parse", "HEAD")


def commit_change(root: Path, value: int = 2) -> str:
    source = root / CONCERNED_FILE
    source.write_text(f"VALUE = {value}\n", encoding="utf-8")
    git(root, "add", CONCERNED_FILE)
    git(root, "commit", "-m", f"fixture change {value}")
    return git(root, "rev-parse", "HEAD")
