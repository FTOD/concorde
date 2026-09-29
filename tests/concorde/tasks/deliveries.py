"""Delivery commits and run store entries for task tests that need them without running delivery.

A delivery commit is the only record of a delivery: ``deliver`` commits a change in a task worktree
with the subject and body ``concorde delivery`` writes, so the task level reads it back from Git as
a real one that verifies, or, asked to, as one that does not. ``write_run`` places a run result or
progress file in the run store of the primary worktree, as the Execution runner would.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from concorde.delivery.commits import commit_message
from concorde.execution import binding

FIXED = "def add(a, b):\n    return a + b\n"
IDENTITY = ("-c", "user.name=t", "-c", "user.email=t@t")


def git(root: Path, *arguments: str, stdin: str | None = None) -> str:
    return subprocess.run(
        ["git", *arguments],
        cwd=root,
        input=stdin,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def deliver(
    worktree: Path,
    path: str = "src/a/calc.py",
    text: str = FIXED,
    *,
    verifies: bool = True,
) -> str:
    """Change ``path`` in the bound ``worktree`` and commit it as the workspace's next delivery
    commit; the new head.

    The commit verifies by default; with ``verifies`` false it gets a second parent, a side
    commit, as a merge given the delivery subject would, so it does not."""
    bound = binding.load(worktree)
    head = git(worktree, "rev-parse", "HEAD")
    (worktree / path).write_text(text)
    git(worktree, "add", "-A")
    message = commit_message(bound)
    if verifies:
        git(
            worktree,
            *IDENTITY,
            "commit",
            "-q",
            "--cleanup=verbatim",
            "-F",
            "-",
            stdin=message,
        )
        return git(worktree, "rev-parse", "HEAD")
    tree = git(worktree, "write-tree")
    side = git(
        worktree, *IDENTITY, "commit-tree", f"{head}^{{tree}}", "-p", head, "-m", "side"
    )
    commit = git(
        worktree, *IDENTITY, "commit-tree", tree, "-p", head, "-p", side, stdin=message
    )
    git(worktree, "update-ref", "HEAD", commit)
    return commit


def write_run(
    primary: Path,
    run_id: str,
    workspace: str | None,
    *,
    name: str = "understand",
    kind: str = "operation",
    modules=("module.a",),
    status: str | None = "ok",
    host_pid: int = 0,
    traces: Path | None = None,
) -> Path:
    """A finished run's ``result.json`` (``status`` given) or a running run's ``status.json``
    (``status`` None) in the run store of ``primary``: the workspace folder of the task named
    ``workspace``, or ``.concorde/unbound/`` for an unbound run, or the workspace folder
    ``traces`` when given. A running run is running only while a test holds its run lock
    (``concorde.tracing.locks.hold`` of its lock file)."""
    concorde = primary / ".concorde"
    if traces is not None:
        directory = Path(traces) / "runs" / run_id
    elif workspace is None:
        directory = concorde / "unbound" / run_id
    else:
        directory = concorde / "tasks" / workspace / "workspace" / "runs" / run_id
    directory.mkdir(parents=True, exist_ok=True)
    stamp = "2026-09-27T00:00:00Z"
    if status is None:
        path = directory / "status.json"
        value = {
            "kind": kind,
            "run_id": run_id,
            "name": name,
            "workspace": workspace,
            "worktree": str(primary),
            "modules": list(modules),
            "host_pid": host_pid,
            "phase": "running",
            "status": None,
            "started_at": stamp,
            "updated_at": stamp,
        }
    else:
        path = directory / "result.json"
        value = {
            "kind": kind,
            "name": name,
            "workspace": workspace,
            "modules": list(modules),
            "run_id": run_id,
            "status": status,
            "summary": f"{name} ended {status}.",
            "output": None,
            "worker": None,
            "worker_runs": [],
            "host_evidence": [],
            "error": None,
            "started_at": stamp,
            "finished_at": stamp,
        }
    path.write_text(json.dumps(value, indent=2) + "\n")
    return path


__all__ = ["FIXED", "deliver", "git", "write_run"]
