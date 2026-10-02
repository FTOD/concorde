"""``concorde task session``: the boundary it writes and the session it starts and records, and
what the end of its task does to a Claude Code task session."""

from __future__ import annotations

import contextlib
import io
import json
import os
import shlex
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from concorde.spec.verification import verifies
from tests.concorde.support.ignored import TRACES
from concorde.coordination.tasks import cli, session, store
from concorde.kernel.tracing import node as trace
from tests.concorde.support.operation_project import OperationProject, commit
from tests.concorde.tasks.deliveries import deliver


SESSION_ID = "33afbc14-3ec3-4a74-b3d5-b2278eda5756"


class FakeClaude:
    """Stands in for ``claude --bg`` and ``claude agents --json --all``: records each call and
    answers like Claude Code, listing the sessions ``listed`` names."""

    def __init__(
        self,
        returncode=0,
        stdout="backgrounded · 33afbc14 · task-t1\n",
        listed=({"id": "33afbc14", "sessionId": SESSION_ID, "state": "working"},),
    ):
        self.returncode, self.stdout = returncode, stdout
        self.listed = list(listed)
        self.calls = []

    def __call__(self, command, **options):
        self.calls.append((command, options))
        if command[1] == "agents":
            return subprocess.CompletedProcess(command, 0, json.dumps(self.listed), "")
        return subprocess.CompletedProcess(command, self.returncode, self.stdout, "")


class TaskSessionTests(unittest.TestCase):
    def setUp(self):
        self.project = OperationProject(self)
        self.root = self.project.root
        self.project.open_task("t1", goal="Let reports carry a severity.")
        self.worktree = self.project.worktree("t1")
        self.folder = self.root / ".concorde/tasks/t1"

    def recorded(self, started: dict) -> None:
        """The task's trace holds ``started`` as its only session, a node of its own."""
        (found,) = store.sessions(self.root, "t1")
        fields = (
            "id",
            "reported_id",
            "session_id",
            "name",
            "main",
            "model",
            "started_at",
        )
        self.assertEqual(
            {key: started[key] for key in fields}, {key: found[key] for key in fields}
        )
        folder = self.folder / "sessions" / started["id"]
        self.assertEqual(str(folder), found["directory"])
        node = trace.read(folder)
        self.assertEqual(
            (started["id"], "session", "unknown"),
            (node["id"], node["kind"], node["status"]),
        )
        self.assertEqual(
            (started["name"], started["main"], started["session_id"]),
            tuple(
                node["content"]["data"][key] for key in ("name", "main", "session_id")
            ),
        )
        self.assertEqual((None, None), (node["ended_at"], node["usage"]["turns"]))
        # The record keeps no sessions.
        self.assertNotIn("sessions", store.load_task(self.root, "t1"))

    @verifies("scenario.task-session.start")
    def test_start_a_task_session(self):
        claude = FakeClaude()
        started = session.start(self.root, "t1", "concorde-7d", run=claude)
        directory = self.folder / "runtime"
        self.assertTrue((directory / "settings.json").is_file())
        self.assertTrue((directory / "write_hook.py").is_file())
        (command, options), (listing, _) = claude.calls
        self.assertEqual(self.worktree, Path(options["cwd"]))
        self.assertEqual(["claude", "--bg", "--name", "task-t1"], command[:4])
        self.assertIn("--settings", command)
        self.assertEqual(
            str(directory / "settings.json"), command[command.index("--settings") + 1]
        )
        mode = command[command.index("--permission-mode") + 1]
        self.assertEqual("auto", mode)
        self.assertNotIn("--allow-dangerously-skip-permissions", command)
        brief = command[-1]
        self.assertIn("You are a task session", brief)
        self.assertIn("Let reports carry a severity.", brief)
        self.assertIn("`concorde-7d`", brief)
        self.assertIn(str(self.worktree), brief)
        self.assertEqual(
            ("33afbc14", "task-t1", "concorde-7d"),
            (started["id"], started["name"], started["main"]),
        )
        # Claude Code's list of sessions gives the full session id, its transcript's name.
        self.assertEqual(["claude", "agents", "--json", "--all"], listing)
        self.assertEqual(SESSION_ID, started["session_id"])
        self.recorded(started)
        # The task record names the session's main, which the prompt gives as the one at start.
        self.assertEqual("concorde-7d", store.load_task(self.root, "t1")["main"])
        self.assertIn("Main agent session when this session started", brief)
        self.assertIn("`concorde task report` prints", brief)

    @verifies("scenario.task-session.start")
    def test_a_coloured_start_line_is_recognised(self):
        # Claude Code 2.1.283 colours the id and adds dimmed help lines.
        claude = FakeClaude(
            stdout="backgrounded \u00b7 \x1b[36me3b90936\x1b[39m \u00b7 task-t1\n"
            "\x1b[2m  claude agents             list sessions\x1b[22m\n"
            "\x1b[2m  claude attach e3b90936    open in this terminal\x1b[22m\n"
        )
        started = session.start(self.root, "t1", "m", run=claude)
        self.assertEqual("e3b90936", started["id"])
        # Claude Code does not list it yet: the task's end asks again.
        self.assertIsNone(started["session_id"])
        self.recorded(started)

    @verifies("scenario.task-session.start")
    def test_a_session_claude_code_did_not_start_is_refused(self):
        claude = FakeClaude(
            returncode=1, stdout="Workspace not trusted. Run `claude` in ... once."
        )
        before = store.load_task(self.root, "t1")
        with self.assertRaises(store.TaskError) as raised:
            session.start(self.root, "t1", "m", run=claude)
        self.assertEqual("session_failed", raised.exception.code)
        self.assertIn("Workspace not trusted", str(raised.exception))
        self.assertEqual(before, store.load_task(self.root, "t1"))
        self.assertEqual([], store.sessions(self.root, "t1"))
        self.assertFalse((self.folder / "sessions").exists())

    @verifies("scenario.task-session.start")
    def test_a_closed_task_starts_no_session(self):
        store.close_task(self.root, "t1", "completed", note="tried it")
        with self.assertRaises(store.TaskError) as raised:
            session.start(self.root, "t1", "m", run=FakeClaude())
        self.assertEqual("task_closed", raised.exception.code)
        # No boundary is written into the task's folder in the history.
        self.assertFalse((self.root / ".concorde/history/t1/runtime").exists())
        self.assertFalse(self.folder.exists())

    def hook(self, target: Path) -> dict | None:
        """The written hook's decision on an Edit of ``target``: None allows."""
        hook = self.folder / "runtime/write_hook.py"
        decided = subprocess.run(
            [sys.executable, str(hook)],
            input=json.dumps(
                {
                    "tool_name": "Edit",
                    "cwd": str(self.worktree),
                    "tool_input": {"file_path": str(target)},
                }
            ),
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(decided.stdout) if decided.stdout.strip() else None

    @verifies("scenario.task-session.project-mcp")
    def test_a_task_session_gets_the_project_mcp_server_without_a_channel(self):
        claude = FakeClaude()
        session.start(self.root, "t1", "concorde-7d", run=claude)
        (command, _), _ = claude.calls
        path = self.folder / "runtime" / "mcp.json"
        self.assertEqual(str(path), command[command.index("--mcp-config") + 1])
        # Claude Code never wakes a background session with channel events.
        self.assertNotIn("--dangerously-load-development-channels", command)
        self.assertNotIn("--channels", command)
        server = json.loads(path.read_text())["mcpServers"]["concorde"]
        self.assertEqual("0", server["env"]["CONCORDE_CHANNEL"])
        self.assertEqual("project-mcp", server["args"][-1])
        self.assertTrue(Path(server["args"][0]).is_file())

    def claude_config(self) -> tuple[Path, Path]:
        """An empty Claude Code configuration folder, which ``CLAUDE_CONFIG_DIR`` names for the
        rest of the test, and an empty managed settings folder."""
        config, managed = (
            self.project.home / "claude-config",
            self.project.home / "managed",
        )
        (managed / "managed-settings.d").mkdir(parents=True)
        config.mkdir()
        environ = patch.dict(os.environ, {"CLAUDE_CONFIG_DIR": str(config)})
        environ.start()
        self.addCleanup(environ.stop)
        return config, managed

    @staticmethod
    def write(path: Path, data) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(data if isinstance(data, str) else json.dumps(data))

    @staticmethod
    def servers(*names: str) -> dict:
        return {"mcpServers": {name: {"command": "true"} for name in names}}

    @verifies("scenario.task-session.mcp-approval")
    def test_the_session_carries_over_the_primary_worktrees_mcp_approvals(self):
        config, managed = self.claude_config()
        # The primary worktree's .mcp.json, which a session in the task worktree inside it loads
        # too, and one server only the task worktree declares.
        self.write(
            self.root / ".mcp.json",
            self.servers("concorde", "local", "rejected", "never", "user.tool"),
        )
        self.write(
            self.worktree / ".mcp.json", self.servers("legacy", "managed", "fresh")
        )
        self.write(
            self.root / ".claude/settings.local.json",
            {
                "enabledMcpjsonServers": ["concorde", "local", "rejected"],
                "disabledMcpjsonServers": ["rejected"],
            },
        )
        # Claude Code compares names with every character but letters, digits, _ and - as _.
        self.write(config / "settings.json", {"enabledMcpjsonServers": ["user_tool"]})
        self.write(
            config / ".claude.json",
            {
                "projects": {
                    os.path.realpath(self.root): {"enabledMcpjsonServers": ["legacy"]}
                }
            },
        )
        self.write(
            managed / "managed-settings.d/10-mcp.json",
            {"enabledMcpjsonServers": ["managed"]},
        )
        self.assertEqual(
            {
                "enabledMcpjsonServers": ["legacy", "local", "managed", "user.tool"],
                "disabledMcpjsonServers": ["concorde", "fresh", "never", "rejected"],
            },
            session.mcp_approvals(self.root, self.worktree, managed),
        )
        # Approving every project server approves all but those rejected, never concorde.
        self.write(
            self.root / ".claude/settings.local.json",
            {"enableAllProjectMcpServers": True, "disabledMcpjsonServers": ["never"]},
        )
        self.assertEqual(
            {
                "enabledMcpjsonServers": [
                    "fresh",
                    "legacy",
                    "local",
                    "managed",
                    "rejected",
                    "user.tool",
                ],
                "disabledMcpjsonServers": ["concorde", "never"],
            },
            session.mcp_approvals(self.root, self.worktree, managed),
        )

    @verifies("scenario.task-session.mcp-approval")
    def test_the_session_settings_disable_the_project_concorde_entry(self):
        _, managed = self.claude_config()
        self.write(self.root / ".mcp.json", self.servers("concorde", "other"))
        with patch.object(session, "MANAGED", managed):
            shown = session.start(self.root, "t1", "m", dry_run=True)
        written = json.loads(Path(shown["settings"]).read_text())
        self.assertEqual([], written["enabledMcpjsonServers"])
        self.assertEqual(["concorde", "other"], written["disabledMcpjsonServers"])

    @verifies("scenario.task-session.mcp-approval")
    def test_an_unusable_mcp_json_still_starts_the_session(self):
        _, managed = self.claude_config()
        self.write(self.root / ".mcp.json", "{not json")
        self.write(self.worktree / ".mcp.json", {"mcpServers": ["a list"]})
        self.write(self.root / ".claude/settings.local.json", "[]")
        expected = {"enabledMcpjsonServers": [], "disabledMcpjsonServers": ["concorde"]}
        self.assertEqual(
            expected, session.mcp_approvals(self.root, self.worktree, managed)
        )
        (self.root / ".mcp.json").unlink()
        (self.worktree / ".mcp.json").unlink()
        self.assertEqual(
            expected, session.mcp_approvals(self.root, self.worktree, managed)
        )
        claude = FakeClaude()
        with patch.object(session, "MANAGED", managed):
            session.start(self.root, "t1", "m", run=claude)
        self.assertEqual(1, len(store.sessions(self.root, "t1")))

    @verifies("scenario.task-session.boundary")
    def test_the_boundary_confines_the_session_to_its_task(self):
        shown = session.start(self.root, "t1", "m", dry_run=True)
        self.assertEqual(str(self.worktree), shown["cwd"])
        self.assertIsNone(self.hook(self.worktree / "src/a/calc.py"))
        self.assertIsNone(self.hook(self.folder / "decisions.md"))
        # The task's record and trace are Tasks' own: the hook denies them.
        self.assertIsNotNone(self.hook(self.folder / "task.json"))
        # Issues are written through the Issue command or tools, never by Edit or Write.
        self.assertIsNotNone(self.hook(self.root / ".concorde/issues/I-0.md"))
        denied = self.hook(self.root / "src/a/calc.py")
        self.assertEqual("deny", denied["hookSpecificOutput"]["permissionDecision"])
        self.assertIn(
            str(self.worktree), denied["hookSpecificOutput"]["permissionDecisionReason"]
        )
        settings = json.loads(Path(shown["settings"]).read_text())
        # Nothing but the hook restricts the session: no sandbox, no deny rules.
        self.assertNotIn("sandbox", settings)
        self.assertNotIn("permissions", settings)
        self.assertEqual(
            {"enabledMcpjsonServers", "disabledMcpjsonServers", "hooks"},
            set(settings),
        )
        # A dry run records no session.
        self.assertEqual([], store.sessions(self.root, "t1"))


# Stands in for Claude Code's ``claude stop``, ``claude rm`` and ``claude agents --json --all``:
# appends each call, with whether the task worktree still exists then, to the log its
# configuration names, and answers with the exit code and output configured for the subcommand,
# by default as Claude Code does, listing the sessions its configuration names.
FAKE_CLAUDE = """\
import json, os, sys
config = json.loads(open(os.environ["FAKE_CLAUDE"]).read())
command, target = sys.argv[1], sys.argv[2]
with open(config["log"], "a") as stream:
    stream.write(json.dumps({"argv": sys.argv[1:],
                             "worktree": os.path.isdir(config["worktree"])}) + "\\n")
if command == "agents":
    default = [0, json.dumps(config["listed"]), ""]
else:
    default = [0, {"stop": "stopped ", "rm": "removed "}[command] + target + "\\n", ""]
code, out, err = config.get("answers", {}).get(command, default)
sys.stdout.write(out)
sys.stderr.write(err)
sys.exit(code)
"""
AGENTS = ["agents", "--json", "--all"]


def full_id(short: str) -> str:
    return f"{short}-1111-2222-3333-444455556666"


class EndOfTaskTests(unittest.TestCase):
    """A task's end stops, keeps and removes its Claude Code task sessions."""

    def setUp(self):
        self.project = OperationProject(self)
        self.root = self.project.root
        gitignore = self.root / ".gitignore"
        gitignore.write_text(
            gitignore.read_text() + "".join(f"{path}\n" for path in TRACES)
        )
        subprocess.run(["git", "config", "user.name", "t"], cwd=self.root, check=True)
        subprocess.run(
            ["git", "config", "user.email", "t@t"], cwd=self.root, check=True
        )
        commit(self.root, "ignore task records")
        self.project.open_task("t1")
        self.worktree = self.project.worktree("t1")
        scratch = self.project.home / "claude-fake"
        self.claude_config = self.project.home / "claude-config"
        (scratch / "bin").mkdir(parents=True)
        program = scratch / "bin/claude"
        program.write_text(f"#!{sys.executable}\n{FAKE_CLAUDE}")
        program.chmod(0o755)
        self.log = scratch / "calls.jsonl"
        self.config = scratch / "config.json"
        self.listed: list[dict] = []
        self.answers: dict = {}
        self.answer()
        environ = patch.dict(
            os.environ,
            {
                "PATH": f"{scratch / 'bin'}{os.pathsep}{os.environ['PATH']}",
                "FAKE_CLAUDE": str(self.config),
                "CLAUDE_CONFIG_DIR": str(self.claude_config),
            },
        )
        environ.start()
        self.addCleanup(environ.stop)

    def answer(self, **answers):
        """Let the fake ``claude`` answer a subcommand with ``[code, stdout, stderr]``."""
        self.answers = answers
        self.config.write_text(
            json.dumps(
                {
                    "log": str(self.log),
                    "worktree": str(self.worktree),
                    "answers": answers,
                    "listed": self.listed,
                }
            )
        )

    def calls(self) -> list[dict]:
        if not self.log.exists():
            return []
        return [json.loads(line) for line in self.log.read_text().splitlines()]

    def claude_session(
        self, short: str, *, known: bool = True, state: str | None = "done"
    ) -> None:
        """Record a started session, with its full session id when ``known``, and let Claude
        Code list it in ``state``, or not at all when ``state`` is None."""
        store.record_session(
            self.root,
            "t1",
            {
                "id": short,
                "reported_id": short,
                "session_id": full_id(short) if known else None,
                "name": "task-t1",
                "main": "concorde-7d",
                "model": None,
            },
        )
        if state is not None:
            self.listed.append(
                {
                    "id": short,
                    "sessionId": full_id(short),
                    "cwd": str(self.worktree),
                    "kind": "background",
                    "state": state,
                }
            )
            self.answer(**self.answers)

    def transcript(
        self,
        short: str,
        project: str | None = None,
        records: list[dict] | None = None,
        subagent: list[dict] | None = None,
    ) -> Path:
        """Write the session's transcript where Claude Code keeps it, in the project folder of
        the task worktree unless ``project`` names another, with a subagent transcript beside."""
        folder = (
            self.claude_config
            / "projects"
            / (project or session._project_folder(str(self.worktree)))
        )
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"{full_id(short)}.jsonl"
        lines = records or [{"type": "user", "session": short}]
        path.write_text("".join(json.dumps(line) + "\n" for line in lines))
        beside = path.with_suffix("") / "subagents"
        beside.mkdir(parents=True)
        (beside / "agent-1.jsonl").write_text(
            "".join(json.dumps(line) + "\n" for line in subagent or [{}])
        )
        return path

    def command(self, *argv):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = cli.main(list(argv), cwd=self.root)
        return status, json.loads(output.getvalue())

    def kept(self, short: str, source: Path) -> None:
        """The history keeps the session's transcript and its folder in the session's node."""
        folder = self.root / ".concorde/history/t1/sessions" / short
        self.assertEqual(
            source.read_bytes(), (folder / session.TRANSCRIPT).read_bytes()
        )
        self.assertTrue((folder / "transcript/subagents/agent-1.jsonl").is_file())
        node = trace.read(folder)
        self.assertEqual(
            [("transcript", "transcript.jsonl", trace.digest(source))],
            [(item["id"], item["path"], item["digest"]) for item in node["artifacts"]],
        )
        # Claude Code lists the session as done, waiting for its next message.
        self.assertEqual(
            ("ok", "done", full_id(short)),
            (
                node["status"],
                node["outcome"],
                node["content"]["data"]["session_id"],
            ),
        )

    @verifies("scenario.task-session.end-removed")
    def test_a_merge_keeps_and_removes_every_claude_code_session(self):
        # The first's full session id is learnt only at the task's end.
        self.claude_session("aaaa1111", known=False)
        self.claude_session("bbbb2222")
        first = self.transcript("aaaa1111")
        # A transcript in another project folder is found too.
        second = self.transcript("bbbb2222", project="-elsewhere")
        deliver(self.worktree)
        with store.decision_log_path(self.root, "t1").open("a") as stream:
            stream.write("\n## Delivered\n")
        check = shlex.join([sys.executable, "-c", ""])
        status, value = self.command("merge", "t1", "--check", check)
        self.assertEqual(0, status, value)
        self.assertEqual([], value["warnings"])
        self.assertEqual("merged", value["record"]["closed"]["outcome"])
        # A merge stops nothing; it asks Claude Code once for its sessions and removes each
        # once the task has closed.
        self.assertEqual(
            [AGENTS, ["rm", "aaaa1111"], ["rm", "bbbb2222"]],
            [item["argv"] for item in self.calls()],
        )
        self.assertFalse(any(item["worktree"] for item in self.calls()))
        self.kept("aaaa1111", first)
        self.kept("bbbb2222", second)

    @verifies("scenario.task-session.close-stops")
    def test_a_close_without_a_merge_stops_its_claude_code_sessions_first(self):
        self.claude_session("aaaa1111")
        source = self.transcript("aaaa1111")
        status, value = self.command(
            "close", "t1", "--failed", "--reason", "wrong direction", "--no-error"
        )
        self.assertEqual(0, status, value)
        self.assertEqual([], value["warnings"])
        self.assertEqual("failed", value["record"]["state"])
        # Stopped while its worktree still existed, removed after the close.
        self.assertEqual(
            [
                (["stop", "aaaa1111"], True),
                (AGENTS, False),
                (["rm", "aaaa1111"], False),
            ],
            [(item["argv"], item["worktree"]) for item in self.calls()],
        )
        self.kept("aaaa1111", source)

    @verifies("scenario.task-session.close-stops")
    def test_a_session_claude_code_no_longer_knows_counts_as_stopped(self):
        self.claude_session("aaaa1111", state=None)
        self.transcript("aaaa1111")
        gone = [1, "", "No job matching 'aaaa1111'\n"]
        self.answer(stop=gone, rm=gone)
        status, value = self.command("close", "t1", "--completed", "--note", "done")
        self.assertEqual(0, status, value)
        self.assertEqual([], value["warnings"])

    @verifies("scenario.task-session.stop-unconfirmed")
    def test_a_stop_claude_code_cannot_confirm_refuses_the_close(self):
        self.claude_session("aaaa1111")
        self.answer(
            stop=[
                1,
                "",
                "couldn't confirm aaaa1111 was stopped — the service restarts\n",
            ]
        )
        before = store.load_task(self.root, "t1")
        status, value = self.command("close", "t1", "--completed", "--note", "done")
        self.assertEqual(1, status, value)
        error = value["error"]
        self.assertEqual("session_stop_failed", error["code"])
        for text in ("aaaa1111", "couldn't confirm", "claude stop aaaa1111"):
            self.assertIn(text, error["detail"])
        self.assertEqual(before, store.load_task(self.root, "t1"))
        self.assertTrue(self.worktree.is_dir())
        self.assertEqual(
            [["stop", "aaaa1111"]], [item["argv"] for item in self.calls()]
        )

    @verifies("scenario.task-session.remove-best-effort")
    def test_a_session_not_removed_only_warns(self):
        self.claude_session("aaaa1111")
        self.claude_session("bbbb2222")
        source = self.transcript("aaaa1111")
        # bbbb2222 has no transcript: it is not removed, so nothing of it is lost.
        self.answer(rm=[1, "", "couldn't remove aaaa1111 — kill_unconfirmed\n"])
        status, value = self.command("close", "t1", "--completed", "--note", "done")
        self.assertEqual(0, status, value)
        self.assertEqual("closed", value["record"]["state"])
        removed, unkept = value["warnings"][1], value["warnings"][0]
        for text in (
            "aaaa1111",
            "couldn't remove aaaa1111 — kill_unconfirmed",
            "`claude rm aaaa1111`",
        ):
            self.assertIn(text, removed)
        for text in (
            "bbbb2222",
            f"no transcript {full_id('bbbb2222')}.jsonl",
            "`claude rm bbbb2222`",
        ):
            self.assertIn(text, unkept)
        self.assertEqual(
            [["stop", "aaaa1111"], ["stop", "bbbb2222"], AGENTS, ["rm", "aaaa1111"]],
            [item["argv"] for item in self.calls()],
        )
        self.kept("aaaa1111", source)
        folder = self.root / ".concorde/history/t1/sessions/bbbb2222"
        self.assertFalse((folder / session.TRANSCRIPT).exists())
        node = trace.read(folder)
        self.assertEqual([], node["artifacts"])
        # It still receives what Claude Code told of it, and no figures.
        self.assertEqual(
            ("ok", None, None),
            (node["status"], node["ended_at"], node["usage"]["turns"]),
        )

    def test_a_session_claude_code_cannot_name_warns(self):
        # Neither the start nor the end learnt the full session id.
        self.claude_session("aaaa1111", known=False, state=None)
        self.transcript("aaaa1111")
        status, value = self.command("close", "t1", "--completed", "--note", "done")
        self.assertEqual(0, status, value)
        [warning] = value["warnings"]
        for text in (
            "aaaa1111",
            "did not tell its full session id",
            "`claude agents --json --all` lists no session aaaa1111",
            "`claude rm aaaa1111`",
        ):
            self.assertIn(text, warning)
        node = trace.read(self.root / ".concorde/history/t1/sessions/aaaa1111")
        self.assertEqual(("unknown", None), (node["status"], node["outcome"]))
        self.assertNotIn(["rm", "aaaa1111"], [item["argv"] for item in self.calls()])

    @verifies("scenario.task-session.node-finished")
    def test_a_session_node_receives_its_figures_from_claude_code(self):
        self.claude_session("aaaa1111")
        # Claude Code no longer lists the second; its id was learnt when it started.
        self.claude_session("bbbb2222", state=None)

        def said(at, message, model="claude-opus-5-5", **used):
            return {
                "type": "assistant",
                "timestamp": at,
                "message": {"id": message, "model": model, "usage": used},
            }

        opus = {
            "inputTokens": 15,
            "outputTokens": 150,
            "cacheReadInputTokens": 3000,
            "cacheCreationInputTokens": 200,
            "costUSD": 0.4,
        }
        first = [
            {"type": "user", "timestamp": "2026-09-30T10:00:00.000Z"},
            # One API message over two records is counted once.
            said(
                "2026-09-30T10:00:05.000Z",
                "msg_1",
                input_tokens=10,
                output_tokens=100,
                cache_read_input_tokens=1000,
                cache_creation_input_tokens=200,
            ),
            said(
                "2026-09-30T10:00:06.000Z",
                "msg_1",
                input_tokens=10,
                output_tokens=100,
                cache_read_input_tokens=1000,
                cache_creation_input_tokens=200,
            ),
            said(
                "2026-09-30T10:01:00.000Z",
                "msg_2",
                input_tokens=5,
                output_tokens=50,
                cache_read_input_tokens=2000,
                cache_creation_input_tokens=0,
            ),
            # A message Claude Code wrote itself is no model's.
            said("2026-09-30T10:01:30.000Z", "msg_x", model="<synthetic>"),
            {
                "type": "cost-state",
                "sessionId": full_id("aaaa1111"),
                "totalCostUSD": 0.42,
                "totalAPIDuration": 41000,
                "modelUsage": {"claude-opus-5-5": opus},
            },
            {"type": "last-prompt", "lastPrompt": "report"},
        ]
        subagent = [
            {"type": "user", "timestamp": "2026-09-30T11:00:00.000Z"},
            said(
                "2026-09-30T11:00:01.000Z",
                "msg_3",
                model="claude-haiku-4-5",
                input_tokens=1,
                output_tokens=2,
                cache_read_input_tokens=3,
                cache_creation_input_tokens=4,
            ),
        ]
        self.transcript("aaaa1111", records=first, subagent=subagent)
        second = [
            {"type": "user", "timestamp": "2026-09-30T09:00:00.000Z"},
            said("2026-09-30T09:00:10.500Z", "msg_9", input_tokens=7, output_tokens=8),
        ]
        self.transcript("bbbb2222", records=second)
        deliver(self.worktree)
        with store.decision_log_path(self.root, "t1").open("a") as stream:
            stream.write("\n## Delivered\n")
        check = shlex.join([sys.executable, "-c", ""])
        status, value = self.command("merge", "t1", "--check", check)
        self.assertEqual(0, status, value)
        self.assertEqual([], value["warnings"])
        sessions = self.root / ".concorde/history/t1/sessions"
        node = trace.read(sessions / "aaaa1111")
        self.assertEqual(
            {
                "tokens_in": 16,
                "tokens_out": 152,
                "tokens_cache_read": 3003,
                "tokens_cache_write": 204,
                "cost_usd": 0.42,
                "turns": 3,
                "duration_seconds": 90.0,
            },
            node["usage"],
        )
        self.assertEqual(
            ("ok", "done", "2026-09-30T10:01:30.000000Z"),
            (node["status"], node["outcome"], node["ended_at"]),
        )
        data = node["content"]["data"]
        self.assertEqual(
            {
                "claude-opus-5-5": {
                    "tokens_in": 15,
                    "tokens_out": 150,
                    "tokens_cache_read": 3000,
                    "tokens_cache_write": 200,
                    "messages": 2,
                },
                "claude-haiku-4-5": {
                    "tokens_in": 1,
                    "tokens_out": 2,
                    "tokens_cache_read": 3,
                    "tokens_cache_write": 4,
                    "messages": 1,
                },
            },
            data["models"],
        )
        self.assertEqual(
            (full_id("aaaa1111"), "done", {"claude-opus-5-5": opus}),
            (data["session_id"], data["claude_state"], data["model_usage"]),
        )
        # Without a cost-state record the cost is null; unlisted, the status stays unknown.
        node = trace.read(sessions / "bbbb2222")
        self.assertEqual(
            (7, 8, None, 1, 10.5),
            tuple(
                node["usage"][key]
                for key in (
                    "tokens_in",
                    "tokens_out",
                    "cost_usd",
                    "turns",
                    "duration_seconds",
                )
            ),
        )
        self.assertEqual(
            ("unknown", None, "2026-09-30T09:00:10.500000Z", None, None),
            (
                node["status"],
                node["outcome"],
                node["ended_at"],
                node["content"]["data"]["claude_state"],
                node["content"]["data"]["model_usage"],
            ),
        )

    def test_a_node_written_before_version_2_is_finished(self):
        self.claude_session("aaaa1111")
        source = self.transcript("aaaa1111")
        folder = self.root / ".concorde/tasks/t1/sessions/aaaa1111"
        record = trace.read(folder)
        record["content"] = {
            "type_id": store.SESSION_TRACE,
            "schema_version": 1,
            "data": {
                "name": "task-t1",
                "main": "concorde-7d",
                "model": None,
                "reported_id": "aaaa1111",
            },
        }
        (folder / "trace.json").write_text(json.dumps(record))
        status, value = self.command("close", "t1", "--completed", "--note", "done")
        self.assertEqual(0, status, value)
        self.assertEqual([], value["warnings"])
        self.kept("aaaa1111", source)
        node = trace.read(self.root / ".concorde/history/t1/sessions/aaaa1111")
        self.assertEqual(2, node["content"]["schema_version"])


if __name__ == "__main__":
    unittest.main()
