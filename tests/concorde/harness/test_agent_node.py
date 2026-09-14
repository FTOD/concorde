"""An Agent invocation is a LangGraph node whose typed state is the selected Mode's contract."""
import unittest

from langgraph.types import Command

from concorde.development.loop_flow import (DevelopmentState, build_loop_flow, loop_destinations,
                                            loop_successors, merge_artifacts, stage_command)
from concorde.development.plan_flow import build_plan_flow
from concorde.development.specify_flow import build_specify_flow
from concorde.harness.agent_model import agent_definition
from concorde.harness.agent_node import AgentNode, state_schema, typed_state
from concorde.spec.typed_data import DATA_SCHEMAS, TypedDataError, typed
from concorde.spec.verification import verifies


def _stage_context():
    from concorde.harness.context import PROTOCOL_PATHS  # noqa: F401  (import keeps the fixture honest)
    snapshot = {
        "context_id": "sha256:" + "3" * 64, "schema_version": 3, "target_id": "service.fixture",
        "kind": "module", "focus_id": None, "phase": "plan", "task": "Plan", "constraints": [],
        "protocol_binding": {"version": "5.1.0", "digest": "sha256:" + "4" * 64}, "protocol": [],
        "spec_resolution": {"query_id": "service.fixture", "query_kind": "module", "module_id": "service.fixture",
                            "documents": ["specs/fixture.md"], "references": [], "sources": []},
        "instructions": "Fixture.", "stage_inputs": [], "implementation_entries": [],
        "implementation_files": [], "implementation_artifacts": [],
        "documentation_entries": [], "documentation_artifacts": [],
        "workspace": {"kind": "unversioned", "current_worktree": "/fixture", "current_branch": None,
                      "primary_worktree": None, "primary_branch": None, "change_id": None, "phase": None,
                      "status": None, "outcome": None, "gaps": [], "components": [], "active_worktrees": []},
    }
    return typed("concorde-agent-stage-context", {"snapshot": typed("concorde-context-snapshot", snapshot),
                                                  "change_id": None, "expected_artifacts": []})


class AgentNodeTests(unittest.TestCase):
    @verifies("scenario.harness.agent-node")
    def test_node_schemas_are_exactly_the_mode_contract_fields(self):
        for agent, mode in (("spec_engineer", "plan"), ("programmer", "code-review"), ("coordinator", "route"),
                            ("spec_engineer", "topology-author")):
            with self.subTest(agent=agent, mode=mode):
                node = AgentNode.select(agent_definition(agent), mode)
                self.assertEqual(set(DATA_SCHEMAS[node.input_type]["properties"]),
                                 set(node.input_schema.__annotations__))
                self.assertEqual(set(DATA_SCHEMAS[node.result_type]["properties"]),
                                 set(node.output_schema.__annotations__))
                union = state_schema(node.input_type, node.result_type, name="S")
                self.assertEqual(set(node.input_schema.__annotations__) | set(node.output_schema.__annotations__),
                                 set(union.__annotations__))
                drawing = node.flow().get_graph()
                self.assertEqual({"__start__", agent, "__end__"}, set(drawing.nodes))
        self.assertEqual({"snapshot", "change_id", "expected_artifacts"},
                         set(typed_state("concorde-agent-stage-context").__annotations__))

    @verifies("scenario.harness.agent-node")
    def test_invocation_validates_context_in_and_result_out(self):
        node = AgentNode.select(agent_definition("spec_engineer"), "plan")
        context = _stage_context()
        seen = []

        def launcher(admitted):
            seen.append(admitted)
            return {"context_id": admitted["data"]["snapshot"]["data"]["context_id"], "outcome": "completed",
                    "answer": "Planned.", "gaps": [], "documents": [], "plan": "Do the work.", "tasks": [],
                    "reflection_findings": []}
        data = node.invoke(context, launcher)
        self.assertEqual("Do the work.", data["plan"])
        self.assertEqual([context], seen)
        with self.assertRaises(TypedDataError):
            node.invoke(context, lambda admitted: {"outcome": "completed"})
        broken = {**context, "data": {**context["data"], "expected_artifacts": "not-a-list"}}
        with self.assertRaises(TypedDataError):
            node.invoke(broken, launcher)
        with self.assertRaisesRegex(RuntimeError, "inspection only"):
            node.flow().invoke(context["data"])

    @verifies("scenario.harness.agent-node", "scenario.harness.flow-inspection")
    def test_plan_flow_exposes_its_agent_nodes_for_inspection(self):
        flow = build_plan_flow(lambda name: (lambda state: {}))
        drawing = flow.get_graph(xray=True)
        names = set(drawing.nodes)
        self.assertTrue(any(name.endswith("author_plan:spec_engineer") for name in names), names)
        self.assertTrue(any(name.endswith("assess_context:spec_engineer") for name in names), names)


class TypedFlowStateTests(unittest.TestCase):
    @verifies("scenario.development.flow-execution")
    def test_artifact_reducer_keeps_the_newest_reference_per_id_in_order(self):
        current = [{"id": "review.a.spec", "path": "old"}, {"id": "plan", "path": "p"}]
        update = [{"id": "review.a.spec", "path": "new"}, {"id": "review.b.code", "path": "b"}]
        self.assertEqual([{"id": "review.a.spec", "path": "new"}, {"id": "plan", "path": "p"},
                          {"id": "review.b.code", "path": "b"}], merge_artifacts(current, update))
        self.assertEqual({"route", "output", "result", "artifacts"}, set(DevelopmentState.__annotations__))

    @verifies("scenario.development.flow-execution")
    def test_stage_commands_select_declared_destinations_and_stops_summarize(self):
        successors = loop_successors(include_specify=True, entry="plan", has_code=True)
        self.assertEqual(("tasks", "summarize", "__end__"), loop_destinations("review_code", successors, dynamic=True)[1:])
        self.assertIn("tasks", loop_destinations("review_code", successors, dynamic=True))
        self.assertEqual(("plan", "tasks", "implement", "validate", "summarize", "__end__"),
                         loop_destinations("specify_loop", successors, dynamic=True))
        command = stage_command("__end__", output={"outcome": "failed"}, artifacts=[])
        self.assertIsInstance(command, Command)
        self.assertEqual(("summarize", {"output": {"outcome": "failed"}, "artifacts": []}),
                         (command.goto, command.update))
        self.assertEqual("tasks", stage_command("tasks", output={}).goto)

    @verifies("scenario.development.flow-execution")
    def test_loop_and_specify_flows_run_on_commands_and_accumulate_artifacts(self):
        visited = []

        def loop_node(name):
            def node(state):
                visited.append(name)
                if name == "initialize":
                    return Command(goto="specify_loop")
                if name == "summarize":
                    return {"output": {"final": True, "artifacts": state["artifacts"]}}
                if name == "ready":
                    return Command(goto="summarize", update={"output": {"outcome": "ready", "artifacts": []}})
                route = {"specify_loop": "plan", "plan": "tasks", "tasks": "implement", "implement": "validate",
                         "validate": "review_code", "review_code": "ready"}[name]
                return stage_command(route, output={"outcome": "completed", "artifacts": []},
                                     artifacts=[{"id": f"review.{name}", "path": name}])
            return node
        result = build_loop_flow(loop_node, dynamic=True).invoke({"output": {}, "artifacts": []},
                                                                 {"recursion_limit": 50})
        self.assertEqual(["initialize", "specify_loop", "plan", "tasks", "implement", "validate", "review_code",
                          "ready", "summarize"], visited)
        self.assertEqual([f"review.{name}" for name in ("specify_loop", "plan", "tasks", "implement", "validate",
                                                          "review_code")],
                         [item["id"] for item in result["output"]["artifacts"]])

        seen = []

        def specify_node(name):
            def node(state):
                seen.append(name)
                if name == "initialize":
                    return Command(goto="review_spec")
                if name == "summarize":
                    return {"output": {"artifacts": state["artifacts"]}}
                return Command(goto="summarize", update={"output": {"outcome": "completed"},
                                                         "artifacts": [{"id": "review.x.spec", "path": "x"}]})
            return node
        outcome = build_specify_flow(specify_node).invoke({"output": {}, "artifacts": []})
        self.assertEqual(["initialize", "review_spec", "summarize"], seen)
        self.assertEqual(["review.x.spec"], [item["id"] for item in outcome["output"]["artifacts"]])


if __name__ == "__main__":
    unittest.main()
