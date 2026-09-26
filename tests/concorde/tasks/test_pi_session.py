"""The pi task session: its boundary, its rounds, their supervisor and the outcomes it records.

A fake ``pi`` plays each round; what the boundary extension enforces inside a real pi process is
exercised live. The boundary's decisions run under Node when Node is available.
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from concorde.harness import pi_backend
from concorde.spec.schema import ContractError, validate
from concorde.spec.verification import verifies
from concorde.tasks import cli, pi_session, store
from tests.concorde.support.operation_project import OperationProject
from tests.concorde.support.paths import REPOSITORY_ROOT

FAKE = Path(__file__).with_name("fake_pi_session.py")
COMMIT = "a" * 40
SESSION_VARIABLES = (
    "CONCORDE_CLIENT",
    "CLAUDECODE",
    "PI_SESSION_ID",
    "PI_CODING_AGENT",
)


def fake_which(name: str) -> str | None:
    return f"/usr/bin/{name}" if name in ("bwrap", "socat") else None


def plan(value: dict) -> str:
    return "FAKE-PLAN: " + json.dumps(value)


TASK_CONTRACTS = "specs/concorde/tasks/contracts.md"
SESSION_CONTRACTS = "specs/concorde/agents/task-session/contracts.md"


def contract(heading: str, document: str = TASK_CONTRACTS) -> dict:
    text = (REPOSITORY_ROOT / document).read_text()
    section = text.split(heading, 1)[1] if heading else text
    return json.loads(section.split("```concorde-contract\n", 1)[1].split("```")[0])


def report_cases():
    delivered = {
        "status": "delivered",
        "summary": "Delivered.",
        "commit": COMMIT,
        "escalations": [],
        "decisions": [],
        "open": [],
    }
    escalated = dict(delivered, status="escalated", commit=None, escalations=[1])
    cases = [
        ("delivered", delivered, True),
        ("escalated", escalated, True),
        ("sha256", dict(delivered, commit="b" * 64), True),
    ]
    for name, report in (("delivered", delivered), ("escalated", escalated)):
        for field in report:
            cases.append(
                (
                    f"{name} missing {field}",
                    {k: v for k, v in report.items() if k != field},
                    False,
                )
            )
        for changes in (
            {"summary": ""},
            {"summary": None},
            {"decisions": [""]},
            {"open": [1]},
            {"open": None},
            {"extra": True},
            {"status": "done"},
            {"commit": ""},
        ):
            cases.append((f"{name} {changes}", {**report, **changes}, False))
    for changes in (
        {"commit": None},
        {"commit": "a" * 39},
        {"commit": "g" * 40},
        {"commit": COMMIT + "\n"},
        {"escalations": [1]},
        {"escalations": None},
    ):
        cases.append((f"delivered {changes}", {**delivered, **changes}, False))
    for changes in (
        {"commit": COMMIT},
        {"escalations": []},
        {"escalations": [1, 1]},
        {"escalations": [0]},
        {"escalations": [-1]},
        {"escalations": [1.5]},
        {"escalations": [True]},
        {"escalations": ["1"]},
    ):
        cases.append((f"escalated {changes}", {**escalated, **changes}, False))
    return cases


class PiSessionTests(unittest.TestCase):
    def setUp(self):
        self.project = OperationProject(self)
        self.root = self.project.root
        base = self.project.base
        self.pi = base / "pi"
        self.pi.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{FAKE}" "$@"\n')
        self.pi.chmod(0o755)
        self.runtime = base / "sandbox-runtime"
        (self.runtime / "dist").mkdir(parents=True)
        (self.runtime / "dist/index.js").write_text("export {};\n")
        self.log = base / "fake-pi.jsonl"
        environ = patch.dict(
            os.environ,
            {
                "CONCORDE_PI": str(self.pi),
                "CONCORDE_SANDBOX_RUNTIME": str(self.runtime),
                "FAKE_PI_LOG": str(self.log),
            },
        )
        environ.start()
        self.addCleanup(environ.stop)
        which = patch.object(pi_backend, "which", side_effect=fake_which)
        which.start()
        self.addCleanup(which.stop)
        self.addCleanup(self.remove_short_tmp)
        self.addCleanup(self.stop_rounds)

    def remove_short_tmp(self):
        directory = self.root / ".concorde/tasks"
        for session in directory.glob("*.session"):
            shutil.rmtree(pi_session.short_tmp(session), ignore_errors=True)

    def stop_rounds(self):
        """Leave no supervisor of a test behind."""
        for task in store.list_tasks(self.root):
            found = pi_session.latest(task)
            busy = pi_session.running(found)
            if busy:
                pi_session.stop(self.root, task["id"])
                deadline = time.monotonic() + 5
                while (
                    pi_session._alive(busy["supervisor_pid"])
                    and time.monotonic() < deadline
                ):
                    time.sleep(0.05)
                self.assertFalse(pi_session._alive(busy["supervisor_pid"]))

    def open(self, task: str, steps: dict) -> Path:
        self.project.open_task(
            task, goal=f"Let reports carry a severity. {plan(steps)}"
        )
        return self.project.worktree(task)

    def start(self, task: str, **options) -> dict:
        return pi_session.start(
            self.root, task, "main-7", home=self.project.home, **options
        )

    def wait(self, task: str, number: int, timeout: float = 30.0) -> dict:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            found = pi_session.latest(store.load_task(self.root, task))
            rounds = found["rounds"] if found else []
            if len(rounds) >= number and rounds[number - 1]["status"] != "running":
                return rounds[number - 1]
            time.sleep(0.1)
        self.fail(f"round {number} of {task} did not end within {timeout}s")

    def calls(self) -> list[dict]:
        if not self.log.is_file():
            return []
        return [json.loads(line) for line in self.log.read_text().splitlines()]

    def escalate(self, task: str, level: str = "task-session") -> None:
        from concorde import errors

        store.escalate(
            self.root,
            task,
            errors.link(
                level,
                f"{level} (task {task})",
                "needs_decision",
                "whether warnings block delivery",
                reason="decision",
                explanation="the Spec does not say",
            ),
        )

    def deliver(self, task: str, commit: str = COMMIT) -> None:
        def change(record):
            record.setdefault("deliveries", []).append(
                {
                    "run_id": "r-20260926T000000-delivery-00000000",
                    "commit": commit,
                    "bundle": f".concorde/evidence/{task}/1.json",
                    "readiness_run": "r-20260926T000000-delivery-00000000",
                    "at": store.now(),
                }
            )
            return record

        store.update(self.root, task, change)

    @verifies("scenario.task-session.pi-start")
    def test_start_a_pi_task_session(self):
        worktree = self.open(
            "t1",
            {
                "actions": [["bash", {"command": "concorde run implement --task t1"}]],
                "report": {
                    "status": "escalated",
                    "summary": "Implemented the levels; one question is open.",
                    "commit": None,
                    "escalations": [1],
                    "decisions": ["Named the enum Severity."],
                    "open": ["Whether warnings block delivery."],
                },
            },
        )
        self.escalate("t1")
        started = self.start("t1")
        directory = self.root / ".concorde/tasks/t1.session"
        self.assertEqual(
            ("pi", "task-t1", "main-7", str(directory), None),
            (
                started["program"],
                started["name"],
                started["main"],
                started["directory"],
                started["model"],
            ),
        )
        self.assertEqual("running", started["rounds"][0]["status"])
        ended = self.wait("t1", 1)
        self.assertEqual("escalated", ended["status"], ended)
        self.assertEqual([1], ended["report"]["escalations"])
        self.assertIsNone(ended["error"])
        boundary = (directory / "boundary.ts").read_text()
        decision_log = os.path.realpath(self.root / ".concorde/tasks/t1.decisions.md")
        self.assertIn(json.dumps(os.path.realpath(worktree)), boundary)
        self.assertIn(json.dumps(decision_log), boundary)
        self.assertIn(json.dumps(str(self.runtime / "dist/index.js")), boundary)
        self.assertNotIn("{} as SessionPolicy", boundary)
        for name in ("pi_policy.ts", "pi_session_policy.ts"):
            self.assertTrue((directory / name).is_file(), name)
        [call] = self.calls()
        argv = call["argv"]
        self.assertEqual(["-p", "--mode", "json", "--approve", "-e"], argv[:5])
        self.assertEqual(str(directory / "boundary.ts"), argv[5])
        self.assertEqual(str(directory / "pi"), argv[argv.index("--session-dir") + 1])
        self.assertEqual(started["id"], argv[argv.index("--session-id") + 1])
        self.assertNotIn("--model", argv)
        self.assertNotIn("--no-extensions", argv)
        self.assertEqual(os.path.realpath(worktree), os.path.realpath(call["cwd"]))
        tmp = pi_session.short_tmp(directory)
        self.assertLess(len(str(tmp / "srt-mux-4194304-0.sock")), 108)
        self.assertEqual(0o700, tmp.stat().st_mode & 0o777)
        self.assertEqual(
            ("t1", "pi", str(tmp)),
            (
                call["env"]["CONCORDE_TASK_SESSION"],
                call["env"]["CONCORDE_CLIENT"],
                call["env"]["TMPDIR"],
            ),
        )
        self.assertEqual(str(tmp), call["env"]["CLAUDE_CODE_TMPDIR"])
        self.assertTrue((self.root / ".concorde/runs").is_dir())
        self.assertEqual(str(self.log), call["env"]["FAKE_PI_LOG"])
        self.assertIn("You work in rounds", call["prompt"])
        self.assertIn("Let reports carry a severity.", call["prompt"])
        self.assertIn(str(worktree), call["prompt"])
        self.assertIn("`main-7`", call["prompt"])
        progress = json.loads((directory / "status.json").read_text())
        self.assertEqual(
            ("task-session", "finished", "escalated", 1),
            (
                progress["kind"],
                progress["phase"],
                progress["status"],
                progress["round"],
            ),
        )
        self.assertEqual("concorde_report", progress["last_action"]["tool"])
        events = Path(ended["events"]).read_text()
        self.assertIn("concorde run implement --task t1", events)
        record = store.load_task(self.root, "t1")
        validate(record, contract("")["schema"])

    @verifies("scenario.task-session.pi-start")
    def test_a_machine_without_pi_starts_no_session(self):
        self.open("t1", {})
        before = store.load_task(self.root, "t1")
        missing = patch.dict(
            os.environ,
            {
                "CONCORDE_PI": str(self.project.base / "nowhere"),
                "CONCORDE_SANDBOX_RUNTIME": str(self.project.base / "no-runtime"),
            },
        )
        with missing, self.assertRaises(store.TaskError) as raised:
            self.start("t1")
        self.assertEqual("session_failed", raised.exception.code)
        self.assertIn("nowhere", str(raised.exception))
        self.assertIn("sandbox-runtime", str(raised.exception))
        self.assertEqual(before, store.load_task(self.root, "t1"))

    @verifies("scenario.task-session.pi-rounds")
    def test_the_answer_starts_the_next_round(self):
        self.open(
            "t1",
            {
                "report": {
                    "status": "escalated",
                    "summary": "One question.",
                    "commit": None,
                    "escalations": [1],
                    "decisions": [],
                    "open": [],
                }
            },
        )
        self.escalate("t1")
        started = self.start("t1")
        self.wait("t1", 1)
        self.deliver("t1")
        answered = pi_session.answer(
            self.root,
            "t1",
            "Warnings do not block. "
            + plan(
                {
                    "report": {
                        "status": "delivered",
                        "summary": "Delivered.",
                        "commit": COMMIT,
                        "escalations": [],
                        "decisions": [],
                        "open": [],
                    }
                }
            ),
        )
        self.assertEqual(2, len(answered["rounds"]))
        second = self.wait("t1", 2)
        self.assertEqual(
            ("delivered", COMMIT), (second["status"], second["report"]["commit"])
        )
        self.assertEqual("answer", second["prompt"])
        first, again = self.calls()
        session_id = first["argv"][first["argv"].index("--session-id") + 1]
        self.assertEqual(started["id"], session_id)
        self.assertEqual(
            session_id, again["argv"][again["argv"].index("--session-id") + 1]
        )
        self.assertIn("The main agent's answer", again["prompt"])
        self.assertIn("Warnings do not block.", again["prompt"])
        self.assertNotIn("You work in rounds", again["prompt"])
        validate(store.load_task(self.root, "t1"), contract("")["schema"])

    @verifies("scenario.task-session.pi-rounds")
    def test_one_round_runs_at_a_time(self):
        self.open("t1", {"sleep": 30})
        self.start("t1")
        with self.assertRaises(store.TaskError) as raised:
            pi_session.answer(self.root, "t1", "more")
        self.assertEqual("session_busy", raised.exception.code)
        with self.assertRaises(store.TaskError) as raised:
            self.start("t1")
        self.assertEqual("session_busy", raised.exception.code)
        self.open("t2", {})
        with self.assertRaises(store.TaskError) as raised:
            pi_session.answer(self.root, "t2", "more")
        self.assertEqual("no_session", raised.exception.code)

    @verifies("scenario.task-session.pi-stop")
    def test_stop_a_running_round(self):
        self.open("t1", {"actions": [["read", {"path": "README.md"}]], "sleep": 60})
        started = self.start("t1")
        pid = started["rounds"][0]["supervisor_pid"]
        deadline = time.monotonic() + 10
        while not self.calls() and time.monotonic() < deadline:
            time.sleep(0.1)
        began = time.monotonic()
        stopped = pi_session.stop(self.root, "t1")
        self.assertEqual("stopped", stopped["rounds"][0]["status"])
        self.assertLess(time.monotonic() - began, pi_session.STOP_GRACE)
        self.assertIn({"signal": "SIGTERM"}, self.calls())
        deadline = time.monotonic() + 10
        while pi_session._alive(pid) and time.monotonic() < deadline:
            time.sleep(0.1)
        self.assertFalse(pi_session._alive(pid))
        with self.assertRaises(store.TaskError) as raised:
            pi_session.stop(self.root, "t1")
        self.assertEqual("session_idle", raised.exception.code)

    @verifies("scenario.task-session.pi-stop")
    def test_a_pi_that_ignores_sigterm_is_killed_after_the_grace_period(self):
        self.open("t1", {"sleep": 60, "ignore_term": True})
        self.start("t1")
        deadline = time.monotonic() + 10
        while not self.calls() and time.monotonic() < deadline:
            time.sleep(0.1)
        [call] = self.calls()
        began = time.monotonic()
        stopped = pi_session.stop(self.root, "t1")
        self.assertEqual("stopped", stopped["rounds"][0]["status"])
        self.assertGreaterEqual(time.monotonic() - began, pi_session.STOP_GRACE - 0.5)
        self.assertIn({"signal": "SIGTERM"}, self.calls())
        self.assertFalse(pi_session._alive(call["pid"]))

    @verifies("scenario.task-session.pi-report-verified")
    def test_a_report_the_record_contradicts_fails_the_round(self):
        self.open(
            "t1",
            {
                "report": {
                    "status": "delivered",
                    "summary": "Delivered.",
                    "commit": COMMIT,
                    "escalations": [],
                    "decisions": [],
                    "open": [],
                }
            },
        )
        self.start("t1")
        ended = self.wait("t1", 1)
        self.assertEqual("failed", ended["status"])
        self.assertEqual("session_report_unverified", ended["error"]["code"])
        self.assertIn(COMMIT, ended["error"]["detail"])
        self.assertIn("deliveries are none", ended["error"]["detail"])
        self.assertEqual(COMMIT, ended["report"]["commit"])
        self.escalate("t1", level="main-agent")
        record = store.load_task(self.root, "t1")
        mismatches = pi_session.verify(
            {"status": "escalated", "escalations": [1, 3]}, record
        )
        self.assertEqual(2, len(mismatches))
        self.assertIn("level main-agent", mismatches[0])
        self.assertIn("escalation 3 does not exist", mismatches[1])

    @verifies("scenario.task-session.pi-failed")
    def test_a_round_without_a_report_fails_with_its_evidence(self):
        self.open("t1", {"error": "model overloaded", "stderr": "boom", "exit": 1})
        self.start("t1")
        ended = self.wait("t1", 1)
        self.assertEqual("failed", ended["status"])
        error = ended["error"]
        self.assertEqual("session_no_report", error["code"])
        for part in (
            "exit code 1",
            "last stop reason error",
            "model overloaded",
            "boom",
            ended["events"],
        ):
            self.assertIn(part, error["detail"])
        self.assertEqual(
            {ended["events"], ended["stderr"]},
            {item["ref"] for item in error["evidence"]},
        )
        progress = json.loads(
            (self.root / ".concorde/tasks/t1.session/status.json").read_text()
        )
        self.assertEqual(
            ("finished", "failed"), (progress["phase"], progress["status"])
        )

    @verifies("scenario.task-session.pi-failed")
    def test_a_round_whose_supervisor_vanished_is_settled_as_failed(self):
        self.open("t1", {})
        gone = subprocess.Popen([sys.executable, "-c", "pass"])
        gone.wait()
        directory = self.root / ".concorde/tasks/t1.session"
        store.record_session(
            self.root,
            "t1",
            {
                "program": "pi",
                "id": "task-t1-x",
                "name": "task-t1",
                "main": None,
                "directory": str(directory),
                "model": None,
                "started_at": store.now(),
                "rounds": [pi_session._round(1, directory, gone.pid, None)],
            },
        )
        record = pi_session.settle(self.root, store.load_task(self.root, "t1"))
        [ended] = pi_session.latest(record)["rounds"]
        self.assertEqual(
            ("failed", "session_supervisor_lost"),
            (ended["status"], ended["error"]["code"]),
        )
        self.assertIn(str(gone.pid), ended["error"]["detail"])

    def command(self, *argv: str, client: str | None) -> tuple[int, dict]:
        values = {"CONCORDE_CLIENT": client} if client else {}
        output = io.StringIO()
        with patch.dict(os.environ, values), contextlib.redirect_stdout(output):
            if not client:
                for name in SESSION_VARIABLES:
                    os.environ.pop(name, None)
            status = cli.main(list(argv), cwd=self.root)
        return status, json.loads(output.getvalue())

    @verifies("scenario.task-session.program")
    def test_a_task_session_runs_on_the_main_sessions_program(self):
        self.open("t1", {})
        status, value = self.command(
            "session", "t1", "--main", "m", "--dry-run", client="claude"
        )
        self.assertEqual(0, status, value)
        self.assertIn("settings", value)
        status, value = self.command("session", "t1", "--dry-run", client="pi")
        self.assertEqual(0, status, value)
        self.assertIn("boundary", value)
        self.assertIn("--approve", value["command"])
        status, value = self.command("session", "t1", "--dry-run", client=None)
        self.assertEqual(1, status)
        self.assertEqual("client_unknown", value["error"]["code"])
        for name in SESSION_VARIABLES:
            self.assertIn(name, value["error"]["detail"])
        self.assertEqual([], store.load_task(self.root, "t1")["sessions"])

    @verifies("scenario.task-session.start")
    def test_a_claude_code_session_takes_no_answer_or_stop(self):
        self.open("t1", {})
        for extra in (("--answer", "yes"), ("--stop",)):
            status, value = self.command("session", "t1", *extra, client="claude")
            self.assertEqual(1, status)
            self.assertEqual("invalid_input", value["error"]["code"])
            self.assertIn("SendMessage", value["error"]["detail"])
        status, value = self.command("session", "t1", "--dry-run", client="claude")
        self.assertEqual(("invalid_input", 1), (value["error"]["code"], status))

    @verifies("scenario.task-session.pi-boundary")
    def test_the_boundary_policy_confines_writes_to_the_task(self):
        worktree = self.open("t1", {})
        shown = self.start("t1", dry_run=True)
        self.assertEqual(str(worktree), shown["cwd"])
        directory = self.root / ".concorde/tasks/t1.session"
        boundary = Path(shown["boundary"]).read_text()
        value = json.loads(
            boundary.split("const POLICY: SessionPolicy = ", 1)[1].split(";\n", 1)[0]
        )
        home = Path(os.path.realpath(self.project.home))
        self.assertEqual(
            sorted(
                str(Path(os.path.realpath(path)))
                for path in (
                    worktree,
                    self.root / ".git",
                    self.root / ".concorde/runs",
                    self.root / ".concorde/tasks",
                    pi_session.short_tmp(directory),
                    home / ".cache",
                    home / ".npm",
                )
            ),
            value["sandbox"]["allowWrite"],
        )
        self.assertEqual(pi_session.TOOL_SCHEMA, value["reportSchema"])
        self.assertEqual([], store.load_task(self.root, "t1")["sessions"])

    @verifies("scenario.task-session.pi-report-verified")
    def test_fabricated_escalation_fails_the_supervised_round(self):
        self.open(
            "t1",
            {
                "report": {
                    "status": "escalated",
                    "summary": "Need a decision.",
                    "commit": None,
                    "escalations": [1],
                    "decisions": [],
                    "open": [],
                }
            },
        )
        self.start("t1")
        ended = self.wait("t1", 1)
        self.assertEqual("failed", ended["status"])
        self.assertEqual("session_report_unverified", ended["error"]["code"])
        self.assertIn("escalation 1 does not exist", ended["error"]["detail"])

    @verifies("scenario.task-session.pi-report-shape")
    def test_report_validators_agree_and_supervisor_rejects_invalid_shapes(self):
        fields = {"status", "summary", "commit", "escalations", "decisions", "open"}
        self.assertEqual("object", pi_session.TOOL_SCHEMA["type"])
        self.assertEqual(fields, set(pi_session.TOOL_SCHEMA["required"]))
        self.assertEqual(fields, set(pi_session.TOOL_SCHEMA["properties"]))
        self.assertNotIn("oneOf", pi_session.TOOL_SCHEMA)
        record = {
            "deliveries": [{"commit": COMMIT}, {"commit": "b" * 64}],
            "escalations": [{"error": {"level": "task-session"}}],
        }
        for name, report, accepted in report_cases():
            with self.subTest(name=name):
                if accepted:
                    validate(report, pi_session.REPORT_SCHEMA)
                    validate(report, pi_session.TOOL_SCHEMA)
                else:
                    with self.assertRaises(ContractError):
                        validate(report, pi_session.REPORT_SCHEMA)
                stream = pi_backend.PiStream(result_tool="concorde_report")
                stream.result = report
                result = pi_session.outcome(
                    "t1",
                    "session",
                    {"round": 1, "events": "events.jsonl", "stderr": "stderr.log"},
                    stream,
                    0,
                    False,
                    record,
                )
                self.assertEqual(
                    report["status"] if accepted else "failed", result["status"]
                )
                self.assertEqual(report, result["report"])
                if not accepted:
                    self.assertEqual(
                        "session_report_unverified", result["error"]["code"]
                    )

    @verifies("scenario.task-session.pi-report-shape")
    def test_persisted_v1_reports_are_not_revalidated_or_rewritten(self):
        self.open("t1", {})
        old_report = {
            "status": "delivered",
            "summary": "Historical delivery.",
            "commit": COMMIT,
            "decisions": [],
            "open": [],
        }
        directory = self.root / ".concorde/tasks/t1.session"
        ended = {
            **pi_session._round(1, directory, os.getpid(), None),
            "status": "delivered",
            "ended_at": store.now(),
            "report": old_report,
            "error": None,
        }
        store.record_session(
            self.root,
            "t1",
            {
                "program": "pi",
                "id": "historical",
                "name": "task-t1",
                "main": None,
                "directory": str(directory),
                "model": None,
                "started_at": store.now(),
                "rounds": [ended],
            },
        )
        before = store.load_task(self.root, "t1")
        self.assertEqual(before, pi_session.settle(self.root, before))
        self.assertEqual(before, store.load_task(self.root, "t1"))
        validate(before, contract("")["schema"])

    def test_the_report_schema_is_the_contract(self):
        found = contract("## Session report", SESSION_CONTRACTS)
        self.assertEqual("contract.task-session.report", found["id"])
        self.assertEqual(2, found["version"])
        self.assertEqual(pi_session.REPORT_SCHEMA, found["schema"])
        validate(found["example"], pi_session.REPORT_SCHEMA)


DECISIONS = """
import {{ reportProblem, sessionWriteDecision }} from {decisions};
const policy = {policy};
console.log(JSON.stringify({{
  inside: sessionWriteDecision(policy, {inside}),
  log: sessionWriteDecision(policy, {log}),
  outside: sessionWriteDecision(policy, {outside}),
  delivered: reportProblem({{ status: "delivered", summary: "s", commit: "{commit}", escalations: [], decisions: [], open: [] }}),
  deliveredWithoutCommit: reportProblem({{ status: "delivered", summary: "s", escalations: [], decisions: [], open: [] }}),
  escalated: reportProblem({{ status: "escalated", summary: "s", commit: null, escalations: [1], decisions: [], open: [] }}),
  escalatedEmpty: reportProblem({{ status: "escalated", summary: "s", commit: null, escalations: [], decisions: [], open: [] }}),
  unknown: reportProblem({{ status: "done", summary: "s", commit: null, escalations: [], decisions: [], open: [] }}),
}}));
"""


@unittest.skipUnless(
    shutil.which("node"), "Node is needed to run the boundary's decisions"
)
class BoundaryDecisionTests(unittest.TestCase):
    @verifies("scenario.task-session.pi-report-shape")
    def test_report_policy_agrees_with_contract_for_every_case(self):
        cases = report_cases()
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            for source in (pi_session.DECISIONS_SOURCE, pi_session.PATHS_SOURCE):
                shutil.copy2(source, base / source.name)
            probe = base / "probe.mts"
            probe.write_text(
                'import { reportProblem } from "./pi_session_policy.ts";\n'
                + "const cases = "
                + json.dumps([report for _, report, _ in cases])
                + ";\n"
                + "console.log(JSON.stringify(cases.map(reportProblem)));\n"
            )
            done = subprocess.run(
                ["node", "--experimental-strip-types", "--no-warnings", str(probe)],
                capture_output=True,
                text=True,
                check=True,
            )
        for (name, _report, accepted), problem in zip(
            cases, json.loads(done.stdout), strict=True
        ):
            with self.subTest(name=name):
                self.assertEqual(accepted, problem is None, problem)

    @verifies("scenario.task-session.pi-boundary")
    def test_writes_outside_the_task_are_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            worktree = base / "project/.claude/worktrees/t1"
            (worktree / "src").mkdir(parents=True)
            log = base / "project/.concorde/tasks/t1.decisions.md"
            log.parent.mkdir(parents=True)
            log.write_text("# Decision log\n")
            code = base / "code"
            code.mkdir()
            for source in (pi_session.DECISIONS_SOURCE, pi_session.PATHS_SOURCE):
                shutil.copy2(source, code / source.name)
            probe = code / "probe.mts"
            probe.write_text(
                DECISIONS.format(
                    decisions=json.dumps((code / "pi_session_policy.ts").as_uri()),
                    policy=json.dumps(
                        {
                            "task": "t1",
                            "worktree": str(worktree),
                            "files": [str(log)],
                            "sandbox": {"allowWrite": []},
                            "reportSchema": {},
                        }
                    ),
                    inside=json.dumps(str(worktree / "src/new.py")),
                    log=json.dumps(str(log)),
                    outside=json.dumps(str(base / "project/src/calc.py")),
                    commit=COMMIT,
                )
            )
            done = subprocess.run(
                ["node", "--experimental-strip-types", "--no-warnings", str(probe)],
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(0, done.returncode, done.stderr)
        out = json.loads(done.stdout)
        self.assertIsNone(out["inside"])
        self.assertIsNone(out["log"])
        self.assertIn(str(worktree), out["outside"])
        self.assertIn("outside task t1", out["outside"])
        self.assertIsNone(out["delivered"])
        self.assertIn("commit", out["deliveredWithoutCommit"])
        self.assertIsNone(out["escalated"])
        self.assertIn("escalations", out["escalatedEmpty"])
        self.assertIn("status", out["unknown"])


if __name__ == "__main__":
    unittest.main()
