"""The ``spec_review`` Operation end to end, with a fake ``claude`` per reviewer and checker."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from concorde.worker_harness.runs import read_record
from concorde.issues.store import list_issues, read_issue, report_issue
from concorde.spec.grants import grant
from concorde.spec.repository import SpecRepository
from concorde.spec.schema import validate
from concorde.spec.verification import verifies
from concorde.method.spec_review.operation import PAYLOAD_SCHEMA
from concorde.method.review_issues import NOT_RECORDED
from tests.concorde.support.operation_project import (
    OperationProject,
    link_at,
    worker_error,
)
from tests.concorde.support.paths import REPOSITORY_ROOT

FAKE_REVIEWER = Path(__file__).with_name("fake_reviewer.py")


# A ``concorde`` that refuses ``issues`` as Distribution's does where the issues part is not
# installed.
NO_ISSUES = [
    sys.executable,
    "-c",
    f"import json, sys; sys.path.insert(0, {str(REPOSITORY_ROOT / 'src')!r}); "
    "from concorde.distribution.cli import part_missing; "
    "print(json.dumps({'error': part_missing('issues', 'commands', 'issues')})); sys.exit(1)",
]


def without_issues():
    """Patch the reviews' ``concorde`` so that it offers no ``issues``."""
    return patch(
        "concorde.method.review_issues.concorde_command", return_value=NO_ISSUES
    )


def finding(path, tier="obvious-fix", module="module.a", **extra):
    return {
        "module": module,
        "path": path,
        "dimension": "obligations",
        "severity": "high",
        "tier": tier,
        "title": f"A problem in {path}",
        "problem": f"A problem in {path}.",
        "impact": "A reader could not rely on it.",
        "evidence": "Quoted text.",
        "suggestion": "Rewrite it.",
        **extra,
    }


def earlier_report(module, tier, title, operation="spec_review", root=None):
    """Record an open Issue of ``module`` as an earlier review, or another reporter, made it."""
    receipt = report_issue(
        root,
        {
            "report_key": title,
            "tier": tier,
            "severity": "medium",
            "type": "bug",
            "subtype": None,
            "title": title,
            "description": f"Earlier problem {title}.",
            "impact": "A reader could not rely on it.",
            "basis": "An earlier review.",
            "owner_target_id": module,
            "evidence": [],
        },
        {
            "invocation_id": f"r-earlier-{title}",
            "agent": "operation" if operation != "issues" else "task-session",
            "operation": operation,
            "phase": "report",
            "target_id": module,
            "context_id": "sha256:" + "a" * 64,
            "change_id": None,
            "head": None,
        },
    )
    return receipt["issue_id"]


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
        """The worker run's record, rebuilt from its trace node below the primary's records."""
        return read_record(self.root / ".concorde", run_id)

    def brief(self, run_id):
        """The worker's first prompt: the brief its run directory keeps."""
        return (Path(self.record(run_id)["run_directory"]) / "brief.md").read_text()

    def kinds(self, envelope):
        return [item["kind"] for item in envelope["host_evidence"]]

    def issues(self):
        """Every Issue of the project by identity: its record."""
        return {
            row["id"]: read_issue(self.root, row["id"])[0]
            for row in list_issues(self.root)
        }

    def earlier(self, tier, title, module="module.a", operation="spec_review"):
        return earlier_report(module, tier, title, operation, root=self.root)

    @verifies("scenario.spec-review.accepted")
    def test_suggestions_only_are_accepted_and_recorded(self):
        exit_status, envelope = self.review(
            {
                "reviewer module.a": reviewer(
                    finding("specs/a/module.md", "suggestion", dimension="readability")
                )
            }
        )
        self.assertEqual((0, "ok"), (exit_status, envelope["status"]), envelope)
        output = envelope["output"]
        self.assertEqual("accepted", output["verdict"])
        (module,) = output["modules"]
        self.assertEqual("accepted", module["outcome"])
        self.assertEqual(self.identity("module.a"), module["context_identity"])
        (item,) = module["findings"]
        self.assertEqual("suggestion", item["tier"])
        self.assertIsNone(item["check"])
        self.assertEqual(
            {"carried": [], "resolved": [], "ignored": []}, module["earlier_issues"]
        )
        # The suggestion is a new Issue of the project, committed on the primary branch.
        issues = self.issues()
        self.assertEqual([item["issue"]], list(issues))
        record = issues[item["issue"]]
        (entry,) = record["reports"]
        self.assertEqual(
            ("suggestion", "module.a", "readability"),
            (
                entry["report"]["tier"],
                entry["report"]["owner_target_id"],
                entry["report"]["evidence"][0]["description"]
                .split(", cited by the ")[1]
                .split(" ")[0],
            ),
        )
        self.assertEqual(
            {
                "invocation_id": envelope["run_id"],
                "agent": "operation",
                "operation": "spec_review",
                "phase": "report",
                "target_id": "module.a",
                "context_id": self.identity("module.a"),
                "change_id": "t1",
            },
            {key: value for key, value in entry["source"].items() if key != "head"},
        )
        log = subprocess.run(
            ["git", "log", "-1", "--format=%s%n%b"],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        self.assertIn(f"Concorde-Issue: {item['issue']}", log)
        # The review changes no file of the workspace.
        self.assertEqual("", self.status())
        self.assertIn("issue", self.kinds(envelope))
        self.assertEqual(1, len(envelope["worker_runs"]))
        brief = self.brief(envelope["worker_runs"][0])
        self.assertIn("You are a Concorde Spec reviewer", brief)
        self.assertIn("Your role: reviewer.", brief)
        self.assertIn("Reviewed Module: `module.a`", brief)
        self.assertIn("every blocking finding you can establish in this one run", brief)
        self.assertIn("No earlier review left an open Issue for this Module.", brief)
        self.assertIn("## The Protocol's criteria", brief)
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
                        "decision-needed",
                        dimension="readability",
                        problem="Usage never shows a normal path.",
                    ),
                )
            }
        )
        self.assertEqual((0, "ok"), (exit_status, envelope["status"]), envelope)
        output = envelope["output"]
        self.assertEqual("changes_required", output["verdict"])
        # The verdict reaches a workflow as a review note (the step output convention).
        [note] = output["workflow"]["notes"]
        self.assertEqual(
            ("review", "changes_required"), (note["kind"], note["data"]["verdict"])
        )
        findings = output["modules"][0]["findings"]
        self.assertEqual(
            ["specs/a/obligations.md", "specs/a/module.md"],
            [item["path"] for item in findings],
        )
        self.assertEqual(
            ["obvious-fix", "decision-needed"], [item["tier"] for item in findings]
        )
        self.assertEqual("req.a.two", findings[0]["anchor"])
        issues = self.issues()
        for item in findings:
            self.assertTrue(
                item["dimension"] and item["evidence"] and item["suggestion"]
            )
            report = issues[item["issue"]]["reports"][-1]["report"]
            self.assertEqual(
                (item["tier"], item["severity"], item["title"], item["impact"]),
                (report["tier"], report["severity"], report["title"], report["impact"]),
            )
            self.assertIn(item["problem"], report["description"])
            self.assertIn(item["evidence"], report["basis"])
        self.assertEqual(
            [
                {
                    "path": "specs/a/obligations.md",
                    "description": "req.a.two, cited by the obligations finding",
                }
            ],
            issues[findings[0]["issue"]]["reports"][-1]["report"]["evidence"],
        )
        # Worker claims stay out of the host's summary and evidence.
        host_text = json.dumps(envelope["host_evidence"]) + envelope["summary"]
        self.assertNotIn("normal path", host_text)
        self.assertIn("2 blocking Issue(s) stand", envelope["summary"])

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
        self.assertEqual("obvious-fix", item["tier"])
        self.assertEqual(
            {"status": "disputed", "reason": "The quoted text is not in the Spec."},
            item["check"],
        )
        self.assertIsNone(item["issue"])
        self.assertEqual({}, self.issues())
        self.assertEqual(2, len(envelope["worker_runs"]))
        brief = self.brief(envelope["worker_runs"][1])
        self.assertIn("Your role: checker.", brief)
        self.assertIn("Finding 1:", brief)
        checker_grant = self.record(envelope["worker_runs"][1])
        self.assertEqual(self.identity("module.a"), checker_grant["context_identity"])

    def resolved(self, *items):
        return [{"issue": issue, "reason": reason} for issue, reason in items]

    @verifies("scenario.spec-review.earlier-issues")
    def test_a_repeated_review_builds_on_the_earlier_issues(self):
        first = self.earlier("obvious-fix", "first")
        second = self.earlier("decision-needed", "second")
        third = self.earlier("suggestion", "third")
        fourth = self.earlier("obvious-fix", "fourth", operation="issues")
        unknown = "I-" + "9" * 32
        before = self.issues()
        updated = finding(
            "specs/a/module.md", earlier=second, problem="Changed problem."
        )
        status, envelope = self.review(
            {
                "reviewer module.a": [
                    {
                        "result": {
                            "output": {
                                "findings": [
                                    updated,
                                    finding("specs/a/module.md", "suggestion"),
                                ],
                                "resolved": self.resolved(
                                    (third, "The Usage was rewritten."),
                                    (unknown, "No such Issue."),
                                ),
                            }
                        }
                    }
                ]
            }
        )
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        (module,) = envelope["output"]["modules"]
        # The first Issue was not mentioned: it is carried, still open and blocking.
        self.assertEqual("changes_required", module["outcome"])
        changed, new = module["findings"]
        self.assertEqual((second, second), (changed["earlier"], changed["issue"]))
        self.assertNotIn("earlier", new)
        self.assertNotIn(new["issue"], before)
        summary = module["earlier_issues"]
        self.assertEqual(
            [
                {
                    "issue": first,
                    "severity": "medium",
                    "tier": "obvious-fix",
                    "title": "first",
                }
            ],
            summary["carried"],
        )
        self.assertEqual(
            self.resolved((third, "The Usage was rewritten.")), summary["resolved"]
        )
        self.assertEqual([unknown], [item["issue"] for item in summary["ignored"]])
        after = self.issues()
        self.assertEqual(2, len(after[second]["reports"]))
        self.assertIn(
            "Changed problem.", after[second]["reports"][-1]["report"]["description"]
        )
        for unchanged in (first, third, fourth):
            self.assertEqual(before[unchanged], after[unchanged])
        self.assertEqual("open", after[third]["status"])
        brief = self.brief(envelope["worker_runs"][0])
        self.assertIn("Earlier problem first.", brief)
        self.assertNotIn("Earlier problem fourth.", brief)
        self.assertNotIn("r-earlier", brief)

    @verifies("scenario.spec-review.blank-earlier")
    def test_a_blank_earlier_names_no_earlier_issue(self):
        unknown = "I-" + "9" * 32
        status, envelope = self.review(
            {
                "reviewer module.a": reviewer(
                    finding("specs/a/module.md", earlier=""),
                    finding("specs/a/module.md", "suggestion", earlier="  "),
                    finding("specs/a/module.md", "suggestion", earlier=unknown),
                )
            }
        )
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        (module,) = envelope["output"]["modules"]
        self.assertEqual(3, len(module["findings"]))
        for item in module["findings"]:
            self.assertNotIn("earlier", item)
            self.assertIsNotNone(item["issue"])
        self.assertEqual(
            [unknown], [item["issue"] for item in module["earlier_issues"]["ignored"]]
        )
        self.assertEqual(3, len(self.issues()))

    @verifies("scenario.spec-review.finding-path")
    def test_a_finding_whose_path_does_not_hold_is_rejected_alone(self):
        status, envelope = self.review(
            {
                "reviewer module.a": reviewer(
                    finding("../elsewhere/module.md", earlier="I-" + "1" * 32),
                    finding("specs/a/module.md"),
                )
            }
        )
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        (module,) = envelope["output"]["modules"]
        [rejected] = module["rejected"]
        self.assertEqual("../elsewhere/module.md", rejected["finding"]["path"])
        self.assertNotIn("earlier", rejected["finding"])
        self.assertIn("not a path in the task worktree", rejected["reason"])
        self.assertIn("invalid-output", self.kinds(envelope))
        [reported] = module["findings"]
        self.assertEqual([reported["issue"]], list(self.issues()))
        self.assertEqual("changes_required", module["outcome"])

    @verifies("scenario.spec-review.citation-resume")
    def test_a_reviewer_is_resumed_once_to_correct_a_path(self):
        status, envelope = self.review(
            {
                "reviewer module.a": reviewer(finding("../elsewhere/module.md"))
                + reviewer(finding("specs/a/module.md"))
            }
        )
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        (module,) = envelope["output"]["modules"]
        self.assertEqual([], module["rejected"])
        self.assertEqual(["specs/a/module.md"], [f["path"] for f in module["findings"]])
        record = self.record(envelope["worker_runs"][0])
        self.assertEqual(["initial", "repair"], [r["prompt"] for r in record["rounds"]])
        self.assertIn("'../elsewhere/module.md'", record["rounds"][0]["validation"])

    @verifies("scenario.spec-review.without-issues")
    def test_without_the_issues_part_the_findings_stay_in_the_result(self):
        with without_issues():
            status, envelope = self.review(
                {"reviewer module.a": reviewer(finding("specs/a/module.md"))}
            )
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        (module,) = envelope["output"]["modules"]
        self.assertEqual("changes_required", module["outcome"])
        self.assertEqual([None], [item["issue"] for item in module["findings"]])
        self.assertIsNone(module["earlier_issues"])
        self.assertIn(NOT_RECORDED, envelope["summary"])
        self.assertEqual({}, self.issues())
        brief = self.brief(envelope["worker_runs"][0])
        self.assertIn("the issues part is not installed", brief)

    @verifies("scenario.spec-review.last-blocker-resolved")
    def test_resolving_every_earlier_blocking_issue_accepts_the_module(self):
        first = self.earlier("obvious-fix", "first")
        _, envelope = self.review(
            {
                "reviewer module.a": [
                    {
                        "result": {
                            "output": {
                                "findings": [],
                                "resolved": self.resolved((first, "Split.")),
                            }
                        }
                    }
                ]
            }
        )
        self.assertEqual("accepted", envelope["output"]["verdict"], envelope)
        (module,) = envelope["output"]["modules"]
        self.assertEqual("accepted", module["outcome"])
        self.assertEqual(
            self.resolved((first, "Split.")), module["earlier_issues"]["resolved"]
        )
        self.assertEqual("open", self.issues()[first]["status"])

    @verifies("scenario.spec-review.issues-refused")
    def test_a_refused_report_stops_the_module_and_is_no_issue(self):
        standing = self.earlier("obvious-fix", "standing")
        before = self.issues()
        goal = "Review the Specs.\nFAKE-PLANS: " + json.dumps(
            {
                "reviewer module.a": reviewer(
                    finding("specs/a/module.md", earlier=standing),
                    finding("specs/a/obligations.md"),
                )
            }
        )
        self.project.open_task("t1", modules=("module.a",), goal=goal)
        self.worktree = self.project.worktree("t1")
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
        status, envelope = self.project.run(
            "spec_review", "--task", "t1", "--modules", "module.a"
        )
        self.assertEqual((1, "failed"), (status, envelope["status"]), envelope)
        self.assertIsNotNone(envelope["output"], envelope["error"])
        (module,) = envelope["output"]["modules"]
        self.assertEqual("incomplete", module["outcome"])
        self.assertEqual([None, None], [item["issue"] for item in module["findings"]])
        # Nothing was appended to the earlier Issue the first finding named: no finding claims
        # it as `earlier`, and it is carried.
        for item in module["findings"]:
            self.assertNotIn("earlier", item)
        self.assertEqual(
            [standing], [item["issue"] for item in module["earlier_issues"]["carried"]]
        )
        self.assertEqual(before, self.issues())
        [cause] = envelope["error"]["causes"]
        self.assertEqual("issues_unreported", cause["code"])
        [store] = cause["causes"]
        self.assertEqual("merge_incomplete", store["code"])
        self.assertEqual("environment", store["unhandled"]["reason"])

    @verifies("scenario.spec-review.unbound-reports")
    def test_an_unbound_review_reports_to_the_projects_issues(self):
        # An unbound run has no goal to carry the fake reviewer's plans: the wrapper gives them.
        plans = json.dumps(
            {"reviewer module.a": reviewer(finding("specs/a/module.md"))}
        )
        wrapper = self.project.base / "claude-unbound"
        wrapper.write_text(
            f"#!/bin/sh\nFAKE_REVIEW_PLANS='{plans}' "
            f'exec "{sys.executable}" "{FAKE_REVIEWER}" "$@"\n'
        )
        wrapper.chmod(0o755)
        self.project.fake = wrapper
        before = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        status, envelope = self.project.run("spec_review", "--modules", "module.a")
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        (item,) = envelope["output"]["modules"][0]["findings"]
        record = self.issues()[item["issue"]]
        source = record["reports"][0]["source"]
        self.assertEqual(
            (envelope["run_id"], "spec_review", None, before),
            (
                source["invocation_id"],
                source["operation"],
                source["change_id"],
                source["head"],
            ),
        )
        changed = subprocess.run(
            ["git", "diff", "--name-only", before, "HEAD"],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.split()
        self.assertEqual([record["id"]], [Path(path).stem for path in changed])
        self.assertEqual(
            "",
            subprocess.run(
                ["git", "status", "--porcelain", "--untracked-files=no"],
                cwd=self.root,
                capture_output=True,
                text=True,
                check=True,
            ).stdout,
        )

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
                    finding("specs/a/module.md", "suggestion"),
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
            ("module.b", "suggestion"), (about_b["module"], about_b["tier"])
        )
        owner = self.issues()[about_b["issue"]]["reports"][-1]["report"][
            "owner_target_id"
        ]
        self.assertEqual("module.b", owner)
        self.assertIn("finding-scope", self.kinds(envelope))
        self.assertEqual(2, len(envelope["worker_runs"]))
        for run_id, module in zip(envelope["worker_runs"], ("module.a", "module.b")):
            record = self.record(run_id)
            frozen = json.loads(
                (Path(record["run_directory"]) / "grant.json").read_text()
            )
            node = json.loads(
                (Path(record["run_directory"]) / "trace.json").read_text()
            )
            self.assertEqual(
                ([module], "review-spec"),
                (node["metadata"]["modules"], frozen["task_type"]),
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
        # A Mermaid block is a structural error (CHK.view.marked).
        entry.write_text(entry.read_text() + "\n```mermaid\ngraph TD\n  a --> b\n```\n")
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
                "rejected": [],
                "earlier_issues": None,
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


if __name__ == "__main__":
    unittest.main()
