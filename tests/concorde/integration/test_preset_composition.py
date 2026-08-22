import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import REPOSITORY_ROOT


class PresetCompositionTests(unittest.TestCase):
    def test_fragments_are_append_only_and_preserve_one_spec(self):
        manifest = (REPOSITORY_ROOT / "presets/concorde-core/preset.yml").read_text()
        self.assertEqual(manifest.count('type: "template"'), 3)
        self.assertEqual(manifest.count('type: "command"'), 9)
        self.assertEqual(manifest.count('strategy: "append"'), 12)
        fragments = REPOSITORY_ROOT / "presets/concorde-core/templates"
        combined = "\n".join(path.read_text() for path in fragments.glob("*.md"))
        self.assertIn("single canonical", combined)
        self.assertIn("representative", combined.lower())
        self.assertIn("contracts", combined.lower())
        self.assertNotIn("# Feature Specification:", combined)
        command_fragments = REPOSITORY_ROOT / "presets/concorde-core/commands"
        self.assertEqual(len(tuple(command_fragments.glob("*.md"))), 9)

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
                ["specify", "preset", "add", "--dev", str(REPOSITORY_ROOT / "presets/concorde-core")],
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
            self.assertIn("Concorde Architecture Alignment", resolved)
            self.assertIn("User Scenarios", resolved)


if __name__ == "__main__":
    unittest.main()
