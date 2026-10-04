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
[session boundary](../../glossary.json#concept.session-boundary)'s hook, which leaves reads open. An
[Issue](../../glossary.json#concept.issue) record is outside the task worktree, so these tools
never write one; the session writes Issues through the Issue tools or the Issue command, as the
runs it starts do.

### req.task-session.no-sandbox — A task session's shell is not restricted

The boundary Task sessions writes for a task session SHALL restrict nothing but its file-writing
tools, carrying no sandbox, so that the session's commands reach every path, process, socket and
network host the machine offers.

A task session must change nothing outside its task worktree and nothing else about it is
restricted. What keeps its shell inside the task is the task-session
[guidance](../../glossary.json#concept.main-session-guidance) and Claude Code's `auto` mode, and
`concorde task merge` audits at the end that nothing outside the task worktree changed
([req.tasks.merge-nothing-outside](../tasks/requirements.md#req.tasks.merge-nothing-outside)). So
the session prepares its own worktree, probes the machine it runs on and runs whatever the work
needs, and no workaround is owed to a restriction that is not there.

### req.task-session.project-mcp — A task session gets the project MCP server without a channel

Task sessions SHALL start every task session with the
[project MCP server](../../glossary.json#concept.project-mcp-server) in an MCP configuration it
passes explicitly, telling the server that the session has no channel.

Claude Code does not wake a background session with channel events: a probe on 2026-09-29 (Claude
Code 2.1.284) found a `claude --bg` session started with
`--dangerously-load-development-channels server:concorde` never woken by the event of a wait it had
registered. Told so, `register_wait` answers the session with the `concorde task wait` command for
its background Bash instead of promising an event that never comes.

### req.task-session.mcp-approval — A task session is never asked to approve a project MCP server

The settings Task sessions writes for a task session SHALL disable the project `.mcp.json` entry
`concorde`, enable every other `.mcp.json` server the session loads that the primary worktree
approved, and disable every one it never approved.

Nobody answers Claude Code's dialog "New MCP server found in this project" in a background
session, which otherwise waits on it for ever. The `--mcp-config` server replaces the entry
`concorde`; a server counts as approved as Claude Code judges it from the settings sources that
record approvals ([module](module.md#project-mcp-approvals)); and a `.mcp.json` that is missing or
unusable names no server and does not keep the session from starting.

### req.task-session.boundary-first — The boundary is written before the session starts

Task sessions SHALL write a task session's boundary before it starts the session.

`--dry-run` writes the boundary and starts nothing, so no task session runs without its boundary.

### req.task-session.recorded — A started session is recorded

Task sessions SHALL record a task session as a node of the task's [trace](../../glossary.json#concept.trace), through Tasks' record updates, only after Claude Code reported it started.

A session that did not start leaves the task unchanged. A session Claude Code started whose record
is refused, because the task was closed meanwhile or its node cannot be written, is removed with
`claude rm`, which kills it, before the refusal is returned, since no end of the task would ever
stop, keep or remove a session no node names; the refusal says whether it was removed, and names
the `claude rm` that removes it by hand when it was not. The node's `main` names the main agent's
session the task session was started for, as `--main` gave it, and the recorded session makes it
the [task record](../../glossary.json#concept.task-record)'s `main`, the session the task session reports to until the main agent rebinds the
task.

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

The transcript is found by the session's full session id, which Claude Code's own list of sessions
gives, never by a pattern that could match another session's. A transcript that cannot be found or
copied does not fail the close; it is named in the close's warnings.

### req.task-session.node-finished — A task session's node receives its figures from Claude Code

When a task ends, Task sessions SHALL write into each task session's
[trace node](../../glossary.json#concept.trace-node), before the task's folder moves to the
[history](../../glossary.json#concept.history), the session's full session id, its status from
Claude Code's state of the session and, from its kept transcript, its usage and its end, taking the
cost only from Claude Code's own account in the transcript and leaving it null without one.

The figures are written into the node, not computed when a trace is read, because retention later
removes the transcript they come from while the node stays. A state Claude Code does not report as
`done` or `failed` leaves the status `unknown`.

### req.task-session.removed — An ended task leaves no task session in Claude's session list

Once a task has ended, by any outcome, Task sessions SHALL remove each of its task sessions whose
transcript it kept from Claude's session list with `claude rm`, as a best effort whose failure
leaves the close as it succeeded.

Each session it does not remove, because its transcript was not kept or `claude rm` failed, is
named in the close's warnings with the whole reason and the command that removes it by hand. A
task session matters to the developer only through the
[main agent](../../glossary.json#concept.main-agent), so an ended one is noise in that list.
