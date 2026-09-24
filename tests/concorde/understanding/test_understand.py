"""The understand Operation end to end, with the fake ``claude`` of the worker tests."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from concorde.harness.runs import read_record
from concorde.spec.verification import verifies
from concorde.understanding.operation import ASSESSMENT_SCHEMA
from tests.concorde.support.operation_project import (
    OperationProject,
    link_at,
    worker_error,
)
from tests.concorde.support.paths import REPOSITORY_ROOT

GOAL = "let A answer two questions"


def assessment(**changes) -> dict:
    value = {
        "goal": GOAL,
        "modules": [{"module": "module.a", "promises": "A answers one question."}],
        "sufficient": True,
        "gaps": [],
        "plan": None,
    }
    value.update(changes)
    return value


PLAN = {
    "summary": "Declare the new file, then implement it.",
    "modules": ["module.a"],
    "pending": [
        {
            "module": "module.a",
            "realization": "realization.a.code",
            "path": "src/a/second.py",
            "reason": "the second answer",
        }
    ],
    "steps": [
        {"operation": "specify", "modules": ["module.a"], "purpose": "state it"},
        {"operation": "implement", "modules": ["module.a"], "purpose": "build it"},
    ],
    "decisions": ["whether the second answer is optional"],
}
GAP = {
    "module": "module.a",
    "document": "specs/a/module.md",
    "missing": "what the second question is",
    "needed_for": "the goal names a second answer",
    "suggestion": "add a scenario for the second question",
}


class UnderstandTests(unittest.TestCase):
    def setUp(self):
        self.project = OperationProject(self)
        self.project.open_task()
        self.worktree = self.project.worktree()

    def understand(self, rounds, *extra):
        return self.project.run(
            "understand",
            "--task",
            "t1",
            "--goal",
            OperationProject.plan(rounds),
            *extra,
        )

    def fake_round(self, envelope) -> dict:
        record = read_record(self.project.root, envelope["worker_runs"][-1])
        work = Path(record["run_directory"]) / "work"
        return json.loads((work / "fake-round-1.json").read_text())

    @verifies("scenario.understanding.sufficient")
    def test_a_sufficient_spec_is_confirmed_without_a_plan(self):
        status, envelope = self.understand([{"result": {"output": assessment()}}])
        self.assertEqual(0, status, envelope)
        self.assertEqual("ok", envelope["status"])
        output = envelope["output"]
        self.assertTrue(output["sufficient"])
        self.assertEqual([], output["gaps"])
        self.assertIsNone(output["plan"])
        # The goal is the host's argument, repeated verbatim.
        self.assertIn("FAKE-PLAN", output["goal"])
        seen = self.fake_round(envelope)
        tools = seen["argv"][seen["argv"].index("--tools") + 1]
        self.assertEqual("Read,Glob,Grep", tools)
        brief = seen["prompt"]
        readable = brief.split("You may read these paths")[1].split("You may know")[0]
        names = brief.split("You may know that these files exist")[1]
        writable = brief.split("You may change only these paths")[1].split(
            "You may read"
        )[0]
        self.assertIn(f"{self.worktree}/specs/a/module.md", readable)
        self.assertIn(f"{self.worktree}/src/a/", names)
        self.assertNotIn("src/a/", readable)
        self.assertIn("(none)", writable)
        self.assertIn("Plan requested: no", brief)
        record = read_record(self.project.root, envelope["worker_runs"][-1])
        self.assertEqual(1, len(record["rounds"]))
        self.assertIsNone(record["rounds"][0].get("checks"))

    @verifies("scenario.understanding.plan")
    def test_a_plan_is_returned_on_request(self):
        status, envelope = self.understand(
            [{"result": {"output": assessment(plan=PLAN)}}], "--plan"
        )
        self.assertEqual(0, status, envelope)
        plan = envelope["output"]["plan"]
        self.assertEqual(["module.a"], plan["modules"])
        self.assertEqual("realization.a.code", plan["pending"][0]["realization"])
        self.assertEqual(
            ["specify", "implement"], [step["operation"] for step in plan["steps"]]
        )
        self.assertIn("Plan requested: yes", self.fake_round(envelope)["prompt"])

    @verifies("scenario.understanding.gap")
    def test_a_missing_promise_is_reported_as_a_gap(self):
        status, envelope = self.understand(
            [{"result": {"output": assessment(sufficient=False, gaps=[GAP])}}],
            "--plan",
        )
        self.assertEqual(0, status, envelope)
        output = envelope["output"]
        self.assertFalse(output["sufficient"])
        self.assertEqual(GAP, output["gaps"][0])
        self.assertIsNone(output["plan"])

    @verifies("scenario.understanding.unassessable")
    def test_a_goal_that_cannot_be_assessed_escalates(self):
        status, envelope = self.understand(
            [
                {
                    "result": {
                        "status": "blocked",
                        "summary": "cannot assess",
                        "error": worker_error(
                            "the goal concerns module.b, which is not bound",
                            code="unbound_module",
                            reason="scope",
                            attempts=["read the A Spec"],
                            options=["bind module.b"],
                        ),
                        "output": assessment(sufficient=False),
                    }
                }
            ]
        )
        self.assertEqual(1, status)
        self.assertEqual("blocked", envelope["status"])
        worker = link_at(envelope["error"], "worker")
        self.assertIn("module.b", worker["detail"])
        self.assertEqual("scope", worker["unhandled"]["reason"])
        self.assertEqual(["read the A Spec"], worker["attempts"])
        self.assertEqual(["bind module.b"], worker["options"])
        self.assertIn("bind module.b", envelope["error"]["options"])
        self.assertIsNone(envelope["output"])

    @verifies("scenario.understanding.unknown-module")
    def test_an_unknown_module_fails_the_run(self):
        bad = assessment(sufficient=False, gaps=[{**GAP, "module": "module.zzz"}])
        status, envelope = self.understand([{"result": {"output": bad}}])
        self.assertEqual(1, status)
        self.assertEqual("failed", envelope["status"])
        unknown = [
            item
            for item in envelope["host_evidence"]
            if item["kind"] == "unknown-module"
        ]
        self.assertEqual(["module.zzz"], [item["ref"] for item in unknown])
        self.assertIsNone(envelope["output"])
        self.assertEqual(
            "module.zzz", envelope["worker"]["output"]["gaps"][0]["module"]
        )

    @verifies("scenario.understanding.inconsistent")
    def test_an_inconsistent_assessment_fails_the_run(self):
        for rounds, extra in (
            ([{"result": {"output": assessment(plan=PLAN)}}], ()),
            ([{"result": {"output": assessment(sufficient=False, gaps=[])}}], ()),
            ([{"result": {"output": assessment(gaps=[GAP])}}], ()),
            ([{"result": {"output": assessment()}}], ("--plan",)),
        ):
            status, envelope = self.understand(rounds, *extra)
            self.assertEqual("failed", envelope["status"], rounds)
            self.assertTrue(
                any(
                    item["kind"] == "inconsistent-assessment"
                    for item in envelope["host_evidence"]
                )
            )
            self.assertEqual(1, len(envelope["worker_runs"]))

    @verifies("scenario.understanding.change-detected")
    def test_a_change_to_the_worktree_fails_the_run(self):
        target = self.worktree / "specs/a/module.md"
        status, envelope = self.understand(
            [
                {
                    "writes": {str(target): "# A\n\nChanged.\n"},
                    "result": {"output": assessment()},
                },
                {"result": {"output": assessment()}},
            ]
        )
        self.assertEqual(1, status)
        self.assertEqual("failed", envelope["status"])
        error = envelope["error"]
        self.assertEqual("audit_violation", error["code"])
        self.assertEqual("permission", error["unhandled"]["reason"])
        self.assertIn("specs/a/module.md", error["detail"])
        record = read_record(self.project.root, envelope["worker_runs"][-1])
        self.assertEqual(1, len(record["rounds"]))


class ContractTests(unittest.TestCase):
    def test_the_output_schema_is_the_assessment_contract(self):
        text = (
            REPOSITORY_ROOT / "specs/concorde/operations/understanding/contracts.md"
        ).read_text()
        fence = re.search(r"```concorde-contract\n(.*?)\n```", text, re.S).group(1)
        self.assertEqual(json.loads(fence)["schema"], ASSESSMENT_SCHEMA)


if __name__ == "__main__":
    unittest.main()
