import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import CONTEXT_PROJECT, REPOSITORY_ROOT


REMOVED = {"workspace_kind", "feature_abstract", "feature_implementation", "feature_" + "directory", "feature_" + "design", "module_summary", "module_design", "contracts_dir", "diagrams_dir", "parent_context"}


class AttemptWorkspaceIntegration(unittest.TestCase):
    def run_adapter(self, root: Path, phase: str, feature: str, persist: bool = False, feature_id: str | None = None) -> dict:
        command = [sys.executable, str(REPOSITORY_ROOT / "extensions/concorde/scripts/python/workspace.py"), "--project-root", str(root), "--phase", phase, "--feature-path", feature]
        if feature_id is not None:
            command.extend(["--feature-id", feature_id])
        if persist:
            command.append("--persist")
        completed = subprocess.run(
            command,
            cwd=REPOSITORY_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        return json.loads(completed.stdout)

    def test_adapter_emits_workspace_protocol_twelve_without_removed_authorities(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            shutil.copytree(CONTEXT_PROJECT, root)
            feature = "specs/example/modules/api/features/001-invoke.md"
            payload = self.run_adapter(root, "plan", feature)
            workspace = payload["workspace"]
            self.assertEqual(payload["schema_version"], 12)
            self.assertEqual(payload["phase_root"], ".concorde/attempts/feature.example.api.invoke")
            self.assertEqual(workspace["feature_path"], feature)
            self.assertEqual(workspace["module_architecture"], "specs/example/modules/api/architecture.md")
            self.assertEqual([item["module_id"] for item in workspace["module_ancestry"]], ["module.example"])
            self.assertTrue(REMOVED.isdisjoint(workspace))

    def test_specify_routes_an_absent_flat_feature_to_its_module(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            shutil.copytree(CONTEXT_PROJECT, root)
            feature = "specs/example/modules/api/features/002-observe-health.md"
            payload = self.run_adapter(root, "specify", feature, persist=True)
            self.assertEqual(payload["phase_root"], feature)
            self.assertEqual(payload["workspace"]["providing_module"], "module.example.api")
            self.assertEqual(payload["workspace"]["attempt_state"], "unresolved")
            self.assertIsNone(payload["workspace"]["attempt_dir"])
            self.assertFalse((root / feature).exists())
            self.assertEqual(json.loads((root / ".specify/feature.json").read_text(encoding="utf-8")), {"feature_path": feature})

            preflight = self.run_adapter(
                root,
                "specify",
                feature,
                feature_id="feature.example.api.observe-health",
            )
            self.assertEqual(preflight["workspace"]["attempt_state"], "absent")
            self.assertEqual(
                preflight["workspace"]["attempt_dir"],
                ".concorde/attempts/feature.example.api.observe-health",
            )


if __name__ == "__main__":
    unittest.main()
