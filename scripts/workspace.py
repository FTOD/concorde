#!/usr/bin/env python3
"""Portable JSON adapter for selected Concorde feature paths."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT / "src"))

from concorde.understanding.feature_workspace import (  # noqa: E402
    WorkspaceError,
    persist_selection,
    phase_target,
    resolve_selected_workspace,
)


def main() -> int:
    parser = argparse.ArgumentParser(prog="concorde-workspace")
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--feature-path")
    parser.add_argument("--feature-id")
    parser.add_argument("--phase")
    parser.add_argument("--persist", action="store_true")
    arguments = parser.parse_args()
    try:
        paths = resolve_selected_workspace(
            arguments.project_root,
            arguments.feature_path,
            allow_missing_feature=arguments.phase == "specify",
            planned_feature_id=arguments.feature_id,
        )
        status = (
            persist_selection(
                arguments.project_root,
                paths.feature_path,
                allow_missing_feature=arguments.phase == "specify",
                planned_feature_id=arguments.feature_id,
            )
            if arguments.persist
            else "resolved"
        )
        payload = {"schema_version": 13, "status": status, "workspace": paths.to_dict()}
        if arguments.phase:
            payload["phase"] = arguments.phase
            payload["phase_root"] = phase_target(paths, arguments.phase)
    except WorkspaceError as error:
        payload = {"schema_version": 13, "status": "invalid", "error": str(error)}
        print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
        return 1
    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
