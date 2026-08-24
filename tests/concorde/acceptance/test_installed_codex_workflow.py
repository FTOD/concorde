import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.contract.test_installed_command_surfaces import _builder
from tests.concorde.support.catalog_server import CatalogServer
from tests.concorde.support.installed_command_surface import CONCORDE_COMMANDS, registered_artifact
from tests.concorde.support.paths import CONTEXT_PROJECT
from tests.concorde.support.specify_project import SpecifyProject


class InstalledCodexWorkflowTests(unittest.TestCase):
    def test_six_commands_use_installed_runtime_and_missing_adapter_fails(self):
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
                project.run("bundle", "install", "concorde-starter")
                shutil.copytree(CONTEXT_PROJECT / ".concorde", root / ".concorde", dirs_exist_ok=True)
                shutil.copytree(CONTEXT_PROJECT / "specs", root / "specs", dirs_exist_ok=True)
                (root / ".specify/feature.json").write_text(
                    json.dumps({"feature_directory": "specs/example/features/001-deliver"}, separators=(",", ":")) + "\n",
                    encoding="utf-8",
                )
                self.assertEqual(
                    len({registered_artifact(root, "codex", command) for command in CONCORDE_COMMANDS}),
                    6,
                )
                launcher = root / ".specify/extensions/concorde/scripts/python/concorde.py"
                operations = (
                    (["validate"], {"success"}),
                    (["context", "module.example"], {"success"}),
                    (["feature", "create", "--module-id", "module.example.api", "--feature-id", "feature.example.api.observe", "--short-name", "observe"], {"proposal"}),
                    (["feature", "select", "feature.example.deliver"], {"selected", "unchanged"}),
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
                implementation = root / "specs/example/features/001-deliver/implementation"
                implementation.mkdir()
                (implementation / "tasks.md").write_text("# Tasks\n\n- [X] T001 Complete installed fixture\n", encoding="utf-8")
                harden = subprocess.run(
                    [sys.executable, str(launcher), "--project-root", str(root), "feature", "harden", "--propose"],
                    cwd=root,
                    text=True,
                    capture_output=True,
                )
                self.assertEqual(harden.returncode, 0, harden.stdout + harden.stderr)
                self.assertEqual(json.loads(harden.stdout)["status"], "eligible")
                adapter = root / ".specify/extensions/concorde/scripts/python/workspace.py"
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
