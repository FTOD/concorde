"""Genuine optional StateGraph integration; service injection is trusted, not model State."""

import asyncio
import unittest

from concorde.harness.operation_node import OperationNode
from concorde.harness.operation_state import OperationRuntimeContext
from concorde.spec.typed_data import typed
from concorde.spec.verification import verifies
from tests.concorde.harness.test_operation_node import _stage_context


class OptionalOperationTests(unittest.TestCase):
    @verifies("scenario.harness.optional-operation")
    def test_stategraph_sync_and_async_share_one_boundary(self):
        context = _stage_context()
        seen = []

        def result(value):
            seen.append(value)
            return typed(
                "concorde-agent-stage-result",
                {
                    "context_id": value["data"]["snapshot"]["data"]["context_id"],
                    "outcome": "completed",
                    "answer": "Trusted admitted native result fixture",
                    "blockers": [],
                    "documents": [],
                    "plan": "Plan",
                    "tasks": [],
                },
            )

        operation = OperationNode("planner")
        graph = operation.graph()
        self.assertEqual(
            set(graph.get_graph().nodes), {"__start__", "terminal_agent", "__end__"}
        )
        value = graph.invoke(
            context["data"], context=OperationRuntimeContext(launcher=result)
        )
        self.assertEqual(value["plan"], "Plan")

        async def native_service(value):
            return result(value)

        value = asyncio.run(
            graph.ainvoke(
                context["data"],
                context=OperationRuntimeContext(launcher=native_service),
            )
        )
        self.assertEqual(value["plan"], "Plan")
        self.assertEqual(seen, [context, context])
        with self.assertRaisesRegex(RuntimeError, "inspection only"):
            graph.invoke(context["data"])
