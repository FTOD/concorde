import tempfile
import unittest
from pathlib import Path

from tests.concorde.self_hosting_support import (
    hash_paths,
    initialize_checkout,
    load_self_hosting,
    preserved_sentinels,
    run_cli,
    select_integration,
    skill_file,
    skill_root,
    surface_tree,
)


self_host = load_self_hosting()


class SelfHostedCheckoutAcceptanceTests(unittest.TestCase):
    def test_complete_surface_inventory_refresh_and_preservation(self):
        for integration in ("codex", "claude"):
            with self.subTest(integration=integration), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                initialize_checkout(root, integration)
                inactive = "claude" if integration == "codex" else "codex"
                inactive_surface = skill_file(root, inactive, "speckit.concorde.ask").relative_to(root).as_posix()
                inactive_agent = str(self_host.integration_profile(inactive)["agent_surfaces"][0])
                sentinels = {
                    **preserved_sentinels(),
                    inactive_surface: f"inactive {inactive} surface\n",
                    inactive_agent: f"inactive {inactive} reflection agent\n",
                }
                for relative, content in sentinels.items():
                    path = root / relative
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(content)
                before = hash_paths(root, tuple(sentinels))
                run_cli(root, "propose")
                _, applied = run_cli(root, "apply", "--proposal", ".specify/self-hosting-proposal.json")
                self.assertEqual(applied["status"], "applied")
                self.assertEqual(len(list(skill_root(root, integration).glob("speckit-*/SKILL.md"))), 16)
                for relative in self_host.integration_profile(integration)["agent_surfaces"]:
                    self.assertTrue((root / str(relative)).is_file(), relative)
                fast_loop = skill_file(root, integration, "speckit.fast-loop")
                self.assertTrue(fast_loop.is_file())
                fast_loop_content = fast_loop.read_text(encoding="utf-8")
                for requirement in (
                    "--phase fast-loop",
                    "anchor feature",
                    "affected feature set",
                    "Every affected feature",
                    "inter-module contract",
                    "module responsibility",
                    "dependency direction",
                    "users of the whole project",
                    "review_pending",
                    "No attempt: yes",
                ):
                    self.assertIn(requirement, fast_loop_content)
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

    def test_switching_active_integration_twice_preserves_every_inactive_concorde_surface(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            initialize_checkout(root, "codex")
            run_cli(root, "propose")
            _, applied = run_cli(root, "apply", "--proposal", ".specify/self-hosting-proposal.json")
            self.assertEqual(applied["status"], "applied")
            codex_tree = surface_tree(root, ".agents/skills")
            self.assertEqual(len(list(skill_root(root, "codex").glob("speckit-*/SKILL.md"))), 16)

            select_integration(root, "claude")
            _, proposal = run_cli(root, "propose")
            self.assertEqual([item["path"] for item in proposal["changes"] if item["path"].startswith(".agents/")], [])
            _, applied = run_cli(root, "apply", "--proposal", ".specify/self-hosting-proposal.json")
            self.assertEqual(applied["status"], "applied")
            self.assertEqual(surface_tree(root, ".agents/skills"), codex_tree)
            for command in self_host.EXTENSION_COMMANDS + ("speckit.fast-loop",):
                self.assertTrue(skill_file(root, "codex", command).is_file(), command)
            self.assertEqual(len(list(skill_root(root, "claude").glob("speckit-*/SKILL.md"))), 15)
            claude_tree = surface_tree(root, ".claude/skills")
            _, current = run_cli(root, "status")
            self.assertEqual(current["status"], "current")

            select_integration(root, "codex")
            run_cli(root, "propose")
            _, applied = run_cli(root, "apply", "--proposal", ".specify/self-hosting-proposal.json")
            self.assertEqual(applied["status"], "applied")
            self.assertEqual(surface_tree(root, ".claude/skills"), claude_tree)
            for command in self_host.EXTENSION_COMMANDS:
                link = skill_file(root, "claude", command)
                self.assertTrue(link.is_symlink(), command)
                self.assertTrue(link.resolve().is_file(), command)
            self.assertEqual(surface_tree(root, ".agents/skills"), codex_tree)
            _, current = run_cli(root, "status")
            self.assertEqual(current["status"], "current")


if __name__ == "__main__":
    unittest.main()
