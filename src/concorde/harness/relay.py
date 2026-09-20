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
    progress,
    read_change,
    refresh_registry,
    resume_owner,
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


def source_checkout(root: Path) -> bool:
    return (root / "concorde.json").is_file() and (root / "src/concorde").is_dir()


def verify_local_execution(host: OperationHost) -> None:
    """Installed entry admission is local and read-only; source-private fixtures stay separate."""
    if (
        host.package_root.name != "framework"
        or host.package_root.parent.name != ".concorde"
    ):
        return
    from ..distribution.local_installation import verify_installation

    if host.package_root != host.project_root / INSTALLED_FRAMEWORK_ROOT:
        raise SpecError(
            "installed execution requires this worktree's local Framework",
            "local_installation_required",
        )
    try:
        local = verify_installation(host.project_root)
        import langgraph.graph

        runtime = local.python.parent.parent
        if Path(sys.prefix).resolve() != runtime or not Path(
            langgraph.graph.__file__
        ).resolve().is_relative_to(runtime):
            raise ValueError(
                "the executing interpreter or LangGraph dependency is not worktree-local"
            )
    except (ValueError, OSError) as error:
        raise SpecError(
            f"local installation unavailable: {error}; run the explicit installer before retrying",
            "local_installation_required",
        ) from error


def relay_launcher(
    host: OperationHost, candidate: Path, *, bootstrap: bool = False
) -> list[str]:
    """Select only verified candidate-local code and dependencies, never provider execution."""
    if source_checkout(candidate):
        from ..distribution.build import verify_fresh

        verify_fresh(candidate)
        python = candidate / ".venv/bin/python"
        launcher = candidate / "scripts/run-operation.py"
        if (
            not python.is_file()
            or python.parent.parent.resolve() != candidate / ".venv"
            or not launcher.is_file()
            or launcher.resolve() != launcher
        ):
            raise SpecError(
                "source candidate requires its own environment and launcher",
                "missing_runtime",
            )
        return [str(python), str(launcher)]
    from ..distribution.local_installation import admit_package, ensure_installation

    try:
        source = admit_package(host.package_root)
        local = ensure_installation(
            candidate, source, bootstrap=bootstrap, preserve_project=True
        )
    except (ValueError, OSError) as error:
        raise SpecError(
            f"candidate local installation unavailable: {error}; explicitly install/update this worktree before retrying",
            "local_installation_required",
        ) from error
    return [str(local.python), str(local.launcher)]


def relay_operation(
    host: OperationHost, operation: str, invocation: dict, candidate: Path
) -> tuple[dict, str]:
    """Run ``invocation`` with the candidate worktree's launcher; return its envelope and stderr.

    A self-hosted candidate must already have a fresh build from its own sources;
    relay verifies it without rebuilding or substituting another checkout's outputs. A host
    interrupt reaches the launcher as SIGTERM, which cancels its worker and prints its result;
    only a launcher that does not finish within the grace period is killed."""
    try:
        if not source_checkout(candidate):
            state = read_change(candidate, required=True)
            target = host.relay_target or {}
            if target.get("change_id") != state["change_id"] or target.get(
                "path"
            ) != str(candidate):
                raise SpecError(
                    "relay target does not own this candidate", "workspace_mismatch"
                )
            # Reject conflicting root intent before installation writes; review intent stays independent.
            if operation not in {
                "concorde-code-review",
                "concorde-spec-review",
                "concorde-context-solve",
            }:
                resume_owner(state, invocation["input"]["data"])
        argv = [
            *relay_launcher(
                host,
                candidate,
                bootstrap=bool((host.relay_target or {}).get("bootstrap_installation")),
            ),
            operation,
        ]
    except SpecError as error:
        if error.code == "local_installation_required":
            progress(candidate, status="blocked", outcome=error.code)
        raise
    environment = {
        key: value
        for key, value in os.environ.items()
        if key not in {"CONCORDE_STUDIO_URL", "PYTHONPATH", "PYTHONHOME"}
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
    if (
        mutation
        and host.mode == "execute"
        and in_primary
        and host.package_root == host.project_root
        and (host.project_root / "concorde.json").is_file()
    ):
        raise SpecError(
            "source maintenance requires a fresh Concorde-catalog-free child in an assigned candidate",
            "fresh_session_required",
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
            "bootstrap_installation": True,
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
