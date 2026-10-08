"""The preparation of an unbound run's checkout before the run's first step.

A commit never holds what the project's build produces, so a check that needs the build finds
nothing in a fresh checkout. The project declares the commands that make it in
``.concorde/preparation.json``, Execution's own file beside the other trusted host configuration,
and only the copy committed in the checkout counts: the runner reads it there once the checkout
and its links exist and runs its commands in order, each in Check execution's read-only check
boundary with the checkout as the one writable place besides the command's scratch. Whatever the
checkout only links, such as the starting worktree's environments, stays read-only, and so does
every other file of the host, the starting worktree and the primary worktree included. A bound run
is never prepared: whoever prepares its workspace does that.

Each command's output is kept as ``preparation/<n>.log`` in the run's node, and each command that
ran is ``preparation`` host evidence. A file that breaks its contract, or a command that exits
non-zero, runs out of time or cannot get its boundary, is a ``PreparationError`` whose link the
runner keeps as the cause of its own: the run ends ``failed`` before any step.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from pathlib import Path

from ..kernel.errors import evidence, link
from ..kernel.refusal import KernelError
from ..kernel.schema import decode, validate
from .checks.check_executor import CheckSandboxError, execute_check
from .checks.checks import CheckError, environment, service_error

# Where a project declares its preparation, relative to the checkout's root.
PREPARATION = ".concorde/preparation.json"
# The folder of the run's node that holds each command's log.
LOGS = "preparation"
ACTOR = "Execution (unbound preparation)"
# The end of a failed command's log its link carries.
LOG_TAIL = 3000

# contract.execution.preparation, version 1
PREPARATION_SCHEMA: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": ["commands"],
    "properties": {
        "commands": {"type": "array", "items": {"$ref": "#/$defs/command"}},
    },
    "$defs": {
        "command": {
            "type": "object",
            "additionalProperties": False,
            "required": ["argv", "timeout_seconds"],
            "properties": {
                "argv": {
                    "type": "array",
                    "minItems": 1,
                    "items": {"type": "string", "minLength": 1},
                },
                "timeout_seconds": {"type": "number", "minimum": 1},
            },
        },
    },
}


class PreparationError(Exception):
    """A preparation the runner cannot carry out: ``code`` is the run's own code,
    ``preparation_invalid`` or ``preparation_failed``, and ``cause`` the link of
    ``Execution (unbound preparation)`` that says why."""

    def __init__(self, code: str, message: str, cause: dict):
        super().__init__(message)
        self.code, self.cause = code, cause


def declared(checkout: Path) -> list[dict]:
    """The commands the checkout's committed preparation file declares, none without the file;
    ``PreparationError`` ``preparation_invalid`` for a file that breaks its contract."""
    path = checkout / PREPARATION
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return []
    except (OSError, UnicodeDecodeError) as error:
        raise _invalid(f"{PREPARATION} cannot be read: {error}") from error
    try:
        value = decode(text)
        validate(value, PREPARATION_SCHEMA)
    except KernelError as error:
        where = f" at {error.field}" if getattr(error, "field", "") else ""
        raise _invalid(f"{PREPARATION} breaks its contract{where}: {error}") from error
    return value["commands"]


def _invalid(detail: str) -> PreparationError:
    return PreparationError(
        "preparation_invalid",
        detail,
        link(
            "component",
            ACTOR,
            "invalid_preparation",
            f"{detail}; the file is a JSON object whose only field, commands, lists objects "
            "with a nonempty argv of strings and a timeout_seconds of at least 1",
            reason="input",
            explanation="the runner runs only the preparation the project committed in a valid "
            "file and never guesses a command",
            options=[f"correct {PREPARATION} and commit it"],
        ),
    )


def prepare(
    checkout: Path,
    folder: Path,
    found: list[dict],
    keep: Callable[[str, str], None],
) -> None:
    """Run the checkout's preparation commands in order in its boundary, the checkout writable.

    Each command's log is written to ``folder``/``preparation/<n>.log`` and named to ``keep``
    with its identity and path relative to ``folder``; ``found`` receives the ``preparation``
    evidence of each command that ran. ``PreparationError`` for an invalid file or a failed
    command, after which no later command runs. A cancellation raised while a command runs goes
    on unchanged once its process tree has ended, its output kept in the log."""
    commands = declared(checkout)
    if not commands:
        return
    logs = folder / LOGS
    logs.mkdir(parents=True, exist_ok=True)
    for number, command in enumerate(commands, start=1):
        argv = list(command["argv"])
        shown = " ".join(argv)
        relative = f"{LOGS}/{number}.log"
        log = folder / relative
        keep(f"preparation-{number}", relative)
        started = time.monotonic()
        try:
            outcome = execute_check(
                checkout,
                argv,
                timeout=float(command["timeout_seconds"]),
                environment=environment(),
                writable_project=True,
            )
        except CheckSandboxError as error:
            log.write_bytes(
                (error.stdout or b"")
                + b"\n"
                + (error.stderr or b"")
                + str(error).encode()
            )
            found.append(evidence("preparation", shown, f"not started: {error}"))
            refusal = CheckError(
                f"the preparation command {shown} could not run in its boundary: {error}",
                "check_sandbox_unavailable",
            )
            raise PreparationError(
                "preparation_failed",
                f"the preparation command {number}, {shown}, could not get its boundary: "
                f"{error}",
                link(
                    "component",
                    ACTOR,
                    "preparation_sandbox_unavailable",
                    f"the preparation command {number} of {PREPARATION}, {shown}, could not "
                    f"start in {checkout}, since its boundary could not be set up: {error}; "
                    f"log {log}",
                    reason="environment",
                    explanation="a preparation command runs only inside Check execution's "
                    "boundary, with the checkout as its one writable place",
                    evidence=[evidence("log", log.as_posix(), "")],
                    causes=[service_error(refusal)],
                ),
            ) from error
        except BaseException as error:
            stdout, stderr = getattr(error, "check_output", (b"", b""))
            log.write_bytes(stdout + b"\n" + stderr)
            raise
        log.write_bytes(outcome.stdout + b"\n" + outcome.stderr)
        seconds = time.monotonic() - started
        if not outcome.timed_out and outcome.returncode == 0:
            found.append(
                evidence(
                    "preparation",
                    shown,
                    f"command {number} of {PREPARATION} exited 0 in {seconds:.1f} s; log {log}",
                )
            )
            continue
        ended = (
            f"ran out of its {command['timeout_seconds']:g} s"
            if outcome.timed_out
            else f"exited {outcome.returncode}"
        )
        found.append(
            evidence(
                "preparation",
                shown,
                f"command {number} of {PREPARATION} {ended} after {seconds:.1f} s; log {log}",
            )
        )
        tail = log.read_bytes()[-LOG_TAIL:].decode("utf-8", "replace").strip()
        raise PreparationError(
            "preparation_failed",
            f"the preparation command {number}, {shown}, {ended}; log {log}",
            link(
                "component",
                ACTOR,
                "preparation_timed_out"
                if outcome.timed_out
                else "preparation_command_failed",
                f"the preparation command {number} of {PREPARATION}, {shown}, {ended} in "
                f"{checkout}; its log {log} ends with:\n{tail or '(empty)'}",
                reason="input",
                explanation="the command and the commit it prepares are the project's, which "
                "the runner neither repairs nor works around",
                evidence=[evidence("log", log.as_posix(), "")],
                options=[
                    f"repair what the log shows, or the command in {PREPARATION}, commit, "
                    "and run again"
                ],
            ),
        )


__all__ = [
    "PREPARATION",
    "PREPARATION_SCHEMA",
    "PreparationError",
    "declared",
    "prepare",
]
