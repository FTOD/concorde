"""Sessions in this checkout load both of Concorde's skills from the build's output."""

import importlib.util
import os
import subprocess
import unittest
from pathlib import Path

from concorde.distribution.build import build, skill_path
from concorde.distribution.prompt_resolver import resolve_role_prompt
from concorde.spec.verification import verifies
from tests.concorde.support.paths import REPOSITORY_ROOT


def load_initializer():
    spec = importlib.util.spec_from_file_location(
        "init_references", REPOSITORY_ROOT / "scripts/development/init-references.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def git(*arguments: str) -> str:
    return subprocess.run(
        ("git", *arguments),
        cwd=REPOSITORY_ROOT,
        text=True,
        capture_output=True,
        check=False,
    ).stdout.strip()


class DevelopmentSkillTests(unittest.TestCase):
    @verifies("scenario.concorde.development-skills")
    def test_sessions_in_this_checkout_load_both_skills(self):
        # The preparation's reference initializer makes the links, which Git ignores and does not
        # track; what it makes is checked here without relying on this worktree's preparation.
        script = load_initializer()
        self.assertEqual(script.SKILLS, ("concorde", "concorde-development"))
        for name in script.SKILLS:
            link = Path(".claude/skills") / name
            with self.subTest(skill=name):
                self.assertEqual(
                    Path(skill_path(name)).parent.as_posix(),
                    os.path.normpath(link.parent / script.skill_target(name)),
                )
                self.assertEqual(git("ls-files", "--", link.as_posix()), "")
                self.assertEqual(
                    git("check-ignore", "--", link.as_posix()), link.as_posix()
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
