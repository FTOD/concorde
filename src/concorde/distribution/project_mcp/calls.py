"""The server's side of every tool call: the call runs in a fresh process of the primary worktree's
current Concorde, and the server keeps only what needs a process that lives as long as its session,
the wait processes it watches and the merge processes it reaps.

Each call runs ``concorde project-mcp --call <tool>`` with the ``concorde`` of the primary worktree
as it is at that moment, its ``.concorde/bin/concorde`` or, in Concorde's source checkout, its
``scripts/concorde.py``, so a merge or a ``concorde update`` during the session changes the code
that answers the next call. The call's arguments and the session's provenance go to that process as
one JSON object on its standard input, and its last line of standard output is the answer.

A tool whose registration names the session's worktree, such as ``workflow_step``, runs the
``concorde`` of the worktree the session started in instead. How each tool is served, and the
server's instructions, come from ``concorde project-mcp --tools`` of the current code.

A wait a tool registered for a channel (its answer's ``watch``), such as ``concorde task wait …`` of
the primary worktree, runs as a child that dies with the server, whose printed answer or refusal
becomes the channel event. The long work a ``long_work`` tool starts, such as a merge, is the very
process the call started: having answered, it replaced itself with the work's command, so the
server reaps it and reports its exit status as the event the answer's ``work`` names.
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

from .. import formats
from .tools import ACTOR, INSTRUCTIONS, Refusal

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


def concorde_of(worktree: Path) -> tuple[list[str], dict]:
    """The worktree's own ``concorde`` command line and the environment to run it with: its
    installed command, or its checkout's script, or else this package itself."""
    environment = dict(os.environ)
    installed = Path(worktree) / ".concorde/bin/concorde"
    if installed.is_file():
        return [str(installed)], environment
    script = Path(worktree) / "scripts/concorde.py"
    if script.is_file():
        return [sys.executable, str(script)], environment
    # This package itself: make it importable for the child.
    environment["PYTHONPATH"] = os.pathsep.join(
        [str(Path(__file__).resolve().parents[3])]
        + ([environment["PYTHONPATH"]] if environment.get("PYTHONPATH") else [])
    )
    return [sys.executable, "-m", "concorde"], environment


def toplevel(folder: Path) -> Path | None:
    """The worktree ``folder`` lies in, or None outside a Git worktree."""
    try:
        found = subprocess.run(
            ["git", "-C", str(folder), "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return Path(found.stdout.strip()) if found.returncode == 0 else None


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
        # How each tool is served, from the last listing: worktree, long_work and threaded.
        self.serving: dict[str, dict] | None = None
        self.instructions = INSTRUCTIONS
        self._runtime: Path | None = None

    def runtime(self) -> Path:
        """A private temporary directory for what the calls that start merges print themselves
        before they become the merge, whose own output goes to its attempt's trace node."""
        if self._runtime is None:
            self._runtime = Path(tempfile.mkdtemp(prefix="concorde-project-mcp-"))
        return self._runtime

    def command(
        self, *words: str, worktree: Path | None = None
    ) -> tuple[list[str], dict]:
        command, environment = concorde_of(worktree or self.primary)
        return [*command, *words], environment

    # --- the tool listing -------------------------------------------------------------------

    def describe(self) -> dict | None:
        """What the current code's ``concorde project-mcp --tools`` prints, or None when its
        process gives nothing readable."""
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
            if not isinstance(value["tools"], list) or not isinstance(
                value["serving"], dict
            ):
                raise TypeError("no list of tools")
        except (OSError, subprocess.TimeoutExpired, ValueError, KeyError, TypeError):
            return None
        return value

    def tools(self) -> list[dict]:
        """The tools of the current code, none when its process gives none."""
        value = self.describe()
        if value is None:
            self.listed = None
            return []
        self.listed = value["digest"]
        self.serving = value["serving"]
        self.instructions = value.get("instructions") or INSTRUCTIONS
        return value["tools"]

    def served(self, name: str) -> dict:
        """How the tool ``name`` is served, as the current code's listing says."""
        if self.serving is None or name not in self.serving:
            self.tools()
        return (self.serving or {}).get(
            name, {"worktree": "primary", "long_work": False, "threaded": False}
        )

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
        served = self.served(name)
        worktree = (
            (toplevel(self.where) or self.primary)
            if served["worktree"] == "session"
            else self.primary
        )
        if served["long_work"]:
            reply = self.long_work(name, envelope)
        else:
            reply = self.run(name, envelope, CALL_LIMIT, worktree)
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

    def failed(
        self, name: str, argv: list[str], detail: str, where: Path | None = None
    ) -> Refusal:
        return Refusal(
            formats.link(
                f"{ACTOR} ({name})",
                "call_failed",
                f"`{shlex.join(argv)}` in {where or self.primary} {detail}",
                reason="environment",
                explanation="the server answers only with the answer of the current Concorde, "
                "which gave none",
                options=[
                    (
                        "run a `concorde` command in the primary worktree from Bash to see "
                        "whether its Concorde works"
                    ),
                    "repair the primary worktree's Concorde, then call again",
                ],
            )
        )

    def run(self, name: str, envelope: dict, limit: float, worktree: Path) -> dict:
        argv, environment = self.command(
            "project-mcp", "--call", name, worktree=worktree
        )
        try:
            done = subprocess.run(
                argv,
                cwd=worktree,
                env=environment,
                input=json.dumps(envelope, ensure_ascii=False),
                capture_output=True,
                text=True,
                timeout=limit,
                check=False,
            )
        except subprocess.TimeoutExpired:
            raise self.failed(
                name,
                argv,
                f"gave no answer within {limit:g} seconds and was stopped",
                worktree,
            ) from None
        except OSError as error:
            raise self.failed(
                name, argv, f"could not be started: {error}", worktree
            ) from None
        reply = last_answer(done.stdout)
        if reply is None:
            output = (done.stderr or done.stdout).strip()[-2000:] or "(no output)"
            raise self.failed(
                name,
                argv,
                f"exited with status {done.returncode} and printed no answer: {output}",
                worktree,
            )
        return reply

    # --- long work ---------------------------------------------------------------------------

    def long_work(self, name: str, envelope: dict) -> dict:
        """The answer of a call of a ``long_work`` tool, such as ``task_merge``, whose process,
        once it answered that it started the work, is the work, as a process of its own session
        that outlives the server."""
        runtime = self.runtime()
        with self.lock:
            number = len(list(runtime.glob("*.log"))) + 1
            messages = runtime / f"{number}-{name}.log"
            messages.touch()
        envelope = {**envelope, "long_work": {"call": messages.as_posix()}}
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
        # The answer ends when the process exits or, having started the work, became it.
        text = process.stdout.read().decode("utf-8", "replace")
        process.stdout.close()
        reply = last_answer(text)
        if reply is None or "error" in reply or not isinstance(reply.get("work"), dict):
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
        self.reap(process, reply.pop("work"))
        return reply

    def reap(self, process, work: dict) -> None:
        def reaped():
            code = process.wait()
            if not self.channel or self.closing:
                return
            output, messages = Path(work["output"]), Path(work["messages"])
            if not output.is_file() and work.get("locate"):
                # The work moved its files, as a close moves a task with the attempt's folder
                # to the history: the current code finds them where they are now.
                found = self.located(work["locate"])
                if found is not None:
                    output, messages = found
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
                f"Concorde: `{work['command']}` ended with exit status {code} "
                f"({status}). Its output ({output}, errors in {messages}):\n{body}",
                {
                    **work.get("meta", {}),
                    "event": work.get("event", "work_ended"),
                    "exit_code": str(code),
                    "status": status,
                },
            )

        threading.Thread(
            target=reaped, name=f"work {work['command']}", daemon=True
        ).start()

    def located(self, words: list[str]) -> tuple[Path, Path] | None:
        """The output files of a long work where they are now, as the current code's
        ``concorde <words>`` prints them under ``attempt``; None when it cannot tell."""
        argv, environment = self.command(*words)
        try:
            done = subprocess.run(
                argv,
                cwd=self.primary,
                env=environment,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                timeout=60,
                check=False,
            )
            attempt = json.loads(done.stdout)["attempt"]
            return Path(attempt["output"]), Path(attempt["messages"])
        except (OSError, subprocess.SubprocessError, ValueError, KeyError, TypeError):
            return None

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
                    f"{formats.render(link)}",
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
                    f"{formats.render(link)}",
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
