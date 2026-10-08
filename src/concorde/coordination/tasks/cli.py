"""``concorde task open|list|show|session|resolve|rebind|close|merge|deliver|escalate|report|answer|wait``:
print one JSON value; refusals exit 1, bad usage 2.

While a merge is unfinished, every one of them that changes something is refused with
``merge_incomplete`` apart from ``merge --resume`` and ``merge --abort`` of that task; ``list`` and ``show`` still answer.

A refusal prints ``{"error": <error link>}``: the Tasks component's account of what it refused,
why it cannot handle it, and what the caller can do. ``session`` starts a Claude Code task
session in a task worktree.
``wait`` blocks until a task reaches a state, a run ends or a lock is released, without polling.
``escalate`` records the escalating session's own link of an error chain (the main agent's, or a
task session's to the main agent), with the errors of the named runs, files or earlier escalations
as its causes; naming none records that link alone as the whole chain, as for a decision an ok run
took that the session may not keep alone.
``report`` records a task session's report in the task record and decision log before the
session messages the main agent, and prints the main agent's session the task record names now;
``answer`` records the main agent's answer to reports, and ``rebind`` names a new main agent's
session for a task, after the main agent's session name changed. ``deliver`` delivers a task from
its worktree where the method part is not installed.
"""

from __future__ import annotations

import argparse
import json
import sys
from contextlib import ExitStack
from pathlib import Path

from ...kernel import errors
from ...kernel.tracing import reader
from ...kernel.refusal import KernelError
from ...kernel.schema import validate
from . import deliver, merge, parts, runs, session, store, wait

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
    "record_unwritable": (
        "environment",
        "the file system refused to write the task record",
    ),
    "decision_log_failed": (
        "environment",
        "the file system refused the decision log after the task record was written, and "
        "Tasks does not undo a written record",
    ),
    "decision_log_uncommitted": (
        "environment",
        "Git refused the commit of the decision log after the task record was written, and "
        "Tasks does not undo a written record",
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
    "delivery_unverified": (
        "decision",
        "Tasks merges only a delivery commit Delivery could have created, with exactly one "
        "parent, and repairing the task branch is work for the task",
    ),
    "binding_failed": (
        "environment",
        "the file system refused the workspace binding, and Tasks does not remove a worktree it "
        "just created",
    ),
    "session_failed": (
        "environment",
        "Claude Code did not start the task session Tasks asked for, or the machine lacks a "
        "program it needs; Tasks installs nothing",
    ),
    "session_running": (
        "decision",
        "a task session of the task still works in its worktree, and whether to stop it or "
        "message it is the main agent's decision",
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
    "changed_outside": (
        "decision",
        "a worktree no task is working in holds changes nobody accounts for, and Tasks neither "
        "commits nor discards what it did not write",
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
    "workspace_busy": (
        "environment",
        "a run of the task's workspace holds its workspace lock, and waiting for that run or "
        "stopping it is the caller's choice",
    ),
    "merge_incomplete": (
        "decision",
        "a merge into the primary branch ended before its checks decided whether it stays, "
        "and whether to check it again or undo it is the main agent's decision",
    ),
    "not_resumable": (
        "decision",
        "the primary branch's head is no longer the merge that could be checked again, and "
        "Tasks does not merge again on its own",
    ),
    "merge_diverged": (
        "decision",
        "the primary branch moved in a way the interrupted merge did not, and Tasks never "
        "resets commits it did not make",
    ),
    "wait_timeout": (
        "environment",
        "what the wait waits for did not happen within its timeout, and how long to keep "
        "waiting is the caller's choice",
    ),
    "wait_failed": (
        "environment",
        "the kernel refused to watch the lock the wait depends on",
    ),
    "part_missing": (
        "input",
        "the command, or an option of it, needs a part the project has not installed",
    ),
    "part_unknown": (
        "environment",
        "the worktree's own concorde could not be asked whether a part the command needs is "
        "installed",
    ),
    "issues_unavailable": (
        "environment",
        "the issues command, through which Tasks reads the project's Issues, did not answer",
    ),
    "delivery_by_method": (
        "input",
        "the method part is installed, and its delivery validates the workspace before it "
        "commits, which task deliver does not",
    ),
}
OPTIONS = {
    "unknown_task": ["run concorde task list to see the tasks"],
    "unknown_module": ["name registered Modules, or register the Module first"],
    "invalid_issue": [
        "run concorde issues list and name open Issues; reopen a closed one first"
    ],
    "dirty_worktree": [
        "deliver or discard the changes",
        "close with --completed or --failed and --force",
    ],
    "not_merged": [
        "merge the task with concorde task merge, which closes it",
        "deliver the task again if its branch moved past the last delivery",
    ],
    "delivery_unverified": [
        "inspect the task branch's head in the task worktree",
        "revert or remove the commit that does not verify, then run delivery again",
    ],
    "merge_busy": [
        "run the command again, or merge with a longer --wait; the holder's lock is released "
        "as soon as its process ends",
    ],
    "primary_dirty": [
        "commit, move into a task or remove the listed paths of the primary worktree",
        "check out the primary branch in the primary worktree",
    ],
    "changed_outside": [
        "find out what wrote the listed paths, then revert them",
        "have the session of the task they belong to commit and deliver them",
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
        "inspect git status in the primary worktree, then run concorde task merge <task> "
        "--abort to restore the primary branch to the commit named",
    ],
    "workspace_busy": [
        "run the command again with a longer --wait, which waits for the run named inside "
        "the command instead of polling (concorde task show <task> shows the run)",
        "stop that run if it must not finish",
    ],
    "merge_incomplete": [
        "run concorde task merge <task> --resume to rerun its checks on the merge commit and "
        "close the task, or undo the merge when a check fails",
        "run concorde task merge <task> --abort to reset the primary branch to the commit "
        "before the merge and return the task to delivered",
    ],
    "not_resumable": [
        "run concorde task merge <task> --abort, which returns the task to delivered, then "
        "merge it again",
    ],
    "wait_timeout": [
        "run the same wait again, or with a longer --timeout",
        "concorde task show <task> names the run holding the task's workspace lock",
    ],
    "wait_unreachable": [
        "wait for a state the task can still reach, or read how it ended with concorde task "
        "show <task>",
    ],
    "merge_diverged": [
        "inspect the primary branch, restore it by hand to the commit before the merge or to "
        "the merge commit named, and run --abort or --resume again",
    ],
    "worktree_not_ignored": [
        "add .claude/worktrees/ to .gitignore",
    ],
    "session_running": [
        "message the working task session the refusal names",
        "stop it with claude stop <id>, then start the task session again",
    ],
    "session_failed": [
        "have the developer run claude once in the task worktree and accept the trust prompt",
        "work in the task yourself instead of starting a session",
    ],
    "decision_log_failed": [
        "make the decision log writable, then run the same close again, which appends the "
        "closing and changes nothing else",
        "for an escalation, a report or an answer, append the entry the message carries to "
        "the decision log by hand; recording it again would record it twice",
    ],
    "already_answered": [
        "read the answer with concorde task show <task>; answer only the reports whose "
        "answer is null",
    ],
    "part_missing": [
        "install the missing part, or do without the option that needs it",
    ],
    "delivery_by_method": [
        "run concorde task-validation, then concorde delivery, in the task worktree",
    ],
    "not_task_worktree": [
        "run the command in the task's worktree, which concorde task show <task> names",
    ],
    "decision_log_uncommitted": [
        "fix what Git refused in the primary worktree, such as a detached HEAD, an unfinished "
        "merge or a commit hook, then run the same close again, which commits the log and "
        "finishes the close",
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
    opening.add_argument("--resolves", default="")
    listing = commands.add_parser("list")
    listing.add_argument("--state")
    listing.add_argument("--main")
    showing = commands.add_parser("show")
    showing.add_argument("task_id")
    starting = commands.add_parser("session")
    starting.add_argument("task_id")
    starting.add_argument("--main")
    starting.add_argument("--model")
    starting.add_argument("--dry-run", action="store_true")
    resolving = commands.add_parser("resolve")
    resolving.add_argument("task_id")
    resolving.add_argument("issues", nargs="+")
    rebinding = commands.add_parser("rebind")
    rebinding.add_argument("task_id")
    rebinding.add_argument("--main", required=True)
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
    closing.add_argument("--wait", type=float, default=store.MERGE_WAIT)
    merging = commands.add_parser("merge")
    merging.add_argument("task_id")
    merging.add_argument("--check", action="append", default=[])
    merging.add_argument("--wait", type=float, default=store.MERGE_WAIT)
    finishing = merging.add_mutually_exclusive_group()
    finishing.add_argument("--resume", action="store_true")
    finishing.add_argument("--abort", action="store_true")
    delivering = commands.add_parser("deliver")
    delivering.add_argument("task_id")
    delivering.add_argument("--check", action="append", default=[])
    delivering.add_argument("--wait", type=float, default=store.MERGE_WAIT)
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
    reporting = commands.add_parser("report")
    reporting.add_argument("task_id")
    reporting.add_argument("--text", required=True)
    reporting.add_argument("--escalation", action="append", type=int, default=[])
    answering = commands.add_parser("answer")
    answering.add_argument("task_id")
    answering.add_argument("--report", action="append", type=int, required=True)
    answering.add_argument("--text", required=True)
    waiting = commands.add_parser("wait")
    waiting.add_argument("task_id", nargs="?")
    target = waiting.add_mutually_exclusive_group(required=True)
    target.add_argument("--until")
    target.add_argument("--run")
    target.add_argument("--lock", choices=list(wait.LOCKS))
    target.add_argument("--rebound")
    target.add_argument("--merge", action="store_true")
    waiting.add_argument("--timeout", type=float)
    return root


def _checked(value, source: str) -> dict:
    try:
        validate(value, errors.ERROR_SCHEMA)
    except KernelError as error:
        raise store.TaskError(
            "invalid_error",
            f"{source} is not an error link: {error.field or '/'}: {error}",
        ) from error
    return value


def _run_error(primary: Path, task: dict, run_id: str) -> dict:
    concorde = store.concorde(primary)
    workspace = store.workspace_folder(store.task_folder(primary, task["id"]))
    result = runs.load_result(concorde, workspace, run_id)
    if result is None:
        # A run of another workspace or an unbound one: say whose it is when it can be found.
        try:
            folder, _ = reader.locate(run_id, [store.concorde(primary)])
            result = json.loads((folder / "result.json").read_text())
        except (reader.ReadError, OSError, ValueError):
            raise store.TaskError(
                "unknown_run",
                f"{run_id} has no readable result in the workspace folder of task "
                f"{task['id']} ({runs.result_path(concorde, workspace, run_id)})",
            ) from None
    if result.get("workspace") != task["id"]:
        raise store.TaskError(
            "unknown_run",
            f"{run_id} is a run of {result.get('workspace') or 'no workspace'}, not of the "
            f"workspace of task {task['id']}",
        )
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


def _escalated_error(primary: Path, task: dict, number: int) -> dict:
    escalations = store.escalations(primary, task["id"])
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
        task = store.refuse_closed(primary, arguments.task_id)
        errors = [_run_error(primary, task, run) for run in arguments.run]
        errors += [_file_error(path) for path in arguments.error_file]
    return store.close_task(
        here,
        arguments.task_id,
        outcome,
        note=arguments.reason if outcome == "failed" else arguments.note,
        errors=errors,
        force=arguments.force,
        wait=arguments.wait,
    )


def start_session(here: Path, arguments) -> dict:
    """Start a Claude Code task session in a task worktree."""
    store.guard_merges(store.require_primary(here), arguments.task_id)
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


def escalate(here: Path, arguments) -> dict:
    primary = store.primary_of(here)
    task = store.load_task(primary, arguments.task_id)
    store.guard_merges(primary, task["id"])
    causes = [_run_error(primary, task, run) for run in arguments.run]
    causes += [_file_error(path) for path in arguments.error_file]
    causes += [
        _escalated_error(primary, task, number) for number in arguments.escalation
    ]
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
    number = store.escalate(primary, task["id"], link)
    return {
        "escalated": link,
        "number": number,
        "decision_log": store.decision_log_path(primary, task["id"]).as_posix(),
        "rendered": errors.render(link),
    }


def require_execution(here: Path) -> None:
    """Refuse with ``part_missing`` where the execution part, whose runs a wait for a run waits
    for, is not installed: the worktree's own ``concorde`` does not offer ``run``."""
    worktree = store.worktree_of(here)
    try:
        offered = parts.offers(worktree, "run")
    except parts.Failed as failure:
        raise store.TaskError(
            "part_unknown", f"a wait for a run needs the execution part, and {failure}"
        ) from None
    if not offered:
        raise store.TaskError(
            "part_missing",
            f"a wait for a run needs the execution part, which is not installed in {worktree} "
            "(`concorde run` is not offered), so no run exists to wait for",
        )


def wait_for(here: Path, arguments) -> dict:
    """``task wait``: one of a task state, a run's end or a lock's release."""
    if arguments.run is not None:
        if arguments.task_id is not None:
            raise store.TaskError(
                "invalid_input", "--run names the run alone, not a task"
            )
        require_execution(here)
        return wait.wait_run(here, arguments.run, arguments.timeout)
    primary = store.primary_of(here)
    if arguments.merge:
        if arguments.task_id is None:
            raise store.TaskError(
                "invalid_input", "--merge waits for the end of a task's merge"
            )
        return wait.wait_merge(primary, arguments.task_id, arguments.timeout)
    if arguments.rebound is not None:
        if arguments.task_id is None:
            raise store.TaskError(
                "invalid_input",
                "--rebound waits for the main agent's session of a task",
            )
        return wait.wait_rebound(
            primary, arguments.task_id, arguments.rebound, arguments.timeout
        )
    if arguments.lock is not None:
        if arguments.lock == "merge" and arguments.task_id is not None:
            raise store.TaskError(
                "invalid_input",
                "--lock merge names no task: the merge lock is the project's",
            )
        if arguments.task_id is not None:
            store.load_any(primary, arguments.task_id)
        return wait.wait_lock(
            primary, arguments.lock, arguments.task_id, arguments.timeout
        )
    if arguments.task_id is None:
        raise store.TaskError("invalid_input", "--until names the states of a task")
    until = [item.strip() for item in arguments.until.split(",") if item.strip()]
    return wait.wait_task(primary, arguments.task_id, until, arguments.timeout)


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
    # A merge holds its task's merge attempt lock until its answer is written, whatever it is.
    with ExitStack() as held:
        code, value = _answer(here, command, arguments, held)
        sys.stdout.write(json.dumps(value, indent=2) + "\n")
        sys.stdout.flush()
        return code


def _answer(here: Path, command: str, arguments, held: ExitStack) -> tuple[int, dict]:
    """The exit status and the JSON answer of one task command."""
    try:
        if arguments.command == "open":
            record = store.open_task(
                here,
                arguments.task_id,
                arguments.goal,
                [item.strip() for item in arguments.modules.split(",") if item.strip()],
                base=arguments.base,
                resolves=[
                    item.strip()
                    for item in arguments.resolves.split(",")
                    if item.strip()
                ],
            )
            value = {
                "record": record,
                "decision_log": store.decision_log_path(
                    store.primary_of(here), record["id"]
                ).as_posix(),
            }
        elif arguments.command == "list":
            states = (
                None
                if arguments.state is None
                else [
                    item.strip() for item in arguments.state.split(",") if item.strip()
                ]
            )
            value = store.list_tasks(store.primary_of(here), states, arguments.main)
        elif arguments.command == "show":
            value = store.show_task(store.primary_of(here), arguments.task_id)
        elif arguments.command == "session":
            value = start_session(here, arguments)
        elif arguments.command == "resolve":
            value = store.resolve(
                store.primary_of(here), arguments.task_id, arguments.issues
            )
        elif arguments.command == "rebind":
            value = store.rebind(
                store.require_primary(here), arguments.task_id, arguments.main
            )
        elif arguments.command == "escalate":
            value = escalate(here, arguments)
        elif arguments.command == "report":
            value = store.report(
                store.primary_of(here),
                arguments.task_id,
                arguments.text,
                arguments.escalation,
            )
        elif arguments.command == "answer":
            value = store.answer(
                store.require_primary(here),
                arguments.task_id,
                arguments.report,
                arguments.text,
            )
        elif arguments.command == "wait":
            value = wait_for(here, arguments)
        elif arguments.command == "merge":
            value = merge.merge_task(
                here,
                arguments.task_id,
                arguments.check,
                arguments.wait,
                resume=arguments.resume,
                abort=arguments.abort,
                held=held,
            )
        elif arguments.command == "deliver":
            value = deliver.deliver_task(
                here, arguments.task_id, arguments.check, arguments.wait
            )
        else:
            value = close(here, arguments)
    except store.TaskError as error:
        return 1, {"error": refusal(command, error)}
    except Exception as error:  # noqa: BLE001 -- every failure leaves a detailed error
        link = errors.from_exception(
            f"Tasks (concorde task {command})",
            error,
            explanation="Tasks has no recovery for an unexpected error; nothing after it ran",
        )
        return 1, {"error": link}
    return 0, value
