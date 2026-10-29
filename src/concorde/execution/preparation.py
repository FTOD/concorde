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

A preparation writes only what the examined commit's Git ignores, such as build output: the run
examines the commit, so the tracked files, the Specs, the code and the worker configuration among
them, stay as committed, and no file appears that the commit's Git would list. The runner reads the
Git status of the checkout and of each submodule checked out in it on its own, before the first
command and after the last, each time from a fresh index of the repository's ``HEAD``, so Git
compares every tracked file's content rather than its timestamps, and with the Git directory it
read before any command ran, never a ``.git`` file as a command left it. A new ``.gitignore``
counts only where the commit's own rules already ignore its directory, so a command cannot hide a
file by ignoring it, and a submodule that is not checked out must stay empty. Any difference is
``preparation_changed_commit``.

Each command's output is kept as ``preparation/<n>.log`` in the run's node, and each command that
ran is ``preparation`` host evidence; the comparison is ``preparation-check`` host evidence. A file
that breaks its contract, a command that exits non-zero, runs out of time or cannot get its
boundary, or a preparation that changed what the commit holds, is a ``PreparationError`` whose link
the runner keeps as the cause of its own: the run ends ``failed`` before any step.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import time
from collections.abc import Callable
from dataclasses import dataclass
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
# How many changed paths a preparation_changed_commit link names.
SHOWN_CHANGES = 20
# Git never runs a hook of the repository for the checkout.
GIT = ("git", "-c", "core.hooksPath=/dev/null")

# contract.execution.preparation, version 2
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
    layout = _layout(checkout)
    before = _state(checkout, layout)
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
    _unchanged(checkout, layout, before, found)


class _Unverified(Exception):
    """Git could not tell what the checkout holds."""


def _run_git(
    checkout: Path,
    git_dir: str,
    index: Path | None,
    *arguments: str,
    given: str | None = None,
) -> bytes:
    environment = {
        key: value for key, value in os.environ.items() if not key.startswith("GIT_")
    }
    environment.update(
        GIT_DIR=git_dir, GIT_WORK_TREE=checkout.as_posix(), GIT_OPTIONAL_LOCKS="0"
    )
    if index is not None:
        environment["GIT_INDEX_FILE"] = index.as_posix()
    try:
        result = subprocess.run(
            [*GIT, *arguments],
            cwd=checkout,
            input=None if given is None else given.encode("utf-8", "surrogateescape"),
            capture_output=True,
            check=False,
            env=environment,
        )
    except OSError as error:
        raise _Unverified(
            f"git {' '.join(arguments)} could not start: {error}"
        ) from error
    # check-ignore exits 1 when it matched nothing, which is an answer.
    if result.returncode != 0 and not (
        arguments[0] == "check-ignore" and result.returncode == 1
    ):
        said = (result.stderr or result.stdout).decode("utf-8", "replace").strip()
        raise _Unverified(
            f"git {' '.join(arguments)} exited {result.returncode}: {said or 'no output'}"
        )
    return result.stdout


def _git_dir(work_tree: Path) -> str:
    """The Git directory of the repository checked out at ``work_tree``, read before any command
    could change its ``.git`` file; ``_Unverified`` unless ``work_tree`` is that repository's
    own top level."""
    environment = {
        key: value for key, value in os.environ.items() if not key.startswith("GIT_")
    }
    try:
        result = subprocess.run(
            [*GIT, "rev-parse", "--absolute-git-dir", "--show-toplevel"],
            cwd=work_tree,
            capture_output=True,
            text=True,
            check=False,
            env=environment,
        )
    except OSError as error:
        raise _Unverified(f"git rev-parse could not start: {error}") from error
    lines = result.stdout.splitlines()
    if result.returncode != 0 or len(lines) != 2:
        said = (result.stderr or result.stdout).strip() or "no output"
        raise _Unverified(
            f"git rev-parse --absolute-git-dir in {work_tree} exited "
            f"{result.returncode}: {said}"
        )
    if os.path.realpath(lines[1]) != os.path.realpath(work_tree):
        raise _Unverified(
            f"{work_tree} holds a .git, yet Git finds the top level {lines[1]} for it"
        )
    return lines[0]


@dataclass(frozen=True)
class _Layout:
    """The repositories of a checkout, read before any command ran: each checked-out one as its
    path relative to the checkout (empty for the checkout itself) with its Git directory, and
    the path of each submodule no repository is checked out at."""

    repositories: tuple[tuple[str, str], ...]
    empty: tuple[str, ...]


def _layout(checkout: Path) -> _Layout:
    """The checkout's repositories, its submodules and theirs included: a submodule whose
    directory holds a ``.git`` is a repository of its own, read with the Git directory found
    now; any other is an empty directory, as in a fresh clone."""
    try:
        repositories = [("", _git_dir(checkout))]
        empty: list[str] = []
        for prefix, git_dir in repositories:
            tree = _run_git(
                _inside(checkout, prefix), git_dir, None, "ls-tree", "-r", "-z", "HEAD"
            )
            for record in tree.split(b"\0"):
                head, _, name = record.partition(b"\t")
                if not head.startswith(b"160000 "):
                    continue
                path = _joined(prefix, name.decode("utf-8", "surrogateescape"))
                if os.path.lexists(checkout / path / ".git"):
                    repositories.append((path, _git_dir(checkout / path)))
                else:
                    empty.append(path)
    except _Unverified as error:
        raise _unverified(checkout, str(error)) from error
    return _Layout(tuple(repositories), tuple(empty))


def _inside(checkout: Path, prefix: str) -> Path:
    return checkout / prefix if prefix else checkout


def _joined(prefix: str, path: str) -> str:
    return f"{prefix}/{path}" if prefix else path


def _state(checkout: Path, layout: _Layout) -> frozenset[str]:
    """What the checkout holds beyond what the commit's Git ignores, each submodule read on its
    own with the Git directory of the layout: each repository's readings and, for a submodule
    no repository is checked out at, each entry its directory holds."""
    entries: set[str] = set()
    for prefix, git_dir in layout.repositories:
        entries |= _repository_state(checkout, prefix, git_dir)
    for path in layout.empty:
        try:
            names = os.listdir(checkout / path)
        except FileNotFoundError:
            names = []
        except OSError as error:
            raise _unverified(
                checkout, f"the submodule directory {path} cannot be listed: {error}"
            ) from error
        entries |= {
            f"?? {path}/{name} (in a submodule that is not checked out)"
            for name in names
        }
    return frozenset(entries)


def _repository_state(checkout: Path, prefix: str, git_dir: str) -> set[str]:
    """One repository's reading, its paths relative to the checkout: each status entry, against
    a fresh index of its ``HEAD`` so that Git compares contents, each new ``.gitignore`` whose
    directory its commit's own rules do not ignore, and the bytes of its ``.git`` file. Its
    submodules are left to their own readings, never reached through their ``.git`` files."""
    work_tree = _inside(checkout, prefix)
    try:
        with tempfile.TemporaryDirectory(prefix="concorde-preparation-") as scratch:
            index = Path(scratch) / "index"
            _run_git(work_tree, git_dir, index, "read-tree", "HEAD")
            status = _run_git(
                work_tree,
                git_dir,
                index,
                "status",
                "--porcelain=v1",
                "-z",
                "--untracked-files=all",
                "--ignore-submodules=all",
                "--no-renames",
            )
            entries = {
                _relocated(prefix, entry.decode("utf-8", "surrogateescape"))
                for entry in status.split(b"\0")
                if entry
            }
            others = _run_git(work_tree, git_dir, index, "ls-files", "-z", "--others")
            folders = sorted(
                {
                    path.decode("utf-8", "surrogateescape").rpartition("/")[0]
                    for path in others.split(b"\0")
                    if path == b".gitignore" or path.endswith(b"/.gitignore")
                }
            )
            ignored: set[str] = set()
            # Asked without a trailing slash, Git judges a directory by the rules above it alone,
            # never by the .gitignore it holds.
            asked = [folder for folder in folders if folder]
            if asked:
                answer = _run_git(
                    work_tree,
                    git_dir,
                    index,
                    "check-ignore",
                    "--no-index",
                    "-z",
                    "--stdin",
                    given="\0".join(asked) + "\0",
                )
                ignored = {
                    path.decode("utf-8", "surrogateescape")
                    for path in answer.split(b"\0")
                    if path
                }
            for folder in folders:
                if folder not in ignored:
                    entries.add(
                        f"?? {_joined(prefix, _joined(folder, '.gitignore'))} (hides files)"
                    )
    except _Unverified as error:
        raise _unverified(checkout, str(error)) from error
    except OSError as error:
        raise _unverified(
            checkout, f"a temporary index could not be made: {error}"
        ) from error
    marker = _joined(prefix, ".git")
    try:
        entries.add(f"{GIT_FILE}{marker}\0{(checkout / marker).read_bytes().hex()}")
    except OSError as error:
        entries.add(f"{GIT_FILE}{marker}\0unreadable: {error.strerror}")
    return entries


# What starts the entry of a repository's ``.git`` file, never a status entry's start.
GIT_FILE = "git-file "


def _relocated(prefix: str, entry: str) -> str:
    """A porcelain status entry ``XY path`` of the repository at ``prefix``, its path made
    relative to the checkout."""
    return entry[:3] + _joined(prefix, entry[3:]) if prefix else entry


def _unchanged(
    checkout: Path, layout: _Layout, before: frozenset[str], found: list[dict]
) -> None:
    """``PreparationError`` ``preparation_failed`` when the commands changed what the checkout
    holds beyond what the commit's Git ignores; ``preparation-check`` evidence either way."""
    after = _state(checkout, layout)
    changed = [_shown(entry) for entry in sorted(after - before)]
    if not changed:
        found.append(
            evidence(
                "preparation-check",
                "git status",
                "the checkout and each of its submodules hold the commit's tracked files "
                "unchanged and no untracked file the commit's Git does not ignore",
            )
        )
        return
    listed = "; ".join(changed[:SHOWN_CHANGES]) + (
        f"; and {len(changed) - SHOWN_CHANGES} more"
        if len(changed) > SHOWN_CHANGES
        else ""
    )
    found.append(evidence("preparation-check", "git status", f"changed: {listed}"))
    raise PreparationError(
        "preparation_failed",
        f"the preparation commands of {PREPARATION} changed what the examined commit holds: "
        f"{listed}",
        link(
            "component",
            ACTOR,
            "preparation_changed_commit",
            f"after the preparation commands of {PREPARATION} ran in {checkout}, Git status "
            f"against the examined commit differs from before them: {listed}; a preparation "
            "may write only paths the commit's Git ignores",
            reason="input",
            explanation="the run examines the commit, so its steps and workers must read the "
            "tracked files as committed, and the runner neither restores nor accepts a change",
            options=[
                "make the preparation write only paths the commit's .gitignore ignores, or "
                "ignore them there, commit, and run again"
            ],
        ),
    )


def _shown(entry: str) -> str:
    if entry.startswith(GIT_FILE):
        return entry[len(GIT_FILE) :].partition("\0")[0] + " file of the checkout"
    return entry


def _unverified(checkout: Path, detail: str) -> PreparationError:
    return PreparationError(
        "preparation_failed",
        f"Git could not tell what the checkout {checkout} holds: {detail}",
        link(
            "component",
            ACTOR,
            "preparation_unverified",
            f"Git could not compare the checkout {checkout} with the examined commit around "
            f"the preparation commands of {PREPARATION}: {detail}",
            reason="environment",
            explanation="the runner runs no step on a prepared checkout it cannot compare with "
            "the commit the run examines",
            options=["repair what Git reports and run again"],
        ),
    )


__all__ = [
    "PREPARATION",
    "PREPARATION_SCHEMA",
    "PreparationError",
    "declared",
    "prepare",
]
