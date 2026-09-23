"""The pytest timing plugin records run reasons, input fingerprints and separate time figures."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from concorde.spec.verification import verifies
from tests.concorde.support.paths import REPOSITORY_ROOT


class PytestTimingTests(unittest.TestCase):
    @verifies("scenario.concorde.test-timing")
    def test_runner_fingerprints_and_default_cli(self):
        from tests.concorde.support import pytest_timing as runner

        selected = ["tests/concorde/spec/test_typed_data.py::TypedDataTests::test_x"]
        first = runner.fingerprint(selected)
        self.assertEqual(first, runner.fingerprint(selected))
        self.assertNotEqual(first["digest"], runner.fingerprint(["other"])["digest"])
        read_bytes = Path.read_bytes
        role = REPOSITORY_ROOT / "protocol/boundaries.md"

        def changed_role(path):
            content = read_bytes(path)
            return content + b"\nchanged role\n" if path == role else content

        with patch.object(Path, "read_bytes", changed_role):
            changed = runner.fingerprint(selected)
        self.assertNotEqual(first["input"], changed["input"])
        with tempfile.TemporaryDirectory() as directory:
            command = [
                sys.executable,
                "-m",
                "pytest",
                "-p",
                "no:cacheprovider",
                "-n",
                "2",
                "tests/concorde/spec/test_typed_data.py",
                "tests/concorde/issues/test_reporting.py",
            ]
            report = Path(directory) / "report.json"
            # A caller may pass no reason, scope, phase or attempt.
            result = subprocess.run(
                [*command, f"--json={report}"],
                cwd=REPOSITORY_ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            value = json.loads(report.read_text())
            self.assertEqual(value["reason"], "manual")
            self.assertEqual(value["scope"], "unspecified")
            self.assertEqual(value["phase"], "unspecified")
            self.assertEqual(value["attempt"], 1)
            self.assertIsNone(value["prior_run_id"])
            self.assertIsNone(value["same_declared_inputs"])
            self.assertTrue(all(s["layer"] == "C" for s in value["spans"]))
            self.assertEqual(
                {"test.total", "test.discovery", "test.unit"},
                {s["name"] for s in value["spans"]},
            )
            self.assertEqual(value["totals"]["tests"], value["totals"]["collected"])
            self.assertEqual(value["totals"]["failed"] + value["totals"]["error"], 0)
            self.assertEqual(value["totals"]["workers"], 2)
            self.assertGreaterEqual(value["discovery_seconds"], 0)
            self.assertGreaterEqual(
                value["elapsed_seconds"], value["discovery_seconds"]
            )
            self.assertIn("not elapsed wall time", value["timing_note"])
            units = {unit["nodeid"]: unit for unit in value["units"]}
            self.assertEqual(len(units), value["totals"]["tests"])
            # Elapsed is the controller's own interval; unit seconds are summed concurrent work.
            self.assertGreaterEqual(
                value["elapsed_seconds"],
                max(unit["execution_seconds"] for unit in units.values()),
            )
            self.assertAlmostEqual(
                value["totals"]["unit_seconds"],
                sum(unit["execution_seconds"] for unit in units.values()),
                places=1,
            )
            for unit in units.values():
                self.assertIsNone(unit["setup_seconds"])
                self.assertGreaterEqual(unit["queue_seconds"], 0)
                self.assertGreaterEqual(unit["execution_seconds"], 0)
                self.assertEqual(
                    {"setup", "call", "teardown"}, set(unit["phase_seconds"])
                )
            # An explicitly scoped rerun recognizes unchanged declared inputs.
            # Values are joined with "=": an existing prior path as a separate argument would
            # be taken for a test path while pytest decides its rootdir.
            again = Path(directory) / "again.json"
            result = subprocess.run(
                [
                    *command,
                    f"--json={again}",
                    f"--prior={report}",
                    "--reason=failure",
                    "--scope=targeted",
                    "--phase=maintenance",
                    "--attempt=2",
                ],
                cwd=REPOSITORY_ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            second = json.loads(again.read_text())
            self.assertEqual(second["prior_run_id"], value["run_id"])
            self.assertEqual(
                (second["reason"], second["scope"], second["phase"], second["attempt"]),
                ("failure", "targeted", "maintenance", 2),
            )
            self.assertEqual(
                second["fingerprint"]["digest"], value["fingerprint"]["digest"]
            )
            self.assertEqual(
                second["same_declared_inputs"],
                True if value["fingerprint"]["input_complete"] else None,
            )
            self.assertIn("same declared inputs as prior run", result.stdout)
            self.assertFalse(second["fingerprint"]["environment_complete"])


if __name__ == "__main__":
    unittest.main()
