"""``concorde task deliver``: deliver a task where the method part is not installed.

Where Method is installed, a task is delivered by its ``delivery`` execution command, which
validates the whole workspace first; ``task deliver`` then refuses with ``delivery_by_method``, so
that a workspace Method could validate is never delivered without that validation. Whether Method
is installed is told by the host: the task worktree's own ``concorde`` offers ``delivery``
(``parts.offers``).

Elsewhere it runs in the task's worktree, holding the task's workspace lock, runs the checks it is
given there, stages every change Git does not ignore and commits it as the workspace's next
delivery commit, by the Kernel's convention, even with nothing staged, as the mark of the
delivery. A head that already is a delivery commit of the workspace that verifies,
with a clean worktree, is reported as delivered and nothing is committed. Each attempt is a trace
node ``deliveries/<n>/`` of the task with each check a node ``checks/<n>/`` below it.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from ...kernel import binding, delivery, errors
from ...kernel.refusal import KernelError
from ...kernel.schema import register
from ...kernel.tracing.kinds import NodeKind, register as register_kinds
from ...kernel.tracing.node import Node
from . import checks, parts, store
from .store import TaskError

_COMMIT = {"type": "string", "pattern": "^[0-9a-f]{40}([0-9a-f]{24})?$"}
# contract.tasks.delivery-trace, version 1
DELIVERY_TRACE = "concorde-delivery-trace"
register(
    DELIVERY_TRACE,
    1,
    {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "branch",
            "before",
            "commit",
            "recovered",
            "checks",
            "waited_seconds",
        ],
        "properties": {
            "branch": {"type": "string", "minLength": 1},
            "before": _COMMIT,
            "commit": {"anyOf": [{"type": "null"}, _COMMIT]},
            "recovered": {"type": "boolean"},
            "checks": {
                "type": "array",
                "items": {"type": "array", "items": {"type": "string"}},
            },
            "waited_seconds": {"type": "number", "minimum": 0},
        },
    },
)
# contract.tasks.delivery-check-trace, version 1
DELIVERY_CHECK_TRACE = "concorde-delivery-check-trace"
register(
    DELIVERY_CHECK_TRACE,
    1,
    {
        "type": "object",
        "additionalProperties": False,
        "required": ["argv", "exit_code"],
        "properties": {
            "argv": {"type": "array", "items": {"type": "string"}},
            "exit_code": {"anyOf": [{"type": "null"}, {"type": "integer"}]},
        },
    },
)
register_kinds(
    NodeKind("delivery", DELIVERY_TRACE, ("task", "branch", "commit")),
    NodeKind("delivery-check", DELIVERY_CHECK_TRACE, ()),
)
DELIVERIES = "deliveries"


def _method_installed(worktree: Path) -> bool:
    try:
        return parts.offers(worktree, "delivery")
    except parts.Failed as failure:
        raise TaskError(
            "part_unknown",
            f"`concorde task deliver` delivers only where the method part is not installed, "
            f"and {failure}",
        ) from None


def _bound_task(here: Path, task_id: str) -> tuple[Path, Path, dict]:
    """The primary worktree, the task's worktree and its record, for a command run inside that
    worktree; ``not_task_worktree`` elsewhere, ``task_closed`` for a task that ended,
    ``wrong_branch`` for a worktree not on the task branch."""
    worktree = store.worktree_of(here)
    primary = store.primary_of(here)
    record = store.load_unended(primary, task_id, "an ended task is delivered no more")
    try:
        bound = binding.load(worktree)
    except (KernelError, OSError, ValueError):
        bound = None
    if (
        os.path.realpath(worktree) != os.path.realpath(record["worktree"])
        or not bound
        or bound.get("workspace") != task_id
    ):
        raise TaskError(
            "not_task_worktree",
            f"`concorde task deliver {task_id}` runs only in the worktree of task {task_id}, "
            f"{record['worktree']}, whose workspace binding names it; it ran in {worktree}",
        )
    branch = store._git(worktree, "symbolic-ref", "-q", "--short", "HEAD", check=False)
    if branch.returncode != 0 or branch.stdout.strip() != record["branch"]:
        where = (
            f"is on branch {branch.stdout.strip()}"
            if branch.returncode == 0
            else "has a detached HEAD"
        )
        raise TaskError(
            "wrong_branch",
            f"the worktree {worktree} of task {task_id} {where}, not on the task branch "
            f"{record['branch']}; a delivery commit is made only on the task branch",
        )
    return primary, worktree, record


def _next_folder(primary: Path, task_id: str) -> Path:
    """The folder of the task's next delivery attempt; read only while holding its workspace
    lock, which every ``task deliver`` of the task holds."""
    parent = store.task_folder(primary, task_id) / DELIVERIES
    earlier = (
        [item for item in parent.iterdir() if item.is_dir()] if parent.is_dir() else []
    )
    return parent / str(1 + len(earlier))


def deliver_task(
    here: Path,
    task_id: str,
    texts: list[str] | None = None,
    wait: float = store.MERGE_WAIT,
) -> dict:
    """Deliver the task whose worktree ``here`` is in, after the checks ``texts`` passed there."""
    commands = checks.parse(
        list(texts or []), lambda message: TaskError("invalid_input", message)
    )
    if wait < 0:
        raise TaskError("invalid_input", f"--wait {wait:g} is negative")
    worktree = store.worktree_of(here)
    if _method_installed(worktree):
        raise TaskError(
            "delivery_by_method",
            f"the method part is installed in {worktree}, so task {task_id} is delivered by "
            "`concorde delivery`, which validates the whole workspace before it commits; "
            "`concorde task deliver` delivers only where the method part is not installed",
        )
    primary, worktree, _ = _bound_task(here, task_id)
    with store.task_workspace_locked(
        primary, task_id, "deliver", wait, retake=False
    ) as waited:
        # A close, a merge or a branch switch may have come while this process waited: admit
        # the task again under the lock and act on the record read now.
        primary, worktree, record = _bound_task(worktree, task_id)
        return _delivered(primary, worktree, record, commands, waited)


def _head(worktree: Path) -> str:
    return store._git(worktree, "rev-parse", "HEAD").stdout.strip()


def _delivered(
    primary: Path, worktree: Path, record: dict, commands: list[list[str]], waited
) -> dict:
    task_id = record["id"]
    before = _head(worktree)
    folder = _next_folder(primary, task_id)
    data = {
        "branch": record["branch"],
        "before": before,
        "commit": None,
        "recovered": False,
        "checks": [list(argv) for argv in commands],
        "waited_seconds": float(waited),
    }
    node = Node(
        folder,
        f"delivery-{folder.name}",
        "delivery",
        content_type=DELIVERY_TRACE,
        metadata={"task": task_id, "branch": record["branch"]},
        content=data,
    ).start()
    # The refused writes of the trace nodes of its checks.
    failures: list[str] = []
    try:
        answer = _deliver(primary, worktree, record, commands, data, node, failures)
    except TaskError as refusal:
        node.finish(
            "failed",
            outcome=refusal.code
            if refusal.code in ("check_failed", "git_failed")
            else "refused",
            error=errors.link(
                "component",
                f"Tasks (concorde task deliver of task {task_id})",
                refusal.code,
                str(refusal),
                reason="decision" if refusal.code == "check_failed" else "environment",
                explanation="the delivery attempt ended with this refusal",
            ),
            content=data,
        )
        raise checks.with_failures(refusal, [*node.failures, *failures]) from None
    shown = store.load_task(primary, task_id)
    shown["state"] = store.derived_state(primary, shown)
    return {
        "record": shown,
        "delivery": {
            "commit": data["commit"],
            "recovered": data["recovered"],
            "checks": answer,
            "waited_seconds": data["waited_seconds"],
            "log": folder.as_posix(),
        },
        "warnings": [*node.failures, *failures],
    }


def _deliver(
    primary: Path,
    worktree: Path,
    record: dict,
    commands: list[list[str]],
    data: dict,
    node: Node,
    failures: list[str],
) -> list[dict]:
    task_id, before = record["id"], data["before"]
    found = store.deliveries(primary, record)
    if (
        found
        and found[-1]["commit"] == before
        and not found[-1]["mismatches"]
        and not store._dirty(worktree)
    ):
        data.update(commit=before, recovered=True)
        node.refer("found_commit", before)
        node.finish("ok", outcome="recovered", content=data, commit=before)
        return []
    results = []
    for number, argv in enumerate(commands, start=1):
        result, problem = checks.run(
            worktree,
            argv,
            node.folder / "checks" / str(number),
            identity=f"check-{number}",
            kind="delivery-check",
            content_type=DELIVERY_CHECK_TRACE,
            failures=failures,
        )
        results.append(result)
        if problem:
            raise TaskError(
                "check_failed",
                f"task {task_id} was not delivered: {problem}; the full output is in "
                f"{node.folder / 'checks' / str(number) / 'output.log'}, and nothing was "
                "committed",
            )
    commit = _commit(worktree, record, before)
    data["commit"] = commit
    node.refer("commit", commit)
    node.finish("ok", outcome="delivered", content=data, commit=commit)
    return results


def _special(worktree: Path) -> list[str]:
    """The new paths Git cannot version, such as a sandbox's ``/dev/null`` mounts, which are no
    content of the task and would make ``git add`` refuse the whole delivery."""
    raw = store._git(
        worktree,
        "--no-optional-locks",
        "status",
        "--porcelain",
        "-z",
        "--untracked-files=all",
        check=False,
    ).stdout
    found = []
    for entry in raw.split("\0"):
        if entry.startswith("?? "):
            path = worktree / entry[3:]
            if not (path.is_symlink() or path.is_file() or path.is_dir()):
                found.append(entry[3:])
    return found


def _commit(worktree: Path, record: dict, before: str) -> str:
    """Stage every change Git does not ignore and commit it as the delivery commit; the commit,
    or ``git_failed`` with the branch where it was."""
    task_id = record["id"]
    excluded = [f":(exclude,literal){path}" for path in _special(worktree)]
    staged = store._git(worktree, "add", "-A", "--", ".", *excluded, check=False)
    if staged.returncode != 0:
        raise TaskError(
            "git_failed",
            f"git add -A in {worktree} exited {staged.returncode}: "
            f"{(staged.stderr or staged.stdout).strip() or '(no output)'}; nothing was "
            f"committed and the branch {record['branch']} is still at {before}",
        )
    committed = subprocess.run(
        ["git", "commit", "-q", "--allow-empty", "--cleanup=verbatim", "-F", "-"],
        cwd=worktree,
        input=delivery.message(task_id, record["goal"]),
        capture_output=True,
        text=True,
        check=False,
    )
    if committed.returncode != 0:
        raise TaskError(
            "git_failed",
            f"git commit of the delivery of task {task_id} in {worktree} exited "
            f"{committed.returncode}: "
            f"{(committed.stdout + committed.stderr).strip()[-checks.OUTPUT_TAIL :] or '(no output)'}"
            f"; nothing was committed, the branch {record['branch']} is still at {before} and "
            "the changes stay staged",
        )
    head = _head(worktree)
    parents = store._git(
        worktree, "rev-list", "--parents", "-n", "1", head
    ).stdout.split()[1:]
    subject = store._git(worktree, "log", "-1", "--format=%s", head).stdout.strip()
    if parents != [before] or subject != delivery.subject(task_id):
        store._git(worktree, "reset", "--soft", before, check=False)
        raise TaskError(
            "git_failed",
            f"the delivery commit {head} of task {task_id} does not verify: its parents are "
            f"{', '.join(parents) or 'none'} instead of {before} alone and its subject is "
            f"{subject!r}, as a commit hook may make it; it was taken off the branch with git "
            f"reset --soft {before}, keeping its changes staged",
        )
    return head


__all__ = ["DELIVERY_CHECK_TRACE", "DELIVERY_TRACE", "deliver_task"]
