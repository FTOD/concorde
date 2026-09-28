"""The bookkeeping command records reports and dispositions for the main agent."""

from __future__ import annotations

import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from functools import cache
from pathlib import Path

from concorde.errors import link
from concorde.issues.store import list_issues, read_issue
from concorde.spec.repository import digest
from concorde.spec.verification import verifies
from tests.concorde.issues.test_store import racing_writer, refused_record_writes
from tests.concorde.support.issue_reports import report

COMMAND = Path(__file__).resolve().parents[3] / "scripts/issues.py"
REGISTRY = {
    "schema_version": 1,
    "modules": [
        {"id": "module.app", "contains": [{"target": "module.service"}]},
        {"id": "module.service", "contains": []},
    ],
}
DISPOSITION = ("--note", "n", "--evidence", "e")


@cache
def command():
    """The command loaded into this process, so that a test's patches reach its store calls."""
    spec = importlib.util.spec_from_file_location("issues_command", COMMAND)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class IssueCommandTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / ".concorde").mkdir()
        (self.root / ".concorde/config.json").write_text(
            json.dumps({"profile_version": 19})
        )
        (self.root / ".concorde/specs.json").write_text(json.dumps(REGISTRY))
        (self.root / "specs/service").mkdir(parents=True)
        (self.root / "specs/service/module.md").write_text("# Service\n")

    def run_command(self, *args):
        result = subprocess.run(
            [sys.executable, str(COMMAND), *args, "--root", str(self.root)],
            cwd=self.root,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        return result.returncode, json.loads(result.stdout)

    def run_in_process(self, *args):
        output = io.StringIO()
        with redirect_stdout(output):
            status = command().main([*args, "--root", str(self.root)])
        return status, json.loads(output.getvalue())

    def records(self):
        return {
            path.name: path.read_bytes()
            for path in (self.root / ".concorde").rglob("I-*.md")
        }

    def report_file(self, name="report.json", **changes):
        path = self.root / name
        path.write_text(
            json.dumps(report(**{"owner_target_id": "module.service", **changes}))
        )
        return str(path)

    def recorded(self, **changes):
        status, value = self.run_command(
            "report", "--file", self.report_file(**changes)
        )
        self.assertEqual(0, status, value)
        return value

    def assert_refused(self, status, code, fragments, *args, run=None):
        before = self.records()
        result, value = (run or self.run_command)(*args)
        self.assertEqual((status, code), (result, value["error"]["code"]), value)
        self.assertEqual("component", value["error"]["level"])
        self.assertTrue(value["error"]["unhandled"]["explanation"])
        for fragment in fragments:
            self.assertIn(fragment, value["error"]["detail"])
        self.assertEqual(before, self.records())
        return value

    @verifies("scenario.issues.command-report")
    def test_report_records_the_file_with_provenance_the_command_supplies(self):
        status, value = self.run_command(
            "report", "--file", self.report_file(), "--task", "task-7"
        )
        self.assertEqual(0, status, value)
        record, revision = read_issue(self.root, value["receipt"]["issue_id"])
        self.assertEqual(revision, value["revision"])
        self.assertEqual("open", record["status"])
        observation = record["reports"][0]
        self.assertEqual(
            report(owner_target_id="module.service"), observation["report"]
        )
        source = dict(observation["source"])
        self.assertTrue(source.pop("invocation_id").startswith("cli-"))
        self.assertEqual(
            {
                "agent": "main-agent",
                "operation": "issues",
                "phase": "report",
                "target_id": "module.service",
                "context_id": digest((self.root / ".concorde/specs.json").read_bytes()),
                "change_id": "task-7",
                "head": None,
            },
            source,
        )
        self.assertEqual(
            (0, {"issue": record, "revision": revision}),
            self.run_command("show", value["receipt"]["issue_id"]),
        )

    @verifies("scenario.issues.command-report")
    def test_report_records_the_git_head_of_the_project(self):
        git = ["git", "-C", str(self.root), "-c", "user.name=t", "-c", "user.email=t@t"]
        subprocess.run([*git, "init", "-q"], check=True)
        subprocess.run([*git, "commit", "-q", "--allow-empty", "-m", "x"], check=True)
        head = subprocess.run(
            [*git, "rev-parse", "HEAD"], capture_output=True, text=True, check=True
        ).stdout.strip()
        value = self.recorded()
        record, _ = read_issue(self.root, value["receipt"]["issue_id"])
        self.assertEqual(head, record["reports"][0]["source"]["head"])
        self.assertIsNone(record["reports"][0]["source"]["change_id"])

    @verifies("scenario.issues.command-report-repeated")
    def test_repeating_a_creation_is_not_an_idempotent_cli_retry(self):
        path = self.report_file()
        first_status, first = self.run_command("report", "--file", path)
        second_status, second = self.run_command("report", "--file", path)
        self.assertEqual((0, 0), (first_status, second_status))
        self.assertNotEqual(first["receipt"]["issue_id"], second["receipt"]["issue_id"])
        observations = []
        for reply in (first, second):
            record, revision = read_issue(self.root, reply["receipt"]["issue_id"])
            self.assertEqual(reply["revision"], revision)
            self.assertEqual("open", record["status"])
            self.assertEqual(1, len(record["reports"]))
            observations.append(record["reports"][0])
        self.assertEqual(observations[0]["report"], observations[1]["report"])
        self.assertNotEqual(
            observations[0]["source"]["invocation_id"],
            observations[1]["source"]["invocation_id"],
        )
        self.assertEqual(2, len(list_issues(self.root)))

    @verifies("scenario.issues.command-report-unknown-owner")
    def test_a_report_without_owner_is_filed_under_the_root_module(self):
        value = self.recorded(owner_target_id=None)
        record, _ = read_issue(self.root, value["receipt"]["issue_id"])
        self.assertIsNone(record["reports"][0]["report"]["owner_target_id"])
        self.assertEqual("module.app", record["reports"][0]["source"]["target_id"])
        self.assertEqual((0, {"errors": [], "notes": []}), self.run_command("check"))

    def origin_project(self):
        """Another project with a run directory as evidence, and the origin naming it."""
        other = tempfile.TemporaryDirectory()
        self.addCleanup(other.cleanup)
        elsewhere = Path(other.name)
        (elsewhere / ".concorde/runs/r-1").mkdir(parents=True)
        origin = {
            "project": str(elsewhere),
            "head": "a" * 40,
            "concorde_commit": "b" * 40,
            "task": "retry-limit",
        }
        return elsewhere, origin

    def written(self, directory, name, **changes):
        path = directory / name
        path.write_text(json.dumps(report(**changes)))
        return str(path)

    @verifies("scenario.issues.command-report-origin")
    def test_a_report_seen_in_another_project_keeps_its_origin_and_chain(self):
        elsewhere, origin = self.origin_project()
        chain = link(
            "main-agent",
            "main agent (task retry-limit)",
            "concorde_defect",
            "the test grant omits a used Module's tests",
            reason="scope",
            explanation="the fix lies in the Concorde repository",
            causes=[
                link(
                    "operation",
                    "test",
                    "read_refused",
                    "tests/billing/ was refused",
                    reason="permission",
                    explanation="the grant does not name it",
                )
            ],
        )
        # The report is written in the other project, outside the one recording it.
        path = self.written(
            elsewhere,
            "defect.json",
            owner_target_id=None,
            type="bug",
            subtype=None,
            evidence=[{"path": ".concorde/runs/r-1", "description": "the refused run"}],
            origin=origin,
            error_chain=chain,
        )
        status, value = self.run_command("report", "--file", path)
        self.assertEqual(0, status, value)
        record, _ = read_issue(self.root, value["receipt"]["issue_id"])
        observation = record["reports"][0]
        self.assertEqual(origin, observation["report"]["origin"])
        self.assertEqual(chain, observation["report"]["error_chain"])
        self.assertEqual("module.app", observation["source"]["target_id"])
        self.assertEqual(
            digest((self.root / ".concorde/specs.json").read_bytes()),
            observation["source"]["context_id"],
        )

    @verifies("scenario.issues.command-report-origin-missing-evidence")
    def test_evidence_absent_from_the_origin_project_is_refused(self):
        elsewhere, origin = self.origin_project()
        # The path exists in this project, but the origin project is where it must exist.
        (self.root / ".concorde/runs/r-2").mkdir(parents=True)
        absent = self.written(
            elsewhere,
            "absent.json",
            evidence=[{"path": ".concorde/runs/r-2", "description": "x"}],
            origin=origin,
        )
        self.assert_refused(
            1,
            "missing_evidence",
            ["absent.json", ".concorde/runs/r-2", str(elsewhere), "origin project"],
            "report",
            "--file",
            absent,
        )

    @verifies("scenario.issues.command-report-invalid-error-chain")
    def test_an_error_chain_outside_the_error_contract_is_refused(self):
        elsewhere, origin = self.origin_project()
        broken = self.written(
            elsewhere,
            "broken.json",
            evidence=[{"path": ".concorde/runs/r-1", "description": "the run"}],
            origin=origin,
            error_chain={"code": "x"},
        )
        self.assert_refused(
            1,
            "invalid_issue",
            ["broken.json", "error_chain"],
            "report",
            "--file",
            broken,
        )

    @verifies("scenario.issues.command-report-check")
    def test_check_answers_valid_and_records_nothing(self):
        status, value = self.run_command(
            "report", "--file", self.report_file(), "--check"
        )
        self.assertEqual(0, status, value)
        self.assertEqual(
            {
                "valid": True,
                "file": str(self.root / "report.json"),
                "report_key": "missing-retry",
                "reporting_module": "module.service",
            },
            value,
        )
        self.assertEqual([], list_issues(self.root))

    @verifies("scenario.issues.command-report-check-refused")
    def test_check_refuses_a_failing_report_as_recording_would(self):
        incomplete = report()
        del incomplete["report_key"]
        (self.root / "incomplete.json").write_text(json.dumps(incomplete))
        absent = self.report_file(
            "absent.json", evidence=[{"path": "specs/absent.md", "description": "x"}]
        )
        for path, code, fragments in (
            (
                str(self.root / "incomplete.json"),
                "invalid_issue",
                ["incomplete.json", "report_key", "required field is missing"],
            ),
            (absent, "missing_evidence", ["absent.json", "specs/absent.md"]),
        ):
            with self.subTest(code=code):
                checked = self.assert_refused(
                    1, code, fragments, "report", "--file", path, "--check"
                )
                recorded = self.assert_refused(1, code, [], "report", "--file", path)
                self.assertEqual(
                    recorded["error"]["detail"], checked["error"]["detail"]
                )
        self.assertEqual([], list_issues(self.root))

    @verifies("scenario.issues.command-append")
    def test_append_at_the_current_revision_adds_the_report(self):
        first = self.recorded()
        identifier = first["receipt"]["issue_id"]
        appended = self.recorded(
            report_key="later",
            type="bug",
            subtype=None,
            title="Retries are lost",
            issue_id=identifier,
            expected_revision=first["revision"],
        )
        self.assertEqual(identifier, appended["receipt"]["issue_id"])
        record, revision = read_issue(self.root, identifier)
        self.assertEqual(revision, appended["revision"])
        self.assertEqual(2, len(record["reports"]))
        self.assertEqual("open", record["status"])
        row = list_issues(self.root)[0]
        self.assertEqual(
            ("bug", None, "Retries are lost", "module.service"),
            (row["type"], row["subtype"], row["title"], row["owner_target_id"]),
        )

    @verifies("scenario.issues.command-append-stale")
    def test_append_at_an_old_revision_is_refused(self):
        first = self.recorded()
        identifier = first["receipt"]["issue_id"]
        appended = self.recorded(
            report_key="later", issue_id=identifier, expected_revision=first["revision"]
        )
        stale = self.report_file(
            "stale.json",
            report_key="stale",
            issue_id=identifier,
            expected_revision=first["revision"],
        )
        self.assert_refused(
            1,
            "stale_issue",
            [identifier, first["revision"], appended["revision"]],
            "report",
            "--file",
            stale,
        )
        record, revision = read_issue(self.root, identifier)
        self.assertEqual((2, appended["revision"]), (len(record["reports"]), revision))

    @verifies("scenario.issues.command-close", "scenario.issues.command-reopen")
    def test_close_and_reopen_record_main_agent_dispositions(self):
        identifier = self.recorded()["receipt"]["issue_id"]
        status, closed = self.run_command(
            "close",
            identifier,
            "--reason",
            "resolved",
            "--note",
            "Retries are specified",
            "--evidence",
            "commit abc123",
            "check.issues.store passed",
        )
        self.assertEqual(0, status, closed)
        record, revision = read_issue(self.root, identifier)
        self.assertEqual(
            {"issue_id": identifier, "status": "closed", "revision": revision}, closed
        )
        disposition = record["dispositions"][0]
        self.assertEqual(
            ("resolved", "main-agent", ["commit abc123", "check.issues.store passed"]),
            (disposition["reason"], disposition["actor"], disposition["evidence"]),
        )
        status, reopened = self.run_command(
            "reopen", identifier, "--note", "Regressed", "--evidence", "failing test"
        )
        self.assertEqual(0, status, reopened)
        record, revision = read_issue(self.root, identifier)
        self.assertEqual(("open", revision), (reopened["status"], reopened["revision"]))
        self.assertEqual("reopened", record["dispositions"][-1]["reason"])
        self.assertEqual(1, len(record["reports"]))

    @verifies("scenario.issues.command-close-duplicate")
    def test_duplicate_names_another_open_issue(self):
        first = self.recorded()["receipt"]["issue_id"]
        second = self.recorded(report_key="again")["receipt"]["issue_id"]
        status, value = self.run_command(
            "close",
            second,
            "--reason",
            "duplicate",
            "--duplicate-of",
            first,
            *DISPOSITION,
        )
        self.assertEqual(0, status, value)
        disposition = read_issue(self.root, second)[0]["dispositions"][0]
        self.assertEqual(
            ("duplicate", first), (disposition["reason"], disposition["duplicate_of"])
        )
        self.assertEqual("open", read_issue(self.root, first)[0]["status"])

    @verifies("scenario.issues.command-close-duplicate-of-closed")
    def test_a_duplicate_of_a_closed_issue_is_refused(self):
        closed = self.recorded()["receipt"]["issue_id"]
        self.run_command("close", closed, "--reason", "not-actionable", *DISPOSITION)
        third = self.recorded(report_key="third")["receipt"]["issue_id"]
        self.assert_refused(
            1,
            "invalid_issue",
            [closed, "closed"],
            "close",
            third,
            "--reason",
            "duplicate",
            "--duplicate-of",
            closed,
            *DISPOSITION,
        )
        self.assertEqual("open", read_issue(self.root, third)[0]["status"])

    @verifies("scenario.issues.command-usage")
    def test_unusable_arguments_exit_2_and_name_the_argument(self):
        identifier = self.recorded()["receipt"]["issue_id"]
        for args, fragments in (
            (("report",), ["--file"]),
            (("close", identifier, "--reason", "fixed", *DISPOSITION), ["--reason"]),
            (("close", identifier, "--reason", "duplicate", *DISPOSITION), ["--dup"]),
            (("close", identifier, "--reason", "resolved", "--note", "n"), ["--evi"]),
            (("reopen", identifier, "--note", " ", "--evidence", "e"), ["--note"]),
            (("reopen", identifier, "--note", "n", "--evidence", "e", "e"), ["'e'"]),
            (("show",), ["issue_id"]),
            (("list", identifier), [identifier]),
        ):
            with self.subTest(args=args):
                self.assert_refused(2, "usage", fragments, *args)

    @verifies("scenario.issues.command-unreadable-file")
    def test_an_unreadable_report_file_exits_2(self):
        (self.root / "latin.json").write_bytes(b'{"title": "caf\xe9"}')
        for name in ("absent.json", "latin.json"):
            with self.subTest(name=name):
                self.assert_refused(
                    2,
                    "unreadable_file",
                    [name],
                    "report",
                    "--file",
                    str(self.root / name),
                )

    @verifies("scenario.issues.command-not-a-project")
    def test_a_directory_that_is_not_a_project_exits_2(self):
        identifier = self.recorded()["receipt"]["issue_id"]
        path = self.report_file("next.json", report_key="next")
        (self.root / ".concorde/config.json").unlink()
        for args in (
            ("list",),
            ("show", identifier),
            ("check",),
            ("report", "--file", path),
            ("close", identifier, "--reason", "resolved", *DISPOSITION),
            ("reopen", identifier, *DISPOSITION),
        ):
            with self.subTest(args=args):
                self.assert_refused(2, "not_a_project", [str(self.root)], *args)

    @verifies("scenario.issues.command-refused")
    def test_a_report_file_with_an_invalid_field_is_refused(self):
        blank = self.report_file("blank.json", title=" ")
        half = self.report_file("half.json", issue_id="I-" + "0" * 32)
        for path, fragments in (
            (blank, ["blank.json", "title"]),
            (half, ["half.json", "issue_id", "expected_revision"]),
        ):
            with self.subTest(path=path):
                self.assert_refused(
                    1, "invalid_issue", fragments, "report", "--file", path
                )
        self.assertEqual([], list_issues(self.root))

    @verifies("scenario.issues.command-report-unregistered-owner")
    def test_a_report_naming_an_unregistered_owner_is_refused(self):
        foreign = self.report_file("foreign.json", owner_target_id="module.foreign")
        self.assert_refused(
            1,
            "unknown_owner",
            ["foreign.json", "owner_target_id", "module.foreign"],
            "report",
            "--file",
            foreign,
        )

    @verifies("scenario.issues.command-report-missing-evidence")
    def test_a_report_naming_absent_evidence_is_refused(self):
        absent = self.report_file(
            "absent.json", evidence=[{"path": "specs/absent.md", "description": "x"}]
        )
        self.assert_refused(
            1,
            "missing_evidence",
            ["absent.json", "evidence/0/path", "specs/absent.md"],
            "report",
            "--file",
            absent,
        )

    @verifies("scenario.issues.command-unknown-issue")
    def test_naming_an_absent_issue_is_refused(self):
        identifier = self.recorded()["receipt"]["issue_id"]
        unknown = "I-" + "0" * 32
        append = self.report_file(
            "append.json",
            report_key="append",
            issue_id=unknown,
            expected_revision="sha256:" + "0" * 64,
        )
        for args in (
            ("show", unknown),
            ("close", unknown, "--reason", "resolved", *DISPOSITION),
            ("reopen", unknown, *DISPOSITION),
            ("close", identifier, "--reason", "duplicate", "--duplicate-of", unknown)
            + DISPOSITION,
            ("report", "--file", append),
        ):
            with self.subTest(args=args):
                self.assert_refused(1, "unknown_issue", [unknown], *args)
        self.assertEqual("open", read_issue(self.root, identifier)[0]["status"])

    @verifies("scenario.issues.command-malformed-identity")
    def test_a_malformed_issue_identity_is_refused(self):
        self.assert_refused(1, "invalid_issue", ["'I-1'"], "show", "I-1")

    @verifies("scenario.issues.command-close-closed")
    def test_closing_a_closed_issue_is_refused(self):
        identifier = self.recorded()["receipt"]["issue_id"]
        self.run_command("close", identifier, "--reason", "resolved", *DISPOSITION)
        self.assert_refused(
            1,
            "closed_issue",
            [identifier],
            "close",
            identifier,
            "--reason",
            "resolved",
            *DISPOSITION,
        )
        self.assertEqual(1, len(read_issue(self.root, identifier)[0]["dispositions"]))

    @verifies("scenario.issues.command-append-closed")
    def test_appending_to_a_closed_issue_is_refused(self):
        first = self.recorded()
        identifier = first["receipt"]["issue_id"]
        status, closed = self.run_command(
            "close", identifier, "--reason", "resolved", *DISPOSITION
        )
        self.assertEqual(0, status, closed)
        later = self.report_file(
            "later.json",
            report_key="later",
            issue_id=identifier,
            expected_revision=closed["revision"],
        )
        self.assert_refused(1, "closed_issue", [identifier], "report", "--file", later)
        self.assertEqual(1, len(read_issue(self.root, identifier)[0]["reports"]))

    @verifies("scenario.issues.command-reopen-open")
    def test_reopening_an_open_issue_is_refused(self):
        identifier = self.recorded()["receipt"]["issue_id"]
        self.assert_refused(
            1, "open_issue", [identifier], "reopen", identifier, *DISPOSITION
        )
        self.assertEqual([], read_issue(self.root, identifier)[0]["dispositions"])

    @verifies("scenario.issues.command-close-self-duplicate")
    def test_an_issue_named_as_its_own_duplicate_is_refused(self):
        identifier = self.recorded()["receipt"]["issue_id"]
        self.assert_refused(
            1,
            "invalid_issue",
            [identifier, "itself"],
            "close",
            identifier,
            "--reason",
            "duplicate",
            "--duplicate-of",
            identifier,
            *DISPOSITION,
        )
        self.assertEqual("open", read_issue(self.root, identifier)[0]["status"])

    @verifies("scenario.issues.command-write-failed")
    def test_a_refused_record_write_is_an_environment_error(self):
        self.recorded()
        with refused_record_writes():
            value = self.assert_refused(
                1,
                "io_error",
                [".concorde/issues/I-"],
                "report",
                "--file",
                self.report_file("next.json", report_key="next"),
                run=self.run_in_process,
            )
        self.assertEqual("environment", value["error"]["unhandled"]["reason"])
        self.assertEqual(1, len(list_issues(self.root)))

    @verifies("scenario.issues.command-write-raced")
    def test_a_record_changed_during_the_write_is_stale(self):
        first = self.recorded()
        identifier = first["receipt"]["issue_id"]
        later = self.report_file(
            "later.json",
            report_key="later",
            issue_id=identifier,
            expected_revision=first["revision"],
        )
        with racing_writer() as left:
            status, value = self.run_in_process("report", "--file", later)
        self.assertEqual((1, "stale_issue"), (status, value["error"]["code"]), value)
        self.assertIn(identifier, value["error"]["detail"])
        self.assertEqual(left[-1], (self.root / first["receipt"]["path"]).read_bytes())

    @verifies("scenario.issues.command-write-failed")
    def test_a_read_only_issue_directory_is_an_environment_error(self):
        if os.geteuid() == 0:
            self.skipTest("root writes into a read-only directory")
        self.recorded()
        directory = self.root / ".concorde/issues"
        directory.chmod(0o555)
        self.addCleanup(directory.chmod, 0o755)
        value = self.assert_refused(
            1,
            "io_error",
            [".concorde/issues/I-"],
            "report",
            "--file",
            self.report_file("next.json", report_key="next"),
        )
        self.assertEqual("environment", value["error"]["unhandled"]["reason"])
        directory.chmod(0o755)
        self.assertEqual(1, len(list_issues(self.root)))


if __name__ == "__main__":
    unittest.main()
