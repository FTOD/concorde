"""One check a merge or a ``task deliver`` runs, as a trace node of its attempt.

A check is a command, split into words as a shell would and run without a shell, in the worktree
it checks; its standard output and error go to ``output.log`` of its node, and one still running
after ``TIMEOUT`` seconds is stopped and counts as failed, so that no lock stays held for ever by a
check that hangs.
"""

from __future__ import annotations

import shlex
import subprocess
import time
from pathlib import Path

from ...kernel.tracing.node import Node

TIMEOUT = 1800
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
) -> tuple[dict, str | None]:
    """Run one check in ``cwd`` as the node ``folder``; its result and, when it failed, why."""
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
    try:
        ran = subprocess.run(
            argv,
            cwd=cwd,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=TIMEOUT,
            check=False,
        )
        code, output = ran.returncode, ran.stdout or ""
        problem = None if code == 0 else f"exited {code}"
    except subprocess.TimeoutExpired as error:
        code, output = -1, error.stdout if isinstance(error.stdout, str) else ""
        problem = f"was stopped after {TIMEOUT} s"
    except OSError as error:
        code, output = -1, ""
        problem = f"could not run: {error}"
    seconds = round(time.monotonic() - started, 3)
    with log.open("a", encoding="utf-8") as stream:
        stream.write(
            f"$ {shlex.join(argv)}\n{output}"
            f"{'' if output.endswith(chr(10)) or not output else chr(10)}"
            f"[exit {code} after {seconds} s]\n"
        )
    node.finish(
        "ok" if problem is None else "failed",
        outcome="passed" if problem is None else "failed",
        content={"argv": list(argv), "exit_code": code if code >= 0 else None},
        used={"duration_seconds": seconds},
    )
    result = {"argv": list(argv), "exit_code": code, "seconds": seconds}
    if problem is None:
        return result, None
    tail = output.strip()[-OUTPUT_TAIL:] or "(no output)"
    return result, f"the check `{shlex.join(argv)}` {problem}; its output ends: {tail}"


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


__all__ = ["OUTPUT_TAIL", "TIMEOUT", "parse", "run"]
