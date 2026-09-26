"""The bookkeeping command records reports and dispositions for the main agent."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from concorde.errors import link
from concorde.issues.store import list_issues, read_issue
from concorde.spec.repository import digest
from concorde.spec.verification import verifies
from tests.concorde.support.issue_reports import report

COMMAND = Path(__file__).resolve().parents[3] / "scripts/issues.py"
REGISTRY = {
    "schema_version": 1,
    "modules": [
        {"id": "module.app", "contains": [{"target": "module.service"}]},
        {"id": "module.service", "contains": []},
    ],
}


class IssueCommandTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / ".concorde").mkdir()
        (self.root / ".concorde/config.json").write_text(
            json.dumps({"registry": ".concorde/specs.json"})
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

    def assert_refused(self, status, code, fragments, *args):
        before = sorted(p.name for p in (self.root / ".concorde").rglob("I-*.md"))
        result, value = self.run_command(*args)
        self.assertEqual((status, code), (result, value["error"]["code"]), value)
        self.assertEqual("component", value["error"]["level"])
        self.assertTrue(value["error"]["unhandled"]["explanation"])
        for fragment in fragments:
            self.assertIn(fragment, value["error"]["detail"])
        after = sorted(p.name for p in (self.root / ".concorde").rglob("I-*.md"))
        self.assertEqual(before, after)
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

    @verifies("scenario.issues.command-report-unknown-owner")
    def test_a_report_without_owner_is_filed_under_the_root_module(self):
        value = self.recorded(owner_target_id=None)
        record, _ = read_issue(self.root, value["receipt"]["issue_id"])
        self.assertIsNone(record["reports"][0]["report"]["owner_target_id"])
        self.assertEqual("module.app", record["reports"][0]["source"]["target_id"])
        self.assertEqual((0, {"errors": [], "notes": []}), self.run_command("check"))

    @verifies("scenario.issues.command-report-origin")
    def test_a_report_seen_in_another_project_keeps_its_origin_and_chain(self):
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
        evidence = [{"path": ".concorde/runs/r-1", "description": "the refused run"}]
        # The report is written in the other project, outside the one recording it.
        path = elsewhere / "defect.json"
        path.write_text(
            json.dumps(
                report(
                    owner_target_id=None,
                    type="bug",
                    subtype=None,
                    evidence=evidence,
                    origin=origin,
                    error_chain=chain,
                )
            )
        )
        status, value = self.run_command("report", "--file", str(path))
        self.assertEqual(0, status, value)
        record, _ = read_issue(self.root, value["receipt"]["issue_id"])
        observation = record["reports"][0]
        self.assertEqual(origin, observation["report"]["origin"])
        self.assertEqual(chain, observation["report"]["error_chain"])
        self.assertEqual("module.app", observation["source"]["target_id"])
        # Evidence absent from the origin project is refused, naming that project.
        absent = elsewhere / "absent.json"
        absent.write_text(
            json.dumps(
                report(
                    report_key="absent",
                    evidence=[{"path": ".concorde/runs/r-2", "description": "x"}],
                    origin=origin,
                )
            )
        )
        self.assert_refused(
            1,
            "missing_evidence",
            [".concorde/runs/r-2", str(elsewhere), "origin project"],
            "report",
            "--file",
            str(absent),
        )
        broken = elsewhere / "broken.json"
        broken.write_text(
            json.dumps(
                report(
                    report_key="broken",
                    evidence=evidence,
                    origin=origin,
                    error_chain={"code": "x"},
                )
            )
        )
        self.assert_refused(
            1,
            "invalid_issue",
            ["broken.json", "error_chain"],
            "report",
            "--file",
            str(broken),
        )

    @verifies("scenario.issues.command-append")
    def test_append_needs_the_current_revision_and_an_open_issue(self):
        first = self.recorded()
        identifier = first["receipt"]["issue_id"]
        appended = self.recorded(
            report_key="later",
            type="bug",
            subtype=None,
            issue_id=identifier,
            expected_revision=first["revision"],
        )
        self.assertEqual(identifier, appended["receipt"]["issue_id"])
        self.assertEqual(read_issue(self.root, identifier)[1], appended["revision"])
        self.assertEqual(2, len(read_issue(self.root, identifier)[0]["reports"]))
        self.assertEqual("bug", list_issues(self.root)[0]["type"])
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
        self.assertEqual(2, len(read_issue(self.root, identifier)[0]["reports"]))

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

    @verifies("scenario.issues.command-close")
    def test_duplicate_names_another_open_issue(self):
        first = self.recorded()["receipt"]["issue_id"]
        second = self.recorded(report_key="again")["receipt"]["issue_id"]
        arguments = ("--note", "Same gap", "--evidence", "comparison")
        status, value = self.run_command(
            "close",
            second,
            "--reason",
            "duplicate",
            "--duplicate-of",
            first,
            *arguments,
        )
        self.assertEqual(0, status, value)
        self.assertEqual(
            first, read_issue(self.root, second)[0]["dispositions"][0]["duplicate_of"]
        )
        self.run_command("close", first, "--reason", "not-actionable", *arguments)
        third = self.recorded(report_key="third")["receipt"]["issue_id"]
        self.assert_refused(
            1,
            "invalid_issue",
            [first, "closed"],
            "close",
            third,
            "--reason",
            "duplicate",
            "--duplicate-of",
            first,
            *arguments,
        )
        self.assertEqual("open", read_issue(self.root, third)[0]["status"])

    @verifies("scenario.issues.command-usage")
    def test_unusable_requests_exit_2_and_name_the_problem(self):
        identifier = self.recorded()["receipt"]["issue_id"]
        disposition = ("--note", "n", "--evidence", "e")
        for args, fragments in (
            (("report",), ["--file"]),
            (("report", "--file", str(self.root / "absent.json")), ["absent.json"]),
            (("close", identifier, "--reason", "fixed", *disposition), ["--reason"]),
            (("close", identifier, "--reason", "duplicate", *disposition), ["--dup"]),
            (("close", identifier, "--reason", "resolved", "--note", "n"), ["--evi"]),
            (("reopen", identifier, "--note", " ", "--evidence", "e"), ["--note"]),
            (("reopen", identifier, "--note", "n", "--evidence", "e", "e"), ["'e'"]),
            (("show",), ["issue_id"]),
            (("list", identifier), [identifier]),
        ):
            with self.subTest(args=args):
                code = "unreadable_file" if "absent.json" in args[-1] else "usage"
                self.assert_refused(2, code, fragments, *args)
        (self.root / ".concorde/config.json").unlink()
        self.assert_refused(2, "not_a_project", [str(self.root)], "list")

    @verifies("scenario.issues.command-refused")
    def test_refused_operations_exit_1_name_the_issue_file_or_field(self):
        identifier = self.recorded()["receipt"]["issue_id"]
        unknown = "I-" + "0" * 32
        disposition = ("--note", "n", "--evidence", "e")
        blank = self.report_file("blank.json", title=" ")
        foreign = self.report_file("foreign.json", owner_target_id="module.foreign")
        absent = self.report_file(
            "absent.json", evidence=[{"path": "specs/absent.md", "description": "x"}]
        )
        missing = self.report_file("missing.json", issue_id=unknown)
        for args, code, fragments in (
            (("report", "--file", blank), "invalid_issue", ["blank.json", "title"]),
            (
                ("report", "--file", foreign),
                "unknown_owner",
                ["foreign.json", "owner_target_id", "module.foreign"],
            ),
            (
                ("report", "--file", absent),
                "missing_evidence",
                ["absent.json", "evidence/0/path", "specs/absent.md"],
            ),
            (
                ("report", "--file", missing),
                "invalid_issue",
                ["missing.json", "issue_id", "expected_revision"],
            ),
            (("show", unknown), "unknown_issue", [unknown]),
            (("show", "I-1"), "invalid_issue", ["'I-1'"]),
            (("reopen", identifier, *disposition), "open_issue", [identifier]),
            (
                (
                    "close",
                    identifier,
                    "--reason",
                    "duplicate",
                    "--duplicate-of",
                    identifier,
                )
                + disposition,
                "invalid_issue",
                [identifier, "itself"],
            ),
            (
                (
                    "close",
                    identifier,
                    "--reason",
                    "duplicate",
                    "--duplicate-of",
                    unknown,
                )
                + disposition,
                "unknown_issue",
                [unknown],
            ),
        ):
            with self.subTest(args=args):
                self.assert_refused(1, code, fragments, *args)
        self.run_command("close", identifier, "--reason", "resolved", *disposition)
        self.assert_refused(
            1,
            "closed_issue",
            [identifier],
            "close",
            identifier,
            "--reason",
            "resolved",
            *disposition,
        )
        record, revision = read_issue(self.root, identifier)
        self.assertEqual((1, 1), (len(record["reports"]), len(record["dispositions"])))
        self.assertEqual(1, len(list_issues(self.root)))


if __name__ == "__main__":
    unittest.main()
