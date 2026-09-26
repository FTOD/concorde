"""The ``spec_review`` Operation end to end, with a fake ``claude`` per reviewer and checker."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from concorde.spec.grants import grant
from concorde.spec.repository import SpecRepository
from concorde.spec.schema import validate
from concorde.spec.verification import verifies
from concorde.spec_review.memory import MEMORY_SCHEMA
from concorde.spec_review.operation import PAYLOAD_SCHEMA
from tests.concorde.support.operation_project import (
    OperationProject,
    link_at,
    worker_error,
)
from tests.concorde.support.paths import REPOSITORY_ROOT

FAKE_REVIEWER = Path(__file__).with_name("fake_reviewer.py")


def finding(path, severity="blocking", module="module.a", **extra):
    return {
        "module": module,
        "path": path,
        "dimension": "obligations",
        "severity": severity,
        "problem": f"A problem in {path}.",
        "evidence": "Quoted text.",
        "suggestion": "Rewrite it.",
        **extra,
    }


def reviewer(*findings, **result):
    return [{"result": {"output": {"findings": list(findings)}, **result}}]


def checker(*checks):
    return [{"result": {"output": {"checks": list(checks)}}}]


class SpecReviewTests(unittest.TestCase):
    def setUp(self):
        self.project = OperationProject(self)
        self.root = self.project.root
        wrapper = self.project.base / "claude-reviewer"
        wrapper.write_text(
            f'#!/bin/sh\nexec "{sys.executable}" "{FAKE_REVIEWER}" "$@"\n'
        )
        wrapper.chmod(0o755)
        self.project.fake = wrapper

    def review(self, plans, *extra, modules=("module.a",)):
        goal = "Review the Specs.\nFAKE-PLANS: " + json.dumps(plans)
        self.project.open_task("t1", modules=modules, goal=goal)
        self.worktree = self.project.worktree("t1")
        return self.project.run(
            "spec_review", "--task", "t1", "--modules", ",".join(modules), *extra
        )

    def identity(self, module):
        return grant(
            SpecRepository(self.worktree, REPOSITORY_ROOT), [module], "review-spec"
        ).value["context_identity"]

    def status(self):
        return subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=self.worktree,
            capture_output=True,
            text=True,
            check=True,
        ).stdout

    def record(self, run_id):
        return json.loads(
            (self.root / ".concorde/runs" / run_id / "record.json").read_text()
        )

    def brief(self, run_id):
        work = Path(self.record(run_id)["run_directory"]) / "work"
        return json.loads((work / "fake-round-1.json").read_text())["prompt"]

    def kinds(self, envelope):
        return [item["kind"] for item in envelope["host_evidence"]]

    @verifies("scenario.spec-review.accepted")
    def test_advisory_findings_only_are_accepted(self):
        exit_status, envelope = self.review(
            {
                "reviewer module.a": reviewer(
                    finding("specs/a/module.md", "advisory", dimension="readability")
                )
            }
        )
        self.assertEqual((0, "ok"), (exit_status, envelope["status"]), envelope)
        output = envelope["output"]
        self.assertEqual("accepted", output["verdict"])
        (module,) = output["modules"]
        self.assertEqual("accepted", module["outcome"])
        self.assertEqual(self.identity("module.a"), module["context_identity"])
        self.assertEqual(
            ["advisory"], [item["severity"] for item in module["findings"]]
        )
        self.assertIsNone(module["findings"][0]["check"])
        # The review changes nothing but the Module's review memory, which keeps the advisory.
        self.assertEqual("?? .concorde/reviews/\n", self.status())
        memory = json.loads(
            (self.worktree / ".concorde/reviews/spec/module.a.json").read_text()
        )
        self.assertEqual(
            [("f.1", "open", "advisory")],
            [(f["id"], f["status"], f["severity"]) for f in memory["findings"]],
        )
        self.assertEqual(1, len(envelope["worker_runs"]))
        brief = self.brief(envelope["worker_runs"][0])
        self.assertIn("You are a Concorde Spec reviewer", brief)
        self.assertIn("Your role: reviewer.", brief)
        self.assertIn("Reviewed Module: `module.a`", brief)
        self.assertIn("every blocking finding you can establish in this one run", brief)
        validate(output, PAYLOAD_SCHEMA)

    @verifies("scenario.spec-review.changes-required")
    def test_every_blocking_finding_is_returned_in_one_result(self):
        # The second finding cites an absolute path, as a worker reading absolute paths would.
        exit_status, envelope = self.review(
            {
                "reviewer module.a": reviewer(
                    finding("specs/a/obligations.md", anchor="req.a.two", line=3),
                    finding(
                        "@WORKTREE@/specs/a/module.md",
                        dimension="readability",
                        problem="Usage never shows a normal path.",
                    ),
                )
            }
        )
        self.assertEqual((0, "ok"), (exit_status, envelope["status"]), envelope)
        output = envelope["output"]
        self.assertEqual("changes_required", output["verdict"])
        findings = output["modules"][0]["findings"]
        self.assertEqual(
            ["specs/a/obligations.md", "specs/a/module.md"],
            [item["path"] for item in findings],
        )
        self.assertEqual(
            ["blocking", "blocking"], [item["severity"] for item in findings]
        )
        self.assertEqual("req.a.two", findings[0]["anchor"])
        for item in findings:
            self.assertTrue(
                item["dimension"] and item["evidence"] and item["suggestion"]
            )
        # Worker claims stay out of the host's summary and evidence.
        host_text = json.dumps(envelope["host_evidence"]) + envelope["summary"]
        self.assertNotIn("normal path", host_text)
        self.assertIn("2 blocking finding(s) stand", envelope["summary"])

    @verifies("scenario.spec-review.checker")
    def test_a_disputed_finding_does_not_require_changes(self):
        exit_status, envelope = self.review(
            {
                "reviewer module.a": reviewer(finding("specs/a/module.md")),
                "checker module.a": checker(
                    {
                        "finding": 1,
                        "status": "disputed",
                        "reason": "The quoted text is not in the Spec.",
                    }
                ),
            },
            "--check-findings",
        )
        self.assertEqual((0, "ok"), (exit_status, envelope["status"]), envelope)
        output = envelope["output"]
        self.assertEqual("accepted", output["verdict"])
        (item,) = output["modules"][0]["findings"]
        self.assertEqual("blocking", item["severity"])
        self.assertEqual(
            {"status": "disputed", "reason": "The quoted text is not in the Spec."},
            item["check"],
        )
        self.assertEqual(2, len(envelope["worker_runs"]))
        brief = self.brief(envelope["worker_runs"][1])
        self.assertIn("Your role: checker.", brief)
        self.assertIn("Finding 1:", brief)
        checker_grant = self.record(envelope["worker_runs"][1])
        self.assertEqual(self.identity("module.a"), checker_grant["context_identity"])

    def remembered(self, *findings):
        """A task whose worktree holds a review memory with ``findings`` open."""
        return {
            "schema_version": 1,
            "module": "module.a",
            "findings": [
                {
                    "id": identity,
                    "status": "open",
                    "path": "specs/a/module.md",
                    "dimension": "obligations",
                    "severity": severity,
                    "problem": f"Earlier problem {identity}.",
                    "evidence": "Quoted text.",
                    "suggestion": "Rewrite it.",
                    "first_run": "r-earlier",
                    "last_run": "r-earlier",
                    "resolution": None,
                }
                for identity, severity in findings
            ],
        }

    def review_with_memory(self, memory, plans):
        goal = "Review the Specs.\nFAKE-PLANS: " + json.dumps(plans)
        self.project.open_task("t1", modules=("module.a",), goal=goal)
        self.worktree = self.project.worktree("t1")
        path = self.worktree / ".concorde/reviews/spec/module.a.json"
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(memory))
        status, envelope = self.project.run(
            "spec_review", "--task", "t1", "--modules", "module.a"
        )
        return status, envelope, json.loads(path.read_text())

    @verifies("scenario.spec-review.memory")
    def test_a_repeated_review_adds_updates_resolves_and_carries(self):
        memory = self.remembered(
            ("f.1", "blocking"), ("f.2", "blocking"), ("f.3", "advisory")
        )
        updated = finding(
            "specs/a/module.md", earlier="f.2", problem="Changed problem."
        )
        status, envelope, after = self.review_with_memory(
            memory,
            {
                "reviewer module.a": [
                    {
                        "result": {
                            "output": {
                                "findings": [
                                    updated,
                                    finding("specs/a/module.md", "advisory"),
                                ],
                                "resolved": [
                                    {"id": "f.3", "reason": "The Usage was rewritten."},
                                    {"id": "f.9", "reason": "No such finding."},
                                ],
                            }
                        }
                    }
                ]
            },
        )
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        (module,) = envelope["output"]["modules"]
        # f.1 was not mentioned: it is carried, still open and blocking, so changes are required.
        self.assertEqual("changes_required", module["outcome"])
        self.assertEqual(["f.2", "f.4"], [item["id"] for item in module["findings"]])
        summary = module["memory"]
        self.assertEqual((["f.4"], ["f.2"]), (summary["new"], summary["updated"]))
        self.assertEqual(
            [{"id": "f.3", "reason": "The Usage was rewritten."}], summary["resolved"]
        )
        self.assertEqual(["f.1"], [item["id"] for item in summary["carried"]])
        self.assertEqual(["f.9"], [item["id"] for item in summary["ignored"]])
        state = {item["id"]: item for item in after["findings"]}
        self.assertEqual("Changed problem.", state["f.2"]["problem"])
        self.assertEqual("resolved", state["f.3"]["status"])
        self.assertEqual(envelope["run_id"], state["f.4"]["first_run"])
        brief = self.brief(envelope["worker_runs"][0])
        self.assertIn("Earlier problem f.1.", brief)
        self.assertNotIn("r-earlier", brief)

    @verifies("scenario.spec-review.unchanged")
    def test_a_module_with_unchanged_specs_is_decided_by_its_memory(self):
        memory = self.remembered(("f.1", "blocking"))
        self.project.open_task("t1", modules=("module.a",), goal="Review.")
        self.worktree = self.project.worktree("t1")
        memory["reviewed"] = {
            "context_identity": self.identity("module.a"),
            "run": "r-earlier",
        }
        path = self.worktree / ".concorde/reviews/spec/module.a.json"
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(memory))
        status, envelope = self.project.run(
            "spec_review", "--task", "t1", "--modules", "module.a"
        )
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        self.assertEqual([], envelope["worker_runs"])
        (module,) = envelope["output"]["modules"]
        self.assertEqual("changes_required", module["outcome"])
        self.assertEqual("r-earlier", module["memory"]["unchanged_since"])
        self.assertEqual(["f.1"], [item["id"] for item in module["memory"]["carried"]])
        self.assertIn("review-skipped", self.kinds(envelope))

    @verifies("scenario.spec-review.unchanged")
    def test_a_completed_review_records_what_it_judged_and_force_reviews_again(self):
        status, envelope, after = self.review_with_memory(
            self.remembered(),
            {"reviewer module.a": reviewer(finding("specs/a/module.md", "advisory"))},
        )
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        self.assertEqual(
            {"context_identity": self.identity("module.a"), "run": envelope["run_id"]},
            after["reviewed"],
        )
        self.assertIsNone(envelope["output"]["modules"][0]["memory"]["unchanged_since"])
        _, forced = self.project.run(
            "spec_review", "--task", "t1", "--modules", "module.a", "--force"
        )
        self.assertEqual(1, len(forced["worker_runs"]), forced)

    @verifies("scenario.spec-review.memory")
    def test_resolving_every_earlier_blocking_finding_accepts_the_module(self):
        _, envelope, after = self.review_with_memory(
            self.remembered(("f.1", "blocking")),
            {
                "reviewer module.a": [
                    {
                        "result": {
                            "output": {
                                "findings": [],
                                "resolved": [{"id": "f.1", "reason": "Split."}],
                            }
                        }
                    }
                ]
            },
        )
        self.assertEqual("accepted", envelope["output"]["verdict"], envelope)
        self.assertEqual("resolved", after["findings"][0]["status"])

    @verifies("scenario.spec-review.checker")
    def test_a_confirmed_finding_still_requires_changes(self):
        exit_status, envelope = self.review(
            {
                "reviewer module.a": reviewer(finding("specs/a/module.md")),
                "checker module.a": checker(
                    {"finding": 1, "status": "confirmed", "reason": "It holds."}
                ),
            },
            "--check-findings",
        )
        self.assertEqual(
            (0, "changes_required"), (exit_status, envelope["output"]["verdict"])
        )

    def test_a_failed_checker_leaves_the_findings_unchecked(self):
        exit_status, envelope = self.review(
            {
                "reviewer module.a": reviewer(finding("specs/a/module.md")),
                "checker module.a": [{"raw": "not json"}],
            },
            "--check-findings",
        )
        self.assertEqual((1, "failed"), (exit_status, envelope["status"]))
        output = envelope["output"]
        self.assertEqual("incomplete", output["verdict"])
        self.assertIsNone(output["modules"][0]["findings"][0]["check"])
        error = envelope["error"]
        self.assertEqual("review_incomplete", error["code"])
        [module] = error["causes"]
        self.assertIn("review of module.a", module["actor"])
        self.assertEqual("claude_failed", module["code"])

    @verifies("scenario.spec-review.several-modules")
    def test_each_module_is_reviewed_on_its_own(self):
        exit_status, envelope = self.review(
            {
                "reviewer module.a": reviewer(
                    finding("specs/a/module.md", "advisory"),
                    finding("specs/b/module.md"),
                ),
                "reviewer module.b": reviewer(
                    finding("specs/b/obligations.md", module="module.b")
                ),
            },
            modules=("module.a", "module.b"),
        )
        self.assertEqual((0, "ok"), (exit_status, envelope["status"]), envelope)
        output = envelope["output"]
        by_module = {item["module"]: item for item in output["modules"]}
        self.assertEqual("accepted", by_module["module.a"]["outcome"])
        self.assertEqual("changes_required", by_module["module.b"]["outcome"])
        self.assertEqual("changes_required", output["verdict"])
        about_b = by_module["module.a"]["findings"][1]
        self.assertEqual(
            ("module.b", "advisory"), (about_b["module"], about_b["severity"])
        )
        self.assertIn("finding-scope", self.kinds(envelope))
        self.assertEqual(2, len(envelope["worker_runs"]))
        for run_id, module in zip(envelope["worker_runs"], ("module.a", "module.b")):
            record = self.record(run_id)
            frozen = json.loads(
                (Path(record["run_directory"]) / "control/grant.json").read_text()
            )
            self.assertEqual(
                ([module], "review-spec"), (frozen["modules"], frozen["task_type"])
            )
            self.assertEqual(
                self.identity(module), by_module[module]["context_identity"]
            )
        self.assertNotEqual(
            by_module["module.a"]["context_identity"],
            by_module["module.b"]["context_identity"],
        )

    @verifies("scenario.spec-review.structural-errors")
    def test_a_structurally_invalid_module_is_not_reviewed(self):
        self.project.open_task("t1", goal="Review.")
        self.worktree = self.project.worktree("t1")
        entry = self.worktree / "specs/a/module.md"
        entry.write_text(entry.read_text().replace("## Usage", "## Use"))
        exit_status, envelope = self.project.run(
            "spec_review", "--task", "t1", "--modules", "module.a"
        )
        self.assertEqual((1, "blocked"), (exit_status, envelope["status"]), envelope)
        self.assertEqual([], envelope["worker_runs"])
        output = envelope["output"]
        self.assertEqual("incomplete", output["verdict"])
        self.assertEqual(
            {
                "module": "module.a",
                "outcome": "incomplete",
                "context_identity": None,
                "findings": [],
                "memory": None,
            },
            output["modules"][0],
        )
        structural = [
            item for item in envelope["host_evidence"] if item["kind"] == "structural"
        ]
        self.assertTrue(structural)
        self.assertTrue(all("specs/a/" in item["ref"] for item in structural))
        [module] = envelope["error"]["causes"]
        self.assertEqual("structural_errors", module["code"])
        self.assertTrue(module["causes"])
        self.assertTrue(all("specs/a/" in item["detail"] for item in module["causes"]))

    def test_an_unloadable_worktree_fails_the_run(self):
        self.project.open_task("t1", goal="Review.")
        self.worktree = self.project.worktree("t1")
        (self.worktree / ".concorde/specs.json").write_text("{")
        exit_status, envelope = self.project.run(
            "spec_review", "--task", "t1", "--modules", "module.a"
        )
        self.assertEqual((1, "failed"), (exit_status, envelope["status"]), envelope)
        self.assertIsNone(envelope["output"])
        self.assertEqual([], envelope["worker_runs"])
        # The runner already refuses a worktree whose Specs do not load; the review's own
        # loading check is the same rule applied again.
        self.assertTrue({"refused", "structural"} & set(self.kinds(envelope)))

    @verifies("scenario.spec-review.worker-blocked")
    def test_a_blocked_reviewer_makes_the_review_incomplete(self):
        exit_status, envelope = self.review(
            {
                "reviewer module.a": reviewer(
                    status="blocked",
                    error=worker_error(
                        "The entry of module.c is needed to judge the Usage.",
                        code="context_missing",
                        reason="permission",
                        attempts=["read the selected documents"],
                        options=[
                            "add a uses relation to module.c",
                            "review module.c first",
                        ],
                        recommendation="add the relation",
                    ),
                )
            }
        )
        self.assertEqual((1, "blocked"), (exit_status, envelope["status"]))
        output = envelope["output"]
        self.assertEqual(
            ("incomplete", "incomplete"),
            (output["verdict"], output["modules"][0]["outcome"]),
        )
        self.assertEqual(
            self.identity("module.a"), output["modules"][0]["context_identity"]
        )
        worker = link_at(envelope["error"], "worker")
        self.assertEqual(
            "The entry of module.c is needed to judge the Usage.", worker["detail"]
        )
        self.assertEqual(["read the selected documents"], worker["attempts"])
        self.assertEqual(
            ["add a uses relation to module.c", "review module.c first"],
            worker["options"],
        )
        self.assertEqual("blocked", envelope["worker"]["status"])

    @verifies("scenario.spec-review.audit-change")
    def test_a_reviewer_that_changed_a_file_is_incomplete(self):
        exit_status, envelope = self.review(
            {
                "reviewer module.a": [
                    {
                        "writes": {"@WORKTREE@/specs/a/module.md": "# Rewritten\n"},
                        "result": {"output": {"findings": []}},
                    }
                ]
            }
        )
        self.assertEqual((1, "failed"), (exit_status, envelope["status"]), envelope)
        self.assertEqual("incomplete", envelope["output"]["modules"][0]["outcome"])
        audit = [
            item
            for item in envelope["host_evidence"]
            if item["kind"] in {"audit", "audit_violation"}
        ]
        self.assertTrue(
            any("specs/a/module.md" in item["detail"] for item in audit), audit
        )


class PayloadContractTests(unittest.TestCase):
    def test_the_code_follows_the_payload_contract(self):
        repository = SpecRepository(REPOSITORY_ROOT)
        (contract,) = [
            item
            for item in repository.contracts("module.spec-review")
            if item["id"] == "contract.spec-review.payload"
        ]
        self.assertEqual(contract["schema"], PAYLOAD_SCHEMA)
        validate(contract["example"], PAYLOAD_SCHEMA)
        (memory,) = [
            item
            for item in repository.contracts("module.spec-review")
            if item["id"] == "contract.spec-review.memory"
        ]
        self.assertEqual(memory["schema"], MEMORY_SCHEMA)
        validate(memory["example"], MEMORY_SCHEMA)


if __name__ == "__main__":
    unittest.main()
