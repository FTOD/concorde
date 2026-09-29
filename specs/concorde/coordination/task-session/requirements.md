# Task sessions requirements

The Module-wide obligations of [Task sessions](module.md). Exact commands, the session trace node
and error codes are in the [contracts](contracts.md); the [scenarios](scenarios.md) show the
obligations at work.

## Starting and confining

### req.task-session.same-program — A task session runs on the main agent's program

Task sessions SHALL start a [task session](../../glossary.json#concept.task-session) as a
background Claude Code session, the program the main agent runs on.

For now Claude Code is the only program a main agent runs on, so it is the only one a task session
runs on; the [workers](../../glossary.json#concept.worker) of the runs a task session starts take
their program from the [worker configuration](../../glossary.json#concept.worker-configuration)
and may run on pi.

### req.task-session.boundary — A task session's file tools write only its task

The boundary Task sessions writes for a task session SHALL let the session's file-writing tools change only the task worktree and its [decision log](../../glossary.json#concept.decision-log).

The file-writing tools are Edit and Write, checked by the
[write hook](../../glossary.json#concept.write-hook), which leaves reads open.

### req.task-session.shell-boundary — A task session's shell writes only what its task needs

The boundary Task sessions writes for a task session SHALL let the session's shell commands write only the task worktree, the repository's Git directory, the task's own folder `.concorde/tasks/<task>/` and `.concorde/locks/` of the primary worktree and the user's package caches.

The shell is Bash in Claude Code's sandbox, which leaves reads and the network open, allowing every
host, through the sandbox's proxy on `localhost`, which the workers of the runs the session starts
pass on ([req.workers.proxy-passed](../../execution/workers/launch.md#req.workers.proxy-passed)).
The task's folder is writable because the task worktree's
[workspace binding](../../glossary.json#concept.workspace-binding) names its `workspace/` as the
workspace folder of every run started there, and `.concorde/locks/` because those runs take their
locks there.

### req.task-session.boundary-first — The boundary is written before the session starts

Task sessions SHALL write a task session's boundary before it starts the session.

`--dry-run` writes the boundary and starts nothing, so no task session runs without its boundary.

### req.task-session.recorded — A started session is recorded

Task sessions SHALL record a task session as a node of the task's [trace](../../glossary.json#concept.trace), through Tasks' record updates, only after Claude Code reported it started.

A session that did not start leaves the task unchanged. The node's `main` names the main agent's
session the task session reports to, as `--main` gave it.

## Ending with the task

### req.task-session.stopped-before-close — A close without a merge stops task sessions first

Before a task is closed without a merge, Task sessions SHALL stop every task session of the task
with `claude stop`, refusing the close, before it changed anything of the task, when one of them
cannot be confirmed stopped.

A session Claude Code no longer knows counts as stopped. Stopping first keeps a session from going
on working in, or starting runs in, the worktree the close removes; a merge stops nothing, since a
delivered task's session has reported and waits.

### req.task-session.transcript-kept — A task session's transcript moves to the history

When a task ends, Task sessions SHALL copy the transcript of each of its task sessions into that
session's [trace node](../../glossary.json#concept.trace-node) before the task's folder
moves to the [history](../../glossary.json#concept.history), and never write into the history
afterwards.

A transcript that cannot be found or copied does not fail the close; it is named in the close's
warnings.

### req.task-session.removed — An ended task leaves no task session in Claude's session list

Once a task has ended, by any outcome, Task sessions SHALL remove each of its task sessions whose
transcript it kept from Claude's session list with `claude rm`, as a best effort whose failure
leaves the close as it succeeded.

Each session it does not remove, because its transcript was not kept or `claude rm` failed, is
named in the close's warnings with the whole reason and the command that removes it by hand. A
task session matters to the developer only through the
[main agent](../../glossary.json#concept.main-agent), so an ended one is noise in that list.
