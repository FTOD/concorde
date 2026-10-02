#!/usr/bin/env python3
"""List, show and check the project's Issues, record reports and dispositions for the main
agent, recover records Issue writes published but did not commit, and archive records whose folder
does not match their status; never launch a model.

Every action but ``check`` works on the Issues the primary worktree keeps, from any worktree of the
project; ``check`` checks the record files of ``--root`` itself. Every refusal prints
``{"error": <error link>}``, the Issues component's account of what it refused and why it cannot
handle it itself, and exits 2 for a request the command cannot understand, 1 for one the Issue
rules refuse.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from concorde.issues import command  # noqa: E402
from concorde.issues.command import USAGE, Refusal  # noqa: E402


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise Refusal("usage", f"{self.prog}: {message}", USAGE)


def parser() -> Parser:
    common = Parser(add_help=False)
    common.add_argument(
        "--root", default=".", help="a worktree of the project (default: .)"
    )
    top = Parser(description=__doc__)
    actions = top.add_subparsers(dest="action", required=True, metavar="action")
    listing = actions.add_parser("list", parents=[common], help="summary row per Issue")
    listing.add_argument(
        "--status", choices=("open", "closed"), help="only Issues with this status"
    )
    listing.add_argument(
        "--module",
        help="only Issues whose latest report has this owner or reporting Module",
    )
    listing.add_argument(
        "--tier",
        choices=command.TIERS,
        action="append",
        help="only Issues whose latest report has this tier; may be repeated",
    )
    listing.add_argument(
        "--severity",
        choices=command.SEVERITIES,
        action="append",
        help="only Issues whose latest report has this severity; may be repeated",
    )
    listing.add_argument(
        "--sort",
        choices=("severity",),
        help="severity: most severe first, then by tier, decision-needed first, then the "
        "Issue reported first; Issues without a severity last",
    )
    show = actions.add_parser("show", parents=[common], help="one record")
    show.add_argument("issue_id")
    actions.add_parser(
        "check", parents=[common], help="validate every record of --root"
    )
    actions.add_parser(
        "recover",
        parents=[common],
        help="put back the records Issue writes published but did not commit",
    )
    actions.add_parser(
        "archive",
        parents=[common],
        help="move every record whose folder does not match its status into the right one",
    )
    report = actions.add_parser("report", parents=[common], help="record a report")
    report.add_argument("--file", required=True, help="Issue report JSON file")
    report.add_argument("--task", help="the task the report belongs to")
    report.add_argument(
        "--provenance",
        help="a JSON file of the provenance the caller vouches for, such as an Operation's "
        "host reporting its findings; recorded as given, without --task",
    )
    report.add_argument(
        "--check",
        action="store_true",
        help="run every check of report and record nothing",
    )
    close = actions.add_parser("close", parents=[common], help="close an open Issue")
    close.add_argument("issue_id")
    close.add_argument("--reason", required=True, choices=command.CLOSING_REASONS)
    close.add_argument("--duplicate-of")
    reopen = actions.add_parser("reopen", parents=[common], help="reopen a closed one")
    reopen.add_argument("issue_id")
    for action in (close, reopen):
        action.add_argument("--note", required=True)
        action.add_argument("--evidence", required=True, nargs="+", action="extend")
    return top


def emit(value) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def main(argv=None) -> int:
    try:
        args = parser().parse_args(argv)
        root = Path(args.root)
        if args.action == "list":
            emit(
                command.list_action(
                    root,
                    status=args.status,
                    module=args.module,
                    tiers=args.tier,
                    severities=args.severity,
                    sort=args.sort,
                )
            )
        elif args.action == "show":
            emit(command.show_action(root, args.issue_id))
        elif args.action == "check":
            answer, status = command.check(root)
            emit(answer)
            return status
        elif args.action == "recover":
            emit(command.recover_action(root))
        elif args.action == "archive":
            emit(command.archive_action(root))
        elif args.action == "report":
            emit(
                command.report_action(
                    root,
                    file=Path(args.file),
                    task=args.task,
                    check_only=args.check,
                    provenance=Path(args.provenance) if args.provenance else None,
                )
            )
        else:
            closing = args.action == "close"
            emit(
                command.dispose(
                    root,
                    args.issue_id,
                    args.reason if closing else "reopened",
                    args.note,
                    args.evidence,
                    duplicate_of=args.duplicate_of if closing else None,
                )
            )
        return 0
    except Refusal as refusal:
        emit({"error": refusal.link})
        return refusal.status
    except Exception as error:  # noqa: BLE001 -- every failure leaves a detailed error
        emit({"error": command.unexpected(error)})
        return command.REFUSED


if __name__ == "__main__":
    raise SystemExit(main())
