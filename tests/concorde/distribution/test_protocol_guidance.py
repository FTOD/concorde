"""Consumer-root installation contracts without source-checkout AGENTS policy."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from concorde.distribution import installation as installer
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
        self.assertEqual("unchanged", self.install())

    @verifies(
        "scenario.distribution.install-apply",
        "scenario.distribution.install-upgrade",
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

    @verifies("scenario.distribution.install-remove-guidance")
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

    @verifies("scenario.distribution.install-conflict-rejected")
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

    @verifies(
        "scenario.distribution.install-conflict-rejected",
        "scenario.distribution.install-stale-plan",
    )
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

    @verifies("scenario.distribution.install-apply-rollback")
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

    def snapshot(self):
        return {
            path.relative_to(self.root).as_posix(): (
                path.read_bytes(),
                path.stat().st_mode & 0o777,
            )
            for path in self.root.rglob("*")
            if path.is_file()
        }

    @verifies("scenario.distribution.install-remove-guidance-repeat")
    def test_removing_the_blocks_again_changes_no_file_or_receipt_record(self):
        agents = self.root / "AGENTS.md"
        agents.write_bytes(b"# Project rules\n")
        self.install()
        self.assertEqual("installed", self.install(cleanup=True))
        self.assertEqual(b"# Project rules\n", agents.read_bytes())
        before = self.snapshot()
        for _ in range(2):
            actions, _, _ = installer.installation_plan(
                self.root, self.package, remove_protocol_guidance=True
            )
            self.assertEqual([], actions)
            self.assertEqual("unchanged", self.install(cleanup=True))
            self.assertEqual(before, self.snapshot())

    @verifies("scenario.distribution.install-stale-plan")
    def test_a_recomputed_plan_or_package_identity_that_differs_is_refused(self):
        # A desired output that appeared after the preview changes the recomputed plan.
        actions, desired, _ = installer.installation_plan(self.root, self.package)
        before = self.snapshot()
        session = self.root / ".pi/extensions/concorde-session.ts"
        session.parent.mkdir(parents=True)
        session.write_text("developer file\n")
        with_developer_file = self.snapshot()
        with self.assertRaisesRegex(installer.InstallError, "changed since preview"):
            installer.apply_plan(self.root, self.package, actions, desired)
        self.assertEqual(with_developer_file, self.snapshot())
        session.unlink()
        session.parent.rmdir()
        (self.root / ".pi").rmdir()
        # The package the preview admitted changes before the receipt is written.
        actions, desired, _ = installer.installation_plan(self.root, self.package)
        real_identity = installer.package_identity
        calls = []

        def drifting(package):
            calls.append(package)
            identity = real_identity(package)
            if len(calls) > 1:
                identity = {**identity, "digest": "sha256:" + "1" * 64}
            return identity

        with (
            patch.object(installer, "package_identity", side_effect=drifting),
            self.assertRaisesRegex(installer.InstallError, "package changed"),
        ):
            installer.apply_plan(self.root, self.package, actions, desired)
        self.assertEqual(before, self.snapshot())

    @verifies("scenario.distribution.install-apply-rollback")
    def test_a_failed_upgrade_restores_every_created_replaced_and_removed_file(self):
        self.install()
        receipt_path = self.root / installer.RECEIPT_PATH
        receipt = json.loads(receipt_path.read_text())
        # A superseded owned output the upgrade removes.
        retired = self.root / ".concorde/framework/prompts/removed/old.md"
        retired.parent.mkdir(parents=True)
        retired.write_bytes(b"retired owned bytes\n")
        retired.chmod(0o600)
        receipt["outputs"].append(
            {
                "path": retired.relative_to(self.root).as_posix(),
                "role": "framework",
                "sha256": installer._sha256(retired.read_bytes()),
            }
        )
        receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
        receipt_path.chmod(0o640)
        # An owned output the upgrade recreates.
        (self.root / ".pi/extensions/concorde-session.ts").unlink()
        # An owned root block the upgrade replaces, inside a developer's file mode.
        agents = self.root / "AGENTS.md"
        agents.chmod(0o600)
        upgraded = guidance.entry().replace(b"before Concorde", b"before any Concorde")
        before = self.snapshot()
        with (
            patch.object(guidance, "entry", return_value=upgraded),
            patch.object(
                installer, "provision_runtime", side_effect=OSError("late failure")
            ),
        ):
            actions, _, _ = installer.installation_plan(self.root, self.package)
            by_action = {}
            for item in actions:
                by_action.setdefault(item["action"], set()).add(item["path"])
            self.assertIn(".pi/extensions/concorde-session.ts", by_action["create"])
            self.assertIn("AGENTS.md", by_action["update"])
            self.assertIn(
                ".concorde/framework/prompts/removed/old.md", by_action["remove"]
            )
            with self.assertRaisesRegex(OSError, "late failure"):
                self.install()
        self.assertEqual(before, self.snapshot())
        self.assertFalse(
            [
                p
                for p in self.root.rglob(".concorde-*")
                if p.name != ".concorde-runtime.json"
            ]
        )


class SupersededOutputTests(InstallerTestCase):
    """A receipt-owned output the current package no longer ships is removed only when unchanged."""

    SUPERSEDED = ".concorde/framework/prompts/removed/old.md"

    def owned_superseded(self, content=b"owned"):
        path = self.root / self.SUPERSEDED
        path.parent.mkdir(parents=True)
        path.write_bytes(content)
        receipt = self.root / installer.RECEIPT_PATH
        receipt.write_text(
            json.dumps(
                {
                    "schema_version": installer.INSTALL_SCHEMA,
                    "outputs": [
                        {
                            "path": self.SUPERSEDED,
                            "role": "framework",
                            "sha256": installer._sha256(content),
                        }
                    ],
                }
            )
        )
        return path, receipt

    @verifies(
        "scenario.distribution.install-conflict-rejected",
        "scenario.distribution.install-upgrade",
    )
    def test_modified_or_symlinked_superseded_file_blocks_without_writes(self):
        path, receipt = self.owned_superseded()
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

    @verifies(
        "scenario.distribution.install-conflict-rejected",
        "scenario.distribution.install-upgrade",
        "scenario.distribution.install-stale-plan",
    )
    def test_superseded_file_changed_after_preview_is_not_deleted(self):
        path, _ = self.owned_superseded()
        actions, desired, _ = installer.installation_plan(self.root, self.package)
        path.write_bytes(b"new user edit")
        with self.assertRaisesRegex(installer.InstallError, "changed since preview"):
            installer.apply_plan(self.root, self.package, actions, desired)
        self.assertEqual(b"new user edit", path.read_bytes())
        self.assertFalse((self.root / ".pi").exists())

    @verifies(
        "scenario.distribution.install-upgrade",
        "scenario.distribution.install-apply-rollback",
    )
    def test_failed_upgrade_restores_removed_bytes_modes_and_receipt_then_retries(self):
        path, receipt = self.owned_superseded(b"old owned")
        path.chmod(0o600)
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
        self.assertEqual("unchanged", self.install())
