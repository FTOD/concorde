#!/usr/bin/env python3
"""Materialize Concorde's canonical root commands for one coding-agent integration."""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT / "src"))

from concorde.command_assets import CommandAssetError, render_commands  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(prog="render-command-surfaces")
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--package-root", default=str(PACKAGE_ROOT))
    parser.add_argument("--integration", choices=["codex", "claude"], required=True)
    parser.add_argument("--framework-prefix", default="")
    arguments = parser.parse_args()
    project_root = Path(arguments.project_root).resolve()
    package_root = Path(arguments.package_root).resolve()
    try:
        rendered = render_commands(package_root, arguments.integration, arguments.framework_prefix)
    except CommandAssetError as error:
        parser.error(str(error))
    for relative, content in rendered.items():
        target = project_root / relative
        if target.is_symlink() or (target.exists() and not target.is_file()):
            parser.error(f"refusing unsafe command target: {relative}")
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=target.parent, prefix=".concorde-command-", delete=False) as handle:
            staged = Path(handle.name)
            handle.write(content.encode("utf-8"))
        try:
            staged.replace(target)
        finally:
            staged.unlink(missing_ok=True)
        target.chmod(0o644)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
