from __future__ import annotations

import json
import subprocess
import sys
import unittest
from unittest import mock
from pathlib import Path

from tests.concorde.support.paths import REPOSITORY_ROOT, RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.command_assets import load_command_prompt  # noqa: E402
from concorde.workflows import (  # noqa: E402
    STANDARD_DEV_LOOP,
    StageExecution,
    StageResult,
    WorkflowDependencyError,
    build_standard_dev_loop,
    load_workflow_stages,
)


class StandardDevLoopIntegrationTests(unittest.TestCase):
    def test_real_langgraph_runs_exact_stages_prompts_and_prior_results(self):
        calls: list[StageExecution] = []

        def execute(invocation: StageExecution) -> str:
            calls.append(invocation)
            return f"completed:{invocation.stage.name}"

        graph = build_standard_dev_loop(REPOSITORY_ROOT, execute, framework_prefix="")
        result = graph.invoke({"request": "Add audit logging", "stage_results": []})

        self.assertEqual([call.stage.name for call in calls], ["specify", "plan", "tasks", "deliver"])
        self.assertEqual(
            [[prompt.command_id for prompt in call.stage.prompts] for call in calls],
            [
                ["concorde.specify"],
                ["concorde.plan"],
                ["concorde.tasks", "concorde.implement"],
                ["concorde.validate", "concorde.deliver"],
            ],
        )
        self.assertEqual(
            [prompt.command_id for call in calls for prompt in call.stage.prompts],
            [
                "concorde.specify",
                "concorde.plan",
                "concorde.tasks",
                "concorde.implement",
                "concorde.validate",
                "concorde.deliver",
            ],
        )
        for call in calls:
            self.assertEqual(call.request, "Add audit logging")
            for prompt in call.stage.prompts:
                expected = load_command_prompt(REPOSITORY_ROOT, prompt.command_id, "")
                self.assertEqual(prompt, expected)
        self.assertEqual(
            [[prior.stage for prior in call.prior_results] for call in calls],
            [[], ["specify"], ["specify", "plan"], ["specify", "plan", "tasks"]],
        )
        self.assertEqual(
            [(item.stage, item.output) for item in result["stage_results"]],
            [
                ("specify", "completed:specify"),
                ("plan", "completed:plan"),
                ("tasks", "completed:tasks"),
                ("deliver", "completed:deliver"),
            ],
        )

    def test_stage_definitions_are_reusable_and_invocations_do_not_leak_state(self):
        stages = load_workflow_stages(REPOSITORY_ROOT, STANDARD_DEV_LOOP, framework_prefix="")
        self.assertEqual(tuple(stage.name for stage in stages), ("specify", "plan", "tasks", "deliver"))

        calls: list[tuple[str, tuple[str, ...]]] = []

        def execute(invocation: StageExecution) -> str:
            calls.append((invocation.request, tuple(result.stage for result in invocation.prior_results)))
            return invocation.request

        graph = build_standard_dev_loop(REPOSITORY_ROOT, execute, framework_prefix="")
        first = graph.invoke({"request": "first", "stage_results": []})
        second = graph.invoke({"request": "second", "stage_results": []})
        self.assertEqual(len(first["stage_results"]), 4)
        self.assertEqual(len(second["stage_results"]), 4)
        self.assertEqual([item.output for item in first["stage_results"]], ["first"] * 4)
        self.assertEqual([item.output for item in second["stage_results"]], ["second"] * 4)
        self.assertEqual(calls[4], ("second", ()))

    def test_installed_prefix_is_resolved_inside_every_stage_prompt(self):
        seen: dict[str, tuple[str, ...]] = {}

        def execute(invocation: StageExecution) -> str:
            seen[invocation.stage.name] = tuple(prompt.body for prompt in invocation.stage.prompts)
            return "ok"

        graph = build_standard_dev_loop(
            REPOSITORY_ROOT,
            execute,
            framework_prefix=".concorde/framework",
        )
        graph.invoke({"request": "installed", "stage_results": []})
        self.assertIn(
            "python3 .concorde/framework/scripts/workspace.py --phase specify",
            seen["specify"][0],
        )
        self.assertIn(
            "python3 .concorde/framework/scripts/concorde.py validate",
            seen["deliver"][0],
        )
        self.assertNotIn(str(REPOSITORY_ROOT), "\n".join(body for bodies in seen.values() for body in bodies))

    def test_runnable_example_reports_the_real_four_stage_graph(self):
        result = subprocess.run(
            [sys.executable, str(REPOSITORY_ROOT / "examples/standard_dev_loop.py"), "Add audit logging"],
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["request"], "Add audit logging")
        self.assertEqual(
            [stage["stage"] for stage in payload["stages"]],
            ["specify", "plan", "tasks", "deliver"],
        )
        self.assertEqual(
            [command for stage in payload["stages"] for command in stage["prompts"]],
            [
                "concorde.specify",
                "concorde.plan",
                "concorde.tasks",
                "concorde.implement",
                "concorde.validate",
                "concorde.deliver",
            ],
        )
        self.assertEqual(payload["stages"][-1]["prior_stages"], ["specify", "plan", "tasks"])

    def test_plan_failure_is_observable_and_prevents_downstream_stages(self):
        calls: list[str] = []

        def execute(invocation: StageExecution) -> str:
            calls.append(invocation.stage.name)
            if invocation.stage.name == "plan":
                raise RuntimeError("plan failed")
            return "ok"

        graph = build_standard_dev_loop(REPOSITORY_ROOT, execute, framework_prefix="")
        with self.assertRaisesRegex(RuntimeError, "plan failed"):
            graph.invoke({"request": "failure", "stage_results": []})
        self.assertEqual(calls, ["specify", "plan"])

    def test_missing_langgraph_has_a_named_optional_dependency_error(self):
        real_import = __import__

        def without_langgraph(name, *args, **kwargs):
            if name == "langgraph.graph":
                raise ModuleNotFoundError("No module named 'langgraph'", name="langgraph")
            return real_import(name, *args, **kwargs)

        with mock.patch("builtins.__import__", side_effect=without_langgraph):
            with self.assertRaisesRegex(WorkflowDependencyError, r"langgraph>=1\.2,<2"):
                build_standard_dev_loop(REPOSITORY_ROOT, lambda invocation: "ok", framework_prefix="")

    def test_prepopulated_results_are_rejected_before_the_first_executor_call(self):
        calls: list[str] = []

        def execute(invocation: StageExecution) -> str:
            calls.append(invocation.stage.name)
            return "ok"

        graph = build_standard_dev_loop(REPOSITORY_ROOT, execute, framework_prefix="")
        with self.assertRaisesRegex(ValueError, "must start with no stage results"):
            graph.invoke(
                {
                    "request": "ambiguous resume",
                    "stage_results": [StageResult(stage="prior", output="stale")],
                }
            )
        self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()
