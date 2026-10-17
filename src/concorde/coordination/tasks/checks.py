"""One check a merge or a ``task deliver`` runs, as a trace node of its attempt.

A check is a command, split into words as a shell would and run without a shell, in the worktree
it checks; its standard output and error go to ``output.log`` of its node, and one still running
after ``TIMEOUT`` seconds is stopped and counts as failed, so that no lock stays held for ever by a
check that hangs. Each check runs as a process group of its own, which is killed whole when the
check ends, so no process it started writes on after its caller goes on.
"""

from __future__ import annotations

import os
import shlex
import signal
import subprocess
import tempfile
import time
from pathlib import Path

from ...kernel.tracing.node import Node
from .store import TaskError

TIMEOUT = 1800
# How long the end of a check waits for the processes of its group to be gone once killed.
REAP_WAIT = 10.0
# How much of a failed check's output a refusal quotes; the log holds all of it.
OUTPUT_TAIL = 2000


def run(
    cwd: Path,
    argv: list[str],
    folder: Path,
    *,
    identity: str,
    kind: str,
    content_type: str,
    environment: dict | None = None,
    failures: list[str] | None = None,
) -> tuple[dict, str | None]:
    """Run one check in ``cwd`` as the node ``folder``; its result and, when it failed, why.
    Each write of the node's ``trace.json`` the file system refused is added to ``failures``,
    for the caller to report."""
    node = Node(
        folder,
        identity,
        kind,
        content_type=content_type,
        content={"argv": list(argv), "exit_code": None},
    )
    node.keep("output", "output.log")
    node.start()
    log = folder / "output.log"
    started = time.monotonic()
    code, output, problem = _execute(cwd, argv, environment)
    seconds = round(time.monotonic() - started, 3)
    # The node's own write makes the folder; the log is kept even when that write failed, and a
    # log the file system refuses is reported like a refused node write.
    unlogged = None
    try:
        folder.mkdir(parents=True, exist_ok=True)
        with log.open("a", encoding="utf-8") as stream:
            stream.write(
                f"$ {shlex.join(argv)}\n{output}"
                f"{'' if output.endswith(chr(10)) or not output else chr(10)}"
                f"[exit {code} after {seconds} s]\n"
            )
    except OSError as error:
        unlogged = (
            f"the check log {log} could not be written: {type(error).__name__}: {error}"
        )
    node.finish(
        "ok" if problem is None else "failed",
        outcome="passed" if problem is None else "failed",
        content={"argv": list(argv), "exit_code": code if code >= 0 else None},
        used={"duration_seconds": seconds},
    )
    if failures is not None:
        failures.extend([*node.failures, *([unlogged] if unlogged else [])])
    result = {"argv": list(argv), "exit_code": code, "seconds": seconds}
    if problem is None:
        return result, None
    tail = output.strip()[-OUTPUT_TAIL:] or "(no output)"
    return result, f"the check `{shlex.join(argv)}` {problem}; its output ends: {tail}"


def _execute(
    cwd: Path, argv: list[str], environment: dict | None
) -> tuple[int, str, str | None]:
    """Run ``argv`` as a process group of its own; its exit status, its output and, when it
    failed, why. The output goes to a file rather than a pipe, so a process the check left
    holding its output never keeps the check from ending."""
    with tempfile.TemporaryFile() as captured:
        try:
            process = subprocess.Popen(
                argv,
                cwd=cwd,
                env=environment,
                stdin=subprocess.DEVNULL,
                stdout=captured,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
        except OSError as error:
            return -1, "", f"could not run: {error}"
        try:
            code = process.wait(timeout=TIMEOUT)
            problem = None if code == 0 else f"exited {code}"
        except subprocess.TimeoutExpired:
            code, problem = -1, f"was stopped after {TIMEOUT} s"
        finally:
            # Also after a normal exit: a process the check started in the background must not
            # write on after the check ended.
            left = _kill_group(process)
        if left:
            problem = (
                f"{problem or 'passed'}, but processes of its group were still alive "
                f"{REAP_WAIT:g} s after they were killed"
            )
        captured.seek(0)
        output = captured.read().decode("utf-8", "replace")
    return code, output, problem


def _kill_group(process: subprocess.Popen) -> bool:
    """Kill the check's process group and wait for it to be gone; True when processes of the
    group are still alive after ``REAP_WAIT`` seconds."""
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    process.wait()
    deadline = time.monotonic() + REAP_WAIT
    while True:
        try:
            os.killpg(process.pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            # A member that changed its user: it can no longer be told apart from the group's
            # end, so it counts as alive.
            pass
        if time.monotonic() >= deadline:
            return True
        time.sleep(0.05)


def with_failures(refusal: TaskError, failures: list[str]) -> TaskError:
    """``refusal``, its detail naming each write of a trace node that failed, which a refusal
    reports as an answer reports them among its warnings."""
    if not failures:
        return refusal
    return TaskError(
        refusal.code,
        f"{refusal}; besides, its trace is incomplete: " + "; ".join(failures),
    )


def parse(texts: list[str], invalid) -> list[list[str]]:
    """The ``--check`` texts split into words as a shell would; ``invalid(message)`` makes the
    refusal of one that cannot be split or names no command."""
    found = []
    for text in texts:
        try:
            words = shlex.split(text)
        except ValueError as error:
            raise invalid(
                f"--check {text!r} cannot be split into words: {error}"
            ) from error
        if not words:
            raise invalid(f"--check {text!r} names no command")
        found.append(words)
    return found


__all__ = ["OUTPUT_TAIL", "TIMEOUT", "parse", "run", "with_failures"]
