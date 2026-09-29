"""The ``implement`` and ``test`` Operations end to end, with the fake ``claude``."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

from concorde.harness import claude_backend
from concorde.harness.runs import read_record
from concorde.harness.settings import denied
from concorde.implementation.operation import CODE_CHANGE_SCHEMA, TEST_REPORT_SCHEMA
from concorde.execution.context import interpreter_roots
from concorde.spec.repository import SpecRepository
from concorde.spec.verification import verifies
from tests.concorde.support.operation_project import (
    OperationProject,
    commit,
    link_at,
    worker_error,
)
from tests.concorde.support.paths import REPOSITORY_ROOT
from tests.concorde.support.spec_project import set_realization

FIXED = "def add(a, b):\n    return a + b\n"


@contextmanager
def generated_settings():
    """The settings Workers generates for each Claude Code worker, which live only in the
    worker's runtime directory, removed when the worker run ends."""
    seen: list[dict] = []
    original = claude_backend.worker_settings

    def spy(*args, **kwargs):
        value = original(*args, **kwargs)
        seen.append(value)
        return value

    with patch.object(claude_backend, "worker_settings", side_effect=spy):
        yield seen


def brief_of(record: dict) -> str:
    """The worker's first prompt: the brief its run directory keeps."""
    return (Path(record["run_directory"]) / "brief.md").read_text()


def run_node(envelope: dict) -> Path:
    """The run's own trace node folder, which the first host evidence names."""
    [node] = [
        item["detail"] for item in envelope["host_evidence"] if item["kind"] == "trace"
    ]
    return Path(node)


def status_lines(root: Path) -> str:
    return subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout


class ImplementTests(unittest.TestCase):
    def setUp(self):
        self.project = OperationProject(self)
        self.root = self.project.root
        (self.root / "src/a/old.py").write_text("OLD = 1\n")
        commit(self.root, "old file")
        self.project.open_task("t1")
        self.worktree = self.project.worktree("t1")

    def implement(self, rounds, *extra):
        plan = [
            {**item, "result": {"output": {"addresses": []}, **item.get("result", {})}}
            for item in rounds
        ]
        return self.project.run(
            "implement", "--task", "t1", "--goal", OperationProject.plan(plan), *extra
        )

    def record(self, envelope) -> dict:
        return read_record(self.root / ".concorde", envelope["worker_runs"][-1])

    def kinds(self, envelope) -> list[str]:
        return [item["kind"] for item in envelope["host_evidence"]]

    @verifies("scenario.implementation.project-python")
    def test_the_worker_is_told_and_may_run_the_projects_interpreter(self):
        with generated_settings() as generated:
            status, envelope = self.implement([{"writes": {}}])
        self.assertEqual(0, status, envelope)
        record = self.record(envelope)
        prompt = brief_of(record)
        self.assertIn(f"The project's own interpreter is {sys.executable}", prompt)
        # The run's own goal is the task; the workspace's goal is context beside it.
        self.assertIn("## Goal\n\nDo the task.", prompt)
        self.assertIn("## The workspace's goal\n", prompt)
        self.assertIn("Fix A.", prompt.split("## The workspace's goal")[1])
        [settings] = generated
        environment_root = Path(sys.executable).parent.parent.as_posix()
        self.assertIn(
            os.path.realpath(environment_root),
            settings["sandbox"]["filesystem"]["allowRead"],
        )

    @verifies("scenario.implementation.checks-of-users")
    def test_a_change_runs_the_checks_of_the_modules_that_use_it(self):
        # Module A uses Module B, and only A has a check: changing B runs A's check.
        self.project.open_task("t2", modules=("module.b",))
        worktree = self.project.worktree("t2")
        plan = [
            {
                "writes": {f"{worktree}/src/bmod/secret.py": "SECRET = 2\n"},
                "result": {"summary": "changed b", "output": {"addresses": []}},
            }
        ]
        status, envelope = self.project.run(
            "implement", "--task", "t2", "--goal", OperationProject.plan(plan)
        )
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        self.assertEqual(
            [("check.a", "module.a")],
            [(item["check"], item["module"]) for item in envelope["output"]["checks"]],
        )

    @verifies("scenario.implementation.implement-pass")
    def test_a_change_passes_its_checks(self):
        status, envelope = self.implement(
            [
                {
                    "writes": {f"{self.worktree}/src/a/calc.py": FIXED},
                    "result": {
                        "summary": "fixed add",
                        "output": {"addresses": ["scenario.a.answer"]},
                    },
                }
            ]
        )
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        output = envelope["output"]
        self.assertEqual(["src/a/calc.py"], output["changed_files"])
        self.assertEqual([], output["created_files"])
        self.assertEqual(1, output["rounds"])
        self.assertEqual(["scenario.a.answer"], output["addresses"])
        self.assertEqual("fixed add", output["summary"])
        [check] = output["checks"]
        self.assertEqual(
            ("check.a", "module.a", "passed", 0),
            (check["check"], check["module"], check["outcome"], check["exit_code"]),
        )
        # The checks ran in the worker's round: the log is a check node of that round's node,
        # below the worker run's node, below the run's own node.
        worker_run = Path(self.record(envelope)["run_directory"])
        self.assertEqual(run_node(envelope) / "workers", worker_run.parent)
        self.assertEqual(
            (worker_run / "rounds/1/checks/check.a/output.log").as_posix(), check["log"]
        )
        self.assertTrue(Path(check["log"]).is_file())
        self.assertTrue({"audit", "check", "grant"} <= set(self.kinds(envelope)))
        self.assertEqual(FIXED, (self.worktree / "src/a/calc.py").read_text())
        self.assertIn("M src/a/calc.py", status_lines(self.worktree))

    @verifies("scenario.implementation.resume")
    def test_a_failed_check_is_repaired_in_a_resume_round(self):
        flag = f"{self.worktree}/src/a/flag"
        status, envelope = self.implement(
            [{"writes": {flag: "broken"}}, {"writes": {flag: "ok"}}]
        )
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        self.assertEqual(2, envelope["output"]["rounds"])
        self.assertEqual(["src/a/flag"], envelope["output"]["created_files"])
        record = self.record(envelope)
        self.assertEqual(
            ["initial", "check_failures"], [item["prompt"] for item in record["rounds"]]
        )
        self.assertEqual("fake-session-2", record["rounds"][-1]["session"])
        self.assertEqual(1, len(envelope["worker_runs"]))

    @verifies("scenario.implementation.rounds-exhausted")
    def test_checks_still_failing_after_the_last_round(self):
        flag = f"{self.worktree}/src/a/flag"
        status, envelope = self.implement(
            [{"writes": {flag: "broken"}}], "--rounds", "1"
        )
        self.assertEqual((1, "failed"), (status, envelope["status"]))
        self.assertEqual(2, envelope["output"]["rounds"])
        self.assertEqual("failed", envelope["output"]["checks"][0]["outcome"])
        failing = [
            item
            for item in envelope["host_evidence"]
            if item["kind"] == "check" and "exit 1" in item["detail"]
        ]
        self.assertTrue(failing)
        self.assertEqual("broken", (self.worktree / "src/a/flag").read_text())
        self.assertIn("?? src/a/flag", status_lines(self.worktree))

    def test_a_negative_round_limit_is_refused(self):
        status, envelope = self.implement([{}], "--rounds", "-1")
        self.assertEqual("failed", envelope["status"])
        self.assertEqual([], envelope["worker_runs"])

    @verifies("scenario.implementation.spec-gap")
    def test_a_spec_gap_stops_the_run(self):
        status, envelope = self.implement(
            [
                {
                    "result": {
                        "status": "blocked",
                        "error": worker_error(
                            "the Spec of module.a does not say how add rounds"
                        ),
                    }
                }
            ]
        )
        self.assertEqual((1, "blocked"), (status, envelope["status"]))
        worker = link_at(envelope["error"], "worker")
        self.assertIn("does not say", worker["detail"])
        self.assertEqual("decision", envelope["error"]["unhandled"]["reason"])
        record = self.record(envelope)
        self.assertEqual(1, len(record["rounds"]))
        self.assertEqual("", status_lines(self.worktree))
        grant = json.loads((Path(record["run_directory"]) / "grant.json").read_text())
        writable = [item["path"] for item in grant["entries"] if item["level"] == "rw"]
        self.assertEqual(["src/a/", "src/new.py"], writable)
        self.assertFalse(any(path.startswith("specs/") for path in writable))

    @verifies("scenario.implementation.out-of-grant")
    def test_a_write_outside_the_grant_fails_the_run(self):
        status, envelope = self.implement(
            [{"writes": {f"{self.worktree}/src/bmod/secret.py": "SECRET = 2\n"}}]
        )
        self.assertEqual((1, "failed"), (status, envelope["status"]))
        audit = [item for item in envelope["host_evidence"] if item["kind"] == "audit"]
        self.assertIn("src/bmod/secret.py", audit[0]["detail"])
        self.assertNotIn("check", self.kinds(envelope))
        self.assertEqual(1, len(self.record(envelope)["rounds"]))

    @verifies("scenario.implementation.prepared-file")
    def test_a_file_the_task_level_created_and_bound_is_filled(self):
        # The task level creates the skeleton and binds it before the run.
        (self.worktree / "src/prepared.py").write_text("")
        set_realization(
            self.worktree,
            "realization.a.new",
            entries=["src/new.py", "src/prepared.py"],
        )

        def specs():
            return {
                path.relative_to(self.worktree).as_posix(): path.read_bytes()
                for folder in ("specs", ".concorde")
                for path in sorted((self.worktree / folder).rglob("*"))
                if path.is_file() and path.suffix in {".md", ".json"}
            }

        before = specs()
        status, envelope = self.implement(
            [{"writes": {f"{self.worktree}/src/prepared.py": "PREPARED = 1\n"}}]
        )
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        record = self.record(envelope)
        grant = json.loads((Path(record["run_directory"]) / "grant.json").read_text())
        writable = [item["path"] for item in grant["entries"] if item["level"] == "rw"]
        self.assertEqual(["src/a/", "src/new.py", "src/prepared.py"], writable)
        output = envelope["output"]
        self.assertIn("src/prepared.py", output["changed_files"])
        self.assertNotIn("src/prepared.py", output["created_files"])
        self.assertEqual(
            "PREPARED = 1\n", (self.worktree / "src/prepared.py").read_text()
        )
        self.assertEqual(before, specs())

    @verifies("scenario.implementation.deletion")
    def test_a_proposed_deletion_is_performed_by_the_host(self):
        status, envelope = self.implement(
            [
                {
                    "result": {
                        "proposed_deletions": [
                            f"{self.worktree}/src/a/old.py",
                            f"{self.worktree}/src/bmod/secret.py",
                        ]
                    }
                }
            ]
        )
        self.assertEqual("ok", envelope["status"], envelope)
        self.assertFalse((self.worktree / "src/a/old.py").exists())
        self.assertTrue((self.worktree / "src/bmod/secret.py").exists())
        output = envelope["output"]
        self.assertEqual(["src/a/old.py"], output["deleted_files"])
        self.assertEqual(
            [f"{self.worktree}/src/bmod/secret.py"], output["refused_deletions"]
        )
        self.assertIn("deletion-refused", self.kinds(envelope))

    def test_admitted_inputs_reach_the_worker(self):
        _, first = self.implement([{}])
        self.assertEqual("ok", first["status"], first)
        _, second = self.project.run(
            "implement",
            "--task",
            "t1",
            "--goal",
            OperationProject.plan([{"result": {"output": {"addresses": []}}}]),
            "--input",
            first["run_id"],
        )
        prompt = brief_of(self.record(second))
        self.assertIn(first["run_id"], prompt)
        self.assertIn("## Task material", prompt)


class InterpreterRootsTests(unittest.TestCase):
    @verifies("scenario.implementation.project-python")
    def test_every_link_on_the_way_to_the_interpreter_is_readable(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(os.path.realpath(temporary)) / "home"
            installations = home / ".local/share/uv/python"
            release = installations / "cpython-3.9.25"
            (release / "bin").mkdir(parents=True)
            (release / "bin/python3.9").write_text("")
            (installations / "cpython-3.9").symlink_to(release)
            environment = home / "envs/project"
            (environment / "bin").mkdir(parents=True)
            (environment / "bin/python").symlink_to(
                installations / "cpython-3.9/bin/python3.9"
            )
            (home / "link").symlink_to(environment)

            roots = interpreter_roots((home / "link/bin/python").as_posix(), home)

        self.assertIn(installations, roots)
        self.assertIn(release, roots)
        self.assertIn(environment / "bin", roots)
        self.assertNotIn(home, roots)


class NoCheckTests(unittest.TestCase):
    def test_a_module_without_checks_ends_ok_without_check_evidence(self):
        project = OperationProject(self, check=False)
        project.open_task("t1")
        status, envelope = project.run(
            "implement",
            "--task",
            "t1",
            "--goal",
            OperationProject.plan([{"result": {"output": {"addresses": []}}}]),
        )
        self.assertEqual("ok", envelope["status"], envelope)
        self.assertEqual([], envelope["output"]["checks"])
        [note] = [i for i in envelope["host_evidence"] if i["kind"] == "checks"]
        self.assertIn("no configured check", note["detail"])


class TestOperationTests(unittest.TestCase):
    def setUp(self):
        self.project = OperationProject(self)
        self.root = self.project.root
        self.project.open_task("t1")
        self.worktree = self.project.worktree("t1")

    def run_test(self, rounds):
        plan = [
            {
                **item,
                "result": {
                    "output": {"failures": [], "notes": []},
                    **item.get("result", {}),
                },
            }
            for item in rounds
        ]
        return self.project.run(
            "test", "--task", "t1", "--focus", OperationProject.plan(plan)
        )

    def worker_round(self, envelope) -> tuple[dict, str]:
        """The worker's run record and its first prompt."""
        record = read_record(self.root / ".concorde", envelope["worker_runs"][-1])
        return record, brief_of(record)

    @verifies("scenario.implementation.test-pass")
    def test_passing_checks_are_reported(self):
        with generated_settings() as generated:
            status, envelope = self.run_test([{"result": {"summary": "all green"}}])
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        output = envelope["output"]
        self.assertTrue(output["passed"])
        self.assertEqual(["passed"], [item["outcome"] for item in output["checks"]])
        # The host's checks are check nodes below the run's own node.
        node = run_node(envelope)
        self.assertEqual(envelope["run_id"], node.name)
        self.assertEqual(
            (node / "checks/check.a/output.log").as_posix(), output["checks"][0]["log"]
        )
        self.assertTrue(Path(output["checks"][0]["log"]).is_file())
        record, round_one = self.worker_round(envelope)
        self.assertIn("check.a (module.a): passed", round_one)
        self.assertIn("## Focus\n\nDo the task.", round_one)
        self.assertIn("Fix A.", round_one.split("## The workspace's goal")[1])
        self.assertEqual(1, len(record["rounds"]))
        self.assertEqual("", status_lines(self.worktree))
        # The worker may read the log of a check that passed, to see what actually ran.
        # Every check node lies in the run's checks folder, which the worker may read.
        [settings] = generated
        checks = Path(os.path.realpath(output["checks"][0]["log"])).parent.parent
        self.assertFalse(denied(settings["permissions"]["deny"], checks))
        self.assertIn(checks.as_posix(), settings["sandbox"]["filesystem"]["allowRead"])

    @verifies("scenario.implementation.test-fail")
    def test_a_failing_check_is_interpreted(self):
        (self.worktree / "src/a/flag").write_text("broken")
        failure = {
            "check": "check.a",
            "concerns": ["scenario.a.answer"],
            "cause": "the flag file says broken",
            "fault": "code",
            "locations": ["src/a/flag:1"],
        }
        status, envelope = self.run_test(
            [{"result": {"output": {"failures": [failure], "notes": []}}}]
        )
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        output = envelope["output"]
        self.assertFalse(output["passed"])
        self.assertEqual("failed", output["checks"][0]["outcome"])
        self.assertEqual(1, output["checks"][0]["exit_code"])
        self.assertEqual([failure], output["failures"])
        record, round_one = self.worker_round(envelope)
        self.assertEqual("Read,Glob,Grep", record["tools"])
        self.assertIn("### Log of check.a", round_one)
        self.assertIn("check.a (module.a): failed", round_one)

    @verifies("scenario.implementation.test-change")
    def test_a_change_during_a_test_run_fails_it(self):
        status, envelope = self.run_test(
            [{"writes": {f"{self.worktree}/src/a/calc.py": FIXED}}]
        )
        self.assertEqual((1, "failed"), (status, envelope["status"]))
        audit = [item for item in envelope["host_evidence"] if item["kind"] == "audit"]
        self.assertIn("src/a/calc.py", audit[0]["detail"])

    def test_an_unknown_module_fails_before_any_check(self):
        status, envelope = self.project.run(
            "test", "--task", "t1", "--modules", "module.nothing"
        )
        self.assertEqual("failed", envelope["status"])
        self.assertEqual([], envelope["worker_runs"])
        self.assertNotIn("check", [item["kind"] for item in envelope["host_evidence"]])


class ContractTests(unittest.TestCase):
    def test_the_output_schemas_are_the_contracts(self):
        contracts = {
            item["id"]: item["schema"]
            for item in SpecRepository(REPOSITORY_ROOT).contracts(
                "module.implementation"
            )
        }
        self.assertEqual(
            contracts["contract.implementation.code-change"], CODE_CHANGE_SCHEMA
        )
        self.assertEqual(
            contracts["contract.implementation.test-report"], TEST_REPORT_SCHEMA
        )


if __name__ == "__main__":
    unittest.main()
