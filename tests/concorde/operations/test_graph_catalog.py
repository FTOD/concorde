"""The Operation catalog builds its StateGraphs for inspection; without a service they cannot run."""

import unittest
from unittest.mock import patch

from concorde.harness.operation_node import OperationNode
from concorde.harness.operation_state import OperationRuntimeContext
from concorde.harness.worker_profile import worker_profile
from concorde.operations.graph_catalog import catalog, topology
from concorde.spec.verification import verifies
from tests.concorde.harness.test_operation_node import _stage_context


class GraphCatalogTests(unittest.TestCase):
    @verifies("scenario.operations.inspect-catalog")
    def test_catalog_builds_the_topology_execution_compiles(self):
        with patch("subprocess.Popen", side_effect=AssertionError("process started")):
            built = {name: factory() for name, factory in catalog().items()}
        self.assertEqual({"terminal_agent_operation"}, set(built))
        graph = built["terminal_agent_operation"]
        self.assertEqual("terminal_agent_operation", graph.get_name())
        self.assertEqual(
            {"__start__", "terminal_agent", "__end__"}, set(graph.get_graph().nodes)
        )
        executed = OperationNode("context_assessor").graph(lambda value: value)
        self.assertEqual(topology(executed), topology(graph))

    @verifies("scenario.operations.operation-without-service")
    def test_catalog_operation_without_a_service_is_inspection_only(self):
        graph = catalog()["terminal_agent_operation"]()
        data = _stage_context()["data"]
        data["snapshot"]["data"]["phase"] = worker_profile(
            "context_assessor"
        ).contract.phase
        with self.assertRaisesRegex(RuntimeError, "inspection only"):
            graph.invoke(data)
        with self.assertRaisesRegex(RuntimeError, "inspection only"):
            graph.invoke(data, context=OperationRuntimeContext())
        # A launcher placed in State is not a declared channel and never becomes the service.
        with self.assertRaisesRegex(RuntimeError, "inspection only"):
            graph.invoke({**data, "launcher": lambda value: value})


if __name__ == "__main__":
    unittest.main()
