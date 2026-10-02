"""The coordination part's tools of the project MCP server: the task tools, ``task_merge``,
``locks``, ``register_wait``, ``trace_show`` and ``run_result``.

The project MCP server, Distribution's host, presents the tools the coordination part's
registration names and runs each call in a fresh process of the primary worktree's current
Concorde, which calls the tool's entry here with the call as one JSON object: its ``arguments``
and the session's provenance (``primary``, ``where``, ``session``, ``channel`` and, for a merge the
server started, ``merge``). Each entry answers ``{"value": …}`` or ``{"error": <link>}``, a refusal
being Tasks' own link for a task command and the tool's own (actor ``Concorde project MCP server
(<tool>)``) for arguments it cannot take. ``register_wait`` adds ``watch`` when the server is to run
the wait and wake its session; ``task_merge`` adds ``handover``, the merge command the call's
process becomes holding the locks it took, and ``work``, what the server watches of it.

Every call reads the stores afresh from the primary worktree and never waits for a lock: a tool
that needs one is refused at once, naming its holder, when another process holds it.
"""

from __future__ import annotations

import json
import os
import shlex
from argparse import Namespace
from pathlib import Path

from ...kernel import errors
from ...kernel.refusal import KernelError
from ...kernel.schema import validate
from ...kernel.tracing import layout, locks, reader
from . import cli as task_cli
from . import merge, store, wait
from .parts import _environment, concorde_command
from .store import TaskError

ACTOR = "Concorde project MCP server"


class Refusal(Exception):
    """A tool call refused with an error link."""

    def __init__(self, link: dict):
        super().__init__(link["detail"])
        self.link = link


def own(
    tool: str, code: str, detail: str, *, reason="input", explanation="", options=()
):
    return Refusal(
        errors.link(
            "component",
            f"{ACTOR} ({tool})",
            code,
            detail,
            reason=reason,
            explanation=explanation
            or "the call's arguments are not ones the tool can pass on to Tasks",
            options=list(options),
        )
    )


TEXT = {"type": "string", "minLength": 1}
TEXTS = {"type": "array", "items": TEXT}
TASK = {"type": "string", "pattern": "^[a-z0-9][a-z0-9-]{0,47}$"}
ISSUE = {"type": "string", "minLength": 1}


def schema(properties: dict, required=()) -> dict:
    return {
        "type": "object",
        "properties": properties,
        "required": list(required),
        "additionalProperties": False,
    }


TOOLS: dict[str, dict] = {
    "task_list": {
        "description": "Every current and closed task with its derived state, oldest first; "
        "`state` keeps those in one of the states it lists and `main` those whose record names "
        "that main agent's session, both when both are given. As `concorde task list`.",
        "inputSchema": schema(
            {
                "state": {
                    "type": "array",
                    "items": {"enum": list(store.STATES)},
                    "minItems": 1,
                },
                "main": TEXT,
            }
        ),
    },
    "task_show": {
        "description": "One task: its record with the derived state, the main agent's sessions "
        "and the task sessions' reports with their answers (null while unanswered), its "
        "workspace's runs, its delivery commits, task sessions, escalations, the holder of its "
        "workspace lock and the paths of its decision log and folder. As `concorde task show`.",
        "inputSchema": schema({"task": TASK}, ["task"]),
    },
    "trace_show": {
        "description": "A trace node with its subtree, each node's status, times and usage "
        "rolled up; `node` is a task, a history key, a run or worker run identity or a node's "
        "folder, and `depth` limits how many levels below it are shown. As "
        "`concorde trace show`.",
        "inputSchema": schema(
            {"node": TEXT, "depth": {"type": "integer", "minimum": 0}}, ["node"]
        ),
    },
    "run_result": {
        "description": "The saved run result of a run of any task's workspace or of an "
        "unbound run, or, while it runs, its run progress file.",
        "inputSchema": schema({"run": TEXT}, ["run"]),
    },
    "locks": {
        "description": "Who holds the merge lock and each current task's workspace lock now: "
        "each holder line (holder, process, since, session, task), or null when free.",
        "inputSchema": schema({}),
    },
    "task_open": {
        "description": "Open a task from the primary worktree, as `concorde task open`; refused "
        "at once with merge_busy, naming the holder, while another process holds the merge lock.",
        "inputSchema": schema(
            {
                "task": TASK,
                "goal": TEXT,
                "modules": {"type": "array", "items": TEXT, "minItems": 1},
                "base": TEXT,
            },
            ["task", "goal", "modules"],
        ),
    },
    "task_escalate": {
        "description": "Record an escalation, as `concorde task escalate`: the escalating "
        "session's link of the error chain, whose causes are the errors of the named runs, "
        "error files and earlier escalations; naming none records the link alone.",
        "inputSchema": schema(
            {
                "task": TASK,
                "by": {"enum": ["main-agent", "task-session"]},
                "code": {"type": "string", "pattern": "^[a-z][a-z0-9_]*$"},
                "detail": TEXT,
                "reason": {"enum": list(errors.REASONS)},
                "explanation": TEXT,
                "runs": TEXTS,
                "error_files": TEXTS,
                "escalations": {
                    "type": "array",
                    "items": {"type": "integer", "minimum": 1},
                },
                "attempts": TEXTS,
                "options": TEXTS,
                "recommendation": {"type": "string"},
            },
            ["task", "code", "detail", "reason", "explanation"],
        ),
    },
    "task_rebind": {
        "description": "Name the main agent's session the task's task sessions report to from "
        "now on, after its session name changed, as `concorde task rebind`; the task record "
        "keeps every earlier name.",
        "inputSchema": schema({"task": TASK, "main": TEXT}, ["task", "main"]),
    },
    "task_report": {
        "description": "Record a task session's report to the main agent, before messaging it, "
        "as `concorde task report`: the text and the escalations it carries go into the task "
        "record and decision log, and the answer names the main agent's session the task record "
        "names now, the one to message.",
        "inputSchema": schema(
            {
                "task": TASK,
                "text": TEXT,
                "escalations": {
                    "type": "array",
                    "items": {"type": "integer", "minimum": 1},
                },
            },
            ["task", "text"],
        ),
    },
    "task_answer": {
        "description": "Record the main agent's answer to reports of a task, as "
        "`concorde task answer`; a report without an answer is unanswered.",
        "inputSchema": schema(
            {
                "task": TASK,
                "reports": {
                    "type": "array",
                    "items": {"type": "integer", "minimum": 1},
                    "minItems": 1,
                },
                "text": TEXT,
            },
            ["task", "reports", "text"],
        ),
    },
    "task_close": {
        "description": "Close a task without merging, as `concorde task close --completed` or "
        "`--failed`: `outcome` completed takes a `note`, failed takes a `reason` and either "
        "`runs`/`error_files` or `no_error`. Refused at once, naming the holder, while a run of "
        "the task or another process holds a lock the close needs.",
        "inputSchema": schema(
            {
                "task": TASK,
                "outcome": {"enum": ["completed", "failed"]},
                "note": TEXT,
                "reason": TEXT,
                "runs": TEXTS,
                "error_files": TEXTS,
                "no_error": {"type": "boolean"},
                "force": {"type": "boolean"},
            },
            ["task", "outcome"],
        ),
    },
    "task_resolve": {
        "description": "Add open Issues of the project to those the task fixes, as `concorde task "
        "resolve`; once the task is merged and its checks passed, the merge closes each still "
        "open as resolved with the merge commit as evidence.",
        "inputSchema": schema(
            {"task": TASK, "issues": {"type": "array", "items": ISSUE, "minItems": 1}},
            ["task", "issues"],
        ),
    },
    "task_merge": {
        "description": "Merge a delivered task, or finish an interrupted merge with `resume` or "
        "`abort`, without waiting: takes the task's workspace lock and the merge lock at once or "
        "is refused naming who holds the busy one; when granted, starts `concorde task merge` as "
        "a process of its own that holds the locks until it ends, and returns at once. Its "
        "output is kept in the merge attempt's node of the task's trace. With a channel the "
        "session is woken with that output when it ends; without one, run the returned "
        "`concorde task wait <task> --merge` in background Bash.",
        "inputSchema": schema(
            {
                "task": TASK,
                "checks": TEXTS,
                "resume": {"type": "boolean"},
                "abort": {"type": "boolean"},
            },
            ["task"],
        ),
    },
    "register_wait": {
        "description": "Ask to be woken, through this server's Claude Code channel, when a task "
        "reaches one of the states `until` (delivered, merging, closed, failed), when a task's "
        "record names a main agent's session other than `rebound` (with `task`), when a run ends "
        "(`run`), or when a lock is released (`lock` merge, or workspace with `task`). Answers at "
        "once when it already happened. Only notifies: it never takes a lock for you. Without a "
        "channel it says so and returns the blocking `concorde task wait` command to run in "
        "background Bash instead.",
        "inputSchema": schema(
            {
                "task": TASK,
                "until": {
                    "type": "array",
                    "items": {"enum": list(wait.AWAITABLE)},
                    "minItems": 1,
                },
                "run": TEXT,
                "lock": {"enum": list(wait.LOCKS)},
                "rebound": TEXT,
            }
        ),
    },
}

# The Tasks command whose refusals each tool passes on.
COMMANDS = {
    "task_list": "list",
    "task_show": "show",
    "task_open": "open",
    "task_escalate": "escalate",
    "task_close": "close",
    "task_rebind": "rebind",
    "task_report": "report",
    "task_answer": "answer",
    "task_resolve": "resolve",
    "task_merge": "merge",
    "register_wait": "wait",
    "locks": "list",
}


class Call:
    """One call: the primary worktree, the session and whether it has a channel; what the server
    is to do after the answer, run a wait or become the merge, is left in ``watch``,
    ``handover`` and ``work``."""

    def __init__(self, envelope: dict):
        self.primary = Path(envelope["primary"])
        self.where = Path(envelope.get("where") or envelope["primary"])
        self.session = envelope.get("session")
        self.channel = bool(envelope.get("channel"))
        self.merge = envelope.get("long_work")
        self.watch: dict | None = None
        self.handover: dict | None = None
        self.work: dict | None = None


# --- queries --------------------------------------------------------------------------------


def task_list(call: Call, arguments: dict):
    return store.list_tasks(call.primary, arguments.get("state"), arguments.get("main"))


def task_show(call: Call, arguments: dict):
    return store.show_task(call.primary, arguments["task"])


def trace_show(call: Call, arguments: dict):
    try:
        target, concorde = reader.locate(
            arguments["node"], reader.concorde_directories(call.primary)
        )
        return reader.view(target, concorde, depth=arguments.get("depth"))
    except reader.ReadError as error:
        raise own(
            "trace_show",
            error.code,
            str(error),
            explanation="the reader shows only nodes it finds and never guesses another",
            options=["call task_list, or `concorde trace list --history --unbound`"],
        ) from None


def run_result(call: Call, arguments: dict):
    run = arguments["run"]
    try:
        folder, concorde = reader.locate(run, reader.concorde_directories(call.primary))
    except reader.ReadError as error:
        raise own("run_result", "unknown_run", str(error)) from None
    running = locks.held(layout.lock_file(concorde, "run", run))
    result = folder / layout.RESULT
    if not running and result.is_file():
        return {"run": run, "running": False, "result": json.loads(result.read_text())}
    progress = folder / layout.PROGRESS
    return {
        "run": run,
        "running": running,
        "result": None,
        "progress": json.loads(progress.read_text()) if progress.is_file() else None,
    }


def locks_(call: Call, arguments: dict):
    workspaces = {}
    for record in store.list_tasks(call.primary):
        if record["state"] in store.ENDED:
            continue
        path = wait.lock_path(call.primary, "workspace", record["id"])
        workspaces[record["id"]] = locks.entry(path)
    return {
        "merge": locks.entry(store.merge_lock_path(call.primary)),
        "workspaces": workspaces,
    }


# --- short writes ---------------------------------------------------------------------------


def task_open(call: Call, arguments: dict):
    record = store.open_task(
        call.primary,
        arguments["task"],
        arguments["goal"],
        arguments["modules"],
        base=arguments.get("base"),
        wait=0.0,
    )
    return {
        "record": record,
        "decision_log": store.decision_log_path(call.primary, record["id"]).as_posix(),
    }


def task_escalate(call: Call, arguments: dict):
    return task_cli.escalate(
        call.primary,
        Namespace(
            task_id=arguments["task"],
            by=arguments.get("by", "main-agent"),
            code=arguments["code"],
            detail=arguments["detail"],
            reason=arguments["reason"],
            explanation=arguments["explanation"],
            run=arguments.get("runs", []),
            error_file=arguments.get("error_files", []),
            escalation=arguments.get("escalations", []),
            attempt=arguments.get("attempts", []),
            option=arguments.get("options", []),
            recommendation=arguments.get("recommendation", ""),
        ),
    )


def task_rebind(call: Call, arguments: dict):
    return store.rebind(call.primary, arguments["task"], arguments["main"])


def task_report(call: Call, arguments: dict):
    return store.report(
        call.primary,
        arguments["task"],
        arguments["text"],
        arguments.get("escalations", []),
    )


def task_answer(call: Call, arguments: dict):
    return store.answer(
        call.primary, arguments["task"], arguments["reports"], arguments["text"]
    )


def task_close(call: Call, arguments: dict):
    outcome = arguments["outcome"]
    return task_cli.close(
        call.primary,
        Namespace(
            task_id=arguments["task"],
            merged=False,
            completed=outcome == "completed",
            failed=outcome == "failed",
            note=arguments.get("note"),
            reason=arguments.get("reason"),
            run=arguments.get("runs", []),
            error_file=arguments.get("error_files", []),
            no_error=arguments.get("no_error", False),
            force=arguments.get("force", False),
            wait=0.0,
        ),
    )


def task_resolve(call: Call, arguments: dict):
    return store.resolve(call.primary, arguments["task"], arguments["issues"])


# --- long work ------------------------------------------------------------------------------


def _busy(
    tool: str, code: str, task: str, busy: locks.LockBusy, what: str | None = None
) -> Refusal:
    holder = busy.entry or {"holder": busy.holder}
    what = what or (
        "its workspace lock" if code == "workspace_busy" else "the merge lock"
    )
    return Refusal(
        errors.link(
            "component",
            f"{ACTOR} ({tool})",
            code,
            f"{tool} of task {task} needs {what} {busy.path}, which is held by "
            f"{busy.holder}; the server never waits for a lock",
            reason="environment",
            explanation="another process holds the lock, and whether to wait for it is the "
            "caller's choice",
            evidence=[
                errors.evidence("lock", busy.path.as_posix(), json.dumps(holder))
            ],
            options=[
                (
                    "call register_wait with the same lock to be woken when it is "
                    "released, then ask again"
                ),
                "call task_show to see which run of the task holds its workspace lock",
            ],
        )
    )


def task_merge(call: Call, arguments: dict):
    tool = "task_merge"
    task = arguments["task"]
    resume, abort = arguments.get("resume", False), arguments.get("abort", False)
    checks = arguments.get("checks", [])
    if resume and abort:
        raise own(tool, "invalid_input", "resume and abort exclude each other")
    if (resume or abort) and checks:
        raise own(
            tool,
            "invalid_input",
            "resume reruns the checks the interrupted merge recorded and abort runs none, "
            "so neither takes checks",
        )
    merge.parse_checks(list(checks))
    store.load_task(call.primary, task)
    attempt = store.attempt_lock_path(call.primary, task)
    workspace = wait.lock_path(call.primary, "workspace", task)
    merging = store.merge_lock_path(call.primary)
    holder = f"`concorde task merge` of task {task}, started by the project MCP server"
    if call.merge is None:
        raise own(
            tool,
            "invalid_input",
            "a merge starts only through the project MCP server, whose process the merge "
            "becomes",
            reason="environment",
        )
    command = concorde_command(call.primary)
    environment = _environment(command)
    argv = [*command, "task", "merge", task, "--wait", "0"]
    argv += [word for check in checks for word in ("--check", check)]
    argv += ["--resume"] if resume else ["--abort"] if abort else []
    taken = []
    # The task's merge attempt lock first, as the command takes it, so that a merge of the task
    # still running is refused before any other lock is touched.
    wanted = (
        (attempt, "merge_busy", "its merge attempt lock, held by a merge of the task"),
        (workspace, "workspace_busy", None),
        (merging, "merge_busy", None),
    )
    try:
        for path, code, what in wanted:
            try:
                descriptor = locks.acquire(path)
            except locks.LockBusy as busy:
                raise _busy(tool, code, task, busy, what) from None
            taken.append((path, descriptor))
            # This process becomes the merge (the server's hand-over), so its pid is the merge's.
            locks.write_entry(
                descriptor, locks.line(holder, os.getpid(), task, call.session)
            )
        # Holding the task's locks, no other attempt can take the next attempt's folder, where
        # the merge's output is kept with the task, also once it moved to the history.
        folder = merge.next_attempt(call.primary, task)
        folder.mkdir(parents=True)
    except BaseException:
        for _, descriptor in taken:
            os.close(descriptor)
        raise
    environment[locks.INHERITED] = json.dumps(
        {path.as_posix(): descriptor for path, descriptor in taken}
    )
    environment[merge.RESERVED] = folder.as_posix()
    if call.session:
        environment[locks.SESSION] = call.session
    output, messages = folder / merge.OUTPUT, folder / merge.MESSAGES
    shown = "concorde " + shlex.join(argv[len(command) :])
    call.handover = {
        "argv": argv,
        "environment": environment,
        "descriptors": [descriptor for _, descriptor in taken],
        "folder": folder.as_posix(),
        "output": output.as_posix(),
        "messages": messages.as_posix(),
    }
    # What the server watches of the merge: it wakes the session with the output when it ends,
    # finding the attempt's files with `concorde task wait <task> --merge` once the close moved
    # the task, with the attempt's folder, to the history.
    call.work = {
        "command": f"concorde task merge {task}",
        "output": output.as_posix(),
        "messages": messages.as_posix(),
        "event": "merge_ended",
        "meta": {"task": task},
        "locate": ["task", "wait", task, "--merge", "--timeout", "30"],
    }
    fallback = f"concorde task wait {task} --merge"
    return {
        "started": {
            "command": shown,
            "pid": os.getpid(),
            "attempt": folder.as_posix(),
            "output": output.as_posix(),
            "messages": messages.as_posix(),
        },
        "locks": {
            "attempt": taken[0][0].as_posix(),
            "workspace": taken[1][0].as_posix(),
            "merge": taken[2][0].as_posix(),
        },
        "wake": (
            {"channel": True}
            if call.channel
            else {
                "channel": False,
                "command": fallback,
                "explanation": "this session has no channel from the server, so it is not "
                "woken; run the command in background Bash, which returns once the merge "
                "ended and its output is complete, naming the output file to read",
            }
        ),
    }


# --- waits ----------------------------------------------------------------------------------


def register_wait(call: Call, arguments: dict):
    tool = "register_wait"
    task, until = arguments.get("task"), arguments.get("until")
    run, lock = arguments.get("run"), arguments.get("lock")
    former = arguments.get("rebound")
    targets = [
        name
        for name, value in (
            ("until", until),
            ("rebound", former),
            ("run", run),
            ("lock", lock),
        )
        if value
    ]
    if len(targets) != 1:
        raise own(
            tool,
            "invalid_input",
            "name exactly one of `until` (with `task`), `rebound` (with `task`), `run` and "
            "`lock`; got " + (", ".join(targets) or "none"),
        )
    if until and not task:
        raise own(tool, "invalid_input", "`until` names the states of a `task`")
    if former and not task:
        raise own(
            tool,
            "invalid_input",
            "`rebound` names the former main agent's session of a `task`",
        )
    if run and task:
        raise own(tool, "invalid_input", "`run` names the run alone, not a task")
    if lock == "workspace" and not task:
        raise own(tool, "invalid_input", "a workspace lock is the lock of a `task`")
    if lock == "merge" and task:
        raise own(
            tool, "invalid_input", "the merge lock is the project's, not a task's"
        )
    if until:
        description = f"task {task} becoming {' or '.join(until)}"
        words = [task, "--until", ",".join(until)]
        now = wait.reached(call.primary, task, wait.check_until(until))
        if now is not None:
            return {"registered": False, "already": now}
        meta = {"kind": "task", "task": task}
    elif former:
        description = f"task {task} naming a main agent's session other than {former}"
        words = [task, "--rebound", former]
        now = wait.rebound(call.primary, task, former)
        if now is not None:
            return {"registered": False, "already": now}
        meta = {"kind": "rebound", "task": task}
    elif run:
        description = f"the end of run {run}"
        words = ["--run", run]
        now = wait.run_answer(call.primary, run)
        if now is not None:
            return {"registered": False, "already": now}
        meta = {"kind": "run", "run": run}
    else:
        if task:
            store.load_any(call.primary, task)
        description = f"the release of the {lock} lock" + (
            f" of task {task}" if task else ""
        )
        words = [*([task] if task else []), "--lock", lock]
        now = wait.lock_answer(call.primary, lock, task)
        if now["holder"] is None:
            return {"registered": False, "already": {**now, "released": True}}
        # The wait command may start after the holder is gone and then names none; the
        # registration and the event still name the holder it was registered for.
        description += f", held by {json.dumps(now['holder'], ensure_ascii=False)}"
        meta = {"kind": "lock", "lock": lock, **({"task": task} if task else {})}
    command = shlex.join(["concorde", "task", "wait", *words])
    if not call.channel:
        return {
            "registered": False,
            "channel": False,
            "command": command,
            "explanation": "the server cannot wake this session: it was not started "
            "interactively with the server as a Claude Code channel "
            "(`claude --dangerously-load-development-channels server:concorde`), and a "
            "background session, such as a task session, is never woken by channel events; "
            "run the command in background Bash instead: it blocks without polling until "
            f"{description} and prints one JSON value",
        }
    # The server runs the same command as a process it watches and wakes the session with its
    # answer; the wait's identity is the server's.
    call.watch = {
        "words": ["task", "wait", *words],
        "description": description,
        "meta": meta,
    }
    return {"registered": True, "channel": True, "waits_for": description}


CALLS = {
    "task_list": task_list,
    "task_show": task_show,
    "trace_show": trace_show,
    "run_result": run_result,
    "locks": locks_,
    "task_open": task_open,
    "task_escalate": task_escalate,
    "task_rebind": task_rebind,
    "task_report": task_report,
    "task_answer": task_answer,
    "task_close": task_close,
    "task_resolve": task_resolve,
    "task_merge": task_merge,
    "register_wait": register_wait,
}


def answer(envelope: dict) -> dict:
    """The answer of one call of the tool ``envelope["tool"]``: ``{"value"}`` or ``{"error"}``,
    with what the server is to do afterwards."""
    name = str(envelope.get("tool"))
    call = None
    try:
        if name not in CALLS:
            raise own(
                name, "invalid_input", f"the coordination part has no tool {name!r}"
            )
        arguments = envelope.get("arguments")
        arguments = {} if arguments is None else arguments
        if not isinstance(arguments, dict):
            raise own(
                name,
                "invalid_input",
                f"the arguments are not an object: {arguments!r}"[:300],
            )
        try:
            validate(arguments, TOOLS[name]["inputSchema"])
        except KernelError as error:
            raise own(
                name, "invalid_input", f"the arguments of {name} are invalid: {error}"
            ) from None
        call = Call(envelope)
        value = CALLS[name](call, arguments)
    except Refusal as refusal:
        return {"error": refusal.link}
    except TaskError as error:
        return {"error": task_cli.refusal(COMMANDS.get(name, name), error)}
    reply = {"value": value}
    for key in ("watch", "handover", "work"):
        if getattr(call, key) is not None:
            reply[key] = getattr(call, key)
    return reply


__all__ = ["CALLS", "TOOLS", "answer"]
