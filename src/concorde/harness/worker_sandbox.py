"""OS-enforced confinement of one Pi worker process, on Linux with bubblewrap.

The tool gate inside the Pi process decides which tool calls the model may make; this module
decides what the process itself can reach, so a shell command a worker was granted is bounded
too. The mount plan is derived from the launch and never authored separately:

- the host filesystem is mounted read-only, with masks over the developer's credential
  locations and their own agent clients' state (``MASKED_HOME_PATHS``) and over every other
  worktree of the workspace's repository; the repository's shared Git directory stays readable
  so Git keeps working inside a candidate;
- the workspace stays read-only except the launch's write paths, which are bound writable in
  place; a pending entry that does not exist yet gets an empty placeholder (a file or an empty
  directory) so exactly that path is writable, and a placeholder the worker left untouched is
  removed after the run;
- the run directory (Pi configuration, credential copies, policy, prompt, host socket and the
  process's HOME) and its temporary directory are writable; ``/tmp`` is a private tmpfs; ``/proc``
  and ``/dev`` are fresh; PID, IPC and UTS namespaces are private; the sandbox dies with the host;
  the network is shared because Pi must reach its model provider.

``WORKER_SANDBOX_POLICY`` names these rules, and the plan records the exact mounts, so a run's
boundary can be read back. An unavailable boundary refuses the launch rather than running the
worker unconfined.
"""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Sequence

from .check_executor import CheckSandboxError, _bubblewrap

WORKER_SANDBOX_POLICY = "worker-mounts-v1"

# Entries below the developer's home directory that no worker process may read: credentials and
# the developer's own agent clients' state (sessions, trust decisions, tokens). Only existing
# entries are masked; a directory becomes an empty private tmpfs and a file reads as empty.
MASKED_HOME_PATHS: tuple[str, ...] = (
    ".aws",
    ".azure",
    ".claude",
    ".codex",
    ".config/gcloud",
    ".config/gh",
    ".docker/config.json",
    ".git-credentials",
    ".gnupg",
    ".kube",
    ".netrc",
    ".npmrc",
    ".pi",
    ".pypirc",
    ".ssh",
)


class WorkerSandboxError(RuntimeError):
    """The boundary cannot be enforced; the launch is refused rather than run unconfined."""


@dataclass(frozen=True)
class MountPlan:
    """What one worker process may see and change; every path is absolute."""

    policy: str
    workspace: str
    run_dir: str
    home: str
    # An empty regular file inside the run directory, bound read-only over masked files: a bound
    # device node such as /dev/null is not readable inside the sandbox.
    mask_file: str
    masks: tuple[str, ...]
    other_worktrees: tuple[str, ...]
    git_common_dir: str | None
    writable: tuple[str, ...]
    pending: tuple[str, ...]

    def wire(self) -> dict:
        return asdict(self)


def unavailable_reason() -> str | None:
    """Why no worker sandbox can be enforced here, or None when it can."""
    if sys.platform != "linux":
        return f"no worker sandbox backend is available for {sys.platform}"
    try:
        _bubblewrap()
    except CheckSandboxError as error:
        return str(error)
    except OSError as error:
        return f"cannot locate a trusted bubblewrap installation: {error}"
    return None


def _git(workspace: Path, *arguments: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(workspace), *arguments],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None
    return result.stdout if result.returncode == 0 else None


def _git_common_dir(workspace: Path) -> Path | None:
    output = _git(workspace, "rev-parse", "--path-format=absolute", "--git-common-dir")
    return Path(output.strip()).resolve() if output and output.strip() else None


def _other_worktrees(workspace: Path) -> tuple[Path, ...]:
    output = _git(workspace, "worktree", "list", "--porcelain") or ""
    listed = [
        Path(line[len("worktree ") :]).resolve()
        for line in output.splitlines()
        if line.startswith("worktree ")
    ]
    return tuple(path for path in listed if path != workspace)


def plan_mounts(
    workspace: str | Path,
    write_paths: Sequence[str],
    run_dir: str | Path,
    *,
    home: str | Path | None = None,
) -> MountPlan:
    """Derive the mount plan of one launch; ``home`` defaults to the developer's home directory."""
    root = Path(workspace).resolve()
    run = Path(run_dir).resolve()
    if not root.is_dir() or not run.is_dir():
        raise WorkerSandboxError("the workspace and run directory must be existing directories")
    if root == Path("/") or run == Path("/") or run.is_relative_to(root):
        raise WorkerSandboxError(
            "the workspace cannot be the root directory or contain the run directory"
        )
    developer_home = Path(home if home is not None else Path.home()).resolve()
    masks = tuple(
        str(developer_home / relative)
        for relative in MASKED_HOME_PATHS
        if (developer_home / relative).is_symlink() or (developer_home / relative).exists()
    )
    others = _other_worktrees(root)
    common = _git_common_dir(root)
    writable: list[str] = []
    pending: list[str] = []
    for entry in write_paths:
        target = root / entry
        if target.is_symlink():
            raise WorkerSandboxError(f"a write entry cannot be a symlink: {entry}")
        if not target.resolve().is_relative_to(root):
            raise WorkerSandboxError(f"a write entry cannot leave the workspace: {entry}")
        if target.exists():
            writable.append(str(target))
        else:
            # A pending directory keeps its trailing slash so the placeholder is a directory.
            pending.append(str(target) + ("/" if entry.endswith("/") else ""))
    return MountPlan(
        policy=WORKER_SANDBOX_POLICY,
        workspace=str(root),
        run_dir=str(run),
        home=str(run / "home"),
        mask_file=str(run / "mask"),
        masks=masks,
        other_worktrees=tuple(str(path) for path in others),
        git_common_dir=str(common) if common is not None else None,
        writable=tuple(dict.fromkeys(writable)),
        pending=tuple(dict.fromkeys(pending)),
    )


def create_placeholders(plan: MountPlan) -> tuple[str, ...]:
    """Create the pending entries as empty placeholders so exactly those paths can be mounted.

    A pending directory (an entry ending in ``/``) becomes an empty directory; a pending file
    becomes an empty file below any missing parent directories. Everything created is returned,
    deepest first, for ``remove_untouched_placeholders``."""
    created: list[str] = []
    for raw in plan.pending:
        target = Path(raw)
        parents = [
            parent
            for parent in target.parents
            if parent.is_relative_to(plan.workspace) and not parent.exists()
        ]
        for parent in reversed(parents):
            parent.mkdir()
            created.append(str(parent))
        if raw.endswith("/") or raw.endswith(os.sep):
            target.mkdir()
        else:
            target.touch()
        created.append(str(target))
    return tuple(reversed(created))


def remove_untouched_placeholders(created: Sequence[str]) -> None:
    """Remove placeholders the worker left empty; anything written or filled stays."""
    for raw in created:
        path = Path(raw)
        try:
            if path.is_symlink():
                continue
            if path.is_dir():
                if not any(path.iterdir()):
                    path.rmdir()
            elif path.is_file() and path.stat().st_size == 0:
                path.unlink()
        except OSError:
            continue


def bubblewrap_argv(plan: MountPlan, command: Sequence[str]) -> list[str]:
    """The bubblewrap command that runs ``command`` inside ``plan``; every mount is explicit.

    Later mounts stack on earlier ones: the writable run directory and workspace binds follow
    the private ``/tmp`` because host-created capsules and run directories usually live there,
    and the shared Git directory is re-bound after the tmpfs that masks its worktree."""
    try:
        executable = _bubblewrap()
    except (CheckSandboxError, OSError) as error:
        raise WorkerSandboxError(str(error)) from error
    Path(plan.mask_file).touch(exist_ok=True)
    argv = [
        executable,
        "--unshare-user",
        "--unshare-pid",
        "--unshare-ipc",
        "--unshare-uts",
        "--die-with-parent",
        "--new-session",
        "--cap-drop",
        "ALL",
        "--ro-bind",
        "/",
        "/",
        "--proc",
        "/proc",
        "--dev",
        "/dev",
        "--tmpfs",
        "/dev/shm",
        "--tmpfs",
        "/tmp",
    ]
    for path in plan.masks:
        if Path(path).is_dir() and not Path(path).is_symlink():
            argv += ["--tmpfs", path]
        else:
            argv += ["--ro-bind", plan.mask_file, path]
    for path in plan.other_worktrees:
        if Path(path).is_dir():
            argv += ["--tmpfs", path]
    if plan.git_common_dir is not None and Path(plan.git_common_dir).is_dir():
        argv += ["--ro-bind", plan.git_common_dir, plan.git_common_dir]
    argv += ["--ro-bind", plan.workspace, plan.workspace]
    argv += ["--bind", plan.run_dir, plan.run_dir]
    for path in (*plan.writable, *plan.pending):
        mount = path.rstrip("/")
        argv += ["--bind", mount, mount]
    if any("\0" in argument for argument in argv):
        raise WorkerSandboxError("sandbox mount paths cannot contain NUL bytes")
    return [*argv, "--chdir", plan.workspace, "--", *command]
