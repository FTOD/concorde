"""Headless sessions: the command, the logs, the unsettled runs and the wake-up resume."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

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
import json, os, subprocess, sys, time
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
host = subprocess.Popen(["sleep", "1"], start_new_session=True)
run = Path(".concorde/runs/r-1")
run.mkdir(parents=True)
stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
(run / "status.json").write_text(json.dumps({
    "kind": "operation", "run_id": "r-1", "operation": "implement", "task": "t1",
    "phase": "running", "host_pid": host.pid, "started_at": stamp}))
say({"type": "assistant", "message": {"content": [
    {"type": "tool_use", "name": "Bash", "input": {"command": "concorde run implement --task t1"}}]}})
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
            sessions.NOTE, first[first.index("--append-system-prompt") + 1]
        )
        self.assertIn("run Concorde commands in the foreground", sessions.NOTE)
        self.assertEqual(
            list(sessions.MAIN_AGENT_TOOLS), first[first.index("--allowedTools") + 1 :]
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
        runs = self.project / ".concorde/runs"

        def make(name, started, phase, pid, code=None):
            (runs / name).mkdir(parents=True)
            (runs / name / "status.json").write_text(
                json.dumps(
                    {
                        "kind": "operation",
                        "phase": phase,
                        "host_pid": pid,
                        "started_at": started,
                    }
                )
            )
            if phase == "finished":
                (runs / name / "result.json").write_text(
                    json.dumps({"status": "failed", "error": {"code": code}})
                )

        make("r-running", "2026-09-27T10:05:00Z", "running", live.pid)
        make("r-stopped", "2026-09-27T10:05:00Z", "finished", 0, "cancelled")
        make("r-failed", "2026-09-27T10:05:00Z", "finished", 0, "not_deliverable")
        make("r-earlier", "2026-09-27T09:00:00Z", "running", live.pid)
        make("r-gone", "2026-09-27T10:05:00Z", "running", 999999999)
        (runs / "w-1").mkdir()
        (runs / "w-1/status.json").write_text(
            json.dumps({"phase": "worker", "host_pid": live.pid})
        )
        found = sessions.unsettled_runs(self.project, since, time.time())
        self.assertEqual(
            [
                {"run": "r-running", "why": "running"},
                {"run": "r-stopped", "why": "stopped_with_turn"},
            ],
            found,
        )
        # A cancellation long before the round ended was the session's own doing.
        self.assertEqual(
            [{"run": "r-running", "why": "running"}],
            sessions.unsettled_runs(self.project, since, time.time() + 3600),
        )
        self.assertEqual(
            [],
            sessions.unsettled_runs(
                self.project, since, time.time(), {"r-running", "r-stopped"}
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
        self.assertIn("Operation run r-1 (implement, task t1)", woken)
        self.assertIn("result.json", woken)
        self.assertTrue(record["final"].startswith("done after: Notification"))
        self.assertEqual(0.2, record["cost_usd"])
        saved = json.loads((self.base / "session/session.json").read_text())
        self.assertEqual(record, saved)
        shown = sessions.show(self.base / "session")
        self.assertEqual(
            "concorde run implement --task t1",
            shown["rounds"][0]["actions"][0]["target"],
        )


if __name__ == "__main__":
    unittest.main()
