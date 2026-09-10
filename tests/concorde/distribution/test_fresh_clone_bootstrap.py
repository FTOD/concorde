"""Acceptance: a bare ``git clone`` of this checkout bootstraps with exactly one build command.

This exercises the checkout as a *self-hosted* Concorde project (project_root == package_root),
the same way this repository dogfoods itself, not the packaged-consumer install path (see
``test_consumer_install_end_to_end.py`` for that). No network access is used: the clone is a
local, object-sharing clone of this worktree's own repository at its exact current ``HEAD``.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from concorde.spec.contracts import SKILL_NAMES
from concorde.spec.verification import verifies

from tests.concorde.support.paths import REPOSITORY_ROOT

# A target already registered in this project's own .concorde/specs.json (self-hosted registry),
# used only to make a schema-valid concorde-validate request; describe-policy never executes checks.
SELF_HOSTED_TARGET = "module.development"


def _run(args: list[str], cwd: Path, **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(args, cwd=str(cwd), capture_output=True, text=True, **kwargs)


class FreshCloneBootstrapAcceptance(unittest.TestCase):
    """Proposal section 15 (Stage D) / section 16: "a fresh clone works after exactly one build
    command" and "editing a prompt without rebuilding makes every skill invocation fail with
    stale_build"."""

    @classmethod
    def setUpClass(cls) -> None:
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=REPOSITORY_ROOT,
            capture_output=True, text=True, check=True,
        )
        cls.head_sha = head.stdout.strip()

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.clone = Path(self.temporary.name) / "clone"
        # --shared avoids copying the whole object store for a short-lived local, read-only
        # clone; --no-checkout + an explicit checkout of this worktree's exact HEAD avoids any
        # ambiguity about which branch a plain local clone would otherwise default to.
        cloned = _run(["git", "clone", "--shared", "--no-checkout", "--quiet",
                       str(REPOSITORY_ROOT), str(self.clone)], REPOSITORY_ROOT)
        self.assertEqual(0, cloned.returncode, cloned.stderr)
        checked_out = _run(["git", "checkout", "--quiet", self.head_sha], self.clone)
        self.assertEqual(0, checked_out.returncode, checked_out.stderr)

    def _validate_invocation(self) -> dict:
        invocation = {
            "type_id": "concorde-capability-invocation", "schema_version": 3,
            "capability_id": "concorde-validate", "mode": "describe-policy", "configuration": None,
            "input": {"type_id": "concorde-validate-request", "schema_version": 1,
                      "data": {"target_id": SELF_HOSTED_TARGET,
                               "task": "Describe validation readiness for the workflow host Service"}},
        }
        process = _run(
            [sys.executable, "scripts/run-capability.py", "concorde-validate"], self.clone,
            input=json.dumps(invocation), env={**os.environ, "CONCORDE_STUDIO_URL": ""},
        )
        return json.loads(process.stdout)

    def test_clone_carries_no_build_output_or_projected_skills(self):
        self.assertFalse((self.clone / "generated").exists())
        for integration_root in (".claude/skills", ".agents/skills"):
            projected = sorted(p.name for p in (self.clone / integration_root).glob("concorde-*"))
            self.assertEqual([], projected)

    @verifies("scenario.distribution.build-write", "scenario.distribution.worktree-guard-refuses")
    def test_one_build_command_bootstraps_a_fully_working_clone(self):
        build = _run([sys.executable, "scripts/concorde.py", "build"], self.clone)
        self.assertEqual(0, build.returncode, build.stderr)
        built = json.loads(build.stdout)
        self.assertEqual("success", built["status"], built)

        self.assertTrue((self.clone / "generated/build-manifest.json").is_file())
        self.assertTrue((self.clone / "generated/protocol/principles.md").is_file())
        for integration_root in (".claude/skills", ".agents/skills"):
            skills = sorted(
                p.parent.name for p in (self.clone / integration_root).glob("concorde-*/SKILL.md")
            )
            self.assertEqual(sorted(SKILL_NAMES), skills)
            self.assertEqual(7, len(skills))

        # The clone carries the worktree guard and the Claude/Codex files that register it, so a
        # session opened here refuses native worktree creation from its first tool call.
        refused = _run([sys.executable, "scripts/worktree-guard.py", "--check",
                        "git worktree add ../elsewhere"], self.clone)
        self.assertEqual(2, refused.returncode, refused.stderr)
        self.assertTrue(refused.stdout.startswith("deny (git-worktree)"), refused.stdout)
        for integration_file in (".claude/settings.json", ".codex/hooks.json", ".codex/rules/worktree.rules"):
            self.assertTrue((self.clone / integration_file).is_file(), integration_file)

        described = self._validate_invocation()
        self.assertEqual("described", described["status"], described)

    @verifies("scenario.distribution.build-stale-blocks-execution", "scenario.distribution.build-check")
    def test_editing_a_prompt_without_rebuilding_fails_every_invocation_closed(self):
        build = _run([sys.executable, "scripts/concorde.py", "build"], self.clone)
        self.assertEqual(0, build.returncode, build.stderr)
        described = self._validate_invocation()
        self.assertEqual("described", described["status"], described)

        prompt = self.clone / "prompts/workflow-host/worktree-handoff.md"
        original = prompt.read_text(encoding="utf-8")
        prompt.write_text(original + "\n<!-- drifted after the build: source digest changes -->\n",
                          encoding="utf-8")

        blocked = self._validate_invocation()
        self.assertEqual("blocked", blocked["status"], blocked)
        self.assertEqual("stale_build", blocked["errors"][0]["code"], blocked)

        checked = _run([sys.executable, "scripts/concorde.py", "build", "--check"], self.clone)
        self.assertNotEqual(0, checked.returncode, checked.stdout)
        payload = json.loads(checked.stdout)
        self.assertEqual("invalid", payload["status"], payload)


if __name__ == "__main__":
    unittest.main()
