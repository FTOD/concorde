"""The bookkeeping command's actions: list, show and check Issues, record reports and
dispositions for a session, recover what Issue writes left uncommitted and archive misplaced
records; never launch a model.

``scripts/issues.py`` (``concorde issues``) and the project MCP server's Issue tools call the same
actions, so both give the same answer and the same refusal. Every action but ``check`` works on the
project's Issues, which the primary worktree of the repository its ``root`` lies in keeps; ``check``
checks the record files of ``root`` itself, so that a task worktree's configured check proves the
branch's code still reads the records its branch holds.

A refusal is a ``Refusal`` whose ``link`` is the Issues component's error link: its code, what it
refused and why it cannot handle it itself. A refusal whose reason is ``environment`` is a failure
of the Issue system itself, which is never reported as an Issue: its option says to carry the error
chain in the decision log, escalation or run result instead.
"""

from __future__ import annotations

import json
import re
import subprocess
import uuid
from pathlib import Path

from ..errors import from_exception, link
from ..spec.repository import SpecError, digest
from ..spec.typed_data import TypedDataError, decode
from ..tasks.store import MERGE_WAIT
from .shapes import SEVERITIES, TIERS
from .store import (
    CLOSED,
    DIRECTORY,
    RECORD_NAME,
    archive_issues,
    dispose_issue,
    issue_path,
    list_issues,
    locate_issue,
    project_root,
    read_issue,
    read_record_file,
    recover_issues,
    report_issue,
    validate_report,
)

ACTOR = "Issues (concorde issues)"
USAGE, REFUSED = 2, 1
AGENTS = ("main-agent", "task-session")
CLOSING_REASONS = ("resolved", "duplicate", "not-actionable")
# The refusals that are failures of the Issue system itself rather than of the request.
ENVIRONMENT = frozenset(
    {
        "io_error",
        "merge_busy",
        "merge_incomplete",
        "commit_failed",
        "recovery_failed",
        "uncommitted_change",
        "not_a_repository",
    }
)
# What every such failure tells its reader to do instead of reporting it as an Issue.
NOT_AN_ISSUE = (
    "carry this error chain in the task's decision log and escalation, or in the run's result; "
    "never report a failure of the Issue system as an Issue"
)


class Refusal(Exception):
    """A refused request: its code, message, exit status and, when one caused it, the error."""

    def __init__(self, code: str, message: str, status: int = REFUSED, cause=None):
        super().__init__(message)
        self.code, self.status, self.cause = code, status, cause

    @property
    def link(self) -> dict:
        return refusal_link(self.code, str(self), self.cause)


def refusal_link(code: str, message: str, cause=None) -> dict:
    """The refusal as an error link; a SpecError ``cause`` adds its location, the rule it
    breaks and its remediation."""
    environment = code in ENVIRONMENT
    where = cause.where() if isinstance(cause, SpecError) else ""
    options = [cause.remediation] if isinstance(cause, SpecError) else []
    if environment and NOT_AN_ISSUE not in " ".join(options):
        options.append(NOT_AN_ISSUE)
    return link(
        "component",
        ACTOR,
        code if re.fullmatch(r"[a-z][a-z0-9_]*", code) else "refused",
        message + (f" (at {where})" if where and where not in message else ""),
        reason="environment" if environment else "input",
        explanation=(
            cause.reason
            if isinstance(cause, SpecError)
            else "the file system or Git refused an operation the Issues command needs"
            if environment
            else "the request or the Issue record does not satisfy the Issue rules; only "
            "the caller can correct it"
        ),
        options=options,
    )


def guarded(action, *arguments, **keywords):
    """``action``'s answer, every failure turned into a ``Refusal``."""
    try:
        return action(*arguments, **keywords)
    except Refusal:
        raise
    except TypedDataError as error:
        where = f"field {error.field}: " if error.field else ""
        raise Refusal("invalid_issue", f"{where}{error}", REFUSED, error) from error
    except SpecError as error:
        # A file transaction reports a write the operating system refused as system_error.
        code = "io_error" if error.code == "system_error" else error.code
        raise Refusal(code, str(error), REFUSED, error) from error
    except OSError as error:
        raise Refusal(
            "io_error", f"{error.filename or 'file'}: {error.strerror}", REFUSED
        ) from error


def unexpected(error: BaseException) -> dict:
    """An error no rule foresaw, as the Issues component's link."""
    return from_exception(ACTOR, error)


def project(root: Path) -> Path:
    """``root`` resolved, refused with ``not_a_project`` unless it holds a Concorde project."""
    root = Path(root).resolve()
    if not (root / ".concorde/config.json").is_file():
        raise Refusal(
            "not_a_project",
            f"{root} is not an initialized Concorde project: .concorde/config.json is missing",
            USAGE,
        )
    return root


def issues_root(root: Path) -> Path:
    """The primary worktree that keeps the Issues of the project ``root`` belongs to."""
    return guarded(project_root, root)


# --- reads ------------------------------------------------------------------------------------


def list_action(
    root: Path,
    *,
    status: str | None = None,
    module: str | None = None,
    tiers: list[str] | None = None,
    severities: list[str] | None = None,
    sort: str | None = None,
) -> dict:
    """The summary rows of the Issues that pass every filter given, none given every Issue, in
    the order ``sort`` names or by identity."""
    return {
        "issues": guarded(
            list_issues,
            issues_root(project(root)),
            target_id=module,
            status=status,
            tiers=tiers,
            severities=severities,
            sort=sort,
        )
    }


def show_action(root: Path, issue_id: str) -> dict:
    record, revision, path = guarded(locate_issue, issues_root(project(root)), issue_id)
    return {"issue": record, "revision": revision, "path": path}


def registry(root: Path) -> tuple[str, bytes, list[dict]]:
    """The registry's path, bytes and Modules; a refusal names what is wrong."""
    relative = ".concorde/specs.json"
    try:
        data = (root / relative).read_bytes()
        modules = json.loads(data)["modules"]
        return relative, data, modules
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise Refusal(
            "unreadable_registry",
            f"cannot read the registry {root / relative}: {error}",
        ) from error


def check(root: Path) -> tuple[dict, int]:
    """Every record file of ``root`` reads and lies in the folder its status names, once; an open
    Issue must name an owner the registry of ``root`` still lists. The answer and the exit status:
    1 when there are errors.

    One finding per problem names the record; hidden files are not records. A closed Issue of an
    unknown owner is a note that does not fail the check; an absent directory passes.
    """
    root = project(root)
    modules = {record["id"] for record in registry(root)[2]}
    problems, notes = [], []
    places = {}
    for folder in (DIRECTORY, CLOSED):
        directory = root / folder
        if directory.is_symlink() or not directory.is_dir():
            if folder == CLOSED and (directory.is_symlink() or directory.exists()):
                problems.append(f"{folder} is not a directory of closed Issue records")
            continue
        for path in sorted(directory.iterdir()):
            if path.name.startswith("."):
                continue  # Git bookkeeping such as .gitignore, never a record.
            relative = f"{folder}/{path.name}"
            if relative == CLOSED:
                continue  # The folder of closed records, checked in its turn.
            if not RECORD_NAME.fullmatch(path.name) or not path.is_file():
                problems.append(
                    f"{relative} is not a record named I-<32 hex digits>.md"
                )
                continue
            places.setdefault(path.stem, []).append(relative)
            try:
                record, _ = read_record_file(root, relative)
            except (ValueError, OSError) as error:
                problems.append(f"{relative} is invalid: {error}")
                continue
            expected = issue_path(record["id"], record["status"])
            if relative != expected:
                problems.append(
                    f"{relative} holds {record['status']} Issue {record['id']}, whose record "
                    f"belongs at {expected}; run `concorde issues archive` in the primary "
                    "worktree, which moves it there"
                )
            latest = record["reports"][-1]
            owner = latest["report"]["owner_target_id"] or latest["source"]["target_id"]
            if owner in modules:
                continue
            message = f"{record['id']} names unknown owner {owner}"
            (problems if record["status"] == "open" else notes).append(message)
    for identifier, paths in sorted(places.items()):
        if len(paths) > 1:
            problems.append(
                f"Issue {identifier} is recorded twice, as {' and '.join(paths)}, but an Issue "
                "lives in exactly one place: keep the record whose reports and dispositions "
                "begin with the other's, remove the other with `git rm` and commit that removal "
                "alone"
            )
    return {"errors": problems, "notes": notes}, 1 if problems else 0


def recover_action(root: Path, *, wait: float = MERGE_WAIT) -> dict:
    """Put back, under the merge lock, the records Issue writes published in the primary worktree
    but did not commit; name each record change left because no Issue write made it."""
    return guarded(recover_issues, issues_root(project(root)), wait=wait)


def archive_action(root: Path, *, wait: float = MERGE_WAIT) -> dict:
    """Move, under the merge lock and in one commit, every committed record of the primary
    worktree whose folder does not match its status into the folder it names; name each move and
    each misplaced record left."""
    return guarded(archive_issues, issues_root(project(root)), wait=wait)


# --- reports ----------------------------------------------------------------------------------


def load_report(path: Path) -> dict:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        reason = getattr(error, "strerror", None) or str(error)
        raise Refusal(
            "unreadable_file", f"cannot read report file {path}: {reason}", USAGE
        ) from error
    try:
        report = decode(text)
    except TypedDataError as error:
        raise Refusal(
            "invalid_issue",
            f"report file {path} is not valid JSON: {error}",
            cause=error,
        ) from error
    return checked_report(report, f"report file {path}")


def checked_report(report, label: str) -> dict:
    """``report`` validated as a report; ``label`` names it in every refusal."""
    try:
        validate_report(report)
    except TypedDataError as error:
        where = f", field {error.field.lstrip('/')}" if error.field else ""
        raise Refusal(
            "invalid_issue", f"{label}{where}: {error}", cause=error
        ) from error
    except SpecError as error:
        raise Refusal(error.code, f"{label}: {error}", cause=error) from error
    return report


def reporting_module(label: str, report: dict, relative: str, modules: list[dict]):
    """The report's owner when it names one, else the registry's single root Module."""
    known = {module["id"] for module in modules}
    owner = report["owner_target_id"]
    if owner is not None:
        if owner not in known:
            raise Refusal(
                "unknown_owner",
                f"{label}, field owner_target_id: {owner} is not a Module of the registry "
                f"{relative}; name a registered Module or null",
            )
        return owner
    contained = {
        child["target"] for module in modules for child in module.get("contains", ())
    }
    roots = sorted(known - contained)
    if len(roots) != 1:
        raise Refusal(
            "no_reporting_module",
            f"{label} names no owner and the registry {relative} has {len(roots)} top-level "
            f"Modules ({', '.join(roots) or 'none'}) instead of one root; name the owner in "
            "owner_target_id",
        )
    return roots[0]


def head(root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--verify", "--quiet", "HEAD"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def report_action(
    root: Path,
    *,
    file: Path | None = None,
    report: dict | None = None,
    task: str | None = None,
    check_only: bool = False,
    agent: str = "main-agent",
    wait: float = MERGE_WAIT,
) -> dict:
    """Record the report in ``file`` or given as ``report``, made in the worktree ``root``.

    Its owner must be a Module of the registry of the primary worktree, which keeps the Issue;
    its evidence must exist in ``root``, or in its origin project, and its context is the registry
    of ``root``.
    """
    root = project(root)
    if task is not None and not task.strip():
        raise Refusal("usage", "--task must name a task, not an empty string", USAGE)
    if (file is None) == (report is None):
        raise Refusal(
            "usage", "give the report either as a file or as an object", USAGE
        )
    if file is not None:
        label = f"report file {file}"
        report = load_report(Path(file))
    else:
        label = "the report"
        report = checked_report(report, label)
    primary = issues_root(root)
    relative, _, modules = registry(primary)
    target = reporting_module(label, report, relative, modules)
    # A report observed in another project names its evidence in that project.
    where = Path(report["origin"]["project"]) if "origin" in report else root
    for index, item in enumerate(report["evidence"]):
        if not (where / item["path"]).exists():
            raise Refusal(
                "missing_evidence",
                f"{label}, field evidence/{index}/path: {item['path']} does not exist in "
                f"{where}"
                + (" (the report's origin project)" if where != root else ""),
            )
    if check_only:
        # The same checks as a recording, so a report that passes here is refused later only
        # for what differs between the two projects: the owner's registry or its evidence.
        return {
            "valid": True,
            **({"file": str(file)} if file is not None else {}),
            "report_key": report["report_key"],
            "reporting_module": target,
        }
    _, data, _ = registry(root)
    source = {
        "invocation_id": f"cli-{uuid.uuid4()}",
        "agent": agent,
        "operation": "issues",
        "phase": "report",
        "target_id": target,
        "context_id": digest(data),
        "change_id": task,
        "head": head(root),
    }
    receipt = guarded(report_issue, primary, report, source, wait=wait)
    _, revision = guarded(read_issue, primary, receipt["issue_id"])
    return {"receipt": receipt, "revision": revision}


# --- dispositions -----------------------------------------------------------------------------


def disposition_arguments(note: str, evidence: list[str]) -> None:
    if not note.strip():
        raise Refusal("usage", "--note must not be blank", USAGE)
    if not evidence:
        raise Refusal("usage", "--evidence needs at least one item", USAGE)
    for item in evidence:
        if not item.strip():
            raise Refusal("usage", "--evidence items must not be blank", USAGE)
    repeated = sorted({item for item in evidence if evidence.count(item) > 1})
    if repeated:
        raise Refusal(
            "usage", f"--evidence repeats {', '.join(map(repr, repeated))}", USAGE
        )


def dispose(
    root: Path,
    issue_id: str,
    reason: str,
    note: str,
    evidence: list[str],
    *,
    duplicate_of: str | None = None,
    actor: str = "main-agent",
    wait: float = MERGE_WAIT,
    locked: bool = False,
) -> dict:
    """Close (``reason`` resolved, duplicate or not-actionable) or reopen (``reopened``) the
    Issue at its current revision; ``root`` is any worktree of the project."""
    root = project(root)
    if reason != "reopened":
        if reason not in CLOSING_REASONS:
            raise Refusal(
                "usage",
                f"--reason {reason!r} is none of {', '.join(CLOSING_REASONS)}",
                USAGE,
            )
        if (reason == "duplicate") != (duplicate_of is not None):
            raise Refusal(
                "usage",
                "--duplicate-of is required with --reason duplicate and refused otherwise",
                USAGE,
            )
    disposition_arguments(note, evidence)
    primary = issues_root(root)
    _, revision = guarded(read_issue, primary, issue_id)
    new_revision = guarded(
        dispose_issue,
        primary,
        issue_id,
        revision,
        reason=reason,
        note=note,
        evidence=evidence,
        actor=actor,
        duplicate_of=duplicate_of,
        wait=wait,
        locked=locked,
    )
    status = "open" if reason == "reopened" else "closed"
    return {
        "issue_id": issue_id,
        "status": status,
        "revision": new_revision,
        "path": issue_path(issue_id, status),
    }


__all__ = [
    "ACTOR",
    "AGENTS",
    "CLOSING_REASONS",
    "REFUSED",
    "SEVERITIES",
    "TIERS",
    "USAGE",
    "Refusal",
    "archive_action",
    "check",
    "dispose",
    "list_action",
    "recover_action",
    "refusal_link",
    "report_action",
    "show_action",
    "unexpected",
]
