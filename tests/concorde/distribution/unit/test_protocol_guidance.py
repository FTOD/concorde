"""Consumer-root installation contracts without source-checkout AGENTS policy."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tests.concorde.distribution.unit.test_install_concorde import installer
from tests.concorde.support.paths import REPOSITORY_ROOT
from concorde.distribution import protocol_guidance as guidance


class ProtocolGuidanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.package = installer.load_package(REPOSITORY_ROOT)

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        # Runtime provisioning has separate native integration coverage. Exercise the real
        # installer transaction/receipt here without downloading dependencies per case.
        for name, value in (("plan_runtime", {"path": ".concorde/.venv", "role": "runtime",
                                             "action": "unchanged", "sha256": "unused"}),
                            ("provision_runtime", {"path": ".concorde/.venv"})):
            mock = patch.object(installer, name, return_value=value)
            mock.start()
            self.addCleanup(mock.stop)

    def install(self, integration="codex", cleanup=False):
        actions, desired, _ = installer.installation_plan(
            self.root, self.package, integration, remove_protocol_guidance=cleanup)
        return installer.apply_plan(self.root, self.package, integration, actions, desired,
                                    remove_protocol_guidance=cleanup)

    def test_both_integrations_load_single_protocol_asset_without_checkout_policy(self):
        for integration, name in guidance.FILES.items():
            with self.subTest(integration=integration):
                self.install(integration)
                root = (self.root / name).read_text()
                self.assertNotIn("Source-Checkout", root)
                self.assertIn(guidance.PROTOCOL, root)
                if integration == "claude":
                    self.assertIn("\n@" + guidance.PROTOCOL + "\n", root)
                else:
                    self.assertIn("Read and follow", root)
                protocol = (self.root / guidance.PROTOCOL).read_bytes()
                self.assertEqual(protocol, (REPOSITORY_ROOT / "generated/protocol/principles.md").read_bytes())
                self.assertIn(b"### P10. Copyable agent handoffs", protocol)
                self.assertNotIn(b"### P10", (self.root / name).read_bytes())
                for directory in (".agents/skills", ".claude/skills"):
                    for skill in (self.root / directory).glob("*/SKILL.md"):
                        self.assertNotIn("Copyable agent handoffs", skill.read_text())
                self.assertEqual("unchanged", self.install(integration))

    def test_user_bytes_modes_and_post_install_edits_survive_upgrade_switch_and_cleanup(self):
        original = b"# User rules\r\nKeep my text exactly.\r\nNo final newline"
        root = self.root / "AGENTS.md"
        root.write_bytes(original)
        root.chmod(0o600)
        self.install()
        root.write_bytes(root.read_bytes() + b"\nNew user instructions\n")
        preserved = original + b"\nNew user instructions\n"
        self.assertEqual("unchanged", self.install())
        upgraded = guidance.entry("codex").replace(b"before Concorde", b"before any Concorde")
        with patch.object(guidance, "entry", return_value=upgraded):
            self.install()
        self.assertEqual(preserved, b"".join(guidance.split(root.read_bytes())[::2]))
        self.assertEqual(0o600, root.stat().st_mode & 0o777)
        self.install("claude")
        self.assertEqual(preserved, root.read_bytes())
        self.assertEqual("installed", self.install("claude", cleanup=True))
        self.assertEqual(b"", (self.root / "CLAUDE.md").read_bytes())
        self.assertEqual("unchanged", self.install("claude", cleanup=True))
        self.assertTrue((self.root / guidance.PROTOCOL).is_file())
        receipt = json.loads((self.root / installer.RECEIPT_PATH).read_text())
        self.assertFalse(any(item["role"] == guidance.ROLE for item in receipt["outputs"]))
        self.install()
        self.assertEqual(preserved, b"".join(guidance.split(root.read_bytes())[::2]))

    def test_markers_symlinks_and_modified_owned_blocks_conflict_without_writes(self):
        name = self.root / "AGENTS.md"
        cases = [guidance.entry("codex"), guidance.START, guidance.END,
                 guidance.entry("codex") * 2, guidance.END + guidance.START,
                 b"<!-- concorde-protocol:forged -->\n"]
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
        for integration, cleanup in (("codex", False), ("claude", False), ("codex", True)):
            with self.assertRaises(installer.InstallError):
                self.install(integration, cleanup)
            self.assertEqual(before, name.read_bytes())

    def test_entry_precedes_user_fences_and_survives_lifecycle_block_cleanup(self):
        from concorde.host.change_worktree import GUIDANCE_START, GUIDANCE_END, strip_guidance
        root = self.root / "CLAUDE.md"
        original = b"# User examples\n```text\nunclosed fence\n"
        root.write_bytes(original)
        self.install("claude")
        installed = root.read_text()
        self.assertTrue(installed.startswith(guidance.entry("claude").decode()))
        injected = installed + GUIDANCE_START + "Local candidate state\n" + GUIDANCE_END
        self.assertEqual(installed, strip_guidance(injected))
        root.write_text(injected)
        self.install("claude", cleanup=True)
        self.assertEqual(original.decode() + GUIDANCE_START + "Local candidate state\n" + GUIDANCE_END,
                         root.read_text())

    def test_stale_preview_rejects_new_user_edits_or_symlink_before_writing(self):
        actions, desired, _ = installer.installation_plan(self.root, self.package, "codex")
        path = self.root / "AGENTS.md"
        path.write_text("new user edit")
        with self.assertRaisesRegex(installer.InstallError, "changed since preview"):
            installer.apply_plan(self.root, self.package, "codex", actions, desired)
        self.assertFalse((self.root / installer.RECEIPT_PATH).exists())
        self.assertEqual("new user edit", path.read_text())
        path.unlink()
        path.symlink_to(self.root / "missing")
        with self.assertRaises(installer.InstallError):
            installer.apply_plan(self.root, self.package, "codex", actions, desired)

    def test_failure_restores_root_bytes_mode_and_receipt(self):
        path = self.root / "AGENTS.md"
        path.write_bytes(b"user instructions")
        path.chmod(0o600)
        with patch.object(installer, "provision_runtime", side_effect=OSError("runtime failure")):
            with self.assertRaisesRegex(OSError, "runtime failure"):
                self.install()
        self.assertEqual(b"user instructions", path.read_bytes())
        self.assertEqual(0o600, path.stat().st_mode & 0o777)
        self.assertFalse((self.root / installer.RECEIPT_PATH).exists())

    def test_install_upgrade_does_not_accept_old_project_protocol_binding(self):
        config = self.root / ".concorde/config.json"
        config.parent.mkdir()
        before = b'{"protocol":{"version":"1.0.0","digest":"old"}}\n'
        config.write_bytes(before)
        self.install()
        self.assertEqual(before, config.read_bytes())
        self.assertIn('"version": "1.2.0"', (self.root / ".concorde/framework/protocol/manifest.json").read_text())
