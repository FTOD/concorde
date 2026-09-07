"""Worktree affinity for Concorde's own project-local Skills (AGENTS.md worktree-affinity policy).

An agent session must not carry loaded project-local ``concorde-*`` Skills from the worktree
where the session started into another linked worktree. ``verify_worktree_affinity`` requires the
SKILL.md path the agent runtime actually advertised to belong to the worktree the current task
would read or change, and requires that worktree's own build to be fresh: after Stage B1 the
rendered ``.claude/skills``/``.agents/skills`` directories are untracked build output, not a
synced projection, so freshness is exactly ``build.verify_fresh`` rather than a byte-for-byte
drift comparison against canonical sources.
"""

from __future__ import annotations

import hashlib
import re
import subprocess
from pathlib import Path

from .build import BuildError, verify_fresh
from .session_handoff import handoff_prompt
from .worktree import inspect_worktree

SKILL_NAME = re.compile(r"^concorde-[a-z0-9]+(?:-[a-z0-9]+)*$")
INTEGRATION_ROOTS = {
    "codex": Path(".agents/skills"),
    "claude": Path(".claude/skills"),
}


class WorktreeAffinityError(ValueError):
    """Loaded source-checkout Skills belong to a different worktree, or this worktree is stale."""


def _sha256(content: bytes) -> str:
    return "sha256:" + hashlib.sha256(content).hexdigest()


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


def _handoff(root: Path, *, maintenance: bool = False) -> str:
    branch = subprocess.run(("git", "-C", str(root), "branch", "--show-current"),
                            capture_output=True, text=True, check=False)
    return handoff_prompt(
        root, branch=branch.stdout.strip() if branch.returncode == 0 else None,
        checks="Source-checkout affinity verification failed; task checks are unknown to this verifier.",
        next_steps=("Start a maintenance session without invoking project-local Concorde Skills. "
                    "Inspect canonical sources and any saved patch, run this worktree's "
                    "python3 scripts/concorde.py build, then verify-worktree again. "
                    if maintenance else "Verify affinity in this worktree, then resume the accepted task. ")
                   + "Use this runtime's advertised absolute project-local Skill path for verify-worktree.",
        completion="Affinity and build freshness pass; complete the accepted task and its checks.")


def verify_worktree_affinity(root: Path, loaded_skill_path: str | Path) -> dict[str, object]:
    """Require the active worktree to own the loaded project Skill and to have a fresh build."""

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
            f"there and do not update Skills in {loaded_root}.\n\n" + _handoff(root)
        )
    try:
        verify_fresh(root)
    except BuildError as error:
        raise WorktreeAffinityError(
            f"the active worktree's build is stale: {error}. Run python3 scripts/concorde.py build "
            "in this worktree from a maintenance session, then open a fresh agent if any changed "
            "project Skill was already loaded as instructions.\n\n"
            + _handoff(root, maintenance=True)
        ) from error
    return {
        "project_root": str(root),
        "loaded_worktree": str(loaded_root),
        "integration": integration,
        "capability": capability,
        "surface_match": True,
        "worktree_head": active_boundary.head,
    }
