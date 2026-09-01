import tempfile
import unittest
from pathlib import Path

from tests.concorde.contract.test_installed_command_surfaces import _builder
from tests.concorde.support.catalog_server import CatalogServer
from tests.concorde.support.installed_command_surface import NORMAL_PHASES, PRESET_COMMANDS, registered_artifact
from tests.concorde.support.paths import REPOSITORY_ROOT
from tests.concorde.support.specify_project import SpecifyProject


class CommandRecompositionTests(unittest.TestCase):
    def assert_all_winners(self, root: Path, marker: str, commands=PRESET_COMMANDS) -> None:
        for command in commands:
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
                self.assert_all_winners(root, "LOWER_LAYER_MARKER", NORMAL_PHASES)
                project.register_catalogs(server.base_url)
                project.run("bundle", "install", "concorde-bundle")
                self.assert_all_winners(root, "## Workspace gate")

                project.run("preset", "disable", "concorde")
                self.assert_all_winners(root, "## Workspace gate")
                project.run("preset", "enable", "concorde")
                self.assert_all_winners(root, "## Workspace gate")

                project.run("preset", "set-priority", "concorde", "30")
                self.assert_all_winners(root, "## Workspace gate")
                project.run("preset", "set-priority", "concorde", "5")
                self.assert_all_winners(root, "## Workspace gate")

                project.run("bundle", "remove", "concorde-bundle")
                self.assert_all_winners(root, "LOWER_LAYER_MARKER", NORMAL_PHASES)
                self.assertFalse((root / ".agents/skills/speckit-fast-loop/SKILL.md").exists())


if __name__ == "__main__":
    unittest.main()
