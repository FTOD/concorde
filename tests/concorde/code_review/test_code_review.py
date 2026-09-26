"""The ``code_review`` Operation end to end, with the fake ``claude``."""

from __future__ import annotations

import json
import os
import subprocess
import unittest
from pathlib import Path

from concorde.code_review.operation import REVIEW_SCHEMA
from concorde.harness.runs import read_record
from concorde.spec.repository import SpecRepository
from concorde.spec.verification import verifies
from tests.concorde.support.operation_project import OperationProject
from tests.concorde.support.paths import REPOSITORY_ROOT

FIXED = "def add(a, b):\n    return a + b\n"


def finding(number, basis="scenario.a.answer", **values):
    return {
        "id": f"F{number}",
        "severity": "blocking",
        "kind": "violation",
        "module": "module.a",
        "basis": basis,
        "locations": ["src/a/calc.py:2"],
        "description": "add subtracts",
        "suggestion": "add instead",
        **values,
    }


def status_lines(root: Path) -> str:
    return subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout


class CodeReviewTests(unittest.TestCase):
    def setUp(self):
        self.project = OperationProject(self)
        self.root = self.project.root
        self.task = self.project.open_task("t1")
        self.worktree = self.project.worktree("t1")
        (self.worktree / "src/a/calc.py").write_text(FIXED)

    def review(self, findings=(), result=None, *extra):
        plan = [
            {
                "result": {
                    "summary": "reviewed",
                    "output": {"findings": list(findings)},
                    **(result or {}),
                }
            }
        ]
        return self.project.run(
            "code_review",
            "--task",
            "t1",
            "--focus",
            OperationProject.plan(plan),
            *extra,
        )

    def worker(self, envelope) -> tuple[dict, str, int]:
        record = read_record(self.root, envelope["worker_runs"][-1])
        work = Path(record["run_directory"]) / "work"
        rounds = sorted(work.glob("fake-round-*.json"))
        return record, json.loads(rounds[0].read_text())["prompt"], len(rounds)

    @verifies("scenario.code-review.clean")
    def test_a_change_that_keeps_its_promises(self):
        status, envelope = self.review()
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        report = envelope["output"]
        self.assertEqual("clean", report["verdict"])
        self.assertEqual(self.task["base_commit"], report["base"])
        self.assertEqual(["src/a/calc.py"], report["reviewed_paths"])
        self.assertEqual([], report["named_only_paths"])
        self.assertEqual(["passed"], [item["outcome"] for item in report["checks"]])
        kinds = {item["kind"] for item in envelope["host_evidence"]}
        self.assertTrue({"base", "diff", "check", "context-identity", "audit"} <= kinds)
        record, prompt, _ = self.worker(envelope)
        self.assertIn("+    return a + b", prompt)
        self.assertIn("check.a (module.a): passed", prompt)
        self.assertEqual("Read,Glob,Grep", record["tools"])
        settings = json.loads(
            (Path(record["run_directory"]) / "control/settings.json").read_text()
        )
        checks = Path(os.path.realpath(self.root / report["checks"][0]["log"])).parent
        self.assertIn(checks.as_posix(), settings["sandbox"]["filesystem"]["allowRead"])

    @verifies("scenario.code-review.all-blocking")
    def test_every_blocking_finding_in_one_report(self):
        before = status_lines(self.worktree)
        findings = [
            finding(1),
            finding(2, basis="specs/a/module.md#design", kind="defect"),
            finding(3, kind="missing-test", locations=["tests/"]),
        ]
        status, envelope = self.review(findings)
        self.assertEqual("ok", envelope["status"], envelope)
        self.assertEqual("changes_required", envelope["output"]["verdict"])
        self.assertEqual(findings, envelope["output"]["findings"])
        record, _, rounds = self.worker(envelope)
        self.assertEqual((1, 1), (len(record["rounds"]), rounds))
        self.assertEqual(1, len(envelope["worker_runs"]))
        self.assertEqual(before, status_lines(self.worktree))

    def test_advisory_findings_keep_the_verdict_clean(self):
        _, envelope = self.review([finding(1, severity="advisory", basis=None)])
        self.assertEqual("ok", envelope["status"], envelope)
        self.assertEqual("clean", envelope["output"]["verdict"])

    @verifies("scenario.code-review.spec-gap")
    def test_behaviour_the_spec_does_not_settle(self):
        gap = finding(1, kind="spec-gap", basis="specs/a/module.md#design")
        _, envelope = self.review([gap])
        self.assertEqual("ok", envelope["status"], envelope)
        self.assertEqual("spec-gap", envelope["output"]["findings"][0]["kind"])

    @verifies("scenario.code-review.foreign-path")
    def test_a_changed_file_outside_the_grant_is_named_only(self):
        # Another Module's code is readable to a code review, so its change is shown in full;
        # only a file no Module binds stays a name.
        (self.worktree / "src/bmod/secret.py").write_text("SECRET = 2\n")
        (self.worktree / "src/a/extra.py").write_text("EXTRA = 1\n")
        (self.worktree / "tools").mkdir()
        (self.worktree / "tools/helper.py").write_text("HELPER = 3\n")
        out = finding(
            1,
            kind="out-of-scope",
            locations=["tools/helper.py"],
            severity="advisory",
        )
        _, envelope = self.review([out])
        self.assertEqual("ok", envelope["status"], envelope)
        report = envelope["output"]
        self.assertEqual(
            ["src/a/calc.py", "src/a/extra.py", "src/bmod/secret.py"],
            report["reviewed_paths"],
        )
        self.assertEqual(["tools/helper.py"], report["named_only_paths"])
        _, prompt, _ = self.worker(envelope)
        self.assertIn(f"{self.worktree}/tools/helper.py", prompt)
        self.assertNotIn("HELPER = 3", prompt)
        self.assertIn("+SECRET = 2", prompt)
        self.assertIn("+EXTRA = 1", prompt)

    @verifies("scenario.code-review.failing-check")
    def test_a_failing_check_is_reviewed_not_fatal(self):
        (self.worktree / "src/a/flag").write_text("broken")
        _, envelope = self.review()
        self.assertEqual("ok", envelope["status"], envelope)
        [check] = envelope["output"]["checks"]
        self.assertEqual(("failed", 1), (check["outcome"], check["exit_code"]))
        self.assertTrue((self.root / check["log"]).is_file())
        _, prompt, _ = self.worker(envelope)
        self.assertIn("check.a (module.a): failed", prompt)
        self.assertIn(check["log"].split("/")[-1], prompt)

    @verifies("scenario.code-review.unknown-basis")
    def test_a_finding_citing_an_unknown_promise_fails_the_run(self):
        status, envelope = self.review([finding(1, basis="req.a.nothing")])
        self.assertEqual((1, "failed"), (status, envelope["status"]))
        [problem] = [
            item
            for item in envelope["host_evidence"]
            if item["kind"] == "unresolved-basis"
        ]
        self.assertEqual(("req.a.nothing", "F1"), (problem["ref"], problem["detail"]))
        self.assertEqual("unresolved_basis", envelope["error"]["code"])
        self.assertIn("F1 cites req.a.nothing", envelope["error"]["detail"])

    def test_a_blocking_finding_without_basis_fails_the_run(self):
        _, envelope = self.review([finding(1, basis=None)])
        self.assertEqual("failed", envelope["status"])

    def test_a_document_outside_the_context_does_not_resolve(self):
        _, envelope = self.review([finding(1, basis="specs/elsewhere.md#x")])
        self.assertEqual("failed", envelope["status"])

    def test_a_changing_reviewer_fails_the_run(self):
        plan = [
            {
                "writes": {f"{self.worktree}/src/a/calc.py": "BROKEN = 1\n"},
                "result": {"output": {"findings": []}},
            }
        ]
        _, envelope = self.project.run(
            "code_review", "--task", "t1", "--focus", OperationProject.plan(plan)
        )
        self.assertEqual("failed", envelope["status"])
        audit = [item for item in envelope["host_evidence"] if item["kind"] == "audit"]
        self.assertIn("src/a/calc.py", audit[0]["detail"])

    def test_an_unknown_base_fails_before_the_reviewer(self):
        _, envelope = self.review((), None, "--base", "no-such-ref")
        self.assertEqual("failed", envelope["status"])
        self.assertEqual([], envelope["worker_runs"])
        self.assertEqual("base", envelope["host_evidence"][0]["kind"])

    def test_an_explicit_base_is_resolved(self):
        _, envelope = self.review((), None, "--base", "HEAD")
        self.assertEqual("ok", envelope["status"], envelope)
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=self.worktree,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        self.assertEqual(head, envelope["output"]["base"])


class ContractTests(unittest.TestCase):
    def test_the_output_schema_is_the_contract(self):
        [contract] = SpecRepository(REPOSITORY_ROOT).contracts("module.code-review")
        self.assertEqual(contract["schema"], REVIEW_SCHEMA)


if __name__ == "__main__":
    unittest.main()
