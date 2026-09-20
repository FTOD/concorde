"""A worker invocation is a LangGraph node whose typed state is the worker's task contract."""

import unittest

from concorde.planning.plan_graph import build_plan_graph
from concorde.harness.operation_node import OperationNode, state_schema, typed_state
from concorde.harness.worker_profile import worker_profile
from concorde.spec.typed_data import DATA_SCHEMAS, TypedDataError, typed
from concorde.spec.verification import verifies


def _stage_context():
    from concorde.harness.context import (
        PROTOCOL_PATHS,  # noqa: F401  (import keeps the fixture honest)
    )

    snapshot = {
        "context_id": "sha256:" + "3" * 64,
        "schema_version": 6,
        "target_id": "service.fixture",
        "kind": "module",
        "focus_id": None,
        "phase": "plan",
        "task": "Plan",
        "constraints": [],
        "protocol_binding": {"version": "7.0.0", "digest": "sha256:" + "4" * 64},
        "protocol": [],
        "spec_resolution": {
            "schema_version": 1,
            "registration": {
                "id": "service.fixture",
                "kind": "module",
                "title": "Fixture",
                "documents": ["specs/module.md"],
                "references": [],
                "parent": None,
                "uses": [],
                "files": [],
                "checks": [],
            },
            "query_id": "service.fixture",
            "query_kind": "module",
            "module_id": "service.fixture",
            "reading_entry": "specs/module.md",
            "documents": ["specs/module.md"],
            "references": [],
            "sources": [],
        },
        "instructions": "Fixture.",
        "stage_inputs": [],
        "implementation_entries": [],
        "implementation_files": [],
        "implementation_artifacts": [],
        "external_references": [],
        "workspace": {
            "kind": "unversioned",
            "current_worktree": "/fixture",
            "current_branch": None,
            "primary_worktree": None,
            "primary_branch": None,
            "change_id": None,
            "phase": None,
            "status": None,
            "outcome": None,
            "blockers": [],
            "components": [],
            "active_worktrees": [],
        },
    }
    return typed(
        "concorde-agent-stage-context",
        {
            "snapshot": typed("concorde-context-snapshot", snapshot),
            "change_id": None,
            "expected_artifacts": [],
        },
    )


class OperationNodeTests(unittest.TestCase):
    @verifies("scenario.harness.agent-node")
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
                agent = worker_profile(name)
                node = OperationNode(agent.name)
                self.assertEqual(
                    (agent.contract.context, agent.contract.result),
                    (node.input_type, node.result_type),
                )
                self.assertEqual(
                    set(DATA_SCHEMAS[node.input_type]["properties"]),
                    set(node.input_schema.__annotations__),
                )
                assert node.result_type is not None
                self.assertEqual(
                    set(DATA_SCHEMAS[node.result_type]["properties"]),
                    set(node.output_schema.__annotations__),
                )
                union = state_schema(node.input_type, node.result_type, name="S")
                self.assertEqual(
                    set(node.input_schema.__annotations__)
                    | set(node.output_schema.__annotations__),
                    set(union.__annotations__),
                )
                drawing = node.graph().get_graph()
                self.assertEqual({"__start__", name, "__end__"}, set(drawing.nodes))
        self.assertEqual(
            {"snapshot", "change_id", "expected_artifacts"},
            set(typed_state("concorde-agent-stage-context").__annotations__),
        )

    @verifies("scenario.harness.agent-node")
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

    @verifies("scenario.harness.agent-node", "scenario.harness.graph-inspection")
    def test_plan_graph_exposes_its_worker_nodes_for_inspection(self):
        graph = build_plan_graph(lambda name: lambda state: {})
        drawing = graph.get_graph(xray=True)
        names = set(drawing.nodes)
        self.assertTrue(
            any(name.endswith("author_plan:planner") for name in names), names
        )
        self.assertTrue(
            any(name.endswith("assess_context:context_assessor") for name in names),
            names,
        )


if __name__ == "__main__":
    unittest.main()
