"""The command line: one envelope per subcommand, the package check and the Protocol binding."""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests.concorde.support.environment import child_environment
from tests.concorde.support.paths import REPOSITORY_ROOT, RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.distribution import cli
from concorde.distribution.build import write_build
from concorde.spec.diagnostics import canonical_json, exit_code
from concorde.spec.verification import verifies

CLI = REPOSITORY_ROOT / "scripts/concorde.py"
IGNORED = shutil.ignore_patterns("__pycache__", "*.pyc", "node_modules")


def package_copy(root: Path, *, specs: bool) -> None:
    """Copy the package sources (and optionally the project Specs) into ``root`` and build it."""
    for directory in ("agents", "prompts", "protocol", "operations"):
        shutil.copytree(REPOSITORY_ROOT / directory, root / directory, ignore=IGNORED)
    shutil.copytree(
        REPOSITORY_ROOT / "src/concorde", root / "src/concorde", ignore=IGNORED
    )
    (root / ".concorde").mkdir()
    shutil.copy2(REPOSITORY_ROOT / ".concorde/config.json", root / ".concorde")
    if specs:
        shutil.copytree(REPOSITORY_ROOT / "specs", root / "specs", ignore=IGNORED)
        shutil.copy2(REPOSITORY_ROOT / ".concorde/specs.json", root / ".concorde")
    write_build(root)


def run(root: Path, *arguments: str) -> tuple[subprocess.CompletedProcess, dict]:
    process = subprocess.run(
        [sys.executable, str(CLI), "--project-root", str(root), *arguments],
        capture_output=True,
        text=True,
        env=child_environment(),
        cwd=root,
        timeout=300,
        check=False,
    )
    return process, json.loads(process.stdout)


def sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


class PackageCopyCase(unittest.TestCase):
    """A built copy of the package with the project Specs, shared by a class's tests."""

    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix="concorde-cli-")
        cls.root = Path(cls.temporary.name).resolve()
        package_copy(cls.root, specs=True)

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()


class CommandEnvelopeTests(PackageCopyCase):
    def assert_one_envelope(self, process, payload, tool):
        # Exactly one canonical JSON document on standard output, and the exit code of its status.
        self.assertEqual(canonical_json(payload), process.stdout)
        self.assertEqual(tool, payload["tool"])
        self.assertEqual(exit_code(payload["status"]), process.returncode)

    @verifies("scenario.distribution.cli-envelope")
    def test_every_subcommand_prints_one_envelope_with_the_status_exit_code(self):
        empty = self.root / "empty"
        empty.mkdir(exist_ok=True)
        cases = (
            (self.root, ("build", "--check"), "build", "success"),
            (empty, ("build", "--check"), "build", "invalid"),
            (self.root, ("check-package",), "check-package", "success"),
            (empty, ("check-package",), "check-package", "invalid"),
            (self.root, ("protocol-manifest",), "protocol-manifest", "success"),
            (empty, ("protocol-manifest",), "protocol-manifest", "invalid"),
            (empty, ("validate",), "validate", None),
            (empty, ("registry", "--check"), "registry", None),
            (empty, ("docsite", "--propose"), "docsite", None),
            (empty, ("status",), "status", None),
            (
                self.root,
                ("select-session", "--verify", str(empty / "none.json")),
                "select-session",
                "failed",
            ),
            (self.root, ("build", "--unknown-flag"), "build", "failed"),
            (self.root, ("no-such-subcommand",), "validate", "failed"),
        )
        for root, arguments, tool, status in cases:
            with self.subTest(arguments=arguments, root=root.name):
                process, payload = run(root, *arguments)
                self.assert_one_envelope(process, payload, tool)
                if status is not None:
                    self.assertEqual(status, payload["status"], payload)
                if status == "failed":
                    self.assertEqual(
                        "CONCORDE-RUN-001", payload["findings"][0]["rule_id"]
                    )

    @verifies("scenario.distribution.cli-envelope")
    def test_an_unexpected_exception_becomes_a_failed_envelope(self):
        for tool in ("check-package", "build", "status", "validate"):
            with (
                self.subTest(tool=tool),
                mock.patch.object(
                    cli, "dispatch", side_effect=RuntimeError("unexpected fault")
                ),
                contextlib.redirect_stdout(io.StringIO()) as printed,
            ):
                code = cli.main(["--project-root", str(self.root), tool])
            payload = json.loads(printed.getvalue())
            self.assertEqual(canonical_json(payload), printed.getvalue())
            self.assertEqual(3, code)
            self.assertEqual("failed", payload["status"])
            self.assertEqual(tool, payload["tool"])
            [finding] = payload["findings"]
            self.assertEqual("CONCORDE-RUN-001", finding["rule_id"])
            self.assertIn("unexpected fault", finding["message"])


class PackageCheckTests(PackageCopyCase):
    @verifies("scenario.distribution.package-check")
    def test_a_current_package_passes_without_findings(self):
        process, payload = run(self.root, "check-package")
        self.assertEqual(0, process.returncode, process.stdout)
        self.assertEqual("success", payload["status"])
        self.assertEqual([], payload["findings"])

    @verifies("scenario.distribution.package-check-drift")
    def test_a_stale_build_is_a_distribution_finding_and_is_not_repaired(self):
        with tempfile.TemporaryDirectory(prefix="concorde-cli-drift-") as raw:
            root = Path(raw).resolve()
            shutil.copytree(self.root, root, dirs_exist_ok=True, symlinks=True)
            prompt = root / "prompts/native/planner.md"
            prompt.write_text(prompt.read_text() + "\nA changed sentence.\n")

            def files():
                # Imported declaration modules may leave bytecode caches; sources stay.
                return {
                    path: path.read_bytes()
                    for path in root.rglob("*")
                    if path.is_file() and "__pycache__" not in path.parts
                }

            before = files()
            process, payload = run(root, "check-package")
            self.assertEqual(1, process.returncode, process.stdout)
            self.assertEqual("invalid", payload["status"])
            self.assertIn(
                "CONCORDE-BUILD-FRESH-001",
                {finding["rule_id"] for finding in payload["findings"]},
            )
            self.assertEqual(
                {"module.distribution"},
                {finding["subject_id"] for finding in payload["findings"]},
            )
            self.assertEqual(before, files())


class ProtocolManifestBindTests(unittest.TestCase):
    @verifies("scenario.distribution.protocol-manifest-bind")
    def test_accepting_new_protocol_assets_binds_this_checkout(self):
        with tempfile.TemporaryDirectory(prefix="concorde-protocol-bind-") as raw:
            root = Path(raw).resolve()
            package_copy(root, specs=False)
            chapter = root / "protocol/principles.md"
            chapter.write_text(chapter.read_text() + "\nA new Protocol sentence.\n")
            write_build(root)
            # The tracked manifest no longer matches the fresh build until it is accepted.
            process, payload = run(root, "protocol-manifest")
            self.assertEqual("invalid", payload["status"], payload)
            self.assertEqual(
                ["generated/protocol/principles.md"], payload["result"]["differences"]
            )
            process, payload = run(
                root, "protocol-manifest", "--write", "--bind-project"
            )
            self.assertEqual(0, process.returncode, process.stdout)
            self.assertEqual("success", payload["status"])
            manifest_bytes = (root / "protocol/manifest.json").read_bytes()
            manifest = json.loads(manifest_bytes)
            for asset in manifest["assets"]:
                self.assertEqual(
                    sha256((root / asset["path"]).read_bytes()), asset["digest"]
                )
            config = json.loads((root / ".concorde/config.json").read_text())
            self.assertEqual(
                {"version": manifest["version"], "digest": sha256(manifest_bytes)},
                config["protocol"],
            )
            copy = root / ".concorde/protocol"
            self.assertEqual(manifest_bytes, (copy / "manifest.json").read_bytes())
            for asset in manifest["assets"]:
                installed = copy / asset["path"].removeprefix("generated/protocol/")
                self.assertEqual(asset["digest"], sha256(installed.read_bytes()))
            process, payload = run(root, "protocol-manifest")
            self.assertEqual("success", payload["status"])
            self.assertEqual([], payload["result"]["differences"])


if __name__ == "__main__":
    unittest.main()
