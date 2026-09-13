"""Spec completion can stand alone and feed the development loop in the same change."""
import unittest
from unittest.mock import patch

from concorde.harness.change_worktree import read_change
from concorde.spec.verification import verifies
from tests.concorde.development import test_review as fixtures


class SpecifyLoopTests(unittest.TestCase):
    setUp = fixtures.ReviewTests.setUp
    double = fixtures.ReviewTests.double
    call_capability = fixtures.ReviewTests.call_capability
    missing = fixtures.ReviewTests.missing
    gap = staticmethod(fixtures.ReviewTests.gap)

    @verifies("scenario.development.specify-loop")
    def test_standalone_authors_and_reviews_without_implementation_or_readiness(self):
        result = self.call_capability("concorde-specify-loop")
        self.assertEqual("succeeded", result["status"], result)
        data = result["output"]["data"]
        self.assertEqual("completed", data["outcome"])
        self.assertEqual(["specify", "spec-review"], [item["stage"] for item in self.model.calls])
        state = read_change(self.root)
        self.assertNotEqual("ready", state["status"])
        self.assertEqual({"spec": True}, state["review_requirements"][self.task["target_id"]])
        self.assertFalse(state["targets"].get(self.task["target_id"], {}).get("plan"))
        self.assertTrue(data["artifacts"])
        self.assertFalse(data["checks"])
        self.assertIn("concorde-specify", data["completed_capabilities"])

    @verifies("scenario.development.specify-loop", "scenario.development.dev-loop-ready")
    def test_development_composes_specify_loop_and_resumes_its_evidence(self):
        from concorde.development import capability_host
        first = self.call_capability("concorde-specify-loop")
        self.assertEqual("succeeded", first["status"], first)
        with patch.object(capability_host, "invoke_capability", wraps=capability_host.invoke_capability) as invoke:
            result = self.call_capability("concorde-dev-loop")
        self.assertEqual("succeeded", result["status"], result)
        self.assertEqual("ready", result["output"]["data"]["outcome"])
        self.assertEqual(first["output"]["data"]["change_id"], result["output"]["data"]["change_id"])
        stages = [item["stage"] for item in self.model.calls]
        self.assertNotIn("specify", stages)
        self.assertNotIn("spec-review", stages)
        self.assertIn("plan", stages)
        self.assertIn(("concorde-dev-loop", "concorde-specify-loop"),
                      [call.args[:2] for call in invoke.call_args_list])

    @verifies("scenario.development.specify-loop")
    def test_skip_options_record_only_spec_evidence(self):
        result = self.call_capability("concorde-specify-loop",
                                     {**self.task, "specify": False, "run_reviews": False})
        self.assertEqual("succeeded", result["status"], result)
        self.assertEqual([], self.model.calls)
        state = read_change(self.root)
        self.assertEqual({"spec": False}, state["review_requirements"][self.task["target_id"]])
        self.assertEqual({"spec"}, set(state["reviews"][self.task["target_id"]]))
        self.assertEqual("skipped", state["reviews"][self.task["target_id"]]["spec"]["status"])

    @verifies("scenario.development.specify-loop", "scenario.development.dev-loop-spec-gap")
    def test_gap_stops_and_required_review_cannot_be_disabled_on_resume(self):
        first = self.call_capability("concorde-specify-loop", callback=self.missing("spec-review"))
        self.assertEqual("blocked", first["status"], first)
        self.assertEqual("spec_incomplete", first["output"]["data"]["outcome"])
        self.assertEqual("waiting", read_change(self.root)["status"])
        second = self.call_capability("concorde-specify-loop", {**self.task, "run_reviews": False},
                                      callback=self.missing("spec-review"))
        self.assertEqual("blocked", second["status"], second)
        self.assertTrue(read_change(self.root)["review_requirements"][self.task["target_id"]]["spec"])
        self.assertNotEqual("skipped", read_change(self.root)["reviews"][self.task["target_id"]]["spec"]["status"])
        document = self.root / "specs/transfer/module.md"
        document.write_text(document.read_text() + "\nTransfer owns the daily-limit admission rule.\n")
        resumed = self.call_capability("concorde-specify-loop")
        self.assertEqual("succeeded", resumed["status"], resumed)
        self.assertEqual([], read_change(self.root)["gaps"])

    @verifies("scenario.development.specify-loop")
    def test_policy_preview_contains_only_spec_agents_and_does_not_create_change(self):
        result = self.call_capability("concorde-specify-loop", mode="describe-policy")
        self.assertEqual("described", result["status"], result)
        self.assertEqual("described", result["output"]["data"]["outcome"])
        self.assertEqual([], self.model.calls)
        self.assertIsNone(read_change(self.root))
        self.assertEqual(["specify", "spec-review"], [item["phase"] for item in self.host.descriptions])

    @verifies("scenario.development.specify-loop", "scenario.development.flow-execution")
    def test_rejected_author_preserves_the_error_and_never_reaches_review(self):
        def foreign_document(stage, snapshot, data, cwd):
            if stage == "specify":
                data["documents"] = [{"path": "specs/audit/module.md", "content": "Foreign Spec"}]
        result = self.call_capability("concorde-specify-loop", callback=foreign_document)
        self.assertEqual("blocked", result["status"], result)
        self.assertIsNone(result["output"])
        self.assertEqual("child_blocked", result["errors"][0]["code"])
        self.assertIn("permission_denied", result["errors"][0]["message"])
        self.assertEqual(["specify"], [item["stage"] for item in self.model.calls])

    @verifies("scenario.development.specify-loop", "scenario.development.flow-execution")
    def test_studio_exposes_independent_spec_flow_and_development_composition(self):
        from concorde.harness.studio import build_studio_flow
        from tests.concorde.spec.support import PACKAGE
        spec = build_studio_flow("concorde-specify-loop", self.root, PACKAGE).get_graph(xray=True)
        self.assertTrue(any(name.endswith(":specify_loop:specify") for name in spec.nodes))
        self.assertTrue(any(name.endswith(":specify_loop:review_spec") for name in spec.nodes))
        self.assertFalse(any(name.endswith(":plan") or name.endswith(":ready") for name in spec.nodes))
        dev = build_studio_flow("concorde-dev-loop", self.root, PACKAGE).get_graph(xray=True)
        self.assertTrue(any(name.endswith(":development_loop:specify_loop") for name in dev.nodes))
        self.assertFalse(any(name.endswith(":development_loop:review_spec") for name in dev.nodes))
