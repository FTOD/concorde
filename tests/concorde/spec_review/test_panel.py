"""The ``spec_panel`` Operation: the host's accounting, and whole panels with fake workers."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from concorde.worker_harness.claude_backend import ClaudeBackend
from concorde.worker_harness.runs import read_record
from concorde.issues.store import list_issues, read_issue, report_issue
from concorde.spec.grants import grant
from concorde.spec.repository import SpecRepository
from concorde.spec.schema import validate
from concorde.spec.verification import verifies
from concorde.method.review_issues import NOT_RECORDED
from concorde.method.spec_review.panel import PAYLOAD_SCHEMA, account
from tests.concorde.support.operation_project import (
    OperationProject,
    commit,
    link_at,
    worker_error,
)
from tests.concorde.support.paths import REPOSITORY_ROOT

FAKE_PANELIST = Path(__file__).with_name("fake_panelist.py")

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


def earlier_report(module, tier, title, operation="spec_panel", root=None):
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


def finding(path="specs/a/module.md", tier="obvious-fix", **extra):
    return {
        "module": "module.a",
        "path": path,
        "dimension": "obligations",
        "severity": "high",
        "tier": tier,
        "title": f"A {tier} problem",
        "problem": f"A {tier} problem in {path}.",
        "impact": "A reader could not rely on it.",
        "evidence": "Quoted text.",
        "suggestion": "Rewrite it.",
        **extra,
    }


def architectural(path="specs/a/module.md", tier="decision-needed", **extra):
    return finding(
        path,
        tier,
        dimension="interfaces",
        problem="A relies on a promise B does not make.",
        related=["module.b"],
        **extra,
    )


def merged(*sources, note="Verified in the Spec.", **extra):
    return {**finding(**extra), "sources": list(sources), "note": note}


def worker(**output):
    return [{"result": {"output": output}}]


class AccountingTests(unittest.TestCase):
    """The host checks that the chair accounted for every reviewer finding exactly once."""

    def test_every_label_once_is_complete(self):
        report = {
            "findings": [merged("r1.1", "r2.1")],
            "rejected": [{"source": "r2.2", "reason": "Not in the Spec."}],
        }
        self.assertEqual([], account(["r1.1", "r2.1", "r2.2"], report))

    def test_missing_repeated_and_unknown_labels_are_named(self):
        report = {
            "findings": [merged("r1.1"), merged("r1.1", "r9.9")],
            "rejected": [],
        }
        self.assertEqual(
            [
                "r2.1 is not accounted for",
                "r1.1 is accounted for 2 times",
                "r9.9 names no worker finding",
            ],
            account(["r1.1", "r2.1"], report),
        )


class SpecPanelTests(unittest.TestCase):
    def setUp(self):
        self.project = OperationProject(self)
        self.root = self.project.root
        wrapper = self.project.base / "claude-panelist"
        wrapper.write_text(
            f'#!/bin/sh\nexec "{sys.executable}" "{FAKE_PANELIST}" "$@"\n'
        )
        wrapper.chmod(0o755)
        self.project.fake = wrapper

    def panel(self, plans, *extra, modules=("module.a",), architects="0"):
        goal = "Review the Specs.\nFAKE-PLANS: " + json.dumps(plans)
        self.project.open_task("t1", modules=modules, goal=goal)
        self.worktree = self.project.worktree("t1")
        return self.project.run(
            "spec_panel",
            "--task",
            "t1",
            "--modules",
            ",".join(modules),
            "--architects",
            architects,
            *extra,
        )

    def issues(self):
        return {
            row["id"]: read_issue(self.root, row["id"])[0]
            for row in list_issues(self.root)
        }

    def identity(self, task_type, module="module.a"):
        return grant(
            SpecRepository(self.worktree, REPOSITORY_ROOT), [module], task_type
        ).value["context_identity"]

    def record(self, run_id):
        """The worker run's record, rebuilt from its trace node below the primary's records."""
        return read_record(self.root / ".concorde", run_id)

    def briefs(self, envelope, role):
        """The first prompts, the briefs their run directories keep, of the workers of
        ``role``."""
        found = []
        for run_id in envelope["worker_runs"]:
            record = self.record(run_id)
            if record["worker"].rstrip("0123456789") == role:
                found.append((Path(record["run_directory"]) / "brief.md").read_text())
        return found

    def status(self):
        return subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=self.worktree,
            capture_output=True,
            text=True,
            check=True,
        ).stdout

    @verifies("scenario.spec-review.panel-merged")
    def test_the_chair_merges_independent_reviews_into_one_report(self):
        exit_status, envelope = self.panel(
            {
                "reviewer module.a 1": worker(
                    findings=[finding(problem="Two obligations.")]
                ),
                "reviewer module.a 2": worker(
                    findings=[
                        finding(problem="The requirement holds two duties."),
                        finding(tier="suggestion", problem="Wording."),
                    ]
                ),
                "chair module.a 1": worker(
                    findings=[
                        merged(
                            "r1.1",
                            "r2.1",
                            tier="obvious-fix",
                            problem="The requirement holds two obligations.",
                            note="Both quote the same sentence; it has two SHALLs.",
                        )
                    ],
                    rejected=[
                        {"source": "r2.2", "reason": "The next sentence says it."}
                    ],
                ),
            },
            "--reviewers",
            "2",
        )
        self.assertEqual((0, "ok"), (exit_status, envelope["status"]), envelope)
        output = envelope["output"]
        validate(output, PAYLOAD_SCHEMA)
        self.assertEqual("changes_required", output["verdict"])
        [note] = output["workflow"]["notes"]
        self.assertEqual(
            ("review", "changes_required"), (note["kind"], note["data"]["verdict"])
        )
        (module,) = output["modules"]
        self.assertEqual(self.identity("review-spec"), module["context_identity"])
        self.assertIsNone(module["architecture_identity"])
        self.assertEqual(
            [
                ("reviewer1", 1, "ok", ["r1.1"]),
                ("reviewer2", 2, "ok", ["r2.1", "r2.2"]),
            ],
            [
                (
                    r["worker"],
                    r["seat"],
                    r["status"],
                    [f["label"] for f in r["findings"]],
                )
                for r in module["reviews"]
            ],
        )
        (report,) = module["findings"]
        self.assertEqual(
            (["r1.1", "r2.1"], 2, "obvious-fix"),
            (report["sources"], report["workers"], report["tier"]),
        )
        self.assertEqual(["r2.2"], [item["source"] for item in module["rejected"]])
        self.assertIn(
            "1 blocking finding(s) and 0 suggestion(s) merged from 3",
            envelope["summary"],
        )
        # The merged finding is one Issue; the rejection is recorded nowhere.
        issues = self.issues()
        self.assertEqual([report["issue"]], list(issues))
        (entry,) = issues[report["issue"]]["reports"]
        self.assertEqual(
            ("obvious-fix", "high"),
            (entry["report"]["tier"], entry["report"]["severity"]),
        )
        self.assertIn("r1.1, r2.1", entry["report"]["basis"])
        self.assertEqual("spec_panel", entry["source"]["operation"])
        self.assertEqual(3, len(envelope["worker_runs"]))
        reviewers = self.briefs(envelope, "reviewer")
        self.assertEqual(2, len(reviewers))
        self.assertTrue(all("Your role: reviewer." in brief for brief in reviewers))
        self.assertEqual(
            {"Panel seat: 1 of 2.", "Panel seat: 2 of 2."},
            {
                line
                for brief in reviewers
                for line in brief.splitlines()
                if "Panel seat" in line
            },
        )
        (chair,) = self.briefs(envelope, "chair")
        self.assertIn("### Reviewer 2", chair)
        self.assertIn('"label": "r2.2"', chair)
        accounting = [
            i for i in envelope["host_evidence"] if i["kind"] == "panel-accounting"
        ]
        self.assertEqual(
            [
                (
                    "module.a chair attempt 1",
                    "every worker finding accounted for once",
                )
            ],
            [(i["ref"], i["detail"]) for i in accounting],
        )
        graph = next(i for i in envelope["host_evidence"] if i["kind"] == "graph")
        self.assertIn("chair", Path(graph["ref"]).read_text())
        # A panel changes no file of the workspace.
        self.assertEqual("", self.status())

    @verifies("scenario.spec-review.panel-worker-models")
    def test_each_reviewer_runs_on_the_model_configured_for_its_worker_id(self):
        config = {
            "schema_version": 2,
            "enabled_models": {
                "claude-sonnet-5": {},
                "claude-opus-5-5": {},
                "haiku": {},
            },
            "default": {"backend": "claude"},
            "operations": {
                "spec_panel": {
                    "default": {"model": "claude-sonnet-5", "reasoning": "medium"},
                    "workers": {
                        "reviewer2": {"model": "claude-opus-5-5"},
                        "architect1": {"model": "haiku", "reasoning": "low"},
                        "chair": {"model": "claude-opus-5-5", "reasoning": "high"},
                    },
                }
            },
        }
        # The worker configuration is tracked: the task opened by the panel carries it.
        (self.root / ".concorde/workers.json").write_text(json.dumps(config))
        commit(self.root, "choose the panel's models")
        # The command line each worker was launched with, by its worker id: the worker's runtime
        # directory, where the fake notes its arguments, is removed when the worker ends.
        launched = {}
        original = ClaudeBackend.command

        def spy(backend, request, *args, **kwargs):
            argv = original(backend, request, *args, **kwargs)
            launched[request.worker] = argv
            return argv

        with patch.object(ClaudeBackend, "command", spy):
            exit_status, envelope = self.panel(
                {
                    "reviewer module.a 1": worker(findings=[]),
                    "reviewer module.a 2": worker(findings=[]),
                    "architect module.a 1": worker(findings=[]),
                    "chair module.a 1": worker(findings=[], rejected=[]),
                },
                "--reviewers",
                "2",
                architects="1",
            )
        self.assertEqual((0, "ok"), (exit_status, envelope["status"]), envelope)
        chosen = {}
        for run_id in envelope["worker_runs"]:
            record = self.record(run_id)
            argv = launched[record["worker"]]
            chosen[record["worker"]] = (
                argv[argv.index("--model") + 1],
                argv[argv.index("--effort") + 1],
            )
            # The run record keeps the model's local id and the level it was launched with.
            self.assertEqual(
                chosen[record["worker"]], (record["local_model"], record["reasoning"])
            )
        self.assertEqual(
            {
                "reviewer1": ("claude-sonnet-5", "medium"),
                "reviewer2": ("claude-opus-5-5", "medium"),
                "architect1": ("haiku", "low"),
                "chair": ("claude-opus-5-5", "high"),
            },
            chosen,
        )
        models = [
            item["detail"]
            for item in envelope["host_evidence"]
            if item["kind"] == "worker-model"
        ]
        self.assertTrue(
            any(
                detail.startswith("module.a reviewer2: reviewer2 (backend from")
                and "claude-opus-5-5" in detail
                for detail in models
            ),
            models,
        )

    @verifies("scenario.spec-review.panel-accounting")
    def test_a_report_that_drops_a_finding_goes_back_to_the_chair_once(self):
        plans = {
            "reviewer module.a 1": worker(findings=[finding(problem="A.")]),
            "reviewer module.a 2": worker(findings=[finding(problem="B.")]),
            "chair module.a 1": worker(findings=[merged("r1.1")], rejected=[]),
            "chair module.a 2": worker(
                findings=[merged("r1.1")],
                rejected=[{"source": "r2.1", "reason": "Not in the Spec."}],
            ),
        }
        exit_status, envelope = self.panel(plans, "--reviewers", "2")
        self.assertEqual((0, "ok"), (exit_status, envelope["status"]), envelope)
        (second,) = [
            brief
            for brief in self.briefs(envelope, "chair")
            if "Chair attempt: 2" in brief
        ]
        self.assertIn("- r2.1 is not accounted for", second)
        self.assertIn("Your previous report", second)
        self.assertEqual(
            ["r2.1"],
            [i["source"] for i in envelope["output"]["modules"][0]["rejected"]],
        )

    def test_a_chair_may_leave_out_its_optional_lists(self):
        # The chair's report requires only `findings`: an omitted `rejected` or `resolved` is
        # an empty one.
        plans = {
            "reviewer module.a 1": worker(findings=[finding(problem="A.")]),
            "reviewer module.a 2": worker(findings=[]),
            "chair module.a 1": worker(findings=[merged("r1.1")]),
        }
        exit_status, envelope = self.panel(plans, "--reviewers", "2")
        self.assertEqual((0, "ok"), (exit_status, envelope["status"]), envelope)
        (module,) = envelope["output"]["modules"]
        self.assertEqual("changes_required", module["outcome"])
        self.assertEqual([], module["rejected"])
        self.assertEqual(["r1.1"], module["findings"][0]["sources"])
        self.assertEqual(
            {"carried": [], "resolved": [], "ignored": []}, module["earlier_issues"]
        )

    def test_a_chair_that_never_accounts_for_everything_fails_the_module(self):
        plans = {
            "reviewer module.a 1": worker(findings=[finding()]),
            "reviewer module.a 2": worker(findings=[]),
            "chair module.a 1": worker(findings=[], rejected=[]),
            "chair module.a 2": worker(findings=[], rejected=[]),
        }
        exit_status, envelope = self.panel(plans, "--reviewers", "2")
        self.assertEqual((1, "failed"), (exit_status, envelope["status"]))
        self.assertEqual("incomplete", envelope["output"]["verdict"])
        error = envelope["error"]
        self.assertEqual("panel_incomplete", error["code"])
        (cause,) = error["causes"]
        self.assertEqual("report_unaccounted", cause["code"])
        self.assertIn("r1.1 is not accounted for", cause["detail"])
        # The reviews still travel in the payload.
        self.assertEqual(
            1, len(envelope["output"]["modules"][0]["reviews"][0]["findings"])
        )

    @verifies("scenario.spec-review.panel-without-issues")
    def test_without_issues_the_panel_keeps_its_settled_findings(self):
        plans = {
            "reviewer module.a 1": worker(findings=[finding(earlier="")]),
            "reviewer module.a 2": worker(findings=[]),
            "chair module.a 1": worker(
                findings=[merged("r1.1", earlier="not an Issue")], rejected=[]
            ),
        }
        with without_issues():
            exit_status, envelope = self.panel(plans, "--reviewers", "2")
        self.assertEqual((0, "ok"), (exit_status, envelope["status"]), envelope)
        (module,) = envelope["output"]["modules"]
        (reported,) = module["findings"]
        self.assertNotIn("earlier", reported)
        self.assertIsNone(reported["issue"])
        self.assertNotIn("earlier", module["reviews"][0]["findings"][0])
        self.assertEqual("changes_required", module["outcome"])

    @verifies("scenario.spec-review.panel-without-issues")
    def test_a_stopped_panel_drops_the_chairs_earlier_claims(self):
        plans = {
            "reviewer module.a 1": worker(findings=[finding()]),
            "reviewer module.a 2": worker(findings=[finding(problem="B.")]),
            "chair module.a 1": worker(
                findings=[merged("r1.1", earlier="I-" + "1" * 32)], rejected=[]
            ),
            "chair module.a 2": worker(
                findings=[merged("r1.1", earlier="I-" + "1" * 32)], rejected=[]
            ),
        }
        exit_status, envelope = self.panel(plans, "--reviewers", "2")
        self.assertEqual((1, "failed"), (exit_status, envelope["status"]), envelope)
        (module,) = envelope["output"]["modules"]
        self.assertEqual("incomplete", module["outcome"])
        self.assertEqual([None], [item["issue"] for item in module["findings"]])
        self.assertNotIn("earlier", module["findings"][0])

    @verifies("scenario.spec-review.finding-path")
    def test_a_panel_rejects_a_finding_whose_path_does_not_hold_alone(self):
        plans = {
            "reviewer module.a 1": worker(
                findings=[
                    finding("/etc/elsewhere.md", earlier="I-" + "1" * 32),
                    finding(problem="A."),
                ]
            ),
            "reviewer module.a 2": worker(findings=[finding(problem="B.")]),
            "chair module.a 1": worker(
                findings=[
                    merged("r1.1"),
                    merged("r2.1", path="../outside.md", tier="suggestion"),
                ],
                rejected=[],
            ),
        }
        exit_status, envelope = self.panel(plans, "--reviewers", "2")
        self.assertEqual((0, "ok"), (exit_status, envelope["status"]), envelope)
        (module,) = envelope["output"]["modules"]
        first = module["reviews"][0]
        self.assertEqual(["r1.1"], [item["label"] for item in first["findings"]])
        [unusable] = first["rejected"]
        self.assertEqual("/etc/elsewhere.md", unusable["finding"]["path"])
        self.assertNotIn("earlier", unusable["finding"])
        self.assertIn("not a path in the task worktree", unusable["reason"])
        self.assertIn("invalid-output", self.kinds(envelope))
        self.assertEqual(["r1.1"], module["findings"][0]["sources"])
        [rejection] = module["rejected"]
        self.assertEqual("r2.1", rejection["source"])
        self.assertIn("the host rejected the chair's finding", rejection["reason"])
        self.assertEqual(1, len(self.issues()))
        self.assertEqual("changes_required", module["outcome"])

    @verifies("scenario.spec-review.panel-short")
    def test_a_blocked_reviewer_stops_the_panel_before_the_chair(self):
        exit_status, envelope = self.panel(
            {
                "reviewer module.a 1": worker(findings=[finding()]),
                "architect module.a 1": worker(findings=[architectural()]),
                "reviewer module.a 2": [
                    {
                        "result": {
                            "status": "blocked",
                            "output": {"findings": []},
                            "error": worker_error(
                                "The entry of module.c is needed.",
                                code="context_missing",
                                reason="permission",
                            ),
                        }
                    }
                ],
            },
            "--reviewers",
            "2",
            architects="1",
        )
        self.assertEqual((1, "blocked"), (exit_status, envelope["status"]))
        output = envelope["output"]
        self.assertEqual("incomplete", output["verdict"])
        self.assertEqual([], self.briefs(envelope, "chair"))
        self.assertEqual({}, self.issues())
        self.assertEqual(
            [("reviewer1", "ok"), ("reviewer2", "blocked"), ("architect1", "ok")],
            [(r["worker"], r["status"]) for r in output["modules"][0]["reviews"]],
        )
        error = envelope["error"]
        self.assertEqual("panel_incomplete", error["code"])
        (short,) = error["causes"]
        self.assertEqual("panel_short", short["code"])
        (reviewer,) = short["causes"]
        self.assertIn("panel of module.a reviewer2", reviewer["actor"])
        worker_link = link_at(error, "worker")
        self.assertEqual("The entry of module.c is needed.", worker_link["detail"])

    def test_a_blocking_finding_outside_the_module_is_a_suggestion(self):
        exit_status, envelope = self.panel(
            {
                "reviewer module.a 1": worker(findings=[finding("specs/b/module.md")]),
                "reviewer module.a 2": worker(findings=[]),
                "chair module.a 1": worker(
                    findings=[merged("r1.1", path="specs/b/module.md")], rejected=[]
                ),
            },
            "--reviewers",
            "2",
        )
        self.assertEqual((0, "ok"), (exit_status, envelope["status"]), envelope)
        (item,) = envelope["output"]["modules"][0]["findings"]
        self.assertEqual(("suggestion", "module.b"), (item["tier"], item["module"]))
        self.assertEqual("accepted", envelope["output"]["verdict"])
        owner = self.issues()[item["issue"]]["reports"][0]["report"]["owner_target_id"]
        self.assertEqual("module.b", owner)

    @verifies("scenario.spec-review.panel-architects")
    def test_architects_judge_the_module_among_all_the_modules(self):
        exit_status, envelope = self.panel(
            {
                "reviewer module.a 1": worker(findings=[finding()]),
                "reviewer module.a 2": worker(findings=[]),
                "architect module.a 1": worker(findings=[architectural()]),
                "architect module.a 2": worker(
                    findings=[finding(dimension="responsibilities")]
                ),
                "chair module.a 1": worker(
                    findings=[
                        merged(
                            "a1.1",
                            tier="decision-needed",
                            dimension="interfaces",
                            problem="A relies on a promise B does not make.",
                            related=["module.b"],
                            note="B's entry promises nothing of the kind.",
                        ),
                        merged("r1.1", "a2.1"),
                    ],
                    rejected=[],
                ),
            },
            "--reviewers",
            "2",
            architects="2",
        )
        self.assertEqual((0, "ok"), (exit_status, envelope["status"]), envelope)
        (module,) = envelope["output"]["modules"]
        self.assertEqual("changes_required", module["outcome"])
        self.assertEqual(self.identity("review-spec"), module["context_identity"])
        self.assertEqual(
            self.identity("review-architecture"), module["architecture_identity"]
        )
        grants = {}
        for run_id in envelope["worker_runs"]:
            record = self.record(run_id)
            frozen = json.loads(
                (Path(record["run_directory"]) / "grant.json").read_text()
            )
            grants[record["worker"]] = frozen["task_type"]
            readable = {
                entry["path"] for entry in frozen["entries"] if entry["level"] == "ro"
            }
            if frozen["task_type"] == "review-architecture":
                self.assertIn("specs/b/module.md", readable)
        self.assertEqual(
            {
                "reviewer1": "review-spec",
                "reviewer2": "review-spec",
                "architect1": "review-architecture",
                "architect2": "review-architecture",
                "chair": "review-architecture",
            },
            grants,
        )
        (chair,) = self.briefs(envelope, "chair")
        self.assertIn("### Architect 1", chair)
        self.assertIn('"label": "a1.1"', chair)
        (architect, _) = self.briefs(envelope, "architect")
        self.assertIn("Your role: architect.", architect)
        report, mixed = module["findings"]
        self.assertEqual(
            (["a1.1"], ["module.b"]), (report["sources"], report["related"])
        )
        entry = self.issues()[report["issue"]]["reports"][0]
        self.assertEqual("module.a", entry["report"]["owner_target_id"])
        self.assertIn("module.b", entry["report"]["description"])
        self.assertEqual(module["architecture_identity"], entry["source"]["context_id"])
        # Only the architects' finding is of the architecture phase, which project_review's
        # architecture review offers; a finding a reviewer also made stays a report.
        self.assertEqual(
            ("architecture", "architecture/module.a/1"),
            (entry["source"]["phase"], entry["report"]["report_key"]),
        )
        other = self.issues()[mixed["issue"]]["reports"][0]
        self.assertEqual(
            ("report", "module.a/2"),
            (other["source"]["phase"], other["report"]["report_key"]),
        )

    @verifies("scenario.spec-review.panel-no-architects")
    def test_a_panel_without_architects_reads_only_the_modules_context(self):
        exit_status, envelope = self.panel(
            {
                "reviewer module.a 1": worker(findings=[]),
                "reviewer module.a 2": worker(findings=[]),
                "chair module.a 1": worker(findings=[], rejected=[]),
            },
            "--reviewers",
            "2",
        )
        self.assertEqual((0, "ok"), (exit_status, envelope["status"]), envelope)
        self.assertEqual([], self.briefs(envelope, "architect"))
        (chair_run,) = [
            run_id
            for run_id in envelope["worker_runs"]
            if self.record(run_id)["worker"] == "chair"
        ]
        record = self.record(chair_run)
        frozen = json.loads((Path(record["run_directory"]) / "grant.json").read_text())
        self.assertEqual("review-spec", frozen["task_type"])
        self.assertIsNone(envelope["output"]["modules"][0]["architecture_identity"])

    def kinds(self, envelope):
        return [item["kind"] for item in envelope["host_evidence"]]

    def earlier(self, tier, title, module="module.a", operation="spec_panel"):
        return earlier_report(module, tier, title, operation, root=self.root)

    def resolved(self, *items):
        return [{"issue": issue, "reason": reason} for issue, reason in items]

    @verifies("scenario.spec-review.accepted")
    def test_suggestions_only_are_accepted_and_recorded(self):
        suggestion = {"tier": "suggestion", "dimension": "readability"}
        exit_status, envelope = self.panel(
            {
                "reviewer module.a 1": worker(findings=[finding(**suggestion)]),
                "reviewer module.a 2": worker(
                    findings=[finding(**suggestion, problem="The same wording.")]
                ),
                "chair module.a 1": worker(
                    findings=[merged("r1.1", "r2.1", **suggestion)]
                ),
            },
            "--reviewers",
            "2",
        )
        self.assertEqual((0, "ok"), (exit_status, envelope["status"]), envelope)
        output = envelope["output"]
        validate(output, PAYLOAD_SCHEMA)
        self.assertEqual("accepted", output["verdict"])
        (module,) = output["modules"]
        self.assertEqual("accepted", module["outcome"])
        self.assertEqual(self.identity("review-spec"), module["context_identity"])
        (item,) = module["findings"]
        self.assertEqual("suggestion", item["tier"])
        self.assertEqual(
            {"carried": [], "resolved": [], "ignored": []}, module["earlier_issues"]
        )
        # The suggestion is a new Issue of the project, committed on the primary branch.
        issues = self.issues()
        self.assertEqual([item["issue"]], list(issues))
        (entry,) = issues[item["issue"]]["reports"]
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
                "operation": "spec_panel",
                "phase": "report",
                "target_id": "module.a",
                "context_id": self.identity("review-spec"),
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
        # The panel changes no file of the workspace.
        self.assertEqual("", self.status())
        self.assertIn("issue", self.kinds(envelope))
        for brief in self.briefs(envelope, "reviewer"):
            self.assertIn("You are a Concorde Spec reviewer", brief)
            self.assertIn("Your role: reviewer.", brief)
            self.assertIn("Reviewed Module: `module.a`", brief)
            self.assertIn(
                "every blocking finding you can establish in this one run", brief
            )
            self.assertIn(
                "No earlier review left an open Issue for this Module.", brief
            )
            self.assertIn("## The Protocol's criteria", brief)

    @verifies("scenario.spec-review.changes-required")
    def test_every_blocking_finding_is_returned_in_one_result(self):
        two = {"path": "specs/a/obligations.md", "anchor": "req.a.two", "line": 3}
        # The second finding cites an absolute path, as a worker reading absolute paths would.
        usage = {
            "path": "@WORKTREE@/specs/a/module.md",
            "tier": "decision-needed",
            "dimension": "readability",
            "problem": "Usage never shows a normal path.",
        }
        exit_status, envelope = self.panel(
            {
                "reviewer module.a 1": worker(findings=[finding(**two)]),
                "reviewer module.a 2": worker(findings=[finding(**usage)]),
                "chair module.a 1": worker(
                    findings=[merged("r1.1", **two), merged("r2.1", **usage)]
                ),
            },
            "--reviewers",
            "2",
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

    @verifies("scenario.spec-review.several-modules")
    def test_each_module_is_reviewed_on_its_own(self):
        about_b = {"path": "specs/b/module.md"}
        b_own = {"path": "specs/b/obligations.md", "module": "module.b"}
        exit_status, envelope = self.panel(
            {
                "reviewer module.a 1": worker(
                    findings=[finding(tier="suggestion"), finding(**about_b)]
                ),
                "reviewer module.a 2": worker(findings=[]),
                "chair module.a 1": worker(
                    findings=[
                        merged("r1.1", tier="suggestion"),
                        merged("r1.2", **about_b),
                    ]
                ),
                "reviewer module.b 1": worker(findings=[finding(**b_own)]),
                "reviewer module.b 2": worker(findings=[]),
                "chair module.b 1": worker(findings=[merged("r1.1", **b_own)]),
            },
            "--reviewers",
            "2",
            modules=("module.a", "module.b"),
        )
        self.assertEqual((0, "ok"), (exit_status, envelope["status"]), envelope)
        output = envelope["output"]
        by_module = {item["module"]: item for item in output["modules"]}
        self.assertEqual("accepted", by_module["module.a"]["outcome"])
        self.assertEqual("changes_required", by_module["module.b"]["outcome"])
        self.assertEqual("changes_required", output["verdict"])
        in_b = by_module["module.a"]["findings"][1]
        self.assertEqual(("module.b", "suggestion"), (in_b["module"], in_b["tier"]))
        owner = self.issues()[in_b["issue"]]["reports"][-1]["report"]["owner_target_id"]
        self.assertEqual("module.b", owner)
        self.assertIn("finding-scope", self.kinds(envelope))
        self.assertEqual(6, len(envelope["worker_runs"]))
        for run_id in envelope["worker_runs"]:
            record = self.record(run_id)
            if record["worker"] == "chair":
                continue
            frozen = json.loads(
                (Path(record["run_directory"]) / "grant.json").read_text()
            )
            node = json.loads(
                (Path(record["run_directory"]) / "trace.json").read_text()
            )
            (module,) = node["metadata"]["modules"]
            self.assertEqual("review-spec", frozen["task_type"])
            self.assertEqual(
                self.identity("review-spec", module),
                by_module[module]["context_identity"],
            )
        self.assertNotEqual(
            by_module["module.a"]["context_identity"],
            by_module["module.b"]["context_identity"],
        )

    @verifies("scenario.spec-review.unbound-reports")
    def test_an_unbound_panel_reports_to_the_projects_issues(self):
        # An unbound run has no goal to carry the fake workers' plans: the wrapper gives them.
        plans = json.dumps(
            {
                "reviewer module.a 1": worker(findings=[finding()]),
                "reviewer module.a 2": worker(findings=[]),
                "chair module.a 1": worker(findings=[merged("r1.1")]),
            }
        )
        wrapper = self.project.base / "claude-unbound"
        wrapper.write_text(
            f"#!/bin/sh\nFAKE_REVIEW_PLANS='{plans}' "
            f'exec "{sys.executable}" "{FAKE_PANELIST}" "$@"\n'
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
        status, envelope = self.project.run(
            "spec_panel",
            "--modules",
            "module.a",
            "--reviewers",
            "2",
            "--architects",
            "0",
        )
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        (item,) = envelope["output"]["modules"][0]["findings"]
        record = self.issues()[item["issue"]]
        source = record["reports"][0]["source"]
        self.assertEqual(
            (envelope["run_id"], "spec_panel", None, before),
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

    @verifies("scenario.spec-review.without-issues")
    def test_without_the_issues_part_the_findings_stay_in_the_result(self):
        with without_issues():
            status, envelope = self.panel(
                {
                    "reviewer module.a 1": worker(findings=[finding()]),
                    "reviewer module.a 2": worker(findings=[]),
                    "chair module.a 1": worker(findings=[merged("r1.1")]),
                },
                "--reviewers",
                "2",
            )
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        (module,) = envelope["output"]["modules"]
        self.assertEqual("changes_required", module["outcome"])
        self.assertEqual([None], [item["issue"] for item in module["findings"]])
        self.assertIsNone(module["earlier_issues"])
        self.assertIn(NOT_RECORDED, envelope["summary"])
        self.assertEqual({}, self.issues())
        for role in ("reviewer", "chair"):
            for brief in self.briefs(envelope, role):
                self.assertIn("the issues part is not installed", brief)

    @verifies("scenario.spec-review.earlier-issues")
    def test_a_repeated_panel_builds_on_the_earlier_issues(self):
        first = self.earlier("obvious-fix", "first")
        second = self.earlier("decision-needed", "second")
        third = self.earlier("suggestion", "third")
        fourth = self.earlier("obvious-fix", "fourth", operation="issues")
        unknown = "I-" + "9" * 32
        before = self.issues()
        changed = {"earlier": second, "problem": "Changed problem."}
        status, envelope = self.panel(
            {
                "reviewer module.a 1": worker(
                    findings=[finding(**changed), finding(tier="suggestion")]
                ),
                "reviewer module.a 2": worker(
                    findings=[],
                    resolved=self.resolved((third, "The Usage was rewritten.")),
                ),
                "chair module.a 1": worker(
                    findings=[
                        merged("r1.1", **changed),
                        merged("r1.2", tier="suggestion"),
                    ],
                    resolved=self.resolved(
                        (third, "The Usage was rewritten."), (unknown, "No such Issue.")
                    ),
                ),
            },
            "--reviewers",
            "2",
        )
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        (module,) = envelope["output"]["modules"]
        # The first Issue was not mentioned: it is carried, still open and blocking.
        self.assertEqual("changes_required", module["outcome"])
        updated, new = module["findings"]
        self.assertEqual((second, second), (updated["earlier"], updated["issue"]))
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
        for brief in self.briefs(envelope, "reviewer") + self.briefs(envelope, "chair"):
            self.assertIn("Earlier problem first.", brief)
            self.assertNotIn("Earlier problem fourth.", brief)
            self.assertNotIn("r-earlier", brief)

    @verifies("scenario.spec-review.blank-earlier")
    def test_a_blank_earlier_names_no_earlier_issue(self):
        unknown = "I-" + "9" * 32
        claimed = [
            {"earlier": ""},
            {"tier": "suggestion", "earlier": "  "},
            {"tier": "suggestion", "earlier": unknown},
        ]
        status, envelope = self.panel(
            {
                "reviewer module.a 1": worker(
                    findings=[
                        finding(problem=f"Problem {n}.", **extra)
                        for n, extra in enumerate(claimed, 1)
                    ]
                ),
                "reviewer module.a 2": worker(findings=[]),
                "chair module.a 1": worker(
                    findings=[
                        merged(f"r1.{n}", problem=f"Problem {n}.", **extra)
                        for n, extra in enumerate(claimed, 1)
                    ]
                ),
            },
            "--reviewers",
            "2",
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

    @verifies("scenario.spec-review.citation-resume")
    def test_a_reviewer_is_resumed_once_to_correct_a_path(self):
        status, envelope = self.panel(
            {
                "reviewer module.a 1": worker(
                    findings=[finding("../elsewhere/module.md")]
                )
                + worker(findings=[finding()]),
                "reviewer module.a 2": worker(findings=[]),
                "chair module.a 1": worker(findings=[merged("r1.1")]),
            },
            "--reviewers",
            "2",
        )
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        (module,) = envelope["output"]["modules"]
        first = module["reviews"][0]
        self.assertEqual([], first["rejected"])
        self.assertEqual(
            [("r1.1", "specs/a/module.md")],
            [(f["label"], f["path"]) for f in first["findings"]],
        )
        (run_id,) = [
            run_id
            for run_id in envelope["worker_runs"]
            if self.record(run_id)["worker"] == "reviewer1"
        ]
        record = self.record(run_id)
        self.assertEqual(["initial", "repair"], [r["prompt"] for r in record["rounds"]])
        self.assertIn("'../elsewhere/module.md'", record["rounds"][0]["validation"])

    @verifies("scenario.spec-review.last-blocker-resolved")
    def test_resolving_every_earlier_blocking_issue_accepts_the_module(self):
        first = self.earlier("obvious-fix", "first")
        _, envelope = self.panel(
            {
                "reviewer module.a 1": worker(
                    findings=[], resolved=self.resolved((first, "Split."))
                ),
                "reviewer module.a 2": worker(findings=[]),
                "chair module.a 1": worker(
                    findings=[], resolved=self.resolved((first, "Split."))
                ),
            },
            "--reviewers",
            "2",
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
        plans = {
            "reviewer module.a 1": worker(
                findings=[
                    finding(earlier=standing),
                    finding("specs/a/obligations.md"),
                ]
            ),
            "reviewer module.a 2": worker(findings=[]),
            "chair module.a 1": worker(
                findings=[
                    merged("r1.1", earlier=standing),
                    merged("r1.2", path="specs/a/obligations.md"),
                ]
            ),
        }
        goal = "Review the Specs.\nFAKE-PLANS: " + json.dumps(plans)
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
            "spec_panel",
            "--task",
            "t1",
            "--modules",
            "module.a",
            "--reviewers",
            "2",
            "--architects",
            "0",
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

    @verifies("scenario.spec-review.structural-errors")
    def test_a_structurally_invalid_module_is_not_reviewed(self):
        self.project.open_task("t1", goal="Review.")
        self.worktree = self.project.worktree("t1")
        entry = self.worktree / "specs/a/module.md"
        # A Mermaid block is a structural error (CHK.view.marked).
        entry.write_text(entry.read_text() + "\n```mermaid\ngraph TD\n  a --> b\n```\n")
        exit_status, envelope = self.project.run(
            "spec_panel", "--task", "t1", "--modules", "module.a"
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
                "architecture_identity": None,
                "reviews": [],
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
            "spec_panel", "--task", "t1", "--modules", "module.a"
        )
        self.assertEqual((1, "failed"), (exit_status, envelope["status"]), envelope)
        self.assertIsNone(envelope["output"])
        self.assertEqual([], envelope["worker_runs"])
        # The runner already refuses a worktree whose Specs do not load; the review's own
        # loading check is the same rule applied again.
        self.assertTrue({"refused", "structural"} & set(self.kinds(envelope)))

    @verifies("scenario.spec-review.worker-blocked")
    def test_a_blocked_chair_makes_the_panel_incomplete(self):
        exit_status, envelope = self.panel(
            {
                "reviewer module.a 1": worker(findings=[finding()]),
                "reviewer module.a 2": worker(findings=[]),
                "chair module.a 1": [
                    {
                        "result": {
                            "status": "blocked",
                            "output": {"findings": []},
                            "error": worker_error(
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
                        }
                    }
                ],
            },
            "--reviewers",
            "2",
        )
        self.assertEqual((1, "blocked"), (exit_status, envelope["status"]))
        output = envelope["output"]
        self.assertEqual(
            ("incomplete", "incomplete"),
            (output["verdict"], output["modules"][0]["outcome"]),
        )
        self.assertEqual(
            self.identity("review-spec"), output["modules"][0]["context_identity"]
        )
        self.assertEqual("panel_incomplete", envelope["error"]["code"])
        (cause,) = envelope["error"]["causes"]
        self.assertIn("panel of module.a chair attempt 1", cause["actor"])
        chair = link_at(envelope["error"], "worker")
        self.assertEqual(
            "The entry of module.c is needed to judge the Usage.", chair["detail"]
        )
        self.assertEqual(["read the selected documents"], chair["attempts"])
        self.assertEqual(
            ["add a uses relation to module.c", "review module.c first"],
            chair["options"],
        )
        self.assertEqual("blocked", envelope["worker"]["status"])
        self.assertEqual({}, self.issues())

    @verifies("scenario.spec-review.audit-change")
    def test_a_reviewer_that_changed_a_file_is_incomplete(self):
        exit_status, envelope = self.panel(
            {
                "reviewer module.a 1": [
                    {
                        "writes": {"@WORKTREE@/specs/a/module.md": "# Rewritten\n"},
                        "result": {"output": {"findings": []}},
                    }
                ],
                "reviewer module.a 2": worker(findings=[]),
            },
            "--reviewers",
            "2",
        )
        self.assertEqual((1, "failed"), (exit_status, envelope["status"]), envelope)
        self.assertEqual("incomplete", envelope["output"]["modules"][0]["outcome"])
        self.assertEqual([], self.briefs(envelope, "chair"))
        audit = [
            item
            for item in envelope["host_evidence"]
            if item["kind"] in {"audit", "audit_violation"}
        ]
        self.assertTrue(
            any("specs/a/module.md" in item["detail"] for item in audit), audit
        )


class PayloadContractTests(unittest.TestCase):
    def test_the_code_follows_the_panel_payload_contract(self):
        repository = SpecRepository(REPOSITORY_ROOT)
        (contract,) = [
            item
            for item in repository.contracts("module.spec-review")
            if item["id"] == "contract.spec-review.panel-payload"
        ]
        self.assertEqual(contract["schema"], PAYLOAD_SCHEMA)
        validate(contract["example"], PAYLOAD_SCHEMA)


if __name__ == "__main__":
    unittest.main()
