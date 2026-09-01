#!/usr/bin/env python3
"""Portable JSON adapter for selected Concorde feature paths."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

EXTENSION_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(EXTENSION_ROOT / "runtime"))

from concorde.feature_workspace import (  # noqa: E402
    WorkspaceError,
    persist_selection,
    phase_target,
    resolve_selected_workspace,
)


def main() -> int:
    parser = argparse.ArgumentParser(prog="concorde-workspace")
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--feature-directory")
    parser.add_argument("--phase")
    parser.add_argument("--persist", action="store_true")
    arguments = parser.parse_args()
    try:
        paths = resolve_selected_workspace(
            arguments.project_root,
            arguments.feature_directory,
            allow_missing_design=arguments.phase == "specify",
        )
        status = persist_selection(arguments.project_root, paths.feature_directory) if arguments.persist else "resolved"
        payload = {"schema_version": 9, "status": status, "workspace": paths.to_dict()}
        if arguments.phase:
            payload["phase"] = arguments.phase
            payload["phase_root"] = phase_target(paths, arguments.phase)
    except WorkspaceError as error:
        payload = {"schema_version": 9, "status": "invalid", "error": str(error)}
        print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
        return 1
    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
