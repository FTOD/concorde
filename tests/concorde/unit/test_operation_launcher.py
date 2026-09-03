from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import REPOSITORY_ROOT


RUNNER = REPOSITORY_ROOT / "scripts/run-operation.py"


class OperationLauncherTests(unittest.TestCase):
    def test_source_runtime_check_uses_checkout_venv(self):
        result = subprocess.run(
            [
                sys.executable,
                str(RUNNER),
                "operations/concorde-plan/operation.py",
                "--runtime-check",
            ],
            cwd=REPOSITORY_ROOT,
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["operation"], "concorde-plan")
        self.assertEqual(Path(payload["venv"]), REPOSITORY_ROOT / ".venv")
        self.assertEqual(Path(payload["python"]), REPOSITORY_ROOT / ".venv/bin/python")

    def test_installed_layout_fails_closed_when_managed_venv_is_missing(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            runner = root / ".concorde/framework/scripts/run-operation.py"
            operation = root / ".concorde/framework/operations/example/operation.py"
            runner.parent.mkdir(parents=True)
            operation.parent.mkdir(parents=True)
            shutil.copy2(RUNNER, runner)
            operation.write_text("OPERATION_NAME = 'example'\n", encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(runner), str(operation), "--runtime-check"],
                cwd=root,
                text=True,
                capture_output=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn(".concorde/.venv", result.stderr)

    def test_operation_must_resolve_below_the_colocated_framework(self):
        result = subprocess.run(
            [sys.executable, str(RUNNER), "README.md", "--runtime-check"],
            cwd=REPOSITORY_ROOT,
            text=True,
            capture_output=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("operations", result.stderr)


if __name__ == "__main__":
    unittest.main()
