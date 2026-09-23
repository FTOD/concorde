"""An Agent call is a LangGraph node whose typed state is the Agent definition's input and result."""

import unittest

from langgraph.graph import END, START, StateGraph

from concorde.harness.operation_node import OperationNode, state_schema, typed_state
from concorde.harness.operation_state import OperationRuntimeContext
from concorde.harness.worker_profile import agent_definition
from concorde.spec.repository import SpecError
from concorde.spec.typed_data import TypedDataError, data_schema, typed
from concorde.spec.verification import verifies
from tests.concorde.support.stage_context import stage_context as _stage_context


class OperationNodeTests(unittest.TestCase):
    @verifies("scenario.execution.agent-node")
    def test_node_schemas_are_exactly_the_contract_fields(self):
        for name in (
            "context_assessor",
            "planner",
            "task_author",
            "programmer",
            "spec_reviewer",
            "code_reviewer",
            "issue_solver",
        ):
            with self.subTest(worker=name):
                agent = agent_definition(name)
                node = OperationNode(agent.name)
                self.assertEqual(
                    (agent.context, agent.result),
                    (node.input_type, node.result_type),
                )
                self.assertEqual(
                    set(data_schema(node.input_type)["properties"]),
                    set(node.input_schema.__annotations__),
                )
                assert node.result_type is not None
                self.assertEqual(
                    set(data_schema(node.result_type)["properties"]),
                    set(node.output_schema.__annotations__),
                )
                union = state_schema(node.input_type, node.result_type, name="S")
                self.assertEqual(
                    set(node.input_schema.__annotations__)
                    | set(node.output_schema.__annotations__),
                    set(union.__annotations__),
                )
                drawing = node.graph().get_graph()
                self.assertEqual(
                    {"__start__", "terminal_agent", "__end__"}, set(drawing.nodes)
                )
        self.assertEqual(
            {"snapshot", "change_id", "expected_artifacts"},
            set(typed_state("concorde-agent-stage-context").__annotations__),
        )

    @verifies("scenario.execution.agent-node")
    def test_invocation_validates_context_in_and_result_out(self):
        node = OperationNode("planner")
        context = _stage_context()
        seen = []

        def launcher(admitted):
            seen.append(admitted)
            return {
                "context_id": admitted["data"]["snapshot"]["data"]["context_id"],
                "outcome": "completed",
                "answer": "Planned.",
                "blockers": [],
                "documents": [],
                "plan": "Do the work.",
                "tasks": [],
            }

        data = node.invoke(context, launcher)
        self.assertEqual("Do the work.", data["plan"])
        self.assertEqual([context], seen)
        with self.assertRaises(TypedDataError):
            node.invoke(context, lambda admitted: {"outcome": "completed"})
        broken = {
            **context,
            "data": {**context["data"], "expected_artifacts": "not-a-list"},
        }
        with self.assertRaises(TypedDataError):
            node.invoke(broken, launcher)
        with self.assertRaisesRegex(RuntimeError, "inspection only"):
            node.graph().invoke(context["data"])

    @verifies("scenario.execution.agent-node", "scenario.execution.graph-inspection")
    def test_native_plan_has_no_shadow_graph(self):
        from concorde.operations.graph_catalog import catalog

        self.assertNotIn("plan_graph", catalog())


class TerminalAgentGraphTests(unittest.TestCase):
    @verifies("scenario.execution.operation-state")
    def test_model_subgraph_projects_parent_state_and_preserves_unrelated_channels(
        self,
    ):
        node = OperationNode("planner")
        seen = []

        def launcher(value):
            seen.append(value)
            return {
                "context_id": value["data"]["snapshot"]["data"]["context_id"],
                "outcome": "completed",
                "answer": "Planned",
                "blockers": [],
                "documents": [],
                "plan": "The plan",
                "tasks": [],
            }

        from typing import TypedDict, cast

        class ParentState(TypedDict, total=False):
            snapshot: dict
            change_id: str | None
            expected_artifacts: list[str]
            plan: str
            private_parent_channel: str

        graph = StateGraph(ParentState, context_schema=OperationRuntimeContext)
        graph.add_node("plan", node.graph())
        graph.add_edge(START, "plan")
        graph.add_edge("plan", END)
        data = _stage_context()["data"]
        result = graph.compile().invoke(
            cast(ParentState, {**data, "private_parent_channel": "not admitted"}),
            context=OperationRuntimeContext(launcher=launcher),
        )
        self.assertEqual("The plan", result["plan"])
        self.assertEqual("not admitted", result["private_parent_channel"])
        self.assertEqual([typed(node.input_type, data)], seen)
        with self.assertRaises(RuntimeError):
            node.graph().invoke(data)  # State cannot supply the trusted launcher.

    def test_arbitrary_compatibility_names_do_not_register_operations(self):
        with self.assertRaises(SpecError) as refused:
            OperationNode("normalize_plan")
        self.assertEqual("unknown_agent", refused.exception.code)


if __name__ == "__main__":
    unittest.main()
