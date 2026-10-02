"""Headless sessions: the command, the logs, the unsettled runs and the wake-up resume."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

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
FAKE = """#!/usr/bin/env python3
import fcntl, json, os, subprocess, sys, time
from pathlib import Path
argv = sys.argv[1:]
prompt = argv[argv.index("-p") + 1]
Path("fake-argv.jsonl").open("a").write(json.dumps(argv) + "\\n")
def say(event):
    print(json.dumps({**event, "session_id": "s-1"}), flush=True)
say({"type": "system", "subtype": "init"})
if "--resume" in argv:
    # A resume first replays the stopped background command as a turn without a model turn.
    say({"type": "result", "subtype": "success", "num_turns": 0, "result": ""})
    say({"type": "assistant", "message": {"content": [{"type": "text", "text": "woken"}]}})
    say({"type": "result", "subtype": "success", "num_turns": 3, "total_cost_usd": 0.2,
         "result": "done after: " + prompt})
    sys.exit(0)
run = Path(".concorde/tasks/t1/workspace/runs/r-1")
run.mkdir(parents=True)
lock = Path(".concorde/locks/runs/r-1.lock")
lock.parent.mkdir(parents=True)
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
stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
(run / "status.json").write_text(json.dumps({
    "kind": "operation", "run_id": "r-1", "name": "implement", "workspace": "t1",
    "phase": "running", "host_pid": host.pid, "started_at": stamp}))
say({"type": "assistant", "message": {"content": [
    {"type": "tool_use", "name": "Bash", "input": {"command": "concorde run implement"}}]}})
say({"type": "result", "subtype": "success", "num_turns": 2, "total_cost_usd": 0.1,
     "result": "waiting for the run"})
"""


def event(**value) -> str:
    return json.dumps(value)


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
                                {"type": "text", "text": "reported"},
                            ]
                        },
                    ),
                    "not json",
                    event(
                        type="result",
                        subtype="success",
                        num_turns=5,
                        total_cost_usd=1.5,
                        result="the answer",
                    ),
                ]
            )
        )
        summary = sessions.read_log(log)
        self.assertEqual("s-9", summary["session_id"])
        self.assertEqual(
            [{"tool": "Write", "target": "/x/report.json"}], summary["actions"]
        )
        self.assertEqual(["reported"], summary["texts"])
        self.assertEqual(
            {"subtype": "success", "turns": 5, "cost_usd": 1.5, "text": "the answer"},
            summary["result"],
        )

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
        # longer holds its run lock, whose file it left behind.
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
                {"run": "r-running", "why": "running"},
                {"run": "r-stopped", "why": "stopped_with_turn"},
                {"run": "r-step", "why": "running"},
                {"run": "r-unbound", "why": "running"},
                {"run": "r-queued", "why": "running"},
            ],
            found,
        )
        # A cancellation long before the round ended was the session's own doing.
        self.assertEqual(
            ["r-running", "r-step", "r-unbound", "r-queued"],
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
                {"r-running", "r-stopped", "r-step", "r-unbound", "r-queued"},
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


if __name__ == "__main__":
    unittest.main()
