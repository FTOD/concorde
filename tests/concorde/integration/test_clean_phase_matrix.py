import json
import shutil
import tempfile
import unittest
from pathlib import Path

from tests.concorde.contract.test_installed_command_surfaces import _builder
from tests.concorde.support.catalog_server import CatalogServer
from tests.concorde.support.installed_command_surface import (
    PRESET_COMMANDS,
    execute_workspace_surface,
    registered_artifact,
)
from tests.concorde.support.paths import REPOSITORY_ROOT, TWO_LEVEL_PROJECT
from tests.concorde.support.specify_project import SpecifyProject


class CleanPhaseMatrixTests(unittest.TestCase):
    def test_three_runs_route_every_phase_without_root_aliases(self):
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
                selected = "specs/example/features/003-authorize-payment.md"
                (root / ".specify/feature.json").write_text(
                    json.dumps({"feature_path": selected}, separators=(",", ":")) + "\n",
                    encoding="utf-8",
                )
                runs = []
                for _ in range(3):
                    receipts = []
                    for command, phase in PRESET_COMMANDS.items():
                        receipt = execute_workspace_surface(
                            root,
                            registered_artifact(root, "codex", command),
                            command,
                            phase,
                            REPOSITORY_ROOT,
                        )
                        receipts.append(json.dumps(receipt.to_dict(), sort_keys=True, separators=(",", ":")))
                        self.assertEqual(receipt.workspace["feature_id"], "feature.example.checkout.authorize")
                        self.assertEqual(receipt.workspace["module_architecture"], "specs/example/architecture.md")
                        self.assertEqual(
                            [item["feature_id"] for item in receipt.workspace["related_features"]],
                            ["feature.example.checkout", "feature.example.checkout.confirm"],
                        )
                        self.assertNotIn("workspace_kind", receipt.workspace)
                        self.assertNotIn("parent_context", receipt.workspace)
                    runs.append(receipts)
                self.assertEqual(runs[0], runs[1])
                self.assertEqual(runs[1], runs[2])
                feature = root / selected
                self.assertTrue(feature.is_file())
                self.assertFalse((root / ".concorde/attempts/feature.example.checkout.authorize/implementation").is_symlink())


if __name__ == "__main__":
    unittest.main()
