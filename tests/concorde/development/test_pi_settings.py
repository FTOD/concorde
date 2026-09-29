"""The checkout's pi project settings load Concorde's own pi extension from its source."""

import json
import re
import unittest

from concorde.distribution.build import build, skill_path
from concorde.distribution.install import PI_EXTENSION_SOURCES
from concorde.distribution.prompt_resolver import resolve_role_prompt
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


class DevelopmentSkillTests(unittest.TestCase):
    @verifies("scenario.concorde.development-skills")
    def test_sessions_in_this_checkout_load_both_skills(self):
        settings = REPOSITORY_ROOT / ".pi" / "settings.json"
        skills = json.loads(settings.read_text())["skills"]
        loaded = [(settings.parent / entry).resolve() for entry in skills]
        self.assertEqual(
            [
                (REPOSITORY_ROOT / skill_path(name)).parent.resolve()
                for name in ("concorde", "concorde-development")
            ],
            loaded,
        )
        # The build renders exactly those skills, the development skill with the observation
        # rule Dogfooding shares with the develop guidance.
        outputs = {
            output.path: output.content for output in build(REPOSITORY_ROOT).outputs
        }
        rule = " ".join(
            resolve_role_prompt(
                REPOSITORY_ROOT, "prompts/dogfooding/common/observe-runs.md"
            ).body.split()
        )
        development = " ".join(
            outputs[skill_path("concorde-development")].decode().split()
        )
        self.assertIn(rule, development)
        self.assertIn(skill_path("concorde"), outputs)
        for instructions in ("CLAUDE.md", "AGENTS.md"):
            text = (REPOSITORY_ROOT / instructions).read_text()
            with self.subTest(instructions=instructions):
                self.assertIn("Before any work", text)
                self.assertIn("`concorde`", text)
                self.assertIn("`concorde-development`", text)
