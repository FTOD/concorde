"""The server's side of every tool call: the call runs in a fresh process of the primary worktree's
current Concorde, and the server keeps only what needs a process that lives as long as its session,
the wait processes it watches and the merge processes it reaps.

Each call runs ``concorde project-mcp --call <tool>`` with the ``concorde`` of the primary worktree
as it is at that moment, its ``.concorde/bin/concorde`` or, in Concorde's source checkout, its
``scripts/concorde.py``, so a merge or a ``concorde update`` during the session changes the code
that answers the next call. The call's arguments and the session's provenance go to that process as
one JSON object on its standard input, and its last line of standard output is the answer.

A wait registered with a channel is ``concorde task wait …`` of the primary worktree, run as a
child that dies with the server, whose printed answer or refusal becomes the channel event. A merge
is the very process the call started: having answered, it replaced itself with
``concorde task merge``, so the server reaps it and reports its exit status.
"""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

from .. import errors
from .tools import ACTOR, STEP_GRACE, STEP_WAIT, Refusal, concorde_of, digest, listing

# How long an ordinary call's process may take before the call is refused.
CALL_LIMIT = 300
# How much of a finished merge's output a notification carries; the file holds all of it.
CUT = 6000
# Started before a wait command: ties it to the server, so that it ends when the server ends, and
# ends at once when the server was already gone.
TIED = (
    "import ctypes, os, sys\n"
    "try:\n"
    "    ctypes.CDLL(None).prctl(1, 15)  # PR_SET_PDEATHSIG, SIGTERM\n"
    "except (OSError, AttributeError):\n"
    "    pass\n"
    "if os.getppid() != int(sys.argv[1]):\n"
    "    sys.exit(0)\n"
    "os.execvp(sys.argv[2], sys.argv[2:])\n"
)


def last_answer(text: str) -> dict | None:
    """The last line of a call's output that is a JSON object with ``value`` or ``error``."""
    for line in reversed(text.splitlines()):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except ValueError:
            return None
        if isinstance(value, dict) and ("value" in value or "error" in value):
            return value
        return None
    return None


class Calls:
    """Runs the calls of one session in fresh processes and watches what outlives a call."""

    def __init__(
        self,
        primary: Path,
        where: Path,
        session: str | None,
        channel: bool,
        notify,
        changed,
    ):
        self.primary = primary
        self.where = where
        self.session = session
        self.channel = channel
        # A channel event: notify(content, meta).
        self.notify = notify
        # Called when the current code's tools differ from those the session was given.
        self.changed = changed
        self.lock = threading.Lock()
        self.waits = 0
        self.watched: list[subprocess.Popen] = []
        self.closing = False
        self.listed: str | None = None
        self._runtime: Path | None = None

    def runtime(self) -> Path:
        """A private temporary directory for the output of the merges this server started."""
        if self._runtime is None:
            self._runtime = Path(tempfile.mkdtemp(prefix="concorde-project-mcp-"))
        return self._runtime

    def command(self, *words: str) -> tuple[list[str], dict]:
        command, environment = concorde_of(self.primary)
        return [*command, *words], environment

    # --- the tool listing -------------------------------------------------------------------

    def tools(self) -> list[dict]:
        """The tools of the current code, or this server's own when its process gives none."""
        argv, environment = self.command("project-mcp", "--tools")
        try:
            done = subprocess.run(
                argv,
                cwd=self.primary,
                env=environment,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                timeout=CALL_LIMIT,
                check=False,
            )
            value = json.loads(done.stdout)
            tools = value["tools"]
            if not isinstance(tools, list):
                raise TypeError("no list of tools")
        except (OSError, subprocess.TimeoutExpired, ValueError, KeyError, TypeError):
            tools = listing()
        self.listed = digest(tools)
        return tools

    # --- calls ------------------------------------------------------------------------------

    def call(self, name: str, arguments) -> object:
        """The answer of the call's process, or ``Refusal`` with its link."""
        envelope = {
            "arguments": arguments,
            "primary": self.primary.as_posix(),
            "where": self.where.as_posix(),
            "session": self.session,
            "channel": self.channel,
        }
        if name == "task_merge":
            reply = self.merge(name, envelope)
        else:
            limit = CALL_LIMIT
            if name == "workflow_step":
                wait = arguments.get("wait") if isinstance(arguments, dict) else None
                limit = (wait if isinstance(wait, int) else STEP_WAIT) + 2 * STEP_GRACE
            reply = self.run(name, envelope, limit)
        if self.listed is not None and reply.get("tools") not in (None, self.listed):
            # The session was given other tools than the current code's: it lists them again.
            self.listed = reply["tools"]
            self.changed()
        if "error" in reply:
            raise Refusal(reply["error"])
        value = reply["value"]
        if isinstance(reply.get("watch"), dict):
            value = self.start_wait(name, value, reply["watch"])
        return value

    def failed(self, name: str, argv: list[str], detail: str) -> Refusal:
        return Refusal(
            errors.link(
                "component",
                f"{ACTOR} ({name})",
                "call_failed",
                f"`{shlex.join(argv)}` in {self.primary} {detail}",
                reason="environment",
                explanation="the server answers only with the answer of the primary worktree's "
                "current Concorde, which gave none",
                options=[
                    (
                        "run a `concorde` command in the primary worktree from Bash to see "
                        "whether its Concorde works"
                    ),
                    "repair the primary worktree's Concorde, then call again",
                ],
            )
        )

    def run(self, name: str, envelope: dict, limit: float) -> dict:
        argv, environment = self.command("project-mcp", "--call", name)
        try:
            done = subprocess.run(
                argv,
                cwd=self.primary,
                env=environment,
                input=json.dumps(envelope, ensure_ascii=False),
                capture_output=True,
                text=True,
                timeout=limit,
                check=False,
            )
        except subprocess.TimeoutExpired:
            raise self.failed(
                name, argv, f"gave no answer within {limit:g} seconds and was stopped"
            ) from None
        except OSError as error:
            raise self.failed(name, argv, f"could not be started: {error}") from None
        reply = last_answer(done.stdout)
        if reply is None:
            output = (done.stderr or done.stdout).strip()[-2000:] or "(no output)"
            raise self.failed(
                name,
                argv,
                f"exited with status {done.returncode} and printed no answer: {output}",
            )
        return reply

    # --- merges -----------------------------------------------------------------------------

    def merge(self, name: str, envelope: dict) -> dict:
        """The answer of a ``task_merge`` call, whose process, once it answered that it started the
        merge, is the merge, as a process of its own session that outlives the server."""
        arguments = envelope.get("arguments")
        task = arguments.get("task") if isinstance(arguments, dict) else None
        runtime = self.runtime()
        with self.lock:
            number = len(list(runtime.glob("*.json"))) + 1
            output = runtime / f"{number}-merge-{task}.json"
            output.touch()
        messages = runtime / f"{number}-merge-{task}.log"
        envelope = {
            **envelope,
            "merge": {"output": output.as_posix(), "messages": messages.as_posix()},
        }
        argv, environment = self.command("project-mcp", "--call", name)
        try:
            with messages.open("wb") as err:
                process = subprocess.Popen(
                    argv,
                    cwd=self.primary,
                    env=environment,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=err,
                    start_new_session=True,
                )
        except OSError as error:
            raise self.failed(name, argv, f"could not be started: {error}") from None
        try:
            process.stdin.write(
                json.dumps(envelope, ensure_ascii=False).encode("utf-8")
            )
            process.stdin.close()
        except OSError:
            pass
        # The answer ends when the process exits or, having started the merge, became it.
        text = process.stdout.read().decode("utf-8", "replace")
        process.stdout.close()
        reply = last_answer(text)
        if reply is None or "error" in reply:
            process.wait()
            if reply is None:
                try:
                    said = messages.read_text(errors="replace").strip()[-2000:]
                except OSError:
                    said = ""
                raise self.failed(
                    name,
                    argv,
                    f"exited with status {process.returncode} and printed no answer: "
                    f"{said or '(no output)'}",
                )
            return reply
        self.reap(process, str(task), output, messages)
        return reply

    def reap(self, process, task: str, output: Path, messages: Path) -> None:
        def reaped():
            code = process.wait()
            if not self.channel or self.closing:
                return
            try:
                text = output.read_text(encoding="utf-8", errors="replace").strip()
            except OSError:
                text = ""
            try:
                value = json.loads(text)
            except ValueError:
                value = None
            status = (
                "refused"
                if isinstance(value, dict) and "error" in value
                else ("ok" if code == 0 else "failed")
            )
            body = (
                text
                if len(text) <= CUT
                else f"{text[:CUT]}\n…(cut; the whole output is in {output})"
            )
            self.notify(
                f"Concorde: `concorde task merge {task}` ended with exit status {code} "
                f"({status}). Its output ({output}, errors in {messages}):\n{body}",
                {
                    "event": "merge_ended",
                    "task": task,
                    "exit_code": str(code),
                    "status": status,
                },
            )

        threading.Thread(target=reaped, name=f"merge {task}", daemon=True).start()

    # --- waits ------------------------------------------------------------------------------

    def start_wait(self, name: str, value: dict, watch: dict) -> dict:
        """Start the wait the call registered as ``concorde task wait`` and answer with its
        identity. Called on the thread that reads the session, which lives as long as the server,
        since the wait process ends when the thread that started it ends."""
        description = watch["description"]
        command, environment = self.command(*watch["words"])
        argv = [sys.executable, "-c", TIED, str(os.getpid()), *command]
        try:
            process = subprocess.Popen(
                argv,
                cwd=self.primary,
                env=environment,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except OSError as error:
            raise self.failed(
                name, command, f"could not be started to wait: {error}"
            ) from None
        with self.lock:
            self.waits += 1
            identity = str(self.waits)
            self.watched.append(process)
        meta = {**watch["meta"], "wait": identity}

        def watched():
            out, err = process.communicate()
            with self.lock:
                self.watched.remove(process)
            if self.closing:
                return
            try:
                answer = json.loads(out)
            except ValueError:
                answer = None
            if isinstance(answer, dict) and isinstance(answer.get("error"), dict):
                link = answer["error"]
                self.notify(
                    f"Concorde: wait {identity} for {description} ended without it: "
                    f"{errors.render(link)}",
                    {**meta, "event": "wait_failed", "code": str(link.get("code"))},
                )
            elif answer is not None and process.returncode == 0:
                self.notify(
                    f"Concorde: {description} happened (wait {identity}): "
                    f"{json.dumps(answer, ensure_ascii=False)}",
                    {**meta, "event": "wait_done"},
                )
            else:
                said = (err or out).strip()[-2000:] or "(no output)"
                link = self.failed(
                    "register_wait",
                    command,
                    f"exited with status {process.returncode} and printed no answer: {said}",
                ).link
                self.notify(
                    f"Concorde: wait {identity} for {description} failed: "
                    f"{errors.render(link)}",
                    {**meta, "event": "wait_failed", "code": link["code"]},
                )

        threading.Thread(target=watched, name=f"wait {identity}", daemon=True).start()
        return {**value, "wait": identity}

    def close(self) -> None:
        """End every wait still watched: its session is gone. Merges go on."""
        self.closing = True
        with self.lock:
            watched = list(self.watched)
        for process in watched:
            if process.poll() is None:
                process.terminate()


__all__ = ["Calls", "last_answer"]
