from __future__ import annotations

import subprocess
import unittest
from pathlib import Path

import yaml


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
RETIRED_PRESET_ID = "concorde" + "-core"


class PresetIdentityContractTests(unittest.TestCase):
    def test_preset_and_extension_share_a_type_qualified_identity(self) -> None:
        preset_path = REPOSITORY_ROOT / "presets/concorde/preset.yml"
        extension_path = REPOSITORY_ROOT / "extensions/concorde/extension.yml"

        self.assertTrue(preset_path.is_file())
        self.assertTrue(extension_path.is_file())
        preset = yaml.safe_load(preset_path.read_text(encoding="utf-8"))
        extension = yaml.safe_load(extension_path.read_text(encoding="utf-8"))

        self.assertEqual(preset["preset"]["id"], "concorde")
        self.assertEqual(extension["extension"]["id"], "concorde")

    def test_retired_preset_identity_is_absent_from_tracked_paths_and_content(self) -> None:
        listed = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=REPOSITORY_ROOT,
            check=True,
            capture_output=True,
        ).stdout.decode("utf-8").split("\0")
        forbidden_paths = sorted(
            path
            for path in listed
            if path and (REPOSITORY_ROOT / path).exists() and RETIRED_PRESET_ID in path
        )
        self.assertEqual(forbidden_paths, [])

        content = subprocess.run(
            ["git", "grep", "-n", "-I", "-F", RETIRED_PRESET_ID, "--", "."],
            cwd=REPOSITORY_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertIn(content.returncode, {0, 1})
        self.assertEqual(content.stdout, "")


if __name__ == "__main__":
    unittest.main()
