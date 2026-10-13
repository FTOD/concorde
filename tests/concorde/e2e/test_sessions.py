"""Headless sessions: the command, the logs, the unsettled runs and the wake-up resume."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from concorde.execution.runs import Store, run_lock
from concorde.spec.verification import verifies
from tests.concorde.support.paths import REPOSITORY_ROOT

SPEC = importlib.util.spec_from_file_location(
    "e2e", REPOSITORY_ROOT / "scripts/e2e/e2e.py"
)
e2e = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(e2e)
sessions = e2e.sessions

# A stand-in for `claude -p`: the first round starts a detached "Operation host" that lives for
# a second and leaves its run running; a resumed round records the message it was woken with.
# With EVERY_ROUND, each round, resumed or not, leaves a run of its own running; with FAILS, a
# resumed round prints its output and an error and exits 3.
FAKE = """#!/usr/bin/env python3
import fcntl, json, os, subprocess, sys, time
from datetime import UTC, datetime
from pathlib import Path
EVERY_ROUND = False
FAILS = False
argv = sys.argv[1:]
prompt = argv[argv.index("-p") + 1]
Path("fake-argv.jsonl").open("a").write(json.dumps(argv) + "\\n")
calls = len(Path("fake-argv.jsonl").read_text().splitlines())
def say(event):
    print(json.dumps({**event, "session_id": "s-1"}), flush=True)
say({"type": "system", "subtype": "init"})
if "--resume" in argv and FAILS:
    say({"type": "assistant", "message": {"content": [{"type": "text", "text": "failing"}]}})
    print("the round broke", file=sys.stderr)
    sys.exit(3)
if "--resume" in argv and not EVERY_ROUND:
    # A resume first replays the stopped background command as a turn without a model turn.
    say({"type": "result", "subtype": "success", "num_turns": 0, "result": ""})
    say({"type": "assistant", "message": {"content": [{"type": "text", "text": "woken"}]}})
    say({"type": "result", "subtype": "success", "num_turns": 3, "total_cost_usd": 0.2,
         "result": "done after: " + prompt})
    sys.exit(0)
name = "r-%d" % calls
run = Path(".concorde/tasks/t1/workspace/runs") / name
run.mkdir(parents=True)
lock = Path(".concorde/locks/runs") / (name + ".lock")
lock.parent.mkdir(parents=True, exist_ok=True)
HOLD = "import fcntl, os, sys, time; d = os.open(sys.argv[1], os.O_RDWR | os.O_CREAT); " \\
    "fcntl.flock(d, fcntl.LOCK_EX); time.sleep(float(sys.argv[2])); os.unlink(sys.argv[1])"
host = subprocess.Popen([sys.executable, "-c", HOLD, str(lock), "1"], start_new_session=True)
while True:
    try:
        probe = os.open(lock, os.O_RDONLY)
    except FileNotFoundError:
        time.sleep(0.01)
        continue
    try:
        fcntl.flock(probe, fcntl.LOCK_SH | fcntl.LOCK_NB)
    except BlockingIOError:
        break
    finally:
        os.close(probe)
    time.sleep(0.01)
# Execution's progress files name their times to the microsecond.
stamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
(run / "status.json").write_text(json.dumps({
    "kind": "operation", "run_id": name, "name": "implement", "workspace": "t1",
    "phase": "running", "host_pid": host.pid, "started_at": stamp}))
say({"type": "assistant", "message": {"content": [
    {"type": "tool_use", "name": "Bash", "input": {"command": "concorde run implement"}}]}})
say({"type": "result", "subtype": "success", "num_turns": 2, "total_cost_usd": 0.1,
     "result": "waiting for the run"})
"""


def event(**value) -> str:
    return json.dumps(value, ensure_ascii=False)


# A command longer than any display would show, whose end only a whole target keeps.
LONG = "concorde run general " + "x" * 600 + " --end"


class HeadlessSessionTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.base = Path(directory.name)
        self.project = self.base / "project"
        self.project.mkdir()

    @verifies("scenario.headless-sessions.command")
    def test_the_command_tells_the_session_its_conditions_and_grants_its_tools(self):
        first = sessions.command("do it")
        self.assertEqual(["claude", "-p", "do it"], first[:3])
        self.assertEqual(
            f"{sessions.NOTE}\n\n{sessions.MAIN_PROCEDURE}",
            first[first.index("--append-system-prompt") + 1],
        )
        self.assertIn("run Concorde commands in the foreground", sessions.NOTE)
        granted = first[first.index("--allowedTools") + 1 :]
        self.assertEqual(list(sessions.MAIN_AGENT_TOOLS), granted)
        # The test-only exception: a headless Claude Code main session works its tasks itself
        # inside their task worktrees instead of starting task sessions.
        self.assertIn("EnterWorktree", granted)
        self.assertIn("ExitWorktree", granted)
        self.assertNotIn("SendMessage", granted)
        self.assertIn("SendMessage report would find no receiver", sessions.NOTE)
        # The test procedure overrides the skill's delegation rule for this session only and
        # states every step in order.
        procedure = sessions.MAIN_PROCEDURE
        self.assertIn("For this test session only", procedure)
        self.assertIn(
            "overrides the concorde skill's rule to hand every task to a", procedure
        )
        steps = [
            "`concorde task open`",
            "EnterWorktree",
            "running every Concorde command in the foreground",
            "`concorde task-validation` and `concorde delivery`",
            'ExitWorktree with action "keep"',
            "`concorde task merge <task>`",
            "record it in the task's decision log",
        ]
        places = [procedure.find(step) for step in steps]
        self.assertNotIn(-1, places, steps)
        self.assertEqual(sorted(places), places)
        # A headless workflow run works as a task session and carries the note alone.
        workflow = sessions.command("run it", procedure=None)
        self.assertEqual(
            sessions.NOTE, workflow[workflow.index("--append-system-prompt") + 1]
        )
        # Every round runs with the Bash sandbox off, on its own command line, so that a detached
        # runner outlives the call that started it.
        for argv in (first, workflow):
            self.assertEqual(
                {"sandbox": {"enabled": False}},
                json.loads(argv[argv.index("--settings") + 1]),
            )
        self.assertNotIn("--resume", first)
        again = sessions.command("woken", resume="s-1")
        self.assertEqual("s-1", again[again.index("--resume") + 1])
        self.assertEqual("0", sessions.environment()[sessions.WAIT_VARIABLE])

    @verifies("scenario.headless-sessions.logs")
    def test_a_replayed_empty_turn_is_not_the_rounds_answer(self):
        log = self.base / "round.jsonl"
        log.write_text(
            "\n".join(
                [
                    event(type="system", subtype="init", session_id="s-9"),
                    event(type="result", num_turns=0, result=""),
                    event(
                        type="assistant",
                        message={
                            "content": [
                                {
                                    "type": "tool_use",
                                    "name": "Write",
                                    "input": {"file_path": "/x/report.json"},
                                },
                                {
                                    "type": "tool_use",
                                    "name": "Bash",
                                    "input": {"command": LONG},
                                },
                                {"type": "text", "text": "reported\u2028line\u0085end"},
                            ]
                        },
                    ),
                    "not json",
                    event(
                        type="result",
                        subtype="success",
                        num_turns=5,
                        total_cost_usd=1.5,
                        result="the answer\u2029after",
                    ),
                ]
            ),
            # stream-json writes these separators unescaped inside its strings.
            encoding="utf-8",
        )
        self.assertIn("\u2028", log.read_text(encoding="utf-8"))
        summary = sessions.read_log(log)
        self.assertEqual("s-9", summary["session_id"])
        # Every target is read whole.
        self.assertEqual(
            [
                {"tool": "Write", "target": "/x/report.json"},
                {"tool": "Bash", "target": LONG},
            ],
            summary["actions"],
        )
        self.assertEqual(["reported\u2028line\u0085end"], summary["texts"])
        self.assertEqual(
            {
                "subtype": "success",
                "turns": 5,
                "cost_usd": 1.5,
                "text": "the answer\u2029after",
            },
            summary["result"],
        )

    @verifies("scenario.headless-sessions.logs")
    def test_a_round_of_replays_alone_has_no_answer(self):
        log = self.base / "round.jsonl"
        log.write_text(
            "\n".join(
                [
                    event(type="system", subtype="init", session_id="s-9"),
                    event(type="result", num_turns=0, result="", total_cost_usd=0.0),
                ]
            )
        )
        self.assertIsNone(sessions.read_log(log)["result"])

    @verifies("scenario.headless-sessions.unsettled")
    def test_running_runs_and_runs_stopped_with_the_turn_are_unsettled(self):
        live = subprocess.Popen(["sleep", "30"])
        self.addCleanup(live.wait)
        self.addCleanup(live.kill)
        since = "2026-09-27T10:00:00Z"
        concorde = self.project / ".concorde"
        runs = concorde / "tasks/t1/workspace/runs"

        def make(name, started, phase, pid, code=None, folder=None):
            folder = folder or runs / name
            folder.mkdir(parents=True)
            (folder / "status.json").write_text(
                json.dumps(
                    {
                        "kind": "operation",
                        "run_id": name,
                        "phase": phase,
                        "host_pid": pid,
                        "started_at": started,
                    }
                )
            )
            if phase == "finished":
                (folder / "result.json").write_text(
                    json.dumps({"status": "failed", "error": {"code": code}})
                )

        make("r-running", "2026-09-27T10:05:00Z", "running", live.pid)
        make("r-stopped", "2026-09-27T10:05:00Z", "finished", 0, "cancelled")
        make("r-failed", "2026-09-27T10:05:00Z", "finished", 0, "not_deliverable")
        make("r-earlier", "2026-09-27T09:00:00Z", "running", live.pid)
        # Its runner ran in a sandbox's PID namespace as process 1, a live process here; it no
        # longer holds its run lock, whose file it left behind, and never finished the run.
        make("r-gone", "2026-09-27T10:05:00Z", "running", 1)
        # A workflow step's run, and an unbound run started in the project itself.
        make(
            "r-step",
            "2026-09-27T10:06:00Z",
            "running",
            live.pid,
            folder=concorde / "tasks/t1/workspace/workflow/steps/1-specify/run",
        )
        make(
            "r-unbound",
            "2026-09-27T10:07:00Z",
            "running",
            live.pid,
            folder=concorde / "unbound/r-unbound",
        )
        # A bound run queued behind its busy workspace, still in the lobby.
        make(
            "r-queued",
            "2026-09-27T10:08:00Z",
            "running",
            live.pid,
            folder=concorde / "lobby/r-queued",
        )
        store = Store(concorde)
        for name in ("r-running", "r-earlier", "r-step", "r-unbound", "r-queued"):
            self.enterContext(run_lock(store, name, "test runner"))
        (concorde / "locks/runs/r-gone.lock").write_text("")
        # The progress file of the running Operation's worker is no run of its own.
        (runs / "r-running/workers/w-1").mkdir(parents=True)
        (runs / "r-running/workers/w-1/status.json").write_text(
            json.dumps({"phase": "worker", "host_pid": live.pid})
        )
        found = sessions.unsettled_runs(self.project, since, time.time())
        self.assertEqual(
            [
                {"run": "r-queued", "why": "running"},
                {"run": "r-gone", "why": "runner_gone"},
                {"run": "r-running", "why": "running"},
                {"run": "r-stopped", "why": "stopped_with_turn"},
                {"run": "r-step", "why": "running"},
                {"run": "r-unbound", "why": "running"},
            ],
            found,
        )
        # The wake names a run whose runner is gone as one that ended without a result.
        self.assertIn(
            "r-gone (None, workspace none) ended without writing a result",
            sessions.wake_message(
                self.project, [{"run": "r-gone", "why": "runner_gone"}]
            ),
        )
        # A cancellation long before the round ended was the session's own doing.
        self.assertEqual(
            ["r-queued", "r-gone", "r-running", "r-step", "r-unbound"],
            [
                item["run"]
                for item in sessions.unsettled_runs(
                    self.project, since, time.time() + 3600
                )
            ],
        )
        self.assertEqual(
            [],
            sessions.unsettled_runs(
                self.project,
                since,
                time.time(),
                {"r-gone", "r-running", "r-stopped", "r-step", "r-unbound", "r-queued"},
            ),
        )

    @verifies("scenario.headless-sessions.wake")
    def test_a_round_that_leaves_a_run_running_is_resumed_when_it_ends(self):
        fake = self.base / "claude"
        fake.write_text(FAKE)
        fake.chmod(0o755)
        record = sessions.start(
            self.project,
            "add a property",
            self.base / "session",
            claude=str(fake),
            poll=0.1,
        )
        self.assertEqual("idle", record["end"])
        self.assertEqual("s-1", record["session_id"])
        self.assertEqual(["r-1"], record["rounds"][0]["woke_for"])
        self.assertEqual(2, len(record["rounds"]))
        calls = [
            json.loads(line)
            for line in (self.project / "fake-argv.jsonl").read_text().splitlines()
        ]
        self.assertNotIn("--resume", calls[0])
        self.assertEqual("s-1", calls[1][calls[1].index("--resume") + 1])
        woken = calls[1][calls[1].index("-p") + 1]
        self.assertIn("operation run r-1 (implement, workspace t1)", woken)
        self.assertIn("result.json", woken)
        self.assertTrue(record["final"].startswith("done after: Notification"))
        self.assertEqual(0.2, record["cost_usd"])
        saved = json.loads((self.base / "session/session.json").read_text())
        self.assertEqual(record, saved)
        shown = sessions.show(self.base / "session")
        self.assertEqual(
            "concorde run implement",
            shown["rounds"][0]["actions"][0]["target"],
        )

    @verifies("scenario.headless-sessions.wait-exceeded")
    def test_a_run_that_outlives_the_wait_fails_a_kept_session(self):
        fake = self.base / "claude"
        # The run's host outlives the wait, so the session fails after its first round.
        fake.write_text(FAKE.replace('str(lock), "1"]', 'str(lock), "5"]'))
        fake.chmod(0o755)
        directory = self.base / "session"
        with self.assertRaises(e2e.E2EError) as raised:
            sessions.start(
                self.project,
                "add a property",
                directory,
                claude=str(fake),
                wait_limit=0.3,
                poll=0.1,
            )
        progress = str(
            self.project / ".concorde/tasks/t1/workspace/runs/r-1/status.json"
        )
        error = raised.exception
        self.assertEqual("wait_exceeded", error.code)
        self.assertEqual(progress, error.evidence["progress"])
        self.assertEqual(str(directory / "session.json"), error.evidence["session"])
        saved = json.loads((directory / "session.json").read_text())
        self.assertEqual(("wait_exceeded", progress), (saved["end"], saved["progress"]))
        self.assertEqual("s-1", saved["session_id"])
        [round_] = saved["rounds"]
        self.assertEqual([], round_["woke_for"])
        self.assertTrue(Path(round_["log"]).is_file())

    def fake(self, **flags) -> Path:
        """The stand-in for `claude -p`, with the given flags of FAKE set."""
        text = FAKE
        for name, value in flags.items():
            text = text.replace(f"{name} = False", f"{name} = {value!r}")
        path = self.base / "claude"
        path.write_text(text)
        path.chmod(0o755)
        return path

    def calls(self) -> list[list[str]]:
        argv = self.project / "fake-argv.jsonl"
        if not argv.exists():
            return []
        return [json.loads(line) for line in argv.read_text().splitlines()]

    def held_run(self, folder: Path, started: str, **fields) -> None:
        """A run whose runner holds its run lock, started at ``started``."""
        folder.mkdir(parents=True)
        (folder / "status.json").write_text(
            json.dumps(
                {
                    "kind": "command",
                    "run_id": folder.name,
                    "phase": "running",
                    "started_at": started,
                    **fields,
                }
            )
        )
        self.enterContext(
            run_lock(Store(self.project / ".concorde"), folder.name, "test runner")
        )

    @verifies("scenario.headless-sessions.unsettled")
    def test_runs_of_the_sessions_first_second_are_told_by_their_instant(self):
        # Execution names a run's start to the microsecond; the session began within the same
        # second, and times of different precision never compare as text.
        runs = self.project / ".concorde/tasks/t1/workspace/runs"
        self.held_run(runs / "r-before", "2026-10-08T10:00:00.100000Z")
        self.held_run(runs / "r-after", "2026-10-08T10:00:00.900000Z")
        self.held_run(runs / "r-next", "2026-10-08T10:00:01Z")
        found = sessions.unsettled_runs(
            self.project, "2026-10-08T10:00:00.500000Z", time.time()
        )
        self.assertEqual(["r-after", "r-next"], [item["run"] for item in found])
        self.assertEqual(
            ["r-after", "r-before", "r-next"],
            [
                item["run"]
                for item in sessions.unsettled_runs(
                    self.project, "2026-10-08T10:00:00Z", time.time()
                )
            ],
        )

    @verifies("scenario.headless-sessions.moved-run")
    def test_a_run_that_enters_its_workspace_while_listed_is_still_found(self):
        concorde = self.project / ".concorde"
        self.held_run(concorde / "lobby/r-queued", "2026-10-08T10:05:00.000000Z")
        destination = concorde / "tasks/t1/workspace/runs/r-queued"
        listed = sessions.run_folders
        moves = []

        def listing(project):
            # The run moves from the lobby into its workspace folder right after the first
            # listing found it in the lobby, as Execution's runner renames it once it holds
            # the workspace lock.
            found = listed(project)
            if not moves:
                destination.parent.mkdir(parents=True)
                (concorde / "lobby/r-queued").rename(destination)
                moves.append(destination)
            return found

        with patch.object(sessions, "run_folders", listing):
            found = sessions.unsettled_runs(
                self.project, "2026-10-08T10:00:00Z", time.time()
            )
        self.assertEqual([destination], moves)
        self.assertEqual([{"run": "r-queued", "why": "running"}], found)
        # Listed once more, it is found in its workspace folder alone.
        self.assertEqual([destination], sessions.run_folders(self.project))

    @verifies("scenario.headless-sessions.observation-failed")
    def test_an_unreadable_progress_file_or_result_is_an_observation_failure(self):
        runs = self.project / ".concorde/tasks/t1/workspace/runs"
        broken = runs / "r-broken"
        broken.mkdir(parents=True)
        (broken / "status.json").write_text("{not json")
        with self.assertRaises(e2e.E2EError) as raised:
            sessions.unsettled_runs(
                self.project, "2026-10-08T10:00:00Z", time.time(), reread=0.0
            )
        self.assertEqual("observation_failed", raised.exception.code)
        self.assertEqual(str(broken / "status.json"), raised.exception.evidence["file"])
        # A finished run whose result cannot be read.
        (broken / "status.json").write_text(
            json.dumps(
                {
                    "kind": "operation",
                    "run_id": "r-broken",
                    "phase": "finished",
                    "started_at": "2026-10-08T10:05:00.000000Z",
                }
            )
        )
        (broken / "result.json").write_text("[]")
        with self.assertRaises(e2e.E2EError) as raised:
            sessions.unsettled_runs(
                self.project, "2026-10-08T10:00:00Z", time.time(), reread=0.0
            )
        self.assertEqual("observation_failed", raised.exception.code)
        self.assertEqual(str(broken / "result.json"), raised.exception.evidence["file"])
        # Once its result can be read, the finished run is judged as any other.
        (broken / "result.json").write_text(json.dumps({"status": "ok"}))
        self.assertEqual(
            [],
            sessions.unsettled_runs(
                self.project, "2026-10-08T10:00:00Z", time.time(), reread=0.0
            ),
        )

    @verifies("scenario.headless-sessions.observation-failed")
    def test_a_session_that_cannot_observe_a_run_fails_kept(self):
        broken = self.project / ".concorde/unbound/r-broken"
        broken.mkdir(parents=True)
        (broken / "status.json").write_text("")
        directory = self.base / "session"
        with self.assertRaises(e2e.E2EError) as raised:
            sessions.start(
                self.project,
                "add a property",
                directory,
                claude=str(self.fake()),
                poll=0.1,
                reread=0.0,
            )
        error = raised.exception
        self.assertEqual("observation_failed", error.code)
        self.assertEqual(str(broken / "status.json"), error.evidence["file"])
        self.assertEqual(str(directory / "session.json"), error.evidence["session"])
        saved = json.loads((directory / "session.json").read_text())
        self.assertEqual(
            ("observation_failed", str(broken / "status.json")),
            (saved["end"], saved["file"]),
        )
        [round_] = saved["rounds"]
        self.assertEqual([], round_["woke_for"])
        self.assertTrue(Path(round_["log"]).is_file())

    @verifies("scenario.headless-sessions.binding-invalid")
    def test_an_invalid_workspace_binding_refuses_the_session_before_its_first_round(
        self,
    ):
        binding = self.project / ".concorde/workspace.json"
        directory = self.base / "session"
        for text in (
            "{not json",
            json.dumps({"task": "t1"}),
            json.dumps({"concorde": 3}),
        ):
            binding.parent.mkdir(exist_ok=True)
            binding.write_text(text)
            with self.assertRaises(e2e.E2EError) as raised:
                sessions.start(
                    self.project,
                    "add a property",
                    directory,
                    claude=str(self.fake()),
                )
            self.assertEqual("binding_invalid", raised.exception.code)
            self.assertEqual(str(binding), raised.exception.evidence["file"])
            self.assertEqual([], self.calls())
            self.assertFalse((directory / "session.json").exists())

    @verifies("scenario.headless-sessions.rounds-exhausted")
    def test_a_session_that_leaves_runs_behind_every_round_ends_after_its_rounds(self):
        record = sessions.start(
            self.project,
            "add a property",
            self.base / "session",
            claude=str(self.fake(EVERY_ROUND=True)),
            rounds=2,
            poll=0.1,
        )
        calls = self.calls()
        self.assertEqual(2, len(calls))
        self.assertNotIn("--resume", calls[0])
        self.assertEqual("s-1", calls[1][calls[1].index("--resume") + 1])
        self.assertEqual("rounds_exhausted", record["end"])
        first, last = record["rounds"]
        self.assertEqual(["r-1"], first["woke_for"])
        self.assertNotIn("left_behind", first)
        # No round is left to wake for the last round's run: it is left behind, never woken for.
        self.assertEqual([], last["woke_for"])
        self.assertEqual(["r-2"], last["left_behind"])
        self.assertEqual(
            record, json.loads((self.base / "session/session.json").read_text())
        )

    @verifies("scenario.headless-sessions.failed-round")
    def test_a_failed_round_ends_the_session_with_its_evidence_kept(self):
        directory = self.base / "session"
        record = sessions.start(
            self.project,
            "add a property",
            directory,
            claude=str(self.fake(FAILS=True)),
            poll=0.1,
        )
        self.assertEqual("exited", record["end"])
        first, failed = record["rounds"]
        # The earlier round stays as it was, with the run it woke the session for.
        self.assertEqual((0, ["r-1"]), (first["exit"], first["woke_for"]))
        self.assertEqual("waiting for the run", first["result"]["text"])
        self.assertEqual(3, failed["exit"])
        self.assertIn("the round broke", failed["stderr"])
        self.assertIn(
            "failing", (directory / "round-2.jsonl").read_text(encoding="utf-8")
        )
        self.assertIn(
            "the round broke", (directory / "round-2.err").read_text(encoding="utf-8")
        )
        self.assertEqual(record, json.loads((directory / "session.json").read_text()))
        self.assertEqual("waiting for the run", record["final"])


if __name__ == "__main__":
    unittest.main()
