"""``concorde workflow step|report``: run one keyed step of a workflow, or report its result.

``step`` prints the step outcome and exits 0 once the run has finished, 3 while it still runs and
1 when the step is lost, refused or rejected; with ``--stdin``, for pi's command-runner agent, it
waits until the run ends and exits 0 whenever it printed an outcome, since that agent reads only
standard output. ``report`` prints the workflow result and exits 0 when its status is ``ok`` and
1 otherwise. A malformed command line or request prints ``{"error": <link>}`` and exits 2.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .. import errors
from ..spec.schema import ContractError
from ..tasks import store
from .report import report
from .step import WAIT, StepError, check_request, run_step


class UsageError(Exception):
    pass


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise UsageError(f"{self.prog}: {message}")


def parser() -> argparse.ArgumentParser:
    command = _Parser(prog="concorde workflow")
    sub = command.add_subparsers(dest="command", required=True, parser_class=_Parser)
    step = sub.add_parser("step")
    step.add_argument("--task")
    step.add_argument("--workflow")
    step.add_argument("--mode", choices=["interactive", "no-ask"])
    step.add_argument("--key")
    step.add_argument("--answers")
    step.add_argument("--retry", action="store_true")
    step.add_argument("--restart")
    step.add_argument("--wait", type=float, default=WAIT)
    step.add_argument("--json", dest="request")
    step.add_argument("--stdin", action="store_true")
    step.add_argument("argv", nargs="*")
    report_ = sub.add_parser("report")
    report_.add_argument("--task")
    report_.add_argument("--lost", action="append", default=[])
    report_.add_argument("--stdin", action="store_true")
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


def json_in(text: str):
    """The JSON object in a prompt: the text from its first ``{`` to its last ``}``.

    pi-subagents hands a command-runner agent its assembled prompt, which may wrap the task.
    """
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < start:
        raise ValueError("no JSON object in the request")
    return json.loads(text[start : end + 1])


def step_request(arguments) -> dict:
    if arguments.stdin:
        return json_in(sys.stdin.read())
    if arguments.request:
        return json.loads(arguments.request)
    missing = [
        name
        for name in ("task", "workflow", "mode", "key")
        if getattr(arguments, name) is None
    ]
    if missing or not arguments.argv:
        raise UsageError(
            "a step needs --task, --workflow, --mode, --key and the Operation after --, or "
            "--json or --stdin; missing: "
            + ", ".join(
                [f"--{name}" for name in missing]
                + ([] if arguments.argv else ["the Operation"])
            )
        )
    answers = None
    if arguments.answers:
        value = json.loads(Path(arguments.answers).read_text(encoding="utf-8"))
        answers = value.get("answers") if isinstance(value, dict) else value
    return {
        "task": arguments.task,
        "workflow": arguments.workflow,
        "mode": arguments.mode,
        "key": arguments.key,
        "argv": list(arguments.argv),
        "answers": answers,
        "retry": arguments.retry,
        "restart": arguments.restart,
    }


def main(argv, cwd: Path | None = None) -> int:
    here = Path(cwd or Path.cwd())
    try:
        arguments = parser().parse_args(list(argv))
    except UsageError as error:
        return usage(str(error))
    try:
        primary = store.primary_of(here)
    except Exception as error:  # noqa: BLE001 -- not inside a Git repository
        return usage(
            f"{here} is not inside a Git repository: {errors.exception_detail(error)}"
        )
    if arguments.command == "report":
        task, lost = arguments.task, arguments.lost
        if arguments.stdin:
            try:
                value = json_in(sys.stdin.read())
                task, lost = value["task"], list(value.get("lost") or [])
            except (ValueError, KeyError, TypeError) as error:
                return usage(
                    f"the report request on standard input is not usable: {error}"
                )
        if not task:
            return usage("a report needs --task, or --stdin with a JSON request")
        try:
            result = report(primary, task, lost)
        except Exception as error:
            if isinstance(error, store.TaskError):
                raise
            link = errors.link(
                "component",
                "Workflows (concorde workflow report)",
                "report_failed",
                f"the report of task {task} could not be built: "
                f"{errors.exception_detail(error)}",
                reason="capability",
                explanation="a report that cannot be built says why instead of ending in a "
                "traceback, so that the workflow's error chain stays complete",
                options=["repair the cause and run the report again"],
            )
            sys.stdout.write(json.dumps({"error": link}, indent=2) + "\n")
            return 1
            link = errors.link(
                "component",
                "Workflows (concorde workflow report)",
                error.code,
                str(error),
                reason="input",
                explanation="a report is built from a task record that names a workflow",
            )
            sys.stdout.write(json.dumps({"error": link}, indent=2) + "\n")
            return 1
        sys.stdout.write(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
        return 0 if arguments.stdin or result["status"] == "ok" else 1
    try:
        request = check_request(step_request(arguments))
    except (UsageError, ValueError, OSError, ContractError) as error:
        return usage(f"the step request is not usable: {error}")
    try:
        status, value = run_step(
            primary, request, None if arguments.stdin else arguments.wait
        )
    except StepError as refusal:
        sys.stdout.write(json.dumps({"error": refusal.link}, indent=2) + "\n")
        return 0 if arguments.stdin else 1
    sys.stdout.write(json.dumps(value, indent=2, ensure_ascii=False) + "\n")
    return 0 if arguments.stdin else status


__all__ = ["main"]
