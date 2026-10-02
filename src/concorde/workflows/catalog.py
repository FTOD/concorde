"""The workflow catalog, and the rendering of a workflow's procedure as a Claude Code workflow.

The catalog lists the workflows the installed parts register when their code loads: each part that
owns a procedure registers its name, description, script and last step with ``register``, as
Method registers ``brownfield``. A workflow's procedure is written once, as plain JavaScript with no
asynchronous helper functions, by the part that owns it. It calls three functions the adapter
``scripts/claude.js`` defines: ``step(key, argv)`` returns a promise of the step outcome (or null
when the step agent returned nothing), ``report(lost)`` a promise of the reported status, and
``note(text)`` shows progress. ``render`` puts a ``meta`` block, the constants ``WORKFLOW`` and
``LAST_STEP`` and that adapter, whose small subagents relay each step, in front of it.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[3]
# The Claude Code adapter every procedure is rendered with, relative to the package root.
ADAPTER = "src/concorde/workflows/scripts/claude.js"
CATALOG = "src/concorde/workflows/catalog.py"


@dataclass(frozen=True)
class Workflow:
    """One registered workflow. ``script`` and ``registered_in`` are paths relative to the
    package root: the procedure's JavaScript and the module that registered it."""

    name: str
    description: str
    when: str
    phases: tuple[str, ...]
    script: str
    last_step: str
    registered_in: str


WORKFLOWS: dict[str, Workflow] = {}


class WorkflowError(ValueError):
    """An unknown workflow, a conflicting registration or a missing script."""


def register(workflow: Workflow) -> None:
    """Add a workflow to the catalog; registering the same definition again changes nothing."""
    known = WORKFLOWS.get(workflow.name)
    if known is not None and known != workflow:
        raise WorkflowError(
            f"workflow {workflow.name!r} is registered already, by {known.registered_in}"
        )
    WORKFLOWS[workflow.name] = workflow


def get(name: str) -> Workflow:
    """The registered workflow ``name``; ``WorkflowError`` when no installed part registered it."""
    if name not in WORKFLOWS:
        raise WorkflowError(
            f"unknown workflow {name!r}; the installed parts register "
            + (", ".join(sorted(WORKFLOWS)) or "none")
        )
    return WORKFLOWS[name]


def claude_name(name: str) -> str:
    """The name Claude Code offers the workflow under, as ``/concorde-<name>``."""
    return f"concorde-{name}"


def output_path(name: str) -> str:
    """Where the build writes the render, relative to the package root."""
    return f"generated/workflows/claude/{claude_name(name)}.js"


def _read(relative: str, root: Path) -> str:
    path = root / relative
    if not path.is_file():
        raise WorkflowError(f"the workflow source {path} is missing")
    return path.read_text(encoding="utf-8")


def render(name: str, root: Path = PACKAGE_ROOT) -> str:
    """The Claude Code workflow script of one workflow, from the sources under ``root``."""
    entry = get(name)
    procedure = _read(entry.script, root)
    adapter = _read(ADAPTER, root)
    constants = (
        f"const WORKFLOW = {json.dumps(name)}\n"
        f"const LAST_STEP = {json.dumps(entry.last_step)}\n"
    )
    meta = {
        "name": claude_name(name),
        "description": entry.description,
        "whenToUse": entry.when,
        "phases": [{"title": title} for title in entry.phases],
    }
    header = f"export const meta = {json.dumps(meta, indent=2)}\n\n"
    return (
        header
        + constants
        + adapter.rstrip("\n")
        + "\n\n"
        + procedure.rstrip("\n")
        + "\n"
    )


def renders(root: Path = PACKAGE_ROOT) -> dict[str, tuple[str, tuple[str, ...]]]:
    """Every file the build writes for the registered workflows: its path relative to ``root``,
    mapped to its content and the sources it was rendered from."""
    files = {}
    for name in sorted(WORKFLOWS):
        entry = WORKFLOWS[name]
        files[output_path(name)] = (
            render(name, root),
            (entry.script, ADAPTER, CATALOG, entry.registered_in),
        )
    return files


__all__ = [
    "ADAPTER",
    "WORKFLOWS",
    "Workflow",
    "WorkflowError",
    "claude_name",
    "get",
    "output_path",
    "register",
    "render",
    "renders",
]
