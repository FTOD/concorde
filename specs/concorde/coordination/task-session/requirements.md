# Task sessions requirements

The Module-wide obligations of [Task sessions](module.md). The [contracts](contracts.md) give:

- Exact commands.
- The session trace node.
- Error codes.

The [scenarios](scenarios.md) show the obligations at work.

## Starting and confining

### req.task-session.same-program — A task session runs on the main agent's program

Task sessions SHALL start a [task session](../../glossary.json#concept.task-session) as a
background Claude Code session, the program the main agent runs on.

For now Claude Code is the only program a main agent runs on, so it is the only one a task session
runs on. The [workers](../../glossary.json#concept.worker) of the runs a task session starts take
their program from the [worker configuration](../../glossary.json#concept.worker-configuration).
Those workers may run on pi.

### req.task-session.boundary — A task session's file tools write only its task

The boundary Task sessions writes for a task session SHALL let the session's file-writing tools
change only the task worktree and its [decision log](../../glossary.json#concept.decision-log).

The file-writing tools are those the [task-session settings](contracts.md#task-session-settings)
list. The [session boundary](../../glossary.json#concept.session-boundary)'s hook checks every one
of them. The hook leaves reads open. An [Issue](../../glossary.json#concept.issue) record is outside the task
worktree, so these tools never write one. The session writes Issues through the Issue tools or the
Issue command, as the runs it starts do.

### req.task-session.no-sandbox — A task session's shell is not restricted

The boundary Task sessions writes for a task session SHALL restrict nothing but its file-writing
tools, carrying no sandbox, so that the session's commands reach every path, process, socket and
network host the machine offers.

A task session must change nothing outside its task worktree. Nothing else about the session is
restricted. The task-session [guidance](../../glossary.json#concept.main-session-guidance) and
Claude Code's `auto` mode keep its shell inside the task. At the end, `concorde task merge` audits
that nothing outside the task worktree changed
([req.tasks.merge-nothing-outside](../tasks/requirements.md#req.tasks.merge-nothing-outside)). So
the session does the following:

- Prepares its own worktree.
- Probes the machine it runs on.
- Runs whatever the work needs.

No workaround is owed to a restriction that is not there.

### req.task-session.project-mcp — A task session gets the project MCP server without a channel

Task sessions SHALL start every task session with the
[project MCP server](../../glossary.json#concept.project-mcp-server) in an MCP configuration it
passes explicitly, telling the server that the session has no channel.

Claude Code does not wake a background session with channel events. A probe on 2026-09-29 (Claude
Code 2.1.284) tested a `claude --bg` session started with
`--dangerously-load-development-channels server:concorde`. The probe found that the event of a wait
the session registered never woke the session. Told so, `register_wait` answers the session with the
`concorde task wait` command for its background Bash instead of promising an event that never comes.

### req.task-session.mcp-approval — A task session is never asked to approve a project MCP server

The settings Task sessions writes for a task session SHALL disable the project `.mcp.json` entry
`concorde`, enable every other `.mcp.json` server the session loads that the primary worktree or
the task worktree approved, and disable every one that neither approved.

Nobody answers Claude Code's dialog "New MCP server found in this project" in a background session,
which otherwise waits on it for ever. The `--mcp-config` server replaces the entry `concorde`. A
server counts as approved as Claude Code judges it from the settings sources that record approvals
for either worktree ([contracts](contracts.md#project-mcp-approvals)). Claude Code itself honours
the task worktree's approvals in a session started there. A `.mcp.json` that is missing or unusable
names no server. Such a file does not keep the session from starting.

### req.task-session.boundary-first — The boundary is written before the session starts

Before it starts a task session, Task sessions SHALL write that session's boundary.

`--dry-run` writes the boundary and starts nothing, so no task session runs without its boundary.

### req.task-session.one-working — One task session works in a task at a time

While Claude Code lists a recorded task session of a task in a state other than `done` or `failed`,
Task sessions SHALL refuse to start another task session of that task, before writing anything.

Two sessions writing one task worktree would confuse the
[write audits](../../glossary.json#concept.write-audit) of its runs and its delivery.
A session that is `done` waits for its next message. A session that is `done`, `failed` or no longer
listed does not refuse a start, so a stalled or ended session can be replaced. Every start starts
and records a session of its own and never reuses an earlier one. A caller that retries a start
whose result it did not see is refused while the session it started still works.

### req.task-session.recorded — A started session is recorded

Task sessions SHALL record a task session as a node of the task's
[trace](../../glossary.json#concept.trace), through Tasks' record updates, only after Claude Code
reports it started.

A session that did not start leaves the task unchanged. A started session's record can be refused
because the task was closed meanwhile or its node cannot be written. When that record is refused,
the session is removed with `claude rm`, which kills it, before the refusal is returned. This
removal occurs because no end of the task would ever do the following to a session no node names:

- Stop it.
- Keep it.
- Remove it.

The refusal says whether the session was removed. When the session was not removed, the refusal
names the `claude rm` that removes it by hand. The node's `main` names the main agent's session the
task session was started for, as `--main` gave it. The recorded session makes that main agent's
session the [task record](../../glossary.json#concept.task-record)'s `main`. Until the main agent
rebinds the task, the task session reports to that main agent's session.

## Ending with the task

### req.task-session.stopped-before-close — A close without a merge stops task sessions first

Before a task closes without a merge, Task sessions SHALL stop each of its task sessions with
`claude stop`, refusing the close before changing anything of the task when one cannot be confirmed
stopped.

A session Claude Code no longer knows counts as stopped. Stopping first keeps a session from going
on working in, or starting runs in, the worktree the close removes. A merge stops nothing, since a
delivered task's session has reported and waits.

### req.task-session.transcript-kept — A task session's transcript moves to the history

When a task ends, Task sessions SHALL copy the transcript of each of its task sessions into that
session's [trace node](../../glossary.json#concept.trace-node) before the task's folder moves to the
[history](../../glossary.json#concept.history), naming in the close's warnings, without failing the
close, each transcript it cannot find, copy or read.

The transcript is found by the session's full session id, which Claude Code's own list of sessions
gives. It is never found by a pattern that could match another session's. A failed copy leaves no
part of the transcript in the node, or the warning names what could not be removed. Either way the
node lists no transcript.

### req.task-session.history-untouched — Ending task sessions never writes the history

Task sessions SHALL write nothing into a task's [history](../../glossary.json#concept.history)
folder once the task's folder has moved there.

Everything a session's node receives is written before the move. Removing the sessions afterwards
only reads the history.

### req.task-session.node-finished — A task session's node receives its figures from Claude Code

When a task ends, Task sessions SHALL write the following into each task session's
[trace node](../../glossary.json#concept.trace-node) before the task's folder moves to the
[history](../../glossary.json#concept.history):

- The session's full session id, when Claude Code told it at the start or tells it now.
- Its status from Claude Code's state of the session.
- When its transcript was kept, its usage and its end from that transcript, with the number of the
  transcript's unreadable lines.
- When its transcript was kept, its cost, taken only from Claude Code's own account in the
  transcript and left null without one.

The figures are written into the node, not computed when a trace is read, because retention later
removes the transcript they come from while the node stays. When Claude Code does not report a state
as `done` or `failed`, the status is `unknown`. A value Claude Code never told stays null, as the
[session trace](contracts.md#contract.task-session.session-trace) says. The usage counts only the
transcript's records. The count of unreadable lines tells a reader after retention that the figures
leave some lines out.

### req.task-session.removed — An ended task leaves no task session in Claude's session list

Once a task has ended, by any outcome, Task sessions SHALL remove each of its task sessions whose
transcript it kept from Claude's session list with `claude rm`, as a best effort whose failure
leaves the close as it succeeded.

A session whose transcript was kept with unreadable lines is removed all the same, since its node
keeps every line. When a session's transcript was not kept or `claude rm` failed, the close's
warnings name each session not removed, with these details:

- The whole reason.
- The command that removes it by hand.

A task session matters to the developer only through the
[main agent](../../glossary.json#concept.main-agent), so an ended one is noise in that list.
