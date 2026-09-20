"""Consumer-root installation contracts without source-checkout AGENTS policy."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tests.concorde.distribution.test_install_concorde import installer
from tests.concorde.support.paths import REPOSITORY_ROOT
from concorde.distribution import protocol_guidance as guidance
from concorde.spec.repository import PROTOCOL_VERSION
from concorde.spec.verification import verifies


class InstallerTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.package = installer.load_package(REPOSITORY_ROOT)

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        # Runtime provisioning has separate native integration coverage. Exercise the real
        # installer transaction/receipt here without downloading dependencies per case.
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

    def install(self, cleanup=False):
        actions, desired, _ = installer.installation_plan(
            self.root, self.package, remove_protocol_guidance=cleanup
        )
        return installer.apply_plan(
            self.root,
            self.package,
            actions,
            desired,
            remove_protocol_guidance=cleanup,
        )


class ProtocolGuidanceTests(InstallerTestCase):
    @verifies("scenario.distribution.install-apply")
    def test_pi_loads_single_protocol_asset_without_checkout_policy(self):
        self.install()
        root = (self.root / "AGENTS.md").read_text()
        self.assertNotIn("Source-Checkout", root)
        self.assertIn(guidance.PROTOCOL, root)
        self.assertIn("Read and follow", root)
        self.assertEqual(
            (self.root / guidance.PROTOCOL).read_bytes(),
            (REPOSITORY_ROOT / "generated/protocol/principles.md").read_bytes(),
        )
        self.assertNotIn("### P10", root)
        self.assertFalse((self.root / "CLAUDE.md").exists())
        self.assertEqual("unchanged", self.install())

    @verifies(
        "scenario.distribution.install-apply",
        "scenario.distribution.install-retired-clients",
        "scenario.distribution.install-remove-guidance",
    )
    def test_user_bytes_modes_and_post_install_edits_survive_upgrade_and_cleanup(
        self,
    ):
        original = b"# User rules\r\nKeep my text exactly.\r\nNo final newline"
        root = self.root / "AGENTS.md"
        root.write_bytes(original)
        root.chmod(0o600)
        self.install()
        root.write_bytes(root.read_bytes() + b"\nNew user instructions\n")
        preserved = original + b"\nNew user instructions\n"
        self.assertEqual("unchanged", self.install())
        upgraded = guidance.entry().replace(b"before Concorde", b"before any Concorde")
        with patch.object(guidance, "entry", return_value=upgraded):
            self.install()
        self.assertEqual(preserved, b"".join(guidance.split(root.read_bytes())[::2]))
        self.assertEqual(0o600, root.stat().st_mode & 0o777)
        self.assertEqual("installed", self.install(cleanup=True))
        self.assertEqual(preserved, root.read_bytes())
        self.assertEqual("unchanged", self.install(cleanup=True))
        self.assertTrue((self.root / guidance.PROTOCOL).is_file())
        receipt = json.loads((self.root / installer.RECEIPT_PATH).read_text())
        self.assertFalse(
            any(item["role"] == guidance.ROLE for item in receipt["outputs"])
        )
        self.install()
        self.assertEqual(preserved, b"".join(guidance.split(root.read_bytes())[::2]))

    @verifies(
        "scenario.distribution.install-remove-guidance",
        "scenario.distribution.install-retired-clients",
    )
    def test_root_file_the_installer_created_goes_with_its_entry_but_a_user_file_stays(
        self,
    ):
        agents = self.root / "AGENTS.md"
        self.install()
        receipt = json.loads((self.root / installer.RECEIPT_PATH).read_text())
        by_path = {item["path"]: item for item in receipt["outputs"]}
        self.assertTrue(by_path["AGENTS.md"].get("created"))
        self.install(cleanup=True)
        self.assertFalse(agents.exists())
        agents.write_bytes(b"")
        self.install()
        self.install(cleanup=True)
        self.assertTrue(agents.is_file())
        self.assertEqual(b"", agents.read_bytes())
        agents.unlink()
        self.install()
        agents.write_bytes(agents.read_bytes() + b"My own rules\n")
        self.install(cleanup=True)
        self.assertEqual(b"My own rules\n", agents.read_bytes())

    @verifies(
        "scenario.distribution.install-conflict-rejected",
        "scenario.concorde.adopt-conflict",
    )
    def test_markers_symlinks_and_modified_owned_blocks_conflict_without_writes(self):
        name = self.root / "AGENTS.md"
        cases = [
            guidance.entry(),
            guidance.START,
            guidance.END,
            guidance.entry() * 2,
            guidance.END + guidance.START,
            b"<!-- concorde-protocol:forged -->\n",
        ]
        for body in cases:
            with self.subTest(body=body):
                name.write_bytes(body)
                with self.assertRaises(installer.InstallError):
                    self.install()
                self.assertEqual(body, name.read_bytes())
                self.assertFalse((self.root / installer.RECEIPT_PATH).exists())
        name.unlink()
        outside = self.root / "user.txt"
        outside.write_text("user-owned")
        for destination in (outside, self.root / "missing"):
            name.symlink_to(destination)
            with self.assertRaises(installer.InstallError):
                self.install()
            name.unlink()
        self.assertEqual("user-owned", outside.read_text())
        self.install()
        name.write_bytes(name.read_bytes().replace(b"Read and follow", b"Ignore"))
        before = name.read_bytes()
        for cleanup in (False, True):
            with self.assertRaises(installer.InstallError):
                self.install(cleanup=cleanup)
            self.assertEqual(before, name.read_bytes())

    @verifies(
        "scenario.distribution.install-apply",
        "scenario.distribution.install-remove-guidance",
    )
    def test_entry_precedes_user_fences_and_survives_lifecycle_block_cleanup(self):
        from concorde.harness.change_worktree import (
            GUIDANCE_START,
            GUIDANCE_END,
            strip_guidance,
        )

        root = self.root / "AGENTS.md"
        original = b"# User examples\n```text\nunclosed fence\n"
        root.write_bytes(original)
        self.install()
        installed = root.read_text()
        self.assertTrue(installed.startswith(guidance.entry().decode()))
        injected = installed + GUIDANCE_START + "Local candidate state\n" + GUIDANCE_END
        self.assertEqual(installed, strip_guidance(injected))
        root.write_text(injected)
        self.install(cleanup=True)
        self.assertEqual(
            original.decode()
            + GUIDANCE_START
            + "Local candidate state\n"
            + GUIDANCE_END,
            root.read_text(),
        )

    @verifies("scenario.distribution.install-conflict-rejected")
    def test_stale_preview_rejects_new_user_edits_or_symlink_before_writing(self):
        actions, desired, _ = installer.installation_plan(self.root, self.package)
        path = self.root / "AGENTS.md"
        path.write_text("new user edit")
        with self.assertRaisesRegex(installer.InstallError, "changed since preview"):
            installer.apply_plan(self.root, self.package, actions, desired)
        self.assertFalse((self.root / installer.RECEIPT_PATH).exists())
        self.assertEqual("new user edit", path.read_text())
        path.unlink()
        path.symlink_to(self.root / "missing")
        with self.assertRaises(installer.InstallError):
            installer.apply_plan(self.root, self.package, actions, desired)

    def test_failure_restores_root_bytes_mode_and_receipt(self):
        path = self.root / "AGENTS.md"
        path.write_bytes(b"user instructions")
        path.chmod(0o600)
        with patch.object(
            installer, "provision_runtime", side_effect=OSError("runtime failure")
        ):
            with self.assertRaisesRegex(OSError, "runtime failure"):
                self.install()
        self.assertEqual(b"user instructions", path.read_bytes())
        self.assertEqual(0o600, path.stat().st_mode & 0o777)
        self.assertFalse((self.root / installer.RECEIPT_PATH).exists())

    @verifies("scenario.distribution.install-apply")
    def test_install_upgrade_does_not_accept_old_project_protocol_binding(self):
        config = self.root / ".concorde/config.json"
        config.parent.mkdir()
        before = b'{"protocol":{"version":"1.0.0","digest":"old"}}\n'
        config.write_bytes(before)
        self.install()
        self.assertEqual(before, config.read_bytes())
        self.assertIn(
            f'"version": "{PROTOCOL_VERSION}"',
            (self.root / ".concorde/framework/protocol/manifest.json").read_text(),
        )


class LegacyInstallationRetirementTests(InstallerTestCase):
    # Inherit the same offline installer setup, but no production Skill installation helper.
    def legacy_receipt(self, records):
        path = self.root / installer.RECEIPT_PATH
        path.parent.mkdir(parents=True, exist_ok=True)
        value = {
            "schema_version": 1,
            "integrations": ["claude", "codex"],
            "skills": {"cli": "skills@1.7.0", "agents": ["claude-code", "codex"]},
            "outputs": records,
        }
        path.write_text(json.dumps(value))
        return path

    @verifies("scenario.distribution.install-retired-clients")
    def test_upgrade_retires_only_digest_owned_legacy_files_and_block(self):
        block = guidance.START + b"Old Claude import\n" + guidance.END
        claude = self.root / "CLAUDE.md"
        claude.write_bytes(b"Before\n" + block + b"After\n")
        claude.chmod(0o600)
        legacy = self.root / ".claude/skills/concorde-validate/SKILL.md"
        legacy.parent.mkdir(parents=True)
        legacy.write_bytes(b"installer-owned legacy Skill\n")
        user = legacy.parent / "notes.txt"
        user.write_bytes(b"unrelated\n")
        external = self.root / ".agents/skills/concorde-plan/SKILL.md"
        external.parent.mkdir(parents=True)
        external.write_bytes(b"external CLI bytes\n")
        lock = self.root / "skills-lock.json"
        lock.write_bytes(b"external CLI lock\n")
        self.legacy_receipt(
            [
                {
                    "path": "CLAUDE.md",
                    "role": guidance.ROLE,
                    "created": True,
                    "sha256": installer._sha256(block),
                },
                {
                    "path": legacy.relative_to(self.root).as_posix(),
                    "role": "skill",
                    "sha256": installer._sha256(legacy.read_bytes()),
                },
            ]
        )
        self.install()
        self.assertFalse(legacy.exists())
        self.assertEqual(b"Before\nAfter\n", claude.read_bytes())
        self.assertEqual(0o600, claude.stat().st_mode & 0o777)
        self.assertEqual(b"unrelated\n", user.read_bytes())
        self.assertEqual(b"external CLI bytes\n", external.read_bytes())
        self.assertEqual(b"external CLI lock\n", lock.read_bytes())
        receipt = json.loads((self.root / installer.RECEIPT_PATH).read_text())
        self.assertEqual(2, receipt["schema_version"])
        self.assertEqual("pi", receipt["client"])
        self.assertNotIn("skills", receipt)
        self.assertEqual("unchanged", self.install())

    @verifies("scenario.distribution.install-retired-clients")
    def test_retired_block_removes_created_empty_file_not_user_file(self):
        for created in (True, False):
            with self.subTest(created=created):
                path = self.root / "CLAUDE.md"
                block = guidance.START + b"legacy\n" + guidance.END
                path.write_bytes(block)
                self.legacy_receipt(
                    [
                        {
                            "path": "CLAUDE.md",
                            "role": guidance.ROLE,
                            "sha256": installer._sha256(block),
                            "created": created,
                        }
                    ]
                )
                self.install()
                self.assertEqual(not created, path.exists())
                if not created:
                    self.assertEqual(b"", path.read_bytes())
                self.install(cleanup=True)

    @verifies("scenario.distribution.install-conflict-rejected")
    def test_modified_or_symlinked_retired_owned_file_blocks_without_writes(self):
        path = self.root / ".agents/skills/concorde-plan/SKILL.md"
        path.parent.mkdir(parents=True)
        record = {
            "path": path.relative_to(self.root).as_posix(),
            "role": "skill",
            "sha256": installer._sha256(b"owned"),
        }
        receipt = self.legacy_receipt([record])
        before = receipt.read_bytes()
        path.write_bytes(b"locally edited")
        for symlink in (False, True):
            with self.subTest(symlink=symlink):
                if symlink:
                    path.unlink()
                    path.symlink_to(self.root / "missing")
                with self.assertRaises(installer.InstallError):
                    self.install()
                self.assertEqual(before, receipt.read_bytes())
                self.assertFalse((self.root / ".pi").exists())

    @verifies("scenario.distribution.install-conflict-rejected")
    def test_retired_owned_file_changed_after_preview_is_not_deleted(self):
        path = self.root / ".agents/skills/concorde-plan/SKILL.md"
        path.parent.mkdir(parents=True)
        path.write_bytes(b"owned")
        self.legacy_receipt(
            [
                {
                    "path": path.relative_to(self.root).as_posix(),
                    "role": "skill",
                    "sha256": installer._sha256(path.read_bytes()),
                }
            ]
        )
        actions, desired, _ = installer.installation_plan(self.root, self.package)
        path.write_bytes(b"new user edit")
        with self.assertRaisesRegex(installer.InstallError, "changed since preview"):
            installer.apply_plan(self.root, self.package, actions, desired)
        self.assertEqual(b"new user edit", path.read_bytes())
        self.assertFalse((self.root / ".pi").exists())

    @verifies("scenario.distribution.install-retired-clients")
    def test_failed_upgrade_restores_retired_bytes_modes_and_receipt_then_retries(self):
        path = self.root / ".claude/skills/concorde-plan/SKILL.md"
        path.parent.mkdir(parents=True)
        path.write_bytes(b"old owned")
        path.chmod(0o600)
        receipt = self.legacy_receipt(
            [
                {
                    "path": path.relative_to(self.root).as_posix(),
                    "role": "skill",
                    "sha256": installer._sha256(path.read_bytes()),
                }
            ]
        )
        before = receipt.read_bytes()
        with patch.object(
            installer, "provision_runtime", side_effect=OSError("failure")
        ):
            with self.assertRaises(OSError):
                self.install()
        self.assertEqual(b"old owned", path.read_bytes())
        self.assertEqual(0o600, path.stat().st_mode & 0o777)
        self.assertEqual(before, receipt.read_bytes())
        self.install()
        self.assertFalse(path.exists())

    @verifies("scenario.distribution.install-conflict-rejected")
    def test_external_cli_lock_cannot_be_claimed_by_a_receipt(self):
        lock = self.root / "skills-lock.json"
        lock.write_bytes(b"external lock")
        self.legacy_receipt(
            [
                {
                    "path": "skills-lock.json",
                    "role": "skill",
                    "sha256": installer._sha256(lock.read_bytes()),
                }
            ]
        )
        with self.assertRaisesRegex(installer.InstallError, "never installer-owned"):
            self.install()
        self.assertEqual(b"external lock", lock.read_bytes())
