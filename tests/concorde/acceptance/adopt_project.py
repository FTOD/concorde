"""A temporary consumer project that the developer installs Concorde into and the user session drives.

The installer runs as the developer runs it, ``scripts/install-concorde.py --apply``, with an
offline wheelhouse (``adopt_wheelhouse``) and the offline npm stand-in of the installer tests, so
the managed runtime holds its own copies of the locked dependencies. Capabilities are called the
way the user session's ``concorde`` tool calls them: the installed launcher
``.concorde/framework/scripts/run-operation.py`` reads one invocation envelope on stdin and answers
one result envelope. Nothing contacts a network or a model.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from concorde.spec.initialize import apply_project_proposal, project_proposal
from concorde.spec.typed_data import type_version, typed
from tests.concorde.acceptance.adopt_wheelhouse import wheelhouse
from tests.concorde.support.environment import child_environment
from tests.concorde.support.managed_runtime import runtime_install_environment
from tests.concorde.support.paths import REPOSITORY_ROOT

INSTALLER = REPOSITORY_ROOT / "scripts/install-concorde.py"
FRAMEWORK = ".concorde/framework"
LAUNCHER = FRAMEWORK + "/scripts/run-operation.py"
RUNTIME_PYTHON = ".concorde/.venv/bin/python"
DEFAULT_CONFIGURATION = typed(
    "concorde-operation-configuration",
    {"model": "openai-codex/gpt-6-astra", "thinking": "medium"},
)


def configuration(**data) -> dict:
    return typed("concorde-operation-configuration", data)


class ConsumerProject:
    """``unittest.TestCase`` mixin: a committed Git project named ``consumer`` in fresh scratch."""

    def setUp(self):
        super().setUp()
        scratch = tempfile.TemporaryDirectory(prefix="concorde-adopt-")
        self.addCleanup(scratch.cleanup)
        self.scratch = Path(scratch.name).resolve()
        # Every temporary directory a child process makes stays inside this test's scratch.
        self.tmp = self.scratch / "tmp"
        self.tmp.mkdir()
        self.target = self.scratch / "consumer"
        self.git("init", "--quiet", str(self.target), cwd=self.scratch)
        (self.target / "README.md").write_text("# Consumer\n\nAn existing project.\n")
        self.git("add", "README.md")
        self.git(
            "-c",
            "user.name=Developer",
            "-c",
            "user.email=developer@example.invalid",
            "commit",
            "--quiet",
            "-m",
            "Existing project",
        )

    # -- the developer ------------------------------------------------------------------

    def git(self, *arguments: str, cwd: Path | None = None) -> str:
        return subprocess.run(
            ["git", *arguments],
            cwd=cwd or self.target,
            check=True,
            capture_output=True,
            text=True,
        ).stdout

    def install_environment(self) -> dict[str, str]:
        wheels = self.scratch / "wheels"
        if not wheels.is_dir():
            wheelhouse(wheels)
        return {**runtime_install_environment(wheels), "TMPDIR": str(self.tmp)}

    def run_installer(self) -> tuple[int, dict]:
        """``install-concorde.py --target <consumer> --apply --format json`` as a process."""
        process = subprocess.run(
            [
                sys.executable,
                str(INSTALLER),
                "--target",
                str(self.target),
                "--apply",
                "--format",
                "json",
            ],
            capture_output=True,
            text=True,
            check=False,
            env=self.install_environment(),
            timeout=600,
        )
        try:
            payload = json.loads(process.stdout)
        except ValueError:
            raise AssertionError(
                f"installer printed no JSON: {process.stdout!r} {process.stderr!r}"
            ) from None
        return process.returncode, payload

    def install(self) -> dict:
        code, payload = self.run_installer()
        if code != 0 or payload.get("status") != "installed":
            raise AssertionError(f"installation failed: {payload}")
        return payload

    def initialize(self, value: dict = DEFAULT_CONFIGURATION) -> None:
        """Initialize the installed project with the installed package's own initializer."""
        framework = self.target / FRAMEWORK
        apply_project_proposal(
            self.target,
            framework,
            project_proposal(self.target, framework, "Consumer", value),
        )

    # -- the user session ---------------------------------------------------------------

    def call(
        self,
        operation: str,
        data: dict,
        *,
        mode: str = "execute",
        envelope_configuration: dict | None = None,
        checked: bool = True,
    ) -> dict:
        """One capability call through the installed launcher, as the ``concorde`` tool makes it.

        ``checked=False`` sends the request data unchecked, as a session may send a value the
        capability must refuse.
        """
        request = f"{operation}-request"
        invocation = {
            "type_id": "concorde-operation-invocation",
            "schema_version": 3,
            "operation_id": operation,
            "mode": mode,
            "configuration": envelope_configuration,
            "input": typed(request, data)
            if checked
            else {
                "type_id": request,
                "schema_version": type_version(request),
                "data": data,
            },
        }
        process = subprocess.run(
            [sys.executable, str(self.target / LAUNCHER), operation],
            cwd=self.target,
            input=json.dumps(invocation),
            capture_output=True,
            text=True,
            check=False,
            env=child_environment(TMPDIR=str(self.tmp)),
            timeout=600,
        )
        try:
            return json.loads(process.stdout)
        except ValueError:
            raise AssertionError(
                f"launcher printed no envelope: {process.stdout!r} {process.stderr!r}"
            ) from None

    # -- observations -------------------------------------------------------------------

    def read_json(self, relative: str) -> dict:
        return json.loads((self.target / relative).read_text())

    def tree(self, *, exclude: tuple[str, ...] = (".git",)) -> dict[str, str]:
        """Every file below the project (symbolic links by target) with a digest of its bytes."""
        result = {}
        for path in sorted(self.target.rglob("*")):
            relative = path.relative_to(self.target).as_posix()
            if any(
                relative == prefix or relative.startswith(prefix + "/")
                for prefix in exclude
            ) or ("__pycache__" in path.parts):
                continue
            if path.is_symlink():
                result[relative] = "link:" + str(path.readlink())
            elif path.is_file():
                result[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
        return result

    def worktrees(self) -> list[str]:
        return [
            line.removeprefix("worktree ")
            for line in self.git("worktree", "list", "--porcelain").splitlines()
            if line.startswith("worktree ")
        ]

    def runs(self) -> list[str]:
        directory = self.target / ".concorde/runs"
        return sorted(p.name for p in directory.iterdir()) if directory.is_dir() else []
