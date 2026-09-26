"""``concorde task open|list|show|session|close|merge|escalate``: print one JSON value; refusals
exit 1, bad usage 2.

A refusal prints ``{"error": <error link>}``: the Tasks component's account of what it refused,
why it cannot handle it, and what the caller can do. ``session`` starts a task session in a task
worktree on the main session's program, and in pi answers or stops its running round.
``escalate`` records the escalating session's own link of an error chain (the main agent's, or a
task session's to the main agent), with the errors of the named runs, files or earlier escalations
as its causes.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .. import errors
from ..spec.schema import ContractError, validate
from . import merge, pi_session, session, store

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
    "config_copy_failed": (
        "environment",
        "the file system refused the copy, and Tasks does not remove a worktree it just created",
    ),
    "session_failed": (
        "environment",
        "the agent program did not start the task session Tasks asked for, or the machine "
        "lacks a program it needs; Tasks installs nothing",
    ),
    "session_busy": (
        "decision",
        "one round of a task session runs at a time; waiting for its report or stopping it is "
        "the main agent's decision",
    ),
    "missing_worktree": (
        "environment",
        "the task's worktree is gone from disk, and recreating it is not Tasks' decision",
    ),
    "merge_busy": (
        "environment",
        "another concorde task command holds the primary worktree's merge lock, and how long "
        "to keep waiting is the caller's choice",
    ),
    "primary_dirty": (
        "decision",
        "Tasks neither commits nor discards what is in the primary worktree, and merges only "
        "into a clean checked-out branch",
    ),
    "merge_conflict": (
        "decision",
        "resolving a conflict is work for the task, done in its worktree, never a step Tasks "
        "takes in the primary worktree",
    ),
    "check_failed": (
        "decision",
        "the merged primary branch failed a check, and fixing that is new work Tasks cannot do",
    ),
    "rollback_failed": (
        "environment",
        "Git refused to restore the primary branch, so the primary worktree needs inspecting "
        "before anyone merges again",
    ),
}
OPTIONS = {
    "unknown_task": ["run concorde task list to see the tasks"],
    "unknown_module": ["name registered Modules, or register the Module first"],
    "dirty_worktree": [
        "deliver or discard the changes",
        "close with --completed or --failed and --force",
    ],
    "not_merged": [
        "merge the task with concorde task merge, which closes it",
        "deliver the task again if its branch moved past the last delivery",
    ],
    "merge_busy": [
        "run the command again, or merge with a longer --wait; the holder's lock is released "
        "as soon as its process ends",
    ],
    "primary_dirty": [
        "commit, move into a task or remove the listed paths of the primary worktree",
        "check out the primary branch in the primary worktree",
    ],
    "merge_conflict": [
        "merge the primary branch into the task branch in the task worktree, resolve the "
        "conflicts, validate and run delivery again, then run concorde task merge again",
        "close the task with --completed or --failed if its change is no longer wanted",
    ],
    "check_failed": [
        "read the merge log, fix the cause in the task worktree after merging the primary "
        "branch into it, deliver again and merge again",
        "fix the check itself in its own task if the check is what is wrong",
    ],
    "rollback_failed": [
        "inspect git status in the primary worktree and restore the primary branch to the "
        "commit named before merging again",
    ],
    "worktree_not_ignored": [
        "add .claude/worktrees/ to .gitignore",
        "pass --path outside the primary worktree",
    ],
    "session_failed": [
        "in Claude Code, have the developer run claude once in the task worktree and accept "
        "the trust prompt",
        "in pi, install what the message names",
        "work in the task yourself instead of starting a session",
    ],
    "client_unknown": [
        "run the command from the Claude Code or pi main session, or set CONCORDE_CLIENT",
    ],
    "session_busy": [
        "wait until the running round reports",
        "stop it with concorde task session <task> --stop",
    ],
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
    starting = commands.add_parser("session")
    starting.add_argument("task_id")
    starting.add_argument("--main")
    starting.add_argument("--model")
    starting.add_argument("--dry-run", action="store_true")
    starting.add_argument("--answer")
    starting.add_argument("--stop", action="store_true")
    closing = commands.add_parser("close")
    closing.add_argument("task_id")
    mode = closing.add_mutually_exclusive_group(required=True)
    mode.add_argument("--merged", action="store_true")
    mode.add_argument("--completed", action="store_true")
    mode.add_argument("--failed", action="store_true")
    closing.add_argument("--note")
    closing.add_argument("--reason")
    closing.add_argument("--run", action="append", default=[])
    closing.add_argument("--error-file", action="append", default=[])
    closing.add_argument("--no-error", action="store_true")
    closing.add_argument("--force", action="store_true")
    merging = commands.add_parser("merge")
    merging.add_argument("task_id")
    merging.add_argument("--check", action="append", default=[])
    merging.add_argument("--wait", type=float, default=store.MERGE_WAIT)
    escalating = commands.add_parser("escalate")
    escalating.add_argument("task_id")
    escalating.add_argument("--code", required=True)
    escalating.add_argument("--detail", required=True)
    escalating.add_argument("--reason", required=True, choices=list(errors.REASONS))
    escalating.add_argument("--explanation", required=True)
    escalating.add_argument(
        "--by", choices=["main-agent", "task-session"], default="main-agent"
    )
    escalating.add_argument("--run", action="append", default=[])
    escalating.add_argument("--error-file", action="append", default=[])
    escalating.add_argument("--escalation", action="append", type=int, default=[])
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


def _escalated_error(task: dict, number: int) -> dict:
    escalations = task.get("escalations", [])
    if not 1 <= number <= len(escalations):
        raise store.TaskError(
            "unknown_escalation",
            f"--escalation {number} is not an escalation of task {task['id']}, which has "
            f"{len(escalations)} (numbered from 1 in record order)",
        )
    return _checked(
        escalations[number - 1]["error"], f"escalation {number} of task {task['id']}"
    )


def close(here: Path, arguments) -> dict:
    """``task close``: check the options of the chosen outcome, then end the task."""
    outcome = (
        "merged"
        if arguments.merged
        else "completed"
        if arguments.completed
        else "failed"
    )
    sources = bool(arguments.run or arguments.error_file)
    problems = []
    if arguments.reason is not None and outcome != "failed":
        problems.append("--reason belongs to --failed; a completed task takes --note")
    if arguments.note is not None and outcome == "failed":
        problems.append("--failed takes --reason, not --note")
    if (sources or arguments.no_error) and outcome != "failed":
        problems.append("--run, --error-file and --no-error belong to --failed")
    if outcome == "failed" and sources == arguments.no_error:
        problems.append(
            "a failed task names the errors that caused it with --run or --error-file, "
            "or declares with --no-error that no error did"
        )
    if problems:
        raise store.TaskError("invalid_input", "; ".join(problems))
    errors = []
    if outcome == "failed":
        primary = store.primary_of(here)
        task = store.load_task(primary, arguments.task_id)
        errors = [_run_error(primary, task, run) for run in arguments.run]
        errors += [_file_error(path) for path in arguments.error_file]
    return store.close_task(
        here,
        arguments.task_id,
        outcome,
        note=arguments.reason if outcome == "failed" else arguments.note,
        errors=errors,
        force=arguments.force,
    )


def start_session(here: Path, arguments) -> dict:
    """Start, answer or stop a task session on the main session's own program."""
    from ..harness.models import ModelConfigError, detect_client

    try:
        program, _ = detect_client()
    except ModelConfigError as error:
        raise store.TaskError(
            "client_unknown",
            f"a task session runs on the main session's own program, which cannot be read "
            f"from the environment: {error}",
        ) from error
    follow = arguments.answer is not None or arguments.stop
    if arguments.answer is not None and arguments.stop:
        raise store.TaskError("invalid_input", "--answer and --stop exclude each other")
    if follow and (arguments.model or arguments.dry_run or arguments.main):
        raise store.TaskError(
            "invalid_input",
            "--answer and --stop take no --main, --model or --dry-run: they act on the "
            "session already started",
        )
    if program == "claude":
        if follow:
            raise store.TaskError(
                "invalid_input",
                "--answer and --stop are for a pi task session: a Claude Code task session "
                "receives answers through SendMessage and is stopped with claude stop",
            )
        if not arguments.main or not arguments.main.strip():
            raise store.TaskError(
                "invalid_input",
                "--main must name the main agent's session, which the task session reports to",
            )
        return session.start(
            here,
            arguments.task_id,
            arguments.main,
            model=arguments.model,
            dry_run=arguments.dry_run,
        )
    if arguments.stop:
        return pi_session.stop(here, arguments.task_id)
    if arguments.answer is not None:
        return pi_session.answer(here, arguments.task_id, arguments.answer)
    return pi_session.start(
        here,
        arguments.task_id,
        arguments.main,
        model=arguments.model,
        dry_run=arguments.dry_run,
    )


def escalate(here: Path, arguments) -> dict:
    primary = store.primary_of(here)
    task = store.load_task(primary, arguments.task_id)
    causes = [_run_error(primary, task, run) for run in arguments.run]
    causes += [_file_error(path) for path in arguments.error_file]
    causes += [_escalated_error(task, number) for number in arguments.escalation]
    if not causes:
        raise store.TaskError(
            "nothing_to_escalate",
            "name the errors being escalated with --run, --error-file or --escalation",
        )
    actor = "main agent" if arguments.by == "main-agent" else "task session"
    try:
        link = errors.link(
            arguments.by,
            f"{actor} (task {task['id']})",
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
    record = store.escalate(primary, task["id"], link)
    return {
        "escalated": link,
        "number": len(record["escalations"]),
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
        elif arguments.command == "session":
            value = start_session(here, arguments)
        elif arguments.command == "escalate":
            value = escalate(here, arguments)
        elif arguments.command == "merge":
            value = merge.merge_task(
                here, arguments.task_id, arguments.check, arguments.wait
            )
        else:
            value = close(here, arguments)
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
