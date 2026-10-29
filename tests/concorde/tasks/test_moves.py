"""Following the main agent's Claude Code session after a move to the background or a rename.

Claude Code's own records are written here as a move leaves them, observed with Claude Code
2.1.312: the moved session's transcript ends with ``{"type": "continued-in",
"continuedInSessionId": <new id>}``, and ``claude agents --json`` lists the sessions that run by
``sessionId`` and ``name``. A fake ``claude`` prints the list a test writes; no test runs the
developer's own.
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import re
import sys
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from concorde.coordination.tasks import cli, moves, store, wait
from concorde.spec.verification import verifies
from tests.concorde.support.operation_project import OperationProject

# Claude Code's commands as the tests need them: ``agents --json`` prints the list in the file
# ``FAKE_AGENTS`` names, or exits with the status a line ``exit <n>`` there gives.
AGENTS_CLAUDE = """\
import os, sys
if sys.argv[1:3] == ["agents", "--json"]:
    path = os.environ.get("FAKE_AGENTS", "")
    text = open(path).read() if path and os.path.exists(path) else "[]"
    if text.startswith("exit "):
        sys.exit(int(text.split()[1]))
    sys.stdout.write(text)
    sys.exit(0)
print(f"No job matching '{sys.argv[-1]}'. Run 'claude agents' to list running sessions.")
sys.exit(1)
"""


def line(record: dict) -> str:
    return json.dumps(record) + "\n"


def conversation(session_id: str) -> str:
    """The lines of a transcript whose session talked: a prompt and an answer."""
    return line(
        {"type": "user", "sessionId": session_id, "message": {"content": "hello"}}
    ) + line(
        {
            "type": "assistant",
            "sessionId": session_id,
            "message": {"stop_reason": "end_turn", "content": []},
        }
    )


def moved(session_id: str, to: str) -> str:
    """The lines Claude Code appends to a transcript when its session moves to the background."""
    return (
        line({"type": "attachment", "attachment": {"type": "session_cron_carry"}})
        + line({"type": "cost-state", "sessionId": session_id})
        + line(
            {
                "type": "continued-in",
                "sessionId": session_id,
                "continuedInSessionId": to,
            }
        )
    )


class MoveTests(unittest.TestCase):
    def setUp(self):
        self.project = OperationProject(self)
        self.root = self.project.root
        self.primary = store.primary_of(self.root)
        scratch = self.project.home / "claude-fake"
        (scratch / "bin").mkdir(parents=True)
        self.config = scratch / "config"
        self.agents = scratch / "agents.json"
        program = scratch / "bin/claude"
        program.write_text(f"#!{sys.executable}\n{AGENTS_CLAUDE}")
        program.chmod(0o755)
        environ = patch.dict(
            os.environ,
            {
                "PATH": f"{scratch / 'bin'}{os.pathsep}{os.environ['PATH']}",
                "CLAUDE_CONFIG_DIR": str(self.config),
                "FAKE_AGENTS": str(self.agents),
            },
        )
        environ.start()
        self.addCleanup(environ.stop)
        # Claude Code's project folder of the primary worktree, where its sessions' transcripts lie.
        self.folder = (
            self.config / "projects" / re.sub(r"[^A-Za-z0-9]", "-", str(self.primary))
        )
        self.folder.mkdir(parents=True)

    def transcript(self, session_id: str, text: str, mode: str = "w") -> Path:
        path = self.folder / f"{session_id}.jsonl"
        with path.open(mode, encoding="utf-8") as stream:
            stream.write(text)
        return path

    def listing(self, sessions: dict[str, str]) -> None:
        """What ``claude agents --json`` lists: each session id with its name."""
        self.agents.write_text(
            json.dumps(
                [
                    {"pid": 1, "kind": "interactive", "sessionId": key, "name": name}
                    for key, name in sessions.items()
                ]
            )
        )

    def started(self, task_id: str, main: str, main_session: str | None) -> None:
        """Record a task session of ``task_id`` started for ``main``, whose session id the
        record keeps as ``main_session``."""
        store.record_session(
            self.root,
            task_id,
            {
                "id": f"s-{task_id}",
                "reported_id": f"s-{task_id}",
                "name": f"task-{task_id}",
                "main": main,
                "model": None,
                "started_at": store.now(),
            },
            main_session=main_session,
        )

    def command(self, *argv, cwd=None):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = cli.main(list(argv), cwd=cwd or self.root)
        return status, json.loads(output.getvalue())

    def main_hook(self, data: dict) -> str:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(0, cli.main_hook(self.root, io.StringIO(json.dumps(data))))
        return output.getvalue()

    @verifies("scenario.tasks.main-hook-move")
    def test_the_main_hook_marks_the_tasks_of_the_session_it_moved_from(self):
        self.project.open_task("t1")
        self.started("t1", "concorde-74", "sess-a")
        self.project.open_task("t2")
        self.started("t2", "concorde-8e", "sess-b")
        self.transcript("sess-a", conversation("sess-a") + moved("sess-a", "sess-m"))
        self.transcript("sess-m", conversation("sess-m") + moved("sess-m", "sess-n"))
        self.transcript("sess-n", conversation("sess-n"))
        self.transcript("sess-b", conversation("sess-b"))
        hook = {
            "source": "fork",
            "cwd": str(self.root),
            "session_id": "sess-n",
            "transcript_path": str(self.folder / "sess-n.jsonl"),
        }
        text = self.main_hook(hook)
        self.assertRegex(
            text.splitlines()[0],
            r"^Concorde \(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ, session sess-n\): this session "
            r"started as a fork, such as a move to the background\.",
        )
        self.assertIn(
            "- `t1`: main `concorde-74` (this session, moved from sess-a).", text
        )
        self.assertIn("- `t2`: main `concorde-8e`.", text)
        # The session in the middle moved on; the newest session owns the task.
        text = self.main_hook({**hook, "session_id": "sess-m"})
        self.assertIn("- `t1`: main `concorde-74`.", text)
        # A session resumed after its move went on itself, so it continues nowhere.
        self.transcript("sess-a", conversation("sess-a"), mode="a")
        self.assertIn("- `t1`: main `concorde-74`.", self.main_hook(hook))
        # Missing or unreadable transcripts move nothing, and both tasks are still listed.
        self.transcript("sess-a", conversation("sess-a") + moved("sess-a", "sess-m"))
        self.transcript("sess-m", "{not json\n")
        self.assertIn("- `t1`: main `concorde-74`.", self.main_hook(hook))
        for name in ("sess-a", "sess-m"):
            (self.folder / f"{name}.jsonl").unlink()
        text = self.main_hook(hook)
        self.assertIn("- `t1`: main `concorde-74`.", text)
        self.assertIn("- `t2`: main `concorde-8e`.", text)
        # Without a transcript path the hook marks only by the session id, as before.
        text = self.main_hook({**hook, "transcript_path": None, "session_id": "sess-a"})
        self.assertIn("- `t1`: main `concorde-74` (this session).", text)

    @verifies("scenario.tasks.report-follows-move")
    def test_a_report_goes_to_the_session_the_main_session_moved_to(self):
        self.project.open_task("t1")
        self.started("t1", "concorde-74", "sess-a")
        self.transcript("sess-a", conversation("sess-a") + moved("sess-a", "sess-n"))
        self.listing({"sess-n": "项目中途停止状态检查", "sess-x": "concorde-74"})
        worktree = self.project.worktree("t1")
        status, value = self.command(
            "report", "t1", "--text", "delivered", cwd=worktree
        )
        self.assertEqual(0, status, value)
        self.assertEqual(
            ("项目中途停止状态检查", "concorde-74", ["sess-a", "sess-n"]),
            (value["main"], value["recorded_main"], value["followed"]),
        )
        log = Path(value["decision_log"]).read_text()
        self.assertIn("## Report 1 to the main agent (项目中途停止状态检查), ", log)
        self.assertIn(
            "The main agent's session the record names, `concorde-74` (`sess-a`), continues "
            "as `项目中途停止状态检查` (`sess-n`), so the report goes there.",
            log,
        )
        record = store.load_task(self.root, "t1")
        self.assertEqual("concorde-74", record["main"])
        self.assertEqual("concorde-74", record["reports"][0]["main"])
        # A rename keeps the session id: the list names it anew.
        (self.folder / "sess-a.jsonl").unlink()
        self.listing({"sess-a": "concorde-9f"})
        _, value = self.command("report", "t1", "--text", "again", cwd=worktree)
        self.assertEqual(
            ("concorde-9f", ["sess-a"]), (value["main"], value["followed"])
        )
        # Nothing to follow: the record's main, as before.
        for listing in ("exit 3", "not json", "[]"):
            self.agents.write_text(listing)
            _, value = self.command("report", "t1", "--text", "x", cwd=worktree)
            self.assertEqual("concorde-74", value["main"], listing)
            self.assertNotIn("recorded_main", value)
        self.listing({"sess-a": "concorde-74"})
        _, value = self.command("report", "t1", "--text", "x", cwd=worktree)
        self.assertEqual("concorde-74", value["main"])
        self.assertNotIn("followed", value)
        with patch.dict(os.environ, {"PATH": "/nonexistent"}):
            self.assertIsNone(moves.listed())

    @verifies("scenario.tasks.wait-rebound-follows")
    def test_a_rebind_wait_returns_the_session_the_main_session_moved_to(self):
        self.project.open_task("t1")
        self.started("t1", "concorde-74", "sess-a")
        self.transcript("sess-a", conversation("sess-a"))
        self.listing({})

        def move():
            self.listing({"sess-n": "项目中途停止状态检查"})
            self.transcript("sess-n", conversation("sess-n"))
            self.transcript("sess-a", moved("sess-a", "sess-n"), mode="a")

        timer = threading.Timer(0.5, move)
        timer.start()
        self.addCleanup(timer.cancel)
        started = time.monotonic()
        status, value = self.command(
            "wait", "t1", "--rebound", "concorde-74", "--timeout", "30"
        )
        timer.join()
        self.assertEqual(0, status, value)
        self.assertEqual(
            ("项目中途停止状态检查", "concorde-74", ["sess-a", "sess-n"]),
            (value["main"], value["former"], value["followed"]),
        )
        self.assertLess(time.monotonic() - started, 20)
        self.assertEqual("concorde-74", store.load_task(self.root, "t1")["main"])
        # Already followed: it answers at once.
        status, value = self.command("wait", "t1", "--rebound", "concorde-74")
        self.assertEqual((0, 0.0), (status, value["waited_seconds"]))

    @verifies("scenario.tasks.wait-rebound")
    def test_a_rebind_wait_without_a_timeout_is_bounded(self):
        self.project.open_task("t1")
        self.started("t1", "concorde-74", "sess-a")
        self.assertEqual(1800, wait.REBOUND_TIMEOUT)
        with patch.object(wait, "REBOUND_TIMEOUT", 0.3):
            status, value = self.command("wait", "t1", "--rebound", "concorde-74")
        self.assertEqual(1, status, value)
        self.assertEqual("wait_timeout", value["error"]["code"])
        self.assertIn("0.3 s", value["error"]["detail"])


if __name__ == "__main__":
    unittest.main()
