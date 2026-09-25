"""The workflow catalog, and the rendering of a workflow's procedure for each client.

A workflow's procedure is written once, in ``scripts/<name>.js``, as plain JavaScript with no
asynchronous helper functions. It calls three functions an adapter defines: ``step(key, argv)``
returns a promise of the step outcome (or null when the step agent returned nothing), ``report(lost)``
a promise of the reported status, and ``note(text)`` shows progress. ``render`` puts the client's
header and adapter in front of it: for Claude Code a ``meta`` block and a subagent that runs
``concorde workflow step``; for pi a call of the command-runner agent ``concorde-step``.
"""

from __future__ import annotations

import json
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = "src/concorde/workflows/scripts"
CATALOG = "src/concorde/workflows/catalog.py"
CLIENTS = ("claude", "pi")

WORKFLOWS: dict[str, dict] = {
    "brownfield": {
        "description": (
            "Describe a project whose code came before its Specs: survey, scaffold, "
            "code_to_spec per Module, spec review, validation and delivery, in one task"
        ),
        "when": (
            "After installing and initializing Concorde in an existing codebase, in a task bound "
            "to the Module to describe, usually the root"
        ),
        "phases": ["Survey", "Scaffold", "Describe", "Review", "Deliver"],
    },
}


class WorkflowError(ValueError):
    """An unknown workflow or client, or a missing script."""


def claude_name(name: str) -> str:
    """The name Claude Code offers the workflow under, as ``/concorde-<name>``."""
    return f"concorde-{name}"


def output_path(name: str, client: str) -> str:
    """Where the build writes the render, relative to the package root."""
    if client == "claude":
        return f"generated/workflows/claude/{claude_name(name)}.js"
    return f"generated/workflows/pi/{name}.js"


def _read(name: str, root: Path = PACKAGE_ROOT) -> str:
    path = root / SCRIPTS / name
    if not path.is_file():
        raise WorkflowError(f"the workflow source {path} is missing")
    return path.read_text(encoding="utf-8")


def render(name: str, client: str, root: Path = PACKAGE_ROOT) -> str:
    """The script of one workflow for one client, from the sources under ``root``."""
    if name not in WORKFLOWS:
        raise WorkflowError(
            f"unknown workflow {name!r}; the catalog has {', '.join(sorted(WORKFLOWS))}"
        )
    if client not in CLIENTS:
        raise WorkflowError(
            f"unknown client {client!r}; expected one of {', '.join(CLIENTS)}"
        )
    entry = WORKFLOWS[name]
    procedure = _read(f"{name}.js", root)
    adapter = _read(f"{client}.js", root)
    constant = f"const WORKFLOW = {json.dumps(name)}\n"
    if client == "claude":
        meta = {
            "name": claude_name(name),
            "description": entry["description"],
            "whenToUse": entry["when"],
            "phases": [{"title": title} for title in entry["phases"]],
        }
        header = f"export const meta = {json.dumps(meta, indent=2)}\n\n"
    else:
        header = (
            f"// Concorde workflow {name} for pi-subagents; run with "
            "subagent({ workflowScriptPath, args }).\n\n"
        )
    return (
        header
        + constant
        + adapter.rstrip("\n")
        + "\n\n"
        + procedure.rstrip("\n")
        + "\n"
    )


AGENTS = ("concorde-step", "concorde-report")


def agent(name: str, root: Path = PACKAGE_ROOT) -> str:
    """A pi command-runner agent that carries workflow steps or reports."""
    return _read(f"{name}.md", root)


def renders(root: Path = PACKAGE_ROOT) -> dict[str, tuple[str, tuple[str, ...]]]:
    """Every file the build writes for workflows: its path relative to ``root``, mapped to its
    content and the sources it was rendered from."""
    files = {}
    for name in sorted(WORKFLOWS):
        for client in CLIENTS:
            files[output_path(name, client)] = (
                render(name, client, root),
                (f"{SCRIPTS}/{name}.js", f"{SCRIPTS}/{client}.js", CATALOG),
            )
    for name in AGENTS:
        files[f"generated/workflows/pi/agents/{name}.md"] = (
            agent(name, root),
            (f"{SCRIPTS}/{name}.md",),
        )
    return files


__all__ = [
    "AGENTS",
    "CLIENTS",
    "WORKFLOWS",
    "WorkflowError",
    "agent",
    "claude_name",
    "output_path",
    "render",
    "renders",
]
