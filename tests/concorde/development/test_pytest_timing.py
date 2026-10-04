"""The pytest timing plugin records run reasons, input fingerprints and separate time figures.

Every case runs the plugin over a small project written to a temporary directory, never over this
checkout: tests running in parallel change files of the checkout, and a fingerprint of it could
then differ between two readings of the same run.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from concorde.spec.verification import verifies
from tests.concorde.support.paths import REPOSITORY_ROOT

SAMPLE_TESTS = """import unittest


class SampleTests(unittest.TestCase):
    def test_one(self):
        pass

    def test_two(self):
        pass

    def test_three(self):
        pass
"""

SUBTEST_TESTS = """import unittest


class SubtestTests(unittest.TestCase):
    def test_subtests(self):
        for value in range(3):
            with self.subTest(value=value):
                self.assertNotEqual(value, 1)

    def test_plain(self):
        pass
"""


class PytestTimingTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        files = {
            "conftest.py": 'pytest_plugins = ["tests.concorde.support.pytest_timing"]\n',
            "src/sample.py": "VALUE = 1\n",
            "protocol/boundaries.md": "# Boundaries\n",
            "uv.lock": "version = 1\n",
            "checks/test_sample.py": SAMPLE_TESTS,
        }
        for name, content in files.items():
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
        subprocess.run(["git", "init", "--quiet"], cwd=self.root, check=True)
        self.reports = self.root / "reports"
        self.reports.mkdir()
        (self.root / ".git/info/exclude").write_text("reports/\n")

    def pytest(self, *arguments: str, workers: int = 2) -> subprocess.CompletedProcess:
        environment = dict(os.environ, PYTHONPATH=str(REPOSITORY_ROOT))
        command = [sys.executable, "-m", "pytest", "-p", "no:cacheprovider"]
        if workers:
            command += ["-n", str(workers)]
        return subprocess.run(
            [*command, *arguments],
            cwd=self.root,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )

    def run_report(self, name: str, *arguments: str, workers: int = 2) -> dict:
        report = self.reports / name
        result = self.pytest(
            "checks/test_sample.py", f"--json={report}", *arguments, workers=workers
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.output = result.stdout
        return json.loads(report.read_text())

    @verifies("scenario.concorde.test-timing")
    def test_runner_fingerprints_and_default_cli(self):
        from tests.concorde.support import pytest_timing as runner

        # The canonical encoding of development.md#req.concorde.test-fingerprints.
        self.assertEqual(
            "8aa528e6d583124b22694dd542edd2390a7c00000f0c58574a450be32829bbf5",
            runner.fingerprint(["t.py::A::test_one"], self.root)["tests"],
        )
        selected = ["checks/test_sample.py::SampleTests::test_one"]
        first = runner.fingerprint(selected, self.root)
        self.assertTrue(first["input_complete"])
        self.assertEqual(first, runner.fingerprint(selected, self.root))
        self.assertNotEqual(
            first["tests"], runner.fingerprint(["other"], self.root)["tests"]
        )
        (self.root / "protocol/boundaries.md").write_text(
            "# Boundaries\nchanged role\n"
        )
        changed = runner.fingerprint(selected, self.root)
        self.assertNotEqual(first["input"], changed["input"])
        self.assertEqual(first["lock"], changed["lock"])
        (self.root / "uv.lock").write_text("version = 2\n")
        self.assertNotEqual(
            first["lock"], runner.fingerprint(selected, self.root)["lock"]
        )
        # A file outside the declared inputs changes no fingerprint.
        before = runner.fingerprint(selected, self.root)
        (self.root / "notes.txt").write_text("not an input\n")
        self.assertEqual(before, runner.fingerprint(selected, self.root))
        # The environment records Python's effective bytecode setting, however it was set.
        with patch.object(runner.sys, "dont_write_bytecode", True):
            self.assertTrue(
                runner.fingerprint(selected, self.root)["environment_facts"][
                    "bytecode_disabled"
                ]
            )
        with patch.object(runner.sys, "dont_write_bytecode", False):
            self.assertFalse(
                runner.fingerprint(selected, self.root)["environment_facts"][
                    "bytecode_disabled"
                ]
            )

        # A caller may pass no reason, scope, phase or attempt.
        value = self.run_report("report.json")
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
        self.assertEqual(value["totals"]["tests"], 3)
        self.assertEqual(value["totals"]["failed"] + value["totals"]["error"], 0)
        self.assertEqual(value["totals"]["workers"], 2)
        self.assertGreaterEqual(value["discovery_seconds"], 0)
        self.assertGreaterEqual(value["elapsed_seconds"], value["discovery_seconds"])
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
            self.assertEqual({"setup", "call", "teardown"}, set(unit["phase_seconds"]))
        fingerprint = value["fingerprint"]
        self.assertTrue(fingerprint["input_complete"])
        self.assertFalse(fingerprint["environment_complete"])
        self.assertEqual(
            {"digest", "input", "tests", "runtime", "lock", "environment"}
            - set(fingerprint),
            set(),
        )

    @verifies("scenario.concorde.test-prior-unchanged")
    def test_prior_with_unchanged_inputs(self):
        value = self.run_report("report.json")
        # Values are joined with "=": an existing prior path as a separate argument would be
        # taken for a test path while pytest decides its rootdir.
        second = self.run_report(
            "again.json",
            f"--prior={self.reports / 'report.json'}",
            "--reason=failure",
            "--scope=targeted",
            "--phase=maintenance",
            "--attempt=2",
        )
        self.assertEqual(second["prior_run_id"], value["run_id"])
        self.assertEqual(
            (second["reason"], second["scope"], second["phase"], second["attempt"]),
            ("failure", "targeted", "maintenance", 2),
        )
        self.assertEqual(
            second["fingerprint"]["digest"], value["fingerprint"]["digest"]
        )
        self.assertIs(second["same_declared_inputs"], True)
        self.assertIn("same declared inputs as prior run", self.output)

    @verifies("scenario.concorde.test-prior-changed")
    def test_prior_with_changed_input(self):
        value = self.run_report("report.json")
        (self.root / "src/sample.py").write_text("VALUE = 2\n")
        second = self.run_report(
            "again.json", f"--prior={self.reports / 'report.json'}"
        )
        self.assertEqual(second["prior_run_id"], value["run_id"])
        self.assertIs(second["same_declared_inputs"], False)
        self.assertNotEqual(
            second["fingerprint"]["input"], value["fingerprint"]["input"]
        )
        self.assertEqual(second["fingerprint"]["tests"], value["fingerprint"]["tests"])
        self.assertNotIn("same declared inputs as prior run", self.output)

    @verifies("scenario.concorde.test-prior-unreadable")
    def test_unreadable_prior_is_refused_before_tests_run(self):
        (self.reports / "list.json").write_text("[1, 2]\n")
        (self.reports / "broken.json").write_text("{not json\n")
        (self.reports / "no-run-id.json").write_text(
            '{"fingerprint": {"digest": "0"}}\n'
        )
        (self.reports / "no-digest.json").write_text(
            '{"run_id": "r", "fingerprint": {}}\n'
        )
        for prior in (
            "missing.json",
            "list.json",
            "broken.json",
            "no-run-id.json",
            "no-digest.json",
        ):
            with self.subTest(prior=prior):
                report = self.reports / f"after-{prior}"
                result = self.pytest(
                    "checks/test_sample.py",
                    f"--json={report}",
                    f"--prior={self.reports / prior}",
                    workers=0,
                )
                self.assertEqual(result.returncode, 4, result.stdout + result.stderr)
                self.assertIn(f"--prior={self.reports / prior}", result.stderr)
                self.assertNotIn("passed", result.stdout)
                self.assertFalse(report.exists())

    @verifies("scenario.concorde.test-counting")
    def test_failed_subtest_counts_one_failed_unit(self):
        (self.root / "checks/test_subtests.py").write_text(SUBTEST_TESTS)
        report = self.reports / "subtests.json"
        result = self.pytest("checks/test_subtests.py", f"--json={report}", workers=0)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        value = json.loads(report.read_text())
        statuses = {unit["nodeid"]: unit["status"] for unit in value["units"]}
        self.assertEqual(
            statuses,
            {
                "checks/test_subtests.py::SubtestTests::test_subtests": "failed",
                "checks/test_subtests.py::SubtestTests::test_plain": "passed",
            },
        )
        totals = value["totals"]
        self.assertEqual((totals["passed"], totals["failed"]), (1, 1))
        self.assertEqual(totals["tests"], totals["collected"])
        self.assertIn("subtests are not counted on their own", value["counting_note"])


if __name__ == "__main__":
    unittest.main()
