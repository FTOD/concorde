"""The ``spec_panel`` Operation: the host's accounting, and whole panels with fake workers."""

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
from concorde.spec_review.panel import PAYLOAD_SCHEMA, account
from tests.concorde.support.operation_project import (
    OperationProject,
    link_at,
    worker_error,
)
from tests.concorde.support.paths import REPOSITORY_ROOT

FAKE_PANELIST = Path(__file__).with_name("fake_panelist.py")


def finding(path="specs/a/module.md", severity="blocking", **extra):
    return {
        "module": "module.a",
        "path": path,
        "dimension": "obligations",
        "severity": severity,
        "problem": f"A {severity} problem in {path}.",
        "evidence": "Quoted text.",
        "suggestion": "Rewrite it.",
        **extra,
    }


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
                "r9.9 names no reviewer finding",
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

    def panel(self, plans, *extra, modules=("module.a",)):
        goal = "Review the Specs.\nFAKE-PLANS: " + json.dumps(plans)
        self.project.open_task("t1", modules=modules, goal=goal)
        self.worktree = self.project.worktree("t1")
        return self.project.run(
            "spec_panel", "--task", "t1", "--modules", ",".join(modules), *extra
        )

    def record(self, run_id):
        return json.loads(
            (self.root / ".concorde/runs" / run_id / "record.json").read_text()
        )

    def briefs(self, envelope, role):
        found = []
        for run_id in envelope["worker_runs"]:
            record = self.record(run_id)
            if record["worker"].rstrip("0123456789") == role:
                work = Path(record["run_directory"]) / "work"
                found.append(
                    json.loads((work / "fake-round-1.json").read_text())["prompt"]
                )
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
                        finding(severity="advisory", problem="Wording."),
                    ]
                ),
                "chair module.a 1": worker(
                    findings=[
                        merged(
                            "r1.1",
                            "r2.1",
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
        (module,) = output["modules"]
        self.assertEqual(
            grant(
                SpecRepository(self.worktree, REPOSITORY_ROOT),
                ["module.a"],
                "review-spec",
            ).value["context_identity"],
            module["context_identity"],
        )
        self.assertEqual(
            [(1, "ok", ["r1.1"]), (2, "ok", ["r2.1", "r2.2"])],
            [
                (r["reviewer"], r["status"], [f["label"] for f in r["findings"]])
                for r in module["reviews"]
            ],
        )
        (report,) = module["findings"]
        self.assertEqual(
            (["r1.1", "r2.1"], 2), (report["sources"], report["reviewers"])
        )
        self.assertEqual(["r2.2"], [item["source"] for item in module["rejected"]])
        self.assertIn(
            "1 blocking and 0 advisory finding(s) merged from 3", envelope["summary"]
        )
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
                    "every reviewer finding accounted for once",
                )
            ],
            [(i["ref"], i["detail"]) for i in accounting],
        )
        graph = next(i for i in envelope["host_evidence"] if i["kind"] == "graph")
        self.assertIn("chair", Path(graph["ref"]).read_text())
        # A panel writes nothing.
        self.assertEqual("", self.status())

    @verifies("scenario.spec-review.panel-worker-models")
    def test_each_reviewer_runs_on_the_model_configured_for_its_worker_id(self):
        config = {
            "schema_version": 3,
            "default": {"backend": "claude"},
            "operations": {
                "spec_panel": {
                    "default": {"model": "claude-sonnet-5", "reasoning": "medium"},
                    "workers": {
                        "reviewer2": {"model": "claude-opus-5-5"},
                        "chair": {"model": "claude-opus-5-5", "reasoning": "high"},
                    },
                }
            },
        }
        (self.root / ".concorde/worker-models.json").write_text(json.dumps(config))
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
        chosen = {}
        for run_id in envelope["worker_runs"]:
            record = self.record(run_id)
            work = Path(record["run_directory"]) / "work"
            argv = json.loads((work / "fake-round-1.json").read_text())["argv"]
            chosen[record["worker"]] = (
                argv[argv.index("--model") + 1],
                argv[argv.index("--effort") + 1],
            )
        self.assertEqual(
            {
                "reviewer1": ("claude-sonnet-5", "medium"),
                "reviewer2": ("claude-opus-5-5", "medium"),
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

    @verifies("scenario.spec-review.panel-short")
    def test_a_blocked_reviewer_stops_the_panel_before_the_chair(self):
        exit_status, envelope = self.panel(
            {
                "reviewer module.a 1": worker(findings=[finding()]),
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
        )
        self.assertEqual((1, "blocked"), (exit_status, envelope["status"]))
        output = envelope["output"]
        self.assertEqual("incomplete", output["verdict"])
        self.assertEqual([], self.briefs(envelope, "chair"))
        self.assertEqual(
            [(1, "ok"), (2, "blocked")],
            [(r["reviewer"], r["status"]) for r in output["modules"][0]["reviews"]],
        )
        error = envelope["error"]
        self.assertEqual("panel_incomplete", error["code"])
        (short,) = error["causes"]
        self.assertEqual("panel_short", short["code"])
        (reviewer,) = short["causes"]
        self.assertIn("panel of module.a reviewer2", reviewer["actor"])
        worker_link = link_at(error, "worker")
        self.assertEqual("The entry of module.c is needed.", worker_link["detail"])

    def test_a_blocking_finding_outside_the_module_is_advisory(self):
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
        self.assertEqual("advisory", item["severity"])
        self.assertEqual("accepted", envelope["output"]["verdict"])


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
