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
    PRESET_COMMANDS,
    execute_workspace_surface,
    registered_artifact,
)
from tests.concorde.support.paths import REPOSITORY_ROOT, TWO_LEVEL_PROJECT
from tests.concorde.support.specify_project import SpecifyProject


FEATURE = "specs/example/features/003-authorize-payment.md"


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
                project.run("bundle", "install", "concorde-bundle")
                shutil.copytree(TWO_LEVEL_PROJECT / ".concorde", root / ".concorde", dirs_exist_ok=True)
                shutil.copytree(TWO_LEVEL_PROJECT / "specs", root / "specs", dirs_exist_ok=True)
                (root / ".specify/feature.json").write_text(
                    json.dumps({"feature_path": FEATURE}, separators=(",", ":")) + "\n",
                    encoding="utf-8",
                )
                self.assertEqual(
                    len({registered_artifact(root, "gemini", command) for command in CONCORDE_COMMANDS}),
                    5,
                )
                ask = registered_artifact(root, "gemini", "speckit.concorde.ask").read_text(encoding="utf-8")
                for requirement in ("{{args}}", "sources", "uncertainty", "read-only"):
                    self.assertIn(requirement, ask.lower())
                for executable in ("concorde.sh", "concorde.ps1", "concorde.py", "workspace.py"):
                    self.assertNotIn(executable, ask)
                fast_loop = registered_artifact(root, "gemini", "speckit.fast-loop").read_text(encoding="utf-8")
                for requirement in (
                    "one selected feature",
                    "one providing module",
                    "affected architecture entities",
                    "cross-module relationship",
                    "external compatibility policy",
                    "every affected durable/source path",
                    "no attempt was created",
                ):
                    self.assertIn(requirement, fast_loop.lower())
                for command, phase in PRESET_COMMANDS.items():
                    receipt = execute_workspace_surface(
                        root,
                        registered_artifact(root, "gemini", command),
                        command,
                        phase,
                        REPOSITORY_ROOT,
                    )
                    self.assertEqual(receipt.exit_status, 0)
                    self.assertEqual(receipt.checkout_reads, ())
                    self.assertEqual(receipt.workspace["feature_id"], "feature.example.checkout.authorize")
                    self.assertEqual(receipt.workspace["feature_path"], FEATURE)
                    self.assertEqual(receipt.workspace["module_architecture"], "specs/example/architecture.md")
                    self.assertNotIn("workspace_kind", receipt.workspace)
                    self.assertNotIn("parent_context", receipt.workspace)
                    self.assertNotIn("feature_directory", receipt.workspace)
                    self.assertNotIn("feature_design", receipt.workspace)
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
