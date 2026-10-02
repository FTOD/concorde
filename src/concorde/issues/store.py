"""Project-level Issue records; only this store writes them.

The records live in the primary worktree's ``.concorde/issues/``, an open Issue's there and a
closed one's in its ``closed/`` folder, one Markdown file carrying one closed JSON record. The JSON
fence is the sole content authority, not a second rendering of prose elsewhere. Reports are
immutable observations; dispositions are separate history. Every write holds the primary worktree's
merge lock, publishes the record in the folder its status names and commits that one record on the
primary branch, moved there in the same commit when its status changed, before it acknowledges, so
every worktree of the project reads the same Issues at once and a write never lands between a
task's merge commit and its checks. Reads see only committed records: they read the primary
worktree's last commit, never its files. A record a write published but did not commit, because the
write failed and could not put it back or its process was killed, is put back by the next write
before it acts. No store operation controls a worker or resolves a task blocker, and none runs Git
for anything but reading, committing or putting back records.

A failure of this store is never itself reported as an Issue: the Issue system that failed could not
be trusted to record it. It travels as an error chain, in a task's decision log and escalation or a
run's result.
"""

from __future__ import annotations

import copy
import errno
import os
import re
import subprocess
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from ..errors import ERROR_SCHEMA
from ..spec.changes import apply_files
from ..spec.schema import ContractError, validate
from ..spec.typed_data import checked_path
from ..tasks import store as tasks
from ..tracing import locks
from .shapes import (
    ISSUE_ID,
    PROVENANCE,
    RECEIPT,
    RECORD,
    RECORD_VERSION,
    REPORT,
    SEVERITIES,
    TIERED_VERSION,
    TIERS,
)
from ..spec.repository import SpecError, digest
from ..spec.typed_data import TypedDataError, canonical, check_schema, decode


class IssueError(SpecError):
    """A refused Issue record, report or disposition, with the Issue rule it breaks."""

    DEFAULT_CODE = "invalid_issue"
    CODES = {
        "invalid_issue": (
            "an Issue record or report has exactly the fields, values and front matter the "
            "Issue contracts define",
            "correct the named field of the report or record",
        ),
        "unknown_issue": (
            "the identity names no Issue record under .concorde/issues/ or its closed/ folder",
            "run `concorde issues list` and use an existing identity",
        ),
        "closed_issue": (
            "only an open Issue may be closed or reported against",
            "reopen the Issue first, or record a new report",
        ),
        "open_issue": (
            "only a closed Issue may be reopened",
            "close the Issue first, or leave it open",
        ),
        "stale_issue": (
            "an Issue is changed only from the bytes it was read from",
            "read the Issue again and repeat the change",
        ),
        "issue_key_conflict": (
            "one report key identifies one Issue",
            "use the existing Issue with that key, or change the report's key",
        ),
        "not_a_repository": (
            "Issues are kept by the primary worktree of the project's Git repository",
            "run the command inside a worktree of the project's Git repository",
        ),
        "not_primary": (
            "Issue records are written only in the primary worktree, which commits them on the "
            "primary branch",
            "pass the primary worktree, which project_root() finds from any worktree",
        ),
        "merge_busy": (
            "an Issue write commits on the primary branch and so waits for the merge lock, which "
            "one merge, task open or task close holds at a time",
            "wait until the holder named has ended, then repeat the write; carry this error "
            "chain, never an Issue, if it cannot be written",
        ),
        "merge_incomplete": (
            "no Issue is committed on the primary branch while a task's merge there is "
            "unfinished",
            "have the main agent resume or abort the unfinished merge, then repeat the write",
        ),
        "commit_failed": (
            "an Issue write is acknowledged only once its record is committed on the primary "
            "branch",
            "fix what Git reports in the primary worktree, then repeat the write; report this "
            "failure as an error chain in the decision log, escalation or run result, never as "
            "an Issue",
        ),
        "recovery_failed": (
            "a record an Issue write published but did not commit is put back to its committed "
            "version before any other Issue write acts",
            "fix what the operating system or Git reports in the primary worktree, then run "
            "`concorde issues recover` or repeat the write, which puts the record back first; "
            "until then no read shows the uncommitted record",
        ),
        "uncommitted_change": (
            "an Issue record changes only through an Issue write, which commits it; the store "
            "never discards a change of a record it did not make",
            "inspect the change with `git diff HEAD -- <path>` in the primary worktree and "
            "revert it (`git checkout HEAD -- <path>`, or remove a file HEAD does not hold), "
            "then repeat the write",
        ),
    }


DIRECTORY = ".concorde/issues"
# Where a closed Issue's record lives; an open Issue's lives in DIRECTORY itself.
CLOSED = f"{DIRECTORY}/closed"
FOLDERS = {"open": DIRECTORY, "closed": CLOSED}
RECORD_NAME = re.compile(r"I-[0-9a-f]{32}\.md")
# The temporary files a file transaction leaves beside a record when its process is killed.
TEMPORARY = ".concorde-write-"
MAX_REPORT_BYTES = 64 * 1024
MAX_RECORD_BYTES = 16 * 1024 * 1024


def issue_path(identifier: str, status: str = "open") -> str:
    """The record path of ``identifier`` for an Issue of ``status``: ``.concorde/issues/<id>.md``
    while open, ``.concorde/issues/closed/<id>.md`` once closed."""
    if not isinstance(identifier, str) or not re.fullmatch(
        ISSUE_ID["pattern"], identifier
    ):
        raise IssueError(
            f"{identifier!r} is not an Issue identity (I- followed by 32 lowercase hex digits)",
            "invalid_issue",
        )
    return f"{FOLDERS[status]}/{identifier}.md"


def issue_paths(identifier: str) -> tuple[str, str]:
    """Both places a record of ``identifier`` may lie: the open one and the closed one."""
    return issue_path(identifier, "open"), issue_path(identifier, "closed")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def validate_report(report: dict) -> None:
    """A report a caller submits: of the report contract, with its tier and severity."""
    check_schema(report, REPORT)
    _check_report(report)


def _check_report(report: dict) -> None:
    """The rules of a report beyond its schema, also of a stored report written before tiers or
    severities."""
    if (report["type"] == "gap") != (report["subtype"] is not None):
        raise IssueError(
            "field subtype: a gap report requires a gap subtype, a bug or limitation report null",
            "invalid_issue",
        )
    if "error_chain" in report:
        try:
            validate(report["error_chain"], ERROR_SCHEMA)
        except ContractError as error:
            raise IssueError(
                f"field error_chain: not an error link of the Framework's error contract: "
                f"{error}",
                "invalid_issue",
            ) from error
    if ("issue_id" in report) != ("expected_revision" in report):
        raise IssueError(
            "fields issue_id and expected_revision: appending a report requires both, creating an Issue neither",
            "invalid_issue",
        )
    if len(canonical(report).encode()) > MAX_REPORT_BYTES:
        raise IssueError(
            "issue report exceeds 64 KiB; reference evidence instead of copying logs",
            "invalid_issue",
        )


def validate_record(record: dict) -> None:
    check_schema(record, RECORD)
    identifiers = []
    keys = []
    for observation in record["reports"]:
        report, source = observation["report"], observation["source"]
        _check_report(report)
        for field, since in (("tier", TIERED_VERSION), ("severity", RECORD_VERSION)):
            if record["schema_version"] >= since and field not in report:
                raise IssueError(
                    f"field {field}: a report of a record of schema version "
                    f"{record['schema_version']} carries its {field}",
                    "invalid_issue",
                )
        if report.get("issue_id", record["id"]) != record["id"]:
            raise IssueError("report belongs to another issue", "invalid_issue")
        if observation["id"] != digest({"report": report, "source": source}):
            raise IssueError(
                "issue observation digest differs from its content", "invalid_issue"
            )
        identifiers.append(observation["id"])
        keys.append((source["invocation_id"], report["report_key"]))
    if len(set(identifiers)) != len(identifiers) or len(set(keys)) != len(keys):
        raise IssueError("issue contains duplicate observations", "invalid_issue")
    original = record["reports"][0]
    if "issue_id" in original["report"] or record["id"] != _allocated_id(
        original["report"], original["source"]
    ):
        raise IssueError(
            "issue identity differs from its original report", "invalid_issue"
        )
    state = "open"
    for disposition in record["dispositions"]:
        if disposition["reason"] == "duplicate":
            if (
                not disposition["duplicate_of"]
                or disposition["duplicate_of"] == record["id"]
            ):
                raise IssueError(
                    "duplicate disposition requires another issue", "invalid_issue"
                )
        elif disposition["duplicate_of"] is not None:
            raise IssueError(
                "only duplicate dispositions name another issue", "invalid_issue"
            )
        reopened = disposition["reason"] == "reopened"
        if reopened != (state == "closed"):
            raise IssueError("invalid issue disposition transition", "invalid_issue")
        state = "open" if reopened else "closed"
    if record["status"] != state:
        raise IssueError(
            "issue status differs from its disposition history", "invalid_issue"
        )


def render(record: dict) -> str:
    validate_record(record)
    return f"# {record['id']}\n\n```json\n" + json_text(record) + "\n```\n"


def json_text(record: dict) -> str:
    import json

    return json.dumps(record, ensure_ascii=False, indent=2, allow_nan=False)


def parse(text: str, identifier: str) -> dict:
    """Parse one record file; every refusal names the Issue it concerns."""
    prefix = f"# {identifier}\n\n```json\n"
    if not text.startswith(prefix) or not text.endswith("\n```\n"):
        raise IssueError(
            f"Issue {identifier} must contain its identity heading and one JSON record",
            "invalid_issue",
        )
    try:
        record = decode(text[len(prefix) : -5])
        validate_record(record)
    except TypedDataError as error:
        where = f" field {error.field}" if error.field else ""
        raise IssueError(
            f"Issue {identifier}{where}: {error}", "invalid_issue"
        ) from error
    except SpecError as error:
        raise IssueError(f"Issue {identifier}: {error}", error.code) from error
    if record["id"] != identifier:
        raise IssueError(
            f"Issue {identifier}: file name and record id {record['id']} disagree",
            "invalid_issue",
        )
    return record


def read_record_file(root: Path, relative: str) -> tuple[dict, str]:
    """The record file ``relative`` of the worktree ``root``, in either folder, as it is on disk,
    committed or not, and its revision: what the store check reads."""
    identifier = Path(relative).stem
    if relative not in issue_paths(identifier):
        raise IssueError(
            f"{relative} is not the path of an Issue record: .concorde/issues/<id>.md or "
            ".concorde/issues/closed/<id>.md",
            "invalid_issue",
        )
    path = checked_path(root, relative)
    if not path.is_file():
        raise IssueError(
            f"Issue {identifier} does not exist: no {relative}",
            "unknown_issue",
        )
    if path.stat().st_size > MAX_RECORD_BYTES:
        raise IssueError(
            f"Issue {identifier} exceeds the admitted record size of 16 MiB",
            "invalid_issue",
        )
    return _parsed(path.read_bytes(), identifier)


def read_issue(root: Path, identifier: str) -> tuple[dict, str]:
    """The committed record of ``identifier`` in the last commit of the worktree ``root`` and its
    revision; a record published but not committed is not read."""
    record, revision, _ = locate_issue(root, identifier)
    return record, revision


def locate_issue(root: Path, identifier: str) -> tuple[dict, str, str]:
    """The committed record of ``identifier``, its revision and the path it is committed at, in
    whichever folder that is; ``invalid_issue`` when it is committed in both."""
    found = _committed(root, _head(root), list(issue_paths(identifier)))
    if not found:
        raise IssueError(
            f"Issue {identifier} does not exist: neither {' nor '.join(issue_paths(identifier))} "
            f"is committed in {root}",
            "unknown_issue",
        )
    _refuse_twice(identifier, sorted(found))
    [(path, raw)] = found.items()
    record, revision = _parsed(raw, identifier)
    return record, revision, path


def _refuse_twice(identifier: str, paths: list[str]) -> None:
    """``invalid_issue`` when ``identifier`` is committed at more than one path."""
    if len(paths) > 1:
        raise IssueError(
            f"Issue {identifier} is committed twice, as {' and '.join(paths)}, but an Issue "
            "lives in exactly one place; `concorde issues check` names the repair",
            "invalid_issue",
        )


def _parsed(raw: bytes, identifier: str) -> tuple[dict, str]:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise IssueError(
            f"Issue {identifier} is not UTF-8 text: {error.reason} at byte {error.start}",
            "invalid_issue",
        ) from error
    return parse(text, identifier), digest(raw)


def list_issues(
    root: Path,
    *,
    target_id: str | None = None,
    status: str | None = None,
    tiers: list[str] | tuple[str, ...] | None = None,
    severities: list[str] | tuple[str, ...] | None = None,
    sort: str | None = None,
) -> list[dict]:
    """Read-only metadata; an absent collection is empty and is never created by a query."""
    if status not in {None, "open", "closed"}:
        raise IssueError("unknown issue status", "invalid_issue")
    if tiers is not None and not set(tiers) <= set(TIERS):
        raise IssueError("unknown issue tier", "invalid_issue")
    if severities is not None and not set(severities) <= set(SEVERITIES):
        raise IssueError("unknown issue severity", "invalid_issue")
    if sort not in {None, "severity"}:
        raise IssueError(f"unknown issue sort {sort!r}: only severity", "invalid_issue")
    commit = _head(root)
    records = _committed(root, commit, [f"{DIRECTORY}/", f"{CLOSED}/"])
    places = {}
    for path in records:
        places.setdefault(Path(path).stem, []).append(path)
    result = []
    reported = {}
    for identifier, paths in sorted(places.items()):
        _refuse_twice(identifier, sorted(paths))
        record, revision = _parsed(records[paths[0]], identifier)
        latest = record["reports"][-1]
        report, source = latest["report"], latest["source"]
        if status is not None and record["status"] != status:
            continue
        if target_id is not None and target_id not in {
            source["target_id"],
            report["owner_target_id"],
        }:
            continue
        if tiers is not None and report.get("tier") not in tiers:
            continue
        if severities is not None and report.get("severity") not in severities:
            continue
        reported[record["id"]] = record["reports"][0]["created_at"]
        result.append(
            {
                "id": record["id"],
                "severity": report.get("severity"),
                "tier": report.get("tier"),
                "type": report["type"],
                "subtype": report["subtype"],
                "title": report["title"],
                "status": record["status"],
                "target_id": source["target_id"],
                "owner_target_id": report["owner_target_id"],
                "revision": revision,
            }
        )
    if sort == "severity":
        result.sort(key=lambda row: _severity_order(row, reported[row["id"]]))
    return result


def _severity_order(row: dict, reported_at: str) -> tuple:
    """Most severe first, then the strongest tier, then the Issue reported first; an Issue
    without a severity or tier after every one with it."""
    severity, tier = row["severity"], row["tier"]
    return (
        SEVERITIES.index(severity) if severity else len(SEVERITIES),
        -TIERS.index(tier) if tier else 1,
        reported_at,
        row["id"],
    )


def project_root(path: Path) -> Path:
    """The primary worktree of the Git repository ``path`` lies in, which keeps the project's
    Issues; ``not_a_repository`` outside one."""
    try:
        return tasks.primary_of(Path(path))
    except tasks.TaskError as error:
        raise IssueError(
            f"{path} is not inside a Git repository, whose primary worktree keeps the "
            f"project's Issues: {error}",
            "not_a_repository",
        ) from error


def _git(root: Path, *arguments: str, stdin: str | None = None):
    return subprocess.run(
        ["git", *arguments],
        cwd=root,
        input=stdin,
        capture_output=True,
        text=True,
        check=False,
    )


def _git_failure(root: Path, done, what: str) -> OSError:
    output = (done.stdout + done.stderr).strip() or "(no output)"
    return OSError(
        errno.EIO, f"{what} exited {done.returncode}: {output[-2000:]}", str(root)
    )


def _head(root: Path) -> str | None:
    """The commit ``HEAD`` of the worktree ``root`` names, ``None`` on an unborn branch;
    ``not_a_repository`` outside a repository."""
    found = _git(root, "rev-parse", "-q", "--verify", "HEAD^{commit}")
    if found.returncode == 0:
        return found.stdout.strip()
    if found.returncode == 1:
        return None
    raise IssueError(
        f"{root} is not inside a Git repository, whose last commit holds the project's Issues: "
        f"{found.stderr.strip()}",
        "not_a_repository",
    )


def _committed(
    root: Path, commit: str | None, pathspecs: list[str]
) -> dict[str, bytes]:
    """The bytes of every record file ``commit`` holds under ``pathspecs``, by path.

    Entries not named like a record are not records and are left out; a record path that is not a
    regular file in the commit, such as a symbolic link, is refused with ``invalid_issue``.
    """
    if commit is None:
        return {}
    listed = _git(root, "ls-tree", "-z", commit, "--", *pathspecs)
    if listed.returncode != 0:
        raise _git_failure(root, listed, f"git ls-tree of {', '.join(pathspecs)}")
    entries = {}
    for entry in filter(None, listed.stdout.split("\0")):
        meta, path = entry.split("\t", 1)
        mode, _, oid = meta.split()
        folder, _, name = path.rpartition("/")
        if folder not in FOLDERS.values() or not RECORD_NAME.fullmatch(name):
            continue
        if mode not in {"100644", "100755"}:
            raise IssueError(
                f"Issue {Path(path).stem}: {path} is committed as mode {mode}, not as a regular "
                "file",
                "invalid_issue",
            )
        entries[path] = oid
    if not entries:
        return {}
    read = subprocess.run(
        ["git", "cat-file", "--batch"],
        cwd=root,
        input="".join(f"{oid}\n" for oid in entries.values()).encode(),
        capture_output=True,
        check=False,
    )
    if read.returncode != 0:
        raise _git_failure(
            root,
            subprocess.CompletedProcess(
                read.args,
                read.returncode,
                read.stdout.decode(errors="replace"),
                read.stderr.decode(errors="replace"),
            ),
            "git cat-file --batch",
        )
    found, output, at = {}, read.stdout, 0
    for path in entries:
        end = output.index(b"\n", at)
        size = int(output[at:end].split()[2])
        found[path] = output[end + 1 : end + 1 + size]
        at = end + 1 + size + 1
        if size > MAX_RECORD_BYTES:
            raise IssueError(
                f"Issue {Path(path).stem} exceeds the admitted record size of 16 MiB",
                "invalid_issue",
            )
    return found


def _changed_entries(root: Path) -> list[tuple[str, str]]:
    """Every record file and file-transaction temporary of the Issue directory and its closed
    folder whose working tree or index state differs from ``HEAD``, as ``(git status code,
    path)``: staged, unstaged, untracked and ignored alike."""
    status = _git(
        root,
        "--no-optional-locks",
        "status",
        "--porcelain=v1",
        "-z",
        "--no-renames",
        "--untracked-files=all",
        "--ignored",
        "--",
        DIRECTORY,
    )
    if status.returncode != 0:
        raise IssueError(
            f"the uncommitted Issue records of {root} could not be found: "
            f"{_git_failure(root, status, 'git status').strerror}",
            "recovery_failed",
        )
    changed = []
    for entry in filter(None, status.stdout.split("\0")):
        code, path = entry[:2], entry[3:]
        directory, _, name = path.rpartition("/")
        if directory in (DIRECTORY, CLOSED) and (
            RECORD_NAME.fullmatch(name) or name.startswith(TEMPORARY)
        ):
            changed.append((code, path))
    return changed


def _foreign(
    root: Path, path: str, committed: bytes | None, here: bool = True
) -> str | None:
    """Why the uncommitted state of the record ``path`` is no Issue write's, or ``None`` when it
    is what a write publishes before its commit: a valid record of its Issue that continues the
    committed one, if any, with more reports or dispositions. ``committed`` is the Issue's
    committed record, at ``path`` itself when ``here`` and otherwise in its other folder, from
    which a write moving the record publishes it at ``path``."""
    target = root / path
    if target.is_symlink() or not target.is_file():
        return (
            "the committed record was deleted"
            if committed is not None and here and not target.exists()
            else "it is no regular file"
        )
    raw = target.read_bytes()
    if raw == committed and here:
        return "its file equals the committed record but its index entry does not"
    identifier = target.stem
    try:
        record, _ = _parsed(raw, identifier)
    except IssueError as error:
        return f"it is no valid record: {error}"
    if committed is None:
        return None
    try:
        earlier, _ = _parsed(committed, identifier)
    except IssueError as error:
        return f"the committed record is not valid: {error}"
    reports, dispositions = earlier["reports"], earlier["dispositions"]
    if (
        record["schema_version"] != earlier["schema_version"]
        or record["reports"][: len(reports)] != reports
        or record["dispositions"][: len(dispositions)] != dispositions
    ):
        return "it rewrites what the committed record holds instead of adding to it"
    return None


def _put_back(root: Path, path: str) -> str | None:
    """Put the record ``path`` back to its version in ``HEAD``, or remove it, from the index as
    well, when ``HEAD`` holds none; what went wrong, or ``None``."""
    if _git(root, "cat-file", "-e", f"HEAD:{path}").returncode == 0:
        done = _git(root, "checkout", "-q", "HEAD", "--", path)
        if done.returncode != 0:
            return _git_failure(root, done, f"git checkout HEAD -- {path}").strerror
        return None
    done = _git(root, "rm", "-q", "--cached", "--ignore-unmatch", "--", path)
    if done.returncode != 0:
        return _git_failure(root, done, f"git rm --cached {path}").strerror
    try:
        (root / path).unlink(missing_ok=True)
    except OSError as error:
        return f"removing {path}: {error.strerror}"
    return None


def _recover(root: Path) -> dict:
    """Put back every record an Issue write published but did not commit, and remove the
    temporaries of an interrupted file transaction, holding the merge lock.

    A change of a record that no Issue write leaves is left as it is and reported in ``left``.
    ``recovery_failed`` when something could not be put back, after every other one was tried.
    """
    recovered, left, failed = [], [], []
    changed = _changed_entries(root)
    records = [path for _, path in changed if not Path(path).name.startswith(TEMPORARY)]
    # Both places of every Issue whose record changed: a write moving a record between the
    # folders publishes it in one and removes it from the other.
    places = [place for path in records for place in issue_paths(Path(path).stem)]
    committed = _committed(root, _head(root), places) if records else {}
    for _, path in changed:
        if Path(path).name.startswith(TEMPORARY):
            try:
                (root / path).unlink(missing_ok=True)
            except OSError as error:
                failed.append(f"removing {path}: {error.strerror}")
            else:
                recovered.append({"path": path, "action": "removed"})
            continue
        other = next(place for place in issue_paths(Path(path).stem) if place != path)
        if path in committed:
            reason = _foreign(root, path, committed[path])
            # A committed record removed by a write that published it in its other folder.
            if (
                reason == "the committed record was deleted"
                and other in records
                and other not in committed
                and _foreign(root, other, committed[path], here=False) is None
            ):
                reason = None
        else:
            reason = _foreign(
                root, path, committed.get(other), here=other not in committed
            )
        if reason is not None:
            left.append({"path": path, "reason": reason})
            continue
        problem = _put_back(root, path)
        if problem is not None:
            failed.append(problem)
        else:
            action = "restored" if path in committed else "removed"
            recovered.append({"path": path, "action": action})
    if failed:
        raise IssueError(
            f"uncommitted Issue records of the primary worktree {root} could not be put back, "
            f"so no Issue write acts until they are: {'; '.join(failed)}",
            "recovery_failed",
        )
    return {"recovered": recovered, "left": left}


def _untouched(recovery: dict, identifier: str) -> None:
    """Refuse a write of ``identifier`` whose record, in either folder, holds a change no Issue
    write made."""
    for item in recovery["left"]:
        if item["path"] in issue_paths(identifier):
            path = item["path"]
            raise IssueError(
                f"Issue {identifier} was not written: its record file {path} in the primary "
                f"worktree differs from its committed version and no Issue write left that "
                f"change ({item['reason']}), so the store neither overwrites nor discards it",
                "uncommitted_change",
                path=path,
            )


@contextmanager
def _writing(root: Path, what: str, wait: float, locked: bool):
    """Hold the merge lock of the primary worktree ``root`` for one write, putting back first
    what earlier writes published but did not commit; yields what ``_recover`` did.

    ``locked`` says the caller, such as a task merge closing the Issues its task resolves, holds
    it already, so the write neither takes nor waits for it; an unfinished merge refuses it all
    the same. Refused with ``not_primary``, ``merge_busy``, ``merge_incomplete`` or
    ``recovery_failed``.
    """
    try:
        primary = tasks.require_primary(root)
    except tasks.TaskError as error:
        raise IssueError(
            f"{root} is not the primary worktree of its repository, which alone writes Issue "
            f"records: {error}",
            "not_primary",
        ) from error
    if locked:
        _refuse_unfinished_merge(primary, what)
        yield _recover(root)
        return
    path = tasks.merge_lock_path(primary)
    try:
        with locks.hold(path, f"an Issue write ({what})", wait=wait):
            _refuse_unfinished_merge(primary, what)
            yield _recover(root)
    except locks.LockBusy as busy:
        raise IssueError(
            f"{what} waited {wait:g} s for the merge lock {path} of the primary worktree "
            f"{primary}, which is still held by {busy.holder}, and wrote nothing",
            "merge_busy",
        ) from None


def _refuse_unfinished_merge(primary: Path, what: str) -> None:
    """``merge_incomplete`` while a task is stored ``merging``; the merge lock is held."""
    unfinished = tasks.unfinished_merge(primary)
    if unfinished is not None:
        raise IssueError(
            f"{what} was not written: {tasks.incomplete_merge(primary, unfinished)}",
            "merge_incomplete",
        )


def _publish(
    root: Path, record: dict, before: str | None, committed: str | None, message: str
) -> str:
    """Publish the record in the folder its status names and commit it alone, removing it from
    ``committed``, the path it is committed at, when that is the other folder; when anything
    fails after its publication, put it back before refusing, so a refusal leaves only what was
    committed. The record's path."""
    identifier = record["id"]
    path = issue_path(identifier, record["status"])
    moved = committed is not None and committed != path
    _publish_texts(
        root,
        [(identifier, path, render(record), None if moved else before)],
    )
    _settle(root, [path], [committed] if moved else [], [identifier], before, message)
    return path


def _settle(
    root: Path,
    published: list[str],
    removed: list[str],
    identifiers: list[str],
    before: str | None,
    message: str,
) -> None:
    """Remove the committed records ``removed`` that ``published`` replaces in the other folder,
    sync and commit every one of those paths alone; when anything fails, put each back first.
    ``before`` is the revision a single removed record must still have."""
    paths = [*published, *removed]
    one = len(identifiers) == 1
    what = f"Issue {identifiers[0]}" if one else f"{len(identifiers)} Issues"
    record, it, them = ("record", "it", "it") if one else ("records", "they", "them")
    stays = (
        f"the uncommitted {record} {'stays' if one else 'stay'} in the primary worktree, no "
        f"read shows {them}, and the next Issue write or `concorde issues recover` puts {them} "
        "back"
    )
    for old in removed if before is not None else ():
        # Another program changed the record after this write read it: keep its change.
        target = checked_path(root, old)
        if not target.is_file() or digest(target.read_bytes()) != before:
            left = _put_back_all(root, published)
            raise IssueError(
                f"Issue {identifiers[0]} was changed by another program after this write read "
                "it, so nothing was written"
                + (
                    ""
                    if left is None
                    else f"; putting back its record {', '.join(published)} failed: {left}; "
                    + stays
                ),
                "stale_issue" if left is None else "recovery_failed",
                path=old,
            )
    try:
        for old in removed:
            checked_path(root, old).unlink()
        _sync_directory(root)
        problem = _commit(root, paths, message, identifiers)
    except BaseException as error:
        left = _put_back_all(root, paths)
        if left is None or not isinstance(error, Exception):
            raise
        raise IssueError(
            f"{what} was not written: {type(error).__name__}: {error} after "
            f"{'its record' if one else 'their records'} {', '.join(published)} "
            f"{'was' if one else 'were'} published, and putting {'that' if one else 'those'} "
            f"{record} back failed: {left}; {stays}",
            "recovery_failed",
            path=published[0],
        ) from error
    if problem is None:
        return
    left = _put_back_all(root, paths)
    if left is not None:
        raise IssueError(
            f"{what} was not written: committing {', '.join(paths)} on the primary branch of "
            f"{root} failed: {problem}; putting the {record} back failed too: {left}; {stays}",
            "recovery_failed",
            path=published[0],
        )
    raise IssueError(
        f"{what} was not written: committing {', '.join(paths)} on the primary branch of "
        f"{root} failed: {problem}; the {record} {'is' if one else 'are'} back as "
        f"{it} {'was' if one else 'were'}",
        "commit_failed",
        path=published[0],
    )


def _put_back_all(root: Path, paths: list[str]) -> str | None:
    """Put every one of ``paths`` back, restoring the committed ones first; what went wrong, or
    ``None``."""
    problems = [_put_back(root, path) for path in reversed(paths)]
    problems = [problem for problem in problems if problem is not None]
    return "; ".join(problems) if problems else None


def _sync_directory(root: Path) -> None:
    """Persist the renames and removals of published records in both folders; apply_files fsyncs
    the staged contents."""
    for folder in (DIRECTORY, CLOSED):
        path = checked_path(root, folder)
        if not path.is_dir():
            continue
        descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)


def _publish_texts(root: Path, records: list[tuple[str, str, str, str | None]]) -> None:
    """Publish each ``(identifier, path, text, before)`` in one file transaction."""
    for identifier, _, text, _ in records:
        if len(text.encode()) > MAX_RECORD_BYTES:
            raise IssueError(
                f"Issue {identifier}: the record would exceed the admitted size of 16 MiB",
                "invalid_issue",
            )
    changes = [
        {"path": path, "before_digest": before, "content": text}
        for _, path, text, before in records
    ]
    try:
        apply_files(root, changes, {change["path"] for change in changes})
    except SpecError as error:
        # Another program created or changed the record after this write read it.
        if error.code != "stale_proposal":
            raise
        identifier, path, _, before = next(
            (item for item in records if item[1] == error.path), records[0]
        )
        happened = (
            "was created by another program while this write was creating it"
            if before is None
            else "was changed by another program after this write read it"
        )
        raise IssueError(
            f"Issue {identifier} {happened}, so nothing was written",
            "stale_issue",
            path=path,
            causes=(error,),
        ) from error


def _commit(
    root: Path, paths: list[str], message: str, identifiers: list[str]
) -> str | None:
    """Commit ``paths`` alone, the records written and those they replace, on the primary branch
    with the repository's author identity and hooks; what went wrong, or ``None``."""
    branch = _git(root, "symbolic-ref", "-q", "--short", "HEAD")
    if branch.returncode != 0:
        return "the primary worktree has a detached HEAD, so there is no branch to commit on"
    present = [path for path in paths if (root / path).exists()]
    added = _git(root, "add", "-f", "--", *present)
    trailers = "".join(f"Concorde-Issue: {identifier}\n" for identifier in identifiers)
    done = (
        _git(
            root,
            "commit",
            "-q",
            "--only",
            "-F",
            "-",
            "--",
            *paths,
            stdin=f"{message}\n\n{trailers}",
        )
        if added.returncode == 0
        else added
    )
    if done.returncode == 0:
        return None
    output = (done.stdout + done.stderr).strip() or "(no output)"
    return (
        f"git {'commit' if added.returncode == 0 else 'add'} exited {done.returncode} on "
        f"{branch.stdout.strip()}: {output[-2000:]}"
    )


def _allocated_id(report: dict, source: dict) -> str:
    return (
        "I-"
        + uuid5(
            NAMESPACE_URL, canonical([source["invocation_id"], report["report_key"]])
        ).hex
    )


def report_issue(
    root: Path,
    report: dict,
    source: dict,
    *,
    wait: float = tasks.MERGE_WAIT,
    locked: bool = False,
) -> dict:
    """Commit before replying. Identity is idempotent per trusted invocation and report key.

    ``root`` is the primary worktree (``project_root``); the write waits up to ``wait`` seconds
    for its merge lock unless the caller holds it (``locked``).
    Source is the provenance the caller supplies, never part of the report. Reusing a key with changed
    contents is an error, not an overwrite. An append needs a current byte digest; retrying the
    exact accepted append returns its receipt even after later updates, its path where the record
    lies now.
    """
    validate_report(report)
    check_schema(source, PROVENANCE)
    report, source = copy.deepcopy(report), copy.deepcopy(source)
    identifier = report.get("issue_id") or _allocated_id(report, source)
    observation_id = digest({"report": report, "source": source})
    receipt = {
        "issue_id": identifier,
        "report_id": observation_id,
        "path": issue_path(identifier),
    }
    with _writing(root, f"a report to Issue {identifier}", wait, locked) as recovery:
        _untouched(recovery, identifier)
        checked_path(root, receipt["path"])
        # The committed record alone: a report found there is committed, so its receipt holds.
        try:
            record, revision, committed = locate_issue(root, identifier)
        except IssueError as error:
            if error.code != "unknown_issue":
                raise
            record, revision, committed = None, None, None
        if record is not None:
            for previous in record["reports"]:
                if (
                    previous["source"]["invocation_id"] == source["invocation_id"]
                    and previous["report"]["report_key"] == report["report_key"]
                ):
                    if previous["id"] != observation_id:
                        raise IssueError(
                            f"report key {report['report_key']!r} of invocation "
                            f"{source['invocation_id']} already names a different observation "
                            f"in Issue {identifier}",
                            "issue_key_conflict",
                        )
                    return {**receipt, "path": committed}
            if "issue_id" not in report:
                raise IssueError(
                    f"allocated Issue identity {identifier} is already occupied",
                    "issue_key_conflict",
                )
            if revision != report["expected_revision"]:
                raise IssueError(
                    f"Issue {identifier} changed before this observation: expected revision "
                    f"{report['expected_revision']}, current revision {revision}",
                    "stale_issue",
                )
            if record["status"] != "open":
                raise IssueError(
                    f"Issue {identifier} is closed; reopen it before reporting another observation",
                    "closed_issue",
                )
        elif "issue_id" in report:
            raise IssueError(
                f"cannot append to Issue {identifier}: it does not exist",
                "unknown_issue",
            )
        else:
            record = {
                "schema_version": RECORD_VERSION,
                "id": identifier,
                "status": "open",
                "reports": [],
                "dispositions": [],
            }
        record["reports"].append(
            {
                "id": observation_id,
                "created_at": _now(),
                "report": report,
                "source": source,
            }
        )
        receipt["path"] = _publish(
            root,
            record,
            revision,
            committed,
            f"concorde: {'record' if revision is None else 'report to'} Issue {identifier}",
        )
    return receipt


def disposition_record(
    record: dict,
    *,
    reason: str,
    note: str,
    evidence: list[str],
    actor: str,
    duplicate_of: str | None = None,
    created_at: str | None = None,
) -> dict:
    """Prepare exact disposition content without writing or granting disposition authority."""
    updated = copy.deepcopy(record)
    updated["dispositions"].append(
        {
            "reason": reason,
            "note": note,
            "evidence": list(evidence),
            "duplicate_of": duplicate_of,
            "actor": actor,
            "created_at": _now() if created_at is None else created_at,
        }
    )
    updated["status"] = "open" if reason == "reopened" else "closed"
    validate_record(updated)
    return updated


def dispose_issue(
    root: Path,
    identifier: str,
    expected_revision: str,
    *,
    reason: str,
    note: str,
    evidence: list[str],
    actor: str,
    duplicate_of: str | None = None,
    duplicate_revision: str | None = None,
    created_at: str | None = None,
    wait: float = tasks.MERGE_WAIT,
    locked: bool = False,
) -> str:
    """Append the caller's disposition at exactly ``expected_revision``.

    The caller supplies authorization and checks semantic evidence before calling. This operation
    validates shape, current record bytes and referenced duplicate identity; it cannot establish
    that tests passed or that a human/product decision was authorized.
    """
    if reason == "duplicate" and duplicate_of == identifier:
        raise IssueError(
            f"Issue {identifier} cannot be a duplicate of itself", "invalid_issue"
        )
    if (reason == "duplicate") != (duplicate_of is not None):
        raise IssueError(
            f"closing Issue {identifier} as duplicate requires duplicate_of, and only a "
            "duplicate disposition names another Issue",
            "invalid_issue",
        )
    with _writing(
        root, f"a disposition of Issue {identifier}", wait, locked
    ) as recovery:
        _untouched(recovery, identifier)
        record, revision, committed = locate_issue(root, identifier)
        if revision != expected_revision:
            raise IssueError(
                f"Issue {identifier} changed before disposition: expected revision "
                f"{expected_revision}, current revision {revision}",
                "stale_issue",
            )
        if reason == "reopened" and record["status"] != "closed":
            raise IssueError(
                f"Issue {identifier} is open; only a closed Issue can be reopened",
                "open_issue",
            )
        if reason != "reopened" and record["status"] != "open":
            raise IssueError(
                f"Issue {identifier} is already closed; reopen it before closing it again",
                "closed_issue",
            )
        if reason == "duplicate":
            other, other_revision = read_issue(root, duplicate_of)
            if duplicate_revision is not None and other_revision != duplicate_revision:
                raise IssueError(
                    f"duplicate target changed before disposition: Issue {duplicate_of} "
                    f"expected revision {duplicate_revision}, current revision {other_revision}",
                    "stale_issue",
                )
            if other["status"] != "open":
                raise IssueError(
                    f"duplicate target {duplicate_of} is closed; a duplicate must name an "
                    "open Issue",
                    "invalid_issue",
                )
        updated = disposition_record(
            record,
            reason=reason,
            note=note,
            evidence=evidence,
            actor=actor,
            duplicate_of=duplicate_of,
            created_at=created_at,
        )
        _publish(
            root,
            updated,
            revision,
            committed,
            f"concorde: {'reopen' if reason == 'reopened' else 'close'} Issue {identifier}"
            + ("" if reason == "reopened" else f" ({reason})"),
        )
        return digest(render(updated).encode())


def recover_issues(
    root: Path, *, wait: float = tasks.MERGE_WAIT, locked: bool = False
) -> dict:
    """Under the merge lock, put back what Issue writes published but did not commit, as every
    write does before it acts, and say what was done and which changes were left as no Issue
    write's: ``{"recovered": [{path, action}], "left": [{path, reason}]}``."""
    with _writing(
        root, "a recovery of uncommitted Issue records", wait, locked
    ) as recovery:
        return recovery


def archive_issues(
    root: Path, *, wait: float = tasks.MERGE_WAIT, locked: bool = False
) -> dict:
    """Under the merge lock, move every committed record whose folder does not match its status
    into the folder its status names, unchanged, in one commit, and say what was moved and which
    misplaced records were left: ``{"moved": [{issue_id, from, to}], "left": [{path, reason}]}``.

    A record committed in both folders, or whose file holds a change no Issue write made, is left.
    """
    with _writing(
        root, "an archive of misplaced Issue records", wait, locked
    ) as recovery:
        records = _committed(root, _head(root), [f"{DIRECTORY}/", f"{CLOSED}/"])
        places = {}
        for path in records:
            places.setdefault(Path(path).stem, []).append(path)
        changed = {item["path"]: item["reason"] for item in recovery["left"]}
        moves, left = [], []
        for identifier, paths in sorted(places.items()):
            if len(paths) > 1:
                left.extend(
                    {
                        "path": path,
                        "reason": f"Issue {identifier} is committed in both folders",
                    }
                    for path in sorted(paths)
                )
                continue
            [path] = paths
            record, _ = _parsed(records[path], identifier)
            target = issue_path(identifier, record["status"])
            if target == path:
                continue
            foreign = [place for place in (path, target) if place in changed]
            if foreign:
                left.extend(
                    {
                        "path": place,
                        "reason": f"it holds a change no Issue write made ({changed[place]})",
                    }
                    for place in foreign
                )
                continue
            moves.append((identifier, path, target, records[path]))
        if moves:
            _publish_texts(
                root,
                [
                    (identifier, target, raw.decode("utf-8"), None)
                    for identifier, _, target, raw in moves
                ],
            )
            _settle(
                root,
                [target for _, _, target, _ in moves],
                [path for _, path, _, _ in moves],
                [identifier for identifier, _, _, _ in moves],
                None,
                f"concorde: archive {len(moves)} Issue record"
                + ("" if len(moves) == 1 else "s"),
            )
        return {
            "moved": [
                {"issue_id": identifier, "from": path, "to": target}
                for identifier, path, target, _ in moves
            ],
            "left": left,
        }


def resolve_report(root: Path, receipt: dict) -> dict:
    """Resolve an immutable observation, not the issue's possibly changed latest classification."""
    check_schema(receipt, RECEIPT)
    if receipt["path"] not in issue_paths(receipt["issue_id"]):
        raise IssueError(
            f"receipt path differs from both paths of Issue {receipt['issue_id']}: "
            f"{receipt['path']}",
            "invalid_issue",
        )
    record, _ = read_issue(root, receipt["issue_id"])
    for observation in record["reports"]:
        if observation["id"] == receipt["report_id"]:
            return observation
    raise IssueError(
        f"Issue {receipt['issue_id']} holds no report {receipt['report_id']}",
        "stale_issue",
    )
