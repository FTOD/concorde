"""How the project MCP server routes a call, tells its session of changed tools and reads its
channel, with the call's processes stood in for."""

from __future__ import annotations

import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from concorde.distribution.project_mcp import server as server_module
from concorde.distribution.project_mcp import tools
from concorde.distribution.project_mcp.calls import Calls, Rethread, last_answer
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


class Scripted(Calls):
    """``Calls`` whose call processes run ``script`` with this Python instead of ``concorde``."""

    def __init__(self, primary: Path, script: str):
        super().__init__(primary, primary, None, False, None, None)
        self.script = script

    def command(self, *words, worktree=None):
        return [sys.executable, "-c", self.script], dict(os.environ)


class FailedCallTests(unittest.TestCase):
    """A call that gives no answer is refused with what its process printed on both streams."""

    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.primary = Path(directory.name)

    def detail(self, calls: Calls, work) -> str:
        with self.assertRaises(tools.Refusal) as refused:
            work()
        self.assertEqual("call_failed", refused.exception.link["code"])
        return refused.exception.link["detail"]

    @verifies("scenario.distribution.mcp-call-failed")
    def test_a_failed_call_keeps_both_streams(self):
        printing = (
            "import sys, time\n"
            "print('said on stdout', flush=True)\n"
            "print('said on stderr', file=sys.stderr, flush=True)\n"
        )
        cases = {
            "exited": (printing + "sys.exit(3)\n", 30, "exited with status 3"),
            "timed out": (printing + "time.sleep(30)\n", 2, "within 2 seconds"),
        }
        for case, (script, limit, ended) in cases.items():
            with self.subTest(case=case):
                calls = Scripted(self.primary, script)
                detail = self.detail(
                    calls, lambda: calls.run("probe", {}, limit, self.primary)
                )
                self.assertIn(ended, detail)
                self.assertIn("on standard error: said on stderr", detail)
                self.assertIn("on standard output: said on stdout", detail)
        calls = Scripted(self.primary, printing + "sys.exit(4)\n")
        self.addCleanup(lambda: shutil.rmtree(calls.runtime(), ignore_errors=True))
        detail = self.detail(calls, lambda: calls.long_work("probe", {}, self.primary))
        self.assertIn("exited with status 4", detail)
        self.assertIn("on standard error: said on stderr", detail)
        self.assertIn("on standard output: said on stdout", detail)


class AnswerTests(unittest.TestCase):
    def test_the_last_answer_is_found_past_trailing_output(self):
        answer = json.dumps({"value": {"done": True}})
        for after in ("a diagnostic", '{"progress": 3}', "[1, 2]", "a\n{}\n"):
            with self.subTest(after=after):
                self.assertEqual(
                    {"value": {"done": True}}, last_answer(f"{answer}\n{after}\n")
                )
        self.assertIsNone(last_answer('a diagnostic\n{"progress": 3}\n'))
        # The last answer wins over an earlier one.
        self.assertEqual(
            {"error": {"code": "x"}},
            last_answer(f'{answer}\n{{"error": {{"code": "x"}}}}\nend\n'),
        )

    def test_a_wait_answering_null_is_done(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        events = []
        ended = threading.Event()
        cases = {
            "null": ("print('null')", "wait_done"),
            "no JSON": ("print('not json')", "wait_failed"),
            "null, failing": ("import sys; print('null'); sys.exit(1)", "wait_failed"),
        }
        for case, (script, event) in cases.items():
            with self.subTest(case=case):
                calls = Scripted(Path(directory.name), script)

                def notify(content, meta):
                    events.append(meta["event"])
                    ended.set()

                calls.notify = notify
                ended.clear()
                events.clear()
                calls.start_wait(
                    "register_wait", {}, {"description": "x", "words": [], "meta": {}}
                )
                self.assertTrue(ended.wait(30))
                self.assertEqual([event], events)


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
        # On its own thread now, the call has used its reroute: asked again, it is refused.
        calls.replies = [{"reroute": {"probe": PLAIN}, "tools": "sha256:a"}]
        calls.ran = []
        with self.assertRaises(tools.Refusal) as refused:
            calls.call("probe", {}, threaded=True, rerouted=threaded)
        self.assertEqual("call_failed", refused.exception.link["code"])
        self.assertEqual([("run", self.primary, threaded)], calls.ran)
        # A call on a thread of its own that now belongs on the session's thread goes back.
        calls.serving = {"probe": threaded}
        calls.replies = [{"reroute": {"probe": PLAIN}, "tools": "sha256:a"}]
        with self.assertRaises(Rethread) as moved:
            calls.call("probe", {}, threaded=True)
        self.assertEqual(PLAIN, moved.exception.served)
        calls.replies = [{"value": {"answered": True}, "tools": "sha256:a"}]
        self.assertEqual(
            {"answered": True},
            calls.call("probe", {}, threaded=False, rerouted=moved.exception.served),
        )
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
            "protocol": tools.PROTOCOL,
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
        self.assertEqual("sha256:old", calls.listed)

    @verifies("scenario.distribution.mcp-tools-changed-after-failed-listing")
    def test_a_failed_listing_is_followed_by_a_tools_change(self):
        calls = StoodIn(
            self.primary,
            self.primary,
            [None, listing("sha256:new", task_list=PLAIN)],
            [{"value": {}, "tools": "sha256:new"}],
        )
        # The listing fails: the session is given no tools.
        self.assertEqual([], calls.tools())
        calls.call("task_list", {})
        self.assertEqual(["tools changed"], calls.notices)
        self.assertEqual(tools.digest([]), calls.listed)

    @verifies("scenario.distribution.mcp-tools-changed-once")
    def test_telling_the_session_of_a_change_lists_nothing_to_it(self):
        calls = StoodIn(
            self.primary,
            self.primary,
            [
                listing("sha256:old", task_list=PLAIN),
                listing("sha256:new", task_list=PLAIN),
            ],
            [
                {"value": {}, "tools": "sha256:new"},
                {"value": {}, "tools": "sha256:new"},
                {"value": {}, "tools": "sha256:newer"},
                {"value": {}, "tools": "sha256:old"},
                {"value": {}, "tools": "sha256:newer"},
            ],
        )
        calls.tools()
        calls.call("task_list", {})
        self.assertEqual(["tools changed"], calls.notices)
        # Told once of these tools; still not listed, so the baseline stays the old listing.
        calls.call("task_list", {})
        self.assertEqual("sha256:old", calls.listed)
        self.assertEqual(["tools changed"], calls.notices)
        # Other tools again: told again.
        calls.call("task_list", {})
        self.assertEqual(["tools changed"] * 2, calls.notices)
        # The tools it was listed: nothing to tell.
        calls.call("task_list", {})
        self.assertEqual(["tools changed"] * 2, calls.notices)
        # Listing anew makes the listed tools the baseline.
        calls.tools()
        self.assertEqual("sha256:new", calls.listed)
        calls.call("task_list", {})
        self.assertEqual(["tools changed"] * 3, calls.notices)

    @verifies("scenario.distribution.mcp-host-outdated")
    def test_a_call_of_another_protocol_runs_nothing(self):
        envelope = {
            "arguments": {},
            "primary": str(self.primary),
            "where": str(self.primary),
            "served": PLAIN,
        }
        for protocol in (None, 1, tools.PROTOCOL + 1):
            with self.subTest(protocol=protocol):
                call = (
                    envelope if protocol is None else {**envelope, "protocol": protocol}
                )
                with patch.object(tools.parts, "load") as load:
                    reply, handover = tools.answer("task_list", call)
                load.assert_not_called()
                self.assertIsNone(handover)
                self.assertEqual({"error"}, set(reply))
                self.assertEqual("host_outdated", reply["error"]["code"])
                self.assertEqual("environment", reply["error"]["unhandled"]["reason"])
                self.assertTrue(
                    any("/mcp" in option for option in reply["error"]["options"])
                )


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

    @verifies("scenario.distribution.mcp-channel-forced")
    def test_the_environment_gives_a_channel_no_claude_asked_for(self):
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

            def call(self, name, arguments, threaded=True, rerouted=None):
                if not threaded:
                    raise Rethread(name, {**PLAIN, "threaded": True})
                return {
                    "answered": name,
                    "thread": threading.current_thread().name,
                    "rerouted": rerouted,
                }

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
            {
                "answered": "probe",
                "thread": "call 7",
                "rerouted": {**PLAIN, "threaded": True},
            },
            json.loads(answer["result"]["content"][0]["text"]),
        )

    @verifies("scenario.distribution.mcp-reroute-to-session-thread")
    def test_a_call_the_current_code_no_longer_threads_returns_to_the_sessions_thread(
        self,
    ):
        threaded = {**PLAIN, "threaded": True}
        order = []
        release = threading.Event()

        class Fake:
            def served(self, name):
                return threaded if name == "slow" else PLAIN

            def call(self, name, arguments, threaded=True, rerouted=None):
                thread = threading.current_thread().name
                if name == "slow" and threaded:
                    # Rerouted on its own thread: it belongs on the session's thread now.
                    release.wait(10)
                    raise Rethread(name, PLAIN)
                order.append((name, thread, rerouted))
                if name == "quick":
                    release.set()
                return {"answered": name}

            def close(self):
                pass

        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        reader_end, writer_end = os.pipe()
        reader = os.fdopen(reader_end, "r")
        sender = os.fdopen(writer_end, "w")
        output = io.StringIO()
        session = server_module.Session(
            reader, output, environment={}, cwd=Path(directory.name)
        )
        session.calls = Fake()
        ran = threading.Thread(target=session.run)
        ran.start()
        for identity, name in ((1, "slow"), (2, "quick")):
            sender.write(
                json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "id": identity,
                        "method": "tools/call",
                        "params": {"name": name, "arguments": {}},
                    }
                )
                + "\n"
            )
            sender.flush()
        deadline = threading.Event()
        for _ in range(100):
            if len(output.getvalue().splitlines()) == 2:
                break
            deadline.wait(0.1)
        sender.close()
        ran.join(10)
        main = ran.name
        # Both ran on the session's thread, the moved call after the call already there.
        self.assertEqual(
            [("quick", main, None), ("slow", main, PLAIN)],
            order,
        )
        self.assertEqual(
            {1, 2}, {json.loads(line)["id"] for line in output.getvalue().splitlines()}
        )


if __name__ == "__main__":
    unittest.main()
