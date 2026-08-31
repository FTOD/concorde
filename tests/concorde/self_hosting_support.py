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
SKILL_ROOTS = {"codex": ".agents/skills", "claude": ".claude/skills"}


def load_self_hosting():
    spec = importlib.util.spec_from_file_location("concorde_self_hosting", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def integration_init_arguments(integration: str) -> list[str]:
    arguments = [
        "init",
        "--here",
        "--force",
        "--ignore-agent-tools",
        "--integration",
        integration,
    ]
    if integration == "codex":
        arguments.append("--integration-options=--skills")
    arguments.extend(["--script", "sh"])
    return arguments


def skill_root(root: Path, integration: str) -> Path:
    return root / SKILL_ROOTS[integration]


def skill_file(root: Path, integration: str, command: str) -> Path:
    return skill_root(root, integration) / command.replace(".", "-") / "SKILL.md"


def initialize_checkout(root: Path, integration: str = "codex") -> None:
    root.mkdir(parents=True, exist_ok=True)
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    environment.pop("SPECIFY_FEATURE_DIRECTORY", None)
    completed = subprocess.run(
        ["specify", *integration_init_arguments(integration)],
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


def load_preserved_fixture(path: Path) -> dict[str, str]:
    """Read a preserved-files fixture strictly.

    The object keys are the seeded relative paths, so they define preservation coverage rather
    than incidental data. Ordinary JSON parsing keeps the last value of a repeated key silently;
    here a repeated key or non-string content fails the fixture instead (R-039).
    """

    def reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
        value: dict[str, object] = {}
        for key, item in pairs:
            if key in value:
                raise AssertionError(f"Self-hosting preserved-files fixture repeats {key!r}.")
            value[key] = item
        return value

    value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicate_keys)
    if not isinstance(value, dict) or not all(isinstance(key, str) and isinstance(item, str) for key, item in value.items()):
        raise AssertionError("Self-hosting preserved-files fixture must be a string-to-string object.")
    return value


def preserved_sentinels() -> dict[str, str]:
    return load_preserved_fixture(PRESERVED_FIXTURE)


def select_integration(root: Path, integration: str) -> None:
    """Make ``integration`` active the way a maintainer does by hand: rewrite both host records."""
    integration_path = root / ".specify/integration.json"
    state = json.loads(integration_path.read_text(encoding="utf-8"))
    state["integration"] = integration
    state["default_integration"] = integration
    installed = state.setdefault("installed_integrations", [])
    if integration not in installed:
        installed.append(integration)
    state.setdefault("integration_settings", {})[integration] = {"script": "sh", "invoke_separator": "-"}
    integration_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    options_path = root / ".specify/init-options.json"
    options = json.loads(options_path.read_text(encoding="utf-8"))
    options["ai"] = integration
    options["integration"] = integration
    options_path.write_text(json.dumps(options, indent=2) + "\n", encoding="utf-8")


def surface_tree(root: Path, relative: str) -> dict[str, tuple[str, str]]:
    """Every entry below ``relative`` with its representation: ('symlink', link value) or ('file', sha256)."""
    base = root / relative
    result: dict[str, tuple[str, str]] = {}
    if not base.is_dir():
        return result
    for path in sorted(base.rglob("*")):
        key = path.relative_to(root).as_posix()
        if path.is_symlink():
            result[key] = ("symlink", os.readlink(path))
        elif path.is_file():
            result[key] = ("file", hashlib.sha256(path.read_bytes()).hexdigest())
    return result
