import tempfile
import unittest
from pathlib import Path

from tests.concorde.self_hosting_support import hash_paths, initialize_checkout, preserved_sentinels, run_cli, skill_file, skill_root


class SelfHostedCheckoutAcceptanceTests(unittest.TestCase):
    def test_complete_surface_inventory_refresh_and_preservation(self):
        for integration in ("codex", "claude"):
            with self.subTest(integration=integration), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                initialize_checkout(root, integration)
                inactive = "claude" if integration == "codex" else "codex"
                inactive_surface = skill_file(root, inactive, "speckit.concorde.ask").relative_to(root).as_posix()
                sentinels = {**preserved_sentinels(), inactive_surface: f"inactive {inactive} surface\n"}
                for relative, content in sentinels.items():
                    path = root / relative
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(content)
                before = hash_paths(root, tuple(sentinels))
                run_cli(root, "propose")
                _, applied = run_cli(root, "apply", "--proposal", ".specify/self-hosting-proposal.json")
                self.assertEqual(applied["status"], "applied")
                self.assertEqual(len(list(skill_root(root, integration).glob("speckit-*/SKILL.md"))), 16)
                fast_loop = skill_file(root, integration, "speckit.fast-loop")
                self.assertTrue(fast_loop.is_file())
                self.assertIn("--phase fast-loop", fast_loop.read_text(encoding="utf-8"))
                self.assertIn("No attempt: yes", fast_loop.read_text(encoding="utf-8"))
                self.assertEqual(before, hash_paths(root, tuple(sentinels)))
                _, current = run_cli(root, "status")
                self.assertEqual(current["status"], "current")
                source = root / "presets/concorde/README.md"
                source.write_text(source.read_text() + "\nacceptance refresh\n")
                run_cli(root, "propose")
                _, refreshed = run_cli(root, "apply", "--proposal", ".specify/self-hosting-proposal.json")
                self.assertEqual(refreshed["status"], "applied")
                self.assertIn("acceptance refresh", (root / ".specify/presets/concorde/README.md").read_text())
                self.assertEqual(before, hash_paths(root, tuple(sentinels)))


if __name__ == "__main__":
    unittest.main()
