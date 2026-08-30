"""Disposable Concorde checkout helpers for Feature 004."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
from pathlib import Path

from tests.concorde.support.paths import REPOSITORY_ROOT


SCRIPT = REPOSITORY_ROOT / "scripts/development/self-host-concorde.py"
PRESERVED_FIXTURE = REPOSITORY_ROOT / "tests/concorde/fixtures/self-hosting/preserved-files.json"


def load_self_hosting():
    spec = importlib.util.spec_from_file_location("concorde_self_hosting", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def initialize_checkout(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    environment.pop("SPECIFY_FEATURE_DIRECTORY", None)
    completed = subprocess.run(
        [
            "specify",
            "init",
            "--here",
            "--force",
            "--ignore-agent-tools",
            "--integration",
            "codex",
            "--integration-options=--skills",
            "--script",
            "sh",
        ],
        cwd=root,
        text=True,
        capture_output=True,
        env=environment,
    )
    if completed.returncode:
        raise AssertionError(completed.stdout + completed.stderr)
    for relative in ("presets/concorde", "extensions/concorde", "bundles/concorde-bundle"):
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(REPOSITORY_ROOT / relative, destination, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"))
    (root / "scripts/development").mkdir(parents=True)
    shutil.copy2(SCRIPT, root / "scripts/development/self-host-concorde.py")


def run_cli(root: Path, *arguments: str, environment: dict[str, str] | None = None, check: bool = True) -> tuple[subprocess.CompletedProcess[str], dict[str, object]]:
    active_environment = os.environ.copy()
    active_environment.pop("PYTHONPATH", None)
    active_environment.pop("SPECIFY_FEATURE_DIRECTORY", None)
    if environment:
        active_environment.update(environment)
    completed = subprocess.run(
        ["python3", str(root / "scripts/development/self-host-concorde.py"), "--project-root", str(root), *arguments, "--format", "json"],
        cwd=root,
        text=True,
        capture_output=True,
        env=active_environment,
    )
    if check and completed.returncode:
        raise AssertionError(completed.stdout + completed.stderr)
    return completed, json.loads(completed.stdout)


def hash_paths(root: Path, relatives: tuple[str, ...]) -> dict[str, str]:
    result: dict[str, str] = {}
    for relative in relatives:
        base = root / relative
        if base.is_file():
            result[relative] = hashlib.sha256(base.read_bytes()).hexdigest()
        elif base.is_dir():
            for path in sorted(base.rglob("*")):
                if path.is_file():
                    result[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def preserved_sentinels() -> dict[str, str]:
    value = json.loads(PRESERVED_FIXTURE.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or not all(isinstance(key, str) and isinstance(item, str) for key, item in value.items()):
        raise AssertionError("Self-hosting preserved-files fixture must be a string-to-string object.")
    return value
