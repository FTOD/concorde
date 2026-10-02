"""The ``code_review`` Operation end to end, with a fake ``claude`` per reviewed Module."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from concorde.method.code_review.operation import REVIEW_SCHEMA
from concorde.worker_harness import claude_backend
from concorde.worker_harness.runs import read_record
from concorde.issues.store import list_issues, read_issue, report_issue
from concorde.spec.repository import SpecRepository
from concorde.spec.schema import validate
from concorde.spec.verification import verifies
from concorde.method.review_issues import NOT_RECORDED
from tests.concorde.support.operation_project import OperationProject
from tests.concorde.support.paths import REPOSITORY_ROOT

FIXED = "def add(a, b):\n    return a + b\n"
FAKE_REVIEWER = Path(__file__).with_name("fake_reviewer.py")


# A ``concorde`` whose command line knows no ``issues``: the issues part is not installed.
NO_ISSUES = [
    sys.executable,
    "-c",
    "import sys; sys.stderr.write(\"concorde: error: argument command: invalid choice: "
    "'issues'\\n\"); sys.exit(2)",
]


def without_issues():
    """Patch the reviews' ``concorde`` so that it offers no ``issues``."""
    return patch("concorde.method.review_issues.concorde_command", return_value=NO_ISSUES)


def finding(basis="scenario.a.answer", **values):
    return {
        "module": "module.a",
        "kind": "violation",
        "severity": "high",
        "tier": "obvious-fix",
        "title": "add subtracts",
        "problem": "add subtracts its arguments.",
        "impact": "Every caller gets a wrong sum.",
        "basis": basis,
        "locations": ["src/a/calc.py:2"],
        "evidence": "calc.py:2 returns a + b",
        "suggestion": "Add instead.",
        **values,
    }


def reviewer(*findings, resolved=(), **result):
    output = {"findings": list(findings)}
    if resolved:
        output["resolved"] = list(resolved)
    return [{"result": {"summary": "reviewed", "output": output, **result}}]


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
        wrapper = self.project.base / "claude-reviewer"
        wrapper.write_text(
            f'#!/bin/sh\nexec "{sys.executable}" "{FAKE_REVIEWER}" "$@"\n'
        )
        wrapper.chmod(0o755)
        self.project.fake = wrapper
        self.task = self.project.open_task("t1", modules=("module.a", "module.b"))
        self.worktree = self.project.worktree("t1")
        (self.worktree / "src/a/calc.py").write_text(FIXED)

    def review(self, plans, *extra, modules=None):
        """Run the review with one plan per reviewed Module; the settings Workers generated for
        each reviewer are kept in ``self.settings``, since they live in the worker's runtime
        directory, removed at its end."""
        self.settings = []
        original = claude_backend.worker_settings

        def spy(*args, **kwargs):
            value = original(*args, **kwargs)
            self.settings.append(value)
            return value

        focus = "Look at add first.\nFAKE-PLANS: " + json.dumps(plans)
        arguments = ["code_review", "--task", "t1", "--focus", focus, *extra]
        if modules:
            arguments += ["--modules", ",".join(modules)]
        with patch.object(claude_backend, "worker_settings", side_effect=spy):
            status, envelope = self.project.run(*arguments)
        if envelope and envelope.get("output") is not None:
            validate(envelope["output"], REVIEW_SCHEMA)
        return status, envelope

    def change(self, *findings, extra=(), **result):
        """A change review of module.a whose reviewer returns ``findings``."""
        return self.review(
            {"module.a": reviewer(*findings, **result)},
            *extra,
            modules=("module.a",),
        )

    def worker(self, envelope, index=-1) -> tuple[dict, str]:
        """A reviewer's run record and its first prompt (the brief its run directory keeps)."""
        record = read_record(self.root / ".concorde", envelope["worker_runs"][index])
        brief = (Path(record["run_directory"]) / "brief.md").read_text()
        return record, brief

    def issues(self) -> dict:
        """Every Issue of the project by identity: its record."""
        return {
            row["id"]: read_issue(self.root, row["id"])[0]
            for row in list_issues(self.root)
        }

    def earlier(self, title, tier="obvious-fix", operation="code_review"):
        """An open Issue of module.a an earlier review, or another reporter, made."""
        return report_issue(
            self.root,
            {
                "report_key": title,
                "tier": tier,
                "severity": "medium",
                "type": "bug",
                "subtype": None,
                "title": title,
                "description": f"Earlier problem {title}.",
                "impact": "A caller could not rely on it.",
                "basis": "An earlier review.",
                "owner_target_id": "module.a",
                "evidence": [],
            },
            {
                "invocation_id": f"r-earlier-{title}",
                "agent": "operation",
                "operation": operation,
                "phase": "report",
                "target_id": "module.a",
                "context_id": "sha256:" + "a" * 64,
                "change_id": None,
                "head": None,
            },
        )["issue_id"]

    def module_entry(self, envelope, module="module.a") -> dict:
        return next(
            item for item in envelope["output"]["modules"] if item["module"] == module
        )

    # --- change review ---------------------------------------------------------------------

    @verifies("scenario.code-review.clean")
    def test_a_change_that_keeps_its_promises(self):
        status, envelope = self.change()
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        report = envelope["output"]
        self.assertEqual(("change", "accepted"), (report["scope"], report["verdict"]))
        self.assertEqual(self.task["base_commit"], report["base"])
        self.assertEqual(["src/a/calc.py"], report["reviewed_paths"])
        self.assertEqual([], report["named_only_paths"])
        self.assertEqual(["passed"], [item["outcome"] for item in report["checks"]])
        kinds = {item["kind"] for item in envelope["host_evidence"]}
        self.assertTrue(
            {"scope", "base", "diff", "check", "context-identity", "audit"} <= kinds
        )
        entry = self.module_entry(envelope)
        self.assertEqual("accepted", entry["outcome"])
        self.assertRegex(entry["context_identity"], r"^sha256:")
        self.assertEqual("reviewed", entry["summary"])
        self.assertEqual(
            {"carried": [], "resolved": [], "ignored": []}, entry["earlier_issues"]
        )
        record, prompt = self.worker(envelope)
        self.assertIn("Scope: change.", prompt)
        self.assertIn("+    return a + b", prompt)
        self.assertIn("check.a (module.a): passed", prompt)
        self.assertIn("Look at add first.", prompt)
        self.assertIn("No earlier code review left an open Issue", prompt)
        self.assertEqual("Read,Glob,Grep", record["tools"])
        # The check logs are check nodes below the run's own node, readable to the reviewer.
        log = Path(report["checks"][0]["log"])
        self.assertEqual(
            Path(envelope["host_evidence"][0]["detail"]) / "checks/check.a/output.log",
            log,
        )
        self.assertTrue(log.is_file())
        [settings] = self.settings
        checks = Path(os.path.realpath(log)).parent.parent
        self.assertIn(checks.as_posix(), settings["sandbox"]["filesystem"]["allowRead"])
        self.assertEqual({}, self.issues())

    @verifies("scenario.code-review.all-blocking")
    def test_every_blocking_finding_in_one_report_each_an_issue(self):
        findings = [
            finding(),
            finding("specs/a/module.md#design", kind="defect", tier="preferred-fix"),
            finding(
                kind="missing-test", locations=["src/a/calc.py"], tier="obvious-fix"
            ),
        ]
        before = status_lines(self.worktree)
        _, envelope = self.change(*findings)
        self.assertEqual("ok", envelope["status"], envelope)
        self.assertEqual("changes_required", envelope["output"]["verdict"])
        entry = self.module_entry(envelope)
        self.assertEqual("changes_required", entry["outcome"])
        reported = [item["issue"] for item in entry["findings"]]
        self.assertEqual(3, len(set(reported)))
        issues = self.issues()
        self.assertEqual(set(reported), set(issues))
        first = issues[reported[0]]["reports"][-1]
        self.assertEqual(
            ("module.a", "obvious-fix", "high", "gap", "implementation-spec-mismatch"),
            (
                first["report"]["owner_target_id"],
                first["report"]["tier"],
                first["report"]["severity"],
                first["report"]["type"],
                first["report"]["subtype"],
            ),
        )
        self.assertEqual(
            ["src/a/calc.py", "specs/a/obligations.md"],
            [item["path"] for item in first["report"]["evidence"]],
        )
        self.assertEqual("module.a/1", first["report"]["report_key"])
        self.assertEqual(
            ("operation", "code_review", "t1"),
            (
                first["source"]["agent"],
                first["source"]["operation"],
                first["source"]["change_id"],
            ),
        )
        self.assertEqual(entry["context_identity"], first["source"]["context_id"])
        self.assertIn("src/a/calc.py:2", first["report"]["basis"])
        defect = issues[reported[1]]["reports"][-1]["report"]
        self.assertEqual(("bug", None), (defect["type"], defect["subtype"]))
        issue_evidence = [
            item for item in envelope["host_evidence"] if item["kind"] == "issue"
        ]
        self.assertEqual(3, len(issue_evidence))
        record, _ = self.worker(envelope)
        self.assertEqual(1, len(record["rounds"]))
        self.assertEqual(1, len(envelope["worker_runs"]))
        self.assertEqual(before, status_lines(self.worktree))

    def test_suggestions_keep_the_verdict_accepted_and_are_reported(self):
        _, envelope = self.change(finding(tier="suggestion"))
        self.assertEqual("ok", envelope["status"], envelope)
        self.assertEqual("accepted", envelope["output"]["verdict"])
        [item] = self.module_entry(envelope)["findings"]
        self.assertEqual(
            "suggestion", self.issues()[item["issue"]]["reports"][-1]["report"]["tier"]
        )

    @verifies("scenario.code-review.spec-gap")
    def test_behaviour_the_spec_does_not_settle(self):
        gap = finding(
            "specs/a/module.md#design", kind="spec-gap", tier="decision-needed"
        )
        _, envelope = self.change(gap)
        self.assertEqual("ok", envelope["status"], envelope)
        [item] = self.module_entry(envelope)["findings"]
        self.assertEqual("spec-gap", item["kind"])
        report = self.issues()[item["issue"]]["reports"][-1]["report"]
        self.assertEqual(
            ("gap", "missing-contract"), (report["type"], report["subtype"])
        )

    @verifies("scenario.code-review.foreign-path")
    def test_a_changed_file_outside_the_grant_is_named_only(self):
        # Another Module's code is readable to a code review, so its change is shown in full;
        # only a file no Module binds stays a name.
        (self.worktree / "src/bmod/secret.py").write_text("SECRET = 2\n")
        (self.worktree / "src/a/extra.py").write_text("EXTRA = 1\n")
        (self.worktree / "tools").mkdir()
        (self.worktree / "tools/helper.py").write_text("HELPER = 3\n")
        out = finding(
            kind="out-of-scope", locations=["tools/helper.py"], tier="suggestion"
        )
        _, envelope = self.change(out)
        self.assertEqual("ok", envelope["status"], envelope)
        report = envelope["output"]
        self.assertEqual(
            ["src/a/calc.py", "src/a/extra.py", "src/bmod/secret.py"],
            report["reviewed_paths"],
        )
        self.assertEqual(["tools/helper.py"], report["named_only_paths"])
        _, prompt = self.worker(envelope)
        self.assertIn(f"{self.worktree}/tools/helper.py", prompt)
        self.assertNotIn("HELPER = 3", prompt)
        self.assertIn("+SECRET = 2", prompt)
        self.assertIn("+EXTRA = 1", prompt)

    def test_a_deleted_changed_file_may_be_a_location(self):
        (self.worktree / "src/new.py").unlink()
        _, envelope = self.change(finding(kind="defect", locations=["src/new.py"]))
        self.assertEqual("ok", envelope["status"], envelope)

    def test_an_absolute_location_is_kept_relative(self):
        located = finding(locations=[f"{self.worktree}/src/a/calc.py:1-2"])
        _, envelope = self.change(located)
        self.assertEqual("ok", envelope["status"], envelope)
        [item] = self.module_entry(envelope)["findings"]
        self.assertEqual(["src/a/calc.py:1-2"], item["locations"])

    @verifies("scenario.code-review.failing-check")
    def test_a_failing_check_is_reviewed_not_fatal(self):
        (self.worktree / "src/a/flag").write_text("broken")
        _, envelope = self.change()
        self.assertEqual("ok", envelope["status"], envelope)
        [check] = envelope["output"]["checks"]
        self.assertEqual(("failed", 1), (check["outcome"], check["exit_code"]))
        self.assertTrue((self.root / check["log"]).is_file())
        _, prompt = self.worker(envelope)
        self.assertIn("check.a (module.a): failed", prompt)
        self.assertIn(check["log"].split("/")[-1], prompt)

    # --- host checks -----------------------------------------------------------------------

    def unresolved(self, envelope) -> list[dict]:
        self.assertEqual("failed", envelope["status"], envelope)
        self.assertEqual("review_incomplete", envelope["error"]["code"])
        [cause] = envelope["error"]["causes"]
        self.assertEqual("unresolved_evidence", cause["code"])
        self.assertEqual("incomplete", envelope["output"]["verdict"])
        self.assertEqual({}, self.issues())
        return [
            item
            for item in envelope["host_evidence"]
            if item["kind"].startswith("unresolved-")
        ]

    @verifies("scenario.code-review.unknown-basis")
    def test_a_finding_citing_an_unknown_promise_is_not_reported(self):
        status, envelope = self.change(finding("req.a.nothing"), finding())
        self.assertEqual(1, status)
        [problem] = self.unresolved(envelope)
        self.assertEqual(
            ("unresolved-basis", "req.a.nothing"), (problem["kind"], problem["ref"])
        )
        self.assertIn("req.a.nothing", envelope["error"]["causes"][0]["detail"])
        self.assertEqual(
            [None, None],
            [item["issue"] for item in self.module_entry(envelope)["findings"]],
        )

    def test_a_document_outside_the_context_does_not_resolve(self):
        _, envelope = self.change(finding("specs/elsewhere.md#x"))
        self.unresolved(envelope)

    @verifies("scenario.code-review.unknown-location")
    def test_a_finding_located_in_no_file_is_not_reported(self):
        _, envelope = self.change(
            finding(locations=["src/a/missing.py:3"]),
            finding(locations=["src/a/calc.py:40"]),
            finding(locations=["../outside.py"]),
            finding(locations=["src/a/"]),
        )
        problems = self.unresolved(envelope)
        self.assertEqual(
            ["src/a/missing.py:3", "src/a/calc.py:40", "../outside.py", "src/a/"],
            [item["ref"] for item in problems],
        )

    def test_a_finding_about_a_module_not_reviewed_is_not_reported(self):
        _, envelope = self.change(finding(module="module.b"))
        [problem] = self.unresolved(envelope)
        self.assertEqual("unresolved-module", problem["kind"])

    @verifies("scenario.code-review.reviewer-change")
    def test_a_changing_reviewer_fails_the_run(self):
        plan = [
            {
                "writes": {f"{self.worktree}/src/a/calc.py": "BROKEN = 1\n"},
                "result": {"output": {"findings": []}},
            }
        ]
        _, envelope = self.review({"module.a": plan}, modules=("module.a",))
        self.assertEqual("failed", envelope["status"])
        audit = [item for item in envelope["host_evidence"] if item["kind"] == "audit"]
        self.assertIn("src/a/calc.py", audit[0]["detail"])
        self.assertEqual("incomplete", envelope["output"]["verdict"])

    def test_a_blocked_reviewer_blocks_the_run_and_keeps_what_was_obtained(self):
        standing = self.earlier("standing")
        _, envelope = self.change(status="blocked", summary="cannot judge")
        self.assertEqual("blocked", envelope["status"], envelope)
        self.assertEqual("review_incomplete", envelope["error"]["code"])
        entry = self.module_entry(envelope)
        self.assertEqual("cannot judge", entry["summary"])
        self.assertEqual(
            [standing], [item["issue"] for item in entry["earlier_issues"]["carried"]]
        )

    def test_an_unknown_base_fails_before_the_reviewer(self):
        _, envelope = self.change(extra=("--base", "no-such-ref"))
        self.assertEqual("failed", envelope["status"])
        self.assertEqual("unresolved_base", envelope["error"]["code"])
        self.assertIsNone(envelope["output"])
        self.assertEqual([], envelope["worker_runs"])
        self.assertEqual(
            ["trace", "scope", "base"],
            [item["kind"] for item in envelope["host_evidence"]][:3],
        )

    def test_an_explicit_base_is_resolved(self):
        _, envelope = self.change(extra=("--base", "HEAD"))
        self.assertEqual("ok", envelope["status"], envelope)
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=self.worktree,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        self.assertEqual(head, envelope["output"]["base"])

    # --- Module review ---------------------------------------------------------------------

    @verifies("scenario.code-review.module-review")
    def test_each_module_is_judged_whole_by_its_own_reviewer(self):
        b = finding(
            "scenario.b.answer", module="module.b", locations=["src/bmod/secret.py:1"]
        )
        _, envelope = self.review(
            {"module.a": reviewer(), "module.b": reviewer(b)},
            "--scope",
            "module",
        )
        self.assertEqual("ok", envelope["status"], envelope)
        report = envelope["output"]
        self.assertEqual(("module", None), (report["scope"], report["base"]))
        self.assertEqual(
            ([], []), (report["reviewed_paths"], report["named_only_paths"])
        )
        # Only the reviewed Modules' own checks run: module.a has one, module.b none.
        self.assertEqual(["check.a"], [item["check"] for item in report["checks"]])
        self.assertEqual(2, len(envelope["worker_runs"]))
        self.assertEqual(
            [("module.a", "accepted"), ("module.b", "changes_required")],
            [(item["module"], item["outcome"]) for item in report["modules"]],
        )
        self.assertEqual("changes_required", report["verdict"])
        a, b_entry = report["modules"]
        self.assertNotEqual(a["context_identity"], b_entry["context_identity"])
        _, first = self.worker(envelope, 0)
        _, second = self.worker(envelope, 1)
        self.assertIn("Scope: module.", first)
        self.assertIn("Reviewed Module: `module.a`.", first)
        self.assertIn(f"{self.worktree}/specs/a/module.md", first)
        self.assertIn(f"{self.worktree}/src/a/", first)
        self.assertIn(f"{self.worktree}/src/new.py", first)
        self.assertNotIn("### Diff", first)
        self.assertIn("check.a (module.a): passed", first)
        self.assertIn("Reviewed Module: `module.b`.", second)
        self.assertIn(f"{self.worktree}/src/bmod/", second)
        self.assertNotIn("check.a", second.split("### Check results", 1)[1])
        [item] = b_entry["findings"]
        self.assertEqual(
            "module.b",
            self.issues()[item["issue"]]["reports"][-1]["report"]["owner_target_id"],
        )

    def test_a_module_reviewer_judges_only_against_its_own_context(self):
        # module.b does not use module.a, so module.a's Spec is no basis for module.b.
        b = finding(
            "scenario.a.answer", module="module.b", locations=["src/bmod/secret.py"]
        )
        _, envelope = self.review(
            {"module.a": reviewer(), "module.b": reviewer(b)}, "--scope", "module"
        )
        self.assertEqual("failed", envelope["status"], envelope)
        self.assertEqual(
            [("module.a", "accepted"), ("module.b", "incomplete")],
            [
                (item["module"], item["outcome"])
                for item in envelope["output"]["modules"]
            ],
        )
        [cause] = envelope["error"]["causes"]
        self.assertEqual("unresolved_evidence", cause["code"])

    @verifies("scenario.code-review.module-review-base")
    def test_a_module_review_refuses_a_base(self):
        status, envelope = self.review({}, "--scope", "module", "--base", "HEAD")
        self.assertEqual((1, "failed"), (status, envelope["status"]))
        self.assertEqual("base_in_module_scope", envelope["error"]["code"])
        self.assertEqual([], envelope["worker_runs"])

    @verifies("scenario.code-review.spec-challenge")
    def test_a_reviewer_challenges_an_unrealizable_requirement(self):
        challenge = finding(
            "scenario.a.answer",
            kind="spec-challenge",
            tier="decision-needed",
            problem="The scenario asks A to answer every question, which no function can.",
        )
        _, envelope = self.review(
            {"module.a": reviewer(challenge)},
            "--scope",
            "module",
            modules=("module.a",),
        )
        self.assertEqual("ok", envelope["status"], envelope)
        self.assertEqual("changes_required", envelope["output"]["verdict"])
        [item] = self.module_entry(envelope)["findings"]
        report = self.issues()[item["issue"]]["reports"][-1]["report"]
        self.assertEqual(
            ("decision-needed", "gap", "implementation-spec-mismatch"),
            (report["tier"], report["type"], report["subtype"]),
        )
        self.assertIn("spec-challenge", report["basis"])

    @verifies("scenario.code-review.unbound-module-review")
    def test_an_unbound_module_review_reports_to_the_projects_issues(self):
        plans = json.dumps({"module.a": reviewer(finding())})
        _, envelope = self.project.run(
            "code_review",
            "--scope",
            "module",
            "--modules",
            "module.a",
            "--focus",
            f"FAKE-PLANS: {plans}",
            cwd=self.root,
        )
        self.assertEqual("ok", envelope["status"], envelope)
        self.assertIsNone(envelope["workspace"])
        self.assertIsNotNone(envelope["commit"])
        [item] = self.module_entry(envelope)["findings"]
        source = self.issues()[item["issue"]]["reports"][-1]["source"]
        self.assertEqual(
            (None, envelope["commit"]), (source["change_id"], source["head"])
        )

    # --- Issues ----------------------------------------------------------------------------

    @verifies("scenario.code-review.earlier-issue")
    def test_a_problem_already_recorded_is_updated_not_duplicated(self):
        named = self.earlier("named")
        gone = self.earlier("gone")
        standing = self.earlier("standing", tier="decision-needed")
        other = self.earlier("spec problem", operation="spec_review")
        _, envelope = self.change(
            finding(earlier=named, tier="preferred-fix"),
            finding(earlier="I-" + "f" * 32),
            resolved=[
                {"issue": gone, "reason": "add now adds"},
                {"issue": other, "reason": "not offered"},
            ],
        )
        self.assertEqual("ok", envelope["status"], envelope)
        _, prompt = self.worker(envelope)
        offered = prompt.split("Earlier code reviews recorded these", 1)[1].split(
            "## Your boundary"
        )[0]
        self.assertIn(named, offered)
        self.assertNotIn(other, offered)
        entry = self.module_entry(envelope)
        first, second = entry["findings"]
        self.assertEqual((named, named), (first["earlier"], first["issue"]))
        self.assertNotIn("earlier", second)
        self.assertNotEqual(named, second["issue"])
        record = self.issues()[named]
        self.assertEqual(2, len(record["reports"]))
        self.assertEqual("preferred-fix", record["reports"][-1]["report"]["tier"])
        summary = entry["earlier_issues"]
        self.assertEqual([standing], [item["issue"] for item in summary["carried"]])
        self.assertEqual(
            [{"issue": gone, "reason": "add now adds"}], summary["resolved"]
        )
        self.assertEqual(
            {"I-" + "f" * 32, other}, {item["issue"] for item in summary["ignored"]}
        )
        self.assertEqual("open", self.issues()[gone]["status"])
        self.assertEqual("changes_required", entry["outcome"])

    @verifies("scenario.code-review.store-refusal")
    def test_a_refusal_of_the_issue_store_is_an_error_not_an_issue(self):
        interrupted = self.root / ".concorde/tasks/interrupted"
        interrupted.mkdir(parents=True)
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        (interrupted / "task.json").write_text(
            json.dumps(
                {
                    "schema_version": 4,
                    "id": "interrupted",
                    "state": "merging",
                    "merging": {
                        "before": head,
                        "checked": head,
                        "branch": "main",
                        "after": None,
                        "pid": 1,
                        "since": "2026-10-01T00:00:00Z",
                    },
                    "reports": [],
                }
            )
        )
        status, envelope = self.change(finding(), finding(kind="defect"))
        self.assertEqual((1, "failed"), (status, envelope["status"]), envelope)
        entry = self.module_entry(envelope)
        self.assertEqual("incomplete", entry["outcome"])
        self.assertEqual([None, None], [item["issue"] for item in entry["findings"]])
        self.assertEqual({}, self.issues())
        [cause] = envelope["error"]["causes"]
        self.assertEqual("issues_unreported", cause["code"])
        [store] = cause["causes"]
        self.assertEqual("merge_incomplete", store["code"])


    @verifies("scenario.code-review.without-issues")
    def test_without_the_issues_part_the_findings_stay_in_the_report(self):
        with without_issues():
            status, envelope = self.change(finding())
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        entry = self.module_entry(envelope)
        self.assertEqual("changes_required", entry["outcome"])
        self.assertEqual([None], [item["issue"] for item in entry["findings"]])
        self.assertIsNone(entry["earlier_issues"])
        self.assertIn(NOT_RECORDED, envelope["summary"])
        self.assertEqual({}, self.issues())
        _, brief = self.worker(envelope)
        self.assertIn("the issues part is not installed", brief)

class ContractTests(unittest.TestCase):
    def test_the_output_schema_is_the_contract(self):
        [contract] = SpecRepository(REPOSITORY_ROOT).contracts("module.code-review")
        self.assertEqual(contract["schema"], REVIEW_SCHEMA)
        validate(contract["example"], REVIEW_SCHEMA)


if __name__ == "__main__":
    unittest.main()
