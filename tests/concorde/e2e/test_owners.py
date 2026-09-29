"""The owners case and its live sessions, driven by stand-ins for `claude`, `pi` and `concorde`.

The stand-ins speak the protocols the live sessions use (Claude Code's stream-json on standard
input and output, pi's RPC records) and play what the real programs do that the case observes: a
Claude Code session is notified when its own background command ends, and a pi session's run
view shows every run in its status bar and wakes the session with a custom message when a run it
started ends. A pi stand-in that wakes for every run, as the run view once did, must fail the case.
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
runs = RECORDS / "runs"
if args[0] == "task-validation":
    run_id = "r-" + time.strftime("%%Y%%m%%dT%%H%%M%%S") + "-task_validation-" + uuid.uuid4().hex[:8]
    directory = runs / run_id
    directory.mkdir(parents=True)
    held = os.open(directory, os.O_RDONLY)
    fcntl.flock(held, fcntl.LOCK_EX)
    stamp = time.strftime("%%Y-%%m-%%dT%%H:%%M:%%SZ", time.gmtime())
    state = {"kind": "command", "run_id": run_id, "name": "task-validation", "workspace": "t1",
             "phase": "running", "status": None, "host_pid": os.getpid(), "started_at": stamp,
             "updated_at": stamp}
    (directory / "status.json").write_text(json.dumps(state))
    (runs / "locks").mkdir(exist_ok=True)
    lock = (runs / "locks" / "t1.lock").open("a+")
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
# notified when it ends, and a foreground command's output given as its tool result.
FAKE_CLAUDE = """#!/usr/bin/env python3
import json, re, subprocess, sys, threading
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

# A live pi session with Concorde's run view: every run in the status bar, `/concorde` listing
# the runs, `concorde_run` starting one, and a wake for the end of the runs it started, or of
# every run with WAKES_ALL.
FAKE_PI = """#!/usr/bin/env python3
import json, os, subprocess, sys, threading, time
from pathlib import Path
WAKES_ALL = %(wakes_all)r
RECORDS = Path(%(records)r)
WORKTREE = %(worktree)r
lock = threading.Lock()
owned, seen, woken = set(), set(), set()
def say(event):
    with lock:
        print(json.dumps(event), flush=True)
def runs():
    found = {}
    for directory in sorted((RECORDS / "runs").glob("r-*")):
        found[directory.name] = (directory / "result.json").exists()
    return found
def turn(text, custom=None):
    if custom:
        say({"type": "message_start", "message": {"role": "custom", "customType": custom}})
    say({"type": "agent_start"})
    say({"type": "message_end", "message": {"role": "assistant", "content": [
        {"type": "text", "text": text}]}})
    say({"type": "agent_settled"})
def view():
    while True:
        current = runs()
        running = [run for run, ended in current.items() if not ended]
        seen.update(running)
        say({"type": "extension_ui_request", "id": "s", "method": "setStatus",
             "statusKey": "concorde",
             "statusText": f"Concorde: {len(running)} running" if running else ""})
        for run, ended in current.items():
            if ended and run in seen and run not in woken and (run in owned or WAKES_ALL):
                woken.add(run)
                turn("DONE ok", "concorde-run")
        time.sleep(0.2)
threading.Thread(target=view, daemon=True).start()
for line in sys.stdin:
    record = json.loads(line)
    text = record["message"]
    say({"type": "response", "id": record.get("id"), "command": "prompt", "success": True})
    if text == "/concorde":
        lines = [("completed" if ended else "running").ljust(9) + f" t1 · task-validation ({run})"
                 for run, ended in runs().items()]
        say({"type": "extension_ui_request", "id": "n", "method": "notify",
             "message": "\\n".join(lines) or "No Concorde runs in this project yet."})
    elif "concorde_run" in text:
        before = set(runs())
        subprocess.Popen([os.path.join(WORKTREE, ".concorde/bin/concorde"), "task-validation",
                          "--wait", "60"], cwd=WORKTREE, stdout=subprocess.DEVNULL,
                         start_new_session=True)
        while not set(runs()) - before:
            time.sleep(0.05)
        owned.update(set(runs()) - before)
        turn("STARTED")
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
        (self.project / ".concorde/tasks").mkdir(parents=True)
        (self.project / ".pi/extensions").mkdir(parents=True)
        (self.project / ".concorde/tasks/t1.json").write_text(
            json.dumps({"id": "t1", "worktree": str(self.worktree)})
        )
        (self.worktree / ".concorde/workspace.json").write_text(
            json.dumps({"name": "t1", "records": str(self.records)})
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
        claude = self.program(self.base / "claude", FAKE_CLAUDE)
        pi = self.program(
            self.base / "pi",
            FAKE_PI
            % {
                "wakes_all": wakes_all,
                "records": str(self.records),
                "worktree": str(self.worktree),
            },
        )
        return owners.owners(
            self.project,
            self.base / "case",
            grace=1.0,
            limit=60.0,
            claude_program=str(claude),
            pi_program=str(pi),
        )

    @verifies("scenario.e2e.owners-case")
    def test_only_the_owner_of_each_run_is_woken_and_the_others_see_it(self):
        value = self.run_case()
        self.assertEqual("passed", value["status"], value["problems"])
        self.assertEqual(
            ["unowned", "owned-by-pi", "owned-by-claude"],
            [item["phase"] for item in value["phases"]],
        )
        self.assertEqual(
            [None, "pi-1", "claude-1"], [item["owner"] for item in value["phases"]]
        )
        for item in value["phases"]:
            woken = [entry["session"] for entry in item["verdicts"] if entry["woken"]]
            self.assertEqual([item["owner"]] if item["owner"] else [], woken)
            self.assertEqual("ok", item["status"])
            # Every session that does not own the run sees it: pi through /concorde and its
            # status bar, Claude Code through concorde task show.
            self.assertTrue(all(entry["ok"] for entry in item["seen"]), item["seen"])
            self.assertEqual(4 - (1 if item["owner"] else 0), len(item["seen"]))
        owned = value["phases"][1]["verdicts"][2]
        self.assertEqual(
            ("pi-1", ["concorde-run"]), (owned["session"], owned["notifications"])
        )
        claude = value["phases"][2]["verdicts"][0]
        self.assertEqual(["task_notification"], claude["notifications"])
        # Every session's events are kept, and the case is recorded beside them.
        self.assertEqual(
            value, json.loads((self.base / "case/owners.json").read_text())
        )
        for session in value["sessions"]:
            self.assertTrue(Path(session["log"]).read_text())
        # The case released the workspace lock it held.
        with (self.records / "runs/locks/t1.lock").open("a+") as stream:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)

    @verifies("scenario.e2e.owners-case")
    def test_a_session_woken_for_a_run_it_does_not_own_fails_the_case(self):
        value = self.run_case(wakes_all=True)
        self.assertEqual("failed", value["status"])
        self.assertIn(
            "unowned: pi-1 was woken by a run it does not own "
            "(1 turn(s), notifications ['concorde-run'])",
            value["problems"],
        )
        self.assertIn(
            "owned-by-pi: pi-2 was woken by a run it does not own "
            "(1 turn(s), notifications ['concorde-run'])",
            value["problems"],
        )
        self.assertFalse(
            any("claude-2 was woken" in item for item in value["problems"])
        )

    @verifies("scenario.e2e.owners-case")
    def test_the_case_needs_two_sessions_a_task_and_the_pi_extension(self):
        with self.assertRaises(e2e.E2EError) as raised:
            owners.owners(self.project, claude=1, pi=0)
        self.assertEqual("invalid_input", raised.exception.code)
        with self.assertRaises(e2e.E2EError) as raised:
            owners.owners(self.project, task="t9")
        self.assertEqual("no_task", raised.exception.code)
        (self.project / ".pi/extensions").rmdir()
        with self.assertRaises(e2e.E2EError) as raised:
            owners.owners(self.project)
        self.assertEqual("pi_not_installed", raised.exception.code)

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
            claude.write_text(FAKE_CLAUDE)
            claude.chmod(0o755)
            session = live.LiveSession(
                "claude-1", "claude", base, base / "logs", program=str(claude)
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
        argv = live.pi_command("s-1", Path("/tmp/x"))
        self.assertEqual(["pi", "--mode", "rpc", "--approve"], argv[:4])
        self.assertEqual("s-1", argv[argv.index("--session-id") + 1])
        with self.assertRaises(e2e.E2EError) as raised:
            live.LiveSession("x", "codex", Path("."), Path(tempfile.mkdtemp()))
        self.assertEqual("unknown_client", raised.exception.code)


if __name__ == "__main__":
    unittest.main()
