"""The workflow catalog, and the rendering of a workflow's procedure as a Claude Code workflow.

A workflow's procedure is written once, in ``scripts/<name>.js``, as plain JavaScript with no
asynchronous helper functions. It calls three functions the adapter ``scripts/claude.js`` defines:
``step(key, argv)`` returns a promise of the step outcome (or null when the step agent returned
nothing), ``report(lost)`` a promise of the reported status, and ``note(text)`` shows progress.
``render`` puts a ``meta`` block and that adapter, whose small subagents run ``concorde workflow
step``, in front of it.
"""

from __future__ import annotations

import json
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = "src/concorde/workflows/scripts"
CATALOG = "src/concorde/workflows/catalog.py"
# The Claude Code adapter every procedure is rendered with.
ADAPTER = "claude.js"

WORKFLOWS: dict[str, dict] = {
    "brownfield": {
        "description": (
            "Describe a project whose code came before its Specs: survey, scaffold, "
            "code_to_spec per Module, spec review, validation and delivery, in one task"
        ),
        "when": (
            "After installing and initializing Concorde in an existing codebase, in the worktree "
            "of a task bound to the Module to describe, usually the root"
        ),
        "phases": ["Survey", "Scaffold", "Describe", "Review", "Deliver"],
    },
}


class WorkflowError(ValueError):
    """An unknown workflow or a missing script."""


def claude_name(name: str) -> str:
    """The name Claude Code offers the workflow under, as ``/concorde-<name>``."""
    return f"concorde-{name}"


def output_path(name: str) -> str:
    """Where the build writes the render, relative to the package root."""
    return f"generated/workflows/claude/{claude_name(name)}.js"


def _read(name: str, root: Path = PACKAGE_ROOT) -> str:
    path = root / SCRIPTS / name
    if not path.is_file():
        raise WorkflowError(f"the workflow source {path} is missing")
    return path.read_text(encoding="utf-8")


def render(name: str, root: Path = PACKAGE_ROOT) -> str:
    """The Claude Code workflow script of one workflow, from the sources under ``root``."""
    if name not in WORKFLOWS:
        raise WorkflowError(
            f"unknown workflow {name!r}; the catalog has {', '.join(sorted(WORKFLOWS))}"
        )
    entry = WORKFLOWS[name]
    procedure = _read(f"{name}.js", root)
    adapter = _read(ADAPTER, root)
    constant = f"const WORKFLOW = {json.dumps(name)}\n"
    meta = {
        "name": claude_name(name),
        "description": entry["description"],
        "whenToUse": entry["when"],
        "phases": [{"title": title} for title in entry["phases"]],
    }
    header = f"export const meta = {json.dumps(meta, indent=2)}\n\n"
    return (
        header
        + constant
        + adapter.rstrip("\n")
        + "\n\n"
        + procedure.rstrip("\n")
        + "\n"
    )


def renders(root: Path = PACKAGE_ROOT) -> dict[str, tuple[str, tuple[str, ...]]]:
    """Every file the build writes for workflows: its path relative to ``root``, mapped to its
    content and the sources it was rendered from."""
    files = {}
    for name in sorted(WORKFLOWS):
        files[output_path(name)] = (
            render(name, root),
            (f"{SCRIPTS}/{name}.js", f"{SCRIPTS}/{ADAPTER}", CATALOG),
        )
    return files


__all__ = [
    "WORKFLOWS",
    "WorkflowError",
    "claude_name",
    "output_path",
    "render",
    "renders",
]
