"""The tools of the project MCP server, each a thin call into Tasks, Tracing, Workflows' records or
the project's Issues.

``workflow_step`` is the one tool that works on a workspace rather than on records: it runs the
``concorde workflow step`` of the worktree the session started in as a child of this server, so a
step's detached runner is a process of the server rather than of a relaying agent's turn or of one
of the session's background commands, and lives until its run ends.

Every call reads the stores afresh from the primary worktree, so an answer is the state when the
call arrives; the server keeps no copy of any record and adds no rule of its own. A refusal is the
error link of the component that refused, unchanged: Tasks' own for a task command, the server's
own (actor ``Concorde project MCP server (<tool>)``) for arguments it cannot take. The Issue tools
answer and refuse exactly as ``concorde issues`` does, recording the session as ``main-agent`` in
the primary worktree and as ``task-session`` with its task in a bound task worktree. Locks are never
waited for: a tool that needs one is refused at once, naming its holder, when another process holds
it.
"""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
import tempfile
from argparse import Namespace
from pathlib import Path

from .. import errors
from ..issues import command as issues
from ..tasks import cli as task_cli
from ..tasks import merge, store, wait
from ..tasks.store import TaskError
from ..tracing import layout, locks, reader

ACTOR = "Concorde project MCP server"
# The entry point of the running Concorde, which the merge it starts runs too.
SCRIPT = Path(__file__).resolve().parents[3] / "scripts/concorde.py"
# How much of a finished merge's output a notification carries; the file holds all of it.
CUT = 6000
# The longest a workflow_step call waits for its run, so that the call returns within two minutes.
STEP_WAIT = 100
# What a workflow_step call adds to its wait before it gives up on the step command itself.
STEP_GRACE = 60


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
ISSUE = {"type": "string", "minLength": 1}
EVIDENCE = {"type": "array", "items": TEXT, "minItems": 1}


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
    "issue_list": {
        "description": "A summary row per Issue of the project with its severity and tier, as "
        "`concorde issues list`: every Issue, open and closed, unless filtered. `status` keeps "
        "the Issues with that status, `module` those whose latest report has that owner or "
        "reporting Module, `tier` those whose latest report has one of those tiers and "
        "`severity` those whose latest report has one of those severities; given together, an "
        "Issue must pass each. Rows come by identity, or with `sort` severity most severe "
        "first, then by tier, decision-needed first, then the Issue reported first, Issues "
        "without a severity last.",
        "inputSchema": schema(
            {
                "status": {"enum": ["open", "closed"]},
                "module": TEXT,
                "tier": {
                    "type": "array",
                    "items": {"enum": list(issues.TIERS)},
                    "minItems": 1,
                },
                "severity": {
                    "type": "array",
                    "items": {"enum": list(issues.SEVERITIES)},
                    "minItems": 1,
                },
                "sort": {"enum": ["severity"]},
            }
        ),
    },
    "issue_show": {
        "description": "One Issue's complete record and revision, as `concorde issues show`.",
        "inputSchema": schema({"issue": ISSUE}, ["issue"]),
    },
    "issue_check": {
        "description": "Check every Issue record the primary worktree keeps, as `concorde issues "
        "check` there: errors and notes, each naming the record.",
        "inputSchema": schema({}),
    },
    "issue_report": {
        "description": "Record an Issue report, as `concorde issues report`: `report` is the "
        "report object (contract.issues.report, with its tier and severity), or `file` a report file; "
        "`check` checks it and records nothing. It creates an Issue, or appends to the one its "
        "issue_id names at its expected_revision. Evidence paths are checked in the session's "
        "worktree; the report is recorded as the session's (main-agent in the primary worktree, "
        "task-session with its task in a task worktree). Refused at once with merge_busy, naming "
        "the holder, while another process holds the merge lock.",
        "inputSchema": schema(
            {
                "report": {"type": "object"},
                "file": TEXT,
                "check": {"type": "boolean"},
            }
        ),
    },
    "issue_close": {
        "description": "Close an open Issue at its current revision, as `concorde issues "
        "close`: `reason` resolved, duplicate (with `duplicate_of`) or not-actionable, a `note` "
        "and at least one `evidence` item. Refused at once with merge_busy while another "
        "process holds the merge lock.",
        "inputSchema": schema(
            {
                "issue": ISSUE,
                "reason": {"enum": list(issues.CLOSING_REASONS)},
                "note": TEXT,
                "evidence": EVIDENCE,
                "duplicate_of": ISSUE,
            },
            ["issue", "reason", "note", "evidence"],
        ),
    },
    "issue_reopen": {
        "description": "Reopen a closed Issue at its current revision, as `concorde issues "
        "reopen`, with a `note` and at least one `evidence` item. Refused at once with "
        "merge_busy while another process holds the merge lock.",
        "inputSchema": schema(
            {"issue": ISSUE, "note": TEXT, "evidence": EVIDENCE},
            ["issue", "note", "evidence"],
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
    "workflow_step": {
        "description": "Start or await one workflow step in the bound workspace this session "
        "started in, as a step agent relays it: runs that worktree's own `concorde workflow step "
        "--json <request> --wait <wait>` as a process of this server, so the run it starts "
        "outlives the relaying agent's turn, and returns the step outcome it printed. `request` is the step request as an object; `wait` is at most 100 seconds "
        "(default 100). Refused in a worktree without a workspace binding.",
        "inputSchema": schema(
            {
                "request": {"type": "object"},
                "wait": {"type": "integer", "minimum": 0, "maximum": STEP_WAIT},
            },
            ["request"],
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

    def __init__(
        self,
        primary: Path,
        session: str | None,
        channel: bool,
        notify,
        where: Path | None = None,
    ):
        self.primary = primary
        # The folder the session started in, whose worktree workflow_step works on.
        self.where = where or primary
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
        return store.list_tasks(
            self.primary, arguments.get("state"), arguments.get("main")
        )

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

    def task_rebind(self, arguments: dict):
        return store.rebind(self.primary, arguments["task"], arguments["main"])

    def task_report(self, arguments: dict):
        return store.report(
            self.primary,
            arguments["task"],
            arguments["text"],
            arguments.get("escalations", []),
        )

    def task_answer(self, arguments: dict):
        return store.answer(
            self.primary, arguments["task"], arguments["reports"], arguments["text"]
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

    def task_resolve(self, arguments: dict):
        return store.resolve(self.primary, arguments["task"], arguments["issues"])

    # --- Issues -----------------------------------------------------------------------------

    def _reporter(self) -> tuple[Path, str, str | None]:
        """The session's worktree, whom its Issue writes are recorded as and its task: a bound
        task worktree's session is its task's task session, any other the main agent."""
        from ..execution import binding as binding_file

        try:
            root = binding_file.toplevel(self.where)
            bound = binding_file.load(root)
        except binding_file.BindingError:
            return self.primary, "main-agent", None
        if bound is None or root == self.primary:
            return root, "main-agent", None
        return root, "task-session", bound["workspace"]

    def issue_list(self, arguments: dict):
        return issues.list_action(
            self.primary,
            status=arguments.get("status"),
            module=arguments.get("module"),
            tiers=arguments.get("tier"),
            severities=arguments.get("severity"),
            sort=arguments.get("sort"),
        )

    def issue_show(self, arguments: dict):
        return issues.show_action(self.primary, arguments["issue"])

    def issue_check(self, arguments: dict):
        return issues.check(self.primary)[0]

    def issue_report(self, arguments: dict):
        root, agent, task = self._reporter()
        if ("report" in arguments) == ("file" in arguments):
            raise own(
                "issue_report",
                "invalid_input",
                "give the report either as `report`, an object, or as `file`, a path",
            )
        file = arguments.get("file")
        return issues.report_action(
            root,
            file=Path(root, file) if file is not None else None,
            report=arguments.get("report"),
            task=task,
            check_only=arguments.get("check", False),
            agent=agent,
            wait=0.0,
        )

    def issue_close(self, arguments: dict):
        return issues.dispose(
            self.primary,
            arguments["issue"],
            arguments["reason"],
            arguments["note"],
            arguments["evidence"],
            duplicate_of=arguments.get("duplicate_of"),
            actor=self._reporter()[1],
            wait=0.0,
        )

    def issue_reopen(self, arguments: dict):
        return issues.dispose(
            self.primary,
            arguments["issue"],
            "reopened",
            arguments["note"],
            arguments["evidence"],
            actor=self._reporter()[1],
            wait=0.0,
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

    # --- workflow steps ---------------------------------------------------------------------

    def workflow_step(self, arguments: dict):
        """The step outcome ``concorde workflow step`` printed in the session's worktree.

        The command runs as this server's child, and the runner it detaches is a process of its
        own: it lives until its run ends, whether or not the relaying agent's turn, the session's
        Bash calls or the session itself still run. A worktree without a workspace
        binding is refused with ``unbound_worktree``; a request the step command refuses is
        refused with its own link, unchanged; an output that is no JSON object with
        ``step_failed``.
        """
        from ..execution import binding as binding_file
        from ..workflows.step import concorde_command

        tool = "workflow_step"
        try:
            root = binding_file.toplevel(self.where)
            bound = binding_file.load(root)
        except binding_file.BindingError as error:
            raise own(
                tool,
                "unbound_worktree",
                f"the session's folder {self.where} has no usable workspace binding: "
                f"{error.code}: {error}",
                reason="environment",
                explanation="a workflow step runs only in the bound workspace of the session "
                "that asks for it",
                options=["run the workflow in a task worktree, from its task session"],
            ) from None
        if bound is None:
            raise own(
                tool,
                "unbound_worktree",
                f"the session's worktree {root} has no workspace binding "
                f"({binding_file.BINDING}), so it is no workspace a workflow could run in",
                reason="environment",
                explanation="a workflow step runs only in the bound workspace of the session "
                "that asks for it",
                options=["run the workflow in a task worktree, from its task session"],
            )
        wait = arguments.get("wait", STEP_WAIT)
        command = [
            *concorde_command(root),
            "workflow",
            "step",
            "--json",
            json.dumps(arguments["request"], ensure_ascii=False),
            "--wait",
            str(wait),
        ]
        environment = dict(os.environ)
        if command[1:3] == ["-m", "concorde"]:
            environment["PYTHONPATH"] = os.pathsep.join(
                [str(Path(__file__).resolve().parents[2])]
                + ([environment["PYTHONPATH"]] if environment.get("PYTHONPATH") else [])
            )
        shown = shlex.join(command)
        try:
            done = subprocess.run(
                command,
                cwd=root,
                env=environment,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                timeout=wait + STEP_GRACE,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            raise own(
                tool,
                "step_failed",
                f"`{shown}` in {root} did not answer: {error}",
                reason="environment",
                explanation="the server only passes the step command's answer on and has none",
                options=[
                    "ask for the same step again; the same key never starts a run twice"
                ],
            ) from None
        try:
            value = json.loads(done.stdout)
        except ValueError:
            value = None
        if not isinstance(value, dict):
            raise own(
                tool,
                "step_failed",
                f"`{shown}` in {root} exited with status {done.returncode} and printed no JSON "
                f"object: {(done.stderr or done.stdout).strip()[-2000:] or '(no output)'}",
                reason="environment",
                explanation="the server only passes the step command's answer on and has none",
                options=[
                    "ask for the same step again; the same key never starts a run twice"
                ],
            )
        if "key" not in value and isinstance(value.get("error"), dict):
            # The step command refused the request or the workspace: its own link, unchanged.
            raise Refusal(value["error"])
        return value

    def register_wait(self, arguments: dict):
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
            command = f"concorde task wait {task} --until {','.join(until)}"
            now = wait.reached(self.primary, task, wait.check_until(until))
            if now is not None:
                return {"registered": False, "already": now}

            def waiting():
                return wait.wait_task(self.primary, task, until)

            meta = {"kind": "task", "task": task}
        elif former:
            description = (
                f"task {task} naming a main agent's session other than {former}"
            )
            command = f"concorde task wait {task} --rebound {shlex.quote(former)}"
            now = wait.rebound(self.primary, task, former)
            if now is not None:
                return {"registered": False, "already": now}

            def waiting():
                return wait.wait_rebound(self.primary, task, former)

            meta = {"kind": "rebound", "task": task}
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
    "task_rebind": "rebind",
    "task_report": "report",
    "task_answer": "answer",
    "task_resolve": "resolve",
    "task_merge": "merge",
    "register_wait": "wait",
    "workflow_report": "show",
    "locks": "list",
}
# The tools whose calls may take long and are served on a thread of their own, so the session's
# other calls are answered meanwhile.
THREADED = frozenset({"workflow_step"})


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
    except issues.Refusal as refusal:
        # The Issues command's own link, unchanged.
        raise Refusal(refusal.link) from None


__all__ = ["ACTOR", "THREADED", "TOOLS", "Project", "Refusal", "call"]
