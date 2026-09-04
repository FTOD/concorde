#!/usr/bin/env python3
"""Launch the installer-owned official Understand Anything Viewer offline."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence


_SEMVER = re.compile(r"^v?([0-9]+)\.([0-9]+)\.([0-9]+)(?:[-+].*)?$")


class ViewerLaunchError(ValueError):
    """The installed official Viewer or its raw graph input is unsafe or unavailable."""


def _safe_relative(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise ViewerLaunchError(f"{field} must be a string")
    candidate = PurePosixPath(value)
    if not value or candidate.is_absolute() or ".." in candidate.parts or "\\" in value:
        raise ViewerLaunchError(f"{field} must be a safe project-relative path: {value!r}")
    return candidate.as_posix()


def _json_object(path: Path, label: str) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise ViewerLaunchError(f"{label} must be one real file: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ViewerLaunchError(f"cannot read {label} {path}: {error}") from error
    if not isinstance(value, dict):
        raise ViewerLaunchError(f"{label} must be one JSON object: {path}")
    return value


def _project_root(value: str) -> Path:
    requested = Path(value).absolute()
    if requested.is_symlink() or not requested.is_dir():
        raise ViewerLaunchError(f"project root must be one real directory: {requested}")
    return requested.resolve()


def _installed_viewer(project: Path) -> tuple[Mapping[str, Any], Path]:
    framework = project / ".concorde/framework"
    manifest_path = project / ".concorde/framework/concorde.json"
    if framework.is_symlink():
        raise ViewerLaunchError(f"installed Concorde framework must not be a symlink: {framework}")
    manifest = _json_object(manifest_path, "installed Concorde manifest")
    viewer = manifest.get("viewer")
    runtime = manifest.get("operation_runtime")
    if not isinstance(viewer, Mapping) or not isinstance(runtime, Mapping):
        raise ViewerLaunchError("installed Concorde manifest omits Viewer runtime identity")
    venv = _safe_relative(runtime.get("venv"), "operation_runtime.venv")
    if venv != ".concorde/.venv":
        raise ViewerLaunchError("installed Concorde manifest has an unsupported runtime path")
    install_relative = _safe_relative(viewer.get("install_relative"), "viewer.install_relative")
    entrypoint = _safe_relative(viewer.get("entrypoint"), "viewer.entrypoint")
    runtime_root = project.joinpath(*PurePosixPath(venv).parts)
    viewer_root = runtime_root.joinpath(*PurePosixPath(install_relative).parts)
    executable = viewer_root.joinpath(*PurePosixPath(entrypoint).parts)
    for path in (project / ".concorde", runtime_root, viewer_root, executable):
        if path.is_symlink():
            raise ViewerLaunchError(f"installed Viewer path must not be a symlink: {path}")
    marker = _json_object(
        runtime_root / ".concorde-runtime.json",
        "installed Concorde runtime marker",
    )
    if not (
        marker.get("schema_version") == 2
        and marker.get("owner") == "concorde"
        and marker.get("viewer_version") == viewer.get("version")
        and marker.get("viewer_entrypoint") == viewer.get("entrypoint")
    ):
        raise ViewerLaunchError(
            "installed official Viewer runtime identity is stale; rerun the Concorde installer with --apply"
        )
    if not executable.is_file():
        raise ViewerLaunchError(
            "installed official Viewer is missing; rerun the Concorde installer with --apply"
        )
    package_name = viewer.get("package")
    version = viewer.get("version")
    if not isinstance(package_name, str) or not isinstance(version, str):
        raise ViewerLaunchError("installed Viewer manifest identity is invalid")
    package = _json_object(
        viewer_root / "node_modules" / package_name / "package.json",
        "installed official Viewer package",
    )
    if package.get("name") != package_name or package.get("version") != version:
        raise ViewerLaunchError("installed official Viewer package identity is mismatched")
    return viewer, executable


def _raw_graph(project: Path, viewer: Mapping[str, Any]) -> Path:
    paths = viewer.get("graph_paths")
    if not isinstance(paths, list) or len(paths) != 2:
        raise ViewerLaunchError("installed Viewer manifest graph locations are invalid")
    for index, value in enumerate(paths):
        relative = _safe_relative(value, f"viewer.graph_paths[{index}]")
        candidate = project.joinpath(*PurePosixPath(relative).parts)
        current = project
        unsafe = False
        for part in PurePosixPath(relative).parts:
            current /= part
            if current.is_symlink():
                unsafe = True
                break
        if unsafe:
            raise ViewerLaunchError(f"UA graph path must not contain a symlink: {relative}")
        if candidate.is_file():
            graph = _json_object(candidate, "raw Understand Anything graph")
            if graph.get("tool") == "explore" or (
                graph.get("schema_version") == 2
                and isinstance(graph.get("result"), Mapping)
                and "alignment" in graph["result"]
            ):
                raise ViewerLaunchError(
                    "Concorde explore JSON is not Viewer input; pass the project containing the raw "
                    ".ua/knowledge-graph.json instead"
                )
            if not (
                isinstance(graph.get("version"), str)
                and isinstance(graph.get("project"), Mapping)
                and isinstance(graph.get("nodes"), list)
                and isinstance(graph.get("edges"), list)
            ):
                raise ViewerLaunchError(
                    f"raw Understand Anything graph has an unsupported root shape: {relative}"
                )
            return candidate
    raise ViewerLaunchError(
        "no raw Understand Anything graph found; expected .ua/knowledge-graph.json "
        "or legacy .understand-anything/knowledge-graph.json"
    )


def _node() -> str:
    executable = shutil.which("node")
    if executable is None:
        raise ViewerLaunchError("Node.js >=18 is required to run the official Viewer")
    result = subprocess.run(
        [executable, "--version"],
        text=True,
        capture_output=True,
        check=False,
    )
    value = (result.stdout or result.stderr).strip()
    match = _SEMVER.fullmatch(value)
    if result.returncode or match is None:
        raise ViewerLaunchError(f"cannot determine the installed Node.js version: {value!r}")
    version = tuple(int(item) for item in match.groups())
    if version < (18, 0, 0):
        raise ViewerLaunchError(f"official Viewer requires Node.js >=18, observed {value}")
    return executable


def _port(value: str) -> int:
    try:
        port = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("port must be an integer between 0 and 65535") from error
    if port < 0 or port > 65535:
        raise argparse.ArgumentTypeError("port must be an integer between 0 and 65535")
    return port


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="run-viewer")
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--port", type=_port)
    parser.add_argument("--no-open", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = create_parser().parse_args(argv)
    try:
        project = _project_root(arguments.project_root)
        viewer, entrypoint = _installed_viewer(project)
        graph = _raw_graph(project, viewer)
        command = [_node(), str(entrypoint), str(project)]
        if arguments.port is not None:
            command.extend(("--port", str(arguments.port)))
        if arguments.no_open:
            command.append("--no-open")
        print(f"Launching official Understand Anything Viewer for {graph}", flush=True)
        try:
            return subprocess.run(command, cwd=project, check=False).returncode
        except KeyboardInterrupt:
            return 130
    except (ViewerLaunchError, OSError) as error:
        print(f"CONCORDE VIEWER FAILED: {error}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
