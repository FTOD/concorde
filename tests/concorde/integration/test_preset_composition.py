import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import REPOSITORY_ROOT


class PresetCompositionTests(unittest.TestCase):
    def test_templates_append_and_commands_replace_while_preserving_one_spec(self):
        manifest = (REPOSITORY_ROOT / "presets/concorde/preset.yml").read_text()
        self.assertEqual(manifest.count('type: "template"'), 4)
        self.assertEqual(manifest.count('type: "command"'), 10)
        self.assertEqual(manifest.count('strategy: "append"'), 1)
        self.assertEqual(manifest.count('strategy: "replace"'), 13)
        fragments = REPOSITORY_ROOT / "presets/concorde/templates"
        combined = "\n".join(path.read_text() for path in fragments.glob("*.md"))
        self.assertIn("complete durable specification", combined)
        self.assertIn("representative", combined.lower())
        self.assertIn("interfaces", combined.lower())
        self.assertNotIn("# Feature Specification:", combined)
        command_fragments = REPOSITORY_ROOT / "presets/concorde/commands"
        self.assertEqual(len(tuple(command_fragments.glob("*.md"))), 10)
        for command in command_fragments.glob("*.md"):
            content = command.read_text(encoding="utf-8")
            self.assertIn("## Workspace gate", content)
            self.assertIn(".specify/extensions/concorde/scripts/python/workspace.py", content)
            self.assertGreater(len(content.splitlines()), 35)
        for name in ("speckit.specify.md", "speckit.clarify.md", "speckit.checklist.md", "speckit.implement.md"):
            content = (command_fragments / name).read_text(encoding="utf-8")
            self.assertNotIn("FEATURE_DIR/checklists", content)
            self.assertIn("checklists_dir", content.lower())

    def test_resolver_composes_core_plus_concorde_fragment(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            subprocess.run(
                ["specify", "init", "--here", "--force", "--ignore-agent-tools", "--integration", "codex", "--integration-options=--skills"],
                cwd=root,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["specify", "preset", "add", "--dev", str(REPOSITORY_ROOT / "presets/concorde")],
                cwd=root,
                check=True,
                capture_output=True,
            )
            resolver_environment = os.environ.copy()
            resolver_environment.pop("VIRTUAL_ENV", None)
            resolver_environment["PATH"] = "/usr/local/bin:/usr/bin:/bin"
            resolved = subprocess.run(
                [str(root / ".specify/scripts/bash/resolve-template.sh"), "spec-template"],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
                env=resolver_environment,
            ).stdout
        self.assertIn("Concorde Feature Profile", resolved)
        self.assertIn("User Scenarios", resolved)
        self.assertIn("## Interfaces", resolved)
        self.assertIn("## Architecture Zoom", resolved)


if __name__ == "__main__":
    unittest.main()
