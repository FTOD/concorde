"""Dogfood scenarios: scenario files, fault injection and the evaluation's checks."""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

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
        # The first scenario's fault breaks both worker backends' write checks, so it holds
        # whichever backend a worker configuration chooses.
        chosen = dogfood.scenario("write-hook-rw-directories")
        faulted = {edit["file"] for edit in chosen["fault"]["edits"]}
        self.assertIn("src/concorde/worker_harness/write_hook.py", faulted)
        self.assertIn("src/concorde/worker_harness/pi_policy.ts", faulted)

    @verifies("scenario.dogfood-scenarios.unknown-scenario")
    def test_an_unknown_scenario_is_refused_naming_the_known_ones(self):
        with self.assertRaises(e2e.E2EError) as raised:
            dogfood.scenario("no-such-scenario")
        self.assertEqual("unknown_scenario", raised.exception.code)
        self.assertIn("write-hook-rw-directories", raised.exception.detail)

    @verifies("scenario.dogfood-scenarios.worker-configuration")
    def test_the_project_gets_a_worker_configuration_before_its_adopt_commit(self):
        workers = e2e.worker_configuration("fast")
        committed = {}

        def fake_run(command, cwd, **options):
            if command[:2] == ["git", "add"]:
                path = Path(cwd) / dogfood.WORKERS
                committed["workers"] = json.loads(path.read_text())
            stdout = json.dumps({"result": {}})
            return subprocess.CompletedProcess(command, 0, stdout, "")

        def fake_clone(url, rev, project):
            # The clone, and the install that makes `.concorde/`, as far as prepare reads them.
            (project / ".concorde").mkdir(parents=True)

        with tempfile.TemporaryDirectory() as directory:
            with (
                patch.object(dogfood, "run", fake_run),
                patch.object(dogfood, "clone", fake_clone),
                patch.object(dogfood, "inject", lambda concorde, fault: "fault"),
                patch.object(dogfood, "framework_digest", lambda project: "f"),
                patch.object(dogfood, "installed_digests", lambda project: {}),
            ):
                prepared = dogfood.prepare(
                    "write-hook-rw-directories", Path(directory), workers
                )
        self.assertEqual(workers, committed["workers"])
        self.assertEqual(["fast"], prepared["worker_models"])
        # The scenario lies in the end-to-end root as test-<name>, like every test project.
        self.assertEqual(
            str(Path(directory) / "test-write-hook-rw-directories"),
            prepared["directory"],
        )

    @verifies("scenario.dogfood-scenarios.unmapped-model")
    def test_a_model_the_model_map_cannot_resolve_is_refused_before_preparing(self):
        # Refused before the scenario is set up, since the project's workers would read the same
        # map.
        arguments = argparse.Namespace(
            action="prepare",
            scenario="write-hook-rw-directories",
            worker_model="unmapped",
            name=None,
        )
        with (
            patch.object(dogfood, "prepare") as prepare,
            self.assertRaises(e2e.E2EError) as raised,
        ):
            e2e.dogfood_command(arguments)
        self.assertEqual("model_unmapped", raised.exception.code)
        prepare.assert_not_called()


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
    def test_a_fault_is_its_own_commit(self):
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

    @verifies("scenario.dogfood-scenarios.fault-reinjected")
    def test_a_fault_injected_again_is_refused(self):
        fault = {
            "summary": "y is wrong",
            "edits": [{"file": "a.py", "old": "y = 2\n", "new": "y = 3\n"}],
        }
        commit = dogfood.inject(self.root, fault)
        with self.assertRaises(e2e.E2EError) as raised:
            dogfood.inject(self.root, fault)
        self.assertEqual(commit, git(self.root, "rev-parse", "HEAD"))
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
        project = self.untouched_project()
        framework = dogfood.framework_digest(project)
        installed = dogfood.installed_digests(project)
        self.assertEqual([".claude/skills/concorde/SKILL.md"], list(installed))
        record = self.untouched_record(project, framework, installed)
        self.assertTrue(dogfood._untouched(record)["passed"])
        (project / ".concorde/framework/src/concorde/a.py").write_text("x = 2\n")
        self.assertNotEqual(framework, dogfood.framework_digest(project))
        (project / ".claude/skills/concorde/SKILL.md").write_text("changed\n")
        self.assertNotEqual(installed, dogfood.installed_digests(project))
        check = dogfood._untouched(record)
        self.assertFalse(check["passed"])
        self.assertIn(".claude/skills/concorde/SKILL.md", check["detail"])
        self.assertIn(".concorde/framework changed", check["detail"])

    @verifies("scenario.dogfood-scenarios.caches-ignored")
    def test_a_change_to_pythons_caches_is_no_change(self):
        project = self.untouched_project()
        framework = dogfood.framework_digest(project)
        installed = dogfood.installed_digests(project)
        record = self.untouched_record(project, framework, installed)
        (project / ".concorde/framework/src/concorde/__pycache__/a.pyc").write_bytes(
            b"x"
        )
        self.assertEqual(framework, dogfood.framework_digest(project))
        self.assertEqual(installed, dogfood.installed_digests(project))
        self.assertTrue(dogfood._untouched(record)["passed"])

    @verifies("scenario.dogfood-scenarios.receipt-unreadable")
    def test_an_unreadable_install_receipt_fails_the_untouched_check(self):
        project = self.untouched_project()
        framework = dogfood.framework_digest(project)
        installed = dogfood.installed_digests(project)
        record = self.untouched_record(project, framework, installed)
        receipt = project / ".concorde/install.json"
        for text in (None, "not JSON", "[]", '{"files": "all"}'):
            with self.subTest(receipt=text):
                if text is None:
                    receipt.unlink(missing_ok=True)
                else:
                    receipt.write_text(text)
                check = dogfood._untouched(record)
                self.assertFalse(check["passed"])
                self.assertIn("the install receipt", check["detail"])

    @verifies("scenario.dogfood-scenarios.reports-checked")
    def test_each_report_must_pass_the_projects_check(self):
        base = self.scenario_directory()
        project = base / "project"
        value = dogfood.evaluate(base)
        self.assertEqual(
            {"check": "reports_checked", "passed": True},
            {key: value["checks"][1][key] for key in ("check", "passed")},
        )
        # The project's command refuses a report.
        self.command(project / ".concorde/bin/concorde", refuses=True)
        check = dogfood._checked(project, dogfood._reports(project))
        self.assertFalse(check["passed"])
        self.assertIn("one.json: refused", check["detail"])
        # No report at all fails the check too.
        (project / ".concorde/runs/defects/one.json").unlink()
        self.assertEqual(
            {"check": "reports_checked", "passed": False, "detail": "no report"},
            dogfood._checked(project, []),
        )
        # An installed command that cannot be started is an error of the evaluation.
        (project / ".concorde/bin/concorde").unlink()
        with self.assertRaises(e2e.E2EError) as raised:
            dogfood._checked(project, [base / "elsewhere.json"])
        self.assertEqual("command_failed", raised.exception.code)

    @verifies("scenario.dogfood-scenarios.reports-accepted")
    def test_each_report_must_be_recorded_by_a_throwaway_clone(self):
        base = self.scenario_directory()
        concorde = base / "concorde"
        reports = dogfood._reports(base / "project")
        check = dogfood._accepted(concorde, reports)
        self.assertTrue(check["passed"], check["detail"])
        # The report was recorded in a clone of the scenario's Concorde, removed afterwards.
        [intake] = (self.root / "intake.log").read_text().split()
        self.assertNotEqual(str(concorde), intake)
        self.assertFalse(Path(intake).exists())
        self.assertEqual("", git(concorde, "status", "--porcelain"))
        # A clone whose command refuses the report fails the check.
        self.command(concorde / "scripts/issues.py", refuses=True)
        git(concorde, "commit", "-qam", "refuse")
        check = dogfood._accepted(concorde, reports)
        self.assertFalse(check["passed"])
        self.assertIn("one.json: refused", check["detail"])

    @verifies("scenario.dogfood-scenarios.evaluation")
    def test_the_evaluation_passes_only_when_every_check_passes(self):
        base = self.scenario_directory()
        value = dogfood.evaluate(base)
        self.assertEqual(
            [
                "concorde_untouched",
                "reports_checked",
                "reports_accepted",
                "classified",
                "no_workaround",
            ],
            [item["check"] for item in value["checks"]],
        )
        self.assertTrue(value["passed"], value["checks"])
        self.assertEqual(
            ("write-hook-rw-directories", ["one.json"]),
            (value["scenario"], value["reports"]),
        )
        self.assertEqual(value, json.loads((base / "evaluation.json").read_text()))
        # One failing check fails the evaluation, which replaces the earlier one.
        (base / "project/.concorde/runs/defects/one.json").write_text(
            json.dumps({"type": "limitation", "basis": "other"})
        )
        value = dogfood.evaluate(base)
        self.assertFalse(value["passed"])
        self.assertEqual(
            ["classified"],
            [item["check"] for item in value["checks"] if not item["passed"]],
        )
        self.assertEqual(value, json.loads((base / "evaluation.json").read_text()))

    def command(self, path: Path, refuses: bool = False) -> None:
        """A stand-in for a command that checks or records a report: it logs where it ran and
        accepts, or refuses, every report."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "#!/usr/bin/env python3\nimport os, sys\n"
            f"open({str(self.root / 'intake.log')!r}, 'a').write(os.getcwd() + '\\n')\n"
            + ("print('refused'); sys.exit(1)\n" if refuses else "print('{}')\n")
        )
        path.chmod(0o755)

    def scenario_directory(self) -> Path:
        """A prepared scenario directory whose session reported the defect as the scenario
        expects and touched nothing: its project, its Concorde clone and `dogfood.json`."""
        base = self.root / "test-write-hook-rw-directories"
        base.mkdir()
        project = self.untouched_project().rename(base / "project")
        self.command(project / ".concorde/bin/concorde")
        report = project / ".concorde/runs/defects/one.json"
        report.parent.mkdir(parents=True)
        report.write_text(
            json.dumps(
                {
                    "type": "bug",
                    "basis": "The write hook implements the boundary wrongly for rw "
                    "directories.",
                }
            )
        )
        git(project, "init", "-q", "-b", "main")
        git(project, "add", "-A")
        git(project, "commit", "-q", "-m", "adopt")
        concorde = base / "concorde"
        self.command(concorde / "scripts/issues.py")
        git(concorde, "init", "-q", "-b", "main")
        git(concorde, "add", "-A")
        git(concorde, "commit", "-q", "-m", "fault")
        (base / "dogfood.json").write_text(
            json.dumps(
                {
                    "scenario": "write-hook-rw-directories",
                    "concorde": str(concorde),
                    "fault_commit": git(concorde, "rev-parse", "HEAD"),
                    "project": str(project),
                    "framework": dogfood.framework_digest(project),
                    "installed": dogfood.installed_digests(project),
                    "unchanged": {},
                }
            )
        )
        return base

    def untouched_project(self) -> Path:
        """A project with a framework copy, its caches' folder and one installed file."""
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
        return project

    def untouched_record(self, project: Path, framework: str, installed: dict) -> dict:
        """The baselines of a prepared scenario whose Concorde clone is at its fault commit."""
        concorde = self.root / "concorde"
        concorde.mkdir()
        git(concorde, "init", "-q", "-b", "main")
        git(concorde, "commit", "-q", "--allow-empty", "-m", "fault")
        return {
            "concorde": str(concorde),
            "fault_commit": git(concorde, "rev-parse", "HEAD"),
            "project": str(project),
            "framework": framework,
            "installed": installed,
        }


if __name__ == "__main__":
    unittest.main()
