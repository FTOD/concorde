"""Isolated Spec Kit project and lifecycle acceptance helpers."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Iterable


class SpecifyProject:
    def __init__(self, root: Path, integration: str = "codex", skills: bool = True, home: Path | None = None):
        self.root = root.resolve()
        self.integration = integration
        self.skills = skills
        self.home = home.resolve() if home else None

    def run(self, *arguments: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment.pop("SPECIFY_FEATURE_DIRECTORY", None)
        if self.home:
            environment["HOME"] = str(self.home)
        result = subprocess.run(
            ["specify", *arguments],
            cwd=self.root,
            text=True,
            capture_output=True,
            env=environment,
        )
        if check and result.returncode:
            raise AssertionError(
                f"specify {' '.join(arguments)} failed ({result.returncode})\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
            )
        return result

    def initialize(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        arguments = ["init", "--here", "--force", "--ignore-agent-tools", "--integration", self.integration]
        if self.skills:
            arguments.append("--integration-options=--skills")
        self.run(*arguments)

    def register_catalogs(self, base_url: str) -> None:
        self.run("extension", "catalog", "add", f"{base_url}/extensions.json", "--name", "concorde-dev", "--install-allowed")
        self.run("preset", "catalog", "add", f"{base_url}/presets.json", "--name", "concorde-dev", "--install-allowed")
        self.run("bundle", "catalog", "add", f"{base_url}/bundles.json", "--id", "concorde-dev", "--policy", "install-allowed")

    def clear_catalog_caches(self) -> None:
        for path in sorted(self.root.glob(".specify/**/.cache/*")):
            if path.is_file():
                path.unlink()

    def json(self, *arguments: str) -> object:
        return json.loads(self.run(*arguments).stdout)

    def source_hashes(self, roots: Iterable[str] = (".concorde", "specs")) -> dict[str, str]:
        hashes: dict[str, str] = {}
        for name in roots:
            directory = self.root / name
            if not directory.exists():
                continue
            for path in sorted(directory.rglob("*")):
                if path.is_file():
                    hashes[path.relative_to(self.root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
        return hashes

    def registry_snapshot(self) -> dict[str, object]:
        snapshot: dict[str, object] = {}
        for relative in (
            ".specify/bundles/installed.json",
            ".specify/extensions/.registry",
            ".specify/presets/.registry",
        ):
            path = self.root / relative
            if path.is_file():
                snapshot[relative] = json.loads(path.read_text(encoding="utf-8"))
        return snapshot
