# Task session requirements

The Module-wide obligations of [Task session](module.md). Exact commands, the
[session report](../../glossary.json#concept.session-report) and error codes are in the
[contracts](contracts.md); the [scenarios](scenarios.md) show the obligations at work.

## Starting and confining

### req.task-session.same-program — A task session runs on the main session's program

Tasks SHALL start a [task session](../../glossary.json#concept.task-session) only on the agent program of the main session that asked for it, Claude Code or pi, refusing to start one when that program cannot be read from the environment.

A pi task session runs with the developer's own pi configuration, with Concorde's boundary added
on top.

### req.task-session.boundary — A task session writes only its task

The boundary Tasks writes for a task session SHALL let the session's file-writing tools change only the task worktree and its [decision log](../../glossary.json#concept.decision-log), and its shell commands write only the task worktree, the repository's Git directory, the primary worktree's `.concorde/runs/` and `.concorde/tasks/` and the user's package caches.

In Claude Code the file-writing tools are Edit and Write, checked by the
[write hook](../../glossary.json#concept.write-hook), and the shell is Bash in Claude Code's
sandbox; in pi they are `write` and `edit`, checked by the task-session extension, and `bash`
commands run in sandbox-runtime. Both leave reads and the network open, allowing every host. The
[run store](../../glossary.json#concept.run-store) `.concorde/runs/` is writable because the task
worktree's [workspace binding](../../glossary.json#concept.workspace-binding) names the primary
worktree's `.concorde` as the records directory of every run started there.

### req.task-session.recorded — A started session is recorded

Tasks SHALL append a task session to the [task record](../../glossary.json#concept.task-record) only after Claude Code reported it started, or after the supervisor of its first pi round started.

A session that did not start leaves the record unchanged.

### req.task-session.round-recorded — Every pi round ends with a recorded outcome

Tasks SHALL record every pi [session round](../../glossary.json#concept.session-round) as `delivered`, `escalated`, `failed` or `stopped`, recording it as `delivered` only when the task branch holds the commit its session report names as a [delivery commit](../../glossary.json#concept.delivery-commit) of the task's workspace, and as `escalated` only when the task record holds the escalations it names.

A round recorded as `failed` carries an error link naming pi's exit code, stop reason and error
message, the paths of the round's logs and, for a report the record contradicts, each mismatch.
