"""The ``spec_debate`` Operation: the host's stance rules, and whole debates with fake debaters."""

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
from concorde.spec_review.debate import (
    PAYLOAD_SCHEMA,
    apply_responses,
    new_item,
    outcome,
)
from tests.concorde.support.operation_project import (
    OperationProject,
    link_at,
    worker_error,
)
from tests.concorde.support.paths import REPOSITORY_ROOT

FAKE_DEBATER = Path(__file__).with_name("fake_debater.py")


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


def answer(item, stance, reason="Because the Spec says so.", **extra):
    return {"item": item, "stance": stance, "reason": reason, **extra}


def turn(**output):
    return [{"result": {"output": output}}]


def _position(item):
    return item["state"], item["current"], item["last"]


class StanceTests(unittest.TestCase):
    """The host moves an item only by the stance a worker took on it."""

    def setUp(self):
        self.first = finding(problem="First.")
        self.items = [new_item(1, "reviewer", 1, self.first)]

    def test_agreeing_with_a_finding_makes_it_stand(self):
        items, found = apply_responses(
            self.items, "challenger", 2, [answer("d.1", "agree")], {}
        )
        self.assertEqual("agreed", items[0]["state"])
        self.assertEqual(self.first, items[0]["current"])
        self.assertEqual([], found)
        self.assertEqual("open", self.items[0]["state"])  # the input is not changed

    def test_objecting_first_means_it_does_not_hold_and_agreeing_withdraws(self):
        items, _ = apply_responses(
            self.items, "challenger", 2, [answer("d.1", "object")], {}
        )
        self.assertEqual(("open", None, "challenger"), _position(items[0]))
        items, _ = apply_responses(items, "reviewer", 3, [answer("d.1", "agree")], {})
        self.assertEqual("withdrawn", items[0]["state"])

    def test_an_amendment_becomes_the_position_the_other_side_answers(self):
        milder = finding(severity="advisory", problem="First, milder.")
        items, _ = apply_responses(
            self.items, "challenger", 2, [answer("d.1", "amend")], {0: milder}
        )
        self.assertEqual(("open", milder, "challenger"), _position(items[0]))
        self.assertEqual(milder, items[0]["history"][-1]["finding"])
        # The reviewer objects: its own finding is the current position again.
        items, _ = apply_responses(items, "reviewer", 3, [answer("d.1", "object")], {})
        self.assertEqual(("open", self.first, "reviewer"), _position(items[0]))
        items, _ = apply_responses(
            items, "challenger", 4, [answer("d.1", "object")], {}
        )
        self.assertEqual(("open", milder, "challenger"), _position(items[0]))

    def test_restating_the_other_sides_position_settles_the_item(self):
        items, _ = apply_responses(
            self.items, "challenger", 2, [answer("d.1", "amend")], {0: self.first}
        )
        self.assertEqual("agreed", items[0]["state"])

    def test_stray_second_and_empty_responses_move_nothing_and_are_reported(self):
        items, found = apply_responses(
            self.items,
            "reviewer",
            2,
            [answer("d.1", "agree"), answer("d.9", "agree")],
            {},
        )
        self.assertEqual("open", items[0]["state"])  # d.1 does not await its proposer
        self.assertEqual(2, len(found))
        items, found = apply_responses(
            self.items,
            "challenger",
            2,
            [answer("d.1", "amend"), answer("d.1", "agree")],
            {},
        )
        self.assertEqual("agreed", items[0]["state"])
        self.assertIn("an amend without a finding", found[0]["detail"])
        items, found = apply_responses(self.items, "challenger", 2, [], {})
        self.assertEqual("open", items[0]["state"])
        self.assertIn("no response; the item stays open", found[0]["detail"])

    def test_the_outcome_counts_agreed_blocking_findings_before_disagreements(self):
        agreed = dict(new_item(1, "reviewer", 1, finding()), state="agreed")
        contested = dict(new_item(2, "reviewer", 1, finding()), state="contested")
        advisory = dict(
            new_item(3, "reviewer", 1, finding(severity="advisory")),
            state="contested",
        )
        self.assertEqual("changes_required", outcome([agreed, contested], False))
        self.assertEqual("undecided", outcome([contested, advisory], False))
        self.assertEqual("accepted", outcome([advisory], False))
        self.assertEqual("incomplete", outcome([agreed], True))


class SpecDebateTests(unittest.TestCase):
    def setUp(self):
        self.project = OperationProject(self)
        self.root = self.project.root
        wrapper = self.project.base / "claude-debater"
        wrapper.write_text(
            f'#!/bin/sh\nexec "{sys.executable}" "{FAKE_DEBATER}" "$@"\n'
        )
        wrapper.chmod(0o755)
        self.project.fake = wrapper

    def debate(self, plans, *extra, modules=("module.a",)):
        goal = "Review the Specs.\nFAKE-PLANS: " + json.dumps(plans)
        self.project.open_task("t1", modules=modules, goal=goal)
        self.worktree = self.project.worktree("t1")
        return self.project.run(
            "spec_debate", "--task", "t1", "--modules", ",".join(modules), *extra
        )

    def brief(self, run_id):
        record = json.loads(
            (self.root / ".concorde/runs" / run_id / "record.json").read_text()
        )
        work = Path(record["run_directory"]) / "work"
        return json.loads((work / "fake-round-1.json").read_text())["prompt"]

    def status(self):
        return subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=self.worktree,
            capture_output=True,
            text=True,
            check=True,
        ).stdout

    def states(self, envelope):
        return {
            item["id"]: item["state"]
            for item in envelope["output"]["modules"][0]["items"]
        }

    @verifies("scenario.spec-review.debate-agreement")
    def test_findings_both_sides_agree_on_stand_and_dropped_ones_are_withdrawn(self):
        exit_status, envelope = self.debate(
            {
                "reviewer module.a 1": turn(
                    findings=[
                        finding(problem="Two obligations."),
                        finding(severity="advisory", problem="Wording."),
                    ]
                ),
                "challenger module.a 2": turn(
                    responses=[
                        answer("d.1", "agree"),
                        answer("d.2", "object", "The next sentence defines it."),
                    ],
                    additions=[finding(problem="Missed.")],
                ),
                "reviewer module.a 3": turn(
                    responses=[answer("d.2", "agree"), answer("d.3", "agree")]
                ),
            }
        )
        self.assertEqual((0, "ok"), (exit_status, envelope["status"]), envelope)
        output = envelope["output"]
        validate(output, PAYLOAD_SCHEMA)
        self.assertEqual("changes_required", output["verdict"])
        self.assertEqual(
            {"d.1": "agreed", "d.2": "withdrawn", "d.3": "agreed"},
            self.states(envelope),
        )
        module = output["modules"][0]
        self.assertEqual(3, module["turns"])
        self.assertEqual(
            grant(
                SpecRepository(self.worktree, REPOSITORY_ROOT),
                ["module.a"],
                "review-spec",
            ).value["context_identity"],
            module["context_identity"],
        )
        self.assertEqual("challenger", module["items"][2]["proposer"])
        self.assertIsNone(module["items"][1]["finding"])
        # Nothing awaited the challenger after the reviewer's answers: no second challenge.
        self.assertEqual(3, len(envelope["worker_runs"]))
        self.assertIn("2 agreed blocking finding(s)", envelope["summary"])
        challenge = self.brief(envelope["worker_runs"][1])
        self.assertIn("Your role: challenger.", challenge)
        self.assertIn("Debate turn: 2 (challenge).", challenge)
        self.assertIn("### d.1 (proposed by the reviewer)", challenge)
        self.assertIn("This is your first challenge turn", challenge)
        respond = self.brief(envelope["worker_runs"][2])
        self.assertIn("### d.3 (proposed by the challenger)", respond)
        self.assertIn("The next sentence defines it.", respond)
        self.assertIn("- d.1 (agreed): Two obligations.", respond)
        graph = next(i for i in envelope["host_evidence"] if i["kind"] == "graph")
        self.assertIn("challenge", Path(graph["ref"]).read_text())
        # A debate writes nothing, not even a review memory.
        self.assertEqual("", self.status())

    @verifies("scenario.spec-review.debate-contested")
    def test_a_disagreement_left_after_the_last_turn_is_a_decision_point(self):
        exit_status, envelope = self.debate(
            {
                "reviewer module.a 1": turn(findings=[finding(problem="Unclear.")]),
                "challenger module.a 2": turn(
                    responses=[answer("d.1", "object", "It is clear.")], additions=[]
                ),
                "reviewer module.a 3": turn(
                    responses=[answer("d.1", "object", "Line 3 is ambiguous.")]
                ),
                "challenger module.a 4": turn(
                    responses=[answer("d.1", "object", "Line 4 resolves it.")],
                    additions=[],
                ),
                "reviewer module.a 5": turn(
                    responses=[answer("d.1", "object", "Line 4 is a note.")]
                ),
            },
            "--rounds",
            "2",
        )
        self.assertEqual((0, "ok"), (exit_status, envelope["status"]), envelope)
        output = envelope["output"]
        self.assertEqual("undecided", output["verdict"])
        (item,) = output["modules"][0]["items"]
        self.assertEqual("contested", item["state"])
        self.assertIsNone(item["finding"])
        self.assertIsNone(item["positions"]["challenger"])
        self.assertEqual("Unclear.", item["positions"]["reviewer"]["problem"])
        self.assertEqual(
            [("reviewer", "propose")]
            + [(role, "object") for role in ("challenger", "reviewer")] * 2,
            [(entry["role"], entry["stance"]) for entry in item["history"]],
        )
        self.assertEqual(5, output["modules"][0]["turns"])
        self.assertIn("1 decision point(s)", envelope["summary"])
        later = self.brief(envelope["worker_runs"][3])
        self.assertIn("This is a later challenge turn", later)
        self.assertIn("Your last position: the finding does not hold", later)

    @verifies("scenario.spec-review.debate-amended")
    def test_an_agreed_amendment_is_the_finding_that_stands(self):
        exit_status, envelope = self.debate(
            {
                "reviewer module.a 1": turn(findings=[finding(problem="Blocking?")]),
                "challenger module.a 2": turn(
                    responses=[
                        answer(
                            "d.1",
                            "amend",
                            "A reader can still act on it.",
                            finding=finding(severity="advisory", problem="Wording."),
                        )
                    ],
                    additions=[],
                ),
                "reviewer module.a 3": turn(responses=[answer("d.1", "agree")]),
            }
        )
        self.assertEqual((0, "ok"), (exit_status, envelope["status"]), envelope)
        self.assertEqual("accepted", envelope["output"]["verdict"])
        (item,) = envelope["output"]["modules"][0]["items"]
        self.assertEqual(
            ("agreed", "advisory"), (item["state"], item["finding"]["severity"])
        )

    def test_a_blocking_finding_outside_the_module_is_advisory(self):
        exit_status, envelope = self.debate(
            {
                "reviewer module.a 1": turn(findings=[finding("specs/b/module.md")]),
                "challenger module.a 2": turn(
                    responses=[answer("d.1", "agree")], additions=[]
                ),
            }
        )
        self.assertEqual((0, "ok"), (exit_status, envelope["status"]), envelope)
        (item,) = envelope["output"]["modules"][0]["items"]
        self.assertEqual("advisory", item["finding"]["severity"])
        self.assertIn("finding-scope", [i["kind"] for i in envelope["host_evidence"]])

    @verifies("scenario.spec-review.debate-incomplete")
    def test_a_blocked_challenger_makes_the_debate_incomplete_with_its_chain(self):
        exit_status, envelope = self.debate(
            {
                "reviewer module.a 1": turn(findings=[finding()]),
                "challenger module.a 2": [
                    {
                        "result": {
                            "status": "blocked",
                            "output": {"responses": [], "additions": []},
                            "error": worker_error(
                                "The entry of module.c is needed.",
                                code="context_missing",
                                reason="permission",
                            ),
                        }
                    }
                ],
            }
        )
        self.assertEqual((1, "blocked"), (exit_status, envelope["status"]))
        output = envelope["output"]
        self.assertEqual("incomplete", output["verdict"])
        self.assertEqual({"d.1": "open"}, self.states(envelope))
        error = envelope["error"]
        self.assertEqual("debate_incomplete", error["code"])
        (cause,) = error["causes"]
        self.assertIn("debate of module.a turn 2", cause["actor"])
        worker = link_at(error, "worker")
        self.assertEqual("The entry of module.c is needed.", worker["detail"])


class PayloadContractTests(unittest.TestCase):
    def test_the_code_follows_the_debate_payload_contract(self):
        repository = SpecRepository(REPOSITORY_ROOT)
        (contract,) = [
            item
            for item in repository.contracts("module.spec-review")
            if item["id"] == "contract.spec-review.debate-payload"
        ]
        self.assertEqual(contract["schema"], PAYLOAD_SCHEMA)
        validate(contract["example"], PAYLOAD_SCHEMA)


if __name__ == "__main__":
    unittest.main()
