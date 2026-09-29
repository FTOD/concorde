"""The tools of the project MCP server, each a thin call into Tasks, Tracing or Workflows' records.

Every call reads the stores afresh from the primary worktree, so an answer is the state when the
call arrives; the server keeps no copy of any record and adds no rule of its own. A refusal is the
error link of the component that refused, unchanged: Tasks' own for a task command, the server's
own (actor ``Concorde project MCP server (<tool>)``) for arguments it cannot take. Locks are never
waited for: a tool that needs one is refused at once, naming its holder, when another process holds
it.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from argparse import Namespace
from pathlib import Path

from .. import errors
from ..tasks import cli as task_cli
from ..tasks import merge, store, wait
from ..tasks.store import TaskError
from ..tracing import layout, locks, reader

ACTOR = "Concorde project MCP server"
# The entry point of the running Concorde, which the merge it starts runs too.
SCRIPT = Path(__file__).resolve().parents[3] / "scripts/concorde.py"
# How much of a finished merge's output a notification carries; the file holds all of it.
CUT = 6000


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
            or "the call's arguments are not ones the server can pass on to Concorde",
            options=list(options),
        )
    )


def tasks_refusal(tool: str, command: str, error: TaskError) -> Refusal:
    return Refusal(task_cli.refusal(command, error))


TEXT = {"type": "string", "minLength": 1}
TEXTS = {"type": "array", "items": TEXT}
TASK = {"type": "string", "pattern": "^[a-z0-9][a-z0-9-]{0,47}$"}


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
        "`state` filters on it. As `concorde task list`.",
        "inputSchema": schema({"state": {"enum": list(store.STATES)}}),
    },
    "task_show": {
        "description": "One task: its record with the derived state, its workspace's runs, its "
        "delivery commits, task sessions, escalations, the holder of its workspace lock and the "
        "paths of its decision log and folder. As `concorde task show`.",
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
    "workflow_report": {
        "description": "A saved workflow result of a task's workspace: report `number`, or "
        "the latest.",
        "inputSchema": schema(
            {"task": TASK, "number": {"type": "integer", "minimum": 1}}, ["task"]
        ),
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
    "task_merge": {
        "description": "Merge a delivered task, or finish an interrupted merge with `resume` or "
        "`abort`, without waiting: takes the task's workspace lock and the merge lock at once or "
        "is refused naming who holds the busy one; when granted, starts `concorde task merge` as "
        "a process of its own that holds both locks until it ends, and returns at once. With a "
        "channel the session is woken with the merge's output when it ends.",
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
        "reaches one of the states `until` (delivered, merging, closed, failed), when a run ends "
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
            }
        ),
    },
}


def _check(tool: str, arguments: dict) -> dict:
    """The arguments, refused with invalid_input when they do not satisfy the tool's schema."""
    from ..spec.schema import ContractError, validate

    if not isinstance(arguments, dict):
        raise own(
            tool,
            "invalid_input",
            f"the arguments are not an object: {arguments!r}"[:300],
        )
    try:
        validate(arguments, TOOLS[tool]["inputSchema"])
    except ContractError as error:
        raise own(
            tool, "invalid_input", f"the arguments of {tool} are invalid: {error}"
        ) from None
    return arguments


class Project:
    """What every tool needs: the primary worktree, the session and whether it has a channel."""

    def __init__(self, primary: Path, session: str | None, channel: bool, notify):
        self.primary = primary
        self.session = session
        self.channel = channel
        self.notify = notify
        self.waits = 0
        self._runtime: Path | None = None

    def runtime(self) -> Path:
        """A private temporary directory for the output of work this server started."""
        if self._runtime is None:
            self._runtime = Path(tempfile.mkdtemp(prefix="concorde-project-mcp-"))
        return self._runtime

    # --- queries ----------------------------------------------------------------------------

    def task_list(self, arguments: dict):
        return store.list_tasks(self.primary, arguments.get("state"))

    def task_show(self, arguments: dict):
        return store.show_task(self.primary, arguments["task"])

    def trace_show(self, arguments: dict):
        tool = "trace_show"
        try:
            target, concorde = reader.locate(
                arguments["node"], reader.roots(self.primary)
            )
            return reader.view(target, concorde, depth=arguments.get("depth"))
        except reader.ReadError as error:
            raise own(
                tool,
                error.code,
                str(error),
                explanation="the reader shows only nodes it finds and never guesses another",
                options=[
                    "call task_list, or `concorde trace list --history --unbound`"
                ],
            ) from None

    def run_result(self, arguments: dict):
        run = arguments["run"]
        try:
            folder, concorde = reader.locate(run, reader.roots(self.primary))
        except reader.ReadError as error:
            raise own("run_result", "unknown_run", str(error)) from None
        running = locks.held(layout.lock_file(concorde, "run", run))
        result = folder / layout.RESULT
        if not running and result.is_file():
            return {
                "run": run,
                "running": False,
                "result": json.loads(result.read_text()),
            }
        progress = folder / layout.PROGRESS
        return {
            "run": run,
            "running": running,
            "result": None,
            "progress": json.loads(progress.read_text())
            if progress.is_file()
            else None,
        }

    def workflow_report(self, arguments: dict):
        task = arguments["task"]
        _, folder = store.load_any(self.primary, task)
        reports = layout.workflow_folder(layout.workspace_folder(folder)) / "reports"
        numbers = sorted(
            int(path.stem) for path in reports.glob("*.json") if path.stem.isdigit()
        )
        if not numbers:
            raise own(
                "workflow_report",
                "no_report",
                f"the workspace of task {task} has no workflow result in {reports}",
                explanation="a workflow result exists only once `concorde workflow report` "
                "saved one",
            )
        number = arguments.get("number") or numbers[-1]
        path = reports / f"{number}.json"
        if not path.is_file():
            raise own(
                "workflow_report",
                "no_report",
                f"the workspace of task {task} has no workflow result {number}; it has "
                f"{', '.join(map(str, numbers))}",
            )
        return {
            "task": task,
            "number": number,
            "path": path.as_posix(),
            "report": json.loads(path.read_text()),
        }

    def locks(self, arguments: dict):
        workspaces = {}
        for record in store.list_tasks(self.primary):
            if record["state"] in store.ENDED:
                continue
            path = wait.lock_path(self.primary, "workspace", record["id"])
            workspaces[record["id"]] = locks.entry(path)
        return {
            "merge": locks.entry(store.merge_lock_path(self.primary)),
            "workspaces": workspaces,
        }

    # --- short writes -----------------------------------------------------------------------

    def task_open(self, arguments: dict):
        record = store.open_task(
            self.primary,
            arguments["task"],
            arguments["goal"],
            arguments["modules"],
            base=arguments.get("base"),
            wait=0.0,
        )
        return {
            "record": record,
            "decision_log": store.decision_log_path(
                self.primary, record["id"]
            ).as_posix(),
        }

    def task_escalate(self, arguments: dict):
        return task_cli.escalate(
            self.primary,
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

    def task_close(self, arguments: dict):
        outcome = arguments["outcome"]
        return task_cli.close(
            self.primary,
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

    # --- long work --------------------------------------------------------------------------

    def _busy(self, tool: str, code: str, task: str, busy: locks.LockBusy) -> Refusal:
        holder = busy.entry or {"holder": busy.holder}
        what = "its workspace lock" if code == "workspace_busy" else "the merge lock"
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

    def task_merge(self, arguments: dict):
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
        store.load_task(self.primary, task)
        workspace = wait.lock_path(self.primary, "workspace", task)
        merging = store.merge_lock_path(self.primary)
        holder = (
            f"`concorde task merge` of task {task}, started by the project MCP server"
        )
        taken = []
        try:
            for path, code in ((workspace, "workspace_busy"), (merging, "merge_busy")):
                try:
                    descriptor = locks.acquire(path)
                except locks.LockBusy as busy:
                    raise self._busy(tool, code, task, busy) from None
                taken.append((path, descriptor))
                locks.write_entry(
                    descriptor, locks.line(holder, os.getpid(), task, self.session)
                )
            return self._start_merge(task, checks, resume, abort, taken)
        finally:
            for _, descriptor in taken:
                # The merge process has its own copy of each descriptor; closing the server's
                # leaves the lock to it. Before a start, closing releases the lock.
                os.close(descriptor)

    def _start_merge(self, task, checks, resume, abort, taken):
        argv = [sys.executable, SCRIPT.as_posix(), "task", "merge", task, "--wait", "0"]
        argv += [word for check in checks for word in ("--check", check)]
        argv += ["--resume"] if resume else ["--abort"] if abort else []
        runtime = self.runtime()
        number = len(list(runtime.glob("*.json"))) + 1
        output = runtime / f"{number}-merge-{task}.json"
        messages = runtime / f"{number}-merge-{task}.log"
        environment = dict(os.environ)
        environment[locks.INHERITED] = json.dumps(
            {path.as_posix(): descriptor for path, descriptor in taken}
        )
        if self.session:
            environment[locks.SESSION] = self.session
        try:
            with output.open("wb") as out, messages.open("wb") as err:
                process = subprocess.Popen(
                    argv,
                    cwd=self.primary,
                    env=environment,
                    stdin=subprocess.DEVNULL,
                    stdout=out,
                    stderr=err,
                    pass_fds=[descriptor for _, descriptor in taken],
                    start_new_session=True,
                )
        except OSError as error:
            raise own(
                "task_merge",
                "start_failed",
                f"`concorde task merge {task}` could not be started: {error}; both locks were "
                "released",
                reason="environment",
                explanation="the operating system refused to start the process",
            ) from error
        self.watch_process(process, task, output, messages)
        fallback = f"concorde task wait {task} --lock workspace"
        return {
            "started": {
                "command": "concorde " + " ".join(argv[2:]),
                "pid": process.pid,
                "output": output.as_posix(),
                "messages": messages.as_posix(),
            },
            "locks": {
                "workspace": taken[0][0].as_posix(),
                "merge": taken[1][0].as_posix(),
            },
            "wake": (
                {"channel": True}
                if self.channel
                else {
                    "channel": False,
                    "command": fallback,
                    "explanation": "this session has no channel from the server, so it is not "
                    "woken; run the command in background Bash, which returns when the merge "
                    "released the task's workspace lock, then read the output file",
                }
            ),
        }

    def watch_process(self, process, task, output: Path, messages: Path) -> None:
        import threading

        def reap():
            code = process.wait()
            if not self.channel:
                return
            try:
                text = output.read_text(encoding="utf-8", errors="replace").strip()
            except OSError:
                text = ""
            try:
                value = json.loads(text)
            except ValueError:
                value = None
            status = (
                "refused"
                if isinstance(value, dict) and "error" in value
                else ("ok" if code == 0 else "failed")
            )
            body = (
                text
                if len(text) <= CUT
                else f"{text[:CUT]}\n…(cut; the whole output is in {output})"
            )
            self.notify(
                f"Concorde: `concorde task merge {task}` ended with exit status {code} "
                f"({status}). Its output ({output}, errors in {messages}):\n{body}",
                {
                    "event": "merge_ended",
                    "task": task,
                    "exit_code": str(code),
                    "status": status,
                },
            )

        threading.Thread(target=reap, name=f"merge {task}", daemon=True).start()

    # --- waits ------------------------------------------------------------------------------

    def register_wait(self, arguments: dict):
        tool = "register_wait"
        task, until = arguments.get("task"), arguments.get("until")
        run, lock = arguments.get("run"), arguments.get("lock")
        targets = [
            name
            for name, value in (("until", until), ("run", run), ("lock", lock))
            if value
        ]
        if len(targets) != 1:
            raise own(
                tool,
                "invalid_input",
                "name exactly one of `until` (with `task`), `run` and `lock`; got "
                + (", ".join(targets) or "none"),
            )
        if until and not task:
            raise own(tool, "invalid_input", "`until` names the states of a `task`")
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
            command = f"concorde task wait {task} --until {','.join(until)}"
            now = wait.reached(self.primary, task, wait.check_until(until))
            if now is not None:
                return {"registered": False, "already": now}

            def waiting():
                return wait.wait_task(self.primary, task, until)

            meta = {"kind": "task", "task": task}
        elif run:
            description = f"the end of run {run}"
            command = f"concorde task wait --run {run}"
            now = wait.run_answer(self.primary, run)
            if now is not None:
                return {"registered": False, "already": now}

            def waiting():
                return wait.wait_run(self.primary, run)

            meta = {"kind": "run", "run": run}
        else:
            if task:
                store.load_any(self.primary, task)
            description = f"the release of the {lock} lock" + (
                f" of task {task}" if task else ""
            )
            command = f"concorde task wait {task + ' ' if task else ''}--lock {lock}"
            now = wait.lock_answer(self.primary, lock, task)
            if now["holder"] is None:
                return {"registered": False, "already": {**now, "released": True}}

            def waiting():
                return wait.wait_lock(self.primary, lock, task)

            meta = {"kind": "lock", "lock": lock, **({"task": task} if task else {})}
        if not self.channel:
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
        self.waits += 1
        identity = str(self.waits)
        self.start_wait(identity, description, waiting, {**meta, "wait": identity})
        return {
            "registered": True,
            "wait": identity,
            "channel": True,
            "waits_for": description,
        }

    def start_wait(self, identity: str, description: str, waiting, meta: dict) -> None:
        import threading

        def watch():
            try:
                value = waiting()
            except TaskError as error:
                link = task_cli.refusal("wait", error)
                self.notify(
                    f"Concorde: wait {identity} for {description} ended without it: "
                    f"{errors.render(link)}",
                    {**meta, "event": "wait_failed", "code": error.code},
                )
                return
            except Exception as error:  # noqa: BLE001 -- the session must hear of it
                link = errors.from_exception(
                    f"{ACTOR} (register_wait)",
                    error,
                    explanation="the server has no recovery for an unexpected error of a wait",
                )
                self.notify(
                    f"Concorde: wait {identity} for {description} failed: "
                    f"{errors.render(link)}",
                    {**meta, "event": "wait_failed", "code": link["code"]},
                )
                return
            self.notify(
                f"Concorde: {description} happened (wait {identity}): "
                f"{json.dumps(value, ensure_ascii=False)}",
                {**meta, "event": "wait_done"},
            )

        threading.Thread(target=watch, name=f"wait {identity}", daemon=True).start()


# The Tasks command whose refusals each tool passes on.
COMMANDS = {
    "task_list": "list",
    "task_show": "show",
    "task_open": "open",
    "task_escalate": "escalate",
    "task_close": "close",
    "task_merge": "merge",
    "register_wait": "wait",
    "workflow_report": "show",
    "locks": "list",
}


def call(project: Project, name: str, arguments) -> object:
    """The tool's answer, or ``Refusal`` with its error link."""
    if name not in TOOLS:
        raise own(
            str(name),
            "invalid_input",
            f"there is no tool {name!r}; the tools are {', '.join(TOOLS)}",
        )
    arguments = _check(name, arguments if arguments is not None else {})
    try:
        return getattr(project, name)(arguments)
    except TaskError as error:
        raise tasks_refusal(name, COMMANDS.get(name, name), error) from None


__all__ = ["ACTOR", "TOOLS", "Project", "Refusal", "call"]
