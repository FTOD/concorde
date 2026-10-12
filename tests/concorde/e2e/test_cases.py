"""SWE-bench cases: a case at its base commit, its grading and the repair of its Specs."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from concorde.spec.verification import verifies
from tests.concorde.support.paths import REPOSITORY_ROOT

SPEC = importlib.util.spec_from_file_location(
    "e2e", REPOSITORY_ROOT / "scripts/e2e/e2e.py"
)
e2e = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(e2e)
cases = e2e.cases


def git(cwd: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", "-c", "user.name=e2e", "-c", "user.email=e2e@example.com", *arguments],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    ).stdout


class CaseTests(unittest.TestCase):
    @verifies("scenario.swe-bench-cases.prepared")
    def test_a_case_is_cloned_at_its_base_commit(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source = base / "source"
            source.mkdir()
            git(source, "init", "-q")
            (source / "a.txt").write_text("base\n")
            git(source, "add", "-A")
            git(source, "commit", "-q", "-m", "base")
            commit = git(source, "rev-parse", "HEAD").strip()
            (source / "a.txt").write_text("later\n")
            git(source, "commit", "-q", "-am", "later")
            project = base / "psf__requests-1"
            e2e.clone(str(source), commit, project)
            self.assertEqual("base\n", (project / "a.txt").read_text())
            self.assertEqual("main", git(project, "branch", "--show-current").strip())

    @verifies(
        "scenario.swe-bench-cases.grade", "scenario.swe-bench-cases.grade-resolved"
    )
    def test_grading_runs_the_case_tests_on_a_throwaway_tree(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory) / "project"
            project.mkdir()
            git(project, "init", "-q", "-b", "main")
            (project / "calc.py").write_text(
                "def add(a, b):\n    return a - b\n\n\ndef sub(a, b):\n    return a - b\n"
            )
            git(project, "add", "-A")
            git(project, "commit", "-q", "-m", "base")
            base = git(project, "rev-parse", "HEAD").strip()
            test = (
                "from calc import add, sub\n\n\ndef test_add():\n    assert add(2, 1) == 3"
                "\n\n\ndef test_sub():\n    assert sub(2, 1) == 1\n"
            )
            lines = test.splitlines()
            patch = (
                "diff --git a/test_calc.py b/test_calc.py\nnew file mode 100644\n"
                "--- /dev/null\n+++ b/test_calc.py\n"
                f"@@ -0,0 +1,{len(lines)} @@\n"
                + "".join(f"+{line}\n" for line in lines)
            )
            case = {
                "instance_id": "toy__calc-1",
                "base_commit": base,
                "test_patch": patch,
                "FAIL_TO_PASS": json.dumps(["test_calc.py::test_add"]),
                "PASS_TO_PASS": json.dumps(["test_calc.py::test_sub"]),
            }
            python = Path(sys.executable)
            before = cases.grade(project, case, python)
            self.assertFalse(before["resolved"])
            self.assertEqual(
                {"test_calc.py::test_add": "FAILED"},
                before["fail_to_pass"]["not_passed"],
            )
            self.assertEqual(1, before["pass_to_pass"]["passed"])
            (project / "calc.py").write_text(
                "def add(a, b):\n    return a + b\n\n\ndef sub(a, b):\n    return a - b\n"
            )
            # The change brings its own test file, which the case's test patch replaces.
            (project / "test_calc.py").write_text("def test_mine():\n    pass\n")
            git(project, "add", "-A")
            git(project, "commit", "-q", "-m", "fix")
            self.assertTrue(cases.grade(project, case, python)["resolved"])
            # The project is left as it was: its own test file, no extra worktree.
            self.assertEqual(
                "def test_mine():\n    pass\n", (project / "test_calc.py").read_text()
            )
            self.assertEqual(1, git(project, "worktree", "list").count("\n"))

    def _graded(self, directory: str, test: str, listed: dict, **options) -> dict:
        """Grade a one-commit project whose case adds ``test`` as ``test_calc.py``."""
        project = Path(directory) / "project"
        project.mkdir()
        git(project, "init", "-q", "-b", "main")
        (project / "calc.py").write_text("def add(a, b):\n    return a + b\n")
        git(project, "add", "-A")
        git(project, "commit", "-q", "-m", "base")
        lines = test.splitlines()
        patch = (
            "diff --git a/test_calc.py b/test_calc.py\nnew file mode 100644\n"
            "--- /dev/null\n+++ b/test_calc.py\n"
            f"@@ -0,0 +1,{len(lines)} @@\n" + "".join(f"+{line}\n" for line in lines)
        )
        case = {
            "instance_id": "toy__calc-3",
            "base_commit": git(project, "rev-parse", "HEAD").strip(),
            "test_patch": patch,
            "FAIL_TO_PASS": json.dumps(listed["FAIL_TO_PASS"]),
            "PASS_TO_PASS": json.dumps(listed.get("PASS_TO_PASS", [])),
        }
        return cases.grade(project, case, Path(sys.executable), **options)

    @verifies("scenario.swe-bench-cases.grade-statuses")
    def test_statuses_are_read_under_complete_test_identities(self):
        test = (
            "import pytest\n"
            "from calc import add\n\n\n"
            '@pytest.mark.parametrize("a", ["a b", "c d"])\n'
            "def test_add(a):\n    assert add(1, 1) == 2\n\n\n"
            '@pytest.mark.skip(reason="not here")\n'
            "def test_skipped():\n    pass\n\n\n"
            "@pytest.mark.xfail\n"
            "def test_expected():\n    assert False\n\n\n"
            "def test_broken():\n    assert False\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            graded = self._graded(
                directory,
                test,
                {
                    "FAIL_TO_PASS": [
                        "test_calc.py::test_add[a b]",
                        # SWE-bench's datasets cut an identity at its first space.
                        "test_calc.py::test_add[c",
                        "test_calc.py::test_expected",
                    ],
                    "PASS_TO_PASS": ["test_calc.py::test_skipped"],
                },
            )
            self.assertTrue(graded["resolved"], graded)
            self.assertEqual(3, graded["fail_to_pass"]["passed"])
            self.assertEqual(1, graded["pass_to_pass"]["passed"])
        with tempfile.TemporaryDirectory() as directory:
            graded = self._graded(
                directory,
                test,
                {
                    "FAIL_TO_PASS": [
                        "test_calc.py::test_skipped",
                        "test_calc.py::test_broken",
                        "test_calc.py::test_missing",
                    ]
                },
            )
            self.assertFalse(graded["resolved"])
            # A skipped FAIL_TO_PASS test is no resolution, and is named as skipped.
            self.assertEqual(
                {
                    "test_calc.py::test_skipped": "SKIPPED",
                    "test_calc.py::test_broken": "FAILED",
                    "test_calc.py::test_missing": "not run",
                },
                graded["fail_to_pass"]["not_passed"],
            )

    @verifies("scenario.swe-bench-cases.grade")
    def test_pythonpath_directories_come_before_the_callers_own(self):
        from unittest.mock import patch

        test = (
            "import helper\nfrom calc import add\n\n\n"
            "def test_add():\n    assert add(1, 1) == helper.TWO\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            auxiliary = Path(directory) / "auxiliary"
            auxiliary.mkdir()
            (auxiliary / "helper.py").write_text("TWO = 2\n")
            # The project's own calc.py must win over one the caller's path also holds.
            (auxiliary / "calc.py").write_text("def add(a, b):\n    return 0\n")
            with patch.dict(cases.os.environ, {"PYTHONPATH": str(auxiliary)}):
                graded = self._graded(
                    directory,
                    test,
                    {"FAIL_TO_PASS": ["test_calc.py::test_add"]},
                    pythonpath=(".",),
                )
            self.assertTrue(graded["resolved"], graded)

    def test_a_test_run_over_the_grading_limit_is_a_detailed_error(self):
        from unittest.mock import patch

        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory) / "project"
            project.mkdir()
            git(project, "init", "-q", "-b", "main")
            (project / "calc.py").write_text("x = 1\n")
            git(project, "add", "-A")
            git(project, "commit", "-q", "-m", "base")
            patch_text = (
                "diff --git a/test_calc.py b/test_calc.py\nnew file mode 100644\n"
                "--- /dev/null\n+++ b/test_calc.py\n@@ -0,0 +1 @@\n+def test_x(): pass\n"
            )
            case = {
                "instance_id": "toy__calc-2",
                "base_commit": git(project, "rev-parse", "HEAD").strip(),
                "test_patch": patch_text,
                "FAIL_TO_PASS": json.dumps(["test_calc.py::test_x"]),
                "PASS_TO_PASS": "[]",
            }
            real_run = subprocess.run

            def slow_pytest(command, *arguments, **options):
                if "pytest" in command:
                    raise subprocess.TimeoutExpired(
                        command,
                        options["timeout"],
                        output=b"collected 1 item" + b"." * 5000,
                        stderr=b"warning",
                    )
                return real_run(command, *arguments, **options)

            log = Path(directory) / "runs/grade.log"
            log.parent.mkdir()
            log.write_text("an earlier run's output")
            with (
                patch.object(cases.subprocess, "run", slow_pytest),
                self.assertRaises(cases.E2EError) as raised,
            ):
                cases.grade(project, case, Path(sys.executable), log=log)
            error = raised.exception
            self.assertEqual("grade_timeout", error.code)
            self.assertIn("toy__calc-2", error.detail)
            self.assertIn(f"{cases.GRADE_TIMEOUT} seconds", error.detail)
            self.assertIn("pytest", error.detail)
            self.assertEqual("." * 3000, error.evidence["stdout"])
            # The whole output is kept in the log, which replaces an earlier run's.
            self.assertEqual(
                "collected 1 item" + "." * 5000 + "\nwarning", log.read_text()
            )
            self.assertEqual(str(log), error.evidence["log"])
            self.assertIn(str(log), error.detail)
            # The grading worktree is removed even so.
            self.assertEqual(1, git(project, "worktree", "list").count("\n"))

    @verifies(
        "scenario.swe-bench-cases.repair-specs",
        "scenario.swe-bench-cases.repair-accepted",
        "scenario.swe-bench-cases.repair-stopped",
    )
    def test_specs_are_repaired_from_one_review_round(self):
        from types import SimpleNamespace
        from unittest.mock import patch

        def result(name, status="ok", verdict=None):
            output = {"verdict": verdict} if verdict else {}
            return {
                "run_id": f"r-{name}",
                "status": status,
                "summary": name,
                "output": output,
            }

        def repair(outcomes):
            commands, operations = [], []

            def fake_run(command, cwd, **options):
                commands.append(command[1:3])
                return SimpleNamespace(
                    stdout=json.dumps({"record": {"worktree": "/tmp/w"}})
                )

            def operation(concorde, worktree, argv):
                operations.append(argv)
                return outcomes.pop(0)

            with patch.object(cases, "run", fake_run):
                value = cases.repair_specs(
                    Path("/tmp/p"), ["module.a", "module.b"], run_operation=operation
                )
            return value, commands, operations

        value, commands, operations = repair(
            [
                result("review", verdict="changes_required"),
                result("specify"),
                result("review2", verdict="changes_required"),
                result("task-validation"),
                result("delivery"),
            ]
        )
        self.assertIsNone(value["stopped_at"])
        self.assertEqual(
            ["spec_panel", "specify", "spec_panel", "task-validation", "delivery"],
            [argv[0] for argv in operations],
        )
        # The runs work on the task worktree's binding: none of them names the task.
        self.assertFalse(any("--task" in argv for argv in operations))
        specify = operations[1]
        self.assertEqual("r-review", specify[specify.index("--input") + 1])
        self.assertIn("never the code", specify[specify.index("--intent") + 1])
        self.assertEqual("module.a,module.b", specify[specify.index("--modules") + 1])
        self.assertEqual([["task", "open"], ["task", "merge"]], commands)
        # An accepted review needs no repair.
        value, _, operations = repair(
            [
                result("review", verdict="accepted"),
                result("task-validation"),
                result("delivery"),
            ]
        )
        self.assertEqual(
            ["spec_panel", "task-validation", "delivery"], [a[0] for a in operations]
        )
        # A step that does not end ok stops the repair, and the task is not merged.
        value, commands, _ = repair(
            [result("review", verdict="changes_required"), result("specify", "blocked")]
        )
        self.assertEqual("specify", value["stopped_at"])
        self.assertEqual("blocked", value["steps"][-1]["status"])
        self.assertEqual([["task", "open"]], commands)

    def test_a_recorded_command_runs_as_its_own_concorde_command(self):
        with tempfile.TemporaryDirectory() as directory:
            fake = Path(directory) / "concorde"
            fake.write_text(
                f"#!{sys.executable}\n"
                "import json, os, sys\n"
                "print(json.dumps({'argv': sys.argv[1:], 'cwd': os.getcwd()}))\n"
            )
            fake.chmod(0o755)
            where = Path(directory).resolve()
            for argv, expected in (
                (["task-validation"], ["task-validation"]),
                (["delivery", "--adoption"], ["delivery", "--adoption"]),
                (["scaffold", "--input", "r-x"], ["scaffold", "--input", "r-x"]),
                (["spec_panel", "--modules", "module.a"], ["run", "spec_panel"]),
            ):
                with self.subTest(command=argv[0]):
                    value = cases.concorde_run(str(fake), where, argv)
                    self.assertEqual(expected, value["argv"][: len(expected)])
                    self.assertEqual(str(where), value["cwd"])


if __name__ == "__main__":
    unittest.main()
