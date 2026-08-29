import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import REPOSITORY_ROOT


class ManifestContractTests(unittest.TestCase):
    def test_extension_declares_five_commands_and_four_scripts(self):
        manifest = (REPOSITORY_ROOT / "extensions/concorde/extension.yml").read_text(encoding="utf-8")
        self.assertEqual(manifest.count('- name: "speckit.concorde.'), 5)
        self.assertEqual(manifest.count('runtime: "'), 4)
        self.assertIn('name: "speckit.concorde.ask"', manifest)
        self.assertIn('file: "commands/speckit.concorde.ask.md"', manifest)

    def test_bundle_is_native_and_exactly_two_components(self):
        manifest = (REPOSITORY_ROOT / "bundles/concorde-bundle/bundle.yml").read_text()
        self.assertIn('id: "concorde-bundle"', manifest)
        self.assertIn('version: "0.3.0"', manifest)
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

    def test_preset_has_three_append_templates_three_replace_templates_and_nine_replace_commands(self):
        manifest = (REPOSITORY_ROOT / "presets/concorde-core/preset.yml").read_text(encoding="utf-8")
        self.assertEqual(manifest.count('type: "template"'), 6)
        self.assertEqual(manifest.count('type: "command"'), 9)
        self.assertEqual(manifest.count('strategy: "append"'), 3)
        self.assertEqual(manifest.count('strategy: "replace"'), 12)
        self.assertIn('name: "abstract-template"', manifest)
        self.assertIn('name: "implementation-template"', manifest)
        for template in ("abstract-template", "implementation-template"):
            resolved = subprocess.run(
                ["specify", "preset", "resolve", template],
                cwd=REPOSITORY_ROOT,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.replace("\n", "")
            self.assertIn(f"presets/concorde-core/templates/{template}.md", resolved)
            self.assertTrue((REPOSITORY_ROOT / f".specify/presets/concorde-core/templates/{template}.md").is_file())
            self.assertFalse((REPOSITORY_ROOT / f".specify/templates/{template}.md").exists())
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
        self.assertIn("temporal attempt/checklists/", manifest)
        self.assertNotIn("checklists at the durable feature root", manifest)

    def test_plan_and_checklist_templates_preserve_temporal_checklist_authority(self):
        preset_plan = (REPOSITORY_ROOT / "presets/concorde-core/templates/plan-template.md").read_text(encoding="utf-8")
        local_plan = (REPOSITORY_ROOT / ".specify/templates/plan-template.md").read_text(encoding="utf-8")
        checklist = (REPOSITORY_ROOT / ".specify/templates/checklist-template.md").read_text(encoding="utf-8")
        self.assertIn("attempt/checklists/", preset_plan)
        self.assertNotIn("`contracts/`, and `checklists/`", preset_plan)
        self.assertIn("├── abstract.md", local_plan)
        self.assertIn("├── design.md", local_plan)
        self.assertIn("├── implementation.md", local_plan)
        self.assertIn("└── attempt/", local_plan)
        self.assertIn("    ├── checklists/", local_plan)
        self.assertNotIn("\n├── checklists/", local_plan)
        self.assertIn("attempt/checklists/requirements.md", checklist)


if __name__ == "__main__":
    unittest.main()
