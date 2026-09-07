#!/usr/bin/env python3
"""Check, refresh, or verify worktree affinity for Concorde's own agent surfaces."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tempfile
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from concorde.reflections.agent_assets import AgentAssetError, projection_roles, render_projection  # noqa: E402
from concorde.capabilities.skill_assets import (  # noqa: E402
    SkillAssetError,
    capability_projection_roles,
    render_capabilities,
)
from concorde.capabilities.worktree import inspect_worktree  # noqa: E402
from concorde.capabilities.protocol_contracts import PUBLIC_OPERATIONS  # noqa: E402


SKILL_NAME = re.compile(r"^concorde-[a-z0-9]+(?:-[a-z0-9]+)*$")
INTEGRATION_ROOTS = {
    "codex": Path(".agents/skills"),
    "claude": Path(".claude/skills"),
}
GENERATED_PATTERNS = (
    ".agents/skills/concorde-*/SKILL.md",
    ".claude/skills/concorde-*/SKILL.md",
    ".codex/agents/reflection_*.toml",
    ".claude/agents/reflection-*.md",
)


class WorktreeAffinityError(ValueError):
    """Loaded source-checkout Skills belong to a different worktree."""


def _sha256(content: bytes) -> str:
    return "sha256:" + hashlib.sha256(content).hexdigest()


def expected_outputs(root: Path) -> dict[str, bytes]:
    outputs: dict[str, bytes] = {}
    for integration in ("codex", "claude"):
        rendered = render_capabilities(root, integration, "")
        capability_roles = capability_projection_roles(root, integration, "")
        if set(rendered) != set(capability_roles) or len(rendered) != len(PUBLIC_OPERATIONS):
            raise ValueError(
                f"{integration} must expose exactly {len(PUBLIC_OPERATIONS)} public capabilities with owned roles"
            )
        specialist = render_projection(root / "agent-assets/reflections", integration)
        specialist_roles = projection_roles(root / "agent-assets/reflections", integration)
        if set(specialist) != set(specialist_roles):
            raise ValueError(f"{integration} specialist role inventory differs from outputs")
        collisions = set(rendered) & set(specialist)
        if collisions:
            raise ValueError(f"agent surface role collision: {sorted(collisions)}")
        rendered.update(specialist)
        for relative, content in rendered.items():
            encoded = content.encode("utf-8")
            if relative in outputs and outputs[relative] != encoded:
                raise ValueError(f"agent surface collision: {relative}")
            outputs[relative] = encoded
    return dict(sorted(outputs.items()))


def inspect(root: Path, desired: dict[str, bytes]) -> list[dict[str, str]]:
    actions: list[dict[str, str]] = []
    for relative, content in desired.items():
        target = root / relative
        digest = _sha256(content)
        if target.is_symlink():
            action = "replace-symlink"
        elif not target.exists():
            action = "create"
        elif not target.is_file():
            action = "conflict"
        elif target.read_bytes() == content:
            action = "current"
        else:
            action = "update"
        actions.append({"path": relative, "action": action, "sha256": digest})
    return actions


def inspect_checkout(root: Path, desired: dict[str, bytes]) -> list[dict[str, str]]:
    """Inspect desired outputs plus unexpected Concorde-owned projection names."""

    actions = inspect(root, desired)
    observed = {
        path.relative_to(root).as_posix(): path
        for pattern in GENERATED_PATTERNS
        for path in root.glob(pattern)
    }
    for relative, path in observed.items():
        if relative in desired:
            continue
        digest = (
            _sha256(path.read_bytes())
            if path.is_file() and not path.is_symlink()
            else "sha256:" + "0" * 64
        )
        actions.append({"path": relative, "action": "unexpected", "sha256": digest})
    return sorted(actions, key=lambda item: item["path"])


def _loaded_skill_identity(loaded_skill_path: str | Path) -> tuple[Path, str, str]:
    path = Path(loaded_skill_path)
    if not path.is_absolute():
        raise WorktreeAffinityError(
            "--loaded-skill-path must be the absolute path advertised by the agent runtime"
        )
    if path.is_symlink() or not path.is_file():
        raise WorktreeAffinityError(
            f"loaded Skill path is missing, unsafe, or not a file: {path}"
        )
    resolved = path.resolve()
    capability = resolved.parent.name
    if resolved.name != "SKILL.md" or not SKILL_NAME.fullmatch(capability):
        raise WorktreeAffinityError(f"loaded Skill path is not a Concorde capability: {resolved}")
    if len(resolved.parents) < 4:
        raise WorktreeAffinityError(f"loaded Skill path is too shallow: {resolved}")
    if resolved.parents[1].name != "skills":
        raise WorktreeAffinityError(f"loaded Skill has no integration skill root: {resolved}")
    integration_directory = resolved.parents[2].name
    integrations = {".agents": "codex", ".claude": "claude"}
    if integration_directory not in integrations:
        raise WorktreeAffinityError(
            f"loaded Skill is not from a source-checkout integration: {resolved}"
        )
    integration = integrations[integration_directory]
    root = resolved.parents[3]
    expected = root / INTEGRATION_ROOTS[integration] / capability / "SKILL.md"
    if resolved != expected:
        raise WorktreeAffinityError(f"loaded Skill path has an unexpected layout: {resolved}")
    boundary = inspect_worktree(root)
    if Path(boundary.repository_root) != root:
        raise WorktreeAffinityError(f"loaded Skill owner is not a Git worktree root: {root}")
    return root, integration, capability


def _capability_manifest(root: Path, integration: str) -> dict[str, str]:
    surface = root / INTEGRATION_ROOTS[integration]
    if surface.is_symlink() or not surface.is_dir():
        raise WorktreeAffinityError(
            f"{integration} capability surface is missing or unsafe: {surface}"
        )
    manifest: dict[str, str] = {}
    for path in sorted(surface.glob("concorde-*/SKILL.md")):
        if path.is_symlink() or not path.is_file() or not SKILL_NAME.fullmatch(path.parent.name):
            raise WorktreeAffinityError(f"{integration} capability is missing or unsafe: {path}")
        manifest[path.parent.name] = _sha256(path.read_bytes())
    if not manifest:
        raise WorktreeAffinityError(f"{integration} capability surface is empty: {surface}")
    return manifest


def verify_worktree_affinity(root: Path, loaded_skill_path: str | Path) -> dict[str, object]:
    """Require the active worktree to own the project Skill loaded by this conversation."""

    active_boundary = inspect_worktree(root)
    if Path(active_boundary.repository_root) != root:
        raise WorktreeAffinityError(f"active project is not a Git worktree root: {root}")
    loaded_root, integration, capability = _loaded_skill_identity(loaded_skill_path)
    if loaded_root != root:
        try:
            loaded_manifest = _capability_manifest(loaded_root, integration)
            active_manifest = _capability_manifest(root, integration)
            differences = sorted(
                capability_name
                for capability_name in set(loaded_manifest) | set(active_manifest)
                if loaded_manifest.get(capability_name)
                != active_manifest.get(capability_name)
            )
            version_detail = (
                f"Skill versions differ for {', '.join(differences)}. "
                if differences
                else "The generated Skill bytes currently match, but worktree identity still "
                "differs. "
            )
        except WorktreeAffinityError as error:
            version_detail = f"Skill versions could not be compared safely: {error}. "
        raise WorktreeAffinityError(
            f"this agent loaded Concorde Skills from {loaded_root}, but project work targets {root}. "
            + version_detail
            + f"Stop and explicitly ask the user to open a new agent in {root}; do not continue "
            f"there and do not update Skills in {loaded_root}."
        )
    desired = expected_outputs(root)
    drift = [
        item
        for item in inspect_checkout(root, desired)
        if item["action"] != "current"
    ]
    if drift:
        summary = ", ".join(f"{item['action']}:{item['path']}" for item in drift)
        raise WorktreeAffinityError(
            f"the active worktree's generated agent surfaces are stale: {summary}. Run "
            "sync-agent-surfaces.py apply in this worktree from a maintenance session, then open a "
            "fresh agent if any changed project Skill was already loaded as instructions."
        )
    return {
        "project_root": str(root),
        "loaded_worktree": str(loaded_root),
        "integration": integration,
        "capability": capability,
        "surface_match": True,
        "worktree_head": active_boundary.head,
    }


def apply(root: Path, desired: dict[str, bytes], actions: list[dict[str, str]]) -> None:
    conflicts = [item for item in actions if item["action"] == "conflict"]
    if conflicts:
        raise ValueError("generated agent surface has a non-file conflict")
    for item in actions:
        if item["action"] == "current":
            continue
        target = root / item["path"]
        if target.is_symlink():
            target.unlink()
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=target.parent, prefix=".concorde-surface-", delete=False) as handle:
            staged = Path(handle.name)
            handle.write(desired[item["path"]])
        try:
            staged.replace(target)
        finally:
            staged.unlink(missing_ok=True)
        target.chmod(0o644)


def main() -> int:
    parser = argparse.ArgumentParser(prog="sync-agent-surfaces")
    parser.add_argument("tool", choices=["status", "check", "apply", "verify-worktree"])
    parser.add_argument("--project-root", default=str(REPOSITORY_ROOT))
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--loaded-skill-path")
    arguments = parser.parse_args()
    root = Path(arguments.project_root).resolve()
    try:
        if root != REPOSITORY_ROOT:
            raise ValueError(
                f"{arguments.tool} must execute the script from the same worktree named by "
                f"--project-root (checker={REPOSITORY_ROOT}, project={root}). "
                "Run the target worktree's own scripts/development/sync-agent-surfaces.py."
            )
        if arguments.tool == "verify-worktree":
            if arguments.loaded_skill_path is None:
                raise WorktreeAffinityError(
                    "verify-worktree requires --loaded-skill-path from the agent runtime's "
                    "available-skills catalog"
                )
            verified = verify_worktree_affinity(root, arguments.loaded_skill_path)
            result = {
                "schema_version": 1,
                "tool": arguments.tool,
                "status": "current",
                **verified,
            }
            if arguments.format == "json":
                print(json.dumps(result, indent=2, sort_keys=True))
            else:
                print(
                    "Concorde agent worktree: current "
                    f"({verified['integration']}, {verified['capability']}, "
                    f"{verified['project_root']})"
                )
            return 0
        desired = expected_outputs(root)
        actions = inspect_checkout(root, desired)
        if arguments.tool == "apply":
            apply(
                root,
                desired,
                [item for item in actions if item["path"] in desired],
            )
            actions = inspect_checkout(root, desired)
        drift = [item for item in actions if item["action"] != "current"]
        result = {
            "schema_version": 2,
            "tool": arguments.tool,
            "status": "current" if not drift else "drift",
            "outputs": len(desired),
            "actions": actions,
        }
        if arguments.format == "json":
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            print(f"Concorde agent surfaces: {result['status']} ({len(desired)} outputs)")
            for item in drift:
                print(f"  {item['action']}: {item['path']}")
        return 0 if arguments.tool == "status" or not drift else 1
    except WorktreeAffinityError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    except (AgentAssetError, SkillAssetError, ValueError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
