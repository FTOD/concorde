"""How the project MCP server routes a call, tells its session of changed tools and reads its
channel, with the call's processes stood in for."""

from __future__ import annotations

import io
import json
import subprocess
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from concorde.distribution.project_mcp import server as server_module
from concorde.distribution.project_mcp import tools
from concorde.distribution.project_mcp.calls import Calls, Rethread
from concorde.spec.verification import verifies

PLAIN = {"worktree": "primary", "long_work": False, "threaded": False}


class StoodIn(Calls):
    """``Calls`` whose listing and call processes are stood in for: ``listings`` are what
    ``concorde project-mcp --tools`` prints, one per fetch, and ``replies`` what each call's
    process answers; ``ran`` records how each call was routed."""

    def __init__(self, primary: Path, where: Path, listings: list, replies: list):
        self.notices: list[str] = []
        super().__init__(
            primary,
            where,
            "session-main",
            False,
            lambda content, meta: None,
            lambda: self.notices.append("tools changed"),
        )
        self.listings = listings
        self.replies = replies
        self.ran: list[tuple[str, Path, dict]] = []

    def describe(self):
        return self.listings.pop(0)

    def run(self, name, envelope, limit, worktree):
        self.ran.append(("run", worktree, envelope["served"]))
        return self.replies.pop(0)

    def long_work(self, name, envelope, worktree):
        self.ran.append(("long_work", worktree, envelope["served"]))
        return self.replies.pop(0)


def listing(digest: str, **serving) -> dict:
    return {
        "tools": [{"name": name} for name in serving],
        "digest": digest,
        "serving": serving,
        "instructions": "",
    }


class RoutingTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.primary = Path(directory.name) / "primary"
        self.primary.mkdir()
        subprocess.run(["git", "init", "-q", str(self.primary)], check=True)
        self.worktree = Path(directory.name) / "task"
        subprocess.run(
            [
                "git",
                "-C",
                str(self.primary),
                "commit",
                "-q",
                "--allow-empty",
                "-m",
                "a",
            ],
            check=True,
            env={
                "GIT_AUTHOR_NAME": "t",
                "GIT_AUTHOR_EMAIL": "t@t",
                "GIT_COMMITTER_NAME": "t",
                "GIT_COMMITTER_EMAIL": "t@t",
            },
        )
        subprocess.run(
            [
                "git",
                "-C",
                str(self.primary),
                "worktree",
                "add",
                "-q",
                str(self.worktree),
            ],
            check=True,
        )
        self.worktree = self.worktree.resolve()

    @verifies("scenario.distribution.mcp-reroute")
    def test_a_call_is_routed_again_as_the_current_code_serves_its_tool(self):
        session = {**PLAIN, "worktree": "session"}
        calls = StoodIn(
            self.primary,
            self.worktree,
            [listing("sha256:a", probe=PLAIN)],
            [
                {"reroute": {"probe": session}, "tools": "sha256:a"},
                {"value": {"answered": True}, "tools": "sha256:a"},
            ],
        )
        calls.tools()
        self.assertEqual({"answered": True}, calls.call("probe", {}))
        self.assertEqual(
            [("run", self.primary, PLAIN), ("run", self.worktree, session)], calls.ran
        )
        # Long work started in the session's worktree, as its registration now says.
        long_work = {**session, "long_work": True}
        calls.replies = [
            {"reroute": {"probe": long_work}, "tools": "sha256:a"},
            {"value": {"started": True}, "tools": "sha256:a"},
        ]
        calls.ran = []
        self.assertEqual({"started": True}, calls.call("probe", {}))
        self.assertEqual(
            [("run", self.worktree, session), ("long_work", self.worktree, long_work)],
            calls.ran,
        )
        # A call on the session's thread that now belongs on a thread of its own goes there.
        threaded = {**PLAIN, "threaded": True}
        calls.replies = [{"reroute": {"probe": threaded}, "tools": "sha256:a"}]
        with self.assertRaises(Rethread):
            calls.call("probe", {}, threaded=False)
        self.assertEqual(threaded, calls.served("probe"))
        # Routed otherwise twice: the server cannot tell how the tool is served.
        calls.replies = [
            {"reroute": {"probe": PLAIN}, "tools": "sha256:a"},
            {"reroute": {"probe": threaded}, "tools": "sha256:a"},
        ]
        with self.assertRaises(tools.Refusal) as refused:
            calls.call("probe", {})
        self.assertEqual("call_failed", refused.exception.link["code"])
        self.assertEqual([], calls.notices)

    @verifies("scenario.distribution.mcp-reroute")
    def test_the_calls_process_refuses_a_routing_its_registration_does_not_name(self):
        envelope = {
            "arguments": {},
            "primary": str(self.primary),
            "where": str(self.primary),
            "served": {**PLAIN, "worktree": "session"},
        }
        reply, handover = tools.answer("task_list", envelope)
        self.assertIsNone(handover)
        self.assertEqual(PLAIN, reply["reroute"]["task_list"])
        self.assertNotIn("value", reply)
        self.assertNotIn("error", reply)
        self.assertEqual(
            {"value", "tools"},
            set(tools.answer("locks", {**envelope, "served": PLAIN})[0])
            - {"watch", "handover"},
        )

    @verifies("scenario.distribution.mcp-tools-changed-after-refresh")
    def test_learning_how_a_tool_is_served_lists_nothing_to_the_session(self):
        calls = StoodIn(
            self.primary,
            self.primary,
            [
                listing("sha256:old", task_list=PLAIN),
                listing("sha256:new", task_list=PLAIN, late=PLAIN),
            ],
            [{"value": {}, "tools": "sha256:new"}],
        )
        calls.tools()
        # The session calls a tool its listing lacks: the server learns how it is served.
        calls.call("late", {})
        self.assertEqual(["tools changed"], calls.notices)
        self.assertEqual("sha256:new", calls.listed)


class ChannelOverrideTests(unittest.TestCase):
    @verifies("scenario.distribution.mcp-channel-override")
    def test_the_environment_decides_before_the_command_lines(self):
        flagged = [
            "claude",
            "--dangerously-load-development-channels",
            "server:concorde",
        ]
        with patch.object(server_module, "_ancestors", return_value=[(flagged, True)]):
            self.assertTrue(server_module.detect_channel("concorde", {}))
            self.assertFalse(
                server_module.detect_channel("concorde", {"CONCORDE_CHANNEL": "0"})
            )
        with patch.object(server_module, "_ancestors", return_value=[]):
            self.assertFalse(server_module.detect_channel("concorde", {}))
            self.assertTrue(
                server_module.detect_channel("concorde", {"CONCORDE_CHANNEL": "1"})
            )


class ServerRethreadTests(unittest.TestCase):
    @verifies("scenario.distribution.mcp-reroute")
    def test_a_call_the_current_code_threads_is_answered_on_its_own_thread(self):
        class Fake:
            def served(self, name):
                return PLAIN

            def call(self, name, arguments, threaded=True):
                if not threaded:
                    raise Rethread(name)
                return {"answered": name, "thread": threading.current_thread().name}

        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        writer = io.StringIO()
        session = server_module.Session(
            io.StringIO(), writer, environment={}, cwd=Path(directory.name)
        )
        session.calls = Fake()
        session.handle(
            {
                "jsonrpc": "2.0",
                "id": 7,
                "method": "tools/call",
                "params": {"name": "probe", "arguments": {}},
            }
        )
        for thread in threading.enumerate():
            if thread.name == "call 7":
                thread.join(10)
        answer = json.loads(writer.getvalue())
        self.assertEqual(7, answer["id"])
        self.assertEqual(
            {"answered": "probe", "thread": "call 7"},
            json.loads(answer["result"]["content"][0]["text"]),
        )


if __name__ == "__main__":
    unittest.main()
