from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import REPOSITORY_ROOT, RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.command_assets import CommandAssetError, render_command, render_commands  # noqa: E402


class CommandProjectionIntegrationTests(unittest.TestCase):
    def test_root_commands_render_for_both_integrations_without_composition(self):
        manifest = json.loads((REPOSITORY_ROOT / "concorde.json").read_text())
        for integration in ("codex", "claude"):
            with self.subTest(integration=integration):
                rendered = render_commands(REPOSITORY_ROOT, integration, "")
                self.assertEqual(len(rendered), len(manifest["commands"]))
                self.assertTrue(all('author: "concorde"' in content for content in rendered.values()))
                self.assertTrue(all(".specify/" not in content for content in rendered.values()))

    def test_source_and_installed_prefixes_change_paths_not_phase_intent(self):
        command = REPOSITORY_ROOT / "commands/speckit.plan.md"
        source = render_command(command, "codex", "")
        installed = render_command(command, "codex", ".concorde/framework")
        self.assertIn("python3 scripts/workspace.py --phase plan", source)
        self.assertIn("python3 .concorde/framework/scripts/workspace.py --phase plan", installed)
        self.assertIn("./templates/plan-template.md", source)
        self.assertIn(".concorde/framework/templates/plan-template.md", installed)
        for marker in ("Protocol 12", "Concorde Architecture Gate", "Completion gate"):
            self.assertIn(marker, source)
            self.assertIn(marker, installed)

    def test_feature_template_is_complete_and_not_a_fragment(self):
        body = (REPOSITORY_ROOT / "templates/feature-template.md").read_text()
        for section in (
            "# Feature Design", "## Outcome and Scope", "## Usage", "## User Scenarios & Testing",
            "## Interfaces", "## Architecture Zoom", "## Related Features", "## Requirements", "## Success Criteria",
        ):
            self.assertIn(section, body)
        self.assertTrue(body.startswith("---\n"))
        self.assertNotIn("append", body.lower())

    def test_invalid_command_metadata_or_script_path_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            invalid_metadata = root / "speckit.invalid.md"
            invalid_metadata.write_text('---\ndescription: "Invalid"\npriority: 10\n---\n\nBody.\n')
            with self.assertRaisesRegex(CommandAssetError, "unsupported metadata"):
                render_command(invalid_metadata, "codex")
            unsafe = root / "speckit.unsafe.md"
            unsafe.write_text('---\ndescription: "Unsafe"\nscripts:\n  py: ../escape.py\n---\n\nRun {SCRIPT}.\n')
            with self.assertRaisesRegex(CommandAssetError, "safe package-relative"):
                render_command(unsafe, "codex")


if __name__ == "__main__":
    unittest.main()
