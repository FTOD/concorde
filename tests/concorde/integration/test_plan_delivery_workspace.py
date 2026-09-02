import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.feature_workspace import create_feature_file
from tests.concorde.support.paths import CONTEXT_PROJECT, REPOSITORY_ROOT, TWO_LEVEL_PROJECT


ADAPTER = REPOSITORY_ROOT / "scripts/workspace.py"
REMOVED = {"workspace_kind", "feature_abstract", "feature_implementation", "feature_" + "directory", "feature_" + "design", "module_summary", "module_design", "contracts_dir", "parent_context"}


def run_phase(root: Path, feature: str, phase: str) -> dict:
    completed = subprocess.run([sys.executable, str(ADAPTER), "--project-root", str(root), "--feature-path", feature, "--phase", phase], cwd=root, check=True, capture_output=True, text=True)
    return json.loads(completed.stdout)


def hashes(root: Path, paths: tuple[str, ...]) -> dict[str, str]:
    return {path: hashlib.sha256((root / path).read_bytes()).hexdigest() for path in paths}


class PlanDeliveryWorkspaceIntegrationTests(unittest.TestCase):
    def test_plan_task_and_issue_phases_share_attempt_and_preserve_design_architecture(self):
        feature = "specs/example/features/001-deliver.md"
        authorities = (feature, "specs/example/architecture.md")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            shutil.copytree(CONTEXT_PROJECT, root)
            before = hashes(root, authorities)
            payloads = [run_phase(root, feature, phase) for phase in ("plan", "tasks", "taskstoissues")]
            self.assertEqual(hashes(root, authorities), before)
            for payload in payloads:
                self.assertEqual(payload["schema_version"], 12)
                self.assertEqual(payload["phase_root"], ".concorde/attempts/feature.example.deliver")
                self.assertEqual(payload["workspace"]["attempt_dir"], ".concorde/attempts/feature.example.deliver")
                self.assertTrue(REMOVED.isdisjoint(payload["workspace"]))

    def test_flat_related_features_replace_parent_and_sibling_context(self):
        feature = "specs/example/features/004-confirm-order.md"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            shutil.copytree(TWO_LEVEL_PROJECT, root)
            payload = run_phase(root, feature, "plan")
            related = payload["workspace"]["related_features"]
            self.assertEqual([item["feature_id"] for item in related], ["feature.example.checkout", "feature.example.checkout.authorize"])
            self.assertNotIn("Flat Feature Attempt", repr(related))
            self.assertNotIn("parent_context", payload["workspace"])

    def test_planning_uses_code_inventory_not_accepted_realization_narrative(self):
        feature = "specs/example/features/001-plan.md"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            selected = create_feature_file(root, feature, "feature.example.plan")
            source = root / "src/plan.py"
            source.parent.mkdir()
            source.write_text("def plan(): return True\n", encoding="utf-8")
            feature_before = selected.read_bytes()
            payload = run_phase(root, feature, "plan")
            self.assertEqual(payload["workspace"]["executable_context"]["source_roots"], ["src"])
            self.assertEqual(selected.read_bytes(), feature_before)
            self.assertTrue(selected.is_file())


if __name__ == "__main__":
    unittest.main()
