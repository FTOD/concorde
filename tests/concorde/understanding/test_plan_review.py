"""The ``plan_review`` Operation end to end, with the fake ``claude`` of the worker tests.

The fake reads its script from ``FAKE-PLAN: <json>`` in the brief, where the caller's plan is
quoted, so each test writes the script into the plan file it reviews.
"""

from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

from concorde.worker_harness.models import validate_config
from concorde.worker_harness.runs import read_record
from concorde.spec.verification import verifies
from concorde.method.understanding.plan_review import REPORT_SCHEMA
from tests.concorde.support.operation_project import OperationProject, link_at
from tests.concorde.support.paths import REPOSITORY_ROOT
from tests.concorde.understanding.test_understand import assessment


def finding(number, **values) -> dict:
    return {
        "id": f"F{number}",
        "severity": "blocking",
        "kind": "violation",
        "module": "module.a",
        "basis": "scenario.a.answer",
        "locations": ["plan: step 2", "src/a/calc.py:2"],
        "description": "step 2 changes the answer A promises",
        "suggestion": "keep the answer and add the new one beside it",
        "previous": None,
        **values,
    }


def response(finding_id, outcome="settled", comment="the revision settles it") -> dict:
    return {"finding": finding_id, "outcome": outcome, "comment": comment}


class PlanReviewTests(unittest.TestCase):
    def setUp(self):
        self.project = OperationProject(self)
        self.root = self.project.root
        self.project.open_task()
        self.worktree = self.project.worktree()

    def write_plan(self, responses=(), findings=(), steps="1. implement\n2. test\n"):
        """A plan file whose text carries the fake reviewer's answer."""
        script = [
            {
                "result": {
                    "summary": "reviewed the plan",
                    "output": {
                        "responses": list(responses),
                        "findings": list(findings),
                    },
                }
            }
        ]
        path = self.worktree / "plan.md"
        path.write_text(
            "# Plan\n\n" + steps + "\nFAKE-PLAN: " + json.dumps(script) + "\n"
        )
        return path

    def review(self, *extra, plan="plan.md"):
        return self.project.run("plan_review", "--task", "t1", "--plan", plan, *extra)

    def brief(self, envelope) -> tuple[dict, str]:
        record = read_record(self.root / ".concorde", envelope["worker_runs"][-1])
        return record, (Path(record["run_directory"]) / "brief.md").read_text()

    @verifies("scenario.understanding.plan-accepted")
    def test_a_sound_plan_is_accepted(self):
        path = self.write_plan(
            findings=[finding(1, severity="advisory", kind="scope", basis=None)]
        )
        status, envelope = self.review()
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        report = envelope["output"]
        self.assertEqual("accepted", report["verdict"])
        self.assertEqual(
            (1, None, []), (report["iteration"], report["previous"], report["answers"])
        )
        self.assertEqual("reviewed the plan", report["summary"])
        # The exact plan is kept in the run's trace node, bound by its digest.
        data = path.read_bytes()
        self.assertEqual(path.as_posix(), report["plan"]["file"])
        self.assertEqual(
            "sha256:" + hashlib.sha256(data).hexdigest(), report["plan"]["digest"]
        )
        copy = Path(report["plan"]["copy"])
        self.assertEqual("plan.md", copy.name)
        self.assertEqual(data, copy.read_bytes())
        path.unlink()
        self.assertTrue(copy.is_file())
        record, brief = self.brief(envelope)
        self.assertEqual("reviewer", record["worker"])
        self.assertEqual("Read,Glob,Grep", record["tools"])
        self.assertEqual(1, len(record["rounds"]))
        self.assertIsNone(record["rounds"][0].get("checks"))
        self.assertIn("The workspace's goal: Fix A.", brief)
        self.assertIn("1. implement\n2. test", brief)
        self.assertIn("This is the first iteration", brief)
        readable = brief.split("You may read these paths")[1].split("You may know")[0]
        writable = brief.split("You may change only these paths")[1].split(
            "You may read"
        )[0]
        self.assertIn(f"{self.worktree}/specs/a/module.md", readable)
        self.assertIn(f"{self.worktree}/src/a/", readable)
        self.assertIn("(none)", writable)

    @verifies("scenario.understanding.plan-changes-required")
    def test_a_blocking_finding_requires_a_revision(self):
        findings = [finding(1), finding(2, kind="sequence", basis=None, module=None)]
        self.write_plan(findings=findings)
        _, envelope = self.review()
        self.assertEqual("ok", envelope["status"], envelope)
        self.assertEqual("changes_required", envelope["output"]["verdict"])
        self.assertEqual(findings, envelope["output"]["findings"])

    @verifies("scenario.understanding.plan-next-iteration")
    def test_the_next_iteration_answers_the_previous_one(self):
        self.write_plan(findings=[finding(1), finding(2, kind="code", basis=None)])
        _, first = self.review()
        self.assertEqual("ok", first["status"], first)
        restated = finding(1, previous="F2", kind="code", basis=None)
        self.write_plan(
            responses=[response("F1"), response("F2", "maintained", "still wrong")],
            findings=[restated],
            steps="1. specify\n2. implement\n3. test\n",
        )
        status, envelope = self.review(
            "--input",
            first["run_id"],
            "--accept",
            "F1",
            "step 1 now states the new answer",
            "--reject",
            "F2",
            "calc.py already returns both answers",
        )
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        report = envelope["output"]
        self.assertEqual(
            (2, first["run_id"]), (report["iteration"], report["previous"])
        )
        self.assertEqual(
            [
                {
                    "finding": "F1",
                    "answer": "accepted",
                    "text": "step 1 now states the new answer",
                },
                {
                    "finding": "F2",
                    "answer": "rejected",
                    "text": "calc.py already returns both answers",
                },
            ],
            report["answers"],
        )
        self.assertEqual("maintained", report["responses"][1]["outcome"])
        self.assertEqual([restated], report["findings"])
        self.assertEqual("changes_required", report["verdict"])
        _, brief = self.brief(envelope)
        self.assertIn("This is iteration 2", brief)
        self.assertIn("Answer: **accepted**: step 1 now states the new answer", brief)
        self.assertIn(
            "Answer: **rejected**: calc.py already returns both answers", brief
        )
        self.assertIn("+1. specify", brief)
        # The previous run is admitted as the previous iteration, not as other material.
        self.assertNotIn("Other admitted inputs", brief)

    @verifies("scenario.understanding.plan-unanswered")
    def test_an_unanswered_finding_stops_the_next_iteration(self):
        self.write_plan(findings=[finding(1), finding(2)])
        _, first = self.review()
        _, envelope = self.review(
            "--input", first["run_id"], "--accept", "F1", "done", "--reject", "F3", "no"
        )
        self.assertEqual("failed", envelope["status"], envelope)
        self.assertEqual([], envelope["worker_runs"])
        self.assertIsNone(envelope["output"])
        link = link_at(envelope["error"], "operation")
        self.assertEqual(
            ("iteration_mismatch", "input"), (link["code"], link["unhandled"]["reason"])
        )
        self.assertIn("finding F2", link["detail"])
        self.assertIn("no finding F3", link["detail"])

    def test_answers_need_a_previous_iteration(self):
        self.write_plan()
        _, envelope = self.review("--accept", "F1", "done")
        link = link_at(envelope["error"], "operation")
        self.assertEqual("iteration_mismatch", link["code"])
        self.assertEqual([], envelope["worker_runs"])

    def test_only_one_previous_iteration_is_admitted(self):
        self.write_plan()
        _, first = self.review()
        _, second = self.review()
        _, envelope = self.review(
            "--input", first["run_id"], "--input", second["run_id"]
        )
        link = link_at(envelope["error"], "operation")
        self.assertEqual("iteration_mismatch", link["code"])
        self.assertIn("more than one", link["detail"])

    def test_other_inputs_are_material(self):
        _, understood = self.project.run(
            "understand",
            "--task",
            "t1",
            "--goal",
            OperationProject.plan([{"result": {"output": assessment()}}]),
        )
        self.assertEqual("ok", understood["status"], understood)
        self.write_plan()
        _, first = self.review()
        self.write_plan()
        # A previous iteration without findings needs no answer; the understand run the plan
        # started from is material, shown to the reviewer as it is.
        _, envelope = self.review(
            "--input", first["run_id"], "--input", understood["run_id"]
        )
        self.assertEqual("ok", envelope["status"], envelope)
        self.assertEqual(2, envelope["output"]["iteration"])
        self.assertEqual(first["run_id"], envelope["output"]["previous"])
        _, brief = self.brief(envelope)
        material = brief.split("## Other admitted inputs")[1]
        self.assertIn(understood["run_id"], material)
        self.assertIn("A answers one question.", material)
        self.assertNotIn(first["run_id"], material)

    @verifies("scenario.understanding.plan-unreadable")
    def test_a_missing_or_empty_plan_stops_the_run(self):
        for name, content in (
            ("absent.md", None),
            ("empty.md", "  \n"),
            ("binary.md", b"\xff\xfe"),
        ):
            if isinstance(content, str):
                (self.worktree / name).write_text(content)
            elif content is not None:
                (self.worktree / name).write_bytes(content)
            _, envelope = self.review(plan=name)
            self.assertEqual("failed", envelope["status"], (name, envelope))
            self.assertEqual([], envelope["worker_runs"])
            link = link_at(envelope["error"], "operation")
            self.assertEqual(
                ("plan_unreadable", "input"),
                (link["code"], link["unhandled"]["reason"]),
            )

    @verifies("scenario.understanding.plan-inconsistent")
    def test_a_review_that_ignores_the_previous_iteration_fails(self):
        self.write_plan(findings=[finding(1)])
        _, first = self.review()
        for responses, findings, expected in (
            ([], [], "previous finding F1 has 0 responses"),
            (
                [response("F1")],
                [finding(1, previous="F1")],
                "F1 restates F1, which is not maintained",
            ),
            (
                [response("F1", "maintained")],
                [],
                "maintained finding F1 is restated 0 times",
            ),
            (
                [response("F1")],
                [finding(1, module="module.b")],
                "concerns module.b, which is not bound",
            ),
        ):
            self.write_plan(responses=responses, findings=findings)
            _, envelope = self.review(
                "--input", first["run_id"], "--accept", "F1", "done"
            )
            self.assertEqual("failed", envelope["status"], envelope)
            self.assertIsNone(envelope["output"])
            link = link_at(envelope["error"], "operation")
            self.assertEqual(
                ("inconsistent_review", "capability"),
                (link["code"], link["unhandled"]["reason"]),
            )
            self.assertIn(expected, link["detail"])
            record = read_record(self.root / ".concorde", envelope["worker_runs"][-1])
            self.assertEqual(1, len(record["rounds"]))

    @verifies("scenario.understanding.plan-unresolved-basis")
    def test_a_basis_must_resolve(self):
        self.write_plan(
            findings=[
                finding(1, basis="req.nowhere"),
                finding(2, basis=None),
                finding(3, kind="goal", basis=None),
                finding(4, kind="goal", basis="specs/a/module.md#design"),
            ]
        )
        _, envelope = self.review()
        self.assertEqual("failed", envelope["status"], envelope)
        link = link_at(envelope["error"], "operation")
        self.assertEqual(
            ("unresolved_basis", "capability"),
            (link["code"], link["unhandled"]["reason"]),
        )
        self.assertIn("F1 cites req.nowhere", link["detail"])
        self.assertIn("F2 cites (none)", link["detail"])
        self.assertNotIn("F3", link["detail"])
        self.assertNotIn("F4", link["detail"])

    def test_a_plan_is_reviewed_only_in_a_workspace(self):
        path = self.write_plan()
        _, envelope = self.project.run(
            "plan_review",
            "--plan",
            path.as_posix(),
            "--modules",
            "module.a",
            cwd=self.root,
        )
        self.assertEqual("failed", envelope["status"], envelope)
        self.assertIn("binding_required", json.dumps(envelope["error"]))
        self.assertEqual([], envelope["worker_runs"])

    def test_the_reviewer_model_is_configured_by_its_worker_id(self):
        validate_config(
            {
                "schema_version": 2,
                "enabled_models": {"gpt-6.1-sol": {}},
                "default": {"model": "gpt-6.1-sol"},
                "operations": {
                    "plan_review": {"workers": {"reviewer": {"model": "gpt-6.1-sol"}}}
                },
            }
        )
        project = json.loads((REPOSITORY_ROOT / ".concorde/workers.json").read_text())
        self.assertEqual(
            "gpt-6.1-sol",
            project["operations"]["plan_review"]["workers"]["reviewer"]["model"],
        )

    def test_the_contract_matches_the_spec(self):
        text = (
            REPOSITORY_ROOT / "specs/concorde/method/understanding/contracts.md"
        ).read_text()
        block = text.split("## Plan review report")[1].split("```concorde-contract")[1]
        contract = json.loads(block.split("```")[0])
        self.assertEqual("contract.understanding.plan-review", contract["id"])
        self.assertEqual(contract["schema"], REPORT_SCHEMA)


if __name__ == "__main__":
    unittest.main()
