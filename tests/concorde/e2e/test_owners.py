"""The owners case and its live sessions, driven by stand-ins for `claude` and `concorde`.

The `claude` stand-in speaks the protocol the live sessions use, Claude Code's stream-json on
standard input and output, and plays what the real program does that the case observes: a session
is notified when its own background command ends. A stand-in that is also woken for the end of
every run it did not start must fail the case, and so must one never woken at all.
"""

from __future__ import annotations

import fcntl
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
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
owners = e2e.owners
live = sys.modules["live"]

# `concorde task-validation --wait N` records a run that waits in the lobby for the workspace lock,
# then enters the workspace folder and ends ok, or, with REFUSED, is refused in the lobby with
# workspace_busy once it holds the lock, as a run whose wait expired is, DELAY seconds after it
# took the lock; `concorde task show t1`
# lists the runs of t1 with their status.
FAKE_CONCORDE = """#!/usr/bin/env python3
import fcntl, json, os, sys, time, uuid
from pathlib import Path
RECORDS = Path(%(records)r)
REFUSED = %(refused)r
DELAY = %(delay)r
args = sys.argv[1:]
# Tracing's layout: the task's runs in its workspace folder, a run waiting for the workspace lock
# in the lobby, every lock under locks/.
runs = RECORDS / "tasks" / "t1" / "workspace" / "runs"
locks = RECORDS / "locks"
if args[0] == "task-validation":
    assert int(args[args.index("--wait") + 1]) > 0
    run_id = "r-" + time.strftime("%%Y%%m%%dT%%H%%M%%S") + "-task_validation-" + uuid.uuid4().hex[:8]
    directory = RECORDS / "lobby" / run_id
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
    time.sleep(DELAY)
    if REFUSED:
        result = {"run_id": run_id, "status": "failed", "summary": "t1 is busy",
                  "host_evidence": [{"ref": "workspace_busy"}]}
    else:
        runs.mkdir(parents=True, exist_ok=True)
        directory = directory.rename(runs / run_id)
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

# A live Claude Code session: a turn per prompt, a background command run detached and, unless
# NOTIFIES is false, notified when it ends, and a foreground command's output given as its tool
# result; with WAKES_ALL also woken, with a notification of its own, for the end of every run, and
# with EXITS ended right after the turn that started a background command.
FAKE_CLAUDE = """#!/usr/bin/env python3
import json, re, subprocess, sys, threading, time
from pathlib import Path
WAKES_ALL = %(wakes_all)r
NOTIFIES = %(notifies)r
EXITS = %(exits)r
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
        if EXITS:
            sys.exit(0)
        if NOTIFIES:
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
        self.concorde()

    def concorde(self, refused: bool = False, delay: float = 0.0) -> None:
        for place in (self.project, self.worktree):
            self.program(
                place / ".concorde/bin/concorde",
                FAKE_CONCORDE
                % {"records": str(self.records), "refused": refused, "delay": delay},
            )

    def program(self, path: Path, text: str) -> Path:
        path.write_text(text)
        path.chmod(0o755)
        return path

    def run_case(
        self,
        wakes_all: bool = False,
        notifies: bool = True,
        wake: float = 60.0,
        exits: bool = False,
        limit: float = 60.0,
    ) -> dict:
        claude = self.program(
            self.base / "claude",
            FAKE_CLAUDE
            % {
                "wakes_all": wakes_all,
                "notifies": notifies,
                "exits": exits,
                "records": str(self.records),
            },
        )
        return owners.owners(
            self.project,
            self.base / "case",
            grace=1.0,
            wake=wake,
            limit=limit,
            claude_program=str(claude),
        )

    @verifies("scenario.e2e.owners-passed")
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

    @verifies("scenario.e2e.owners-unwanted-wake")
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

    @verifies("scenario.e2e.owner-not-woken")
    def test_an_owner_not_woken_by_its_deadline_fails_the_case_without_an_error(self):
        started = time.monotonic()
        value = self.run_case(notifies=False, wake=2.0)
        # The window ended at the wake deadline, long before the case's limit.
        self.assertLess(time.monotonic() - started, 50)
        self.assertEqual("failed", value["status"])
        self.assertEqual(
            ["owned-by-claude: the owner claude-1 was not woken when its run ended"],
            value["problems"],
        )
        owner = value["phases"][1]["verdicts"][0]
        self.assertEqual(
            ("claude-1", True, False),
            (owner["session"], owner["owner"], owner["woken"]),
        )
        self.assertEqual("ok", value["phases"][1]["status"])
        self.assertEqual(
            value, json.loads((self.base / "case/owners.json").read_text())
        )

    @verifies("scenario.e2e.owners-run-refused")
    def test_a_run_refused_for_a_busy_workspace_stops_the_case_with_an_error(self):
        self.concorde(refused=True)
        # A read after the first that found the result may find none, as one does while the run
        # rewrites its progress file under load: the case must judge the result it read.
        read = owners.result_of
        found = set()

        def once(records, run_id):
            if run_id in found:
                return None
            result = read(records, run_id)
            if result is not None:
                found.add(run_id)
            return result

        with (
            patch.object(owners, "result_of", once),
            self.assertRaises(e2e.E2EError) as raised,
        ):
            self.run_case()
        self.assertEqual("workspace_busy", raised.exception.code)
        self.assertIn("phase unowned", raised.exception.detail)
        refused = Path(raised.exception.evidence["result"])
        self.assertEqual(self.records / "lobby", refused.parent.parent)

    @verifies("scenario.e2e.owners-run-refused")
    def test_a_refusal_after_the_cases_limit_is_still_seen(self):
        # The run is refused later than the case's limit after the release, but within its
        # queue wait: the case reports the refusal, not its own deadline.
        self.concorde(refused=True, delay=4.0)
        with self.assertRaises(e2e.E2EError) as raised:
            self.run_case(limit=3.0)
        self.assertEqual("workspace_busy", raised.exception.code)

    @verifies("scenario.e2e.owners-competing-run")
    def test_a_competing_run_is_never_judged_as_the_cases_run(self):
        # A run of the same workspace that the case did not launch appears in the lobby after
        # the case looked at the run store: its runner is no descendant of the launcher.
        competitor = self.records / "lobby/r-20261008T000000-task_validation-competitor"
        competitor.mkdir(parents=True)
        (competitor / "status.json").write_text(
            json.dumps(
                {
                    "kind": "command",
                    "run_id": competitor.name,
                    "workspace": "t1",
                    "host_pid": os.getpid(),
                }
            )
        )
        with patch.object(owners, "known_runs", return_value=set()):
            value = self.run_case()
        self.assertEqual("passed", value["status"], value["problems"])
        for item in value["phases"]:
            self.assertNotEqual(competitor.name, item["run"])
            self.assertEqual("ok", item["status"])

    def test_the_unowned_launch_that_cannot_start_is_a_command_failure(self):
        (self.worktree / ".concorde/bin/concorde").chmod(0o644)
        with self.assertRaises(e2e.E2EError) as raised:
            self.run_case()
        self.assertEqual("command_failed", raised.exception.code)
        self.assertIn("could not be started", raised.exception.detail)

    @verifies("scenario.e2e.owners-unwanted-wake")
    def test_the_judged_time_starts_when_the_launching_turn_ended(self):
        # A notification read after the launching turn's result but before the case noticed
        # that turn's end lies in the judged time.
        session = live.LiveSession.__new__(live.LiveSession)
        session.events = [
            (10.0, {"type": "system", "subtype": "init"}),
            (11.0, {"type": "result"}),
            (11.2, {"type": "system", "subtype": "task_notification"}),
        ]
        session._lock = threading.Lock()
        baseline = owners.turn_end(session, 9.0)
        self.assertEqual(11.0, baseline)
        self.assertTrue(session.woken(baseline, 12.0))

    def test_the_owner_is_told_the_worktree_as_one_shell_word(self):
        worktree = self.base / "it's a worktree; echo no"
        worktree.mkdir()
        line = owners.owner_prompt(worktree, 60.0).split("STARTED:\n", 1)[1]
        command = line.split(" && ", 1)[0]
        done = subprocess.run(
            ["bash", "-c", f"{command} && pwd"], capture_output=True, text=True
        )
        self.assertEqual(str(worktree), done.stdout.strip())

    @verifies("scenario.e2e.owners-session-ended")
    def test_an_owner_that_ends_before_it_is_woken_stops_the_case(self):
        with self.assertRaises(e2e.E2EError) as raised:
            self.run_case(exits=True)
        self.assertEqual("session_failed", raised.exception.code)
        self.assertIn("live session claude-1 ended", raised.exception.detail)
        self.assertIn("phase owned-by-claude", raised.exception.detail)

    def test_the_queued_run_waits_longer_than_the_case_holds_the_lock(self):
        self.assertEqual(1200, owners.queue_wait(owners.LIMIT_SECONDS))
        self.assertIn(
            "task-validation --wait 120\n", owners.owner_prompt(self.worktree, 60.0)
        )

    @verifies("scenario.e2e.owners-too-few-sessions")
    def test_the_case_needs_two_sessions(self):
        with (
            patch.object(owners, "LiveSession") as started,
            self.assertRaises(e2e.E2EError) as raised,
        ):
            owners.owners(self.project, claude=1)
        self.assertEqual("invalid_input", raised.exception.code)
        started.assert_not_called()

    @verifies("scenario.e2e.owners-no-task")
    def test_the_case_needs_a_task_with_a_worktree(self):
        with (
            patch.object(owners, "LiveSession") as started,
            self.assertRaises(e2e.E2EError) as raised,
        ):
            owners.owners(self.project, task="t9")
        self.assertEqual("no_task", raised.exception.code)
        started.assert_not_called()
        # A task record whose worktree is gone is refused the same way.
        (self.project / ".concorde/tasks/t1/task.json").write_text(
            json.dumps({"id": "t1", "worktree": str(self.base / "removed")})
        )
        with (
            patch.object(owners, "LiveSession") as started,
            self.assertRaises(e2e.E2EError) as raised,
        ):
            owners.owners(self.project, task="t1")
        self.assertEqual("no_task", raised.exception.code)
        self.assertIn("does not exist", raised.exception.detail)
        started.assert_not_called()

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
            claude.write_text(
                FAKE_CLAUDE
                % {
                    "wakes_all": False,
                    "notifies": True,
                    "exits": False,
                    "records": directory,
                }
            )
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
