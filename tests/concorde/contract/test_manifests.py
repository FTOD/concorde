import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import REPOSITORY_ROOT


class ManifestContractTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
