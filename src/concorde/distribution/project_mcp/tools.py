"""The tools of the project MCP server, each a thin call into Tasks, Tracing, the workflow part's
tools or the project's Issues, and the process that answers one call.

The server runs no tool in its own process: each call runs ``concorde project-mcp --call <tool>`` of
the primary worktree as a process of its own (``serve_call`` here), so the answer is always the one
of the Concorde code that worktree's ``concorde`` runs at the time of the call, however long the
session has been running. The call's arguments and the session's provenance arrive as one JSON
object on standard input; the answer leaves as one JSON line on standard output.

``workflow_step`` and ``workflow_report`` are the workflow part's own tools (``workflows/tools.py``),
which the server presents here until it reads the parts' registrations; ``workflow_step`` works on
the worktree the session started in rather than on records.

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

import hashlib
import json
import os
import shlex
from argparse import Namespace
from pathlib import Path

from ...kernel import errors
from ...kernel.refusal import KernelError
from ...issues import command as issues
from ...coordination.tasks import cli as task_cli
from ...coordination.tasks import merge, store, wait
from ...coordination.tasks.store import TaskError
from ...kernel.tracing import layout, locks, reader
from ...workflows import tools as workflow_tools
from ...workflows.tools import STEP_GRACE, STEP_WAIT, concorde_of

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
# What every Issue write tool says of the recovery the write runs first.
RECOVERY = (
    " Before writing, it puts back what a killed Issue write left uncommitted; refused with "
    "recovery_failed when that fails, the record staying uncommitted until the cause is fixed "
    "and `concorde issues recover` (no tool) puts it back, and with uncommitted_change when the "
    "Issue's record holds a change no Issue write made, to be inspected and reverted in the "
    "primary worktree, never committed by hand."
)


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
    # The workflow part's tools, presented here until the server reads part registrations.
    "workflow_report": workflow_tools.TOOLS["workflow_report"],
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
        "the holder, while another process holds the merge lock." + RECOVERY,
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
        "process holds the merge lock." + RECOVERY,
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
        "merge_busy while another process holds the merge lock." + RECOVERY,
        "inputSchema": schema(
            {"issue": ISSUE, "note": TEXT, "evidence": EVIDENCE},
            ["issue", "note", "evidence"],
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
    "workflow_step": workflow_tools.TOOLS["workflow_step"],
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
    from ...spec.schema import ContractError, validate

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
    """What every tool needs: the primary worktree, the session and whether it has a channel.

    One call's process makes one; what the server must do after the answer, start a wait's watch
    or become the merge, it leaves in ``watch`` and ``handover``."""

    def __init__(
        self,
        primary: Path,
        session: str | None,
        channel: bool,
        where: Path | None = None,
        merge: dict | None = None,
    ):
        self.primary = primary
        # The folder the session started in, whose worktree workflow_step works on.
        self.where = where or primary
        self.session = session
        self.channel = channel
        # Set when the server started this call for a merge, which the call's process becomes.
        self.merge = merge
        self.watch: dict | None = None
        self.handover: dict | None = None

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
                arguments["node"], reader.concorde_directories(self.primary)
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
            folder, concorde = reader.locate(
                run, reader.concorde_directories(self.primary)
            )
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
        return workflow_tools.workflow_report(self.where, arguments)

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
        from ...kernel import binding as binding_file

        try:
            root = binding_file.toplevel(self.where)
            bound = binding_file.load(root)
        except KernelError:
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

    def _busy(
        self,
        tool: str,
        code: str,
        task: str,
        busy: locks.LockBusy,
        what: str | None = None,
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
        attempt = store.attempt_lock_path(self.primary, task)
        workspace = wait.lock_path(self.primary, "workspace", task)
        merging = store.merge_lock_path(self.primary)
        holder = (
            f"`concorde task merge` of task {task}, started by the project MCP server"
        )
        if self.merge is None:
            raise own(
                tool,
                "invalid_input",
                "a merge starts only through the project MCP server, whose process the merge "
                "becomes",
                reason="environment",
            )
        command, environment = concorde_of(self.primary)
        argv = [*command, "task", "merge", task, "--wait", "0"]
        argv += [word for check in checks for word in ("--check", check)]
        argv += ["--resume"] if resume else ["--abort"] if abort else []
        taken = []
        # The task's merge attempt lock first, as the command takes it, so that a merge of the
        # task still running is refused before any other lock is touched.
        wanted = (
            (
                attempt,
                "merge_busy",
                "its merge attempt lock, held by a merge of the task",
            ),
            (workspace, "workspace_busy", None),
            (merging, "merge_busy", None),
        )
        try:
            for path, code, what in wanted:
                try:
                    descriptor = locks.acquire(path)
                except locks.LockBusy as busy:
                    raise self._busy(tool, code, task, busy, what) from None
                taken.append((path, descriptor))
                # This process becomes the merge (``hand_over``), so its pid is the merge's.
                locks.write_entry(
                    descriptor, locks.line(holder, os.getpid(), task, self.session)
                )
            # Holding the task's locks, no other attempt can take the next attempt's folder,
            # where the merge's output is kept with the task, also once it moved to the history.
            folder = merge.next_attempt(self.primary, task)
            folder.mkdir(parents=True)
        except BaseException:
            for _, descriptor in taken:
                os.close(descriptor)
            raise
        environment[locks.INHERITED] = json.dumps(
            {path.as_posix(): descriptor for path, descriptor in taken}
        )
        environment[merge.RESERVED] = folder.as_posix()
        if self.session:
            environment[locks.SESSION] = self.session
        output, messages = folder / merge.OUTPUT, folder / merge.MESSAGES
        self.handover = {
            "task": task,
            "argv": argv,
            "environment": environment,
            "descriptors": [descriptor for _, descriptor in taken],
            "folder": folder,
            "output": output,
            "messages": messages,
        }
        fallback = f"concorde task wait {task} --merge"
        return {
            "started": {
                "command": "concorde " + shlex.join(argv[len(command) :]),
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
                if self.channel
                else {
                    "channel": False,
                    "command": fallback,
                    "explanation": "this session has no channel from the server, so it is not "
                    "woken; run the command in background Bash, which returns once the merge "
                    "ended and its output is complete, naming the output file to read",
                }
            ),
        }

    # --- waits ------------------------------------------------------------------------------

    # --- workflow steps ---------------------------------------------------------------------

    def workflow_step(self, arguments: dict):
        return workflow_tools.workflow_step(self.where, arguments)

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
            words = [task, "--until", ",".join(until)]
            now = wait.reached(self.primary, task, wait.check_until(until))
            if now is not None:
                return {"registered": False, "already": now}
            meta = {"kind": "task", "task": task}
        elif former:
            description = (
                f"task {task} naming a main agent's session other than {former}"
            )
            words = [task, "--rebound", former]
            now = wait.rebound(self.primary, task, former)
            if now is not None:
                return {"registered": False, "already": now}
            meta = {"kind": "rebound", "task": task}
        elif run:
            description = f"the end of run {run}"
            words = ["--run", run]
            now = wait.run_answer(self.primary, run)
            if now is not None:
                return {"registered": False, "already": now}
            meta = {"kind": "run", "run": run}
        else:
            if task:
                store.load_any(self.primary, task)
            description = f"the release of the {lock} lock" + (
                f" of task {task}" if task else ""
            )
            words = [*([task] if task else []), "--lock", lock]
            now = wait.lock_answer(self.primary, lock, task)
            if now["holder"] is None:
                return {"registered": False, "already": {**now, "released": True}}
            # The wait command may start after the holder is gone and then names none; the
            # registration and the event still name the holder it was registered for.
            description += f", held by {json.dumps(now['holder'], ensure_ascii=False)}"
            meta = {"kind": "lock", "lock": lock, **({"task": task} if task else {})}
        command = shlex.join(["concorde", "task", "wait", *words])
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
        # The server runs the same command as a process it watches and wakes the session with its
        # answer; the wait's identity is the server's.
        self.watch = {
            "words": ["task", "wait", *words],
            "description": description,
            "meta": meta,
        }
        return {"registered": True, "channel": True, "waits_for": description}


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
# The tools whose calls may take long and are served on a thread of their own, so the session's
# other calls are answered meanwhile.
THREADED = frozenset(workflow_tools.THREADED)


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
    except workflow_tools.ToolRefusal as refusal:
        # The workflow part's own link, unchanged.
        raise Refusal(refusal.link) from None


def listing() -> list[dict]:
    """The tools as ``tools/list`` gives them."""
    return [{"name": name, **tool} for name, tool in TOOLS.items()]


def digest(tools: list[dict]) -> str:
    """The digest of a tool listing, by which the server notices that the tools changed."""
    text = json.dumps(tools, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def answer(name: str, envelope: dict) -> tuple[dict, Project | None]:
    """One call's answer, ``{"value"}`` or ``{"error"}`` with the digest of this code's tools and,
    for a wait the server is to watch, its ``watch``; and the project it was answered in."""
    tools = digest(listing())
    try:
        project = Project(
            Path(envelope["primary"]),
            envelope.get("session"),
            bool(envelope.get("channel")),
            Path(envelope["where"]),
            envelope.get("merge"),
        )
    except (KeyError, TypeError) as error:
        link = own(
            str(name),
            "invalid_input",
            f"the call's input lacks the session's provenance: {error!r}",
            reason="environment",
            explanation="only the project MCP server starts a call's process, and it always "
            "passes the primary worktree and the session's folder",
        ).link
        return {"error": link, "tools": tools}, None
    try:
        value = call(project, name, envelope.get("arguments"))
    except Refusal as refusal:
        return {"error": refusal.link, "tools": tools}, project
    except Exception as failure:  # noqa: BLE001 -- every failure is a detailed error link
        link = errors.from_exception(
            f"{ACTOR} ({name})",
            failure,
            explanation="the server has no recovery for an unexpected error; nothing after it ran",
        )
        return {"error": link, "tools": tools}, project
    reply = {"value": value, "tools": tools}
    if project.watch is not None:
        reply["watch"] = project.watch
    return reply, project


def _write(descriptor: int, text: str) -> None:
    data = text.encode("utf-8")
    while data:
        data = data[os.write(descriptor, data) :]


def hand_over(project: Project, line: str, writer) -> int:
    """Become the merge ``task_merge`` started: answer through a copy of standard output that the
    exec closes, which ends the answer, then replace this process with ``concorde task merge``,
    its standard output and error going to the files of the attempt's folder and the locked
    descriptors inherited.

    When the exec fails, a second answer line refuses the call with ``start_failed``, the folder
    is removed again, and this process ends, which releases the locks."""
    plan = project.handover
    writer.flush()
    reply = os.dup(writer.fileno())  # not inheritable: the exec closes it
    for path, target in ((plan["output"], 1), (plan["messages"], 2)):
        opened = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        os.dup2(opened, target)
        os.close(opened)
    null = os.open(os.devnull, os.O_RDONLY)
    os.dup2(null, 0)
    os.close(null)
    for descriptor in plan["descriptors"]:
        os.set_inheritable(descriptor, True)
    _write(reply, line)
    try:
        os.execve(plan["argv"][0], plan["argv"], plan["environment"])
    except OSError as error:
        for path in (plan["output"], plan["messages"]):
            Path(path).unlink(missing_ok=True)
        try:
            Path(plan["folder"]).rmdir()
        except OSError:
            pass
        link = own(
            "task_merge",
            "start_failed",
            f"`{shlex.join(plan['argv'])}` could not be started: {error}; its locks were "
            "released",
            reason="environment",
            explanation="the operating system refused to start the process",
        ).link
        _write(reply, json.dumps({"error": link}, ensure_ascii=False) + "\n")
        return 1


def serve_call(name: str, reader, writer) -> int:
    """``concorde project-mcp --call <tool>``: answer one call of the server, read as one JSON
    object from ``reader``, with one JSON line on ``writer``."""
    project = None
    try:
        envelope = json.loads(reader.read())
        problem = None if isinstance(envelope, dict) else "it is no JSON object"
    except ValueError as error:
        problem = str(error)
    if problem is not None:
        link = own(
            str(name),
            "invalid_input",
            f"the call's input cannot be read: {problem}",
            reason="environment",
            explanation="only the project MCP server starts a call's process, with one JSON "
            "object on its standard input",
        ).link
        reply = {"error": link, "tools": digest(listing())}
    else:
        reply, project = answer(name, envelope)
    line = json.dumps(reply, ensure_ascii=False, separators=(",", ":")) + "\n"
    if project is not None and project.handover is not None and "error" not in reply:
        return hand_over(project, line, writer)
    writer.write(line)
    writer.flush()
    return 0


__all__ = [
    "ACTOR",
    "STEP_GRACE",
    "STEP_WAIT",
    "THREADED",
    "TOOLS",
    "Project",
    "Refusal",
    "call",
    "concorde_of",
    "digest",
    "listing",
    "serve_call",
]
