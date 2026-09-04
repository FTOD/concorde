from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import unittest

from tests.concorde.support.paths import REPOSITORY_ROOT, RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.capabilities.operation_runtime import OperationExecution  # noqa: E402


OPERATION_PATH = REPOSITORY_ROOT / "operations/concorde-reflections-triage/operation.py"
SPEC = importlib.util.spec_from_file_location("concorde_reflections_triage", OPERATION_PATH)
assert SPEC and SPEC.loader
reflections_triage = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = reflections_triage
SPEC.loader.exec_module(reflections_triage)


class ReflectionsTriageOperationIntegrationTests(unittest.TestCase):
    def run_graph(self, action: str, route: str | None = None):
        calls: list[OperationExecution] = []

        def execute(invocation: OperationExecution) -> str:
            calls.append(invocation)
            return f"prepared:{invocation.capability.name}"

        graph = reflections_triage.build_reflections_triage(
            execute,
            action=action,
            route=route,
            project_root=REPOSITORY_ROOT,
            integration="codex",
            framework_prefix="",
            nested_dispatcher=execute,
        )
        result = graph.invoke({"request": action, "capability_results": []})
        return calls, result

    def test_status_is_deterministic_and_launches_no_model_capability(self):
        calls, result = self.run_graph("status")
        self.assertEqual(calls, [])
        self.assertEqual(result["action"], "status")
        self.assertEqual(result["capability_results"], [])

    def test_close_is_deterministic_and_launches_no_model_capability(self):
        calls, result = self.run_graph("close")
        self.assertEqual(calls, [])
        self.assertEqual(result["action"], "close")
        self.assertEqual(result["capability_results"], [])

    def test_investigate_is_read_only_and_terminates_after_analyze(self):
        calls, _ = self.run_graph("investigate")
        self.assertEqual([call.capability.name for call in calls], ["concorde-analyze"])
        launch = calls[0].launch_specification
        self.assertEqual(launch.policy.write_paths, ())
        self.assertIn("scripts/workspace.py", launch.policy.read_paths)
        receipt = json.loads(launch.workspace_receipt_json)
        self.assertEqual(receipt["schema_version"], 13)
        self.assertEqual(receipt["source_digest"], launch.workspace_digest)
        self.assertIn(receipt["feature_path"], launch.policy.read_paths)

    def test_plan_route_uses_nested_public_planner_and_never_fast_loop(self):
        calls, _ = self.run_graph("implement", "plan")
        self.assertEqual(
            [call.capability.name for call in calls],
            [
                "concorde-analyze",
                "concorde-plan",
                "concorde-tasks",
                "concorde-implement",
                "concorde-validate",
            ],
        )
        self.assertNotIn("concorde-fast-loop", [call.capability.name for call in calls])
        planner = calls[1]
        self.assertEqual(planner.capability.kind, "operation")
        self.assertIsNone(planner.launch_specification)

    def test_fast_loop_route_is_conditional_and_implementer_is_worktree_scoped(self):
        calls, _ = self.run_graph("implement", "fast-loop")
        self.assertEqual(
            [call.capability.name for call in calls],
            ["concorde-analyze", "concorde-fast-loop", "concorde-validate"],
        )
        fast_loop = calls[1].launch_specification.policy
        self.assertTrue(any(".concorde/reflections/worktrees" in path for path in fast_loop.write_paths))
        self.assertFalse(any(path == "." for path in fast_loop.write_paths))

    def test_invalid_action_or_route_fails_before_executor(self):
        calls = []
        with self.assertRaisesRegex(ValueError, "unsupported reflection action"):
            reflections_triage.build_reflections_triage(
                lambda invocation: calls.append(invocation) or "ok",
                action="everything",
                project_root=REPOSITORY_ROOT,
            )
        with self.assertRaisesRegex(ValueError, "route"):
            reflections_triage.build_reflections_triage(
                lambda invocation: calls.append(invocation) or "ok",
                action="implement",
                route=None,
                project_root=REPOSITORY_ROOT,
            )
        self.assertEqual(calls, [])

    def test_operation_cli_and_markdown_pair_report_v5_conditionally(self):
        result = subprocess.run(
            [sys.executable, str(OPERATION_PATH), "status", "--describe-policy"],
            cwd=REPOSITORY_ROOT,
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["operation"], "concorde-reflections-triage")
        self.assertEqual(payload["action"], "status")
        self.assertEqual(payload["capabilities"], [])
        skill = OPERATION_PATH.with_name("SKILL.md").read_text(encoding="utf-8")
        self.assertIn("reflection-triage/v5", skill)
        self.assertIn("operation: operation.py", skill)
        self.assertIn("capabilities:", skill)
        self.assertIn("## Bucket layout", skill)
        self.assertIn("--relocate R-NNN", skill)
        self.assertIn("--remove-closed", skill)
        self.assertIn("`close", skill)


if __name__ == "__main__":
    unittest.main()
