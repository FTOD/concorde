"""The project MCP server over a real stdio MCP connection to ``concorde project-mcp``."""

from __future__ import annotations

import json
import os
import queue
import shlex
import signal
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

from concorde.errors import ERROR_SCHEMA
from concorde.execution.runs import workspace_lock
from concorde.project_mcp.server import channel_from, detect_channel
from concorde.spec.schema import validate
from concorde.spec.verification import verifies
from concorde.tasks import store
from concorde.tracing import layout, locks
from tests.concorde.support.environment import child_environment
from tests.concorde.support.operation_project import OperationProject, commit
from tests.concorde.support.paths import REPOSITORY_ROOT
from tests.concorde.tasks.deliveries import deliver

COMMAND = [sys.executable, str(REPOSITORY_ROOT / "scripts/concorde.py"), "project-mcp"]
TOOLS = {
    "task_list",
    "task_show",
    "trace_show",
    "run_result",
    "workflow_report",
    "locks",
    "task_open",
    "task_escalate",
    "task_rebind",
    "task_report",
    "task_answer",
    "task_close",
    "task_merge",
    "register_wait",
}
# How long a test waits for a channel event before it fails.
EVENT_WAIT = 60
# A post-merge check that passes; the fixture's Specs are not meant to validate.
PASSING = shlex.join([sys.executable, "-c", "pass"])


def git(root, *arguments):
    return subprocess.run(
        ["git", *arguments], cwd=root, check=True, capture_output=True, text=True
    ).stdout.strip()


class Client:
    """A minimal MCP client that also collects the server's channel notifications."""

    def __init__(self, test, cwd: Path, **environment):
        self.process = subprocess.Popen(
            COMMAND,
            cwd=cwd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
            env=child_environment(**environment),
        )
        test.addCleanup(self.close)
        self.next = 0
        self.responses: dict = {}
        self.events: queue.Queue = queue.Queue()
        self.arrived = threading.Condition()
        threading.Thread(target=self.read, daemon=True).start()
        self.initialized = self.request(
            "initialize",
            {
                "protocolVersion": "2025-11-25",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "0"},
            },
        )
        self.send({"jsonrpc": "2.0", "method": "notifications/initialized"})

    def read(self):
        for line in self.process.stdout:
            message = json.loads(line)
            if message.get("method") == "notifications/claude/channel":
                self.events.put(message["params"])
                continue
            with self.arrived:
                self.responses[message.get("id")] = message
                self.arrived.notify_all()

    def close(self):
        if self.process.poll() is None:
            self.process.stdin.close()
            self.process.wait(10)

    def send(self, message):
        self.process.stdin.write(json.dumps(message) + "\n")
        self.process.stdin.flush()

    def request(self, method, params=None):
        self.next += 1
        identity = self.next
        self.send(
            {"jsonrpc": "2.0", "id": identity, "method": method, "params": params or {}}
        )
        with self.arrived:
            self.arrived.wait_for(lambda: identity in self.responses, timeout=60)
        return self.responses.pop(identity)["result"]

    def call(self, name, **arguments):
        result = self.request("tools/call", {"name": name, "arguments": arguments})
        return json.loads(result["content"][0]["text"]), result["isError"]

    def event(self, timeout=EVENT_WAIT) -> dict:
        return self.events.get(timeout=timeout)


def holding(path: Path, session: str, task: str | None = None):
    """A process holding the lock ``path`` for session ``session`` until its stdin closes."""
    code = (
        "import sys\n"
        "from concorde.tracing import locks\n"
        f"with locks.hold({str(path)!r}, 'a test holder', task={task!r}):\n"
        "    print('held', flush=True)\n"
        "    sys.stdin.read()\n"
    )
    process = subprocess.Popen(
        [sys.executable, "-c", code],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
        env=child_environment(
            PYTHONPATH=str(REPOSITORY_ROOT / "src"), CLAUDE_CODE_SESSION_ID=session
        ),
    )
    assert process.stdout.readline().strip() == "held"
    return process


def open_inodes(pid: int) -> set[int]:
    """The inodes of the files the process ``pid`` has open."""
    found = set()
    for entry in Path(f"/proc/{pid}/fd").iterdir():
        try:
            found.add(os.stat(entry).st_ino)
        except OSError:
            pass
    return found


class ProjectMcpTests(unittest.TestCase):
    def setUp(self):
        self.project = OperationProject(self)
        self.root = self.project.root
        gitignore = self.root / ".gitignore"
        gitignore.write_text(
            gitignore.read_text() + "".join(f"{path}\n" for path in layout.IGNORED)
        )
        git(self.root, "config", "user.name", "t")
        git(self.root, "config", "user.email", "t@t")
        commit(self.root, "ignore task records")

    def client(self, channel: bool = True, cwd: Path | None = None, **environment):
        return Client(
            self,
            cwd or self.root,
            CONCORDE_CHANNEL="1" if channel else "0",
            CLAUDE_CODE_SESSION_ID="session-main",
            **environment,
        )

    def refusal(self, value, error, code):
        self.assertTrue(error, value)
        validate(value["error"], ERROR_SCHEMA)
        self.assertEqual(code, value["error"]["code"], value)
        return value["error"]

    def workspace_lock(self, task="t1") -> Path:
        return layout.lock_file(self.root / ".concorde", "workspace", task)

    @verifies("scenario.main-session.project-mcp-session")
    def test_session_declares_tools_and_channel(self):
        client = self.client()
        capabilities = client.initialized["capabilities"]
        self.assertEqual({}, capabilities["experimental"]["claude/channel"])
        self.assertIn("tools", capabilities)
        self.assertEqual("2025-06-18", client.initialized["protocolVersion"])
        listed = client.request("tools/list")["tools"]
        self.assertEqual(TOOLS, {tool["name"] for tool in listed})

    @verifies("scenario.main-session.project-mcp-queries")
    def test_queries_answer_the_project_from_any_worktree(self):
        self.project.open_task("t1")
        worktree = self.project.worktree("t1")
        client = self.client(cwd=worktree, CLAUDE_PROJECT_DIR=str(worktree))
        listed, error = client.call("task_list")
        self.assertFalse(error, listed)
        self.assertEqual(["t1"], [record["id"] for record in listed])
        shown, error = client.call("task_show", task="t1")
        self.assertFalse(error, shown)
        self.assertEqual("open", shown["record"]["state"])
        trace, error = client.call("trace_show", node="t1", depth=1)
        self.assertFalse(error, trace)
        held, error = client.call("locks")
        self.assertEqual({"merge": None, "workspaces": {"t1": None}}, held)

    @verifies("scenario.main-session.project-mcp-refusals")
    def test_refusals_are_error_links(self):
        client = self.client()
        value, error = client.call("task_show", task="nobody")
        link = self.refusal(value, error, "unknown_task")
        self.assertEqual("Tasks (concorde task show)", link["actor"])
        value, error = client.call("task_show")
        link = self.refusal(value, error, "invalid_input")
        self.assertIn("project MCP server", link["actor"])
        value, error = client.call("no_such_tool")
        self.refusal(value, error, "invalid_input")

    @verifies("scenario.main-session.project-mcp-short-writes")
    def test_open_escalate_close(self):
        client = self.client()
        opened, error = client.call(
            "task_open", task="t2", goal="Fix A.", modules=["module.a"]
        )
        self.assertFalse(error, opened)
        self.assertEqual("open", opened["record"]["state"])
        escalated, error = client.call(
            "task_escalate",
            task="t2",
            by="task-session",
            code="need_choice",
            detail="Which retry limit?",
            reason="decision",
            explanation="the limit is a promise of the Module",
            options=["3", "5"],
        )
        self.assertFalse(error, escalated)
        self.assertEqual(1, escalated["number"])
        self.assertEqual("task-session", escalated["escalated"]["level"])
        rebound, error = client.call("task_rebind", task="t2", main="concorde-8e")
        self.assertFalse(error, rebound)
        self.assertEqual(
            ("concorde-8e", None), (rebound["record"]["main"], rebound["former"])
        )
        listed, _ = client.call("task_list", main="concorde-8e")
        self.assertEqual(["t2"], [record["id"] for record in listed])
        reported, error = client.call(
            "task_report", task="t2", text="Which retry limit?", escalations=[1]
        )
        self.assertFalse(error, reported)
        self.assertEqual(
            ("concorde-8e", 1, [1]),
            (
                reported["main"],
                reported["report"]["number"],
                reported["report"]["escalations"],
            ),
        )
        answered, error = client.call("task_answer", task="t2", reports=[1], text="5")
        self.assertFalse(error, answered)
        shown, _ = client.call("task_show", task="t2")
        self.assertEqual("5", shown["record"]["reports"][0]["answer"]["text"])
        closed, error = client.call(
            "task_close", task="t2", outcome="completed", note="answered"
        )
        self.assertFalse(error, closed)
        self.assertEqual("closed", closed["record"]["state"])

    @verifies("scenario.main-session.project-mcp-lock-busy")
    def test_busy_locks_are_refused_at_once_naming_the_holder(self):
        self.project.open_task("t1")
        deliver(self.project.worktree("t1"))
        holder = holding(self.workspace_lock(), "session-other", "t1")
        self.addCleanup(holder.wait)
        self.addCleanup(holder.stdin.close)
        client = self.client()
        started = time.monotonic()
        value, error = client.call("task_merge", task="t1")
        self.assertLess(time.monotonic() - started, 10)
        link = self.refusal(value, error, "workspace_busy")
        self.assertIn("session-other", link["detail"])
        self.assertIn("task t1", link["detail"])
        held = json.loads(link["evidence"][0]["detail"])
        self.assertEqual(
            {"session": "session-other", "task": "t1", "pid": holder.pid},
            {key: held[key] for key in ("session", "task", "pid")},
        )
        holder.stdin.close()
        holder.wait(10)
        merging = holding(store.merge_lock_path(self.root), "session-other", "t9")
        self.addCleanup(merging.wait)
        self.addCleanup(merging.stdin.close)
        value, error = client.call("task_merge", task="t1")
        link = self.refusal(value, error, "merge_busy")
        self.assertIn("session-other", link["detail"])
        # The refusal released the workspace lock it had taken.
        self.assertIsNone(locks.entry(self.workspace_lock()))
        self.assertEqual(
            "delivered", store.show_task(self.root, "t1")["record"]["state"]
        )

    @verifies("scenario.main-session.project-mcp-lock-handover")
    def test_granted_locks_belong_to_the_merge_process(self):
        self.project.open_task("t1")
        deliver(self.project.worktree("t1"))
        marker = Path(tempfile.mkdtemp()) / "go"
        started = Path(tempfile.mkdtemp()) / "started"
        check = shlex.join(
            [
                sys.executable,
                "-c",
                (
                    "import pathlib, time\n"
                    f"pathlib.Path({str(started)!r}).write_text('x')\n"
                    f"while not pathlib.Path({str(marker)!r}).exists(): time.sleep(0.05)\n"
                ),
            ]
        )
        client = self.client()
        value, error = client.call("task_merge", task="t1", checks=[check])
        self.assertFalse(error, value)
        pid = value["started"]["pid"]
        while not started.exists():
            time.sleep(0.05)
        merge_lock = store.merge_lock_path(self.root)
        for path in (merge_lock, self.workspace_lock()):
            entry = locks.entry(path)
            self.assertEqual(
                {"pid": pid, "session": "session-main", "task": "t1"},
                {key: entry[key] for key in ("pid", "session", "task")},
            )
            # The merge process holds the lock's file open; the server no longer does.
            self.assertIn(os.stat(path).st_ino, open_inodes(pid), path)
            self.assertNotIn(
                os.stat(path).st_ino, open_inodes(client.process.pid), path
            )
        # The server ending does not end the merge or release its locks.
        client.process.send_signal(signal.SIGKILL)
        client.process.wait(10)
        self.assertTrue(locks.held(merge_lock))
        self.assertTrue(locks.held(self.workspace_lock()))
        marker.write_text("go")
        self.assertTrue(locks.wait_released(merge_lock, 60))
        self.assertEqual("closed", store.show_task(self.root, "t1")["record"]["state"])
        output = json.loads(Path(value["started"]["output"]).read_text())
        self.assertEqual("merged", output["record"]["closed"]["outcome"])

    @verifies("scenario.main-session.project-mcp-merge-wakes")
    def test_the_merge_end_wakes_the_session_with_its_output(self):
        self.project.open_task("t1")
        deliver(self.project.worktree("t1"))
        client = self.client()
        value, error = client.call("task_merge", task="t1", checks=[PASSING])
        self.assertFalse(error, value)
        self.assertEqual({"channel": True}, value["wake"])
        event = client.event()
        self.assertEqual("merge_ended", event["meta"]["event"])
        self.assertEqual("t1", event["meta"]["task"])
        self.assertEqual("0", event["meta"]["exit_code"], event["content"])
        self.assertIn('"merged"', event["content"])

    @verifies("scenario.main-session.project-mcp-wait-channel")
    def test_register_wait_wakes_on_release_and_on_a_task_state(self):
        self.project.open_task("t1")
        client = self.client()
        holder = holding(self.workspace_lock(), "session-other", "t1")
        self.addCleanup(holder.wait)
        registered, error = client.call("register_wait", lock="workspace", task="t1")
        self.assertFalse(error, registered)
        self.assertTrue(registered["registered"])
        self.assertTrue(client.events.empty())
        # A holder that dies wakes the wait as one that ends does.
        holder.kill()
        event = client.event()
        self.assertEqual(
            ("wait_done", "lock"), (event["meta"]["event"], event["meta"]["kind"])
        )
        self.assertIn("session-other", event["content"])
        registered, error = client.call("register_wait", task="t1", until=["delivered"])
        self.assertTrue(registered["registered"], registered)
        # A delivery is made under the task's workspace lock, as by the delivery run.
        store_ = store.workspace_store(self.root, "t1")
        with workspace_lock(store_, "t1", "a delivery run"):
            deliver(self.project.worktree("t1"))
        event = client.event()
        self.assertEqual("wait_done", event["meta"]["event"])
        self.assertIn('"delivered"', event["content"])
        # Already reached: answered at once, nothing registered.
        now, error = client.call("register_wait", task="t1", until=["delivered"])
        self.assertEqual(
            {"registered": False, "already": {"task": "t1", "state": "delivered"}}, now
        )

    @verifies("scenario.main-session.project-mcp-wait-fallback")
    def test_without_a_channel_the_wait_names_the_command(self):
        self.project.open_task("t1")
        holder = holding(self.workspace_lock(), "session-other", "t1")
        self.addCleanup(holder.wait)
        self.addCleanup(holder.stdin.close)
        client = self.client(channel=False)
        answer, error = client.call("register_wait", lock="workspace", task="t1")
        self.assertFalse(error, answer)
        self.assertEqual(False, answer["registered"])
        self.assertEqual(False, answer["channel"])
        self.assertEqual("concorde task wait t1 --lock workspace", answer["command"])
        answer, _ = client.call("register_wait", task="t1", until=["closed", "failed"])
        self.assertEqual(
            "concorde task wait t1 --until closed,failed", answer["command"]
        )
        store.rebind(self.root, "t1", "concorde-7d")
        answer, _ = client.call("register_wait", task="t1", rebound="concorde-7d")
        self.assertEqual(
            "concorde task wait t1 --rebound concorde-7d", answer["command"]
        )
        answer, _ = client.call("register_wait", task="t1", rebound="concorde-6c")
        self.assertEqual(
            {"task": "t1", "main": "concorde-7d", "former": "concorde-6c"},
            answer["already"],
        )


class ChannelDetectionTests(unittest.TestCase):
    @verifies("scenario.main-session.project-mcp-channel-detection")
    def test_an_interactive_claude_that_names_the_server(self):
        flagged = [
            "claude",
            "--dangerously-load-development-channels",
            "server:concorde",
            "--model",
            "opus",
        ]
        self.assertTrue(
            channel_from("concorde", [(["node", "x"], False), (flagged, True)])
        )
        self.assertTrue(
            channel_from(
                "concorde",
                [(["claude", "--channels", "plugin:a@b server:concorde"], True)],
            )
        )
        # A background session is never woken by channel events, flag or not.
        self.assertFalse(channel_from("concorde", [(flagged, False)]))
        self.assertFalse(
            channel_from("concorde", [(["claude", "--model", "server:concorde"], True)])
        )
        self.assertFalse(
            channel_from(
                "concorde",
                [
                    (
                        [
                            "claude",
                            "--dangerously-load-development-channels",
                            "server:other",
                        ],
                        True,
                    )
                ],
            )
        )
        # The environment decides when it says so.
        self.assertFalse(detect_channel("concorde", {"CONCORDE_CHANNEL": "0"}))
        self.assertTrue(detect_channel("concorde", {"CONCORDE_CHANNEL": "1"}))


if __name__ == "__main__":
    unittest.main()
