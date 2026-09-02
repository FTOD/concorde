import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.feature_workspace import attempt_path, create_feature_file
from tests.concorde.support.paths import CONTEXT_PROJECT, REPOSITORY_ROOT, TWO_LEVEL_PROJECT


ADAPTER = REPOSITORY_ROOT / "scripts/workspace.py"


def run_phase(root: Path, feature: str, phase: str) -> dict:
    completed = subprocess.run([sys.executable, str(ADAPTER), "--project-root", str(root), "--feature-path", feature, "--phase", phase], cwd=root, check=True, capture_output=True, text=True)
    return json.loads(completed.stdout)


def hashes(root: Path, paths: tuple[str, ...]) -> dict[str, str]:
    return {path: hashlib.sha256((root / path).read_bytes()).hexdigest() for path in paths}


class ExecuteReconcileWorkspaceIntegrationTests(unittest.TestCase):
    def test_execute_analysis_and_convergence_share_one_protocol_twelve_attempt(self):
        feature = "specs/example/features/001-deliver.md"
        authorities = (feature, "specs/example/architecture.md")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            shutil.copytree(CONTEXT_PROJECT, root)
            before = hashes(root, authorities)
            payloads = [run_phase(root, feature, phase) for phase in ("implement", "analyze", "converge")]
            self.assertEqual(hashes(root, authorities), before)
            for payload in payloads:
                self.assertEqual(payload["schema_version"], 12)
                self.assertEqual(payload["phase_root"], ".concorde/attempts/feature.example.deliver")
                self.assertNotIn("feature_implementation", payload["workspace"])

    def test_related_flat_feature_summaries_are_bounded_during_execution(self):
        feature = "specs/example/features/004-confirm-order.md"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            shutil.copytree(TWO_LEVEL_PROJECT, root)
            payload = run_phase(root, feature, "implement")
            summaries = payload["workspace"]["related_features"]
            self.assertEqual([item["feature_id"] for item in summaries], ["feature.example.checkout", "feature.example.checkout.authorize"])
            self.assertNotIn("attempt", repr(summaries).lower())

    def test_task_and_evidence_writes_leave_design_architecture_and_code_unchanged(self):
        feature = "specs/example/features/001-execute.md"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            selected = create_feature_file(root, feature, "feature.example.execute")
            source = root / "src/fixture.py"
            source.parent.mkdir()
            source.write_text("VALUE = 1\n", encoding="utf-8")
            authorities = (feature, "specs/example/architecture.md", "src/fixture.py")
            before = hashes(root, authorities)
            attempt = attempt_path(selected)
            attempt.mkdir(parents=True)
            (attempt / "tasks.md").write_text("# Tasks\n\n- [X] T001 Execute fixture\n", encoding="utf-8")
            (attempt / "validation.md").write_text("# Validation\n\n### T001\n\n- **Outcome**: passed\n", encoding="utf-8")
            self.assertEqual(hashes(root, authorities), before)
            payload = run_phase(root, feature, "implement")
            self.assertEqual(payload["workspace"]["attempt_state"], "complete")
            self.assertTrue(selected.is_file())


if __name__ == "__main__":
    unittest.main()
