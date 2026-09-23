"""The check service: selecting Modules, running their checks read-only, logs and staleness."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from concorde.harness.checks import affected_modules, check_revision, run_checks
from concorde.spec.repository import SpecRepository
from concorde.spec.repository_base import SpecError
from concorde.spec.verification import verifies
from tests.concorde.harness.workers.test_workers import WorkerProject
from tests.concorde.support.paths import REPOSITORY_ROOT


class CheckServiceTests(unittest.TestCase):
    def setUp(self):
        self.project = WorkerProject(self)
        self.root = self.project.root
        self.logs = Path(tempfile.mkdtemp())

    def repository(self):
        return SpecRepository(self.root, REPOSITORY_ROOT)

    @verifies("scenario.checks.service-run")
    def test_the_checks_of_changed_modules_run_and_log(self):
        self.assertEqual(
            ["module.a"],
            affected_modules(self.repository(), ["src/a/calc.py"]),
        )
        self.assertEqual(
            ["module.a"],
            affected_modules(self.repository(), ["specs/a/module.md"]),
        )
        [result] = run_checks(
            self.root, changed=["src/a/calc.py"], log_directory=self.logs
        )
        self.assertEqual(
            ("check.a", "module.a", "passed", 0),
            (
                result["check_id"],
                result["module"],
                result["status"],
                result["exit_code"],
            ),
        )
        self.assertEqual(self.logs / "check.a.log", Path(result["log"]))
        self.assertEqual(
            check_revision(self.repository(), "module.a"), result["source_digest"]
        )
        (self.root / "src/a/flag").write_text("broken")
        [failed] = run_checks(self.root, modules=["module.a"], log_directory=self.logs)
        self.assertEqual(("failed", 1), (failed["status"], failed["exit_code"]))
        self.assertEqual(
            [], run_checks(self.root, modules=["module.b"], log_directory=self.logs)
        )

    @verifies("scenario.checks.service-read-only")
    def test_a_check_cannot_change_the_worktree(self):
        check = self.root / "checks/a_check.py"
        check.write_text("open('src/a/calc.py', 'w').write('changed')\n")
        [result] = run_checks(self.root, modules=["module.a"], log_directory=self.logs)
        self.assertEqual("failed", result["status"])
        self.assertIn("def add", (self.root / "src/a/calc.py").read_text())
        self.assertIn("Read-only file system", (self.logs / "check.a.log").read_text())

    @verifies("scenario.checks.service-stale")
    def test_input_changed_during_the_run_is_stale(self):
        from concorde.harness import checks

        real = checks.execute_check

        def changing(worktree, argv, **options):
            outcome = real(worktree, argv, **options)
            (self.root / "src/a/calc.py").write_text("changed = True\n")
            return outcome

        with patch.object(checks, "execute_check", changing):
            with self.assertRaises(SpecError) as raised:
                run_checks(self.root, modules=["module.a"], log_directory=self.logs)
        self.assertEqual("stale_evidence", raised.exception.code)

    @verifies("scenario.checks.service-refused")
    def test_a_refused_check_has_no_result(self):
        from concorde.harness import checks
        from concorde.harness.check_executor import CheckSandboxError

        def refused(*_arguments, **_options):
            raise CheckSandboxError("bubblewrap is unavailable", stderr=b"why")

        with patch.object(checks, "execute_check", refused):
            with self.assertRaises(SpecError) as raised:
                run_checks(self.root, modules=["module.a"], log_directory=self.logs)
        self.assertEqual("check_sandbox_unavailable", raised.exception.code)
        self.assertIn("why", (self.logs / "check.a.log").read_text())

    @verifies("scenario.checks.service-input-missing")
    def test_a_missing_input_stops_before_any_command(self):
        config = json.loads((self.root / ".concorde/config.json").read_text())
        config["checks"][0]["inputs"] = ["checks/missing.py"]
        (self.root / ".concorde/config.json").write_text(json.dumps(config))
        with self.assertRaises(SpecError) as raised:
            run_checks(self.root, modules=["module.a"], log_directory=self.logs)
        self.assertIn("checks/missing.py", str(raised.exception))
        self.assertFalse((self.logs / "check.a.log").exists())


if __name__ == "__main__":
    unittest.main()
