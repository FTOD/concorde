import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.contract.test_installed_command_surfaces import _builder
from tests.concorde.support.catalog_server import CatalogServer
from tests.concorde.support.installed_command_surface import (
    CONCORDE_COMMANDS,
    CONCORDE_RUNTIME_COMMANDS,
    registered_artifact,
)
from tests.concorde.support.paths import TWO_LEVEL_PROJECT
from tests.concorde.support.specify_project import SpecifyProject


class InstalledCodexWorkflowTests(unittest.TestCase):
    def test_seven_surfaces_preserve_six_runtime_operations_and_hardening(self):
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
                    json.dumps({"feature_directory": "specs/example/features/001-checkout/subfeatures/001-authorize-payment"}, separators=(",", ":")) + "\n",
                    encoding="utf-8",
                )
                self.assertEqual(
                    len({registered_artifact(root, "codex", command) for command in CONCORDE_COMMANDS}),
                    7,
                )
                self.assertEqual(len(CONCORDE_RUNTIME_COMMANDS), 6)
                workspace_adapter = root / ".specify/extensions/concorde/scripts/python/workspace.py"
                checklist_paths = subprocess.run(
                    [sys.executable, str(workspace_adapter), "--project-root", str(root), "--phase", "checklist"],
                    cwd=root,
                    text=True,
                    capture_output=True,
                    check=True,
                )
                workspace_payload = json.loads(checklist_paths.stdout)["workspace"]
                self.assertEqual(workspace_payload["workspace_kind"], "subfeature")
                self.assertEqual(workspace_payload["parent_context"]["feature_id"], "feature.example.checkout")
                self.assertEqual(
                    workspace_payload["checklists_dir"],
                    workspace_payload["implementation_dir"] + "/checklists",
                )
                launcher = root / ".specify/extensions/concorde/scripts/python/concorde.py"
                operations = (
                    (["validate"], {"success"}),
                    (["context", "module.example"], {"success"}),
                    (["feature", "create", "--parent-feature", "feature.example.checkout", "--feature-id", "feature.example.checkout.capture", "--short-name", "capture"], {"proposal"}),
                    (["feature", "select", "feature.example.checkout.authorize", "--resume"], {"selected", "unchanged"}),
                )
                for arguments, statuses in operations:
                    result = subprocess.run(
                        [sys.executable, str(launcher), "--project-root", str(root), *arguments],
                        cwd=root,
                        text=True,
                        capture_output=True,
                    )
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    self.assertIn(json.loads(result.stdout)["status"], statuses)
                implementation = root / "specs/example/features/001-checkout/subfeatures/001-authorize-payment/implementation"
                implementation.mkdir(exist_ok=True)
                (implementation / "tasks.md").write_text("# Tasks\n\n- [X] T001 Complete installed fixture\n", encoding="utf-8")
                harden = subprocess.run(
                    [sys.executable, str(launcher), "--project-root", str(root), "feature", "harden", "--propose"],
                    cwd=root,
                    text=True,
                    capture_output=True,
                )
                self.assertEqual(harden.returncode, 0, harden.stdout + harden.stderr)
                harden_payload = json.loads(harden.stdout)
                self.assertEqual(harden_payload["status"], "eligible")
                self.assertEqual(
                    harden_payload["proposal_path"],
                    harden_payload["workspace"]["implementation_dir"] + "/harden-proposal.json",
                )
                self.assertEqual(harden_payload["task_summary"], {"complete": 1, "incomplete": 0, "malformed": 0})
                self.assertEqual(
                    harden_payload["checklist_summary"],
                    {"files": 0, "complete": 0, "incomplete": 0, "malformed": 0},
                )
                adapter = workspace_adapter
                adapter.unlink()
                missing = subprocess.run(
                    [sys.executable, str(adapter), "--project-root", str(root), "--phase", "plan"],
                    cwd=root,
                    text=True,
                    capture_output=True,
                )
                self.assertNotEqual(missing.returncode, 0)


if __name__ == "__main__":
    unittest.main()
