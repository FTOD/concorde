import json
import shutil
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.catalog_server import CatalogServer
from tests.concorde.support.installed_command_surface import (
    CONCORDE_COMMANDS,
    NORMAL_PHASES,
    execute_workspace_surface,
    handoff_digest,
    registered_artifact,
)
from tests.concorde.support.paths import CONTEXT_PROJECT, REPOSITORY_ROOT
from tests.concorde.support.specify_project import SpecifyProject

import importlib.util


_builder_spec = importlib.util.spec_from_file_location(
    "concorde_release_builder", REPOSITORY_ROOT / "scripts/release/build-components.py"
)
assert _builder_spec and _builder_spec.loader
_builder = importlib.util.module_from_spec(_builder_spec)
_builder_spec.loader.exec_module(_builder)


class InstalledCommandSurfaceContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.distribution_temporary = tempfile.TemporaryDirectory()
        cls.dist = Path(cls.distribution_temporary.name)
        cls.server = CatalogServer(cls.dist)
        _builder.build_release(cls.dist, cls.server.base_url)
        cls.server.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.server.__exit__(None, None, None)
        cls.distribution_temporary.cleanup()

    def installed_project(self, temporary: str, integration: str = "codex") -> Path:
        root = Path(temporary) / "target"
        project = SpecifyProject(root, integration=integration, skills=integration == "codex")
        project.initialize()
        project.register_catalogs(self.server.base_url)
        project.run("bundle", "install", "concorde-starter")
        shutil.copytree(CONTEXT_PROJECT / ".concorde", root / ".concorde", dirs_exist_ok=True)
        shutil.copytree(CONTEXT_PROJECT / "specs", root / "specs", dirs_exist_ok=True)
        (root / ".specify/feature.json").write_text(
            json.dumps({"feature_directory": "specs/example/features/001-deliver"}, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
        return root

    def test_release_materializes_nine_normal_and_six_concorde_surfaces(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.installed_project(temporary)
            normal = {registered_artifact(root, "codex", command) for command in NORMAL_PHASES}
            concorde = {registered_artifact(root, "codex", command) for command in CONCORDE_COMMANDS}
            self.assertEqual(len(normal), 9)
            self.assertEqual(len(concorde), 6)
            self.assertTrue(all(path.is_file() for path in normal | concorde))

    def test_every_normal_winner_executes_the_installed_workspace_bootstrap(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.installed_project(temporary)
            receipts = []
            for command, phase in NORMAL_PHASES.items():
                artifact = registered_artifact(root, "codex", command)
                receipt = execute_workspace_surface(
                    root,
                    artifact,
                    command,
                    phase,
                    REPOSITORY_ROOT,
                )
                receipts.append(receipt)
                self.assertEqual(receipt.exit_status, 0)
                expected = receipt.workspace["feature_directory"] if phase in {"specify", "clarify", "checklist"} else receipt.workspace["implementation_dir"]
                self.assertEqual(receipt.phase_root, expected)
                self.assertEqual(
                    receipt.workspace["checklists_dir"],
                    receipt.workspace["implementation_dir"] + "/checklists",
                )
                if phase in {"specify", "clarify", "checklist", "implement"}:
                    content = artifact.read_text(encoding="utf-8")
                    self.assertNotIn("FEATURE_DIR/checklists", content)
                    self.assertIn("CHECKLISTS_DIR", content)
                self.assertEqual(receipt.checkout_reads, ())
            self.assertEqual(len({item.handoff_digest for item in receipts}), 1)

    def test_installed_handoff_bytes_match_release_sources(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.installed_project(temporary)
            installed = handoff_digest(
                root / ".specify/extensions/concorde",
                root / ".specify/presets/concorde-core",
            )
            source = handoff_digest(
                REPOSITORY_ROOT / "extensions/concorde",
                REPOSITORY_ROOT / "presets/concorde-core",
            )
            self.assertEqual(installed, source)


if __name__ == "__main__":
    unittest.main()
