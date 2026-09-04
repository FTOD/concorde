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
    def test_standard_selection_routes_direct_feature_to_stable_id_control_attempt(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            shutil.copytree(CONTEXT_PROJECT, root)
            adapter = REPOSITORY_ROOT / "scripts/workspace.py"
            selected = subprocess.run(
                [sys.executable, str(adapter), "--project-root", str(root), "--feature-path", "specs/example/features/001-deliver.md", "--persist", "--phase", "plan"],
                check=True,
                text=True,
                capture_output=True,
            )
            payload = json.loads(selected.stdout)
            self.assertEqual(payload["status"], "selected")
            self.assertEqual(payload["phase_root"], ".concorde/attempts/feature.example.deliver")
            self.assertEqual(payload["workspace"]["plan"], ".concorde/attempts/feature.example.deliver/plan.md")
            self.assertEqual(json.loads((root / ".concorde/feature.json").read_text())["feature_path"], "specs/example/features/001-deliver.md")
            feature_path = root / payload["workspace"]["feature_path"]
            self.assertTrue(feature_path.is_file())
            self.assertFalse((feature_path.parent / feature_path.stem).exists())
            resolved = subprocess.run(
                [sys.executable, str(adapter), "--project-root", str(root), "--phase", "specify"],
                check=True,
                text=True,
                capture_output=True,
            )
            self.assertEqual(json.loads(resolved.stdout)["status"], "resolved")
            launcher = REPOSITORY_ROOT / "scripts/concorde.py"
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
            python_launcher = REPOSITORY_ROOT / "scripts/concorde.py"
            bash_launcher = REPOSITORY_ROOT / "scripts/concorde.sh"
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
