import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import REPOSITORY_ROOT


class ManifestContractTests(unittest.TestCase):
    def test_extension_declares_seven_commands_and_four_scripts(self):
        manifest = (REPOSITORY_ROOT / "extensions/concorde/extension.yml").read_text(encoding="utf-8")
        self.assertEqual(manifest.count('- name: "speckit.concorde.'), 7)
        self.assertEqual(manifest.count('runtime: "'), 4)
        self.assertIn('name: "speckit.concorde.ask"', manifest)
        self.assertIn('file: "commands/speckit.concorde.ask.md"', manifest)

    def test_bundle_is_native_and_exactly_two_components(self):
        manifest = (REPOSITORY_ROOT / "bundles/concorde-starter/bundle.yml").read_text()
        self.assertIn('id: "concorde-starter"', manifest)
        self.assertIn('version: "0.1.0"', manifest)
        self.assertEqual(len(re.findall(r'^    - id:', manifest, re.MULTILINE)), 2)
        self.assertRegex(manifest, r"steps: \[\]")
        self.assertRegex(manifest, r"workflows: \[\]")
        self.assertNotIn("integration:", manifest)

    def test_extension_and_preset_install_from_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            subprocess.run(
                ["specify", "init", "--here", "--force", "--ignore-agent-tools", "--integration", "codex", "--integration-options=--skills"],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                ["specify", "extension", "add", str(REPOSITORY_ROOT / "extensions/concorde"), "--dev"],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                ["specify", "preset", "add", "--dev", str(REPOSITORY_ROOT / "presets/concorde-core")],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertTrue((root / ".specify/extensions/concorde/extension.yml").is_file())
            self.assertTrue((root / ".specify/presets/concorde-core/preset.yml").is_file())

    def test_preset_has_three_append_templates_one_design_template_and_nine_replace_commands(self):
        manifest = (REPOSITORY_ROOT / "presets/concorde-core/preset.yml").read_text(encoding="utf-8")
        self.assertEqual(manifest.count('type: "template"'), 4)
        self.assertEqual(manifest.count('type: "command"'), 9)
        self.assertEqual(manifest.count('strategy: "append"'), 3)
        self.assertEqual(manifest.count('strategy: "replace"'), 10)
        self.assertEqual(
            (REPOSITORY_ROOT / ".specify/templates/design-template.md").read_bytes(),
            (REPOSITORY_ROOT / "presets/concorde-core/templates/design-template.md").read_bytes(),
        )
        for command in (
            "specify",
            "clarify",
            "checklist",
            "plan",
            "tasks",
            "implement",
            "analyze",
            "converge",
            "taskstoissues",
        ):
            self.assertIn(f'name: "speckit.{command}"', manifest)
        self.assertIn("temporal implementation/checklists/", manifest)
        self.assertNotIn("checklists at the durable feature root", manifest)

    def test_plan_and_checklist_templates_preserve_temporal_checklist_authority(self):
        preset_plan = (REPOSITORY_ROOT / "presets/concorde-core/templates/plan-template.md").read_text(encoding="utf-8")
        local_plan = (REPOSITORY_ROOT / ".specify/templates/plan-template.md").read_text(encoding="utf-8")
        checklist = (REPOSITORY_ROOT / ".specify/templates/checklist-template.md").read_text(encoding="utf-8")
        self.assertIn("implementation/checklists/", preset_plan)
        self.assertNotIn("`contracts/`, and `checklists/`", preset_plan)
        self.assertIn("├── design.md", local_plan)
        self.assertIn("    ├── checklists/", local_plan)
        self.assertNotIn("\n├── checklists/", local_plan)
        self.assertIn("implementation/checklists/requirements.md", checklist)


if __name__ == "__main__":
    unittest.main()
