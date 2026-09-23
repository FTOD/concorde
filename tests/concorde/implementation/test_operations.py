"""The ``implement`` and ``test`` Operations end to end, with the fake ``claude``."""

from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path

from concorde.harness.runs import read_record
from concorde.implementation.operation import CODE_CHANGE_SCHEMA, TEST_REPORT_SCHEMA
from concorde.spec.repository import SpecRepository
from concorde.spec.verification import verifies
from tests.concorde.support.operation_project import OperationProject, commit
from tests.concorde.support.paths import REPOSITORY_ROOT

FIXED = "def add(a, b):\n    return a + b\n"


def status_lines(root: Path) -> str:
    return subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def pending_of(worktree: Path) -> list[str]:
    value = json.loads((worktree / "specs/a/module.md.json").read_text())
    return [
        entry
        for record in value["defines"]
        if record.get("type") == "realization"
        for entry in record.get("pending", [])
    ]


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
        return read_record(self.root, envelope["worker_runs"][-1])

    def kinds(self, envelope) -> list[str]:
        return [item["kind"] for item in envelope["host_evidence"]]

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
        self.assertTrue(check["log"].startswith(".concorde/runs/"))
        self.assertTrue((self.root / check["log"]).is_file())
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
                        "problem": "the Spec of module.a does not say how add rounds",
                        "blocking": True,
                    }
                }
            ]
        )
        self.assertEqual((1, "blocked"), (status, envelope["status"]))
        self.assertEqual("worker", envelope["escalation"]["source"])
        self.assertIn("does not say", envelope["escalation"]["problem"])
        record = self.record(envelope)
        self.assertEqual(1, len(record["rounds"]))
        self.assertEqual("", status_lines(self.worktree))
        grant = json.loads(
            (Path(record["run_directory"]) / "control/grant.json").read_text()
        )
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

    @verifies("scenario.implementation.pending-file")
    def test_a_declared_file_is_created_and_its_marker_cleared(self):
        self.assertEqual(["src/new.py"], pending_of(self.worktree))
        status, envelope = self.implement(
            [{"writes": {f"{self.worktree}/src/new.py": "VALUE = 1\n"}}]
        )
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        self.assertEqual(["src/new.py"], self.record(envelope)["pending_created"])
        self.assertEqual(["src/new.py"], envelope["output"]["created_files"])
        self.assertEqual(["src/new.py"], envelope["output"]["pending_cleared"])
        self.assertEqual([], pending_of(self.worktree))
        self.assertIn("pending-cleared", self.kinds(envelope))
        self.assertEqual(
            ["src/new.py"], pending_of(self.root)
        )  # the primary is untouched

    @verifies("scenario.implementation.unused-pending")
    def test_an_unused_declaration_stays_pending(self):
        status, envelope = self.implement(
            [{"writes": {f"{self.worktree}/src/a/calc.py": FIXED}}]
        )
        self.assertEqual("ok", envelope["status"], envelope)
        self.assertFalse((self.worktree / "src/new.py").exists())
        self.assertEqual(["src/new.py"], pending_of(self.worktree))
        self.assertEqual([], envelope["output"]["pending_cleared"])

    def test_an_unused_declaration_is_removed_after_a_failed_run(self):
        status, envelope = self.implement(
            [{"writes": {f"{self.worktree}/src/bmod/secret.py": "SECRET = 2\n"}}]
        )
        self.assertEqual("failed", envelope["status"])
        self.assertFalse((self.worktree / "src/new.py").exists())
        self.assertEqual(["src/new.py"], pending_of(self.worktree))

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
        work = Path(self.record(second)["run_directory"]) / "work"
        prompt = json.loads((work / "fake-round-1.json").read_text())["prompt"]
        self.assertIn(first["run_id"], prompt)
        self.assertIn("## Task material", prompt)


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

    def worker_round(self, envelope) -> dict:
        record = read_record(self.root, envelope["worker_runs"][-1])
        work = Path(record["run_directory"]) / "work"
        return record, json.loads((work / "fake-round-1.json").read_text())

    @verifies("scenario.implementation.test-pass")
    def test_passing_checks_are_reported(self):
        status, envelope = self.run_test([{"result": {"summary": "all green"}}])
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        output = envelope["output"]
        self.assertTrue(output["passed"])
        self.assertEqual(["passed"], [item["outcome"] for item in output["checks"]])
        self.assertTrue(output["checks"][0]["log"].startswith(".concorde/runs/r-"))
        self.assertIn(envelope["run_id"], output["checks"][0]["log"])
        record, round_one = self.worker_round(envelope)
        self.assertIn("check.a (module.a): passed", round_one["prompt"])
        self.assertEqual(1, len(record["rounds"]))
        self.assertEqual("", status_lines(self.worktree))

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
        self.assertIn("### Log of check.a", round_one["prompt"])
        self.assertIn("check.a (module.a): failed", round_one["prompt"])

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
