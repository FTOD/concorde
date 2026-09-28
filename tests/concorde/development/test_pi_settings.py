"""The checkout's pi project settings load Concorde's own pi extension from its source."""

import json
import re
import unittest

from concorde.distribution.install import PI_EXTENSION_SOURCES
from concorde.spec.verification import verifies
from tests.concorde.support.paths import REPOSITORY_ROOT


class PiSettingsTests(unittest.TestCase):
    @verifies("scenario.concorde.pi-extension-in-checkout")
    def test_the_checkout_loads_the_installed_extension_source(self):
        settings = REPOSITORY_ROOT / ".pi" / "settings.json"
        extensions = json.loads(settings.read_text())["extensions"]
        # Paths in project settings resolve from the project's .pi directory.
        loaded = [(settings.parent / entry).resolve() for entry in extensions]
        entry = (REPOSITORY_ROOT / PI_EXTENSION_SOURCES["index.ts"]).resolve()
        self.assertEqual([entry], loaded)
        # Every module the extension imports lies beside it, as the installer places them.
        imported = re.findall(r'from "\./([^"]+)"', entry.read_text())
        self.assertTrue(imported)
        for name in imported:
            self.assertTrue((entry.parent / name).is_file(), name)
            self.assertIn(
                f"src/concorde/main_session/{name}", PI_EXTENSION_SOURCES.values()
            )
        # The tools that wake the main agent are the ones this extension registers.
        for tool in ("concorde_run", "concorde_task_session"):
            self.assertIn(f'name: "{tool}"', entry.read_text())
