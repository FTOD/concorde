"""Resolve and execute Concorde command bootstraps from installed artifacts."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


NORMAL_PHASES = {
    "speckit.specify": "specify",
    "speckit.clarify": "clarify",
    "speckit.checklist": "checklist",
    "speckit.plan": "plan",
    "speckit.tasks": "tasks",
    "speckit.implement": "implement",
    "speckit.analyze": "analyze",
    "speckit.converge": "converge",
    "speckit.taskstoissues": "taskstoissues",
}

CONCORDE_RUNTIME_COMMANDS = (
    "speckit.concorde.init",
    "speckit.concorde.feature-create",
    "speckit.concorde.feature-select",
    "speckit.concorde.feature-harden",
    "speckit.concorde.context",
    "speckit.concorde.validate",
)

CONCORDE_AGENT_COMMANDS = ("speckit.concorde.ask",)
CONCORDE_COMMANDS = CONCORDE_RUNTIME_COMMANDS + CONCORDE_AGENT_COMMANDS


@dataclass(frozen=True)
class CommandSurfaceReceipt:
    command_id: str
    registered_path: str
    component_id: str
    source_digest: str
    materialized_digest: str
    handoff_digest: str
    workspace: dict[str, object]
    phase_root: str
    exit_status: int
    checkout_reads: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def sha256_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _files(root: Path, relative_roots: Iterable[str]) -> Iterable[Path]:
    for relative in relative_roots:
        candidate = root / relative
        if candidate.is_file():
            yield candidate
        elif candidate.is_dir():
            yield from sorted(
                path
                for path in candidate.rglob("*")
                if path.is_file()
                and "__pycache__" not in path.parts
                and path.suffix not in {".pyc", ".pyo"}
            )


def handoff_digest(extension_root: Path, preset_root: Path) -> str:
    """Digest installed Feature 001 behavior plus the nine routing surfaces."""
    digest = hashlib.sha256()
    for component, root, members in (
        ("extension", extension_root, ("commands", "runtime", "scripts", "schemas")),
        ("preset", preset_root, ("commands", "templates")),
    ):
        for path in _files(root, members):
            relative = path.relative_to(root).as_posix()
            digest.update(component.encode("utf-8") + b"\0")
            digest.update(relative.encode("utf-8") + b"\0")
            digest.update(path.read_bytes())
            digest.update(b"\0")
    return "sha256:" + digest.hexdigest()


def registered_artifact(project_root: Path, integration: str, command_id: str) -> Path:
    if integration == "codex":
        short = command_id.removeprefix("speckit.").replace(".", "-")
        candidate = project_root / ".agents/skills" / f"speckit-{short}" / "SKILL.md"
        if candidate.is_file():
            return candidate
    normalized = command_id.replace(".", "-")
    integration_root = project_root / (".gemini" if integration == "gemini" else f".{integration}")
    matches = []
    if integration_root.is_dir():
        for path in integration_root.rglob("*"):
            if not path.is_file():
                continue
            stem_token = path.stem.replace(".", "-")
            parent_token = path.parent.name.replace(".", "-")
            if normalized in {stem_token, parent_token}:
                matches.append(path)
    if len(matches) != 1:
        raise AssertionError(f"{command_id} resolves to {len(matches)} registered artifacts: {matches}")
    return matches[0]


def execute_workspace_surface(
    project_root: Path,
    artifact: Path,
    command_id: str,
    phase: str,
    source_checkout: Path,
) -> CommandSurfaceReceipt:
    content = artifact.read_text(encoding="utf-8")
    match = re.search(
        r"(?:python3|python)\s+\.specify/extensions/concorde/scripts/python/workspace\.py\s+--phase\s+([a-z]+)",
        content,
    )
    if match is None or match.group(1) != phase:
        raise AssertionError(f"{artifact} does not expose the expected {phase} installed bootstrap")
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    environment.pop("SPECIFY_FEATURE_DIRECTORY", None)
    adapter = project_root / ".specify/extensions/concorde/scripts/python/workspace.py"
    completed = subprocess.run(
        [sys.executable, str(adapter), "--project-root", str(project_root), "--phase", phase],
        cwd=project_root,
        text=True,
        capture_output=True,
        env=environment,
    )
    payload = json.loads(completed.stdout)
    workspace = payload.get("workspace", {})
    implementation_dir = workspace.get("implementation_dir")
    checklists_dir = workspace.get("checklists_dir")
    if not isinstance(implementation_dir, str) or checklists_dir != f"{implementation_dir}/checklists":
        raise AssertionError(
            f"{artifact} returned a non-canonical checklist workspace: {checklists_dir!r}"
        )
    registered = artifact.relative_to(project_root).as_posix()
    checkout_reads: tuple[str, ...] = ()
    for value in (registered, str(adapter)):
        resolved = (project_root / value).resolve() if not Path(value).is_absolute() else Path(value).resolve()
        if resolved.is_relative_to(source_checkout.resolve()):
            checkout_reads += (str(resolved),)
    return CommandSurfaceReceipt(
        command_id=command_id,
        registered_path=registered,
        component_id="concorde-core",
        source_digest=sha256_bytes(
            (project_root / ".specify/presets/concorde-core/commands" / f"{command_id}.md").read_bytes()
        ),
        materialized_digest=sha256_bytes(artifact.read_bytes()),
        handoff_digest=handoff_digest(
            project_root / ".specify/extensions/concorde",
            project_root / ".specify/presets/concorde-core",
        ),
        workspace=workspace,
        phase_root=str(payload.get("phase_root", "")),
        exit_status=completed.returncode,
        checkout_reads=checkout_reads,
    )
