"""The discovery child shown by each public parent must be the child it executes."""

import unittest
from typing import Any, cast
from unittest.mock import Mock, patch

from concorde.operations import target_graph
from concorde.query_routing.main import MainInvocation
from concorde.harness.host import OperationHost
from concorde.harness.admission import run_operation
from concorde.harness.change_worktree import read_change
from concorde.harness.studio import build_studio_graph
from concorde.spec.repository import SpecRepository
from concorde.spec.typed_data import typed
from concorde.spec.verification import verifies
from tests.concorde.harness import test_worktree_lifecycle as lifecycle_fixtures
from tests.concorde.harness.test_studio import invocation
from tests.concorde.spec.support import CONFIGURATION, PACKAGE, ModelProcessDouble


class TargetDiscoveryTests(unittest.TestCase):
    def fixture(self, callback=None):
        fixture = lifecycle_fixtures.WorktreeLifecycleTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        model = ModelProcessDouble(callback)
        return fixture, model

    def graph(self, operation, fixture, model):
        built = []
        build = target_graph.build_discovery_graph

        def instrument(nodes):
            child = build(nodes)
            child.invoke = Mock(wraps=child.invoke)
            built.append(child)
            return child

        with (
            patch.object(target_graph, "build_discovery_graph", side_effect=instrument),
            patch.object(
                SpecRepository,
                "__init__",
                side_effect=AssertionError("inspection resolved context"),
            ),
        ):
            graph = build_studio_graph(
                operation, fixture.change, PACKAGE, executor=model.executor
            )
            drawing = graph.get_graph(xray=True).to_json()
            self.assertEqual(drawing, graph.get_graph(xray=True).to_json())
        self.assertEqual([], model.calls)
        parent = (
            cast(Any, graph.nodes[operation].subgraphs[0]).nodes["execute"].subgraphs[0]
        )
        preparation = parent.nodes["prepare_target"].subgraphs[0]
        child = preparation.nodes["discover"].subgraphs[0]
        self.assertEqual([child], built)
        self.assertIs(child.checkpointer, False)
        child.invoke.assert_not_called()
        prefix = operation + ":execute:prepare_target:"
        nodes = {n["id"] for n in drawing["nodes"]}
        self.assertTrue(
            {
                prefix + "initialize_target",
                prefix + "bind_target",
                prefix + "discover:decide",
                prefix + "discover:expand_context",
                prefix + "discover:bind_routes",
                prefix + "discover:finish",
            }
            <= nodes
        )
        return graph, child

    @verifies(
        "scenario.harness.graph-inspection",
        "scenario.development.graph-execution",
        "scenario.development.resume-bound",
        "scenario.development.standalone-review",
    )
    def test_public_parent_executes_its_inspected_child_and_resume_skips_discovery(
        self,
    ):
        for operation in (
            "concorde-review",
            "concorde-dev-loop",
            "concorde-specify-loop",
        ):
            with self.subTest(operation=operation):
                fixture, model = self.fixture()
                graph, child = self.graph(operation, fixture, model)
                task: dict[str, Any] = dict(fixture.task)
                task.update(
                    {"review_mode": "spec"}
                    if operation == "concorde-review"
                    else {"specify": False, "run_reviews": True}
                )
                request = invocation(operation, data=task)
                # Hidden callback discovery cannot supply this execution evidence.
                with patch.object(
                    MainInvocation,
                    "discover_routes",
                    side_effect=AssertionError(
                        "discovery must run in the composed child"
                    ),
                ):
                    first = graph.invoke({"invocation": request})
                    self.assertEqual("succeeded", first["result"]["status"], first)
                    child.invoke.assert_called_once()
                    self.assertEqual(1, sum(c["stage"] == "route" for c in model.calls))
                    if operation == "concorde-review":
                        from operations import review as review_operation

                        route = next(c for c in model.calls if c["stage"] == "route")
                        self.assertEqual("concorde-router", route["operation"])
                        self.assertIn("router", review_operation.USES)
                    model.calls.clear()
                    second = graph.invoke({"invocation": request})
                self.assertEqual("succeeded", second["result"]["status"], second)
                self.assertNotEqual(
                    first["result"]["invocation_id"], second["result"]["invocation_id"]
                )
                if operation == "concorde-review":
                    self.assertEqual(2, child.invoke.call_count)
                    self.assertEqual(1, sum(c["stage"] == "route" for c in model.calls))
                else:
                    child.invoke.assert_called_once()
                    self.assertFalse(any(c["stage"] == "route" for c in model.calls))
                    self.assertEqual(
                        fixture.task["task"],
                        read_change(fixture.change, required=True)["task"],
                    )

    @verifies(
        "scenario.harness.graph-inspection", "scenario.development.graph-execution"
    )
    def test_blocked_discovery_keeps_typed_output_and_never_enters_dependent_work(self):
        def unsupported(stage, snapshot, data, cwd):
            if stage == "route":
                data.update(
                    outcome="unsupported",
                    answer="Controlled routing stop",
                    routes=[],
                    expand_targets=[],
                    blockers=[],
                )

        for operation in (
            "concorde-review",
            "concorde-dev-loop",
            "concorde-specify-loop",
        ):
            with self.subTest(operation=operation):
                fixture, model = self.fixture(unsupported)
                graph, child = self.graph(operation, fixture, model)
                task = {
                    **fixture.task,
                    **(
                        {"review_mode": "spec"}
                        if operation == "concorde-review"
                        else {}
                    ),
                }
                before = (fixture.change / "app/transfer.py").read_bytes()
                result = graph.invoke({"invocation": invocation(operation, data=task)})[
                    "result"
                ]
                self.assertEqual("blocked", result["status"], result)
                self.assertEqual(operation + "-response", result["output"]["type_id"])
                self.assertEqual("unsupported", result["output"]["data"]["outcome"])
                self.assertEqual(["route"], [c["stage"] for c in model.calls])
                child.invoke.assert_called_once()
                self.assertEqual(
                    before, (fixture.change / "app/transfer.py").read_bytes()
                )

    @verifies(
        "scenario.development.graph-execution", "scenario.development.describe-policy"
    )
    def test_trusted_bound_target_and_policy_preview_preserve_admission(self):
        fixture, model = self.fixture()
        host = OperationHost(
            fixture.change,
            PACKAGE,
            executor=model.executor,
            routed_target="service.transfer",
        )
        with patch.object(
            MainInvocation,
            "stage",
            side_effect=AssertionError("bound child routed again"),
        ):
            result = run_operation(
                "concorde-dev-loop",
                CONFIGURATION,
                typed("concorde-dev-loop-request", {**fixture.task, "specify": False}),
                host_context=host,
            )
        self.assertEqual("succeeded", result["status"], result)
        model.calls.clear()
        wrong = run_operation(
            "concorde-review",
            CONFIGURATION,
            typed(
                "concorde-review-request",
                {"target_id": "scope.bank", "task": "Review", "review_mode": "spec"},
            ),
            host_context=host,
        )
        self.assertEqual("incompatible_handoff", wrong["errors"][0]["code"])
        self.assertEqual([], model.calls)
        graph = build_studio_graph(
            "concorde-review", fixture.change, PACKAGE, executor=model.executor
        )
        preview = graph.invoke(
            {
                "invocation": invocation(
                    "concorde-review",
                    mode="describe-policy",
                    data={**fixture.task, "review_mode": "spec"},
                )
            }
        )
        self.assertEqual("described", preview["result"]["status"], preview)
        self.assertEqual([], model.calls)

    @verifies("scenario.development.graph-execution")
    def test_target_and_dispatch_graph_revisions_invalidate_review_evidence(self):
        from concorde.review import review
        from tests.concorde.operations.test_review import ReviewTests

        fixture = ReviewTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        result = fixture.call_operation(
            "concorde-specify-loop", {**fixture.task, "specify": False}
        )
        self.assertEqual("succeeded", result["status"], result)
        run = fixture.invocation()
        self.assertIsNotNone(review.current(run, "spec"))
        read = review.read_file
        for source in (
            "src/concorde/operations/target_graph.py",
            "src/concorde/operations/dispatch_graph.py",
        ):

            def revised(root, path):
                data = read(root, path)
                return (
                    data + b"\n# changed executable Graph\n" if path == source else data
                )

            with (
                self.subTest(source=source),
                patch.object(review, "read_file", side_effect=revised),
            ):
                self.assertIsNone(review.current(run, "spec"))
