"""Context assessment outcomes the Host decides without a model, and a failed native run."""

import json
import unittest
from pathlib import Path

from concorde.issues.references import receipt
from concorde.issues.store import list_issues, resolve_report
from concorde.planning.records import gap_history
from concorde.spec.verification import verifies
from tests.concorde.planning.native_steps import NativeCandidate


class AssessmentTests(NativeCandidate, unittest.TestCase):
    def transfer_uses(self, **fields):
        """Change the transfer Module's ``uses`` of the ledger in its entry metadata."""
        path = self.change / "specs/transfer/module.md.json"
        metadata = json.loads(path.read_text())
        metadata["module"]["uses"][0].update(fields)
        path.write_text(json.dumps(metadata, indent=2) + "\n")
        registry = self.change / ".concorde/specs.json"
        value = json.loads(registry.read_text())
        record = next(m for m in value["modules"] if m["id"] == "service.transfer")
        record["uses"] = metadata["module"]["uses"]
        registry.write_text(json.dumps(value, indent=2) + "\n")

    def assert_no_agent(self, value):
        self.assertEqual(("not-run", False), (value["state"], value["accepted"]))
        self.assertNotIn("descriptor", value)
        self.assertNotIn("call", value)

    @verifies("scenario.planning.native-assessment-failed")
    def test_a_failed_or_cancelled_native_run_accepts_nothing(self):
        self.own()
        for row, code in (
            ({"exitCode": 1}, "execution_failed"),
            ({"interrupted": True}, "execution_cancelled"),
            ({"stopped": True}, "execution_cancelled"),
        ):
            with self.subTest(row=row):
                prepared = self.prepare("concorde-context-solve")
                issue = self.report(prepared)
                data = self.stage_result(
                    prepared,
                    outcome="spec_incomplete",
                    blockers=[{**issue, "blocked_step": "Plan the transfer"}],
                )
                # The staging gate passed before the native run failed.
                value = self.complete(prepared, data, **row)
                self.assertEqual("rejected", value["state"], value)
                self.assertFalse(value["accepted"])
                envelope = value["result"]
                self.assertEqual([code], [e["code"] for e in envelope["errors"]])
                self.assertIsNone(envelope["output"])
                directory = Path(prepared["descriptor"]).parent
                self.assertFalse((directory / "terminal.json").exists())
                self.assertEqual([], gap_history(self.change_state()))
                self.assertFalse(
                    list((self.change / ".concorde/runs").glob("*/native-context.json"))
                )

    @verifies("scenario.planning.collaboration-gap")
    def test_an_unexplained_collaboration_reports_a_gap_without_an_agent(self):
        self.transfer_uses(meaning="#no-such-explanation")
        value = self.prepare("concorde-context-solve")
        self.assert_no_agent(value)
        output = value["result"]["output"]["data"]
        self.assertEqual("spec_incomplete", output["outcome"], output)
        self.assertEqual(1, len(output["blockers"]))
        blocker = output["blockers"][0]
        self.assertTrue(blocker["blocked_step"])
        report = resolve_report(self.change, receipt(blocker))
        self.assertEqual(
            ("gap", "missing-contract", "service.transfer"),
            (
                report["report"]["type"],
                report["report"]["subtype"],
                report["report"]["owner_target_id"],
            ),
        )
        self.assertIn("uses module.ledger", report["report"]["description"])
        self.assertEqual(
            [blocker["issue_id"]], [issue["id"] for issue in list_issues(self.change)]
        )

    @verifies("scenario.planning.collaboration-conflict")
    def test_inconsistent_collaborations_conflict_without_an_agent_or_issue(self):
        for name, fields in (
            ("foreign relies_on", {"relies_on": ["concept.bank.request"]}),
            ("self use", {"target": "service.transfer"}),
        ):
            with self.subTest(case=name):
                path = self.change / "specs/transfer/module.md.json"
                registry = self.change / ".concorde/specs.json"
                originals = path.read_bytes(), registry.read_bytes()
                self.transfer_uses(**fields)
                value = self.prepare("concorde-context-solve")
                self.assert_no_agent(value)
                output = value["result"]["output"]["data"]
                self.assertEqual("conflicting", output["outcome"], output)
                self.assertEqual([], output["blockers"])
                self.assertIn("conflicts", output["answer"])
                self.assertEqual([], list_issues(self.change))
                path.write_bytes(originals[0])
                registry.write_bytes(originals[1])


if __name__ == "__main__":
    unittest.main()
