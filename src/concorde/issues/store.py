"""Project-level Issue records; only this store writes them.

The records live in the primary worktree's ``.concorde/issues/``, one Markdown file carrying one
closed JSON record. The JSON fence is the sole content authority, not a second rendering of prose
elsewhere. Reports are immutable observations; dispositions are separate history. Every write holds
the primary worktree's merge lock, publishes the record and commits that one file on the primary
branch before it acknowledges, so every worktree of the project reads the same Issues at once and a
write never lands between a task's merge commit and its checks. No store operation controls a
worker or resolves a task blocker, and none runs Git for anything but committing its record.

A failure of this store is never itself reported as an Issue: the Issue system that failed could not
be trusted to record it. It travels as an error chain, in a task's decision log and escalation or a
run's result.
"""

from __future__ import annotations

import copy
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
            "the identity names no Issue record under .concorde/issues/",
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
    }


DIRECTORY = ".concorde/issues"
MAX_REPORT_BYTES = 64 * 1024
MAX_RECORD_BYTES = 16 * 1024 * 1024


def issue_path(identifier: str) -> str:
    if not isinstance(identifier, str) or not re.fullmatch(
        ISSUE_ID["pattern"], identifier
    ):
        raise IssueError(
            f"{identifier!r} is not an Issue identity (I- followed by 32 lowercase hex digits)",
            "invalid_issue",
        )
    return f"{DIRECTORY}/{identifier}.md"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def validate_report(report: dict) -> None:
    """A report a caller submits: of the report contract, with its tier."""
    check_schema(report, REPORT)
    _check_report(report)


def _check_report(report: dict) -> None:
    """The rules of a report beyond its schema, also of a stored report written before tiers."""
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
        if record["schema_version"] >= RECORD_VERSION and "tier" not in report:
            raise IssueError(
                f"field tier: a report of a record of schema version {RECORD_VERSION} "
                "carries its tier",
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


def read_issue(root: Path, identifier: str) -> tuple[dict, str]:
    path = checked_path(root, issue_path(identifier))
    if not path.is_file():
        raise IssueError(
            f"Issue {identifier} does not exist: no {issue_path(identifier)}",
            "unknown_issue",
        )
    if path.stat().st_size > MAX_RECORD_BYTES:
        raise IssueError(
            f"Issue {identifier} exceeds the admitted record size of 16 MiB",
            "invalid_issue",
        )
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise IssueError(
            f"Issue {identifier} is not UTF-8 text: {error.reason} at byte {error.start}",
            "invalid_issue",
        ) from error
    return parse(text, identifier), digest(raw)


def list_issues(
    root: Path, *, target_id: str | None = None, status: str | None = None
) -> list[dict]:
    """Read-only metadata; an absent collection is empty and is never created by a query."""
    if status not in {None, "open", "closed"}:
        raise IssueError("unknown issue status", "invalid_issue")
    directory = checked_path(root, DIRECTORY)
    if not directory.exists():
        return []
    result = []
    for path in sorted(directory.glob("I-*.md")):
        record, revision = read_issue(root, path.stem)
        latest = record["reports"][-1]
        report, source = latest["report"], latest["source"]
        if status is not None and record["status"] != status:
            continue
        if target_id is not None and target_id not in {
            source["target_id"],
            report["owner_target_id"],
        }:
            continue
        result.append(
            {
                "id": record["id"],
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
    return result


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


@contextmanager
def _writing(root: Path, what: str, wait: float, locked: bool):
    """Hold the merge lock of the primary worktree ``root`` for one write.

    ``locked`` says the caller, such as a task merge closing the Issues its task resolves, holds
    it already. Refused with ``not_primary``, ``merge_busy`` or ``merge_incomplete``.
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
        yield
        return
    path = tasks.merge_lock_path(primary)
    try:
        with locks.hold(path, f"an Issue write ({what})", wait=wait):
            unfinished = tasks.unfinished_merge(primary)
            if unfinished is not None:
                raise IssueError(
                    f"{what} was not written: {tasks.incomplete_merge(primary, unfinished)}",
                    "merge_incomplete",
                )
            yield
    except locks.LockBusy as busy:
        raise IssueError(
            f"{what} waited {wait:g} s for the merge lock {path} of the primary worktree "
            f"{primary}, which is still held by {busy.holder}, and wrote nothing",
            "merge_busy",
        ) from None


def _publish(root: Path, record: dict, before: str | None, message: str) -> None:
    _publish_text(root, record["id"], render(record), before)
    _commit(root, record["id"], before, message)


def _publish_text(root: Path, identifier: str, text: str, before: str | None) -> None:
    path = issue_path(identifier)
    if len(text.encode()) > MAX_RECORD_BYTES:
        raise IssueError(
            f"Issue {identifier}: the record would exceed the admitted size of 16 MiB",
            "invalid_issue",
        )
    try:
        apply_files(
            root, [{"path": path, "before_digest": before, "content": text}], {path}
        )
    except SpecError as error:
        # Another program created or changed the record after this write read it.
        if error.code != "stale_proposal":
            raise
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
    # apply_files fsyncs the staged contents; persist the rename before acknowledging the report.
    descriptor = os.open(checked_path(root, DIRECTORY), os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _commit(root: Path, identifier: str, before: str | None, message: str) -> None:
    """Commit the record of ``identifier`` alone on the primary branch; on failure put back the
    bytes it replaced, so a refused write leaves the record as it was."""
    path = issue_path(identifier)
    target = checked_path(root, path)
    branch = _git(root, "symbolic-ref", "-q", "--short", "HEAD")
    if branch.returncode != 0:
        problem = "the primary worktree has a detached HEAD, so there is no branch to commit on"
    else:
        added = _git(root, "add", "-f", "--", path)
        done = (
            _git(
                root,
                "commit",
                "-q",
                "--only",
                "-F",
                "-",
                "--",
                path,
                stdin=f"{message}\n\nConcorde-Issue: {identifier}\n",
            )
            if added.returncode == 0
            else added
        )
        if done.returncode == 0:
            return
        output = (done.stdout + done.stderr).strip() or "(no output)"
        problem = (
            f"git {'commit' if added.returncode == 0 else 'add'} exited {done.returncode} on "
            f"{branch.stdout.strip()}: {output[-2000:]}"
        )
    _restore(root, target, path, before)
    raise IssueError(
        f"Issue {identifier} was not written: committing {path} on the primary branch of "
        f"{root} failed: {problem}; the record is back as it was",
        "commit_failed",
        path=path,
    )


def _restore(root: Path, target: Path, path: str, before: str | None) -> None:
    """Put back the record the failed commit left: the committed one, or none."""
    if _git(root, "cat-file", "-e", f"HEAD:{path}").returncode == 0:
        _git(root, "checkout", "-q", "HEAD", "--", path)
    else:
        _git(root, "rm", "-q", "--cached", "--ignore-unmatch", "--", path)
        target.unlink(missing_ok=True)


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
    exact accepted append returns its immutable receipt even after later updates.
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
    with _writing(root, f"a report to Issue {identifier}", wait, locked):
        path = checked_path(root, receipt["path"])
        record, revision = (
            read_issue(root, identifier) if path.exists() else (None, None)
        )
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
                    return receipt
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
        _publish(
            root,
            record,
            revision,
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
    with _writing(root, f"a disposition of Issue {identifier}", wait, locked):
        record, revision = read_issue(root, identifier)
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
            f"concorde: {'reopen' if reason == 'reopened' else 'close'} Issue {identifier}"
            + ("" if reason == "reopened" else f" ({reason})"),
        )
        return digest(render(updated).encode())


def resolve_report(root: Path, receipt: dict) -> dict:
    """Resolve an immutable observation, not the issue's possibly changed latest classification."""
    check_schema(receipt, RECEIPT)
    if receipt["path"] != issue_path(receipt["issue_id"]):
        raise IssueError(
            f"receipt path differs from the path of Issue {receipt['issue_id']}: "
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
