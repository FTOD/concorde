"""Git-versioned issue records; only the trusted host writes this directory.

One Markdown file carries one closed JSON record. The JSON fence is the sole content authority,
not a second rendering of prose elsewhere. Reports are immutable observations; dispositions are
separate history. No store operation controls a worker, resolves a task blocker or executes Git.
"""

from __future__ import annotations

import copy
import fcntl
import os
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from ..spec.changes import apply_files
from ..spec.issue_shapes import (
    ISSUE_ID,
    LEGACY_RECORD,
    PROVENANCE,
    RECEIPT,
    RECORD,
    REPORT,
)
from ..spec.repository import SpecError, digest
from ..spec.typed_data import canonical, check_schema, checked_path, decode

DIRECTORY = ".concorde/issues"
MAX_REPORT_BYTES = 64 * 1024
MAX_RECORD_BYTES = 16 * 1024 * 1024


def issue_path(identifier: str) -> str:
    check_schema(identifier, ISSUE_ID)
    return f"{DIRECTORY}/{identifier}.md"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def validate_report(report: dict) -> None:
    check_schema(report, REPORT)
    if (report["type"] == "gap") != (report["subtype"] is not None):
        raise SpecError("only gap issues require a gap subtype", "invalid_issue")
    if ("issue_id" in report) != ("expected_revision" in report):
        raise SpecError(
            "appending a report requires issue_id and expected_revision together",
            "invalid_issue",
        )
    if len(canonical(report).encode()) > MAX_REPORT_BYTES:
        raise SpecError(
            "issue report exceeds 64 KiB; reference evidence instead of copying logs",
            "invalid_issue",
        )


def validate_record(record: dict) -> None:
    historical = isinstance(record, dict) and record.get("schema_version") == 1
    check_schema(record, LEGACY_RECORD if historical else RECORD)
    identifiers = []
    keys = []
    for observation in record["reports"]:
        report, source = observation["report"], observation["source"]
        validate_report(report)
        if report.get("issue_id", record["id"]) != record["id"]:
            raise SpecError("report belongs to another issue", "invalid_issue")
        if observation["id"] != digest({"report": report, "source": source}):
            raise SpecError(
                "issue observation digest differs from its content", "invalid_issue"
            )
        identifiers.append(observation["id"])
        keys.append((source["invocation_id"], report["report_key"]))
    if len(set(identifiers)) != len(identifiers) or len(set(keys)) != len(keys):
        raise SpecError("issue contains duplicate observations", "invalid_issue")
    original = record["reports"][0]
    if "issue_id" in original["report"] or record["id"] != _allocated_id(
        original["report"], original["source"]
    ):
        raise SpecError(
            "issue identity differs from its original report", "invalid_issue"
        )
    state = "open"
    for disposition in record["dispositions"]:
        if disposition["reason"] == "duplicate":
            if (
                not disposition["duplicate_of"]
                or disposition["duplicate_of"] == record["id"]
            ):
                raise SpecError(
                    "duplicate disposition requires another issue", "invalid_issue"
                )
        elif disposition["duplicate_of"] is not None:
            raise SpecError(
                "only duplicate dispositions name another issue", "invalid_issue"
            )
        reopened = disposition["reason"] == "reopened"
        if reopened != (state == "closed"):
            raise SpecError("invalid issue disposition transition", "invalid_issue")
        state = "open" if reopened else "closed"
    if record["status"] != state:
        raise SpecError(
            "issue status differs from its disposition history", "invalid_issue"
        )


def require_current_record(record: dict) -> None:
    if record.get("schema_version") != 2:
        raise SpecError(
            "historical Issue schema 1 is read-only; preserve its observations and create a "
            "new schema-2 Issue referencing the historical record before further work",
            "unsupported_issue_version",
        )


def render(record: dict) -> str:
    require_current_record(record)
    validate_record(record)
    return f"# {record['id']}\n\n```json\n" + json_text(record) + "\n```\n"


def json_text(record: dict) -> str:
    import json

    return json.dumps(record, ensure_ascii=False, indent=2, allow_nan=False)


def parse(text: str, identifier: str) -> dict:
    prefix = f"# {identifier}\n\n```json\n"
    if not text.startswith(prefix) or not text.endswith("\n```\n"):
        raise SpecError(
            "issue must contain its identity heading and one JSON record",
            "invalid_issue",
        )
    record = decode(text[len(prefix) : -5])
    validate_record(record)
    if record["id"] != identifier:
        raise SpecError("issue filename and identity disagree", "invalid_issue")
    return record


def read_issue(root: Path, identifier: str) -> tuple[dict, str]:
    path = checked_path(root, issue_path(identifier))
    if not path.is_file():
        raise SpecError(f"issue does not exist: {identifier}", "unknown_issue")
    if path.stat().st_size > MAX_RECORD_BYTES:
        raise SpecError("issue record exceeds the admitted size", "invalid_issue")
    raw = path.read_bytes()
    return parse(raw.decode("utf-8"), identifier), digest(raw)


def list_issues(
    root: Path, *, target_id: str | None = None, status: str | None = None
) -> list[dict]:
    """Read-only metadata; an absent collection is empty and is never created by a query."""
    if status not in {None, "open", "closed"}:
        raise SpecError("unknown issue status", "invalid_issue")
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


@contextmanager
def _lock(root: Path):
    # Runs is already host-local ignored state. No mutable allocation index enters Git history.
    from ..harness.status_store import run_path

    lock = run_path(root, ".concorde/runs/issues.lock")
    lock.parent.mkdir(parents=True, exist_ok=True)
    with lock.open("a+b") as stream:
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def _publish(root: Path, record: dict, before: str | None) -> None:
    _publish_text(root, record["id"], render(record), before)


def _publish_text(root: Path, identifier: str, text: str, before: str | None) -> None:
    path = issue_path(identifier)
    if len(text.encode()) > MAX_RECORD_BYTES:
        raise SpecError("issue record exceeds the admitted size", "invalid_issue")
    apply_files(
        root, [{"path": path, "before_digest": before, "content": text}], {path}
    )
    # apply_files fsyncs the staged contents; persist the rename before acknowledging the report.
    descriptor = os.open(checked_path(root, DIRECTORY), os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _allocated_id(report: dict, source: dict) -> str:
    return (
        "I-"
        + uuid5(
            NAMESPACE_URL, canonical([source["invocation_id"], report["report_key"]])
        ).hex
    )


def report_issue(root: Path, report: dict, source: dict) -> dict:
    """Persist before replying. Identity is idempotent per trusted invocation and report key.

    Source is issued by the host, never accepted as worker parameters. Reusing a key with changed
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
    with _lock(root):
        path = checked_path(root, receipt["path"])
        record, revision = (
            read_issue(root, identifier) if path.exists() else (None, None)
        )
        if record is not None:
            require_current_record(record)
            for previous in record["reports"]:
                if (
                    previous["source"]["invocation_id"] == source["invocation_id"]
                    and previous["report"]["report_key"] == report["report_key"]
                ):
                    if previous["id"] != observation_id:
                        raise SpecError(
                            "report key already names a different observation",
                            "issue_key_conflict",
                        )
                    return receipt
            if "issue_id" not in report:
                raise SpecError(
                    "allocated issue identity is already occupied", "issue_key_conflict"
                )
            if revision != report["expected_revision"]:
                raise SpecError("issue changed before this observation", "stale_issue")
            if record["status"] != "open":
                raise SpecError(
                    "reopen the issue before reporting another observation",
                    "closed_issue",
                )
        elif "issue_id" in report:
            raise SpecError("cannot append to a missing issue", "unknown_issue")
        else:
            record = {
                "schema_version": 2,
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
        _publish(root, record, revision)
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
    require_current_record(record)
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
) -> str:
    """Trusted host disposition, never a worker reporting-tool action.

    The caller supplies authorization and checks semantic evidence before calling. This operation
    validates shape, current record bytes and referenced duplicate identity; it cannot establish
    that tests passed or that a human/product decision was authorized.
    """
    with _lock(root):
        record, revision = read_issue(root, identifier)
        if revision != expected_revision:
            raise SpecError("issue changed before disposition", "stale_issue")
        if reason == "duplicate" and duplicate_of:
            other, other_revision = read_issue(root, duplicate_of)
            if duplicate_revision is not None and other_revision != duplicate_revision:
                raise SpecError(
                    "duplicate target changed before disposition", "stale_issue"
                )
            if other["status"] != "open":
                raise SpecError(
                    "duplicate target must be an open canonical issue", "invalid_issue"
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
        _publish(root, updated, revision)
        return digest(render(updated).encode())


def restore_issue(
    root: Path, identifier: str, original: bytes, expected_revision: str
) -> None:
    """Undo only exact owned disposition bytes, idempotently, under the report/disposition lock."""
    record = parse(original.decode("utf-8"), identifier)
    require_current_record(record)
    if record["status"] != "open":
        raise SpecError(
            "disposition recovery requires an open before-image", "invalid_issue"
        )
    before = digest(original)
    with _lock(root):
        _, revision = read_issue(root, identifier)
        if revision == before:
            return  # A previous rollback completed but its bookkeeping acknowledgement was lost.
        if revision != expected_revision:
            raise SpecError(
                "Issue changed after the pending disposition; preserve concurrent edits",
                "stale_issue",
            )
        _publish_text(root, identifier, original.decode("utf-8"), revision)


def resolve_report(root: Path, receipt: dict) -> dict:
    """Resolve an immutable observation, not the issue's possibly changed latest classification."""
    check_schema(receipt, RECEIPT)
    if receipt["path"] != issue_path(receipt["issue_id"]):
        raise SpecError("issue receipt path differs from identity", "invalid_issue")
    record, _ = read_issue(root, receipt["issue_id"])
    for observation in record["reports"]:
        if observation["id"] == receipt["report_id"]:
            return observation
    raise SpecError("issue observation is absent", "stale_issue")
