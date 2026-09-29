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
from concorde.tasks import cli, session, store
from concorde.tracing import layout
from concorde.tracing import node as trace
from tests.concorde.support.operation_project import OperationProject, commit
from tests.concorde.tasks.deliveries import deliver


class FakeClaude:
    """Stands in for ``claude --bg``: records the call and answers like Claude Code."""

    def __init__(self, returncode=0, stdout="backgrounded · 33afbc14 · task-t1\n"):
        self.returncode, self.stdout = returncode, stdout
        self.calls = []

    def __call__(self, command, **options):
        self.calls.append((command, options))
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
        fields = ("program", "id", "reported_id", "name", "main", "model", "started_at")
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
            ("claude", started["name"], started["main"]),
            tuple(node["content"]["data"][key] for key in ("program", "name", "main")),
        )
        # The record keeps no sessions.
        self.assertNotIn("sessions", store.load_task(self.root, "t1"))

    @verifies("scenario.task-session.start")
    def test_start_a_task_session(self):
        claude = FakeClaude()
        started = session.start(
            self.root, "t1", "concorde-7d", run=claude, home=self.project.home
        )
        directory = self.folder / "runtime"
        self.assertTrue((directory / "settings.json").is_file())
        self.assertTrue((directory / "write_hook.py").is_file())
        [(command, options)] = claude.calls
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
        self.recorded(started)

    @verifies("scenario.task-session.start")
    def test_a_coloured_start_line_is_recognised(self):
        # Claude Code 2.1.283 colours the id and adds dimmed help lines.
        claude = FakeClaude(
            stdout="backgrounded \u00b7 \x1b[36me3b90936\x1b[39m \u00b7 task-t1\n"
            "\x1b[2m  claude agents             list sessions\x1b[22m\n"
            "\x1b[2m  claude attach e3b90936    open in this terminal\x1b[22m\n"
        )
        started = session.start(
            self.root, "t1", "m", run=claude, home=self.project.home
        )
        self.assertEqual("e3b90936", started["id"])
        self.recorded(started)

    @verifies("scenario.task-session.start")
    def test_a_session_claude_code_did_not_start_is_refused(self):
        claude = FakeClaude(
            returncode=1, stdout="Workspace not trusted. Run `claude` in ... once."
        )
        before = store.load_task(self.root, "t1")
        with self.assertRaises(store.TaskError) as raised:
            session.start(self.root, "t1", "m", run=claude, home=self.project.home)
        self.assertEqual("session_failed", raised.exception.code)
        self.assertIn("Workspace not trusted", str(raised.exception))
        self.assertEqual(before, store.load_task(self.root, "t1"))
        self.assertEqual([], store.sessions(self.root, "t1"))
        self.assertFalse((self.folder / "sessions").exists())

    @verifies("scenario.task-session.start")
    def test_a_closed_task_starts_no_session(self):
        store.close_task(self.root, "t1", "completed", note="tried it")
        with self.assertRaises(store.TaskError) as raised:
            session.start(
                self.root, "t1", "m", run=FakeClaude(), home=self.project.home
            )
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

    @verifies("scenario.task-session.boundary")
    def test_the_boundary_confines_the_session_to_its_task(self):
        shown = session.start(
            self.root, "t1", "m", dry_run=True, home=self.project.home
        )
        self.assertEqual(str(self.worktree), shown["cwd"])
        self.assertIsNone(self.hook(self.worktree / "src/a/calc.py"))
        self.assertIsNone(self.hook(self.folder / "decisions.md"))
        # The task's record and trace are Tasks' own: the hook denies them.
        self.assertIsNotNone(self.hook(self.folder / "task.json"))
        denied = self.hook(self.root / "src/a/calc.py")
        self.assertEqual("deny", denied["hookSpecificOutput"]["permissionDecision"])
        self.assertIn(
            str(self.worktree), denied["hookSpecificOutput"]["permissionDecisionReason"]
        )
        settings = json.loads(Path(shown["settings"]).read_text())
        sandbox = settings["sandbox"]
        self.assertTrue(sandbox["enabled"])
        self.assertFalse(sandbox["allowUnsandboxedCommands"])
        self.assertEqual({"allowedDomains": ["*"]}, sandbox["network"])
        home = Path(os.path.realpath(self.project.home))
        self.assertEqual(
            sorted(
                str(Path(os.path.realpath(path)))
                for path in (
                    self.worktree,
                    self.root / ".git",
                    self.folder,
                    self.root / ".concorde/locks",
                    home / ".cache",
                    home / ".npm",
                )
            ),
            sandbox["filesystem"]["allowWrite"],
        )
        # A dry run records no session.
        self.assertEqual([], store.sessions(self.root, "t1"))


# Stands in for Claude Code's ``claude stop`` and ``claude rm``: appends each call, with whether
# the task worktree still exists then, to the log its configuration names, and answers with the
# exit code and output configured for the subcommand, by default as Claude Code does.
FAKE_CLAUDE = """\
import json, os, sys
config = json.loads(open(os.environ["FAKE_CLAUDE"]).read())
command, short = sys.argv[1], sys.argv[2]
with open(config["log"], "a") as stream:
    stream.write(json.dumps({"argv": sys.argv[1:],
                             "worktree": os.path.isdir(config["worktree"])}) + "\\n")
code, out, err = config.get("answers", {}).get(
    command, [0, {"stop": "stopped ", "rm": "removed "}[command] + short + "\\n", ""])
sys.stdout.write(out)
sys.stderr.write(err)
sys.exit(code)
"""


class EndOfTaskTests(unittest.TestCase):
    """A task's end stops, keeps and removes its Claude Code task sessions."""

    def setUp(self):
        self.project = OperationProject(self)
        self.root = self.project.root
        gitignore = self.root / ".gitignore"
        gitignore.write_text(
            gitignore.read_text() + "".join(f"{path}\n" for path in layout.IGNORED)
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
        self.config.write_text(
            json.dumps(
                {
                    "log": str(self.log),
                    "worktree": str(self.worktree),
                    "answers": answers,
                }
            )
        )

    def calls(self) -> list[dict]:
        if not self.log.exists():
            return []
        return [json.loads(line) for line in self.log.read_text().splitlines()]

    def claude_session(self, short: str) -> None:
        store.record_session(
            self.root,
            "t1",
            {
                "program": "claude",
                "id": short,
                "reported_id": short,
                "name": "task-t1",
                "main": "concorde-7d",
                "model": None,
            },
        )

    def transcript(self, short: str, project: str | None = None) -> Path:
        """Write the session's transcript where Claude Code keeps it, in the project folder of
        the task worktree unless ``project`` names another, with a subagent transcript beside."""
        folder = (
            self.claude_config
            / "projects"
            / (project or session._project_folder(str(self.worktree)))
        )
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"{short}-1111-2222-3333-444455556666.jsonl"
        path.write_text(json.dumps({"type": "user", "session": short}) + "\n")
        beside = path.with_suffix("") / "subagents"
        beside.mkdir(parents=True)
        (beside / "agent-1.jsonl").write_text("{}\n")
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
        self.assertEqual("unknown", node["status"])

    @verifies("scenario.task-session.end-removed")
    def test_a_merge_keeps_and_removes_every_claude_code_session(self):
        self.claude_session("aaaa1111")
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
        # A merge stops nothing; it removes each session once the task has closed.
        self.assertEqual(
            [["rm", "aaaa1111"], ["rm", "bbbb2222"]],
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
            [(["stop", "aaaa1111"], True), (["rm", "aaaa1111"], False)],
            [(item["argv"], item["worktree"]) for item in self.calls()],
        )
        self.kept("aaaa1111", source)

    @verifies("scenario.task-session.close-stops")
    def test_a_session_claude_code_no_longer_knows_counts_as_stopped(self):
        self.claude_session("aaaa1111")
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
            "no transcript bbbb2222*.jsonl",
            "`claude rm bbbb2222`",
        ):
            self.assertIn(text, unkept)
        self.assertEqual(
            [["stop", "aaaa1111"], ["stop", "bbbb2222"], ["rm", "aaaa1111"]],
            [item["argv"] for item in self.calls()],
        )
        self.kept("aaaa1111", source)
        folder = self.root / ".concorde/history/t1/sessions/bbbb2222"
        self.assertFalse((folder / session.TRANSCRIPT).exists())
        self.assertEqual([], trace.read(folder)["artifacts"])


if __name__ == "__main__":
    unittest.main()
