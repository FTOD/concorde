import re
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml

from tests.concorde.support.paths import REPOSITORY_ROOT


PRESET = REPOSITORY_ROOT / "presets/concorde"
EXTENSION = REPOSITORY_ROOT / "extensions/concorde"


class ManifestContractTests(unittest.TestCase):
    def test_extension_declares_profile7_commands_scripts_and_agent_assets(self):
        manifest = yaml.safe_load((EXTENSION / "extension.yml").read_text(encoding="utf-8"))
        self.assertEqual(len(manifest["provides"]["commands"]), 5)
        self.assertEqual(len(manifest["provides"]["scripts"]), 5)
        self.assertIn("module-centered", manifest["extension"]["description"])
        descriptions = {item["name"]: item["description"] for item in manifest["provides"]["commands"]}
        self.assertIn("atomically remove", descriptions["speckit.concorde.deliver"])
        self.assertIn("Protocol 12", manifest["provides"]["scripts"][3]["description"])
        self.assertEqual(manifest["extension"]["version"], "0.9.0")
        self.assertIn("reflection-triage/v3", manifest["provides"]["scripts"][4]["description"])
        for relative in (
            "agent-assets/reflections/manifest.json",
            "agent-assets/reflections/orchestrator.md",
            "agent-assets/reflections/roles/investigator.md",
            "agent-assets/reflections/roles/implementer.md",
            "agent-assets/reflections/projections/claude/SKILL.md.tmpl",
            "agent-assets/reflections/projections/codex/SKILL.md.tmpl",
        ):
            self.assertTrue((EXTENSION / relative).is_file(), relative)

    def test_bundle_is_native_exactly_two_components_and_names_profile(self):
        text = (REPOSITORY_ROOT / "bundles/concorde-bundle/bundle.yml").read_text(encoding="utf-8")
        manifest = yaml.safe_load(text)
        self.assertEqual(manifest["bundle"]["id"], "concorde-bundle")
        self.assertEqual(manifest["bundle"]["version"], "0.9.0")
        self.assertIn("Profile 7", manifest["bundle"]["description"])
        self.assertIn("Protocol 12", manifest["bundle"]["description"])
        self.assertEqual(len(manifest["provides"]["extensions"]), 1)
        self.assertEqual(len(manifest["provides"]["presets"]), 1)
        self.assertEqual(manifest["provides"]["steps"], [])
        self.assertEqual(manifest["provides"]["workflows"], [])
        self.assertNotIn("integration:", text)

    def test_preset_has_four_templates_and_ten_design_only_commands(self):
        text = (PRESET / "preset.yml").read_text(encoding="utf-8")
        manifest = yaml.safe_load(text)
        entries = manifest["provides"]["templates"]
        templates = [item for item in entries if item["type"] == "template"]
        commands = [item for item in entries if item["type"] == "command"]
        self.assertEqual([item["name"] for item in templates], [
            "spec-template", "reflections-template", "plan-template", "tasks-template",
        ])
        self.assertEqual(len(commands), 10)
        self.assertEqual(sum(item["strategy"] == "append" for item in entries), 1)
        self.assertEqual(sum(item["strategy"] == "replace" for item in entries), 13)
        self.assertEqual(manifest["preset"]["version"], "0.9.0")
        self.assertFalse((PRESET / "templates/abstract-template.md").exists())
        self.assertFalse((PRESET / "templates/implementation-template.md").exists())
        self.assertIn("embedded interface", templates[0]["description"])
        self.assertIn("architecture-zoom", templates[0]["description"])
        self.assertIn("merged-small removal", templates[1]["description"])

    def test_extension_and_preset_install_from_source_without_removed_templates(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            subprocess.run(
                ["specify", "init", "--here", "--force", "--ignore-agent-tools", "--integration", "codex", "--integration-options=--skills"],
                cwd=root, check=True, capture_output=True, text=True,
            )
            subprocess.run(
                ["specify", "extension", "add", str(EXTENSION), "--dev"],
                cwd=root, check=True, capture_output=True, text=True,
            )
            subprocess.run(
                ["specify", "preset", "add", "--dev", str(PRESET)],
                cwd=root, check=True, capture_output=True, text=True,
            )
            installed_preset = root / ".specify/presets/concorde"
            self.assertTrue((installed_preset / "preset.yml").is_file())
            self.assertTrue((root / ".specify/extensions/concorde/extension.yml").is_file())
            self.assertFalse((installed_preset / "templates/abstract-template.md").exists())
            self.assertFalse((installed_preset / "templates/implementation-template.md").exists())
            self.assertIn('"concorde"', (root / ".specify/presets/.registry").read_text(encoding="utf-8"))
            self.assertIn('"concorde"', (root / ".specify/extensions/.registry").read_text(encoding="utf-8"))

            for command in ("specify", "clarify", "checklist", "plan", "tasks", "implement", "analyze", "converge", "taskstoissues", "fast-loop"):
                rendered = (root / f".agents/skills/speckit-{command}/SKILL.md").read_text(encoding="utf-8")
                self.assertIn("Protocol 12", rendered, command)

    def test_templates_keep_attempt_memory_and_source_authority_distinct(self):
        design = (PRESET / "templates/design-template.md").read_text(encoding="utf-8")
        plan = (PRESET / "templates/plan-template.md").read_text(encoding="utf-8")
        tasks = (PRESET / "templates/tasks-template.md").read_text(encoding="utf-8")
        self.assertIn("complete durable specification", design)
        self.assertIn("## Interfaces", design)
        self.assertIn("## Architecture Zoom", design)
        self.assertIn("current source code", plan)
        self.assertIn("writes only under the returned `attempt_dir`", plan)
        self.assertIn("module `architecture.md`", tasks)
        self.assertIn("direct feature file", tasks)
        self.assertIn("cleanup-only delivery", tasks)
        self.assertNotRegex("\n".join((design, plan, tasks)), re.compile(r"(?:abstract|implementation)-template"))

    def test_reflection_template_keeps_log_v1_with_v3_high_water_lifecycle(self):
        body = (PRESET / "templates/reflections-template.md").read_text(encoding="utf-8")
        for value in (
            "<!-- concorde-reflection-high-water: R-000 -->",
            "Reflection-triage/v3",
            "--allocate-id",
            "`allocated_id`",
            "--remove-merged",
            "without adding Status/Note",
        ):
            self.assertIn(value, body, value)
        self.assertIn("Grammar (Concorde Reflection Log v1)", body)


if __name__ == "__main__":
    unittest.main()
