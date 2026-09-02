#!/usr/bin/env python3
"""Check or refresh this checkout's generated Codex and Claude agent surfaces."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from concorde.agent_assets import AgentAssetError, render_projection  # noqa: E402
from concorde.skill_assets import SkillAssetError, render_capabilities  # noqa: E402


def _sha256(content: bytes) -> str:
    return "sha256:" + hashlib.sha256(content).hexdigest()


def expected_outputs(root: Path) -> dict[str, bytes]:
    outputs: dict[str, bytes] = {}
    for integration in ("codex", "claude"):
        rendered = render_capabilities(root, integration, "")
        rendered.update(render_projection(root / "agent-assets/reflections", integration))
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
    parser.add_argument("tool", choices=["status", "apply"])
    parser.add_argument("--project-root", default=str(REPOSITORY_ROOT))
    parser.add_argument("--format", choices=["text", "json"], default="text")
    arguments = parser.parse_args()
    root = Path(arguments.project_root).resolve()
    try:
        desired = expected_outputs(root)
        actions = inspect(root, desired)
        if arguments.tool == "apply":
            apply(root, desired, actions)
            actions = inspect(root, desired)
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
        return 0 if not drift or arguments.tool == "status" else 1
    except (AgentAssetError, SkillAssetError, ValueError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
