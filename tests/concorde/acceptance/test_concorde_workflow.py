import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import hashlib
from pathlib import Path

from tests.concorde.support.paths import CONTEXT_PROJECT, REPOSITORY_ROOT


class ConcordeWorkflowAcceptance(unittest.TestCase):
    def test_standard_selection_routes_nested_feature_without_root_aliases(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            shutil.copytree(CONTEXT_PROJECT, root)
            adapter = REPOSITORY_ROOT / "extensions/concorde/scripts/python/workspace.py"
            selected = subprocess.run(
                [sys.executable, str(adapter), "--project-root", str(root), "--feature-directory", "specs/example/features/001-deliver", "--persist", "--phase", "plan"],
                check=True,
                text=True,
                capture_output=True,
            )
            payload = json.loads(selected.stdout)
            self.assertEqual(payload["status"], "selected")
            self.assertEqual(payload["phase_root"], "specs/example/features/001-deliver/attempt")
            self.assertTrue(payload["workspace"]["plan"].endswith("/attempt/plan.md"))
            self.assertEqual(json.loads((root / ".specify/feature.json").read_text())["feature_directory"], "specs/example/features/001-deliver")
            feature_root = root / payload["workspace"]["feature_directory"]
            self.assertFalse((feature_root / "plan.md").exists())
            self.assertFalse((feature_root / "tasks.md").exists())
            resolved = subprocess.run(
                [sys.executable, str(adapter), "--project-root", str(root), "--phase", "specify"],
                check=True,
                text=True,
                capture_output=True,
            )
            self.assertEqual(json.loads(resolved.stdout)["status"], "resolved")
            launcher = REPOSITORY_ROOT / "extensions/concorde/scripts/python/concorde.py"
            removed = subprocess.run(
                [sys.executable, str(launcher), "--project-root", str(root), "feature", "select", "feature.example.deliver"],
                text=True,
                capture_output=True,
            )
            self.assertNotEqual(removed.returncode, 0)

    def test_validation_is_identical_across_portable_launchers_and_read_only(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            shutil.copytree(CONTEXT_PROJECT, root)
            before = {path.relative_to(root): hashlib.sha256(path.read_bytes()).hexdigest() for path in root.rglob("*") if path.is_file()}
            python_launcher = REPOSITORY_ROOT / "extensions/concorde/scripts/python/concorde.py"
            bash_launcher = REPOSITORY_ROOT / "extensions/concorde/scripts/bash/concorde.sh"
            outputs = []
            for command in (
                [sys.executable, str(python_launcher)],
                [str(bash_launcher)],
                [sys.executable, str(python_launcher)],
            ):
                result = subprocess.run(command + ["--project-root", str(root), "validate"], text=True, capture_output=True)
                outputs.append((result.returncode, result.stdout))
            self.assertEqual(outputs[0], outputs[1])
            self.assertEqual(outputs[1], outputs[2])
            after = {path.relative_to(root): hashlib.sha256(path.read_bytes()).hexdigest() for path in root.rglob("*") if path.is_file()}
            self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
