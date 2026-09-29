"""Live sessions: keep a real Claude Code or pi main session running in a test project, so that
what wakes it is the program's own notification, never the end-to-end tool's stand-in.

A headless round (``sessions.py``) ends its process with its turn, and the tool must stand in for
every wake. A live session is instead one long-lived process that is fed prompts on standard
input: Claude Code as ``claude -p --input-format stream-json --output-format stream-json``, which
starts a turn of its own when one of its background commands ends, and pi as ``pi --mode rpc``,
whose Concorde extension runs for the whole session and wakes it with a message. Every event the
process prints is kept with the time it arrived, so a case can tell a turn it prompted from a turn
the session began by itself, which is a wake.
"""

from __future__ import annotations

import json
import subprocess
import threading
import time
import uuid
from pathlib import Path

from common import E2EError
from sessions import CLIENTS, environment

# What a live session needs: a prompt of the case may ask it to run a command, in the background
# or not, and to read a file.
LIVE_TOOLS = ("Bash", "Read")
LIVE_NOTE = (
    "This session is run by Concorde's end-to-end tool, which types every prompt you receive; "
    "nobody else answers questions. Each prompt is one step of a test: do exactly what it asks, "
    "nothing more, and reply as briefly as it says."
)
STOP_SECONDS = 30.0


def claude_command(
    tools=LIVE_TOOLS,
    *,
    note: str = LIVE_NOTE,
    model: str | None = None,
    claude="claude",
) -> list[str]:
    """The argument list of a live Claude Code session, which reads its prompts as stream-json."""
    return [
        claude,
        "-p",
        "--input-format",
        "stream-json",
        "--output-format",
        "stream-json",
        "--verbose",
        "--append-system-prompt",
        note,
        *(["--model", model] if model else []),
        "--allowedTools",
        *tools,
    ]


def pi_command(
    session_id: str,
    session_dir: Path,
    *,
    note: str = LIVE_NOTE,
    model: str | None = None,
    pi="pi",
) -> list[str]:
    """The argument list of a live pi session in RPC mode; ``--approve`` trusts the project's
    Concorde extension for the run."""
    return [
        pi,
        "--mode",
        "rpc",
        "--approve",
        "--session-dir",
        str(session_dir),
        "--session-id",
        session_id,
        "--append-system-prompt",
        note,
        *(["--model", model] if model else []),
    ]


class LiveSession:
    """One live main session: its process, every event it printed with its arrival time, and the
    times at which the case prompted it."""

    def __init__(
        self,
        name: str,
        client: str,
        project: Path,
        directory: Path,
        *,
        model: str | None = None,
        program: str | None = None,
        note: str = LIVE_NOTE,
    ):
        if client not in CLIENTS:
            raise E2EError(
                "unknown_client",
                f"a live session runs on {' or '.join(CLIENTS)}, not {client!r}",
            )
        self.name = name
        self.client = client
        directory.mkdir(parents=True, exist_ok=True)
        self.log = directory / f"{name}.jsonl"
        self.errors = directory / f"{name}.err"
        self.session_id = str(uuid.uuid4()) if client == "pi" else None
        if client == "pi":
            argv = pi_command(
                self.session_id,
                directory / f"{name}-pi",
                note=note,
                model=model,
                pi=program or "pi",
            )
        else:
            argv = claude_command(note=note, model=model, claude=program or "claude")
        self.argv = argv
        self.events: list[tuple[float, dict]] = []
        self.prompts: list[float] = []
        self._lock = threading.Lock()
        self._err = self.errors.open("w")
        self._out = self.log.open("w")
        try:
            self.process = subprocess.Popen(
                argv,
                cwd=project,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=self._err,
                env=environment(),
            )
        except OSError as error:
            raise E2EError(
                "session_failed",
                f"live session {name} could not start `{argv[0]}`: {error}",
            ) from error
        self._reader = threading.Thread(target=self._read, daemon=True)
        self._reader.start()

    def _read(self) -> None:
        # Records are split on LF only: a JSON string may hold U+2028, which a text-mode line
        # reader would take for a line end.
        for raw in self.process.stdout:
            try:
                event = json.loads(raw.decode("utf-8"))
            except ValueError:
                continue
            if not isinstance(event, dict):
                continue
            moment = time.time()
            with self._lock:
                self.events.append((moment, event))
                self._out.write(json.dumps({"at": moment, "event": event}) + "\n")
                self._out.flush()

    def send(self, text: str) -> float:
        """Prompt the session; the time the prompt was sent."""
        if self.client == "pi":
            record = {
                "id": f"p{len(self.prompts) + 1}",
                "type": "prompt",
                "message": text,
            }
        else:
            record = {"type": "user", "message": {"role": "user", "content": text}}
        moment = time.time()
        self.prompts.append(moment)
        try:
            self.process.stdin.write((json.dumps(record) + "\n").encode("utf-8"))
            self.process.stdin.flush()
        except OSError as error:
            raise E2EError(
                "session_failed",
                f"live session {self.name} no longer reads its prompts: {error}",
                stderr=self.stderr(),
            ) from error
        return moment

    def since(self, moment: float, until: float | None = None) -> list[dict]:
        """The events that arrived from ``moment`` on, before ``until`` when given."""
        with self._lock:
            return [
                event
                for at, event in self.events
                if at >= moment and (until is None or at < until)
            ]

    def refusal(self, moment: float) -> str | None:
        """The error of a prompt pi refused since ``moment``, such as a model without a key."""
        for event in self.since(moment):
            if event.get("type") == "response" and event.get("success") is False:
                return str(event.get("error"))
        return None

    def settled(self, moment: float) -> bool:
        """Whether a turn ended since ``moment``: Claude Code's ``result`` event, pi's
        ``agent_settled`` or pi's refusal of the prompt."""
        for event in self.since(moment):
            kind = event.get("type")
            if kind == ("agent_settled" if self.client == "pi" else "result"):
                return True
        return self.client == "pi" and self.refusal(moment) is not None

    def wait_settled(self, moment: float, limit: float, poll: float = 0.5) -> None:
        deadline = time.monotonic() + limit
        while not self.settled(moment):
            if self.process.poll() is not None:
                raise E2EError(
                    "session_failed",
                    f"live session {self.name} ended with status {self.process.returncode} "
                    "before its turn ended",
                    log=str(self.log),
                    stderr=self.stderr(),
                )
            if time.monotonic() > deadline:
                raise E2EError(
                    "live_timeout",
                    f"live session {self.name} did not end its turn within {limit:.0f}s",
                    log=str(self.log),
                )
            time.sleep(poll)

    def turns(self, moment: float, until: float | None = None) -> list[dict]:
        """The turns that began from ``moment`` on: Claude Code's ``system`` ``init`` event, which
        opens every turn, and pi's ``agent_start``."""
        return [
            event
            for event in self.since(moment, until)
            if (self.client == "pi" and event.get("type") == "agent_start")
            or (
                self.client == "claude"
                and event.get("type") == "system"
                and event.get("subtype") == "init"
            )
        ]

    def notifications(self, moment: float, until: float | None = None) -> list[dict]:
        """The notifications that reached the session from ``moment`` on: Claude Code's
        ``task_notification`` of a background command, and the custom messages pi's extensions
        send, such as the run view's ``concorde-run``."""
        found = []
        for event in self.since(moment, until):
            if self.client == "claude":
                if event.get("type") == "system" and event.get("subtype") in (
                    "task_notification",
                ):
                    found.append(event)
            elif event.get("type") == "message_start":
                message = event.get("message") or {}
                if message.get("role") == "custom":
                    found.append(event)
        return found

    def woken(self, moment: float, until: float | None = None) -> bool:
        """Whether the session began a turn or received a notification from ``moment`` on without
        being prompted: the case prompts no session in the window it judges."""
        return bool(self.turns(moment, until) or self.notifications(moment, until))

    def statuses(self, moment: float, key: str = "concorde") -> list[str]:
        """The status texts pi's extension showed under ``key`` from ``moment`` on."""
        return [
            str(event.get("statusText") or "")
            for event in self.since(moment)
            if event.get("type") == "extension_ui_request"
            and event.get("method") == "setStatus"
            and event.get("statusKey") == key
        ]

    def notices(self, moment: float) -> list[str]:
        """The messages pi's extensions showed with ``notify`` from ``moment`` on."""
        return [
            str(event.get("message") or "")
            for event in self.since(moment)
            if event.get("type") == "extension_ui_request"
            and event.get("method") == "notify"
        ]

    def tool_output(self, moment: float) -> str:
        """The text of every tool result from ``moment`` on, where a Bash command's output is."""
        parts = []
        for event in self.since(moment):
            if self.client == "claude" and event.get("type") == "user":
                content = (event.get("message") or {}).get("content")
                for block in content if isinstance(content, list) else []:
                    if isinstance(block, dict) and block.get("type") == "tool_result":
                        value = block.get("content")
                        parts.append(
                            value
                            if isinstance(value, str)
                            else json.dumps(value, ensure_ascii=False)
                        )
            elif self.client == "pi" and event.get("type") == "tool_execution_end":
                parts.append(json.dumps(event.get("result"), ensure_ascii=False))
        return "\n".join(parts)

    def stderr(self) -> str:
        try:
            return self.errors.read_text(errors="replace")[-3000:]
        except OSError:
            return ""

    def close(self) -> None:
        """End the session: its standard input closes, which ends either program in order, and
        what is left of it is killed after a grace period."""
        try:
            self.process.stdin.close()
        except OSError:
            pass
        try:
            self.process.wait(timeout=STOP_SECONDS)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait()
        self._reader.join(timeout=5)
        self._out.close()
        self._err.close()

    def record(self) -> dict:
        # Claude Code names its session in its events; pi's is the one the tool chose.
        named = next(
            (event["session_id"] for event in self.since(0) if event.get("session_id")),
            None,
        )
        return {
            "name": self.name,
            "client": self.client,
            "session_id": self.session_id or named,
            "log": str(self.log),
            "stderr": str(self.errors),
            "exit": self.process.returncode,
        }
