"""Delivery commits and run store entries for task tests that need them without running delivery.

A delivery commit is the only record of a delivery: ``deliver`` commits a change in a task worktree
with the subject and trailers ``concorde delivery`` writes, so the task level reads it back from
Git as a real one. ``write_run`` places a run result or progress file in the run store of the
primary worktree, as the Execution runner would.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from concorde.delivery.bundle import bundle_path, commit_message, delivery_commits
from concorde.execution import binding

READINESS_RUN = "r-20260927T000000-task_validation-0000000a"
FIXED = "def add(a, b):\n    return a + b\n"


def git(root: Path, *arguments: str, stdin: str | None = None) -> str:
    return subprocess.run(
        ["git", *arguments],
        cwd=root,
        input=stdin,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def deliver(worktree: Path, path: str = "src/a/calc.py", text: str = FIXED) -> str:
    """Change ``path`` in the bound ``worktree`` and commit it as the workspace's next delivery
    commit; the new head."""
    bound = binding.load(worktree)
    head = git(worktree, "rev-parse", "HEAD")
    sequence = (
        len(delivery_commits(worktree, bound["base_commit"], head, bound["workspace"]))
        + 1
    )
    (worktree / path).write_text(text)
    git(worktree, "add", "-A")
    git(
        worktree,
        "-c",
        "user.name=t",
        "-c",
        "user.email=t@t",
        "commit",
        "-q",
        "--cleanup=verbatim",
        "-F",
        "-",
        stdin=commit_message(
            bound, bundle_path(bound["workspace"], sequence), READINESS_RUN
        ),
    )
    return git(worktree, "rev-parse", "HEAD")


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
) -> Path:
    """A finished run's ``result.json`` (``status`` given) or a running run's ``status.json``
    (``status`` None) in the run store of ``primary``."""
    directory = primary / ".concorde/runs" / run_id
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


__all__ = ["FIXED", "READINESS_RUN", "deliver", "git", "write_run"]
