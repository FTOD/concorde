"""The project MCP server over a real stdio MCP connection to ``concorde project-mcp``."""

from __future__ import annotations

import contextlib
import json
import os
import queue
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import textwrap
import threading
import time
import unittest
from pathlib import Path
from typing import ClassVar

from concorde.kernel.errors import ERROR_SCHEMA
from tests.concorde.support.ignored import TRACES
from concorde.execution.runs import load_result, run_state
from concorde.kernel.locking import workspace_lock
from concorde.distribution.project_mcp.server import channel_from, detect_channel
from concorde.spec.schema import validate
from concorde.spec.verification import verifies
from concorde.coordination.tasks import store, wait
from concorde.kernel.tracing import layout, locks
from concorde.kernel.tracing import node as trace
from concorde.workflows import store as workflow_store
from tests.concorde.support.brownfield_project import BrownfieldProject
from tests.concorde.support.brownfield_project import commit as commit_all
from tests.concorde.support.environment import child_environment
from tests.concorde.support.operation_project import OperationProject, commit
from tests.concorde.support.paths import REPOSITORY_ROOT
from tests.concorde.tasks.deliveries import deliver, write_run

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
    "workflow_step",
    "task_resolve",
    "issue_list",
    "issue_show",
    "issue_check",
    "issue_report",
    "issue_close",
    "issue_reopen",
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
        self.notices: queue.Queue = queue.Queue()
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
            if "method" in message and "id" not in message:
                self.notices.put(message["method"])
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
        "from concorde.kernel.tracing import locks\n"
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


def children(pid: int) -> list[int]:
    """The processes the process ``pid`` started that still run."""
    found = []
    for thread in Path(f"/proc/{pid}/task").iterdir():
        found += [int(word) for word in (thread / "children").read_text().split()]
    return found


def alive(pid: int) -> bool:
    """Whether the process ``pid`` exists and is no zombie."""
    try:
        state = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[0]
    except OSError:
        return False
    return state != "Z"


class ProjectMcpTests(unittest.TestCase):
    def setUp(self):
        self.project = OperationProject(self)
        self.root = self.project.root
        gitignore = self.root / ".gitignore"
        gitignore.write_text(
            gitignore.read_text() + "".join(f"{path}\n" for path in TRACES)
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

    @verifies("scenario.main-session.project-mcp-run-result")
    def test_run_result_answers_running_finished_and_lost_runs_only(self):
        self.project.open_task("t1")
        write_run(self.root, "r-done", "t1", status="ok")
        write_run(self.root, "r-live", "t1", status=None)
        write_run(self.root, "r-lost", "t1", status=None)
        live = layout.lock_file(self.root / ".concorde", "run", "r-live")
        live.parent.mkdir(parents=True, exist_ok=True)
        # The test stands in for the runner of r-live, holding its run lock.
        runner = contextlib.ExitStack()
        self.addCleanup(runner.close)
        runner.enter_context(locks.hold(live, "a test runner", wait=None))
        client = self.client()
        done, error = client.call("run_result", run="r-done")
        self.assertFalse(error, done)
        self.assertEqual(
            ("r-done", False, "ok"), (done["run"], done["running"], done["result"]["status"])
        )
        running, error = client.call("run_result", run="r-live")
        self.assertFalse(error, running)
        self.assertEqual((True, None), (running["running"], running["result"]))
        self.assertEqual("running", running["progress"]["phase"])
        # A runner that ended without its result leaves the run lost.
        lost, error = client.call("run_result", run="r-lost")
        self.assertFalse(error, lost)
        self.assertEqual((False, None), (lost["running"], lost["result"]))
        self.assertEqual("r-lost", lost["progress"]["run_id"])
        # A task's node, or no node at all, is no run.
        for name in ("t1", "r-none"):
            value, error = client.call("run_result", run=name)
            self.refusal(value, error, "unknown_run")

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
        # trace_show refuses with Tracing's own link, as `concorde trace show` does.
        value, error = client.call("trace_show", node="nobody")
        link = self.refusal(value, error, "unknown_node")
        self.assertEqual("Tracing (concorde trace)", link["actor"])
        self.assertIn("concorde trace list --history --unbound", link["options"][0])

    @verifies("scenario.main-session.project-mcp-fresh-code")
    def test_each_call_answers_with_the_primary_worktrees_current_concorde(self):
        self.project.open_task("t1")
        # The primary worktree's `concorde` runs a copy of Concorde that the test changes.
        source = Path(tempfile.mkdtemp()) / "src"
        self.addCleanup(shutil.rmtree, source.parent, True)
        shutil.copytree(
            REPOSITORY_ROOT / "src/concorde",
            source / "concorde",
            ignore=shutil.ignore_patterns("__pycache__"),
        )
        launcher = self.root / ".concorde/bin/concorde"
        launcher.parent.mkdir(parents=True, exist_ok=True)
        launcher.write_text(
            "#!/bin/sh\n"
            f"PYTHONPATH={shlex.quote(str(source))} "
            f'exec {shlex.quote(sys.executable)} -m concorde "$@"\n'
        )
        launcher.chmod(0o755)
        client = self.client()
        self.assertTrue(client.initialized["capabilities"]["tools"]["listChanged"])
        self.assertEqual(
            TOOLS, {tool["name"] for tool in client.request("tools/list")["tools"]}
        )
        listed, error = client.call("task_list")
        self.assertFalse(error, listed)
        self.assertEqual(["t1"], [record["id"] for record in listed])
        # Concorde changes while the session runs, as a merge or `concorde update` changes it: a
        # tool answers otherwise and another tool is added.
        tools = source / "concorde/coordination/tasks/tools.py"
        tools.write_text(
            tools.read_text()
            + textwrap.dedent(
                """
                TOOLS["fresh_probe"] = {"description": "added later", "inputSchema": schema({})}
                CALLS["fresh_probe"] = lambda call, arguments: {"code": "new"}
                _listed = CALLS["task_list"]
                CALLS["task_list"] = lambda call, arguments: {
                    "code": "new", "tasks": _listed(call, arguments)
                }
                """
            )
        )
        registration = source / "concorde/coordination/registration.json"
        data = json.loads(registration.read_text())
        data["mcp_tools"].append(
            {
                "name": "fresh_probe",
                "entry": "tasks.tools:answer",
                "worktree": "primary",
                "long_work": False,
                "threaded": False,
                "requires": [],
            }
        )
        registration.write_text(json.dumps(data))
        changed, error = client.call("task_list")
        self.assertFalse(error, changed)
        self.assertEqual("new", changed["code"])
        self.assertEqual(["t1"], [record["id"] for record in changed["tasks"]])
        # The server noticed that the session's tools are no longer the current code's.
        self.assertEqual(
            "notifications/tools/list_changed", client.notices.get(timeout=10)
        )
        names = {tool["name"] for tool in client.request("tools/list")["tools"]}
        self.assertEqual(TOOLS | {"fresh_probe"}, names)
        probe, error = client.call("fresh_probe")
        self.assertEqual(({"code": "new"}, False), (probe, error))
        self.assertTrue(client.notices.empty())
        # A Concorde that gives no answer is refused, naming the command and what it said.
        launcher.write_text("#!/bin/sh\necho 'concorde is broken' >&2\nexit 3\n")
        value, error = client.call("task_list")
        link = self.refusal(value, error, "call_failed")
        self.assertIn("concorde is broken", link["detail"])
        self.assertIn("status 3", link["detail"])
        self.assertEqual("environment", link["unhandled"]["reason"])

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
        # Without `by`, the level is the calling session's.
        worktree = self.project.worktree("t2")
        for session, level in (
            (client, "main-agent"),
            (
                self.client(cwd=worktree, CLAUDE_PROJECT_DIR=str(worktree)),
                "task-session",
            ),
        ):
            derived, error = session.call(
                "task_escalate",
                task="t2",
                code="need_choice",
                detail="Which retry limit?",
                reason="decision",
                explanation="the limit is a promise of the Module",
            )
            self.assertFalse(error, derived)
            self.assertEqual(level, derived["escalated"]["level"])
        rebound, error = client.call("task_rebind", task="t2", main="concorde-8e")
        self.assertFalse(error, rebound)
        self.assertEqual(
            ("concorde-8e", None), (rebound["record"]["main"], rebound["former"])
        )
        listed, _ = client.call("task_list", main="concorde-8e")
        self.assertEqual(["t2"], [record["id"] for record in listed])
        listed, _ = client.call(
            "task_list", main="concorde-8e", state=["closed", "failed"]
        )
        self.assertEqual([], listed)
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

    @verifies("scenario.main-session.project-mcp-issues")
    def test_issue_tools_manage_the_projects_issues_from_any_worktree(self):
        from tests.concorde.support.issue_reports import report

        self.project.open_task("t1")
        worktree = self.project.worktree("t1")
        # A task session: its reports are the task session's, with its task.
        session = self.client(cwd=worktree, CLAUDE_PROJECT_DIR=str(worktree))
        filed = report(owner_target_id="module.a", evidence=[])
        checked, error = session.call("issue_report", report=filed, check=True)
        self.assertFalse(error, checked)
        self.assertEqual(
            (True, "module.a"), (checked["valid"], checked["reporting_module"])
        )
        recorded, error = session.call("issue_report", report=filed)
        self.assertFalse(error, recorded)
        issue = recorded["receipt"]["issue_id"]
        shown, error = session.call("issue_show", issue=issue)
        self.assertFalse(error, shown)
        source = shown["issue"]["reports"][0]["source"]
        self.assertEqual(("task-session", "t1"), (source["agent"], source["change_id"]))
        self.assertTrue((self.root / recorded["receipt"]["path"]).is_file())
        self.assertFalse((worktree / recorded["receipt"]["path"]).exists())
        # The main agent in the primary worktree sees it at once and disposes it.
        main = self.client()
        listed, error = main.call("issue_list")
        self.assertEqual(
            [(issue, "decision-needed", "high")],
            [(row["id"], row["tier"], row["severity"]) for row in listed["issues"]],
        )
        # Filters keep only the Issues they name.
        for filters, expected in (
            ({"status": "open", "module": "module.a"}, [issue]),
            ({"tier": ["suggestion", "decision-needed"]}, [issue]),
            ({"status": "closed"}, []),
            ({"module": "module.b"}, []),
            ({"tier": ["suggestion"]}, []),
            ({"severity": ["high"], "sort": "severity"}, [issue]),
            ({"severity": ["critical", "low"]}, []),
        ):
            listed, error = main.call("issue_list", **filters)
            self.assertFalse(error, listed)
            self.assertEqual(expected, [row["id"] for row in listed["issues"]])
        for filters in (
            {"tier": ["urgent"]},
            {"severity": ["urgent"]},
            {"sort": "tier"},
        ):
            value, error = main.call("issue_list", **filters)
            self.refusal(value, error, "invalid_input")
        checked, error = main.call("issue_check")
        self.assertEqual({"errors": [], "notes": []}, checked)
        resolved, error = main.call("task_resolve", task="t1", issues=[issue])
        self.assertFalse(error, resolved)
        self.assertEqual([issue], resolved["resolves"])
        closed, error = main.call(
            "issue_close",
            issue=issue,
            reason="not-actionable",
            note="n",
            evidence=["e"],
        )
        self.assertEqual("closed", closed["status"], closed)
        self.assertEqual(
            "main-agent",
            main.call("issue_show", issue=issue)[0]["issue"]["dispositions"][0][
                "actor"
            ],
        )
        value, error = main.call(
            "issue_close", issue=issue, reason="resolved", note="n", evidence=["e"]
        )
        link = self.refusal(value, error, "closed_issue")
        self.assertEqual("Issues (concorde issues)", link["actor"])
        reopened, error = session.call(
            "issue_reopen", issue=issue, note="n", evidence=["e"]
        )
        self.assertEqual("open", reopened["status"], reopened)
        # A write never waits for the merge lock.
        merging = holding(store.merge_lock_path(self.root), "session-other", "t9")
        self.addCleanup(merging.wait)
        self.addCleanup(merging.stdin.close)
        started = time.monotonic()
        value, error = main.call(
            "issue_report",
            report=report(report_key="later", owner_target_id="module.a", evidence=[]),
        )
        self.assertLess(time.monotonic() - started, 10)
        link = self.refusal(value, error, "merge_busy")
        self.assertIn("a test holder", link["detail"])
        self.assertEqual("environment", link["unhandled"]["reason"])
        self.assertTrue(any("never report" in option for option in link["options"]))

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
        attempt_lock = store.attempt_lock_path(self.root, "t1")
        for path in (merge_lock, self.workspace_lock(), attempt_lock):
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
        # The output stays with the attempt's node, which the close moved to the history.
        ended = wait.wait_merge(self.root, "t1", 60)
        self.assertFalse(attempt_lock.exists())
        attempt = ended["attempt"]
        self.assertEqual(
            Path(value["started"]["attempt"]).relative_to(
                store.task_folder(self.root, "t1")
            ),
            Path(attempt["node"]).relative_to(store.history_folder(self.root, "t1")),
        )
        output = json.loads(Path(attempt["output"]).read_text())
        self.assertEqual("merged", output["record"]["closed"]["outcome"])
        self.assertEqual(output["merge"]["log"], attempt["node"])
        self.assertEqual(("ok", "merged"), (attempt["status"], attempt["outcome"]))
        self.assertTrue(Path(attempt["messages"]).is_file())

    @verifies("scenario.main-session.project-mcp-merge-fallback")
    def test_without_a_channel_the_merge_end_is_awaited_and_kept(self):
        self.project.open_task("t1")
        client = self.client(channel=False)
        # Not delivered: the merge is refused, and that refusal is its kept output too.
        value, error = client.call("task_merge", task="t1", checks=[PASSING])
        self.assertFalse(error, value)
        self.assertEqual(
            "concorde task wait t1 --merge", value["wake"]["command"], value["wake"]
        )
        self.assertEqual(
            store.task_folder(self.root, "t1") / "merges" / "1",
            Path(value["started"]["attempt"]),
        )
        ended = wait.wait_merge(self.root, "t1", 60)
        attempt = ended["attempt"]
        self.assertEqual((1, "failed"), (attempt["number"], attempt["status"]))
        refused = json.loads(Path(attempt["output"]).read_text())
        self.assertIn("error", refused)
        node = trace.read(Path(attempt["node"]))
        self.assertEqual(refused["error"]["code"], node["error"]["code"])
        deliver(self.project.worktree("t1"))
        value, error = client.call("task_merge", task="t1", checks=[PASSING])
        self.assertFalse(error, value)
        ended = wait.wait_merge(self.root, "t1", 60)
        attempt = ended["attempt"]
        self.assertEqual((2, "ok"), (attempt["number"], attempt["status"]))
        self.assertIn(
            store.history_folder(self.root, "t1"), Path(attempt["output"]).parents
        )
        output = json.loads(Path(attempt["output"]).read_text())
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
        store_ = store.concorde(self.root)
        with workspace_lock(store_, "t1", "a delivery run"):
            deliver(self.project.worktree("t1"))
        event = client.event()
        self.assertEqual("wait_done", event["meta"]["event"])
        self.assertIn('"delivered"', event["content"])
        # Already reached: answered at once, nothing registered.
        now, error = client.call("register_wait", task="t1", until=["delivered"])
        self.assertEqual(
            {
                "registered": False,
                "already": {"task": "t1", "state": "delivered", "waited_seconds": 0.0},
            },
            now,
        )
        # A free lock answers what `concorde task wait --lock` prints, field for field.
        free, error = client.call("register_wait", lock="merge")
        self.assertFalse(error, free)
        printed = wait.wait_lock(self.root, "merge")
        self.assertEqual(set(printed), set(free["already"]))
        self.assertEqual(
            {
                "lock": "merge",
                "task": None,
                "released": True,
                "held_by": None,
                "waited_seconds": 0.0,
            },
            free["already"],
        )
        # A wait still watched ends with its server, however the server ends.
        holder = holding(self.workspace_lock(), "session-other", "t1")
        self.addCleanup(holder.wait)
        self.addCleanup(holder.stdin.close)
        registered, error = client.call("register_wait", lock="workspace", task="t1")
        self.assertTrue(registered["registered"], registered)
        waiting = children(client.process.pid)
        self.assertEqual(1, len(waiting), waiting)
        command = Path(f"/proc/{waiting[0]}/cmdline")
        deadline = time.monotonic() + 20
        while (
            b"-c" in command.read_bytes().split(b"\0") and time.monotonic() < deadline
        ):
            time.sleep(0.05)
        self.assertIn(b"task\0wait\0t1\0--lock\0workspace", command.read_bytes())
        client.process.send_signal(signal.SIGKILL)
        client.process.wait(10)
        deadline = time.monotonic() + 20
        while alive(waiting[0]) and time.monotonic() < deadline:
            time.sleep(0.05)
        self.assertFalse(alive(waiting[0]), "the wait outlived its server")

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
        refused, error = client.call("register_wait", task="t1", until=["merging"])
        self.assertTrue(error, refused)
        self.assertEqual("invalid_input", refused["error"]["code"])
        self.assertIn("cannot wait for merging", refused["error"]["detail"])
        store.rebind(self.root, "t1", "concorde-7d")
        answer, _ = client.call("register_wait", task="t1", rebound="concorde-7d")
        self.assertEqual(
            "concorde task wait t1 --rebound concorde-7d", answer["command"]
        )
        answer, _ = client.call("register_wait", task="t1", rebound="concorde-6c")
        self.assertEqual(
            {
                "task": "t1",
                "main": "concorde-7d",
                "former": "concorde-6c",
                "waited_seconds": 0.0,
            },
            answer["already"],
        )


class WorkflowStepToolTests(unittest.TestCase):
    """``workflow_step`` on a bound task worktree whose ``task-validation`` runs a slow check."""

    SECONDS = 4

    def setUp(self):
        self.project = BrownfieldProject(self)
        checks = self.project.root / ".concorde/checks/module.shop.json"
        checks.parent.mkdir(parents=True, exist_ok=True)
        checks.write_text(
            json.dumps(
                {
                    "checks": [
                        {
                            "id": "check.shop.slow",
                            "argv": ["sleep", str(self.SECONDS)],
                            "timeout_seconds": 120,
                            "inputs": ["src"],
                        }
                    ]
                }
            )
        )
        commit_all(self.project.root, "a slow check")
        self.project.open_task()
        self.worktree = self.project.worktree()

    def client(self, where: Path) -> Client:
        return Client(
            self,
            where,
            CONCORDE_CHANNEL="0",
            CLAUDE_CODE_SESSION_ID="session-task",
            CLAUDE_PROJECT_DIR=str(where),
        )

    REQUEST: ClassVar[dict] = {
        "workflow": "brownfield",
        "mode": "no-ask",
        "key": "validate",
        "argv": ["task-validation"],
    }

    @verifies("scenario.main-session.workflow-step-tool")
    @verifies("scenario.workflows.step-outlives-call")
    def test_a_step_started_through_the_server_outlives_the_call_and_the_session(self):
        client = self.client(self.worktree)
        # Another call is answered while a step call waits: step calls have threads of their own.
        client.send(
            {
                "jsonrpc": "2.0",
                "id": 900,
                "method": "tools/call",
                "params": {
                    "name": "workflow_step",
                    "arguments": {"request": self.REQUEST, "wait": 2},
                },
            }
        )
        listed, error = client.call("task_list")
        self.assertFalse(error, listed)
        with client.arrived:
            self.assertTrue(
                client.arrived.wait_for(lambda: 900 in client.responses, timeout=60)
            )
        answer = client.responses.pop(900)["result"]
        outcome = json.loads(answer["content"][0]["text"])
        self.assertFalse(answer["isError"], outcome)
        self.assertEqual(("validate", "running"), (outcome["key"], outcome["state"]))
        run_id = outcome["run_id"]
        # The session ends: the server goes, the run it started does not.
        client.close()
        space = workflow_store.workspace(self.worktree)
        deadline = time.monotonic() + 120
        while run_state(space.store, run_id) == "running":
            self.assertLess(time.monotonic(), deadline, "the run never ended")
            time.sleep(0.2)
        self.assertEqual("finished", run_state(space.store, run_id))
        self.assertIsNotNone(load_result(space.store, run_id))
        # A new session finds the same step finished: the key never starts a run twice.
        again, error = self.client(self.worktree).call(
            "workflow_step", request=self.REQUEST, wait=5
        )
        self.assertFalse(error, again)
        self.assertEqual((run_id, "finished"), (again["run_id"], again["state"]))

    @verifies("scenario.main-session.workflow-step-tool")
    def test_a_worktree_without_a_binding_or_a_bad_request_is_refused(self):
        value, error = self.client(self.project.root).call(
            "workflow_step", request=self.REQUEST
        )
        self.assertTrue(error, value)
        validate(value["error"], ERROR_SCHEMA)
        self.assertEqual("unbound_worktree", value["error"]["code"])
        value, error = self.client(self.worktree).call(
            "workflow_step", request={"workflow": "brownfield"}, wait=0
        )
        self.assertTrue(error, value)
        # The step command's own refusal, unchanged.
        self.assertEqual(
            ("invalid_request", "Workflows (concorde workflow)"),
            (value["error"]["code"], value["error"]["actor"]),
        )
        value, error = self.client(self.worktree).call(
            "workflow_step", request=self.REQUEST, wait=101
        )
        self.assertEqual("invalid_input", value["error"]["code"])


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
        self.assertTrue(
            channel_from(
                "concorde",
                [(["/opt/claude-code/bin/claude.exe", *flagged[1:]], True)],
            )
        )
        # A background session is never woken by channel events, flag or not.
        self.assertFalse(channel_from("concorde", [(flagged, False)]))
        # Another program with the same words on a terminal is no Claude Code session.
        self.assertFalse(channel_from("concorde", [(["node", *flagged[1:]], True)]))
        self.assertFalse(
            channel_from("concorde", [(["claudette", *flagged[1:]], True)])
        )
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
