"""The owners case and its live sessions, driven by stand-ins for `claude` and `concorde`.

The `claude` stand-in speaks the protocol the live sessions use, Claude Code's stream-json on
standard input and output, and plays what the real program does that the case observes: a session
is notified when its own background command ends. A stand-in that is also woken for the end of
every run it did not start must fail the case.
"""

from __future__ import annotations

import fcntl
import importlib.util
import json
import os
import sys
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
owners = e2e.owners
live = sys.modules["live"]

# `concorde task-validation --wait N` records a run that waits for the workspace lock and then
# ends ok; `concorde task show t1` lists the runs of t1 with their status.
FAKE_CONCORDE = """#!/usr/bin/env python3
import fcntl, json, os, sys, time, uuid
from pathlib import Path
RECORDS = Path(%(records)r)
args = sys.argv[1:]
# Tracing's layout: the task's runs in its workspace folder, every lock under locks/.
runs = RECORDS / "tasks" / "t1" / "workspace" / "runs"
locks = RECORDS / "locks"
if args[0] == "task-validation":
    run_id = "r-" + time.strftime("%%Y%%m%%dT%%H%%M%%S") + "-task_validation-" + uuid.uuid4().hex[:8]
    directory = runs / run_id
    directory.mkdir(parents=True)
    (locks / "runs").mkdir(parents=True, exist_ok=True)
    held = (locks / "runs" / (run_id + ".lock")).open("a+")
    fcntl.flock(held, fcntl.LOCK_EX)
    stamp = time.strftime("%%Y-%%m-%%dT%%H:%%M:%%SZ", time.gmtime())
    state = {"kind": "command", "run_id": run_id, "name": "task-validation", "workspace": "t1",
             "phase": "running", "status": None, "host_pid": os.getpid(), "started_at": stamp,
             "updated_at": stamp}
    (directory / "status.json").write_text(json.dumps(state))
    (locks / "workspaces").mkdir(parents=True, exist_ok=True)
    lock = (locks / "workspaces" / "t1.lock").open("a+")
    fcntl.flock(lock, fcntl.LOCK_EX)
    result = {"run_id": run_id, "status": "ok", "summary": "t1 may be delivered"}
    (directory / "result.json").write_text(json.dumps(result))
    (directory / "status.json").write_text(json.dumps({**state, "phase": "finished",
                                                       "status": "ok"}))
    print(json.dumps(result))
elif args[:2] == ["task", "show"]:
    listed = []
    for directory in sorted(runs.glob("r-*")):
        state = json.loads((directory / "status.json").read_text())
        result = directory / "result.json"
        listed.append({"run_id": directory.name, "kind": "command", "name": state["name"],
                       "status": json.loads(result.read_text())["status"] if result.exists()
                       else "running"})
    print(json.dumps({"record": {"id": "t1"}, "runs": listed}, indent=2))
"""

# A live Claude Code session: a turn per prompt, a background command run detached and
# notified when it ends, and a foreground command's output given as its tool result; with
# WAKES_ALL also woken, with a notification of its own, for the end of every run.
FAKE_CLAUDE = """#!/usr/bin/env python3
import json, re, subprocess, sys, threading, time
from pathlib import Path
WAKES_ALL = %(wakes_all)r
RECORDS = Path(%(records)r)
lock = threading.Lock()
def say(event):
    with lock:
        print(json.dumps(event), flush=True)
def turn(text, tool_output=None):
    say({"type": "system", "subtype": "init", "session_id": "c-1"})
    if tool_output is not None:
        say({"type": "user", "message": {"role": "user", "content": [
            {"type": "tool_result", "content": tool_output}]}})
    say({"type": "assistant", "message": {"content": [{"type": "text", "text": text}]}})
    say({"type": "result", "subtype": "success", "num_turns": 1, "session_id": "c-1"})
def notify(process):
    process.wait()
    say({"type": "system", "subtype": "task_notification", "status": "completed"})
    turn("DONE ok")
def wake_for_every_run():
    woken = set()
    while True:
        for result in sorted(RECORDS.glob("tasks/*/workspace/runs/r-*/result.json")):
            if result.parent.name not in woken:
                woken.add(result.parent.name)
                say({"type": "system", "subtype": "task_notification", "status": "completed"})
                turn("DONE ok")
        time.sleep(0.1)
if WAKES_ALL:
    threading.Thread(target=wake_for_every_run, daemon=True).start()
for line in sys.stdin:
    text = json.loads(line)["message"]["content"]
    if "run_in_background" in text:
        command = text.split("STARTED:\\n", 1)[1].split("\\n", 1)[0]
        process = subprocess.Popen(["bash", "-c", command], stdout=subprocess.DEVNULL,
                                   start_new_session=True)
        turn("STARTED")
        threading.Thread(target=notify, args=(process,), daemon=True).start()
    elif "task show" in text:
        command = re.search(r"`([^`]*)`", text).group(1)
        output = subprocess.run(["bash", "-c", command], capture_output=True, text=True).stdout
        turn("ok", output)
    else:
        turn("READY")
"""


class OwnersCaseTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.base = Path(os.path.realpath(directory.name))
        self.project = self.base / "project"
        self.worktree = self.project / ".claude/worktrees/t1"
        self.records = self.project / ".concorde"
        (self.worktree / ".concorde/bin").mkdir(parents=True)
        (self.project / ".concorde/bin").mkdir(parents=True)
        (self.project / ".concorde/tasks/t1").mkdir(parents=True)
        (self.project / ".concorde/tasks/t1/task.json").write_text(
            json.dumps({"id": "t1", "worktree": str(self.worktree)})
        )
        (self.worktree / ".concorde/workspace.json").write_text(
            json.dumps(
                {
                    "workspace": "t1",
                    "traces": str(self.records / "tasks/t1/workspace"),
                    "concorde": str(self.records),
                }
            )
        )
        for place in (self.project, self.worktree):
            self.program(
                place / ".concorde/bin/concorde",
                FAKE_CONCORDE % {"records": str(self.records)},
            )

    def program(self, path: Path, text: str) -> Path:
        path.write_text(text)
        path.chmod(0o755)
        return path

    def run_case(self, wakes_all: bool = False) -> dict:
        claude = self.program(
            self.base / "claude",
            FAKE_CLAUDE % {"wakes_all": wakes_all, "records": str(self.records)},
        )
        return owners.owners(
            self.project,
            self.base / "case",
            grace=1.0,
            limit=60.0,
            claude_program=str(claude),
        )

    @verifies("scenario.e2e.owners-case")
    def test_only_the_owner_of_each_run_is_woken_and_the_others_see_it(self):
        value = self.run_case()
        self.assertEqual("passed", value["status"], value["problems"])
        self.assertEqual(
            ["unowned", "owned-by-claude"],
            [item["phase"] for item in value["phases"]],
        )
        self.assertEqual(
            [None, "claude-1"], [item["owner"] for item in value["phases"]]
        )
        for item in value["phases"]:
            woken = [entry["session"] for entry in item["verdicts"] if entry["woken"]]
            self.assertEqual([item["owner"]] if item["owner"] else [], woken)
            self.assertEqual("ok", item["status"])
            # Every session that does not own the run sees it through concorde task show.
            self.assertTrue(all(entry["ok"] for entry in item["seen"]), item["seen"])
            self.assertEqual(2 - (1 if item["owner"] else 0), len(item["seen"]))
        owner = value["phases"][1]["verdicts"][0]
        self.assertEqual(
            ("claude-1", ["task_notification"]),
            (owner["session"], owner["notifications"]),
        )
        # Every session's events are kept, and the case is recorded beside them.
        self.assertEqual(
            value, json.loads((self.base / "case/owners.json").read_text())
        )
        for session in value["sessions"]:
            self.assertTrue(Path(session["log"]).read_text())
        # The case released the workspace lock it held.
        with (self.records / "locks/workspaces/t1.lock").open("a+") as stream:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)

    @verifies("scenario.e2e.owners-case")
    def test_a_session_woken_for_a_run_it_does_not_own_fails_the_case(self):
        value = self.run_case(wakes_all=True)
        self.assertEqual("failed", value["status"])
        for problem in (
            "unowned: claude-1 was woken by a run it does not own",
            "unowned: claude-2 was woken by a run it does not own",
            "owned-by-claude: claude-2 was woken by a run it does not own",
        ):
            self.assertIn(
                f"{problem} (1 turn(s), notifications ['task_notification'])",
                value["problems"],
            )
        # The owner woken for its own run is no problem, however often it is woken.
        self.assertFalse(
            any("owned-by-claude: claude-1" in item for item in value["problems"])
        )

    @verifies("scenario.e2e.owners-case")
    def test_the_case_needs_two_sessions_and_a_task(self):
        with self.assertRaises(e2e.E2EError) as raised:
            owners.owners(self.project, claude=1)
        self.assertEqual("invalid_input", raised.exception.code)
        with self.assertRaises(e2e.E2EError) as raised:
            owners.owners(self.project, task="t9")
        self.assertEqual("no_task", raised.exception.code)

    def test_the_status_listed_for_a_run_is_read_from_task_show(self):
        output = 'noise {"a": 1}\n' + json.dumps(
            {"record": {}, "runs": [{"run_id": "r-1", "status": "blocked"}]}, indent=2
        )
        self.assertEqual("blocked", owners.listed_status(output, "r-1"))
        self.assertIsNone(owners.listed_status(output, "r-2"))
        self.assertIsNone(owners.listed_status("no JSON at all", "r-1"))


class LiveSessionTests(unittest.TestCase):
    @verifies("scenario.headless-sessions.live")
    def test_a_live_session_tells_its_own_wake_from_a_prompted_turn(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            claude = base / "claude"
            claude.write_text(FAKE_CLAUDE % {"wakes_all": False, "records": directory})
            claude.chmod(0o755)
            session = live.LiveSession(
                "claude-1", base, base / "logs", program=str(claude)
            )
            try:
                asked = session.send("Reply READY")
                session.wait_settled(asked, 30)
                self.assertEqual(1, len(session.turns(asked)))
                idle = time.time()
                started = session.send(
                    "in the background (run_in_background true), then end your turn at "
                    "once, replying only STARTED:\nsleep 1\n"
                )
                session.wait_settled(started, 30)
                quiet = time.time()
                self.assertFalse(session.woken(idle, started))
                deadline = time.monotonic() + 30
                while not session.woken(quiet) and time.monotonic() < deadline:
                    time.sleep(0.1)
                self.assertEqual(
                    ["task_notification"],
                    [event["subtype"] for event in session.notifications(quiet)],
                )
            finally:
                session.close()
            self.assertEqual(0, session.record()["exit"])
            kept = [json.loads(line) for line in session.log.read_text().splitlines()]
            self.assertTrue(all("at" in item and "event" in item for item in kept))

    @verifies("scenario.headless-sessions.live")
    def test_the_commands_of_live_sessions(self):
        argv = live.claude_command(model="m")
        self.assertEqual(
            ["claude", "-p", "--input-format", "stream-json", "--output-format"],
            argv[:5],
        )
        self.assertEqual(["Bash", "Read"], argv[argv.index("--allowedTools") + 1 :])
        self.assertEqual("m", argv[argv.index("--model") + 1])
        self.assertEqual(live.LIVE_NOTE, argv[argv.index("--append-system-prompt") + 1])


if __name__ == "__main__":
    unittest.main()
