"""Explicit private instruction selection for a fresh task session.

This returns launch inputs, not a claim that a model loaded them. The caller must
start a fresh, non-forked session with discovery disabled and obey harness depth.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .build import BuildError, check_build, verify_fresh


def _digest(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def select_session(
    candidate: Path, *, mode: str, skill_paths: list[str], runtime: Path
) -> dict:
    """Read exact candidate-built Skills; never resolve a Skill by ambient name."""
    if mode not in {"maintenance", "test", "task"}:
        raise BuildError("unsupported task session mode")
    if candidate.is_symlink() or not candidate.is_dir():
        raise BuildError("candidate must be a real directory")
    root = candidate.resolve()
    if mode == "maintenance" and skill_paths:
        raise BuildError("maintenance sessions must be Skill-free")
    if mode == "test" and not skill_paths:
        raise BuildError("test sessions require explicit candidate Skill paths")
    verify_fresh(root)
    current, differences = check_build(root)
    if not current:
        raise BuildError(f"candidate outputs are stale: {differences}", "stale_build")
    manifest_bytes = (root / "generated/build-manifest.json").read_bytes()
    manifest = json.loads(manifest_bytes)

    def admitted(path: Path, *, built: bool) -> tuple[str, bytes]:
        if not path.is_absolute():
            raise BuildError("selection requires absolute paths, not Skill names")
        try:
            relative = path.relative_to(root).as_posix()
            if path.resolve() != path or any(
                p.is_symlink() for p in (path, *path.parents)
            ):
                raise ValueError("aliased path")
            data = path.read_bytes()
        except (ValueError, OSError) as error:
            raise BuildError(
                f"missing, unreadable or out-of-candidate selection: {path}"
            ) from error
        if built:
            expected = manifest["outputs"].get(relative, {}).get("sha256")
        else:
            expected = manifest["sources"].get(relative)
        if expected != _digest(data):
            raise BuildError(f"unrecorded or stale selection: {path}", "stale_build")
        return relative, data

    runtime_path, runtime_bytes = admitted(runtime, built=False)
    if runtime_path != "scripts/run-operation.py":
        raise BuildError("private runtime must be the candidate launcher")
    skills = []
    for selected in skill_paths:
        relative, data = admitted(Path(selected), built=True)
        if not relative.startswith("generated/session/") or not relative.endswith(
            "/SKILL.md"
        ):
            raise BuildError(
                "only private candidate-built Skill artifacts may be selected"
            )
        try:
            body = data.decode("utf-8")
        except UnicodeError as error:
            raise BuildError(f"unreadable Skill: {selected}") from error
        skills.append({"path": selected, "digest": _digest(data), "body": body})
    return {
        "schema_version": 1,
        "mode": mode,
        "candidate": str(root),
        "fresh_context": True,
        "fork_context": False,
        "discover_skills": False,
        "inherit_skills": False,
        "task_delegation": False,
        "build_digest": _digest(manifest_bytes),
        "runtime": {"path": str(root / runtime_path), "digest": _digest(runtime_bytes)},
        "skills": skills,
        "execution_evidence": None,
    }


def load_selection(root: Path, path: Path) -> dict:
    """Reverify a saved explicit selection at runtime entry; no authority is added."""
    root = root.resolve()
    if (
        not path.is_absolute()
        or path.resolve() != path
        or not path.is_relative_to(root)
    ):
        raise BuildError("session selection must be an exact candidate-local file")
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise BuildError("session selection cannot cross a symlink")
    try:
        value = json.loads(path.read_text())
        expected = select_session(
            root,
            mode=value["mode"],
            skill_paths=[item["path"] for item in value["skills"]],
            runtime=Path(value["runtime"]["path"]),
        )
    except (OSError, UnicodeError, ValueError, KeyError, TypeError) as error:
        raise BuildError(f"invalid session selection: {error}") from error
    if value != expected:
        raise BuildError("session selection provenance changed", "stale_build")
    return value
