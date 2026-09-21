"""Explicit target admission is the same inspectable child for every retained entry."""

import unittest
from unittest.mock import patch

from concorde.spec.repository import SpecRepository
from concorde.spec.verification import verifies
from tests.concorde.harness import test_worktree_lifecycle as lifecycle_fixtures
from tests.concorde.harness.test_studio import invocation
from tests.concorde.spec.support import PACKAGE, ModelProcessDouble
from tests.concorde.support.legacy_graphs.studio import build_studio_graph


class ExplicitTargetTests(unittest.TestCase):
    def fixture(self, callback=None):
        from tests.concorde.support.native_planning import OperationHost

        adapter = patch(
            "tests.concorde.support.legacy_graphs.studio.OperationHost", OperationHost
        )
        adapter.start()
        self.addCleanup(adapter.stop)
        fixture = lifecycle_fixtures.WorktreeLifecycleTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        return fixture, ModelProcessDouble(callback)

    @verifies("scenario.harness.graph-inspection", "scenario.harness.graph-execution")
    def test_explicit_target_child_is_inspectable_without_discovery_or_project_reads(
        self,
    ):
        fixture, model = self.fixture()
        for operation in (
            "concorde-plan",
            "concorde-spec-review",
            "concorde-code-review",
        ):
            with self.subTest(operation=operation):
                with patch.object(
                    SpecRepository,
                    "__init__",
                    side_effect=AssertionError("inspection read project"),
                ):
                    graph = build_studio_graph(
                        operation, fixture.change, PACKAGE, executor=model.executor
                    )
                    drawing = graph.get_graph(xray=True).to_json()
                    self.assertEqual(drawing, graph.get_graph(xray=True).to_json())
                nodes = {node["id"] for node in drawing["nodes"]}
                self.assertIn(operation + ":execute:prepare_target:bind_target", nodes)
                self.assertFalse(
                    any("discover" in node or "router" in node for node in nodes)
                )
                self.assertEqual([], model.calls)
                result = graph.invoke(
                    {"invocation": invocation(operation, data=fixture.task)}
                )["result"]
                self.assertEqual("succeeded", result["status"], result)
                self.assertTrue(model.calls)
                self.assertTrue(
                    all(
                        call["snapshot"]["target_id"] == fixture.task["target_id"]
                        for call in model.calls
                    )
                )
                self.assertNotIn("route", [call["stage"] for call in model.calls])
                model.calls.clear()

    @verifies("scenario.harness.typed-reject", "scenario.harness.change-owner")
    def test_invalid_explicit_selection_stops_before_candidate_or_worker_effects(self):
        fixture, model = self.fixture()
        graph = build_studio_graph(
            "concorde-plan", fixture.change, PACKAGE, executor=model.executor
        )
        before = (fixture.change / "app/transfer.py").read_bytes()
        for data, code in (
            ({"task": "Plan"}, "invalid_field"),
            ({"target_id": "module.absent", "task": "Plan"}, "unknown_target"),
            ({**fixture.task, "focus_id": "scenario.ledger.read"}, "invalid_focus"),
        ):
            with self.subTest(data=data):
                result = graph.invoke(
                    {"invocation": invocation("concorde-plan", data=data)}
                )["result"]
                self.assertEqual("blocked", result["status"], result)
                self.assertEqual(code, result["errors"][0]["code"])
                self.assertEqual([], model.calls)
                self.assertFalse(fixture.state_file().exists())
                self.assertEqual(
                    before, (fixture.change / "app/transfer.py").read_bytes()
                )

    @verifies("scenario.harness.graph-execution", "scenario.harness.describe-policy")
    def test_assessment_stop_keeps_typed_output_and_preview_runs_no_worker(self):
        def unsupported(stage, snapshot, data, cwd):
            if stage == "context-solve":
                data.update(
                    outcome="unsupported", answer="Explicit contract forbids this work."
                )

        fixture, model = self.fixture(unsupported)
        graph = build_studio_graph(
            "concorde-plan", fixture.change, PACKAGE, executor=model.executor
        )
        request = invocation("concorde-plan", data=fixture.task)
        preview = graph.invoke({"invocation": {**request, "mode": "describe-policy"}})
        self.assertEqual("described", preview["result"]["status"], preview)
        self.assertEqual([], model.calls)
        self.assertFalse(fixture.state_file().exists())
        result = graph.invoke({"invocation": request})["result"]
        self.assertEqual("blocked", result["status"], result)
        self.assertEqual("concorde-plan-response", result["output"]["type_id"])
        self.assertEqual("unsupported", result["output"]["data"]["outcome"])
        self.assertEqual(["context-solve"], [call["stage"] for call in model.calls])

    @verifies("scenario.harness.graph-execution")
    def test_target_and_dispatch_revisions_invalidate_review_evidence(self):
        from concorde.review import review
        from tests.concorde.operations.test_review import ReviewTests

        fixture = ReviewTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        from concorde.harness.change_worktree import bind_owner, ensure_change

        ensure_change(fixture.root, task=fixture.task, allow_primary=True)
        bind_owner(fixture.root, fixture.task)
        result = fixture.call_operation("concorde-spec-review", fixture.task)
        self.assertEqual("succeeded", result["status"], result)
        run = fixture.invocation()
        self.assertIsNotNone(review.current(run, "spec"))
        read = review.read_file
        for source in (
            "src/concorde/harness/native_reviews.py",
            "src/concorde/operations/dispatch_graph.py",
        ):

            def revised(root, path, source=source):
                data = read(root, path)
                return data + b"\n# changed Graph\n" if path == source else data

            with (
                self.subTest(source=source),
                patch.object(review, "read_file", side_effect=revised),
            ):
                self.assertIsNone(review.current(run, "spec"))
