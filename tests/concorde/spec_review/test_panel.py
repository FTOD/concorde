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
from concorde.issues.store import list_issues, read_issue
from concorde.spec.grants import grant
from concorde.spec.repository import SpecRepository
from concorde.spec.schema import validate
from concorde.spec.verification import verifies
from concorde.method.spec_review.panel import PAYLOAD_SCHEMA, account
from tests.concorde.support.operation_project import (
    OperationProject,
    commit,
    link_at,
    worker_error,
)
from tests.concorde.support.paths import REPOSITORY_ROOT
from tests.concorde.spec_review.test_operation import without_issues

FAKE_PANELIST = Path(__file__).with_name("fake_panelist.py")


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

    def identity(self, task_type):
        return grant(
            SpecRepository(self.worktree, REPOSITORY_ROOT), ["module.a"], task_type
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
                findings=[finding("/etc/elsewhere.md"), finding(problem="A.")]
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
        self.assertEqual(["r1.1"], module["findings"][0]["sources"])
        [rejection] = module["rejected"]
        self.assertEqual("r2.1", rejection["source"])
        self.assertIn("the host rejected the chair's finding", rejection["reason"])
        self.assertEqual(1, len(self.issues()))

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
                "reviewer module.a 1": worker(findings=[]),
                "reviewer module.a 2": worker(findings=[]),
                "architect module.a 1": worker(findings=[architectural()]),
                "architect module.a 2": worker(findings=[]),
                "chair module.a 1": worker(
                    findings=[
                        merged(
                            "a1.1",
                            tier="decision-needed",
                            dimension="interfaces",
                            problem="A relies on a promise B does not make.",
                            related=["module.b"],
                            note="B's entry promises nothing of the kind.",
                        )
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
        (report,) = module["findings"]
        self.assertEqual(
            (["a1.1"], ["module.b"]), (report["sources"], report["related"])
        )
        entry = self.issues()[report["issue"]]["reports"][0]
        self.assertEqual("module.a", entry["report"]["owner_target_id"])
        self.assertIn("module.b", entry["report"]["description"])
        self.assertEqual(module["architecture_identity"], entry["source"]["context_id"])

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
