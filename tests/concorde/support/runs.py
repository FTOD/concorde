"""Run an Operation or recorded command in-process the way a caller in a task would.

A test names its run as ``<name> [--task <task>] [arguments]``: the task picks the worktree the run
starts in, whose workspace binding the runner reads, and ``--task`` itself never reaches the
runner, which knows no task.
"""

from __future__ import annotations

from pathlib import Path

from concorde.execution.commands import COMMANDS
from concorde.execution.runner import execute
from concorde.tasks import store


def split(argv, primary: Path, cwd: Path | None) -> tuple[str, str, list[str], Path]:
    """The kind, name, arguments and starting directory of a test's run."""
    words = list(argv)
    if "--task" in words:
        at = words.index("--task")
        task = words[at + 1]
        del words[at : at + 2]
        cwd = cwd or Path(store.load_task(primary, task)["worktree"])
    name, rest = words[0], words[1:]
    kind = "command" if name in COMMANDS else "operation"
    return kind, name, rest, cwd or primary


def run(argv, primary: Path, cwd: Path | None = None) -> tuple[int, dict]:
    kind, name, rest, where = split(argv, primary, cwd)
    return execute(kind, name, rest, cwd=where)


__all__ = ["run", "split"]
