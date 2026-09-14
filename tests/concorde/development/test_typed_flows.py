"""The development and specify Flows carry typed state and route with Commands."""
import unittest

from langgraph.types import Command

from concorde.development.loop_flow import (DevelopmentState, build_loop_flow, loop_destinations,
                                            loop_successors, merge_artifacts, stage_command)
from concorde.development.specify_flow import build_specify_flow
from concorde.spec.verification import verifies


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
