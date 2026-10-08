"""Dogfood scenarios: scenario files, fault injection and the evaluation's checks."""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
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

    @verifies("scenario.dogfood-scenarios.invalid-scenario")
    def test_a_scenario_file_of_the_wrong_shape_is_refused_naming_its_field(self):
        valid = dogfood.scenario("write-hook-rw-directories")
        edit = valid["fault"]["edits"][0]
        cases = {
            "not JSON": ("{", "cannot be read as JSON"),
            "no object": ([], "not an object"),
            "a field missing": (
                {k: v for k, v in valid.items() if k != "prompt"},
                "prompt",
            ),
            "another name": ({**valid, "name": "other"}, "name"),
            "a revision of no text": (
                {**valid, "project": {"repository": "psf/requests", "rev": 3}},
                "project",
            ),
            "no edits": ({**valid, "fault": {"summary": "x", "edits": []}}, "edits"),
            "an edit without old text": (
                {
                    **valid,
                    "fault": {"summary": "x", "edits": [{"file": "a", "new": "b"}]},
                },
                "edit 0",
            ),
            "an edit keeping its old text": (
                {
                    **valid,
                    "fault": {
                        "summary": "x",
                        "edits": [{**edit, "new": edit["old"] + "# more"}],
                    },
                },
                "keeps its old text",
            ),
            "no expected types": (
                {**valid, "expect": {**valid["expect"], "types": []}},
                "types",
            ),
            "basis of no list": (
                {**valid, "expect": {**valid["expect"], "basis": "phrase"}},
                "basis",
            ),
        }
        for case, (value, field) in cases.items():
            with self.subTest(case=case), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "write-hook-rw-directories.json"
                path.write_text(value if isinstance(value, str) else json.dumps(value))
                with (
                    patch.object(dogfood, "SCENARIOS", Path(directory)),
                    self.assertRaises(e2e.E2EError) as raised,
                ):
                    dogfood.scenario("write-hook-rw-directories")
                self.assertEqual("invalid_scenario", raised.exception.code)
                self.assertIn(str(path), raised.exception.detail)
                self.assertIn(field, raised.exception.detail)

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


class RunTests(unittest.TestCase):
    """``run``: the session in a directory of its own, then the evaluation."""

    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.base = Path(directory.name) / "test-write-hook-rw-directories"
        self.base.mkdir()
        (self.base / "dogfood.json").write_text(
            json.dumps(
                {
                    "scenario": "write-hook-rw-directories",
                    "project": str(self.base / "project"),
                }
            )
        )
        self.started = []

    def start(self, end: str | None):
        """A stand-in for Headless sessions' start that writes its record and ends ``end``, or
        fails with ``wait_exceeded`` when ``end`` is None."""

        def start(project, prompt, directory, rounds):
            self.started.append((project, prompt, directory, rounds))
            (directory / "session.json").write_text(json.dumps({"end": end}))
            if end is None:
                raise e2e.E2EError("wait_exceeded", "a run still runs")
            return {"end": end}

        return start

    @verifies("scenario.dogfood-scenarios.session-ends")
    def test_every_way_a_session_ends_is_evaluated_but_an_exceeded_wait(self):
        prompt = dogfood.scenario("write-hook-rw-directories")["prompt"]
        for end in ("idle", "exited", "no_session", "rounds_exhausted"):
            with (
                self.subTest(end=end),
                patch.object(dogfood.sessions, "start", self.start(end)),
                patch.object(
                    dogfood, "evaluate", return_value={"passed": False}
                ) as evaluate,
            ):
                value = dogfood.run_scenario(self.base, rounds=2)
                self.assertEqual(
                    {"session": {"end": end}, "evaluation": {"passed": False}}, value
                )
                evaluate.assert_called_once_with(self.base)
                project, given, directory, rounds = self.started[-1]
                self.assertEqual(
                    (self.base / "project", prompt, self.base / "sessions", 2),
                    (project, given, directory.parent, rounds),
                )
        with (
            patch.object(dogfood.sessions, "start", self.start(None)),
            patch.object(dogfood, "evaluate") as evaluate,
            self.assertRaises(e2e.E2EError) as raised,
        ):
            dogfood.run_scenario(self.base)
        self.assertEqual("wait_exceeded", raised.exception.code)
        evaluate.assert_not_called()

    @verifies("scenario.dogfood-scenarios.sessions-kept")
    def test_runs_started_in_the_same_second_keep_their_own_sessions(self):
        common = sys.modules["common"]
        frozen = common.datetime(2026, 10, 8, 6, 0, 0, tzinfo=common.UTC)

        class Clock:
            @staticmethod
            def now(zone):
                return frozen

        with (
            patch.object(common, "datetime", Clock),
            patch.object(dogfood.sessions, "start", self.start("idle")),
            patch.object(dogfood, "evaluate", return_value={}),
        ):
            dogfood.run_scenario(self.base)
            dogfood.run_scenario(self.base)
        first, second = (item[2] for item in self.started)
        self.assertNotEqual(first, second)
        self.assertEqual([first, second], sorted((self.base / "sessions").iterdir()))
        for directory in (first, second):
            self.assertTrue((directory / "session.json").is_file())


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
        # A files value that is no list is refused before any default, false ones included.
        malformed = (
            '{"files": "all"}',
            "{}",
            *(json.dumps({"files": value}) for value in (None, False, 0, "", {})),
        )
        for text in (None, "not JSON", "[]", *malformed):
            with self.subTest(receipt=text):
                if text is None:
                    receipt.unlink(missing_ok=True)
                else:
                    receipt.write_text(text)
                check = dogfood._untouched(record)
                self.assertFalse(check["passed"])
                self.assertIn("the install receipt", check["detail"])

    @verifies("scenario.dogfood-scenarios.receipt-changed")
    def test_a_changed_install_receipt_is_a_touched_concorde(self):
        project = self.untouched_project()
        framework = dogfood.framework_digest(project)
        installed = dogfood.installed_digests(project)
        record = self.untouched_record(project, framework, installed)
        receipt = project / ".concorde/install.json"
        value = json.loads(receipt.read_text())
        # Still a valid receipt naming the same files, with other metadata.
        receipt.write_text(json.dumps({**value, "mode": "develop"}))
        self.assertEqual(installed, dogfood.installed_digests(project))
        check = dogfood._untouched(record)
        self.assertFalse(check["passed"])
        self.assertIn(f"the install receipt {receipt} changed", check["detail"])

    @verifies("scenario.dogfood-scenarios.reports-checked")
    @verifies("scenario.dogfood-scenarios.reports-accepted")
    def test_a_refusal_is_kept_whole_with_its_standard_error(self):
        base = self.scenario_directory()
        project, concorde = base / "project", base / "concorde"
        reports = dogfood._reports(project)
        long = "x" * 2000 + " the end"
        for check, command in (
            (
                lambda: dogfood._checked(project, reports),
                project / ".concorde/bin/concorde",
            ),
            (
                lambda: dogfood._accepted(concorde, reports),
                concorde / "scripts/issues.py",
            ),
        ):
            for stdout, stderr in ((long, ""), ("", "only on standard error")):
                with self.subTest(command=command.name, stderr=bool(stderr)):
                    self.command(command, refuses=True, stdout=stdout, stderr=stderr)
                    if command.is_relative_to(concorde):
                        git(concorde, "commit", "-qam", "refuse")
                    detail = check()["detail"]
                    self.assertIn(f"one.json: {stdout or stderr}".strip(), detail)

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

    def command(
        self,
        path: Path,
        refuses: bool = False,
        stdout: str = "refused",
        stderr: str = "",
    ) -> None:
        """A stand-in for a command that checks or records a report: it logs where it ran and
        accepts, or refuses, every report, printing ``stdout`` and ``stderr``."""
        path.parent.mkdir(parents=True, exist_ok=True)
        refusal = (
            f"print({stdout!r}); print({stderr!r}, file=sys.stderr); sys.exit(1)\n"
        )
        path.write_text(
            "#!/usr/bin/env python3\nimport os, sys\n"
            f"open({str(self.root / 'intake.log')!r}, 'a').write(os.getcwd() + '\\n')\n"
            + (refusal if refuses else "print('{}')\n")
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
                    "receipt": dogfood.receipt_digest(project),
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
            "receipt": dogfood.receipt_digest(project),
            "installed": installed,
        }


if __name__ == "__main__":
    unittest.main()
