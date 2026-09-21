"""The caller selects capabilities and targets; deleted workflows have no aliases."""

import unittest

from concorde.harness.worker_profile import load_worker_profiles
from concorde.operations.graph_catalog import catalog
from concorde.spec.contracts import PUBLIC_OPERATIONS, operation_modules, schemas
from concorde.spec.typed_data import TypedDataError, typed
from concorde.spec.verification import verifies


class OrchestrationRemovalTests(unittest.TestCase):
    @verifies("scenario.operations.execute-unregistered")
    def test_deleted_operations_and_wire_types_are_absent(self):
        removed = (
            "main",
            "dev-loop",
            "specify-loop",
            "specify",
            "answerer",
            "router",
            "topology-designer",
            "topology-author",
            "spec-author",
        )
        modules = operation_modules()
        wire = schemas()
        for name in removed:
            with self.subTest(name=name):
                self.assertNotIn("concorde-" + name, modules)
                with self.assertRaises(TypedDataError) as error:
                    typed("concorde-" + name + "-request", {})
                self.assertEqual(error.exception.code, "unknown_type")
        for name in wire:
            self.assertNotIn("topology", name)
            self.assertNotIn("discovery", name)
            self.assertNotIn("main-stage", name)
        self.assertEqual(
            set(load_worker_profiles()),
            {
                "planner",
                "task_author",
                "context_assessor",
                "programmer",
                "spec_reviewer",
                "code_reviewer",
                "issue_solver",
            },
        )

    @verifies("scenario.harness.typed-reject")
    def test_public_bound_entries_require_explicit_target(self):
        for name in (
            "context-solve",
            "plan",
            "tasks",
            "implement",
            "spec-review",
            "code-review",
        ):
            with self.subTest(name=name):
                operation = "concorde-" + name
                self.assertIn(operation, PUBLIC_OPERATIONS)
                self.assertEqual(
                    operation_modules()[operation].CONTEXT_SELECTION, "bound"
                )
                with self.assertRaises(TypedDataError):
                    typed(operation + "-request", {"task": "Do the selected task"})
                value = typed(
                    operation + "-request",
                    {"target_id": "module.example", "task": "Do the selected task"},
                )
                self.assertEqual(value["data"]["target_id"], "module.example")

    @verifies("scenario.harness.graph-inspection")
    def test_graphs_have_no_deleted_workflow_nodes(self):
        graphs = catalog()
        self.assertTrue(
            set(graphs).isdisjoint(
                {
                    "development_graph",
                    "specify_graph",
                    "discovery_graph",
                    "query_graph",
                    "topology_graph",
                    "topology_apply_graph",
                    "coordination_graph",
                    "stabilization_graph",
                }
            )
        )
        self.assertEqual(set(graphs), {"terminal_agent_operation"})
        self.assertEqual(
            set(graphs["terminal_agent_operation"]().get_graph().nodes),
            {"__start__", "terminal_agent", "__end__"},
        )
        for module in operation_modules().values():
            self.assertTrue(
                set(module.USES).isdisjoint(
                    {"dev_loop", "specify_loop", "specify", "router"}
                )
            )


if __name__ == "__main__":
    unittest.main()
