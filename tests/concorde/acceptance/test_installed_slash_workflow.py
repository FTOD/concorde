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
    NORMAL_PHASES,
    execute_workspace_surface,
    registered_artifact,
)
from tests.concorde.support.paths import CONTEXT_PROJECT, REPOSITORY_ROOT
from tests.concorde.support.specify_project import SpecifyProject


class InstalledSlashWorkflowTests(unittest.TestCase):
    def test_gemini_surfaces_match_workspace_and_runtime_semantics(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            dist = base / "dist"
            server = CatalogServer(dist)
            _builder.build_release(dist, server.base_url)
            with server:
                root = base / "target"
                project = SpecifyProject(root, integration="gemini", skills=False)
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
                    len({registered_artifact(root, "gemini", command) for command in CONCORDE_COMMANDS}),
                    5,
                )
                for command, phase in NORMAL_PHASES.items():
                    receipt = execute_workspace_surface(
                        root,
                        registered_artifact(root, "gemini", command),
                        command,
                        phase,
                        REPOSITORY_ROOT,
                    )
                    self.assertEqual(receipt.exit_status, 0)
                    self.assertEqual(receipt.checkout_reads, ())
                launcher = root / ".specify/extensions/concorde/scripts/python/concorde.py"
                result = subprocess.run(
                    [sys.executable, str(launcher), "--project-root", str(root), "validate"],
                    cwd=root,
                    text=True,
                    capture_output=True,
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(json.loads(result.stdout)["status"], "success")


if __name__ == "__main__":
    unittest.main()
