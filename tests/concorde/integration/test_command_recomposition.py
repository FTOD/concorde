import tempfile
import unittest
from pathlib import Path

from tests.concorde.contract.test_installed_command_surfaces import _builder
from tests.concorde.support.catalog_server import CatalogServer
from tests.concorde.support.installed_command_surface import NORMAL_PHASES, registered_artifact
from tests.concorde.support.paths import REPOSITORY_ROOT
from tests.concorde.support.specify_project import SpecifyProject


class CommandRecompositionTests(unittest.TestCase):
    def assert_all_winners(self, root: Path, marker: str) -> None:
        for command in NORMAL_PHASES:
            content = registered_artifact(root, "codex", command).read_text(encoding="utf-8")
            self.assertIn(marker, content, command)

    def test_disable_priority_and_remove_follow_host_registration_lifecycle(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            dist = base / "dist"
            server = CatalogServer(dist)
            _builder.build_release(dist, server.base_url)
            with server:
                root = base / "target"
                project = SpecifyProject(root)
                project.initialize()
                lower = REPOSITORY_ROOT / "tests/concorde/fixtures/presets/lower-core"
                project.run("preset", "add", "--dev", str(lower), "--priority", "20")
                self.assert_all_winners(root, "LOWER_LAYER_MARKER")
                project.register_catalogs(server.base_url)
                project.run("bundle", "install", "concorde-starter")
                self.assert_all_winners(root, "Concorde Installed Workspace Gate")

                project.run("preset", "disable", "concorde-core")
                self.assert_all_winners(root, "Concorde Installed Workspace Gate")
                project.run("preset", "enable", "concorde-core")
                self.assert_all_winners(root, "Concorde Installed Workspace Gate")

                project.run("preset", "set-priority", "concorde-core", "30")
                self.assert_all_winners(root, "Concorde Installed Workspace Gate")
                project.run("preset", "set-priority", "concorde-core", "5")
                self.assert_all_winners(root, "Concorde Installed Workspace Gate")

                project.run("bundle", "remove", "concorde-starter")
                self.assert_all_winners(root, "LOWER_LAYER_MARKER")


if __name__ == "__main__":
    unittest.main()
