"""Graph execution, viewer inspection and JSON boundaries share real runtime factories."""

import json
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
from typing import Any
from unittest import TestCase
from unittest.mock import Mock, patch

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import InMemorySaver

from concorde.query_routing.main import MainInvocation
from concorde.harness.batch_graph import run_batch_graph
from concorde.spec.verification import verifies
from tests.concorde.harness import test_studio as studio_fixtures

invocation = studio_fixtures.invocation


class GraphTests(TestCase):
    def fixture(self):
        fixture = studio_fixtures.StudioTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        return fixture

    @verifies("scenario.harness.graph-inspection")
    def test_inspection_never_resolves_a_context_or_runs_an_agent(self):
        fixture = self.fixture()
        with (
            patch("concorde.harness.invocation.SpecRepository") as bound,
            patch("concorde.query_routing.main.SpecRepository") as discovered,
            patch("concorde.operations.dispatch.SpecRepository") as dispatched,
        ):
            drawings = {}
            for operation in studio_fixtures.EXPECTED_PUBLIC:
                with self.subTest(operation=operation):
                    graph = fixture.graph(operation)
                    drawing = graph.get_graph(xray=True)
                    self.assertEqual(
                        drawing.to_json(), graph.get_graph(xray=True).to_json()
                    )
                    independent = fixture.graph(operation)
                    self.assertIsNot(graph, independent)
                    self.assertEqual(
                        drawing.to_json(), independent.get_graph(xray=True).to_json()
                    )
                    drawings[operation] = drawing
            for repository in (bound, discovered, dispatched):
                repository.assert_not_called()
        self.assertEqual([], fixture.double.calls)
        drawing = drawings["concorde-main"]
        self.assertTrue(
            any(name.endswith(":discover:decide") for name in drawing.nodes)
        )
        self.assertTrue(
            any(name.endswith(":apply_atomically") for name in drawing.nodes)
        )
        self.assertFalse(
            any(name.endswith(":development_loop") for name in drawing.nodes)
        )

    @verifies(
        "scenario.harness.graph-inspection", "scenario.harness.graph-execution"
    )
    def test_nested_updates_and_checkpoints_contain_json_not_host_objects(self):
        fixture = self.fixture()
        graph = fixture.graph("concorde-main")
        saver = InMemorySaver()
        graph.checkpointer = saver
        config: RunnableConfig = {"configurable": {"thread_id": "graph-json"}}
        updates = list(
            graph.stream(
                {
                    "invocation": invocation(
                        "concorde-main", data={"task": "Explain transfer"}
                    )
                },
                config,
                subgraphs=True,
                stream_mode="updates",
            )
        )
        # This also catches callbacks accidentally returned through private state channels.
        json.dumps(updates)
        names = {name for _, update in updates for name in update}
        self.assertIn("decide", names)
        self.assertIn("expand_context", names)
        for checkpoint in saver.list(config):
            channels = checkpoint.checkpoint["channel_values"]
            json.dumps(channels)
            self.assertNotIn("session", channels)
        result = graph.get_state(config, subgraphs=True).values["result"]
        self.assertEqual("succeeded", result["status"], result)

    @verifies("scenario.harness.graph-inspection")
    def test_concurrent_runs_have_separate_runtime_contexts(self):
        fixture = self.fixture()
        graph = fixture.graph()
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(
                pool.map(lambda _: graph.invoke({"invocation": invocation()}), range(2))
            )
        self.assertEqual(
            ["succeeded", "succeeded"], [value["result"]["status"] for value in results]
        )
        self.assertNotEqual(
            results[0]["result"]["invocation_id"], results[1]["result"]["invocation_id"]
        )
        for value in results:
            ids = {event["invocation_id"] for event in value["events"]}
            self.assertEqual({value["result"]["invocation_id"]}, ids)

    @verifies("scenario.harness.graph-bounds")
    def test_discovery_can_expand_beyond_the_default_langgraph_limit(self):
        # Deliberately partial duck-typed fixture; exercise routing without a real Host.
        main: Any = MainInvocation.__new__(MainInvocation)
        main.repository = SimpleNamespace(
            targets={str(i): SimpleNamespace(kind="module") for i in range(40)},
            select=lambda name: SimpleNamespace(kind="module", id=name),
        )
        main.host = SimpleNamespace(mode="execute")
        main.task = {}
        main.completed = []
        main.discovered = ["entry"]
        main.stage_context_text = lambda _: "\n".join(
            "module." + str(i) for i in range(35)
        )
        main.stage = Mock(
            side_effect=lambda phase, occurrence: (
                {"outcome": "expand", "expand_targets": ["module." + str(occurrence)]}
                if occurrence < 35
                else {"outcome": "answered", "answer": "Complete"}
            )
        )
        routes, decision = main.discover_routes()
        self.assertEqual([], routes)
        self.assertEqual("answered", decision["outcome"])
        self.assertEqual(36, main.stage.call_count)

    @verifies(
        "scenario.harness.graph-bounds", "scenario.harness.graph-execution"
    )
    def test_large_batch_stops_before_running_dependent_items(self):
        visited = []

        def operation(item):
            visited.append(item)
            return {"outcome": "blocked"} if item == 37 else None

        result = run_batch_graph(
            range(60), operation, name="review_test_graph", item_node="review_module"
        )
        self.assertEqual({"outcome": "blocked"}, result)
        self.assertEqual(list(range(38)), visited)

    @verifies("scenario.harness.graph-execution")
    def test_scheduler_failure_keeps_the_error_envelope_and_final_event(self):
        from concorde.harness.host import OperationHost
        from concorde.harness.admission import run_operation

        fixture = self.fixture()
        events = []
        host = OperationHost(
            fixture.root,
            studio_fixtures.PACKAGE,
            observer=lambda event, **details: events.append(event),
        )
        value = invocation()
        with patch("concorde.harness.operation_graph.build_operation_graph") as build:
            build.return_value.invoke.side_effect = RuntimeError("scheduler failed")
            result = run_operation(
                value["operation_id"], None, value["input"], host_context=host
            )
        self.assertEqual("failed", result["status"])
        self.assertEqual("execution_failed", result["errors"][0]["code"])
        self.assertIsNone(result["output"])
        self.assertEqual(["operation_started", "operation_finished"], events)
        self.assertEqual([], fixture.double.calls)

    @verifies("scenario.harness.graph-execution")
    def test_extracted_review_graph_remains_part_of_review_identity(self):
        from concorde.review import review
        from concorde.harness.invocation import Invocation
        from concorde.harness.host import OperationHost

        fixture = self.fixture()
        run = Invocation(
            "concorde-review",
            studio_fixtures.CONFIGURATION,
            {"target_id": "service.transfer", "task": "Inspect transfer"},
            OperationHost(fixture.root, studio_fixtures.PACKAGE),
        )
        before, _ = review.inputs(run, "code")
        read_file = review.read_file

        def changed_graph(root, path):
            data = read_file(root, path)
            return (
                data + b"\n# revised scheduling\n"
                if path == "src/concorde/harness/batch_graph.py"
                else data
            )

        with patch.object(review, "read_file", side_effect=changed_graph):
            after, _ = review.inputs(run, "code")
        self.assertNotEqual(before["input_digest"], after["input_digest"])
        self.assertEqual(before["revision"], after["revision"])

    @verifies("scenario.harness.graph-inspection")
    def test_batch_inspection_matches_executed_nodes_and_stop_edges(self):
        from concorde.harness import batch_graph

        build = batch_graph.build_batch_graph
        for item_node in ("review_module", "coordinate_component"):
            for stop_at in (None, 1):
                with self.subTest(item_node=item_node, stop_at=stop_at):
                    visited, operations, drawings = [], [], []

                    def instrument(factory, **options):
                        def node(name):
                            execute = factory(name)

                            def record(state):
                                visited.append(name)
                                return execute(state)

                            return record

                        graph = build(node, **options)
                        first = graph.get_graph().to_json()
                        self.assertEqual(first, graph.get_graph().to_json())
                        self.assertEqual([], visited)
                        self.assertEqual([], operations)
                        self.assertIs(graph.checkpointer, False)
                        drawings.append(first)
                        return graph

                    def operation(item):
                        operations.append(item)
                        return {"outcome": "blocked"} if item == stop_at else None

                    with patch.object(
                        batch_graph, "build_batch_graph", side_effect=instrument
                    ):
                        result = batch_graph.run_batch_graph(
                            range(3),
                            operation,
                            name="inspection_batch",
                            item_node=item_node,
                        )
                    drawing = drawings[0]
                    edges = {
                        (edge["source"], edge["target"]) for edge in drawing["edges"]
                    }
                    path = ["__start__", *visited, "__end__"]
                    self.assertTrue(
                        all(edge in edges for edge in zip(path, path[1:], strict=False))
                    )
                    self.assertEqual(
                        [0, 1, 2] if stop_at is None else [0, 1], operations
                    )
                    self.assertEqual(
                        None if stop_at is None else {"outcome": "blocked"}, result
                    )
