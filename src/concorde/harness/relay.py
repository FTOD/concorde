"""Workspace binding of an admitted request and its relay into a host-created candidate."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from ..spec.repository import SpecError
from ..spec.typed_data import canonical, decode
from .change_worktree import (
    create_worktree,
    ensure_change,
    read_change,
    refresh_registry,
    workspace_identity,
)
from .host import OperationHost

# An installed consumer keeps the framework below this project-relative root (the installer's
# FRAMEWORK_ROOT); a source checkout is its own framework.
INSTALLED_FRAMEWORK_ROOT = ".concorde/framework"
# How long a relayed launcher may cancel its worker after the host was interrupted.
RELAY_GRACE_SECONDS = 30


def candidate_by_change_id(root: Path, change_id: str) -> dict | None:
    """The one live managed candidate of ``change_id`` in the primary's inventory, or None."""
    inventory = refresh_registry(root, persist=False)
    matches = [
        item
        for item in inventory["worktrees"]
        if item["managed"] and item["change_id"] == change_id
    ]
    return matches[0] if len(matches) == 1 else None


def relay_launcher(host: OperationHost, candidate: Path) -> list[str]:
    """The launcher that runs an operation inside ``candidate``.

    A candidate that carries its own Concorde, the source checkout itself or a consumer project
    whose installed framework is tracked, runs that code, so a change to Concorde is exercised by
    the candidate's own framework. Otherwise the invoking framework runs with the candidate as its
    project root."""
    for framework in (candidate, candidate / INSTALLED_FRAMEWORK_ROOT):
        launcher = framework / "scripts/run-operation.py"
        if launcher.is_file() and (framework / "src/concorde").is_dir():
            return [sys.executable, str(launcher)]
    return [sys.executable, str(host.package_root / "scripts/run-operation.py")]


def relay_operation(
    host: OperationHost, operation: str, invocation: dict, candidate: Path
) -> tuple[dict, str]:
    """Run ``invocation`` with the candidate worktree's launcher; return its envelope and stderr.

    A self-hosted candidate is rebuilt from its own sources first, because its generated
    instructions are untracked and its sources may have changed since it was created. A host
    interrupt reaches the launcher as SIGTERM, which cancels its worker and prints its result;
    only a launcher that does not finish within the grace period is killed."""
    if (candidate / "concorde.json").is_file() and (
        candidate / "src/concorde"
    ).is_dir():
        from ..distribution.build import verify_fresh

        verify_fresh(candidate)
    argv = [*relay_launcher(host, candidate), operation]
    environment = {
        key: value for key, value in os.environ.items() if key != "CONCORDE_STUDIO_URL"
    }
    import signal
    import subprocess

    process = subprocess.Popen(
        argv,
        cwd=str(candidate),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=environment,
    )
    try:
        stdout, stderr = process.communicate(canonical(invocation))
    except KeyboardInterrupt:
        process.send_signal(signal.SIGTERM)
        try:
            stdout, stderr = process.communicate(timeout=RELAY_GRACE_SECONDS)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
    try:
        envelope = decode(stdout)
    except Exception:  # any non-envelope output is the same failure
        envelope = None
    if (
        not isinstance(envelope, dict)
        or envelope.get("type_id") != "concorde-operation-result"
    ):
        detail = stderr.strip()[-2000:] or stdout.strip()[-2000:]
        raise SpecError(
            "the candidate worktree's launcher returned no result envelope"
            + (f": {detail}" if detail else f" (exit code {process.returncode})"),
            "relay_failed",
        )
    return envelope, stderr


def bind_worktree(
    host: OperationHost, mutation: bool, task: dict
) -> tuple[OperationHost, dict | None]:
    primary, current = workspace_identity(host.project_root)
    in_primary = (
        current is not None
        and primary is not None
        and current["path"] == primary["path"]
    )
    if task.get("change_id") is not None:
        state = read_change(host.project_root)
        if state is None and in_primary and host.mode == "execute":
            # From the primary worktree a recorded change continues in its own candidate.
            candidate = candidate_by_change_id(host.project_root, task["change_id"])
            if candidate is not None:
                return host, {
                    "path": candidate["path"],
                    "branch": candidate["branch"],
                    "change_id": task["change_id"],
                    "primary_worktree": primary["path"] if primary else None,
                    "relay": True,
                }
        if state is None:
            # No candidate records this change here or in the inventory: missing_change.
            state = read_change(host.project_root, required=True)
        if task["change_id"] != state["change_id"]:
            raise SpecError(
                "change ID does not own this worktree", "incompatible_handoff"
            )
    if host.mode == "describe-policy":
        return host, None
    if (
        current is not None
        and primary is not None
        and current["path"] != primary["path"]
    ):
        state = ensure_change(
            host.project_root,
            task=task if mutation else None,
            change_id=task.get("change_id"),
        )
        refresh_registry(host.project_root)
        return host, {
            key: state[key]
            for key in (
                "path",
                "branch",
                "base_commit",
                "change_id",
                "primary_worktree",
            )
        }
    if (
        mutation
        and in_primary
        and host.package_root == host.project_root
        and (host.project_root / "concorde.json").is_file()
    ):
        raise SpecError(
            "source maintenance requires a fresh Skill-free child in an assigned candidate",
            "fresh_session_required",
        )
    if mutation and not host.allow_primary_worktree:
        if task.get("_issue_recovery"):
            raise SpecError(
                "pending Issue disposition must recover in its owning worktree; do not create another candidate",
                "workspace_mismatch",
            )
        if primary is None:
            raise SpecError(
                "mutations require a committed Git worktree", "workspace_mismatch"
            )
        # The mutation runs in a host-created candidate; the originating session stays in
        # the primary worktree and receives the candidate's result.
        return host, {
            **create_worktree(host.project_root, task, package_root=host.package_root),
            "relay": True,
        }
    if mutation:
        ensure_change(
            host.project_root,
            task=task,
            change_id=task.get("change_id"),
            allow_primary=True,
        )
    if current is not None:
        refresh_registry(host.project_root)
    return host, None
