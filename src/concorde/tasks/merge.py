"""``concorde task merge``: merge a delivered task into the primary branch under the merge lock.

The whole critical section runs in this one process, which holds the merge lock from the checks
before the merge to the close after it: the merge, the post-merge checks, the reset that undoes a
merge whose checks failed, and closing the task. The kernel releases the lock however the process
ends, so no other session has to wait for this one to announce that it is done. It also holds the
task's workspace lock, so no run of the task changes its branch meanwhile, and merges the exact
commit it checked, always as a merge commit that also adds the task's decision log as
``.concorde/decisions/<history key>.md`` and names the task in its ``Concorde-Task`` trailer. Before ``git merge`` it stores the task as ``merging``; a process that ends
before its checks decided leaves that state behind, which refuses every other mutating task
command until ``--resume`` reruns the checks or ``--abort`` resets the primary branch.

Before it merges, it audits what lies outside the task's worktree: the primary worktree, which
must be clean, and the worktree of every other task that is not working in it, which must hold no
change, since a task changes nothing outside its own worktree.

Every attempt, a merge, a ``--resume`` or an ``--abort``, is a trace node ``merges/<n>/`` of the
task, ended with how the attempt ended; each check it runs is a node ``checks/<i>/`` below it with
the check's output as ``output.log``. A merge the project MCP server started finds its attempt's
folder already made, named in ``CONCORDE_MERGE_ATTEMPT``, with its standard output and error going
to ``output.json`` and ``messages.log`` there; it records the attempt there even when it is refused
before it began, so the merge's whole output stays with the task, also in the history.

The command holds the task's merge attempt lock from before its other locks until it has printed
its output, and removes it then, so ``concorde task wait <task> --merge`` returns only once that
output is complete, although the close removes the task's workspace lock before.

The process imports Concorde's own modules from a snapshot of their sources taken when the merge
starts (``freeze_sources``), so a merge that changes Concorde itself never leaves it running a mix
of the two versions in the steps after the merge.
"""

from __future__ import annotations

import importlib
import importlib.abc
import importlib.util
import os
import shlex
import subprocess
import sys
import time
from contextlib import ExitStack
from pathlib import Path

from .. import errors
from ..spec.typed_data import register
from ..tracing import locks
from ..tracing import node as trace
from ..tracing.node import Node
from . import store
from .store import TaskError

_TEXT = {"type": "string", "minLength": 1}
_COMMIT = {"type": "string", "pattern": "^[0-9a-f]{40}([0-9a-f]{24})?$"}
# contract.tasks.merge-trace, version 1
MERGE_TRACE = "concorde-merge-trace"
register(
    MERGE_TRACE,
    1,
    {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "attempt",
            "branch",
            "before",
            "checked",
            "after",
            "checks",
            "waited_seconds",
        ],
        "properties": {
            "attempt": {"enum": ["merge", "resume", "abort"]},
            "branch": _TEXT,
            "before": _COMMIT,
            "checked": {"anyOf": [{"type": "null"}, _COMMIT]},
            "after": {"anyOf": [{"type": "null"}, _COMMIT]},
            "checks": {
                "type": "array",
                "items": {"type": "array", "items": {"type": "string"}},
            },
            "waited_seconds": {"type": "number", "minimum": 0},
        },
    },
)
# contract.tasks.merge-check-trace, version 1
MERGE_CHECK_TRACE = "concorde-merge-check-trace"
register(
    MERGE_CHECK_TRACE,
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
# The environment variable naming the attempt folder the project MCP server made for the merge,
# and the files of it the merge's standard output and error go to.
RESERVED = "CONCORDE_MERGE_ATTEMPT"
OUTPUT = "output.json"
MESSAGES = "messages.log"
# The outcome of an attempt that a refusal ended, by the refusal's code.
REFUSED = {
    "merge_conflict": "conflict",
    "check_failed": "check_failed",
    "rollback_failed": "rollback_failed",
    "git_failed": "git_failed",
}


class _Source(importlib.abc.SourceLoader):
    """Loads one module from the source bytes a snapshot kept, never from its file now. It
    reports no file times, so it neither reads nor writes a bytecode cache: a cache written from
    the kept source would be taken for the file's new contents."""

    def __init__(self, path: Path, source: bytes):
        self.path, self.source = path, source

    def get_filename(self, fullname: str) -> str:
        return str(self.path)

    def get_data(self, path: str) -> bytes:
        if path == str(self.path):
            return self.source
        return Path(path).read_bytes()


class _Snapshot(importlib.abc.MetaPathFinder):
    """The source of every module of one package, as its files were when it was taken."""

    def __init__(self, name: str, root: Path):
        self.name = name
        self.modules: dict[str, tuple[Path, bytes, bool]] = {}
        for path in sorted(root.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            parts = path.relative_to(root).with_suffix("").parts
            package = parts[-1] == "__init__"
            module = ".".join((name, *(parts[:-1] if package else parts)))
            self.modules[module] = (path, path.read_bytes(), package)

    def find_spec(self, fullname, path=None, target=None):
        found = self.modules.get(fullname)
        if found is None:
            return None
        file, source, package = found
        return importlib.util.spec_from_file_location(
            fullname,
            file,
            loader=_Source(file, source),
            submodule_search_locations=[str(file.parent)] if package else None,
        )


def freeze_sources(name: str = __name__.partition(".")[0]) -> None:
    """Serve every module of the package ``name`` that this process imports from now on from its
    source as it is now, for the rest of the process.

    A merge changes the primary worktree's files while its process runs, and Concorde's own
    sources are among them when the merged task changed Concorde. A module imported after the
    merge, such as one a post-merge step imports when it needs it, would otherwise be the merged
    version, mixed with the modules imported before: an import between the two versions can fail,
    or the mix behave as neither. Frozen, the process stays on the one Concorde it started with,
    while the checks, processes of their own, run the merged one. Only module sources are kept: a
    data file is read as it is when it is read.
    """
    if any(
        isinstance(finder, _Snapshot) and finder.name == name
        for finder in sys.meta_path
    ):
        return
    package = importlib.import_module(name)
    sys.meta_path.insert(0, _Snapshot(name, Path(package.__file__).parent))


def next_attempt(primary: Path, task_id: str) -> Path:
    """The folder the task's next merge attempt gets, ``merges/<n>/`` with ``n`` one more than
    the attempts so far; read only while holding the task's workspace and merge locks."""
    parent = store.task_folder(primary, task_id) / "merges"
    earlier = (
        [item for item in parent.iterdir() if item.is_dir()] if parent.is_dir() else []
    )
    return parent / str(1 + len(earlier))


def reserved_attempt(primary: Path, task_id: str) -> Path | None:
    """The attempt folder the project MCP server made for this merge, once, or None.

    The variable is removed, so that no process the merge starts believes it was given one; a
    folder that is not the task's next attempt, or already holds a node, is not taken."""
    value = os.environ.pop(RESERVED, None)
    if not value:
        return None
    folder = Path(value)
    parent = store.task_folder(primary, task_id) / "merges"
    if (
        folder.name.isdigit()
        and folder.parent.resolve() == parent.resolve()
        and folder.is_dir()
        and trace.read(folder) is None
    ):
        return folder
    return None


class Attempt:
    """One merge attempt's trace node, ``merges/<n>/`` of the task, or the folder ``reserved``
    that the project MCP server made for it, which holds the merge's output files."""

    def __init__(
        self,
        primary: Path,
        task_id: str,
        kind: str,
        merging: dict,
        waited,
        reserved: Path | None = None,
    ):
        parent = store.task_folder(primary, task_id) / "merges"
        earlier = (
            sorted(
                item for item in parent.iterdir() if item.is_dir() and item != reserved
            )
            if parent.is_dir()
            else []
        )
        for folder in earlier:
            # An attempt whose process ended before it decided was interrupted.
            found = trace.read(folder)
            if found is not None and found.get("status") == "running":
                found.update(
                    ended_at=trace.now(), status="failed", outcome="interrupted"
                )
                trace.write(folder, found)
        number = int(reserved.name) if reserved is not None else 1 + len(earlier)
        self.task_id = task_id
        self.folder = parent / str(number)
        self.checks = 0
        self.data = {
            "attempt": kind,
            "branch": merging["branch"],
            "before": merging["before"],
            "checked": merging.get("checked"),
            "after": merging.get("after"),
            "checks": [list(argv) for argv in merging.get("checks") or []],
            "waited_seconds": float(waited),
        }
        self.node = Node(
            self.folder,
            f"merge-{number}",
            "merge",
            content_type=MERGE_TRACE,
            metadata={"task": task_id, "branch": merging["branch"]},
            content=self.data,
        )
        # The merge writes its output after the node ends, so its digest is never taken.
        for identity, name in (("output", OUTPUT), ("messages", MESSAGES)):
            self.node.keep(identity, name, measured=False)
        self.node.start()

    def merged(self, after: str) -> None:
        self.data["after"] = after
        self.node.update(content=self.data, commit=after)

    def check_folder(self) -> Path:
        self.checks += 1
        return self.folder / "checks" / str(self.checks)

    def end(self, status: str, outcome: str, error: dict | None = None) -> None:
        if self.node.record["status"] == "running" and self.folder.is_dir():
            self.node.finish(status, outcome=outcome, error=error, content=self.data)

    def refused(self, refusal: TaskError) -> None:
        self.end(
            "failed",
            REFUSED.get(refusal.code, "refused"),
            errors.link(
                "component",
                f"Tasks (concorde task merge of task {self.task_id})",
                refusal.code,
                str(refusal),
                reason="decision"
                if refusal.code in ("merge_conflict", "check_failed")
                else "environment",
                explanation="the merge attempt ended with this refusal",
            ),
        )


# A check that runs longer than this is stopped and counts as failed, so the lock is not held
# for ever by a check that hangs.
CHECK_TIMEOUT = 1800
# How much of a failed check's output a refusal quotes; the log holds all of it.
OUTPUT_TAIL = 2000
LISTED = 20


def default_checks() -> list[list[str]]:
    """``concorde spec-validation`` of the primary worktree, by this Python and this package."""
    return [[sys.executable, "-m", "concorde", "spec-validation"]]


def parse_checks(texts: list[str]) -> list[list[str]]:
    checks = []
    for text in texts:
        try:
            words = shlex.split(text)
        except ValueError as error:
            raise TaskError(
                "invalid_input", f"--check {text!r} cannot be split into words: {error}"
            ) from error
        if not words:
            raise TaskError("invalid_input", f"--check {text!r} names no command")
        checks.append(words)
    return checks or default_checks()


def _environment() -> dict:
    """The environment of a check: the running package first on Python's path."""
    package = str(Path(__file__).resolve().parents[2])
    environment = dict(os.environ)
    environment["PYTHONPATH"] = os.pathsep.join(
        item for item in (package, environment.get("PYTHONPATH")) if item
    )
    return environment


def _listed(paths: list[str]) -> str:
    more = f" and {len(paths) - LISTED} more" if len(paths) > LISTED else ""
    return ", ".join(paths[:LISTED]) + more


def _status(primary: Path) -> list[str]:
    """The primary worktree's changed paths, by the same rule as a task worktree's: new paths Git
    cannot version, such as a sandbox's mounts of ``.bashrc``, are left out."""
    return [entry[3:] for entry in store._changes(primary)]


def _recover_issues(primary: Path) -> str:
    """Put back, as every Issue write does first, what Issue writes left uncommitted in the
    primary worktree, so that such a leftover never refuses a merge; the caller holds the merge
    lock. What the recovery could not put back or left as no write's, for ``primary_dirty``."""
    try:
        from ..issues import store as issues

        recovery = issues.recover_issues(primary, locked=True)
    except Exception as error:  # noqa: BLE001 -- a failed recovery only leaves the paths dirty
        code = getattr(error, "code", type(error).__name__)
        return (
            f"; recovering the Issue records Issue writes left there failed ({code}: {error}), "
            "so run `concorde issues recover` once its cause is fixed"
        )
    if not recovery["left"]:
        return ""
    left = "; ".join(f"{item['path']} ({item['reason']})" for item in recovery["left"])
    return (
        f"; Issue recovery left these Issue records, whose changes no Issue write made: {left}, "
        "so inspect and revert each"
    )


def _primary_branch(primary: Path, recovered: str = "") -> str:
    """The primary worktree's branch, refused as ``primary_dirty`` unless it is clean;
    ``recovered`` is what Issue recovery said of the paths it did not put back."""
    branch = store._git(primary, "symbolic-ref", "-q", "--short", "HEAD", check=False)
    if branch.returncode != 0:
        head = store._git(primary, "rev-parse", "HEAD").stdout.strip()
        raise TaskError(
            "primary_dirty",
            f"the primary worktree {primary} has a detached HEAD at {head}; a task is merged "
            "only into a checked-out branch",
        )
    paths = _status(primary)
    if paths:
        raise TaskError(
            "primary_dirty",
            f"the primary worktree {primary} has {len(paths)} uncommitted or untracked "
            f"path(s): {_listed(paths)}; a merge starts only from a clean primary worktree, "
            "so that undoing it cannot touch anyone's work, and a task changes nothing "
            "outside its own worktree, so check whether these paths are the task's before "
            f"committing them{recovered}",
        )
    return branch.stdout.strip()


# --- what a task changed outside its worktree --------------------------------------------------
#
# A task session works only inside its task worktree, and since it runs under no sandbox nothing
# but its guidance and Claude Code's `auto` mode holds it there. The merge, the gate into the
# primary branch, therefore looks outside the task's worktree before it merges. What it can judge
# is bounded by what the filesystem says, since nothing in it records who wrote a change:
#
# - the primary worktree must be clean (``primary_dirty`` above). Nothing changes there while
#   tasks run except Concorde's own records, which are either paths Git does not version (the task
#   folders, locks, runs, history and unbound runs, all ignored by the installed .gitignore) or
#   committed by the command that writes them (Issue records, decision logs). An Issue write
#   killed before its commit leaves its record behind, which the merge puts back first, as the
#   next Issue write would (``_recover_issues`` above).
# - a worktree of a task that has ended, and outlived it, is nobody's: a change in it is refused
#   as ``changed_outside``.
# - a worktree of a task that has delivered and waits may hold a change of its own session, which
#   went on working after delivering, or of another task's: a warning names it, since refusing
#   this merge for it would block a task that has nothing to do with it.
#
# The worktree of a task that is still working is not judged at all: its own session changes it
# constantly, and what is written there is not lost, since it becomes that task's content, which
# its own validation, delivery and merge judge -- its merge refuses an uncommitted change as
# ``dirty_worktree``. Worktrees of no task, such as one a developer's own session made, are not
# the project's to judge. The audit judges working trees and not commits: the primary branch
# legitimately moves while a task runs, as other tasks merge, Issues are recorded and the
# developer commits.


def _settled(primary: Path, record: dict) -> bool:
    """Whether a task has delivered and waits: its branch head is a delivery commit of its
    workspace that verifies, so its session has reported and waits for an answer."""
    delivered = store.deliveries(primary, record)
    head = store._git(
        primary, "rev-parse", "--verify", "--quiet", record["branch"], check=False
    ).stdout.strip()
    return bool(
        delivered
        and head
        and delivered[-1]["commit"] == head
        and not store.delivery_mismatches(primary, delivered[-1])
    )


def _elsewhere(primary: Path, task_id: str):
    """Every other task's worktree that still exists, with its task, whether that task ended and
    whether it has delivered and waits.

    A task that ended whose worktree path a task that has not ended now uses, as after a task of
    the same name was opened again at the same path, is left to that task: the path is the live
    task's, not the ended one's.
    """
    live = {
        Path(os.path.realpath(record["worktree"]))
        for record in store._records(primary)
        if record["id"] != task_id
    }
    for record in store._records(primary, history=True):
        if record["id"] == task_id:
            continue
        worktree = Path(record["worktree"])
        ended = record["state"] in store.ENDED
        if not worktree.is_dir() or (
            ended and Path(os.path.realpath(worktree)) in live
        ):
            continue
        yield record["id"], worktree, ended, _settled(primary, record)


def _changed_outside(primary: Path, task_id: str) -> list[str]:
    """Refuse as ``changed_outside`` a change no task will account for; the warnings about a
    change that a delivered task's own session may have written."""
    nobodys, warnings = [], []
    for other, worktree, ended, settled in _elsewhere(primary, task_id):
        paths = [entry[3:] for entry in store._changes(worktree)]
        if not paths:
            continue
        held = (
            f"the worktree {worktree} of task {other} has {len(paths)} uncommitted or "
            f"untracked path(s): {_listed(paths)}"
        )
        if ended:
            nobodys.append(f"{held}, and that task has ended")
        elif settled:
            warnings.append(
                f"{held}, and that task has delivered and waits: its own session may have "
                "written them after delivering, which no other task's session may do; the task "
                "is active again and delivers again before it merges"
            )
    if nobodys:
        raise TaskError(
            "changed_outside",
            f"task {task_id} changes nothing outside its own worktree, and "
            + "; ".join(nobodys)
            + "; nothing accounts for these paths, since no task will validate or deliver "
            "them: find out what wrote them before merging, then revert them or remove the "
            "worktree they are in",
        )
    return warnings


def _head(primary: Path) -> str:
    return store._git(primary, "rev-parse", "HEAD").stdout.strip()


def _stays_merging(task_id: str) -> str:
    return (
        f"; task {task_id} stays merging, which refuses every other mutating task command, "
        f"until `concorde task merge {task_id} --abort` restores the primary branch"
    )


def _rollback(primary: Path, task_id: str, before: str, failure: str) -> str:
    """Reset the primary branch to ``before``; the text of what is left, or ``rollback_failed``."""
    reset = store._git(primary, "reset", "--keep", before, check=False)
    if reset.returncode != 0:
        raise TaskError(
            "rollback_failed",
            f"{failure}; then git reset --keep {before} in {primary} exited "
            f"{reset.returncode}: {(reset.stderr or reset.stdout).strip() or '(no output)'}; "
            f"the primary branch is at {_head(primary)} and its worktree as Git left it"
            + _stays_merging(task_id),
        )
    left = _status(primary)
    if left:
        return (
            f"; the primary branch is back at {before}, but these paths the checks created "
            f"remain in the primary worktree: {_listed(left)}"
        )
    return f"; the primary branch is back at {before}, clean"


def _merge(primary: Path, record: dict, merging: dict) -> str:
    """Merge the checked commit as a merge commit that adds the task's decision log as the
    close will leave it, with the closing dated ``merging.since``; the merge's head, or an
    aborted conflict or Git refusal refused."""
    branch, before = merging["branch"], merging["before"]
    checked, key = merging["checked"], merging["history"]
    merged = store._git(
        primary, "merge", "--no-ff", "--no-commit", checked, check=False
    )
    if merged.returncode != 0:
        output = (merged.stdout + merged.stderr).strip() or "(no output)"
        conflicts = store._git(
            primary, "diff", "--name-only", "--diff-filter=U", check=False
        ).stdout.split()
        failure = (
            f"git merge --no-ff --no-commit {checked} ({record['branch']}) into {branch} of "
            f"{primary} exited {merged.returncode}: {output[-OUTPUT_TAIL:]}"
        )
        _undo_merge(primary, record, branch, before, failure, conflicts)
    in_progress = store._git(
        primary, "rev-parse", "-q", "--verify", "MERGE_HEAD", check=False
    )
    if in_progress.returncode != 0:
        # Already contained: nothing to merge, and closing commits the decision log alone.
        return _head(primary)
    path = store.committed_log(key)
    target = primary / path
    source = store.decision_log_path(primary, record["id"])
    message = f"Merge branch '{record['branch']}' at {checked}\n\nConcorde-Task: {record['id']}\n"
    # The closing the close will append once the checks pass, with the answer it gives the
    # reports still unanswered, so that the copy equals the log as the task ends; a log changed
    # after this commit, such as by a report recorded meanwhile, gets a commit of its own at the
    # close.
    current = store.load_task(primary, record["id"])
    answer = {
        "at": merging["since"],
        "text": store.settling_answer(
            {**current, "merging": merging}, "merged", None, "merge"
        ),
        "by": "merge",
    }
    closing = store.closing_entry(
        {"outcome": "merged", "at": merging["since"], "note": None, "errors": []},
        store.settled_by_end(store.settled(current["reports"], answer)),
    )
    try:
        logged = source.read_bytes() if source.is_file() else b""
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(logged + closing.encode("utf-8"))
        added = store._git(primary, "add", "-f", "--", path, check=False)
        if added.returncode != 0:
            raise OSError(
                f"git add -f {path} exited {added.returncode}: "
                f"{(added.stdout + added.stderr).strip() or '(no output)'}"
            )
        committed = subprocess.run(
            ["git", "commit", "-q", "-F", "-"],
            cwd=primary,
            input=message,
            capture_output=True,
            text=True,
            check=False,
        )
        if committed.returncode != 0:
            raise OSError(
                f"git commit of the merge exited {committed.returncode}: "
                f"{(committed.stdout + committed.stderr).strip()[-OUTPUT_TAIL:] or '(no output)'}"
            )
    except OSError as error:
        failure = (
            f"merging {checked} ({record['branch']}) into {branch} of {primary} with the "
            f"decision log {source} as {path} failed: {error}"
        )
        _undo_merge(primary, record, branch, before, failure, [], target)
    return _head(primary)


def _undo_merge(
    primary: Path,
    record: dict,
    branch: str,
    before: str,
    failure: str,
    conflicts: list[str],
    written: Path | None = None,
) -> None:
    """Abort the merge in progress, remove the decision log it wrote, return the primary branch
    to ``before`` and the task to delivered, and refuse with ``merge_conflict`` or
    ``git_failed``."""
    in_progress = store._git(
        primary, "rev-parse", "-q", "--verify", "MERGE_HEAD", check=False
    )
    if in_progress.returncode == 0:
        aborted = store._git(primary, "merge", "--abort", check=False)
        if aborted.returncode != 0:
            raise TaskError(
                "rollback_failed",
                f"{failure}; then git merge --abort exited {aborted.returncode}: "
                f"{aborted.stderr.strip() or '(no output)'}; the primary branch is at "
                f"{_head(primary)} and its worktree as Git left it"
                + _stays_merging(record["id"]),
            )
    if written is not None:
        written.unlink(missing_ok=True)
    left = (
        _rollback(primary, record["id"], before, failure)
        if _head(primary) != before
        else ""
    )
    store.end_merge(primary, record["id"])
    if conflicts:
        raise TaskError(
            "merge_conflict",
            f"merging task {record['id']} ({record['branch']}) into {branch} conflicts in "
            f"{len(conflicts)} path(s): {_listed(conflicts)}; the merge was aborted{left} and "
            f"the task is still delivered",
        )
    raise TaskError(
        "git_failed",
        failure
        + (
            left
            or f"; the merge was aborted and the primary branch is back at {before}"
        )
        + "; the task is still delivered",
    )


def _check(
    primary: Path, argv: list[str], attempt: "Attempt"
) -> tuple[dict, str | None]:
    """Run one check in the primary worktree as a node of the attempt; its result and, when it
    failed, why."""
    folder = attempt.check_folder()
    node = Node(
        folder,
        f"check-{attempt.checks}",
        "merge-check",
        content_type=MERGE_CHECK_TRACE,
        content={"argv": list(argv), "exit_code": None},
    )
    node.keep("output", "output.log")
    node.start()
    log = folder / "output.log"
    started = time.monotonic()
    try:
        ran = subprocess.run(
            argv,
            cwd=primary,
            env=_environment(),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=CHECK_TIMEOUT,
            check=False,
        )
        code, output = ran.returncode, ran.stdout or ""
        problem = None if code == 0 else f"exited {code}"
    except subprocess.TimeoutExpired as error:
        code, output = -1, error.stdout if isinstance(error.stdout, str) else ""
        problem = f"was stopped after {CHECK_TIMEOUT} s"
    except OSError as error:
        code, output = -1, ""
        problem = f"could not run: {error}"
    seconds = round(time.monotonic() - started, 3)
    with log.open("a", encoding="utf-8") as stream:
        stream.write(
            f"$ {shlex.join(argv)}\n{output}"
            f"{'' if output.endswith(chr(10)) or not output else chr(10)}"
            f"[exit {code} after {seconds} s]\n"
        )
    node.finish(
        "ok" if problem is None else "failed",
        outcome="passed" if problem is None else "failed",
        content={"argv": list(argv), "exit_code": code if code >= 0 else None},
        used={"duration_seconds": seconds},
    )
    result = {"argv": list(argv), "exit_code": code, "seconds": seconds}
    if problem is None:
        return result, None
    tail = output.strip()[-OUTPUT_TAIL:] or "(no output)"
    return result, f"the check `{shlex.join(argv)}` {problem}; its output ends: {tail}"


def merge_task(
    here: Path,
    task_id: str,
    checks: list[str] | None = None,
    wait: float = store.MERGE_WAIT,
    *,
    resume: bool = False,
    abort: bool = False,
    held: ExitStack | None = None,
) -> dict:
    """Merge a delivered task into the primary branch, check it, and close the task; or, with
    ``resume`` or ``abort``, finish a merge of it whose process ended before its checks decided.

    The task's merge attempt lock is held until ``held`` closes, after the caller printed the
    answer, or, without ``held``, until this returns.
    """
    freeze_sources()
    primary = store.require_primary(here)
    if resume and abort:
        raise TaskError("invalid_input", "--resume and --abort exclude each other")
    if (resume or abort) and checks:
        raise TaskError(
            "invalid_input",
            "--resume reruns the checks the interrupted merge recorded and --abort runs none, "
            "so neither takes --check",
        )
    commands = parse_checks(list(checks or []))
    if wait < 0:
        raise TaskError("invalid_input", f"--wait {wait:g} is negative")
    store.load_task(primary, task_id)
    started = time.monotonic()
    own = ExitStack()
    with own:
        _hold_attempt(held if held is not None else own, primary, task_id, wait)
        remaining = max(0.0, wait - (time.monotonic() - started))
        # The task's own runs are waited for first, without the merge lock, so that a delivery
        # still finishing in the task never holds up the merges of other tasks.
        with store.task_workspace_locked(primary, task_id, "merge", remaining):
            remaining = max(0.0, wait - (time.monotonic() - started))
            with store.merge_lock(primary, "merge", task_id, remaining):
                waited = round(time.monotonic() - started, 3)
                reserved = reserved_attempt(primary, task_id)
                kind = "abort" if abort else "resume" if resume else "merge"
                try:
                    return _locked(primary, task_id, commands, waited, kind, reserved)
                except TaskError as refusal:
                    _refused_early(
                        primary, task_id, kind, commands, waited, reserved, refusal
                    )
                    raise


def _hold_attempt(stack: ExitStack, primary: Path, task_id: str, wait: float) -> None:
    """Take the task's merge attempt lock into ``stack``, removed when ``stack`` closes."""
    path = store.attempt_lock_path(primary, task_id)
    try:
        stack.enter_context(
            locks.hold(
                path,
                f"`concorde task merge` of task {task_id}",
                wait=wait,
                remove=True,
                task=task_id,
            )
        )
    except locks.LockBusy as busy:
        raise TaskError(
            "merge_busy",
            f"`concorde task merge` of task {task_id} waited {wait:g} s for the task's merge "
            f"attempt lock {path}, which is still held by {busy.holder}; one merge of a task "
            "runs at a time",
        ) from None


def _locked(
    primary: Path,
    task_id: str,
    commands: list[list[str]],
    waited,
    kind: str,
    reserved: Path | None,
) -> dict:
    unfinished = store.unfinished_merge(primary)
    if unfinished is not None and not (kind != "merge" and unfinished["id"] == task_id):
        raise store.incomplete_merge(primary, unfinished)
    record = store.load_task(primary, task_id)
    if kind != "merge" and record["state"] != "merging":
        raise TaskError(
            "not_merging",
            f"task {task_id} is {store.derived_state(primary, record)}, not merging; "
            "--resume and --abort finish only a merge whose process ended before its "
            "checks decided",
        )
    if kind == "abort":
        return _abort(primary, record, waited, reserved)
    if kind == "resume":
        return _resume(primary, record, waited, reserved)
    return _merge_new(primary, task_id, commands, waited, reserved)


def _refused_early(
    primary: Path,
    task_id: str,
    kind: str,
    commands: list[list[str]],
    waited,
    reserved: Path | None,
    refusal: TaskError,
) -> None:
    """Record a refusal before the attempt began as the node of the folder the server made for
    it, with the primary worktree's branch and commit as it found them, so that folder, which
    holds the merge's output, is a node like every attempt's."""
    if reserved is None or trace.read(reserved) is not None:
        return
    head = store._git(primary, "rev-parse", "--verify", "-q", "HEAD", check=False)
    name = store._git(primary, "symbolic-ref", "-q", "--short", "HEAD", check=False)
    if head.returncode != 0:
        return
    merging = {
        "branch": name.stdout.strip() if name.returncode == 0 else "HEAD",
        "before": head.stdout.strip(),
        "checks": commands if kind == "merge" else [],
    }
    Attempt(primary, task_id, kind, merging, waited, reserved).refused(refusal)


def _merge_new(
    primary: Path,
    task_id: str,
    commands: list[list[str]],
    waited,
    reserved: Path | None = None,
) -> dict:
    record, checked = store.mergeable(primary, task_id)
    branch = _primary_branch(primary, _recover_issues(primary))
    outside = _changed_outside(primary, task_id)
    before = _head(primary)
    merging = {
        "before": before,
        "checked": checked,
        "branch": branch,
        "after": None,
        "history": store.history_key(primary, task_id),
        "checks": commands,
        "since": store.now(),
        "pid": os.getpid(),
    }
    store.begin_merge(primary, task_id, merging)
    attempt = Attempt(primary, task_id, "merge", merging, waited, reserved)
    try:
        after = _merge(primary, record, merging)
    except TaskError as refusal:
        attempt.refused(refusal)
        raise
    attempt.merged(after)
    merging = store.merged_at(primary, task_id, after)["merging"]
    return _check_and_close(primary, record, merging, attempt, waited, outside)


def _check_and_close(
    primary: Path,
    record: dict,
    merging: dict,
    attempt: Attempt,
    waited,
    outside: list[str] | None = None,
) -> dict:
    """Run the merge's checks on its commit; close the task, or undo the merge and refuse."""
    try:
        return _checked_close(primary, record, merging, attempt, waited, outside)
    except TaskError as refusal:
        attempt.refused(refusal)
        raise


def _checked_close(
    primary: Path,
    record: dict,
    merging: dict,
    attempt: Attempt,
    waited,
    outside: list[str] | None = None,
) -> dict:
    task_id, branch = record["id"], merging["branch"]
    before, after = merging["before"], merging["after"]
    results = []
    for argv in merging["checks"]:
        result, problem = _check(primary, argv, attempt)
        results.append(result)
        if problem:
            left = _rollback(primary, task_id, before, problem)
            store.end_merge(primary, task_id)
            raise TaskError(
                "check_failed",
                f"after merging task {task_id} into {branch} at {after}, {problem}{left}; "
                f"the full output is in the checks of {attempt.folder}; the task is delivered "
                "again",
            )
    paths = _status(primary)
    if paths:
        problem = (
            f"the checks left {len(paths)} uncommitted path(s) in the primary worktree: "
            f"{_listed(paths)}"
        )
        left = _rollback(primary, task_id, before, problem)
        store.end_merge(primary, task_id)
        raise TaskError(
            "check_failed",
            f"after merging task {task_id} into {branch} at {after}, {problem}{left}; "
            f"the checks' output is in {attempt.folder}; the task is delivered again",
        )
    # Read before closing, which appends how the task ended.
    warnings = [
        text
        for text in (store.unwritten_decision_log(primary, record),)
        if text is not None
    ]
    warnings.extend(outside or [])
    try:
        folder = attempt.folder
        closed = store.close_locked(
            primary,
            task_id,
            "merged",
            again=f"`concorde task merge {task_id} --resume`",
            before_move=lambda: attempt.end("ok", "merged"),
            warnings=warnings,
            key=merging.get("history"),
            at=merging["since"],
            by="merge",
        )
    except TaskError as error:
        if error.code in ("decision_log_failed", "decision_log_uncommitted"):
            raise TaskError(
                error.code,
                f"task {task_id} was merged into {branch} at {after}, every check passed and "
                f"the task is closed as merged, but {error}",
            ) from error
        raise TaskError(
            error.code,
            f"task {task_id} was merged into {branch} at {after} and every check passed, but "
            f"closing it failed: {error}; the merge stays and the task stays merging, and "
            f"once the cause is fixed `concorde task merge {task_id} --resume` reruns the "
            "checks and closes it",
        ) from error
    # Still under the merge lock: the Issues the task fixed close with the merge as evidence.
    # Whatever happens to them, the sessions still end and the merge still answers.
    try:
        resolved, unresolved = store.close_resolved(primary, closed, after)
    except Exception as error:  # noqa: BLE001 -- the merge stands whatever an Issue does
        resolved, unresolved = [], [store.unclosed(closed, error)]
    warnings.extend(unresolved)
    return {
        "record": closed,
        "resolved": resolved,
        "merge": {
            "before": before,
            "after": after,
            "checks": results,
            "waited_seconds": waited,
            "log": (
                store.history_folder(primary, closed["closed"]["history"])
                / folder.relative_to(store.task_folder(primary, task_id))
            ).as_posix(),
        },
        "warnings": warnings + store.end_sessions(primary, closed),
    }


def _diverged(primary: Path, record: dict, where: str) -> TaskError:
    merging = record["merging"]
    return TaskError(
        "merge_diverged",
        f"the interrupted merge of task {record['id']} merged {merging['checked']} into "
        f"{merging['branch']} of {primary} at {merging['before']}, but the primary worktree "
        f"{where}; Tasks resets only a merge it made, so restore {merging['branch']} by hand "
        f"to {merging['before']} or to the merge commit "
        f"{merging.get('after') or '(never recorded)'} and run the command again",
    )


def _resume(primary: Path, record: dict, waited, reserved: Path | None = None) -> dict:
    """Rerun the recorded checks on the merge commit, then close or undo."""
    merging = record["merging"]
    branch = _primary_branch(primary)
    if branch != merging["branch"]:
        raise _diverged(primary, record, f"is now on branch {branch}")
    after = store.merge_commit(primary, merging)
    if after is None:
        head = _head(primary)
        if head == merging["before"]:
            detail = (
                "the commit before the merge, so the merge never landed or was undone"
            )
        else:
            detail = "neither the commit before the merge nor the merge commit"
        raise TaskError(
            "not_resumable",
            f"task {record['id']} is merging, but {branch} of {primary} is at {head}, "
            f"{detail}; only a merge whose commit is still the primary branch's head can be "
            f"checked again, and `concorde task merge {record['id']} --abort` returns the "
            "task to delivered when the branch is at the commit before the merge or at the "
            "merge commit",
        )
    merging = dict(merging, after=after)
    attempt = Attempt(primary, record["id"], "resume", merging, waited, reserved)
    return _check_and_close(primary, record, merging, attempt, waited)


def _abort(primary: Path, record: dict, waited, reserved: Path | None = None) -> dict:
    """Reset the primary branch to the commit before the merge and return the task to
    delivered."""
    merging = record["merging"]
    attempt = Attempt(primary, record["id"], "abort", merging, waited, reserved)
    try:
        return _aborted(primary, record, attempt, waited)
    except TaskError as refusal:
        attempt.refused(refusal)
        raise


def _aborted(primary: Path, record: dict, attempt: Attempt, waited) -> dict:
    merging = record["merging"]
    before = merging["before"]
    in_progress = store._git(
        primary, "rev-parse", "-q", "--verify", "MERGE_HEAD", check=False
    )
    if in_progress.returncode == 0:
        aborted = store._git(primary, "merge", "--abort", check=False)
        if aborted.returncode != 0:
            raise TaskError(
                "rollback_failed",
                f"--abort found a merge in progress in {primary}, and git merge --abort "
                f"exited {aborted.returncode}: {aborted.stderr.strip() or '(no output)'}; "
                f"the primary branch is at {_head(primary)} and its worktree as Git left it"
                + _stays_merging(record["id"]),
            )
    branch = store._git(primary, "symbolic-ref", "-q", "--short", "HEAD", check=False)
    if branch.returncode != 0 or branch.stdout.strip() != merging["branch"]:
        where = (
            f"is on branch {branch.stdout.strip()}"
            if branch.returncode == 0
            else f"has a detached HEAD at {_head(primary)}"
        )
        raise _diverged(primary, record, where)
    head = _head(primary)
    undone = None
    if head != before:
        if store.merge_commit(primary, merging) != head:
            raise _diverged(primary, record, f"is at {head}")
        _rollback(primary, record["id"], before, f"--abort of the merge at {head}")
        undone = head
    left = _status(primary)
    attempt.end("ok", "aborted")
    ended = store.end_merge(primary, record["id"])
    ended["state"] = store.derived_state(primary, ended)
    return {
        "record": ended,
        "abort": {
            "before": before,
            "undone": undone,
            "left": left,
            "waited_seconds": waited,
        },
    }


__all__ = [
    "CHECK_TIMEOUT",
    "MESSAGES",
    "OUTPUT",
    "RESERVED",
    "default_checks",
    "merge_task",
    "next_attempt",
    "parse_checks",
    "reserved_attempt",
]
