"""``concorde task open|list|show|close|escalate``: print one JSON value; refusals exit 1, bad
usage 2.

A refusal prints ``{"error": <error link>}``: the Tasks component's account of what it refused,
why it cannot handle it, and what the caller can do. ``escalate`` records the main agent's own
link of an error chain, with the errors of the named runs or files as its causes.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .. import errors
from ..spec.schema import ContractError, validate
from . import store

# Why Tasks cannot handle each refusal itself; every other code is an input the caller corrects.
HANDLING = {
    "git_failed": ("environment", "Git refused a command Tasks needs"),
    "worktree_failed": ("environment", "Git could not add or remove the task worktree"),
    "record_conflict": (
        "environment",
        "other processes kept changing the task record while Tasks retried",
    ),
    "record_unreadable": (
        "environment",
        "the task record on disk is not readable JSON",
    ),
    "dirty_worktree": (
        "decision",
        "discarding uncommitted changes of a task worktree is the caller's decision",
    ),
    "not_merged": (
        "decision",
        "closing a task as merged requires its last delivery to be contained in the primary "
        "branch; merging is the main agent's step",
    ),
}
OPTIONS = {
    "unknown_task": ["run concorde task list to see the tasks"],
    "unknown_module": ["name registered Modules, or register the Module first"],
    "dirty_worktree": [
        "deliver or discard the changes",
        "close with --abandoned --force",
    ],
    "not_merged": ["merge the task branch, then close the task"],
}


def refusal(command: str, error: store.TaskError) -> dict:
    reason, explanation = HANDLING.get(
        error.code,
        (
            "input",
            "the request names a task, Module, state or path Tasks does not admit",
        ),
    )
    return errors.link(
        "component",
        f"Tasks (concorde task {command})",
        error.code,
        str(error),
        reason=reason,
        explanation=explanation,
        options=OPTIONS.get(error.code, []),
    )


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise store.TaskError("invalid_command", f"{self.prog}: {message}")


def parser() -> argparse.ArgumentParser:
    root = _Parser(prog="concorde task")
    commands = root.add_subparsers(dest="command", required=True, parser_class=_Parser)
    opening = commands.add_parser("open")
    opening.add_argument("task_id")
    opening.add_argument("--goal", required=True)
    opening.add_argument("--modules", required=True)
    opening.add_argument("--base")
    opening.add_argument("--path")
    listing = commands.add_parser("list")
    listing.add_argument("--state", choices=store.STATES)
    showing = commands.add_parser("show")
    showing.add_argument("task_id")
    closing = commands.add_parser("close")
    closing.add_argument("task_id")
    mode = closing.add_mutually_exclusive_group(required=True)
    mode.add_argument("--merged", action="store_true")
    mode.add_argument("--abandoned", action="store_true")
    closing.add_argument("--force", action="store_true")
    escalating = commands.add_parser("escalate")
    escalating.add_argument("task_id")
    escalating.add_argument("--code", required=True)
    escalating.add_argument("--detail", required=True)
    escalating.add_argument("--reason", required=True, choices=list(errors.REASONS))
    escalating.add_argument("--explanation", required=True)
    escalating.add_argument("--run", action="append", default=[])
    escalating.add_argument("--error-file", action="append", default=[])
    escalating.add_argument("--attempt", action="append", default=[])
    escalating.add_argument("--option", action="append", default=[])
    escalating.add_argument("--recommendation", default="")
    return root


def _checked(value, source: str) -> dict:
    try:
        validate(value, errors.ERROR_SCHEMA)
    except ContractError as error:
        raise store.TaskError(
            "invalid_error", f"{source} is not an error link: {error}"
        ) from error
    return value


def _run_error(primary: Path, task: dict, run_id: str) -> dict:
    runs = {run["run_id"]: run for run in task["runs"]}
    if run_id not in runs:
        raise store.TaskError(
            "unknown_run",
            f"{run_id} is not a run of task {task['id']} (its runs: "
            f"{', '.join(runs) or 'none'})",
        )
    path = primary / ".concorde/runs" / run_id / "result.json"
    try:
        result = json.loads(path.read_text())
    except (OSError, ValueError) as error:
        raise store.TaskError(
            "unknown_run", f"the result of {run_id} cannot be read at {path}: {error}"
        ) from error
    if result.get("error") is None:
        raise store.TaskError(
            "nothing_to_escalate",
            f"{run_id} ended {result.get('status')} without an error",
        )
    return _checked(result["error"], f"the error of {run_id}")


def _file_error(path: str) -> dict:
    try:
        value = json.loads(Path(path).read_text())
    except (OSError, ValueError) as error:
        raise store.TaskError(
            "invalid_error", f"--error-file {path} cannot be read as JSON: {error}"
        ) from error
    if isinstance(value, dict) and isinstance(value.get("error"), dict):
        value = value["error"]
    return _checked(value, f"--error-file {path}")


def escalate(here: Path, arguments) -> dict:
    primary = store.primary_of(here)
    task = store.load_task(primary, arguments.task_id)
    causes = [_run_error(primary, task, run) for run in arguments.run]
    causes += [_file_error(path) for path in arguments.error_file]
    if not causes:
        raise store.TaskError(
            "nothing_to_escalate",
            "name the errors being escalated with --run or --error-file",
        )
    try:
        link = errors.link(
            "main-agent",
            f"main agent (task {task['id']})",
            arguments.code,
            arguments.detail,
            reason=arguments.reason,
            explanation=arguments.explanation,
            attempts=arguments.attempt,
            options=arguments.option,
            recommendation=arguments.recommendation,
            causes=causes,
        )
    except ValueError as error:
        raise store.TaskError("invalid_error", str(error)) from error
    _checked(link, "the escalation")
    store.escalate(primary, task["id"], link)
    return {
        "escalated": link,
        "decision_log": store.decision_log_path(primary, task["id"]).as_posix(),
        "rendered": errors.render(link),
    }


def main(argv, cwd: Path | None = None) -> int:
    words = list(argv)
    command = words[0] if words else "?"
    here = Path(cwd or Path.cwd())
    try:
        arguments = parser().parse_args(words)
    except store.TaskError as error:
        sys.stdout.write(
            json.dumps({"error": refusal(command, error)}, indent=2) + "\n"
        )
        return 2
    except SystemExit as exit_:
        return 0 if exit_.code in (0, None) else 2
    try:
        if arguments.command == "open":
            value = store.open_task(
                here,
                arguments.task_id,
                arguments.goal,
                [item.strip() for item in arguments.modules.split(",") if item.strip()],
                base=arguments.base,
                path=Path(arguments.path) if arguments.path else None,
            )
        elif arguments.command == "list":
            value = store.list_tasks(store.primary_of(here), arguments.state)
        elif arguments.command == "show":
            value = store.show_task(store.primary_of(here), arguments.task_id)
        elif arguments.command == "escalate":
            value = escalate(here, arguments)
        else:
            if arguments.force and not arguments.abandoned:
                raise store.TaskError(
                    "invalid_input", "--force applies only to --abandoned"
                )
            value = store.close_task(
                here,
                arguments.task_id,
                merged=arguments.merged,
                abandoned=arguments.abandoned,
                force=arguments.force,
            )
    except store.TaskError as error:
        sys.stdout.write(
            json.dumps({"error": refusal(command, error)}, indent=2) + "\n"
        )
        return 1
    except Exception as error:  # noqa: BLE001 -- every failure leaves a detailed error
        link = errors.from_exception(
            f"Tasks (concorde task {command})",
            error,
            explanation="Tasks has no recovery for an unexpected error; nothing after it ran",
        )
        sys.stdout.write(json.dumps({"error": link}, indent=2) + "\n")
        return 1
    sys.stdout.write(json.dumps(value, indent=2) + "\n")
    return 0
