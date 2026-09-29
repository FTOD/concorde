"""Sessions in this checkout load both of Concorde's skills from the build's output."""

import unittest

from concorde.distribution.build import build, skill_path
from concorde.distribution.prompt_resolver import resolve_role_prompt
from concorde.spec.verification import verifies
from tests.concorde.support.paths import REPOSITORY_ROOT


class DevelopmentSkillTests(unittest.TestCase):
    @verifies("scenario.concorde.development-skills")
    def test_sessions_in_this_checkout_load_both_skills(self):
        for name in ("concorde", "concorde-development"):
            link = REPOSITORY_ROOT / ".claude" / "skills" / name
            with self.subTest(skill=name):
                self.assertTrue(link.is_symlink())
                self.assertEqual(
                    (REPOSITORY_ROOT / skill_path(name)).parent.resolve(),
                    link.resolve(),
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
        text = (REPOSITORY_ROOT / "CLAUDE.md").read_text()
        self.assertIn("Before any work", text)
        self.assertIn("`concorde`", text)
        self.assertIn("`concorde-development`", text)
