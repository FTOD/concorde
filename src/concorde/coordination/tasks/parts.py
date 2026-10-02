"""The parts Tasks relies on without depending on them, reached only through what they publish.

The coordination part depends on the kernel alone (``specs/concorde/coordination/module.md``,
Optional integrations). Every other part it uses is an optional integration, reached through that
part's ``concorde`` command, JSON in and out, or read through a file format that part's Spec
defines, and never through its Python code:

- Spec core (the spec part) through its registry mirror ``.concorde/specs.json``: the spec part is
  installed for a worktree exactly when that file exists, the same rule Issues uses;
- Distribution through its update mark ``.concorde/update.json``;
- Issues (the issues part) through ``concorde issues``;
- Execution and Method through whether ``concorde`` offers their commands, ``run`` and
  ``delivery``, and Execution's run store through its formats (``runs.py``).

A part is absent from an installation when the worktree's own ``concorde`` does not offer its
command: Distribution's ``concorde`` refuses a command of a part the project has not installed by
printing ``{"error": <link>}`` with the code ``part_missing`` (``ABSENT_CODE``) and exiting with
status 1. Any other answer, a refusal of the arguments included, means the command is offered.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from contextlib import nullcontext
from dataclasses import dataclass
from pathlib import Path

from ...kernel.tracing import locks

# Spec core's registry mirror, whose existence tells that the spec part is installed.
REGISTRY = ".concorde/specs.json"
# Distribution's mark of an update not validated since.
UPDATE_MARK = ".concorde/update.json"
# The code by which ``concorde`` refuses a command of a part the project has not installed.
ABSENT_CODE = "part_missing"
# How long one call of another part's command may take: a write waits up to 300 s for the merge
# lock, and an Issue write commits.
TIMEOUT = 900
# How long asking whether a command is offered may take.
PROBE_TIMEOUT = 120
# The part each command belongs to, as the refusals name it.
PARTS = {"run": "execution", "delivery": "method", "issues": "issues"}


class Absent(Exception):
    """The part whose command was called is not installed."""

    def __init__(self, part: str, command: str):
        super().__init__(
            f"the {part} part is not installed: `concorde {command}` is not offered"
        )
        self.part = part


class Failed(Exception):
    """The command could not run to its end, or answered no JSON: ``detail`` says how."""


@dataclass(frozen=True)
class Answer:
    """What a command answered: its exit status and its JSON value, None for no output."""

    status: int
    value: object

    @property
    def error(self) -> dict | None:
        """The error link of a refusal, ``{"error": <link>}``, else None."""
        if isinstance(self.value, dict) and isinstance(self.value.get("error"), dict):
            return self.value["error"]
        return None


def concorde_command(worktree: Path) -> list[str]:
    """The worktree's own ``concorde``: its installed command, or this checkout's script, or this
    package run by this Python."""
    installed = Path(worktree) / ".concorde/bin/concorde"
    if installed.is_file():
        return [str(installed)]
    script = Path(worktree) / "scripts/concorde.py"
    if script.is_file():
        return [sys.executable, str(script)]
    return [sys.executable, "-m", "concorde"]


def _environment(command: list[str], extra: dict | None = None) -> dict:
    environment = dict(os.environ)
    if command[1:3] == ["-m", "concorde"]:
        # This package itself: make it importable for the child.
        package = str(Path(__file__).resolve().parents[3])
        environment["PYTHONPATH"] = os.pathsep.join(
            item for item in (package, environment.get("PYTHONPATH")) if item
        )
    environment.update(extra or {})
    return environment


def _absent(completed: subprocess.CompletedProcess, value) -> bool:
    """Whether ``concorde`` refused the command as one of a part that is not installed."""
    if completed.returncode != 1 or not isinstance(value, dict):
        return False
    error = value.get("error")
    return isinstance(error, dict) and error.get("code") == ABSENT_CODE


def _decoded(text: str):
    try:
        return json.loads(text) if text.strip() else None
    except ValueError:
        return None


def call(
    worktree: Path,
    words: list[str],
    *,
    handing: tuple[Path, ...] = (),
    timeout: float = TIMEOUT,
) -> Answer:
    """``concorde <words>`` of ``worktree``, run there; ``Absent`` when the command's part is not
    installed, ``Failed`` when it could not run or answered no JSON. ``handing`` names locks this
    process holds that the command takes, handed on to it as Tracing's "Handing a lock on" says."""
    command = concorde_command(worktree)
    argv = [*command, *words]
    shown = " ".join(["concorde", *words])
    handed = locks.handed_on(*handing) if handing else nullcontext(({}, ()))
    try:
        with handed as (variables, descriptors):
            completed = subprocess.run(
                argv,
                cwd=worktree,
                env=_environment(command, variables),
                pass_fds=descriptors,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise Failed(
            f"`{shown}` in {worktree} could not run to its end: "
            f"{type(error).__name__}: {error}"
        ) from error
    value = _decoded(completed.stdout)
    if _absent(completed, value):
        raise Absent(PARTS.get(words[0], words[0]), words[0])
    if value is None:
        raise Failed(
            f"`{shown}` in {worktree} exited {completed.returncode} without a JSON answer: "
            f"{(completed.stdout + completed.stderr).strip()[-2000:] or '(no output)'}"
        )
    return Answer(completed.returncode, value)


def offers(worktree: Path, command: str) -> bool:
    """Whether the worktree's own ``concorde`` offers ``command``, that is whether its part is
    installed; ``Failed`` when ``concorde`` could not be asked. It asks for the command's help,
    which changes nothing, and judges only whether the command was refused as absent."""
    concorde = concorde_command(worktree)
    try:
        completed = subprocess.run(
            [*concorde, command, "--help"],
            cwd=worktree,
            env=_environment(concorde),
            capture_output=True,
            text=True,
            timeout=PROBE_TIMEOUT,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise Failed(
            f"asking `concorde {command} --help` in {worktree} whether the {PARTS[command]} "
            f"part is installed could not run to its end: {type(error).__name__}: {error}"
        ) from error
    return not _absent(completed, _decoded(completed.stdout))


def registry_modules(root: Path) -> set[str] | None:
    """The Modules the registry mirror of ``root`` lists, or None where the spec part is not
    installed, as the mirror's absence tells; ``ValueError`` names a mirror that does not read."""
    path = Path(root) / REGISTRY
    if not path.exists() and not path.is_symlink():
        return None
    try:
        modules = json.loads(path.read_text(encoding="utf-8"))["modules"]
        found = {module["id"] for module in modules}
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise ValueError(f"the registry {path} cannot be read: {error}") from error
    if not all(isinstance(item, str) for item in found):
        raise ValueError(f"the registry {path} names a Module whose id is no string")
    return found


def spec_installed(root: Path) -> bool:
    """Whether the spec part is installed for the worktree ``root``: its registry mirror exists."""
    path = Path(root) / REGISTRY
    return path.exists() or path.is_symlink()


def update_unvalidated(primary: Path) -> bool:
    """Whether Distribution's mark says an update of the primary worktree is not validated yet."""
    return (Path(primary) / UPDATE_MARK).is_file()


__all__ = [
    "ABSENT_CODE",
    "REGISTRY",
    "UPDATE_MARK",
    "Absent",
    "Answer",
    "Failed",
    "call",
    "concorde_command",
    "offers",
    "registry_modules",
    "spec_installed",
    "update_unvalidated",
]
