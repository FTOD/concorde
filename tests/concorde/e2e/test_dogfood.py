"""Dogfood scenarios: scenario files, fault injection and the evaluation's checks."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from concorde.spec.verification import verifies
from tests.concorde.support.paths import REPOSITORY_ROOT

SPEC = importlib.util.spec_from_file_location(
    "e2e", REPOSITORY_ROOT / "scripts/e2e/e2e.py"
)
e2e = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(e2e)
dogfood = e2e.dogfood


def git(cwd: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@t", *arguments],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


class ScenarioTests(unittest.TestCase):
    @verifies("scenario.dogfood-scenarios.scenarios-apply")
    @verifies("scenario.dogfood-scenarios.client")
    def test_every_scenario_is_complete_and_its_fault_applies_to_this_checkout(self):
        names = [item["name"] for item in dogfood.listing()]
        self.assertIn("write-hook-rw-directories", names)
        for name in names:
            with self.subTest(scenario=name):
                value = dogfood.scenario(name)
                self.assertEqual(name, value["name"])
                self.assertTrue(value["prompt"].strip())
                self.assertTrue(value["expect"].get("types"))
                for edit in value["fault"]["edits"]:
                    text = (REPOSITORY_ROOT / edit["file"]).read_text()
                    self.assertEqual(1, text.count(edit["old"]), edit["file"])
        # A scenario's fault covers both worker backends, so it runs on either client.
        chosen = dogfood.scenario("write-hook-rw-directories")
        self.assertEqual("claude", chosen["client"])
        faulted = {edit["file"] for edit in chosen["fault"]["edits"]}
        self.assertIn("src/concorde/harness/write_hook.py", faulted)
        self.assertIn("src/concorde/harness/pi_policy.ts", faulted)
        concorde, project = Path("/c"), Path("/p")
        self.assertNotIn("--pi", dogfood.install_command(concorde, project, "claude"))
        self.assertEqual(
            ["/p", "--develop", "--without-d2", "--pi"],
            dogfood.install_command(concorde, project, "pi")[2:],
        )
        with self.assertRaises(e2e.E2EError) as raised:
            dogfood.scenario("no-such-scenario")
        self.assertEqual("unknown_scenario", raised.exception.code)
        self.assertIn("write-hook-rw-directories", raised.exception.detail)


class FaultTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        (self.root / "a.py").write_text("x = 1\ny = 2\n")
        git(self.root, "init", "-q", "-b", "main")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-qm", "base")

    @verifies("scenario.dogfood-scenarios.fault")
    def test_a_fault_is_its_own_commit_and_refused_once_it_no_longer_applies(self):
        fault = {
            "summary": "y is wrong",
            "edits": [{"file": "a.py", "old": "y = 2\n", "new": "y = 3\n"}],
        }
        commit = dogfood.inject(self.root, fault)
        self.assertEqual(git(self.root, "rev-parse", "HEAD"), commit)
        self.assertEqual(
            "Inject fault: y is wrong", git(self.root, "log", "-1", "--format=%s")
        )
        self.assertEqual("x = 1\ny = 3\n", (self.root / "a.py").read_text())
        self.assertEqual("", git(self.root, "status", "--porcelain"))
        with self.assertRaises(e2e.E2EError) as raised:
            dogfood.inject(self.root, fault)
        self.assertEqual("fault_not_applicable", raised.exception.code)
        self.assertIn("a.py", raised.exception.detail)
        self.assertIn("0 time(s)", raised.exception.detail)


class EvaluationTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)

    @verifies("scenario.dogfood-scenarios.classified")
    def test_a_report_matches_by_type_and_every_basis_phrase(self):
        expect = {"types": ["bug"], "basis": ["implements the boundary wrongly"]}
        report = {
            "type": "bug",
            "basis": "Case 3: Concorde IMPLEMENTS the boundary wrongly; the grant differs.",
        }
        self.assertTrue(dogfood.matches(report, expect))
        self.assertFalse(dogfood.matches({**report, "type": "limitation"}, expect))
        self.assertFalse(
            dogfood.matches(
                {**report, "basis": "the project's Specs are wrong"}, expect
            )
        )
        reports = self.root / "defects"
        reports.mkdir()
        (reports / "one.json").write_text(json.dumps(report))
        (reports / "broken.json").write_text("{")
        check = dogfood._classified(sorted(reports.glob("*.json")), expect)
        self.assertEqual(
            (True, "matching: one.json"), (check["passed"], check["detail"])
        )

    @verifies("scenario.dogfood-scenarios.no-workaround")
    def test_a_path_changed_on_any_branch_or_worktree_is_a_workaround(self):
        project = self.root / "project"
        project.mkdir()
        (project / "models.py").write_text("class Response: pass\n")
        git(project, "init", "-q", "-b", "main")
        git(project, "add", "-A")
        git(project, "commit", "-qm", "base")
        blob = git(project, "rev-parse", "HEAD:models.py")
        expected = {"models.py": blob}
        self.assertEqual([], dogfood.unchanged(project, expected))
        worktree = self.root / "task"
        git(project, "worktree", "add", "-q", "-b", "task", str(worktree))
        (worktree / "models.py").write_text(
            "class Response:\n    informational = True\n"
        )
        self.assertEqual(
            [f"models.py differs in the worktree {worktree}"],
            dogfood.unchanged(project, expected),
        )
        git(worktree, "commit", "-qam", "work around")
        self.assertIn(
            "models.py differs on branch task", dogfood.unchanged(project, expected)
        )

    @verifies("scenario.dogfood-scenarios.untouched")
    def test_a_changed_framework_or_installed_file_is_seen(self):
        project = self.root / "project"
        (project / ".concorde/framework/src/concorde").mkdir(parents=True)
        (project / ".concorde/framework/src/concorde/__pycache__").mkdir()
        (project / ".concorde/framework/src/concorde/a.py").write_text("x = 1\n")
        (project / ".claude/skills/concorde").mkdir(parents=True)
        (project / ".claude/skills/concorde/SKILL.md").write_text("guidance\n")
        (project / ".concorde/install.json").write_text(
            json.dumps(
                {
                    "files": [
                        ".claude/skills/concorde/SKILL.md",
                        ".concorde/bin/concorde",
                    ]
                }
            )
        )
        framework = dogfood.framework_digest(project)
        installed = dogfood.installed_digests(project)
        self.assertEqual([".claude/skills/concorde/SKILL.md"], list(installed))
        # Python's caches are no change.
        (project / ".concorde/framework/src/concorde/__pycache__/a.pyc").write_bytes(
            b"x"
        )
        self.assertEqual(framework, dogfood.framework_digest(project))
        (project / ".concorde/framework/src/concorde/a.py").write_text("x = 2\n")
        self.assertNotEqual(framework, dogfood.framework_digest(project))
        (project / ".claude/skills/concorde/SKILL.md").write_text("changed\n")
        self.assertNotEqual(installed, dogfood.installed_digests(project))


if __name__ == "__main__":
    unittest.main()
