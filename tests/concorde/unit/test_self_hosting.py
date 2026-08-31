import json
import os
import tempfile
import unittest
from pathlib import Path

from tests.concorde.self_hosting_support import initialize_checkout, load_preserved_fixture, load_self_hosting, preserved_sentinels


self_host = load_self_hosting()


class SelfHostingUnitTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        initialize_checkout(self.root)

    def tearDown(self):
        self.temporary.cleanup()

    def test_source_model_is_complete_ordered_and_deterministic(self):
        components, first, integration = self_host.component_model(self.root)
        self.assertEqual([item["kind"] for item in components], ["preset", "extension", "bundle"])
        self.assertEqual([item["id"] for item in components], ["concorde", "concorde", "concorde-bundle"])
        self.assertEqual(integration, "codex")
        self.assertEqual(first, self_host.component_model(self.root)[1])

    def test_supported_integration_profiles_define_root_and_init_behavior(self):
        codex = self_host.integration_profile("codex")
        claude = self_host.integration_profile("claude")
        self.assertEqual(codex["skill_root"], ".agents/skills")
        self.assertEqual(claude["skill_root"], ".claude/skills")
        self.assertIn(".codex/agents/reflection_investigator.toml", codex["agent_surfaces"])
        self.assertIn(".claude/agents/reflection-investigator.md", claude["agent_surfaces"])
        self.assertIn("--integration-options=--skills", self_host.integration_init_arguments("codex"))
        self.assertNotIn("--integration-options=--skills", self_host.integration_init_arguments("claude"))
        self.assertEqual(self_host.skill_path("speckit.plan", "codex"), ".agents/skills/speckit-plan/SKILL.md")
        self.assertEqual(self_host.skill_path("speckit.plan", "claude"), ".claude/skills/speckit-plan/SKILL.md")

    def test_claude_extension_surface_accepts_canonical_link_or_regular_fallback(self):
        command = "speckit.concorde.ask"
        relative = self_host.skill_path(command, "claude")
        surface = self.root / relative
        target = self.root / self_host.claude_extension_target(command)
        target.parent.mkdir(parents=True)
        target.write_text("canonical extension skill\n")
        surface.parent.mkdir(parents=True)
        surface.symlink_to(os.path.relpath(target, surface.parent))

        evidence = self_host.surface_evidence(self.root, relative, "claude", extension_command=command)
        self.assertEqual(evidence["representation"], "symlink")
        self.assertEqual(evidence["target"], target.relative_to(self.root).as_posix())

        surface.unlink()
        surface.write_text("regular fallback\n")
        evidence = self_host.surface_evidence(self.root, relative, "claude", extension_command=command)
        self.assertEqual(evidence["representation"], "file")
        self.assertNotIn("target", evidence)

    def test_surface_evidence_rejects_unsafe_or_undeclared_links(self):
        command = "speckit.concorde.ask"
        relative = self_host.skill_path(command, "claude")
        surface = self.root / relative
        surface.parent.mkdir(parents=True)
        outside = self.root / "unrelated.md"
        outside.write_text("unrelated\n")

        surface.symlink_to(os.path.relpath(outside, surface.parent))
        self.assertIsNone(self_host.surface_evidence(self.root, relative, "claude", extension_command=command))
        surface.unlink()
        surface.symlink_to(outside)
        self.assertIsNone(self_host.surface_evidence(self.root, relative, "claude", extension_command=command))
        surface.unlink()
        surface.symlink_to("missing.md")
        self.assertIsNone(self_host.surface_evidence(self.root, relative, "claude", extension_command=command))

        preset_relative = self_host.skill_path("speckit.plan", "claude")
        preset_surface = self.root / preset_relative
        preset_surface.parent.mkdir(parents=True)
        preset_surface.symlink_to(os.path.relpath(outside, preset_surface.parent))
        self.assertIsNone(self_host.surface_evidence(self.root, preset_relative, "claude"))

    def test_source_change_changes_digest(self):
        before = self_host.component_model(self.root)[1]
        readme = self.root / "extensions/concorde/README.md"
        readme.write_text(readme.read_text() + "\nobservable change\n")
        self.assertNotEqual(before, self_host.component_model(self.root)[1])

    def test_source_model_qualifies_same_id_bundle_pins_by_component_type(self):
        bundle = self.root / "bundles/concorde-bundle/bundle.yml"
        text = bundle.read_text(encoding="utf-8")
        preset_section = '  presets:\n    - id: "concorde"'
        self.assertIn(preset_section, text)
        bundle.write_text(text.replace(preset_section, '  presets:\n    - id: "missing"', 1), encoding="utf-8")
        with self.assertRaises(self_host.SelfHostError) as raised:
            self_host.component_model(self.root)
        self.assertEqual(raised.exception.finding["code"], "CONCORDE-SELF-HOST-008")

    def test_path_boundary_rejects_absolute_parent_backslash_and_symlink(self):
        for unsafe in ("/tmp/x", "../x", "a/../x", "a\\b", "a/"):
            with self.assertRaises(ValueError, msg=unsafe):
                self_host.safe_relative(unsafe)
        (self.root / "outside").mkdir()
        (self.root / "linked").symlink_to(self.root / "outside", target_is_directory=True)
        with self.assertRaises(ValueError):
            self_host.resolve_project_path(self.root, "linked/file")

    def test_source_inventory_rejects_symlinks(self):
        (self.root / "presets/concorde/linked").symlink_to(self.root / "bundles/concorde-bundle")
        with self.assertRaises(self_host.SelfHostError) as raised:
            self_host.component_model(self.root)
        self.assertEqual(raised.exception.finding["code"], "CONCORDE-SELF-HOST-002")

    def test_unsupported_host_and_integration_are_actionable(self):
        path = self.root / ".specify/integration.json"
        data = json.loads(path.read_text())
        data["version"] = "0.17.0"
        path.write_text(json.dumps(data))
        with self.assertRaises(self_host.SelfHostError) as raised:
            self_host.integration_state(self.root)
        self.assertEqual(raised.exception.finding["code"], "CONCORDE-SELF-HOST-006")

        data["version"] = "0.16.4"
        data["integration"] = "gemini"
        path.write_text(json.dumps(data))
        with self.assertRaises(self_host.SelfHostError) as raised:
            self_host.integration_state(self.root)
        self.assertEqual(raised.exception.finding["code"], "CONCORDE-SELF-HOST-005")

    def test_claude_is_a_supported_source_model(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            initialize_checkout(root, "claude")
            components, _, integration = self_host.component_model(root)
        self.assertEqual(integration, "claude")
        self.assertEqual([item["kind"] for item in components], ["preset", "extension", "bundle"])

    def test_absent_status_is_read_only_and_activation_unknown(self):
        before = {p.relative_to(self.root).as_posix(): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        result = self_host.status(self.root)
        after = {p.relative_to(self.root).as_posix(): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(result["status"], "absent")
        self.assertEqual(result["dimensions"]["activation"]["status"], "unknown")
        self.assertEqual(before, after)

    def test_preserved_inactive_paths_cover_only_the_other_integration(self):
        codex_active = self_host.preserved_inactive_paths("codex")
        claude_active = self_host.preserved_inactive_paths("claude")
        self.assertEqual(len(codex_active), 16)
        self.assertIn(".specify/extensions/concorde/.specify-dev/agent-commands/claude", codex_active)
        self.assertTrue(all(path.startswith((".claude/skills/speckit-", ".specify/")) for path in codex_active))
        self.assertEqual(len(claude_active), 15)
        self.assertTrue(all(path.startswith(".agents/skills/speckit-") for path in claude_active))
        self.assertFalse(set(codex_active) & set(self_host.owned_paths("codex")))
        self.assertFalse(set(claude_active) & set(self_host.owned_paths("claude")))
        with self.assertRaises(self_host.SelfHostError):
            self_host.preserved_inactive_paths("gemini")


class PreservedFixtureTests(unittest.TestCase):
    """The preservation fixture's keys define SC-005 coverage, so they are read strictly (R-039)."""

    REQUIRED_SENTINELS = frozenset(
        {
            "specs/example/abstract.md",
            "specs/example/design.md",
            "specs/example/implementation.md",
            "specs/example/architecture/contracts/io/contract.md",
            "specs/example/diagrams/components.json",
            "specs/example/attempt/tasks.md",
            "docs/user.md",
            "src/user.py",
            "tests/user.txt",
            ".concorde/config.json",
            "generated/user.html",
            ".agents/skills/user-owned/SKILL.md",
        }
    )

    def test_fixture_seeds_every_preserved_content_class(self):
        sentinels = preserved_sentinels()
        self.assertLessEqual(self.REQUIRED_SENTINELS, set(sentinels))
        self.assertTrue(all(content for content in sentinels.values()))
        self.assertEqual(
            len({sentinels[path] for path in ("specs/example/abstract.md", "specs/example/design.md", "specs/example/implementation.md")}),
            3,
        )

    def test_fixture_loader_rejects_repeated_paths_and_non_string_content(self):
        repeated = '{"specs/example/design.md": "# a\\n", "specs/example/design.md": "# b\\n"}'
        self.assertEqual(json.loads(repeated), {"specs/example/design.md": "# b\n"})
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Path(temporary) / "preserved-files.json"
            fixture.write_text(repeated, encoding="utf-8")
            with self.assertRaisesRegex(AssertionError, "repeats 'specs/example/design.md'"):
                load_preserved_fixture(fixture)
            fixture.write_text('{"specs/example/design.md": 1}', encoding="utf-8")
            with self.assertRaisesRegex(AssertionError, "string-to-string"):
                load_preserved_fixture(fixture)
            fixture.write_text('["specs/example/design.md"]', encoding="utf-8")
            with self.assertRaisesRegex(AssertionError, "string-to-string"):
                load_preserved_fixture(fixture)


if __name__ == "__main__":
    unittest.main()
