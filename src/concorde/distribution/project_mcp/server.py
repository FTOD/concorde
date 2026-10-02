"""The stdio session of the project MCP server: newline-delimited JSON-RPC 2.0 on standard input
and output, with Claude Code channel notifications sent from the threads that watch.

The server finds the project once, at start: the primary worktree of the Git repository that
``CLAUDE_PROJECT_DIR``, or else its working directory, lies in, found through Git's common
directory, so a server started from any worktree serves the same tasks, traces and locks. It is a
child of one Claude Code session and lives as long as that session, but answers no call with its
own code: each runs in a fresh process of the primary worktree's current Concorde (``calls.py``),
so the session never meets the code the server started with once Concorde changed. It declares
the tools capability and the experimental ``claude/channel`` capability; whether the session
actually listens to it as a channel is not something Claude Code tells a server, so it is read from
``CONCORDE_CHANNEL`` (``1`` or ``0``) when set, otherwise from its ancestor processes: one of them
must be a ``claude``, a program named ``claude`` or ``claude.exe``, started with
``--dangerously-load-development-channels server:<name>`` or ``--channels server:<name>`` whose
standard input is a terminal. Only an interactive session is
woken by channel events: a probe on 2026-09-29 (Claude Code 2.1.284) found a ``claude --bg``
session started with the flag never woken, and ``claude -p`` registers no channel at all.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import threading
from pathlib import Path
from typing import IO

from ...kernel import errors
from ...coordination.tasks import store
from .calls import Calls
from .tools import ACTOR, THREADED, Refusal, digest, listing, serve_call

NAME = "concorde"
SUPPORTED_VERSIONS = ("2025-06-18", "2025-03-26", "2024-11-05")
CHANNEL_FLAGS = ("--dangerously-load-development-channels", "--channels")
# The names Claude Code's program runs under, the first word of its command line.
CLAUDE_PROGRAMS = ("claude", "claude.exe")
# How far up the process tree the server looks for the claude that started it.
ANCESTORS = 8
INSTRUCTIONS = (
    "Concorde's project MCP server: the project's tasks, traces and locks, read fresh from the "
    "primary worktree on every call by the Concorde its `concorde` runs at that moment. "
    "Queries: task_list, task_show, trace_show, run_result, workflow_report, locks. Short "
    "writes: task_open, task_escalate, task_report, task_answer, task_rebind, task_close. "
    "workflow_step starts or awaits a workflow step of the bound "
    "workspace the session started in, as a process of this server, for step agents. "
    "task_merge "
    "takes the task's workspace lock and the merge lock without waiting (a busy lock is refused "
    "naming its holder) and starts the merge as its own process. register_wait asks to be woken "
    "when a task reaches a state or is rebound to another main agent's session, a run ends or a "
    "lock is released; it never takes a lock for you. When this server is loaded as a channel, events arrive as "
    '<channel source="concorde" event="...">: wait_done, wait_failed or merge_ended, with '
    "the task, run or lock in the attributes and the answer or output in the body; act on them "
    "as on a finished background command. Every refusal is an error chain link: read it whole."
)


def _on_terminal(pid: int) -> bool:
    """Whether the process's standard input is a terminal, as an interactive session's is."""
    try:
        target = os.readlink(f"/proc/{pid}/fd/0")
    except OSError:
        return False
    return target.startswith(("/dev/pts/", "/dev/tty"))


def _ancestors(start: int, depth: int = ANCESTORS) -> list[tuple[list[str], bool]]:
    """The command line of each ancestor process, nearest first, and whether it runs on a
    terminal."""
    found, pid = [], start
    for _ in range(depth):
        try:
            with open(f"/proc/{pid}/stat", encoding="utf-8") as stat:
                parent = int(stat.read().rsplit(")", 1)[1].split()[1])
            with open(f"/proc/{parent}/cmdline", "rb") as cmdline:
                words = [
                    word.decode("utf-8", "replace")
                    for word in cmdline.read().split(b"\0")
                    if word
                ]
        except (OSError, ValueError, IndexError):
            break
        found.append((words, _on_terminal(parent)))
        if parent <= 1:
            break
        pid = parent
    return found


def channel_requested(name: str, words: list[str]) -> bool:
    """Whether the command line starts Claude Code with ``server:<name>`` as a channel."""
    entry = f"server:{name}"
    listening = False
    for word in words:
        if word in CHANNEL_FLAGS:
            listening = True
        elif word.startswith("--"):
            listening = False
        elif listening and entry in word.split():
            return True
    return False


def is_claude(words: list[str]) -> bool:
    """Whether the command line runs Claude Code's program, by the name of its first word."""
    return bool(words) and os.path.basename(words[0]) in CLAUDE_PROGRAMS


def channel_from(name: str, ancestors: list[tuple[list[str], bool]]) -> bool:
    """Whether an interactive ``claude`` ancestor, one on a terminal, names this server as a
    channel."""
    return any(
        terminal and is_claude(words) and channel_requested(name, words)
        for words, terminal in ancestors
    )


def detect_channel(name: str, environment: dict, pid: int | None = None) -> bool:
    configured = environment.get("CONCORDE_CHANNEL")
    if configured in ("1", "0"):
        return configured == "1"
    return channel_from(name, _ancestors(pid or os.getpid()))


def find_primary(environment: dict, cwd: Path) -> Path | None:
    here = Path(environment.get("CLAUDE_PROJECT_DIR") or cwd)
    try:
        return store.primary_of(here)
    except store.TaskError:
        return None


class Session:
    def __init__(
        self,
        reader: IO[str],
        writer: IO[str],
        environment=None,
        cwd: Path | None = None,
        name: str = NAME,
    ):
        self.reader = reader
        self.writer = writer
        self.lock = threading.Lock()
        environment = dict(os.environ if environment is None else environment)
        primary = find_primary(environment, Path(cwd or Path.cwd()))
        self.where = Path(environment.get("CLAUDE_PROJECT_DIR") or cwd or Path.cwd())
        self.calls = (
            Calls(
                primary,
                self.where,
                environment.get("CLAUDE_CODE_SESSION_ID") or None,
                detect_channel(name, environment),
                self.notify,
                self.tools_changed,
            )
            if primary is not None
            else None
        )

    # --- transport --------------------------------------------------------------------------

    def send(self, message: dict) -> None:
        text = json.dumps(message, separators=(",", ":"), ensure_ascii=False) + "\n"
        with self.lock:
            self.writer.write(text)
            self.writer.flush()

    def notify(self, content: str, meta: dict) -> None:
        """A Claude Code channel event; Claude Code drops it silently without a channel."""
        self.send(
            {
                "jsonrpc": "2.0",
                "method": "notifications/claude/channel",
                "params": {
                    "content": content,
                    "meta": {key: str(value) for key, value in meta.items()},
                },
            }
        )

    def tools_changed(self) -> None:
        """Tell the client that the current code's tools differ from those it was given."""
        self.send({"jsonrpc": "2.0", "method": "notifications/tools/list_changed"})

    def reply(self, identity, result: dict) -> None:
        self.send({"jsonrpc": "2.0", "id": identity, "result": result})

    # --- dispatch ---------------------------------------------------------------------------

    def handle(self, message: dict) -> None:
        method = message.get("method")
        identity = message.get("id")
        if method is None or identity is None:
            return  # a response or a notification: nothing to answer
        if method == "initialize":
            requested = (message.get("params") or {}).get("protocolVersion")
            self.reply(
                identity,
                {
                    "protocolVersion": requested
                    if requested in SUPPORTED_VERSIONS
                    else SUPPORTED_VERSIONS[0],
                    "capabilities": {
                        "tools": {"listChanged": True},
                        "experimental": {"claude/channel": {}},
                    },
                    "serverInfo": {"name": NAME, "version": "1"},
                    "instructions": INSTRUCTIONS,
                },
            )
        elif method == "ping":
            self.reply(identity, {})
        elif method == "tools/list":
            self.reply(
                identity,
                {"tools": self.calls.tools() if self.calls is not None else listing()},
            )
        elif method == "tools/call":
            params = message.get("params") or {}
            name, arguments = params.get("name"), params.get("arguments")
            if name in THREADED:
                # A workflow step waits up to its bound: answer the other calls meanwhile.
                threading.Thread(
                    target=lambda: self.reply(
                        identity, self.tool_result(name, arguments)
                    ),
                    name=f"call {identity}",
                    daemon=True,
                ).start()
            else:
                self.reply(identity, self.tool_result(name, arguments))
        else:
            self.send(
                {
                    "jsonrpc": "2.0",
                    "id": identity,
                    "error": {"code": -32601, "message": f"method not found: {method}"},
                }
            )

    def tool_result(self, name, arguments) -> dict:
        try:
            if self.calls is None:
                raise Refusal(
                    errors.link(
                        "component",
                        f"{ACTOR} ({name})",
                        "no_project",
                        f"{self.where} lies in no Git repository, so the server has no primary "
                        "worktree whose tasks it could serve",
                        reason="environment",
                        explanation="the server serves only the project of the session that "
                        "started it",
                        options=[
                            "start the session in a worktree of a Concorde project"
                        ],
                    )
                )
            value, error = self.calls.call(name, arguments), False
        except Refusal as refusal:
            value, error = {"error": refusal.link}, True
        except Exception as failure:  # noqa: BLE001 -- every failure is a detailed error link
            value = {
                "error": errors.from_exception(
                    f"{ACTOR} ({name})",
                    failure,
                    explanation="the server has no recovery for an unexpected error; nothing "
                    "after it ran",
                )
            }
            error = True
        text = json.dumps(value, indent=1, ensure_ascii=False, sort_keys=True)
        return {"content": [{"type": "text", "text": text}], "isError": error}

    def run(self) -> int:
        for line in self.reader:
            if not line.strip():
                continue
            try:
                message = json.loads(line)
            except ValueError:
                self.send(
                    {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {"code": -32700, "message": "parse error"},
                    }
                )
                continue
            if isinstance(message, dict):
                self.handle(message)
        if self.calls is not None:
            self.calls.close()
        return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="concorde project-mcp")
    parser.add_argument(
        "--name",
        default=NAME,
        help="the name the server is registered under, which a channel flag names as "
        "server:<name>",
    )
    parser.add_argument(
        "--call",
        metavar="TOOL",
        help="answer one call of the server, read as a JSON object from standard input; only the "
        "server runs this",
    )
    parser.add_argument(
        "--tools",
        action="store_true",
        help="print the tools of this Concorde as tools/list gives them; only the server runs this",
    )
    arguments = parser.parse_args(argv if argv is not None else [])
    if arguments.call is not None:
        return serve_call(arguments.call, sys.stdin, sys.stdout)
    if arguments.tools:
        tools = listing()
        sys.stdout.write(json.dumps({"tools": tools, "digest": digest(tools)}) + "\n")
        return 0
    return Session(sys.stdin, sys.stdout, name=arguments.name).run()


__all__ = ["Session", "channel_from", "channel_requested", "detect_channel", "main"]
