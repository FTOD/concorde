#!/usr/bin/env python3
"""List, show and check branch-local Issues, and record reports and dispositions for the main
agent; never launch a model.

Every refusal prints ``{"error": <error link>}``, the Issues component's account of what it refused
and why it cannot handle it itself, and exits 2 for a request the command cannot understand, 1 for
one the Issue rules refuse.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from concorde.errors import link  # noqa: E402
from concorde.issues.store import (  # noqa: E402
    DIRECTORY,
    dispose_issue,
    list_issues,
    read_issue,
    report_issue,
    validate_report,
)
from concorde.spec.repository import SpecError, digest  # noqa: E402
from concorde.spec.typed_data import TypedDataError, decode  # noqa: E402

RECORD_NAME = re.compile(r"I-[0-9a-f]{32}\.md")
USAGE, REFUSED = 2, 1
ACTOR = "main-agent"
CLOSING_REASONS = ("resolved", "duplicate", "not-actionable")


class Refusal(Exception):
    def __init__(self, code: str, message: str, status: int = REFUSED, cause=None):
        super().__init__(message)
        self.code, self.status, self.cause = code, status, cause


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise Refusal("usage", f"{self.prog}: {message}", USAGE)


def parser() -> Parser:
    common = Parser(add_help=False)
    common.add_argument("--root", default=".", help="project root (default: .)")
    top = Parser(description=__doc__)
    actions = top.add_subparsers(dest="action", required=True, metavar="action")
    actions.add_parser("list", parents=[common], help="summary row per Issue")
    show = actions.add_parser("show", parents=[common], help="one record")
    show.add_argument("issue_id")
    actions.add_parser("check", parents=[common], help="validate every record")
    report = actions.add_parser("report", parents=[common], help="record a report")
    report.add_argument("--file", required=True, help="Issue report JSON file")
    report.add_argument("--task", help="the task the report belongs to")
    close = actions.add_parser("close", parents=[common], help="close an open Issue")
    close.add_argument("issue_id")
    close.add_argument("--reason", required=True, choices=CLOSING_REASONS)
    close.add_argument("--duplicate-of")
    reopen = actions.add_parser("reopen", parents=[common], help="reopen a closed one")
    reopen.add_argument("issue_id")
    for action in (close, reopen):
        action.add_argument("--note", required=True)
        action.add_argument("--evidence", required=True, nargs="+", action="extend")
    return top


def main(argv=None) -> int:
    try:
        args = parser().parse_args(argv)
        root = Path(args.root).resolve()
        if not (root / ".concorde/config.json").is_file():
            raise Refusal(
                "not_a_project",
                f"{root} is not an initialized Concorde project: .concorde/config.json is missing",
                USAGE,
            )
        return ACTIONS[args.action](root, args)
    except Refusal as refusal:
        return refuse(refusal.code, str(refusal), refusal.status, refusal.cause)
    except TypedDataError as error:
        where = f"field {error.field}: " if error.field else ""
        return refuse("invalid_issue", f"{where}{error}", REFUSED, error)
    except SpecError as error:
        return refuse(error.code, str(error), REFUSED, error)
    except OSError as error:
        return refuse(
            "io_error", f"{error.filename or 'file'}: {error.strerror}", REFUSED
        )
    except Exception as error:  # noqa: BLE001 -- every failure leaves a detailed error
        from concorde.errors import from_exception

        print(
            json.dumps(
                {"error": from_exception("Issues (concorde issues)", error)},
                ensure_ascii=False,
                indent=2,
            )
        )
        return REFUSED


def refuse(code: str, message: str, status: int, cause=None) -> int:
    """Print the refusal as an error link; a SpecError ``cause`` adds its location, the
    rule it breaks and its remediation."""
    environment = code in ("io_error", "git_failed")
    where = cause.where() if isinstance(cause, SpecError) else ""
    error = link(
        "component",
        "Issues (concorde issues)",
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
        options=[cause.remediation] if isinstance(cause, SpecError) else [],
    )
    print(json.dumps({"error": error}, ensure_ascii=False, indent=2))
    return status


def emit(value) -> int:
    print(json.dumps(value, ensure_ascii=False, indent=2))
    return 0


def list_action(root: Path, args) -> int:
    return emit({"issues": list_issues(root)})


def show_action(root: Path, args) -> int:
    record, revision = read_issue(root, args.issue_id)
    return emit({"issue": record, "revision": revision})


def registry(root: Path) -> tuple[str, bytes, list[dict]]:
    """The configured registry's path, bytes and Modules; a refusal names what is wrong."""
    config_path = root / ".concorde/config.json"
    try:
        relative = json.loads(config_path.read_text(encoding="utf-8"))["registry"]
        data = (root / relative).read_bytes()
        modules = json.loads(data)["modules"]
        return relative, data, modules
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise Refusal(
            "unreadable_registry",
            f"cannot read the registry configured in {config_path}: {error}",
        ) from error


def check(root: Path, args=None) -> int:
    """Every record reads; an open Issue must name an owner the registry still lists.

    One finding per problem names the record; hidden files are not records. A closed Issue of an
    unknown owner is a note that does not fail the check; an absent directory passes.
    """
    modules = {record["id"] for record in registry(root)[2]}
    problems, notes = [], []
    directory = root / DIRECTORY
    entries = sorted(directory.iterdir()) if directory.is_dir() else []
    for path in entries:
        if path.name.startswith("."):
            continue  # Git bookkeeping such as .gitignore, never a record.
        relative = f"{DIRECTORY}/{path.name}"
        if not RECORD_NAME.fullmatch(path.name) or not path.is_file():
            problems.append(f"{relative} is not a record named I-<32 hex digits>.md")
            continue
        try:
            record, _ = read_issue(root, path.stem)
        except (ValueError, OSError) as error:
            problems.append(f"{relative} is invalid: {error}")
            continue
        latest = record["reports"][-1]
        owner = latest["report"]["owner_target_id"] or latest["source"]["target_id"]
        if owner in modules:
            continue
        message = f"{record['id']} names unknown owner {owner}"
        (problems if record["status"] == "open" else notes).append(message)
    print(
        json.dumps({"errors": problems, "notes": notes}, ensure_ascii=False, indent=2)
    )
    return 1 if problems else 0


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
        validate_report(report)
    except TypedDataError as error:
        if error.code == "invalid_json":
            raise Refusal(
                "invalid_issue",
                f"report file {path} is not valid JSON: {error}",
                cause=error,
            ) from error
        where = f", field {error.field.lstrip('/')}" if error.field else ""
        raise Refusal(
            "invalid_issue", f"report file {path}{where}: {error}", cause=error
        ) from error
    except SpecError as error:
        raise Refusal(
            error.code, f"report file {path}: {error}", cause=error
        ) from error
    return report


def reporting_module(path: Path, report: dict, relative: str, modules: list[dict]):
    """The report's owner when it names one, else the registry's single root Module."""
    known = {module["id"] for module in modules}
    owner = report["owner_target_id"]
    if owner is not None:
        if owner not in known:
            raise Refusal(
                "unknown_owner",
                f"report file {path}, field owner_target_id: {owner} is not a Module of "
                f"the registry {relative}; name a registered Module or null",
            )
        return owner
    contained = {
        child["target"] for module in modules for child in module.get("contains", ())
    }
    roots = sorted(known - contained)
    if len(roots) != 1:
        raise Refusal(
            "no_reporting_module",
            f"report file {path} names no owner and the registry {relative} has "
            f"{len(roots)} top-level Modules ({', '.join(roots) or 'none'}) instead of one "
            "root; name the owner in owner_target_id",
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


def report_action(root: Path, args) -> int:
    if args.task is not None and not args.task.strip():
        raise Refusal("usage", "--task must name a task, not an empty string", USAGE)
    path = Path(args.file)
    report = load_report(path)
    relative, data, modules = registry(root)
    target = reporting_module(path, report, relative, modules)
    for index, item in enumerate(report["evidence"]):
        if not (root / item["path"]).exists():
            raise Refusal(
                "missing_evidence",
                f"report file {path}, field evidence/{index}/path: {item['path']} does not "
                f"exist in {root}",
            )
    source = {
        "invocation_id": f"cli-{uuid.uuid4()}",
        "agent": ACTOR,
        "operation": "issues",
        "phase": "report",
        "target_id": target,
        "context_id": digest(data),
        "change_id": args.task,
        "head": head(root),
    }
    receipt = report_issue(root, report, source)
    _, revision = read_issue(root, receipt["issue_id"])
    return emit({"receipt": receipt, "revision": revision})


def disposition_arguments(args) -> None:
    if not args.note.strip():
        raise Refusal("usage", "--note must not be blank", USAGE)
    for item in args.evidence:
        if not item.strip():
            raise Refusal("usage", "--evidence items must not be blank", USAGE)
    repeated = sorted({item for item in args.evidence if args.evidence.count(item) > 1})
    if repeated:
        raise Refusal(
            "usage", f"--evidence repeats {', '.join(map(repr, repeated))}", USAGE
        )


def dispose(root: Path, args, reason: str, duplicate_of: str | None) -> int:
    disposition_arguments(args)
    _, revision = read_issue(root, args.issue_id)
    new_revision = dispose_issue(
        root,
        args.issue_id,
        revision,
        reason=reason,
        note=args.note,
        evidence=args.evidence,
        actor=ACTOR,
        duplicate_of=duplicate_of,
    )
    status = "open" if reason == "reopened" else "closed"
    return emit({"issue_id": args.issue_id, "status": status, "revision": new_revision})


def close_action(root: Path, args) -> int:
    if (args.reason == "duplicate") != (args.duplicate_of is not None):
        raise Refusal(
            "usage",
            "--duplicate-of is required with --reason duplicate and refused otherwise",
            USAGE,
        )
    return dispose(root, args, args.reason, args.duplicate_of)


def reopen_action(root: Path, args) -> int:
    return dispose(root, args, "reopened", None)


ACTIONS = {
    "list": list_action,
    "show": show_action,
    "check": check,
    "report": report_action,
    "close": close_action,
    "reopen": reopen_action,
}


if __name__ == "__main__":
    raise SystemExit(main())
