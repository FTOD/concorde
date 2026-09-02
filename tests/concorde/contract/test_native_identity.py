from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


class NativeIdentityContractTests(unittest.TestCase):
    def test_single_manifest_owns_one_concorde_identity(self):
        manifest = json.loads((REPOSITORY_ROOT / "concorde.json").read_text())
        self.assertEqual(manifest["name"], "concorde")
        self.assertEqual(manifest["version"], "1.1.0")
        self.assertEqual(manifest["command_namespace"], "concorde")
        self.assertIn("Concorde owns", manifest["format_lineage"])

    def test_removed_host_package_paths_are_not_tracked(self):
        tracked = subprocess.run(
            ["git", "ls-files", "-z"], cwd=REPOSITORY_ROOT, check=True, capture_output=True
        ).stdout.decode().split("\0")
        forbidden = (".specify/", "presets/", "extensions/", "bundles/", "catalogs/")
        self.assertEqual([
            path for path in tracked
            if path.startswith(forbidden) and (REPOSITORY_ROOT / path).exists()
        ], [])

    def test_development_dependencies_do_not_include_host_cli(self):
        pyproject = (REPOSITORY_ROOT / "pyproject.toml").read_text().lower()
        lock = (REPOSITORY_ROOT / "uv.lock").read_text().lower()
        self.assertNotIn("specify-cli", pyproject)
        self.assertNotIn('name = "specify-cli"', lock)

    def test_compatibility_command_names_resolve_to_root_files(self):
        manifest = json.loads((REPOSITORY_ROOT / "concorde.json").read_text())
        self.assertEqual(len(manifest["commands"]), 16)
        self.assertTrue(all(name.startswith("concorde.") for name in manifest["commands"]))
        self.assertTrue(all((REPOSITORY_ROOT / "commands" / f"{name}.md").is_file() for name in manifest["commands"]))


if __name__ == "__main__":
    unittest.main()
