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

    @verifies("scenario.swe-bench-cases.grade")
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

    @verifies("scenario.swe-bench-cases.repair-specs")
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
                return SimpleNamespace(stdout=json.dumps({"worktree": "/tmp/w"}))

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
                result("validate"),
                result("delivery"),
            ]
        )
        self.assertIsNone(value["stopped_at"])
        self.assertEqual(
            ["spec_review", "specify", "spec_review", "validate", "delivery"],
            [argv[0] for argv in operations],
        )
        specify = operations[1]
        self.assertEqual("r-review", specify[specify.index("--input") + 1])
        self.assertIn("never the code", specify[specify.index("--intent") + 1])
        self.assertEqual("module.a,module.b", specify[specify.index("--modules") + 1])
        self.assertEqual([["task", "open"], ["task", "merge"]], commands)
        # An accepted review needs no repair.
        value, _, operations = repair(
            [
                result("review", verdict="accepted"),
                result("validate"),
                result("delivery"),
            ]
        )
        self.assertEqual(
            ["spec_review", "validate", "delivery"], [a[0] for a in operations]
        )
        # A step that does not end ok stops the repair, and the task is not merged.
        value, commands, _ = repair(
            [result("review", verdict="changes_required"), result("specify", "blocked")]
        )
        self.assertEqual("specify", value["stopped_at"])
        self.assertEqual("blocked", value["steps"][-1]["status"])
        self.assertEqual([["task", "open"]], commands)


if __name__ == "__main__":
    unittest.main()
