from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

from tests.concorde.support.paths import REPOSITORY_ROOT, RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.operation_runtime import OperationExecution  # noqa: E402


OPERATION_PATH = REPOSITORY_ROOT / "operations/concorde-reflections-triage/operation.py"
SPEC = importlib.util.spec_from_file_location("concorde_reflections_triage", OPERATION_PATH)
assert SPEC and SPEC.loader
reflections_triage = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = reflections_triage
SPEC.loader.exec_module(reflections_triage)


class ReflectionsTriageOperationIntegrationTests(unittest.TestCase):
    def test_real_graph_composes_leaf_skills_in_declared_stage_order(self):
        calls: list[OperationExecution] = []

        def execute(invocation: OperationExecution) -> str:
            calls.append(invocation)
            return f"prepared:{invocation.stage.name}"

        graph = reflections_triage.build_reflections_triage(execute, framework_prefix="")
        result = graph.invoke({"request": "status", "stage_results": []})
        self.assertEqual(
            [call.stage.name for call in calls],
            ["investigate", "route", "implement", "validate"],
        )
        self.assertEqual(
            [skill.name for call in calls for skill in call.stage.skills],
            list(reflections_triage.OPERATION_SKILLS),
        )
        self.assertEqual([item.stage for item in result["stage_results"]], [
            "investigate", "route", "implement", "validate",
        ])

    def test_operation_cli_and_markdown_pair_report_v4(self):
        result = subprocess.run(
            [sys.executable, str(OPERATION_PATH), "status"],
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["operation"], "concorde-reflections-triage")
        self.assertEqual([stage["stage"] for stage in payload["stages"]], [
            "investigate", "route", "implement", "validate",
        ])
        skill = OPERATION_PATH.with_name("SKILL.md").read_text(encoding="utf-8")
        self.assertIn("reflection-triage/v4", skill)
        self.assertIn("operation: operation.py", skill)


if __name__ == "__main__":
    unittest.main()
