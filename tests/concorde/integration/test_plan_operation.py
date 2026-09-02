from __future__ import annotations

import hashlib
import importlib.util
import sys
import unittest
from pathlib import Path

from tests.concorde.support.paths import REPOSITORY_ROOT, RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.operation_runtime import OperationExecution  # noqa: E402


OPERATION_PATH = REPOSITORY_ROOT / "operations/concorde-plan/operation.py"
SPEC = importlib.util.spec_from_file_location("concorde_plan_operation", OPERATION_PATH)
assert SPEC and SPEC.loader
plan_operation = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = plan_operation
SPEC.loader.exec_module(plan_operation)

PROJECT = REPOSITORY_ROOT / "tests/concorde/fixtures/permission-planning-project"
SELECTED = "specs/example/modules/consumer/features/001-change.md"


def durable_hashes(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
        and not path.relative_to(root).as_posix().startswith(".concorde/attempts/")
        and path.relative_to(root).as_posix() != ".concorde/reflections/log.md"
    }


class PlanOperationIntegrationTests(unittest.TestCase):
    def test_real_langgraph_runs_context_then_author_with_distinct_policies(self):
        calls: list[OperationExecution] = []
        before = durable_hashes(PROJECT)

        def execute(invocation: OperationExecution) -> str:
            calls.append(invocation)
            return f"completed:{invocation.capability.name}"

        graph = plan_operation.build_plan_operation(
            execute,
            project_root=PROJECT,
            feature_path=SELECTED,
            integration="codex",
            framework_prefix="",
        )
        result = graph.invoke({"request": "Plan bounded change", "capability_results": []})

        self.assertEqual(
            [call.capability.name for call in calls],
            ["concorde-plan-context", "concorde-plan-author"],
        )
        self.assertEqual([call.stage for call in calls], ["context", "author"])
        self.assertEqual(calls[0].prior_results, ())
        self.assertEqual(
            [item.capability for item in calls[1].prior_results],
            ["concorde-plan-context"],
        )
        self.assertEqual(calls[0].launch_specification.policy.write_paths, ())
        self.assertEqual(
            set(calls[1].launch_specification.policy.write_paths),
            {
                ".concorde/attempts/feature.example.consumer.change",
                ".concorde/reflections/log.md",
            },
        )
        self.assertEqual(
            [item.capability for item in result["capability_results"]],
            ["concorde-plan-context", "concorde-plan-author"],
        )
        self.assertEqual(durable_hashes(PROJECT), before)

    def test_context_failure_prevents_author(self):
        calls = []

        def fail_context(invocation: OperationExecution) -> str:
            calls.append(invocation.capability.name)
            raise RuntimeError("context failed")

        graph = plan_operation.build_plan_operation(
            fail_context,
            project_root=PROJECT,
            feature_path=SELECTED,
            integration="claude",
            framework_prefix="",
        )
        with self.assertRaisesRegex(RuntimeError, "context failed"):
            graph.invoke({"request": "Plan bounded change", "capability_results": []})
        self.assertEqual(calls, ["concorde-plan-context"])

    def test_literal_topology_and_public_pair_are_exact(self):
        self.assertEqual(
            plan_operation.OPERATION_CAPABILITIES,
            ("concorde-plan-context", "concorde-plan-author"),
        )
        self.assertEqual(
            plan_operation.OPERATION_STAGES,
            (
                ("context", ("concorde-plan-context",)),
                ("author", ("concorde-plan-author",)),
            ),
        )
        skill = OPERATION_PATH.with_name("SKILL.md").read_text(encoding="utf-8")
        self.assertIn("capabilities:\n  - concorde-plan-context\n  - concorde-plan-author", skill)
        self.assertNotIn("skills/concorde-plan/SKILL.md", skill)


if __name__ == "__main__":
    unittest.main()
