import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import hashlib
from pathlib import Path

from tests.concorde.support.paths import CONTEXT_PROJECT, REPOSITORY_ROOT


class CoreWorkflowAcceptance(unittest.TestCase):
    def test_propose_select_and_route_nested_feature_without_root_aliases(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            shutil.copytree(CONTEXT_PROJECT, root)
            launcher = REPOSITORY_ROOT / "extensions/concorde/scripts/python/concorde.py"
            proposed = subprocess.run(
                [sys.executable, str(launcher), "--project-root", str(root), "feature", "create", "--module-id", "module.example.api", "--feature-id", "feature.example.api.observe", "--short-name", "observe-health"],
                check=True,
                text=True,
                capture_output=True,
            )
            proposal = json.loads(proposed.stdout)
            self.assertEqual(proposal["status"], "proposal")
            self.assertFalse((root / proposal["workspace"]["feature_directory"]).exists())
            selected = subprocess.run(
                [sys.executable, str(launcher), "--project-root", str(root), "feature", "select", "feature.example.deliver"],
                check=True,
                text=True,
                capture_output=True,
            )
            payload = json.loads(selected.stdout)
            self.assertEqual(payload["status"], "selected")
            self.assertTrue(payload["workspace"]["plan"].endswith("/implementation/plan.md"))
            feature_root = root / payload["workspace"]["feature_directory"]
            self.assertFalse((feature_root / "plan.md").exists())
            self.assertFalse((feature_root / "tasks.md").exists())

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
