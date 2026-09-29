"""``concorde workflow step|report``: run one keyed step of a workflow, or report its result.

Both work in the bound workspace they are started in, whose binding names it; a workflow never
names a task. ``step`` prints the step outcome and exits 0 once the run has finished, 3 while it
still runs and 1 when the step is lost, refused or rejected. ``report`` prints the workflow result and exits 0 when its status is ``ok`` and
1 otherwise. A malformed command line or request prints ``{"error": <link>}`` and exits 2.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .. import errors
from ..spec.schema import ContractError
from .report import report
from .step import WAIT, StepError, check_request, run_step
from .store import WorkflowError, workspace


class UsageError(Exception):
    pass


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise UsageError(f"{self.prog}: {message}")


def parser() -> argparse.ArgumentParser:
    command = _Parser(prog="concorde workflow")
    sub = command.add_subparsers(dest="command", required=True, parser_class=_Parser)
    step = sub.add_parser("step")
    step.add_argument("--workflow")
    step.add_argument("--mode", choices=["interactive", "no-ask"])
    step.add_argument("--key")
    step.add_argument("--answers")
    step.add_argument("--retry", action="store_true")
    step.add_argument("--restart")
    step.add_argument("--wait", type=float, default=WAIT)
    step.add_argument("--json", dest="request")
    step.add_argument("argv", nargs="*")
    report_ = sub.add_parser("report")
    report_.add_argument("--lost", action="append", default=[])
    return command


def usage(message: str) -> int:
    link = errors.link(
        "component",
        "Workflows (concorde workflow)",
        "invalid_request",
        message,
        reason="input",
        explanation="the command runs only a complete, well-formed step or report request",
        options=["correct the command line or the request and run it again"],
    )
    sys.stdout.write(json.dumps({"error": link}, indent=2) + "\n")
    return 2


def step_request(arguments) -> dict:
    if arguments.request:
        return json.loads(arguments.request)
    missing = [
        name for name in ("workflow", "mode", "key") if getattr(arguments, name) is None
    ]
    if missing or not arguments.argv:
        raise UsageError(
            "a step needs --workflow, --mode, --key and the Operation or command after --, or "
            "--json; missing: "
            + ", ".join(
                [f"--{name}" for name in missing]
                + ([] if arguments.argv else ["the Operation or command"])
            )
        )
    answers = None
    if arguments.answers:
        value = json.loads(Path(arguments.answers).read_text(encoding="utf-8"))
        answers = value.get("answers") if isinstance(value, dict) else value
    return {
        "workflow": arguments.workflow,
        "mode": arguments.mode,
        "key": arguments.key,
        "argv": list(arguments.argv),
        "answers": answers,
        "retry": arguments.retry,
        "restart": arguments.restart,
    }


def refused(error: WorkflowError, command: str) -> int:
    link = errors.link(
        "component",
        f"Workflows (concorde workflow {command})",
        error.code,
        str(error),
        reason="input",
        explanation="a workflow runs and reports only in a bound workspace whose workflow "
        "record admits the request",
        options=["run it in the workspace the workflow belongs to"],
    )
    sys.stdout.write(json.dumps({"error": link}, indent=2) + "\n")
    return 1


def main(argv, cwd: Path | None = None) -> int:
    here = Path(cwd or Path.cwd())
    try:
        arguments = parser().parse_args(list(argv))
    except UsageError as error:
        return usage(str(error))
    try:
        space = workspace(here)
    except WorkflowError as error:
        return refused(error, arguments.command)
    if arguments.command == "report":
        try:
            result = report(space, arguments.lost)
        except WorkflowError as error:
            return refused(error, "report")
        except Exception as error:  # noqa: BLE001 -- say why instead of a traceback
            link = errors.link(
                "component",
                "Workflows (concorde workflow report)",
                "report_failed",
                f"the report of workspace {space.name} could not be built: "
                f"{errors.exception_detail(error)}",
                reason="capability",
                explanation="a report that cannot be built says why instead of ending in a "
                "traceback, so that the workflow's error chain stays complete",
                options=["repair the cause and run the report again"],
            )
            sys.stdout.write(json.dumps({"error": link}, indent=2) + "\n")
            return 1
        sys.stdout.write(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
        return 0 if result["status"] == "ok" else 1
    try:
        request = check_request(step_request(arguments))
    except (UsageError, ValueError, OSError, ContractError) as error:
        return usage(f"the step request is not usable: {error}")
    try:
        status, value = run_step(space, request, arguments.wait)
    except StepError as refusal:
        sys.stdout.write(json.dumps({"error": refusal.link}, indent=2) + "\n")
        return 1
    sys.stdout.write(json.dumps(value, indent=2, ensure_ascii=False) + "\n")
    return status


__all__ = ["main"]
