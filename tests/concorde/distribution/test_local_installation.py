"""Full local installation service, without a model call or a shared Python environment."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from concorde.distribution import installation as installer
from concorde.distribution import managed_runtime
from concorde.distribution.local_installation import (
    admit_package,
    ensure_installation,
    installation_lock,
    verify_installation,
)
from concorde.spec.initialize import apply_project_proposal, project_proposal
from concorde.spec.verification import verifies
from tests.concorde.support.environment import (
    child_environment,
    scrubbed_process_environment,
)
from tests.concorde.support.managed_runtime import seed_npm_cache
from tests.concorde.support.paths import REPOSITORY_ROOT


class PreservedProjectTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.package = installer.load_package(REPOSITORY_ROOT)

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="concorde-install-project-")
        self.addCleanup(temporary.cleanup)
        self.target = Path(temporary.name)
        # These cases isolate ownership/transaction mechanics. The separate native case
        # below provisions real independent Python packages and real locked TypeBox.
        for name, value in (
            (
                "plan_runtime",
                {
                    "path": ".concorde/.venv",
                    "role": "runtime",
                    "action": "unchanged",
                    "sha256": "unused",
                },
            ),
            ("provision_runtime", {"path": ".concorde/.venv"}),
        ):
            mock = patch.object(installer, name, return_value=value)
            mock.start()
            self.addCleanup(mock.stop)

    def apply(self):
        actions, desired, _ = installer.installation_plan(
            self.target, self.package, preserve_project=True
        )
        return installer.apply_plan(
            self.target, self.package, actions, desired, preserve_project=True
        )

    def seed_protocol(self):
        for relative, (content, role) in installer.desired_outputs(
            self.package
        ).items():
            if role == "protocol":
                path = self.target / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)

    @verifies("scenario.distribution.install-preserve-project")
    def test_inherited_and_user_guidance_and_accepted_protocol_remain_unowned(self):
        self.seed_protocol()
        agents = self.target / "AGENTS.md"
        agents.write_bytes(installer.guidance.entry() + b"\nUser text\r\n")
        agents.chmod(0o640)
        (self.target / "NOTES.md").write_bytes(b"user notes\n")
        config = self.target / ".concorde/config.json"
        config.write_bytes(b'{"protocol": "accepted project binding"}\n')
        before = {
            p.relative_to(self.target): p.read_bytes()
            for p in self.target.rglob("*")
            if p.is_file()
        }
        self.assertEqual("installed", self.apply())
        for path, content in before.items():
            self.assertEqual(content, (self.target / path).read_bytes())
        self.assertEqual(0o640, agents.stat().st_mode & 0o777)
        receipt = json.loads((self.target / installer.RECEIPT_PATH).read_text())
        owned = {item["path"] for item in receipt["outputs"]}
        self.assertFalse(owned.intersection(str(p) for p in before))
        self.assertTrue(receipt["preserve_project"])
        self.assertIn(
            {"path": "AGENTS.md", "role": "protocol-guidance"}, receipt["preserved"]
        )
        self.assertEqual("unchanged", self.apply())
        # An existing arbitrary root file is not rewritten even to add a missing block.
        agents.write_bytes(b"only the project's own rules\n")
        self.assertEqual("unchanged", self.apply())
        self.assertEqual(b"only the project's own rules\n", agents.read_bytes())

    @verifies("scenario.distribution.task-subagents")
    def test_tester_owned_update_protects_edits(self):
        self.apply()
        tester = self.target / ".pi/agents/tester.md"
        original = tester.read_bytes()
        self.assertFalse((self.target / ".pi/agents/maintenance-worker.md").exists())
        for source_only in (
            ".concorde/framework/prompts/task-subagent/source",
            ".concorde/framework/prompts/user-session",
        ):
            self.assertFalse((self.target / source_only).exists())
        self.assertEqual("unchanged", self.apply())
        self.assertEqual(original, tester.read_bytes())
        tester.write_text("user edit")
        with self.assertRaisesRegex(installer.InstallError, "ownership conflicts"):
            self.apply()
        self.assertEqual("user edit", tester.read_text())

    @verifies("scenario.distribution.install-preserve-project")
    def test_missing_project_assets_seed_owned_entries_and_repeat_retains_ownership(
        self,
    ):
        self.apply()
        before = (self.target / installer.RECEIPT_PATH).read_bytes()
        self.assertEqual("unchanged", self.apply())
        self.assertEqual(before, (self.target / installer.RECEIPT_PATH).read_bytes())
        receipt = json.loads(before)
        self.assertIn("AGENTS.md", {item["path"] for item in receipt["outputs"]})
        self.assertIn(
            ".concorde/protocol/manifest.json",
            {item["path"] for item in receipt["outputs"]},
        )
        (self.target / "AGENTS.md").write_bytes(
            installer.guidance.entry().replace(b"Read", b"Changed")
        )
        with self.assertRaisesRegex(installer.InstallError, "modified owned"):
            self.apply()
        self.assertEqual(before, (self.target / installer.RECEIPT_PATH).read_bytes())

    @verifies("scenario.distribution.install-preserve-project")
    def test_partial_unsafe_and_different_protocol_are_not_silently_completed_or_accepted(
        self,
    ):
        protocol = self.target / installer.PROTOCOL_ROOT
        protocol.mkdir(parents=True)
        (protocol / "principles.md").write_text("partial")
        with self.assertRaises(installer.InstallError):
            self.apply()
        self.assertFalse((self.target / ".pi").exists())
        self.seed_protocol()
        manifest = protocol / "manifest.json"
        value = json.loads(manifest.read_text())
        value["version"] = "different-accepted-version"
        manifest.write_text(json.dumps(value))
        before = manifest.read_bytes()
        # Complete but incompatible project bundle remains unchanged. Installation is not admission.
        self.apply()
        self.assertEqual(before, manifest.read_bytes())
        self.assertFalse((self.target / ".concorde/config.json").exists())
        (protocol / "principles.md").unlink()
        with self.assertRaisesRegex(installer.InstallError, "partial"):
            self.apply()

    @verifies("scenario.distribution.install-local-failure")
    def test_preserved_project_and_old_owned_outputs_survive_failed_install(self):
        (self.target / "AGENTS.md").write_text("project rules")
        self.seed_protocol()
        before = {
            str(p.relative_to(self.target)): p.read_bytes()
            for p in self.target.rglob("*")
            if p.is_file()
        }
        with patch.object(
            installer, "provision_runtime", side_effect=OSError("injected")
        ):
            with self.assertRaisesRegex(OSError, "injected"):
                self.apply()
        after = {
            str(p.relative_to(self.target)): p.read_bytes()
            for p in self.target.rglob("*")
            if p.is_file()
        }
        self.assertEqual(before, after)
        self.apply()
        owned = self.target / ".pi/extensions/concorde-session.ts"
        owned.write_text("locally modified")
        with self.assertRaisesRegex(installer.InstallError, "ownership conflicts"):
            self.apply()
        self.assertEqual("locally modified", owned.read_text())

    @verifies("scenario.distribution.install-preserve-project")
    def test_owned_protocol_edits_and_missing_differently_bound_protocol_are_refused(
        self,
    ):
        self.apply()
        receipt = (self.target / installer.RECEIPT_PATH).read_bytes()
        manifest = self.target / installer.PROTOCOL_ROOT / "manifest.json"
        value = json.loads(manifest.read_text())
        value["version"] = "locally changed"
        manifest.write_text(json.dumps(value))
        with self.assertRaisesRegex(installer.InstallError, "modified owned Protocol"):
            self.apply()
        self.assertEqual(receipt, (self.target / installer.RECEIPT_PATH).read_bytes())
        with tempfile.TemporaryDirectory() as raw:
            target = Path(raw)
            (target / ".concorde").mkdir()
            config = target / ".concorde/config.json"
            config.write_text(
                json.dumps(
                    {"protocol": {"version": "old", "digest": "sha256:" + "0" * 64}}
                )
            )
            with self.assertRaisesRegex(
                installer.InstallError, "different accepted binding"
            ):
                installer.installation_plan(target, self.package, preserve_project=True)
            self.assertFalse((target / installer.PROTOCOL_ROOT).exists())

    @verifies("scenario.distribution.install-local-failure")
    def test_concurrent_installer_and_symlink_targets_are_refused(self):
        with installation_lock(self.target):
            with self.assertRaisesRegex(installer.InstallError, "another installer"):
                with installation_lock(self.target):
                    self.fail("lock must exclude another writer")
        # A released lock is reusable, including after an exception.
        with installation_lock(self.target):
            pass
        alias = self.target / "alias"
        alias.symlink_to(self.target, target_is_directory=True)
        with self.assertRaisesRegex(installer.InstallError, "canonical"):
            verify_installation(alias)


class NativeLocalInstallationTests(unittest.TestCase):
    @verifies(
        "scenario.distribution.install-local-worktree",
        "scenario.distribution.install-local-failure",
    )
    def test_source_and_installed_provider_supply_independent_git_worktree_installs(
        self,
    ):
        with tempfile.TemporaryDirectory(prefix="concorde-local-installs-") as raw:
            root = Path(raw)
            wheels = os.environ.get("CONCORDE_TEST_WHEELHOUSE")
            if wheels is None:
                # Acquire ordinary wheels, never copy or link an existing runtime. CI can
                # preseed this external wheelhouse to run the same test wholly offline.
                wheels = str(root / "wheels")
                download_env = root / "download-environment"
                subprocess.run(
                    [sys.executable, "-m", "venv", str(download_env)],
                    check=True,
                    capture_output=True,
                )
                subprocess.run(
                    [
                        str(managed_runtime.runtime_python(download_env)),
                        "-m",
                        "pip",
                        "download",
                        "--disable-pip-version-check",
                        "--dest",
                        wheels,
                        "--requirement",
                        str(REPOSITORY_ROOT / "scripts/requirements.lock"),
                    ],
                    check=True,
                    capture_output=True,
                )
            environment = {
                "PIP_NO_INDEX": "1",
                "PIP_FIND_LINKS": wheels,
                "PYTHONNOUSERSITE": "1",
                "NPM_CONFIG_OFFLINE": "true",
                "PIP_DISABLE_PIP_VERSION_CHECK": "1",
            }
            # Offline installs below read the npm cache in use; fill it from local bytes first.
            seed_npm_cache(child_environment(**environment), REPOSITORY_ROOT)
            primary = root / "project"
            primary.mkdir()

            def git(*args):
                return subprocess.run(
                    ["git", "-C", str(primary), *args],
                    check=True,
                    capture_output=True,
                    text=True,
                ).stdout

            git("init", "-q")
            git("config", "user.name", "Installation Test")
            git("config", "user.email", "installation@example.invalid")
            (primary / ".gitignore").write_text(
                ".pi/\n.concorde/framework/\n.concorde/.venv/\n.concorde/install*\n"
            )
            with scrubbed_process_environment(**environment):
                source = admit_package(REPOSITORY_ROOT)
                first = ensure_installation(primary, source, bootstrap=True)
                # Deterministic fixture initialization, not an Operation or model call.
                proposal = project_proposal(
                    primary,
                    first.framework,
                    "Install fixture",
                    {
                        "type_id": "concorde-operation-configuration",
                        "schema_version": 2,
                        "data": {},
                    },
                )
                apply_project_proposal(primary, first.framework, proposal)
                project_bytes = {
                    item["path"]: (primary / item["path"]).read_bytes()
                    for item in proposal["files"]
                }
                # Only ordinary project data and Protocol/guidance are committed.
                git("add", ".")
                git("commit", "-qm", "consumer project")
                target = root / "worktree"
                git("worktree", "add", "-qb", "candidate", str(target))
                self.assertFalse((target / installer.RECEIPT_PATH).exists())
                before = (target / "AGENTS.md").read_bytes()
                installed_source = admit_package(first.framework)
                self.assertEqual(source.identity, installed_source.identity)
                with self.assertRaisesRegex(
                    installer.InstallError, "receipt is missing"
                ):
                    ensure_installation(target, installed_source)
                with self.assertRaisesRegex(
                    installer.InstallError, "admitted package changed"
                ):
                    ensure_installation(
                        target,
                        replace(installed_source, digest="sha256:" + "0" * 64),
                        bootstrap=True,
                    )
                with patch.object(
                    managed_runtime,
                    "_install_pi",
                    side_effect=managed_runtime.ManagedRuntimeError(
                        "injected acquisition failure"
                    ),
                ):
                    with self.assertRaisesRegex(
                        installer.InstallError, "injected acquisition"
                    ):
                        ensure_installation(target, installed_source, bootstrap=True)
                self.assertFalse((target / installer.RECEIPT_PATH).exists())
                self.assertFalse((target / ".concorde/.venv").exists())
                self.assertEqual(before, (target / "AGENTS.md").read_bytes())
                second = ensure_installation(target, installed_source, bootstrap=True)
                self.assertEqual(before, (target / "AGENTS.md").read_bytes())
                self.assertTrue(second.protocol_matches_package)
                self.assertEqual(source.identity, second.package.identity)
                for path, content in project_bytes.items():
                    self.assertEqual(content, (target / path).read_bytes())
                self.assertNotEqual(first.python, second.python)
                # No acquisition or marker/receipt refresh occurs during verified reuse.
                snapshot = {
                    p: p.read_bytes()
                    for p in (
                        second.receipt,
                        target / ".concorde/.venv/.concorde-runtime.json",
                    )
                }
                with (
                    patch.object(
                        installer,
                        "apply_plan",
                        side_effect=AssertionError("must not reinstall"),
                    ),
                    patch.object(
                        managed_runtime,
                        "provision_runtime",
                        side_effect=AssertionError("must not provision"),
                    ),
                ):
                    self.assertEqual(
                        second,
                        ensure_installation(target, installed_source, bootstrap=True),
                    )
                for path, content in snapshot.items():
                    self.assertEqual(content, path.read_bytes())
                # Remove availability of the provider's runtime entirely. Only system Python/Node
                # and this worktree's own installation may satisfy its verification/imports.
                shutil.rmtree(primary / ".concorde/.venv")
                local = verify_installation(target)
                probe = subprocess.run(
                    [
                        str(local.python),
                        "-I",
                        "-c",
                        "import sys,langgraph.graph,pydantic; print(sys.prefix); print(langgraph.graph.__file__); print(pydantic.__file__)",
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                    cwd=target,
                )
                for line in probe.stdout.splitlines():
                    self.assertTrue(
                        Path(line).is_relative_to(target / ".concorde/.venv"), line
                    )
                # A matching prefix/marker cannot hide an external .pth dependency bridge.
                site = next(
                    (target / ".concorde/.venv/lib").glob("python*/site-packages")
                )
                bridge = site / "foreign-runtime.pth"
                external_dependencies = root / "foreign-dependencies"
                external_dependencies.mkdir()
                bridge.write_text(str(external_dependencies) + "\n")
                with self.assertRaisesRegex(
                    installer.InstallError, "dependency isolation"
                ):
                    verify_installation(target)
                bridge.unlink()
                role_probe = subprocess.run(
                    [
                        str(local.python),
                        "-I",
                        "-c",
                        "import sys,json; sys.path[:0]=sys.argv[1:]; "
                        "import agents; from concorde.harness.worker_profile import load_worker_profiles; "
                        "print(json.dumps({'agents':agents.AGENTS,'task':agents.TASK_SUBAGENTS,"
                        "'domain':list(load_worker_profiles()),'source':agents.__file__}))",
                        str(local.framework),
                        str(local.framework / "src"),
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                    cwd=target,
                )
                discovered = json.loads(role_probe.stdout)
                self.assertEqual(8, len(discovered["agents"]))
                self.assertEqual(["tester"], discovered["task"])
                self.assertEqual(7, len(discovered["domain"]))
                self.assertNotIn("main", discovered["agents"])
                self.assertNotIn("user-session", discovered["agents"])
                self.assertNotIn("maintenance-worker", discovered["agents"])
                self.assertTrue(
                    Path(discovered["source"]).is_relative_to(local.framework)
                )
                self.assertFalse((local.framework / "agents/source").exists())
                shim = local.pi_entry.read_text()
                self.assertIn(
                    "../../.concorde/framework/pi/extensions/concorde-session.ts", shim
                )
                self.assertIn(".concorde/.venv/bin/python", shim)
                # A consumer has the same supported bootstrap; source checkout not needed.
                third = root / "manual-worktree"
                git("worktree", "add", "-qb", "manual", str(third))
                result = subprocess.run(
                    [
                        sys._base_executable,
                        str(local.framework / "scripts/install-concorde.py"),
                        "--target",
                        str(third),
                        "--preserve-project",
                        "--apply",
                        "--format",
                        "json",
                    ],
                    cwd=target,
                    env=child_environment(),
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(0, result.returncode, result.stdout + result.stderr)
                self.assertEqual("installed", json.loads(result.stdout)["status"])
                self.assertEqual(
                    source.identity, verify_installation(third).package.identity
                )
                for worktree in (target, third):
                    tester = (worktree / ".pi/agents/tester.md").read_text()
                    self.assertIn("name: tester", tester)
                    self.assertIn(
                        "../../.concorde/framework/pi/extensions/concorde-tester.ts",
                        tester,
                    )
                    self.assertFalse(
                        (worktree / ".pi/agents/maintenance-worker.md").exists()
                    )
                    for source_only in (
                        ".concorde/framework/prompts/task-subagent/source",
                        ".concorde/framework/prompts/user-session",
                    ):
                        self.assertFalse((worktree / source_only).exists())
                    for path, content in project_bytes.items():
                        self.assertEqual(content, (worktree / path).read_bytes())
                    validation = subprocess.run(
                        [
                            str(
                                managed_runtime.runtime_python(
                                    worktree / ".concorde/.venv"
                                )
                            ),
                            str(
                                worktree
                                / installer.FRAMEWORK_ROOT
                                / "scripts/concorde.py"
                            ),
                            "validate",
                        ],
                        cwd=worktree,
                        capture_output=True,
                        text=True,
                    )
                    self.assertEqual(
                        0, validation.returncode, validation.stdout + validation.stderr
                    )
                    self.assertEqual("success", json.loads(validation.stdout)["status"])
                    self.assertFalse((worktree / ".concorde/status").exists())
                    self.assertFalse((worktree / ".concorde/runs").exists())
                # Corrupt owned framework: neither a same-version label nor bootstrap bypasses it.
                local.launcher.write_text("modified owned launcher")
                with self.assertRaises(installer.InstallError):
                    verify_installation(target)
                with self.assertRaises(installer.InstallError):
                    ensure_installation(
                        target, admit_package(REPOSITORY_ROOT), bootstrap=True
                    )
                self.assertEqual("modified owned launcher", local.launcher.read_text())


if __name__ == "__main__":
    unittest.main()
