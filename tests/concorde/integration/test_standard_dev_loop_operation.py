from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import unittest
from unittest import mock

from tests.concorde.support.paths import REPOSITORY_ROOT, RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.operation_runtime import (  # noqa: E402
    CapabilityResult,
    OperationDependencyError,
    OperationExecution,
    build_operation_graph,
    load_operation_bindings,
    load_operation_stages,
)
from concorde.skill_assets import load_skill_prompt  # noqa: E402


OPERATION_PATH = REPOSITORY_ROOT / "operations/concorde-standard-dev-loop/operation.py"
PLANNING_PROJECT = REPOSITORY_ROOT / "tests/concorde/fixtures/permission-planning-project"
PLANNING_FEATURE = "specs/example/modules/consumer/features/001-change.md"
SPEC = importlib.util.spec_from_file_location("concorde_standard_dev_loop", OPERATION_PATH)
assert SPEC and SPEC.loader
standard_dev_loop = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = standard_dev_loop
SPEC.loader.exec_module(standard_dev_loop)


class StandardDevLoopOperationIntegrationTests(unittest.TestCase):
    def build(self, executor):
        return standard_dev_loop.build_standard_dev_loop(
            executor,
            project_root=REPOSITORY_ROOT,
            integration="codex",
            framework_prefix="",
            nested_dispatcher=executor,
        )

    def test_real_langgraph_runs_direct_capabilities_and_prior_results(self):
        calls: list[OperationExecution] = []

        def execute(invocation: OperationExecution) -> str:
            calls.append(invocation)
            return f"completed:{invocation.capability.name}"

        result = self.build(execute).invoke(
            {"request": "Add audit logging", "capability_results": []}
        )
        self.assertEqual(
            [call.capability.name for call in calls],
            list(standard_dev_loop.OPERATION_CAPABILITIES),
        )
        self.assertEqual(
            [call.stage for call in calls],
            ["specify", "plan", "tasks", "tasks", "deliver", "deliver"],
        )
        self.assertEqual(
            [len(call.prior_results) for call in calls],
            [0, 1, 2, 3, 4, 5],
        )
        self.assertEqual(
            [item.capability for item in result["capability_results"]],
            list(standard_dev_loop.OPERATION_CAPABILITIES),
        )
        for call in calls:
            self.assertEqual(call.request, "Add audit logging")
            self.assertEqual(
                call.capability,
                load_skill_prompt(REPOSITORY_ROOT, call.capability.name, ""),
            )

    def test_nested_planner_is_one_opaque_public_outer_capability(self):
        calls: list[OperationExecution] = []

        def execute(invocation: OperationExecution) -> str:
            calls.append(invocation)
            return "ok"

        self.build(execute).invoke({"request": "nested", "capability_results": []})
        plan = [call for call in calls if call.stage == "plan"]
        self.assertEqual([call.capability.name for call in plan], ["concorde-plan"])
        self.assertEqual(plan[0].capability.kind, "operation")
        self.assertIsNone(plan[0].launch_specification)
        flattened = repr(standard_dev_loop.OPERATION_STAGES)
        self.assertNotIn("concorde-plan-context", flattened)
        self.assertNotIn("concorde-plan-author", flattened)

    def test_trusted_nested_dispatch_runs_inner_enforced_leaves_independently(self):
        outer_calls = []
        inner_calls = []

        def outer_execute(invocation: OperationExecution) -> str:
            outer_calls.append(invocation.capability.name)
            return "outer-ok"

        def inner_execute(invocation: OperationExecution) -> str:
            inner_calls.append(invocation)
            self.assertIsNotNone(invocation.launch_specification)
            return "inner-ok"

        def dispatch(invocation: OperationExecution) -> str:
            self.assertEqual(invocation.capability.name, "concorde-plan")
            return standard_dev_loop._dispatch_plan(
                invocation,
                inner_execute,
                project_root=PLANNING_PROJECT,
                feature_path=PLANNING_FEATURE,
                integration="codex",
                native_enforcement=True,
                outer_sandbox=None,
                framework_prefix="",
            )

        graph = standard_dev_loop.build_standard_dev_loop(
            outer_execute,
            project_root=PLANNING_PROJECT,
            feature_path=PLANNING_FEATURE,
            integration="codex",
            framework_prefix="",
            nested_dispatcher=dispatch,
        )
        result = graph.invoke({"request": "nested enforcement", "capability_results": []})
        self.assertEqual(
            outer_calls,
            [
                "concorde-specify",
                "concorde-tasks",
                "concorde-implement",
                "concorde-validate",
                "concorde-deliver",
            ],
        )
        self.assertEqual(
            [invocation.capability.name for invocation in inner_calls],
            ["concorde-plan-context", "concorde-plan-author"],
        )
        self.assertEqual(
            [item.capability for item in result["capability_results"]],
            list(standard_dev_loop.OPERATION_CAPABILITIES),
        )

    def test_each_leaf_receives_its_own_non_union_launch_policy(self):
        calls: list[OperationExecution] = []

        def execute(invocation: OperationExecution) -> str:
            calls.append(invocation)
            return "ok"

        self.build(execute).invoke({"request": "policies", "capability_results": []})
        tasks = next(call for call in calls if call.capability.name == "concorde-tasks")
        implement = next(call for call in calls if call.capability.name == "concorde-implement")
        self.assertIsNot(tasks.launch_specification, implement.launch_specification)
        self.assertNotEqual(
            tasks.launch_specification.policy.digest,
            implement.launch_specification.policy.digest,
        )
        self.assertTrue(
            set(tasks.launch_specification.policy.write_paths)
            < set(implement.launch_specification.policy.write_paths)
        )

    def test_installed_prefix_is_resolved_per_direct_capability(self):
        seen: dict[str, str] = {}

        def execute(invocation: OperationExecution) -> str:
            seen[invocation.capability.name] = invocation.capability.body
            return "ok"

        graph = standard_dev_loop.build_standard_dev_loop(
            execute,
            project_root=REPOSITORY_ROOT,
            integration="claude",
            framework_prefix=".concorde/framework",
            nested_dispatcher=execute,
        )
        graph.invoke({"request": "installed", "capability_results": []})
        self.assertIn(
            "python3 .concorde/framework/scripts/workspace.py --phase specify",
            seen["concorde-specify"],
        )
        self.assertIn(
            "python3 .concorde/framework/scripts/run-operation.py "
            ".concorde/framework/operations/concorde-plan/operation.py",
            seen["concorde-plan"],
        )

    def test_runnable_operation_describes_direct_capabilities_without_model_launch(self):
        result = subprocess.run(
            [
                sys.executable,
                str(OPERATION_PATH),
                "Add audit logging",
                "--integration",
                "codex",
                "--describe-policy",
            ],
            cwd=REPOSITORY_ROOT,
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["operation"], "concorde-standard-dev-loop")
        self.assertEqual(
            [item["capability"] for item in payload["capabilities"]],
            list(standard_dev_loop.OPERATION_CAPABILITIES),
        )
        self.assertTrue(all("policy" in item for item in payload["capabilities"] if item["kind"] == "skill"))

    def test_plan_failure_is_observable_and_prevents_downstream_capabilities(self):
        calls: list[str] = []

        def execute(invocation: OperationExecution) -> str:
            calls.append(invocation.capability.name)
            if invocation.capability.name == "concorde-plan":
                raise RuntimeError("plan failed")
            return "ok"

        with self.assertRaisesRegex(RuntimeError, "plan failed"):
            self.build(execute).invoke({"request": "failure", "capability_results": []})
        self.assertEqual(calls, ["concorde-specify", "concorde-plan"])

    def test_missing_langgraph_and_prepopulated_results_fail_before_execution(self):
        real_import = __import__

        def without_langgraph(name, *args, **kwargs):
            if name == "langgraph.graph":
                raise ModuleNotFoundError("No module named 'langgraph'", name="langgraph")
            return real_import(name, *args, **kwargs)

        with mock.patch("builtins.__import__", side_effect=without_langgraph):
            with self.assertRaisesRegex(OperationDependencyError, r"langgraph>=1\.2,<2"):
                self.build(lambda invocation: "ok")

        calls = []
        graph = self.build(lambda invocation: calls.append(invocation) or "ok")
        with self.assertRaisesRegex(ValueError, "no capability results"):
            graph.invoke(
                {
                    "request": "ambiguous resume",
                    "capability_results": [
                        CapabilityResult(
                            operation="prior",
                            stage="prior",
                            occurrence=0,
                            capability="concorde-prior",
                            output="stale",
                        )
                    ],
                }
            )
        self.assertEqual(calls, [])

    def test_missing_leaf_factory_nested_dispatcher_or_immutable_launch_fails_before_executor(self):
        calls = []
        stages = load_operation_stages(
            REPOSITORY_ROOT,
            (("specify", ("concorde-specify",)),),
            framework_prefix="",
        )
        bindings = load_operation_bindings(
            stages,
            (("specify", 0, "concorde-specify", "specifier"),),
        )
        with self.assertRaisesRegex(ValueError, "non-null enforcement launch factory"):
            build_operation_graph(
                "concorde-test",
                stages,
                bindings,
                lambda invocation: calls.append(invocation) or "ok",
            )
        self.assertEqual(calls, [])

        graph = build_operation_graph(
            "concorde-test",
            stages,
            bindings,
            lambda invocation: calls.append(invocation) or "ok",
            launch_factory=lambda invocation: None,
        )
        with self.assertRaisesRegex(TypeError, "frozen immutable launch specification"):
            graph.invoke({"request": "missing enforcement", "capability_results": []})
        self.assertEqual(calls, [])

        with self.assertRaisesRegex(ValueError, "explicit enforcing dispatcher"):
            standard_dev_loop.build_standard_dev_loop(
                lambda invocation: calls.append(invocation) or "ok",
                project_root=REPOSITORY_ROOT,
                integration="codex",
                framework_prefix="",
                nested_dispatcher=None,
            )
        self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()
