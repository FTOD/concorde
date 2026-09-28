# Task sessions requirements

The Module-wide obligations of [Task sessions](module.md). Exact commands, the
[session report](../../glossary.json#concept.session-report) and error codes are in the
[contracts](contracts.md); the [scenarios](scenarios.md) show the obligations at work.

## Starting and confining

### req.task-session.same-program — A task session runs on the main session's program

Task sessions SHALL start a [task session](../../glossary.json#concept.task-session) only on the agent program of the main session that asked for it, Claude Code or pi.

A pi task session runs with the developer's own pi configuration, with Concorde's boundary added
on top.

### req.task-session.program-unknown — No task session without a known program

A `concorde task session` command SHALL be refused, starting no task session, when the main session's program cannot be read from the environment.

The refusal is `client_unknown` and names each variable it looked at; the command line of Tasks
reads the program before handing the command to Task sessions.

### req.task-session.boundary — A task session's file tools write only its task

The boundary Task sessions writes for a task session SHALL let the session's file-writing tools change only the task worktree and its [decision log](../../glossary.json#concept.decision-log).

In Claude Code the file-writing tools are Edit and Write, checked by the
[write hook](../../glossary.json#concept.write-hook); in pi they are `write` and `edit`, checked by
the task-session extension. Both leave reads open.

### req.task-session.shell-boundary — A task session's shell writes only what its task needs

The boundary Task sessions writes for a task session SHALL let the session's shell commands write only the task worktree, the repository's Git directory, the primary worktree's `.concorde/runs/` and `.concorde/tasks/`, the user's package caches and, in pi, the session's private temporary directory.

In Claude Code the shell is Bash in Claude Code's sandbox; in pi `bash` commands run in
sandbox-runtime, whose sockets need the private temporary directory. Both leave reads and the
network open, allowing every host. The [run store](../../glossary.json#concept.run-store)
`.concorde/runs/` is writable because the task worktree's
[workspace binding](../../glossary.json#concept.workspace-binding) names the primary worktree's
`.concorde` as the records directory of every run started there.

### req.task-session.boundary-first — The boundary is written before the session starts

Task sessions SHALL write a task session's boundary before it starts the session.

`--dry-run` writes the boundary and starts nothing, so no task session runs without its boundary.

### req.task-session.recorded — A started session is recorded

Task sessions SHALL append a task session to the [task record](../../glossary.json#concept.task-record), through Tasks' record updates, only after Claude Code reported it started, or after the supervisor of its first pi round started.

A session that did not start leaves the record unchanged.

### req.task-session.round-recorded — Every pi round ends with a recorded outcome

Task sessions SHALL record every pi [session round](../../glossary.json#concept.session-round) as `delivered`, `escalated`, `failed` or `stopped`.

A round recorded as `failed` carries an error link naming pi's exit code, stop reason and error
message, the paths of the round's logs and, for a report the record contradicts, each mismatch.
A round whose supervisor ended without recording it is recorded `failed` by the next start,
`--answer` or `--stop` of the task.

### req.task-session.delivered-verified — Delivered only with the delivery commit

Task sessions SHALL record a pi session round as `delivered` only when the task branch holds the commit its session report names as a [delivery commit](../../glossary.json#concept.delivery-commit) of the task's workspace.

### req.task-session.escalated-verified — Escalated only with the recorded escalations

Task sessions SHALL record a pi session round as `escalated` only when the task record holds the escalations its session report names.
