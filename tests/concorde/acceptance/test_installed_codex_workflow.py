import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.contract.test_installed_command_surfaces import _builder
from tests.concorde.support.catalog_server import CatalogServer
from tests.concorde.support.feature_workspace import write_complete_attempt
from tests.concorde.support.installed_command_surface import (
    CONCORDE_COMMANDS,
    CONCORDE_RUNTIME_COMMANDS,
    registered_artifact,
)
from tests.concorde.support.paths import TWO_LEVEL_PROJECT
from tests.concorde.support.specify_project import SpecifyProject


FEATURE = "specs/example/features/003-authorize-payment.md"
ATTEMPT = ".concorde/attempts/feature.example.checkout.authorize"


class InstalledCodexWorkflowTests(unittest.TestCase):
    def test_five_surfaces_preserve_four_runtime_operations_and_cleanup_delivery(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            dist = base / "dist"
            server = CatalogServer(dist)
            _builder.build_release(dist, server.base_url)
            with server:
                root = base / "target"
                project = SpecifyProject(root)
                project.initialize()
                project.register_catalogs(server.base_url)
                project.run("bundle", "install", "concorde-bundle")
                shutil.copytree(TWO_LEVEL_PROJECT / ".concorde", root / ".concorde", dirs_exist_ok=True)
                shutil.copytree(TWO_LEVEL_PROJECT / "specs", root / "specs", dirs_exist_ok=True)
                (root / ".specify/feature.json").write_text(
                    json.dumps({"feature_path": FEATURE}, separators=(",", ":")) + "\n",
                    encoding="utf-8",
                )

                self.assertEqual(
                    len({registered_artifact(root, "codex", command) for command in CONCORDE_COMMANDS}),
                    5,
                )
                self.assertEqual(len(CONCORDE_RUNTIME_COMMANDS), 4)

                workspace_adapter = root / ".specify/extensions/concorde/scripts/python/workspace.py"
                checklist_paths = subprocess.run(
                    [sys.executable, str(workspace_adapter), "--project-root", str(root), "--phase", "checklist"],
                    cwd=root,
                    text=True,
                    capture_output=True,
                    check=True,
                )
                payload = json.loads(checklist_paths.stdout)
                self.assertEqual(payload["schema_version"], 12)
                workspace = payload["workspace"]
                self.assertEqual(workspace["feature_id"], "feature.example.checkout.authorize")
                self.assertEqual(workspace["feature_path"], FEATURE)
                self.assertEqual(workspace["module_architecture"], "specs/example/architecture.md")
                self.assertEqual(workspace["module_ancestry"], [])
                self.assertEqual(workspace["checklists_dir"], workspace["attempt_dir"] + "/checklists")
                for removed in (
                    "feature_directory", "feature_design", "workspace_kind", "feature_abstract",
                    "feature_implementation", "module_summary", "module_design", "contracts_dir", "parent_context",
                ):
                    self.assertNotIn(removed, workspace)

                launcher = root / ".specify/extensions/concorde/scripts/python/concorde.py"
                for arguments in (("validate",), ("context", "module.example")):
                    result = subprocess.run(
                        [sys.executable, str(launcher), "--project-root", str(root), *arguments],
                        cwd=root,
                        text=True,
                        capture_output=True,
                    )
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    self.assertEqual(json.loads(result.stdout)["status"], "success")

                feature_path = root / FEATURE
                attempt = write_complete_attempt(feature_path)
                design = feature_path
                architecture = root / "specs/example/architecture.md"
                retained_before = {path: path.read_bytes() for path in (design, architecture)}

                proposed = subprocess.run(
                    [sys.executable, str(launcher), "--project-root", str(root), "deliver", "--propose"],
                    cwd=root,
                    text=True,
                    capture_output=True,
                )
                self.assertEqual(proposed.returncode, 0, proposed.stdout + proposed.stderr)
                delivery = json.loads(proposed.stdout)
                self.assertEqual(delivery["status"], "eligible")
                self.assertEqual(delivery["proposal_version"], 8)
                self.assertEqual(delivery["schema_version"], 12)
                self.assertEqual(delivery["task_summary"], {"complete": 1, "incomplete": 0, "malformed": 0})
                self.assertEqual(delivery["evidence_summary"], {"passed": 1, "missing": 0})
                self.assertNotIn("feature_implementation", delivery["workspace"])

                proposal_path = root / delivery["proposal_path"]
                proposal_path.write_text(
                    json.dumps(
                        {
                            "proposal_version": 8,
                            "operation": "deliver",
                            "target": delivery["target"],
                            "source_digest": delivery["source_digest"],
                            "remove": [delivery["workspace"]["attempt_dir"]],
                        }
                    )
                    + "\n",
                    encoding="utf-8",
                )
                applied = subprocess.run(
                    [
                        sys.executable,
                        str(launcher),
                        "--project-root",
                        str(root),
                        "deliver",
                        "--apply",
                        "--proposal",
                        delivery["proposal_path"],
                    ],
                    cwd=root,
                    text=True,
                    capture_output=True,
                )
                self.assertEqual(applied.returncode, 0, applied.stdout + applied.stderr)
                applied_payload = json.loads(applied.stdout)
                self.assertEqual(applied_payload["status"], "delivered")
                self.assertFalse(attempt.exists())
                self.assertTrue(feature_path.is_file())
                self.assertEqual(retained_before, {path: path.read_bytes() for path in retained_before})
                self.assertTrue(applied_payload["removed_artifacts"])
                self.assertTrue(all(path.startswith(ATTEMPT + "/") for path in applied_payload["removed_artifacts"]))
                self.assertIn(ATTEMPT + "/tasks.md", applied_payload["removed_artifacts"])

                workspace_adapter.unlink()
                missing = subprocess.run(
                    [sys.executable, str(workspace_adapter), "--project-root", str(root), "--phase", "plan"],
                    cwd=root,
                    text=True,
                    capture_output=True,
                )
                self.assertNotEqual(missing.returncode, 0)


if __name__ == "__main__":
    unittest.main()
