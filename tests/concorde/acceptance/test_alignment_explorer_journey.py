from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import CONTEXT_PROJECT, REPOSITORY_ROOT


def bytes_by_path(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


class AlignmentExplorerJourneyAcceptance(unittest.TestCase):
    def test_source_launcher_browses_specification_without_mutation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            shutil.copytree(CONTEXT_PROJECT, root)
            before = bytes_by_path(root)
            result = subprocess.run(
                [
                    sys.executable,
                    str(REPOSITORY_ROOT / "scripts/concorde.py"),
                    "--project-root", str(root),
                    "explore", "feature.example.deliver",
                ],
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["tool"], "explore")
            self.assertEqual(payload["schema_version"], 2)
            self.assertEqual(payload["status"], "success")
            self.assertEqual(payload["target"], "feature.example.deliver")
            self.assertEqual({record["status"] for record in payload["result"]["alignment"]["records"]}, {"unknown"})
            self.assertEqual(before, bytes_by_path(root))

    def test_cli_help_advertises_native_explore_operation(self):
        result = subprocess.run(
            [sys.executable, str(REPOSITORY_ROOT / "scripts/concorde.py"), "--help"],
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertIn("explore", result.stdout)


if __name__ == "__main__":
    unittest.main()
