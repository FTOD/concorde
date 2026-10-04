# Task sessions

## Purpose

Task sessions is how the [main agent](../../glossary.json#concept.main-agent) delegates the task
level of the work. Task sessions starts a task session for every task. This background session of
the main agent's own program works inside that task's worktree while the main agent stays in the
primary worktree. For now that program is Claude Code, the only one a main agent runs on. The
[workers](../../glossary.json#concept.worker) of the runs a task session starts may run on pi. Task
sessions manages those sessions:

- It starts them.
- It confines them.
- It ends them.

The main agent relies on Task sessions to have every task worked, one or several at once. Each
session works under a boundary that keeps its writes inside its task. Task sessions does not decide
how work is split. It never merges a task into the primary branch or closes it. It does not tell a
session how to work in a task. That method is the main agent's own, given by the
[Main session](../main-session/module.md) guidance. The session follows the method at a smaller
scale. Its boundary guards against mistakes, not a malicious session.

Task sessions matter to the developer only through the main agent. The developer talks to main
sessions. Once its task ends, a task session, a means of the main agent, has served its purpose. So
Task sessions also ends task sessions with their task. When a task is closed without a merge, Task
sessions first stops any task session still running. Once a task ends, Task sessions removes each of
its task sessions from Claude's session list after keeping its transcript in the task's trace. The
trace moves to the history with the task. Otherwise, finished task sessions would pile up beside the
developer's main sessions in Claude's session list.

## Core concepts

A **[task session](../../glossary.json#concept.task-session)**, a term of the root, is not a level
of its own but the task level delegated. The main agent delegates every task. Keeping the main agent
out of task worktrees has these effects:

- It keeps the main agent free to talk with the developer while tasks run.
- It keeps the main agent free to answer every session while tasks run.
- It puts every task under a write boundary, which the main agent itself does not have.

A task session escalates to the main agent while the main agent escalates to the developer. A task
session has a start and ends with its task. It never merges its task into the primary branch. After
a merge conflict or a `concorde update`, when the main agent asks, the task session merges the
primary branch into its task branch. This is the one merge the task session makes, a change inside
its own worktree and branch. Because it does the main agent's own task-level work at a smaller
scale, a task session runs on the main agent's own program and configuration. An isolated
configuration, such as a worker gets, would give the task session other tools and instructions than
the main agent's.

Its **[session boundary](../../glossary.json#concept.session-boundary)**, this Module's own, is the
Claude Code settings and hook that keep its own file-writing tools inside its task. That is its one
restriction. Everything else of the session, its shell included, is as open as the main agent's.
[The session boundary](#the-session-boundary) explains it.

## Overview

### A task session's life

The task level of the work is always delegated. The main agent never works inside a task worktree.
The main agent starts a [task session](../../glossary.json#concept.task-session) for every task,
even a single one, from the primary worktree. Before starting the session, the main agent records
the [task brief](../../glossary.json#concept.task-brief) in its
[decision log](../../glossary.json#concept.decision-log). A task session travels over time from the
main agent's start to the end of its task:

```d2 illustrative
grid-columns: 4
horizontal-gap: 110
main: "Main agent\nlevel 1, primary worktree" {
  grid-columns: 1
  vertical-gap: 50
  start: "concorde task session\n<task> --main <session>"
  g1: "" {style.opacity: 0}
  g2: "" {style.opacity: 0}
  g3: "" {style.opacity: 0}
  answer: "Read the report,\nanswer every escalation\nat once"
  end: "concorde task merge\nor task close"
}
tasks: Tasks {
  grid-columns: 1
  vertical-gap: 50
  check: "Check the primary\nworktree, the task\nand the options"
  g1: "" {style.opacity: 0}
  g2: "" {style.opacity: 0}
  record: "Record the session\nin the task's trace"
  g3: "" {style.opacity: 0}
  close: "Close the task"
}
starter: "Session starter" {
  grid-columns: 1
  vertical-gap: 50
  g1: "" {style.opacity: 0}
  boundary: "Write the session\nboundary and the\nMCP configuration"
  launch: "claude --bg: guidance,\ngoal, Modules,\ndecision log"
  g2: "" {style.opacity: 0}
  g3: "" {style.opacity: 0}
  stop: "Stop its sessions,\nkeep their transcripts,\nremove them"
}
session: "Task session\nlevel 2, task worktree" {
  grid-columns: 1
  vertical-gap: 50
  g1: "" {style.opacity: 0}
  g2: "" {style.opacity: 0}
  work: "Work the task:\nworkflows, Operations,\ndelivery"
  g3: "" {style.opacity: 0}
  report: "SendMessage: delivered,\nor every escalation"
  g4: "" {style.opacity: 0}
}
main.start -> tasks.check
tasks.check -> starter.boundary: checks passed
starter.boundary -> starter.launch
starter.launch -> session.work: starts
starter.launch -> tasks.record
session.work -> session.report
session.report <-> main.answer: "the report,\nevery answer"
main.answer -> main.end: delivered
main.end -> tasks.close
tasks.close -> starter.stop
```

The main agent starts the session through `concorde task session`. Tasks checks the start before
handing it here. Task sessions performs these steps:

- It writes the session's boundary.
- It starts the session in the task worktree with its first prompt.
- It records the session in the task's [trace](../../glossary.json#concept.trace), naming the main
  agent's session in the [task record](../../glossary.json#concept.task-record).

The session then works the task following its guidance and reports to the main agent. It records its
delivery, or every decision it needs, with `concorde task report`. Then it wakes the main agent with
SendMessage to the session the record names at that moment. The main agent answers together the same
way. When the main agent merges or closes the task, Tasks' close has Task sessions do the following:

- If the task ends without a merge, stop the task's sessions.
- Keep the task sessions' transcripts.
- Remove the task sessions from Claude's session list.

### Its place in the levels of work

A task session plays level 2 of Concorde's [levels of work](../../module.md#the-levels-of-work), the
task level, in place of the main agent. Only the main agent at level 1 calls this
[Module](../../glossary.json#concept.module), with `concorde task session` from the primary
worktree. The call arrives through Tasks. Before handing the call here, Tasks' command line checks
the task and the options. Task sessions then starts one agent session in the task worktree. That
session, not this Module, does the task's work. Following its guidance, the session does the
following inside its task worktree:

- It changes Specs and code.
- It starts workflows (level 3).
- It runs Operations and [execution commands](../../glossary.json#concept.execution-command) (level
  4).

The session never reaches a worker except through an Operation. Its results go up to level 1 only,
never to the developer. The session reports to the main agent with SendMessage. What the session may
not decide, it escalates with `concorde task escalate --by task-session`. The escalation is a link
of level `task-session` on top of the failed runs' chains. The escalation is for the main agent to
decide or to pass on with its own link.

```d2 illustrative
main: Main session
module: Task sessions
tasksession: "Task session (agent, level 2)"
workflows: Workflows
runs: "Runs: Operations and execution commands"
workers: Workers
main -> module: starts
module -> tasksession: starts in its task worktree
tasksession -> workflows: starts in its task worktree
tasksession -> runs: starts in its task worktree
workflows -> runs: runs one at a time
runs -> workers: an Operation launches
```

## Starting a session

```text
concorde task session severity --main concorde-7d
```

The command belongs to the `concorde task` family, which [Tasks](../tasks/module.md) runs. Its
command line checks that it runs in the primary worktree and checks the options. Task sessions does
the rest. What Task sessions writes for a session goes into the task's folder of the primary
worktree:

- The session's boundary configuration goes under `runtime/`, which the close removes with the
  folder.
- The session's [trace node](../../glossary.json#concept.trace-node) goes under
  `sessions/<session>/`. Tasks' updates write the node so the task's
  [trace](../../glossary.json#concept.trace) holds every session.

Task sessions writes the session's [session boundary](../../glossary.json#concept.session-boundary)
under `.concorde/tasks/severity/runtime/`. The boundary comprises a settings file and its own
task-session hook with the task's paths embedded. Task sessions writes an MCP configuration
`mcp.json` there that gives the session the
[project MCP server](../../glossary.json#concept.project-mcp-server). Task sessions starts
`claude --bg` in the task worktree with that configuration. Its first prompt contains:

- The task-session guidance.
- The task's goal.
- The task's Modules.
- The task's decision log.
- The main agent's session name.

Task sessions records the started session as a node `sessions/<id>/` of the task's trace. The short
id `claude --bg` reported names the node. Since Concorde does not see a Claude Code session end, the
node has status `unknown` until its task ends. Task sessions has Tasks name the `--main` session as
the task's main in its record.

The first prompt gives that name too, but only as the main agent's session when the task session
started. A Claude Code session's name does not survive a restart or resume of that session. So
whenever the task session reports, it takes the name to message from the record. Once the main
agent's name changed, the main agent rebinds the record with `concorde task rebind`
([Tasks](../tasks/module.md#reports-and-the-main-agents-session)).

Task sessions also asks Claude Code for the session's full session id, the name of its transcript,
with `claude agents --json --all`. The entry of that short id gives the full id as `sessionId`. Task
sessions records the full id in the node. When Claude Code does not tell it then, the node records
none and the task's end asks again.

`--main` is required. A start without it is refused with `invalid_input`. `--dry-run` writes the
boundary and prints the command without starting anything. The following cases cause refusal with
Claude Code's output in the detail:

- A task that is closed or failed (`task_closed`).
- A missing worktree (`missing_worktree`).
- A Claude Code that does not report a started background session (`session_failed`).

The session receives the main agent's answers through SendMessage. Once `concorde task report`
recorded the session's reports, the session sends them the same way. `claude stop` stops the
session.

The server is passed explicitly, as the running Python with the running package. So a task session
has the server whatever the project's `.mcp.json` holds and whoever approved it. The server comes
without a channel, and its configuration says so (`CONCORDE_CHANNEL=0`). Claude Code does not wake a
background session with channel events.

A probe on 2026-09-29 (Claude Code 2.1.284) started a `claude --bg` session with
`--dangerously-load-development-channels server:concorde`. The server loaded and registered a wait
on a held [merge lock](../../glossary.json#concept.merge-lock). When the lock was released, the idle
session was never woken. So `register_wait` answers a task session with the `concorde task wait`
command. The task session runs that command in background Bash. When the command returns, it wakes
the task session.

The server runs as every MCP server does, as a process of the session beside its tools. Its tools
may change any task's record. The developer accepted that a task session can reach the task
management tools, which are no boundary. So the guidance, not the boundary, keeps a task session
from merging or closing its task. The server's `workflow_step` starts the runs of the session's
workflows from there ([below](#workflow-runs-through-the-server)).

<a id="project-mcp-approvals"></a>

Nobody answers Claude Code's dialog "New MCP server found in this project" in a background session
either. In a trusted project, a `claude --bg` session shows the dialog for each server of the
project's `.mcp.json` that nobody approved. The session waits on the dialog for ever, even for the
entry `concorde` that `--mcp-config` passes as well. This was seen with Claude Code 2.1.285 on
2026-10-01. So the session's settings answer the dialog beforehand, server by server, from what
Claude Code itself would read:

- The servers are those of every `.mcp.json` Claude Code loads for a session in the task worktree.
  Claude Code loads that of each folder from the task worktree up to, but not including, the
  filesystem root. When the task worktree lies inside the primary worktree, Claude Code includes the
  primary worktree's file. A file names no server in any of these cases:

  - The file is missing.
  - The file is unreadable.
  - The file has no `mcpServers` object.

Since Claude Code loads no server from such a file, it asks about none. The session starts all the
same.
- The entry `concorde` is disabled (`disabledMcpjsonServers`). The `--mcp-config` server replaces
  it. With both, Claude Code loads only the latter, so nothing is lost.
- When the primary worktree approved any other server, that server is enabled
  (`enabledMcpjsonServers`). Otherwise, the server is disabled, as the dialog's "Continue without
  using this MCP server" would.

When any settings source lists a server in `disabledMcpjsonServers`, Claude Code 2.1.285 judges the
server rejected. Otherwise, Claude Code judges the server approved when any source lists it in
`enabledMcpjsonServers` or sets `enableAllProjectMcpServers`. When comparing names, Claude Code
leaves these characters unchanged:

- Letters.
- Digits.
- `_`.
- `-`.

When comparing names, Claude Code reads every other character as `_`.

Task sessions judges the same way over every source that records such an approval for the primary
worktree or the task worktree:

- The user's settings.
- Both worktrees' `.claude/settings.json` and `.claude/settings.local.json`.
- The managed settings with their drop-ins.
- The primary worktree's entry in Claude Code's global configuration. When Claude Code next starts
  there, it moves that entry's approvals into the local settings.

A source that is missing or unreadable approves nothing.

The dialog records its answer in the local settings of the folder it was shown in. These settings
only reach the session through `--settings`, so they change no approval anywhere else.

## The session boundary

<a id="concept.session-boundary"></a>

A task session is restricted in one thing: it changes nothing outside its task worktree. Its
**[session boundary](../../glossary.json#concept.session-boundary)** holds its file tools to that.
The boundary is a Claude Code settings file with a PreToolUse hook of its own on these tools:

- Edit
- Write
- MultiEdit
- NotebookEdit

The hook lets these tools change the task worktree and the task's
[decision log](../../glossary.json#concept.decision-log). It denies every other path, an
[Issue](../../glossary.json#concept.issue) record among them, with a reason naming the task
worktree. Since Edit and Write write through a symbolic link, the hook judges the link by the file
it points to. A link in the task worktree to a file outside it is denied like that file. Once the
task is closed, its folder is in the [history](../../glossary.json#concept.history). At that point,
the decision log's folder no longer exists. The hook then refuses every write to the decision log
rather than recreate its folder. Where the issues part is installed, the session writes Issues
through the Issue command or the Issue tools, as the runs it starts do.

The boundary is Coordination's own. A worker's harness belongs to the worker harness, with these
components:

- Its grant
- Its [deny rules](../../glossary.json#concept.deny-rules)
- Its sandbox

Since the coordination part installs without the worker harness, the two share no code.
[The contracts](contracts.md#task-session-settings) give the settings exactly. Nothing else of the
session is restricted. Its commands run under no operating-system sandbox. These are all open to its
commands:

- Every path
- Every process
- Every socket
- Every home-state file
- Every network host

With these open, the session does the following:

- It prepares its own worktree, including:

  - Dependencies
  - Submodules
  - Build outputs

- It probes the machine it runs on.
- It starts the runs of its task as the main agent starts its own.

The session boundary guards against mistakes, not a malicious session. A task session is the main
agent's own role at a smaller scale: the main agent works under no boundary at all. After the
shell's sandbox cost fourteen problems in one week, the developer decided it away. Only four
problems were answered by changing a rule. The rest were answered by a workaround that moved work to
the main agent or into the project MCP server. The problems were:

- A PID namespace per Bash call that killed every
  [detached run](../../glossary.json#concept.detached-run)
- A network namespace reached only through a proxy
- Unix sockets blocked by seccomp, which broke the nested sandbox of every pi worker a session
  started
- Protected paths such as `.git/config` that no setting could open
- Placeholder files the host saw
- Only paths existing at the start made writable

These keep the shell inside the task now:

- The task-session [guidance](../../glossary.json#concept.main-session-guidance)
- Claude Code's `auto` mode
- At the end, the audit `concorde task merge` runs over what lies outside the task worktree
  ([Tasks](../tasks/module.md#nothing-changed-outside-the-task))

When the primary worktree, or the worktree of a task that ended, holds changes nobody accounts for,
the merge is refused. The task's own merge refuses an uncommitted change in its worktree, so it
catches what another session wrote there too.

Since nobody answers permission prompts in a background session, the session runs in Claude Code's
`auto` mode. A classifier approves or refuses each action instead of asking. This is the only check
between the guidance and the session's shell. `bypassPermissions` would skip that check. Only after
the developer accepted a disclaimer once does Claude Code start a background session in that mode. A
model without `auto` mode would fall back to asking and stall, so `--model` must name one that has
it. Reads are open because the session needs the whole project's context.

The boundary's hook guards Edit and Write only. Tools that MCP servers add are outside that hook,
and so are the server's own writes. The
[project MCP server](../../glossary.json#concept.project-mcp-server)'s task tools can change any
task's record and take any lock. The developer accepted this for these reasons:

- The server is a management tool.
- The guidance, not the boundary, says what a task session does with the server.

A run's [write audit](../../glossary.json#concept.write-audit) attributes every change of the
worktree to the run's workers. For this reason, while a run of the worktree runs, the guidance has
the session edit and commit nothing in that worktree. A run of the session's own, started in
background Bash, lives as long as that background call. The session starts such a run with:

- `concorde run`
- `task-validation`
- `delivery`

For this reason, before `task-validation` and `delivery`, the guidance has the session let its runs
finish and stop every other background command. A run that still runs holds the
[workspace lock](../../glossary.json#concept.workspace-lock), which refuses both. `delivery` commits
every uncommitted change, so a command still writing in the worktree would decide what the
[delivery commit](../../glossary.json#concept.delivery-commit) holds.

<a id="workflow-runs-through-the-server"></a>

**A task session's workflow runs start from the project MCP server.** Where the workflow part is
installed, the [step agents](../../glossary.json#concept.step-agent) of the session's
[workflows](../../glossary.json#concept.workflow) start and await every step through that server's
`workflow_step`. This runs the task worktree's own `concorde workflow step` as a process of the
server ([Workflows](../../workflows/module.md#steps-in-claude-code)). A
[workflow step](../../glossary.json#concept.workflow-step) may outlast many relays. A run started
there depends on neither of these:

- A relaying agent's turn
- A background command Claude Code ends after two hours or when the session is stopped

Concorde's own bounds apply to those runs, as they do to the main agent's:

- The runner works only on the bound workspace of the session's own task worktree, with its trace
  and locks. For `delivery`, the runner commits only on the task branch.
- Each worker keeps its [grant](../../glossary.json#concept.grant) and its own boundary.
- Each [configured check](../../glossary.json#concept.configured-check) runs in the
  [read-only check boundary](../../glossary.json#concept.read-only-check-boundary).

This path rests on the task-session guidance, as `task_merge` and `task_escalate` of the same server
do. The guidance has a task session start its workflows as the installed workflows. The guidance has
the session use the server's tools only as they are meant for.

## When the task ends

<a id="ending-claude-sessions"></a>

Tasks' close hands its task sessions, every one the task's trace lists, to Task sessions at three
points:

- A close without a merge (`--completed` or `--failed`) first runs `claude stop <id>` for each. This
  ensures no session goes on working in the worktree the close removes or starts another run there.
  A session already ended or no longer known to Claude Code (`No job matching`) counts as stopped.
  When a stop cannot be confirmed, the close is refused with `session_stop_failed` before it changes
  the task. The refusal names:

  - The session
  - Claude Code's answer
  - The command to stop it by hand

- Every close, a merge's included, finishes each session's trace node just before the task's folder
  moves to the history. It asks Claude Code once, with `claude agents --json --all`, for every
  session it still lists. When the node does not record the full session id yet, the close takes
  that id from the session's entry. The close also takes the session's working directory and state
  from that entry. It opens the transcript by that exact id:
  `projects/<the working directory, every character that is no letter or digit as ->/<session id>.jsonl`
  of Claude Code's configuration folder (`$CLAUDE_CONFIG_DIR`, by default `~/.claude`). Otherwise,
  it opens the file of that name in any project folder. When Claude Code does not tell a session's
  id, a warning names the session. When the transcript is in neither place, a warning also names the
  session. In either case, the warning says what was asked and where the close looked. The
  transcript becomes `transcript.jsonl`, an artifact of the node. The folder Claude Code keeps
  beside it, with subagent transcripts and long tool results, becomes `transcript/`. From these
  records the node receives what the session consumed and when it ended
  ([below](#finishing-a-session-node)). The history thus keeps each session's conversation and its
  figures. The history is never written after the move.
- Once the task is closed, `claude rm <id>` removes each session whose transcript was kept from
  Claude's session list. It kills a session that still runs and deletes Claude Code's own state of
  the job. Only when Claude Code created a worktree for the session does the removal remove that
  worktree. It never removes the task worktree a task session is started in. The removal is best
  effort. A failing `claude rm` never fails the close. A transcript that could not be kept never
  fails the close either. In that case, the session is left in the list so nothing of it is lost.
  The close's `warnings` name:

  - The session
  - The whole reason
  - The command that removes it by hand

### Finishing a session node

When a task session starts, its node is written. Concorde sees nothing of the session until its task
ends. Its figures then come from Claude Code's own records, as
[Tracing](../../kernel/tracing/requirements.md#req.tracing.reported-usage) requires. The figures are
written into the node because retention later removes the transcript:

- **usage**: the following tokens, summed over the `assistant` records of the transcript and of the
  subagent transcripts beside it:

  - Tokens read.
  - Tokens written.
  - Tokens read from the prompt cache.
  - Tokens written to the prompt cache.

Each API message is counted by its `message.id` once, since one message may span several records.
The turns are those messages. The duration runs from the earliest time the transcript's records
carry to the latest. Claude Code's own cost account is the `totalCostUSD` of the transcript's last
`cost-state` record. When that record exists and no `assistant` record follows it, the cost is that
account. Otherwise, the cost is null. A background session's transcript often has no such record.
Concorde computes no price.
- **end**: when a transcript was kept, the latest time the transcript's records carry.
- **status**: from the session's state in `claude agents --json --all`, as follows:

  - `ok` for `done`, a session waiting for its next message.
  - `failed` for `failed`.
  - `unknown` for any other state or when Claude Code no longer lists the session.

The state itself is the node's outcome.
- **content**: the following:

  - The full session id.
  - Claude Code's state.
  - The tokens and messages of each model.
  - When there is one, the `modelUsage` of that `cost-state` record, per model with its cost.

When Claude Code tells them, a session whose transcript was not kept still receives its session id
and status. Its usage stays null. Claude Code judges a session's state by whether its process lives.
Thus, a state read while a session still works says nothing about how it ended. For this reason,
Concorde takes the state only at the close, when the task has ended.

## Escalating

A task session escalates what it may not decide with `concorde task escalate --by task-session`.
Tasks records this as a link of level `task-session` on top of the failed runs' chains. When the
developer must decide, the main agent adds its own link above it. A task never asks the developer in
place. The session handles every decision it needs as follows:

- It gathers every decision.
- It records each decision as an escalation.
- It reports the decisions together, in one report and one SendMessage.

`concorde task report` records that report with the escalations it carries. The main agent answers
the decisions together. When that message reaches no session because the main agent's session was
restarted under another name, the report stays recorded. In that case, the session waits in
background Bash with `concorde task wait <task> --rebound <name>` until the main agent has rebound
the task. Then the session sends the report again to the new name. The following documents give the
details:

- Exact commands and error codes are in the [contracts](contracts.md).
- The obligations are in the [requirements](requirements.md).
- The behaviour is in the [scenarios](scenarios.md).

## What the started session relies on

These collaborations are the started session's, which follows its guidance. Task sessions itself
starts no workflow or run and owes them nothing. Each collaboration is an
[optional integration](../../glossary.json#concept.optional-integration). The guidance a session
starts with holds the sections of the parts installed, so a session never reaches for a part the
project does not have.

<a id="uses-workflows"></a>

Where the workflow part is installed, **Workflows** is level 3. When the work follows a known
procedure, a task session may start this level for its task. The session starts a
[workflow](../../glossary.json#concept.workflow) for its own task only. It uses the
[mode](../../glossary.json#concept.workflow-mode) its task brief names. When the task brief names no
mode, the session uses interactive mode. An interactive workflow ends at its first
[decision point](../../glossary.json#concept.decision-point) not yet settled. Since nobody answers
the session in place, the session escalates every pending point of that step at once, with the
workflow result as the cause. The session starts the workflow again with the main agent's answers. A
no-ask workflow decides those points itself. It reports every decision at the end. The session's
workflow steps start through the project MCP server
([The session boundary](#workflow-runs-through-the-server)). The session relies on the
[workflow result](../../glossary.json#concept.workflow-result) listing those decisions and keeping
every step's [error chain](../../glossary.json#concept.error-chain) whole. The session copies the
decisions and problems into the task's [decision log](../../glossary.json#concept.decision-log). It
gives the decisions in its own report. It escalates to the main agent what needs the developer:

- A result that is not `ok` and that the session cannot repair within the task, with the session's
  own link above the result's chain.
- A decision of major impact a no-ask workflow took, which carries no error, with the session's own
  link alone.

The workflow never merges or closes the task. Merging and closing it stay the main agent's.

<a id="uses-execution"></a>

Where the execution part is installed, **Execution** is level 4. Whenever no workflow fits, a task
session runs this level directly. It runs an [Operation](../../glossary.json#concept.operation) with
`concorde run`. Where the method part is installed, it may also run the execution commands
`concorde task-validation` and `concorde delivery`. It always runs these inside its task worktree
with the worktree's own `concorde`. When the task opened, Tasks wrote the worktree's
[workspace binding](../../glossary.json#concept.workspace-binding). Every run reads that binding, so
the run works on the task's goal and Modules without naming the task. Every run holds the workspace
lock, so two runs of one task never overlap. The session relies on each
[run result](../../glossary.json#concept.run-result) separating what the runner verified from what a
worker claimed. The session either repairs a failed result within the task, by a changed
[Spec](../../glossary.json#concept.spec) or code and a new run, or escalates it. An escalation keeps
the result's chain unchanged beneath the session's link. The session reaches a worker only through
an Operation. It never starts a worker or another agent itself. Where the method part is not
installed, the session delivers with `concorde task deliver` instead
([Tasks](../tasks/module.md#delivering-without-method)), with the checks its task brief names. The
session prepares each worker's environment instead. A realization binds only files that exist. A
worker writes only bound files and new files inside bound directories. Because of these limits, the
session itself prepares any other new file the work needs as follows:

- It creates the file with the least content its format needs to be valid.
- It binds the file to its Module before it starts the run that fills the file
  ([req.main-session.task-session-prepares-workers](../main-session/requirements.md#req.main-session.task-session-prepares-workers)).

<a id="uses-operations"></a>

**Operations** provides the catalog of the Operations a task session may run in its task: those the
installed parts register. These are the same Operations the main agent would run, with the same
arguments.

## Inside and around it

```d2
tasksession: Task sessions {
  starter: Session starter {
    "session.py"
  }
}
```

<a id="realization.task-session.starter"></a>

The **session starter** (`session.py`) assembles the session's settings around the hook. The session
starter starts `claude --bg`. It also ends a task's task sessions when Tasks' close calls it:

- It stops the sessions.
- It copies their transcripts.
- It removes the sessions.

The task-session hook (`session_hook.py`) goes with the session starter. The session's settings
install the hook. The tests (`test_session.py` under `tests/concorde/tasks/`) run on real Git
repositories with a fake `claude`.

A start touches one piece of each provider and its own boundary. The session starter:

- Writes the session boundary.
- Prompts the session with the Main session's guidance.
- Records the session in the task's trace through Tasks.

```d2
starter: Session starter
guidance: Main session / Main-session guidance
boundary: Session boundary
task: Tasks / Task
starter -> guidance: prompts with
starter -> boundary: writes
starter -> task: records sessions in the trace of
```

<a id="uses-tasks"></a>

**Tasks** provides the [task](../../glossary.json#concept.task) a session works in:

- Its worktree.
- Its [record](../../glossary.json#concept.task-record).
- Its [decision log](../../glossary.json#concept.decision-log).

Tasks also provides the `concorde task` command. After checking that it runs in the primary
worktree, the command dispatches `session` here. Task sessions records a started session only
through Tasks' record updates. When Tasks refuses the update, it refuses the start.

<a id="uses-kernel"></a>

The **Kernel** gives Task sessions what a started session works within without depending on any
other part. This includes the [workspace binding](../../glossary.json#concept.workspace-binding)
Tasks wrote into the task worktree. Every run the session starts reads that binding. The Kernel also
gives Task sessions the [merge lock](../../glossary.json#concept.merge-lock) that every Issue write
and every merge takes. For that lock, a session waits with `concorde task wait --lock merge` rather
than polling.

<a id="uses-issues"></a>

Where the issues part is installed, **Issues** keeps the project's
[Issues](../../glossary.json#concept.issue) in the primary worktree's `.concorde/issues/`. Each
write holds the merge lock and commits its record alone on the primary branch. Task sessions relies
on an Issue record lying outside every task worktree, so that the session boundary refuses an Issue
record. Thus, a task session reaches Issues only through the Issue command or the Issue tools, as
the runs it starts do. Without the issues part there is no Issue to reach, and nothing changes for
the boundary.

<a id="uses-workers"></a>

Where the worker harness part is installed, **Workers** launches the
[workers](../../glossary.json#concept.worker) of the Operations a task session starts. Task sessions
relies on each worker's [worker backend](../../glossary.json#concept.worker-backend) coming from the
[worker configuration](../../glossary.json#concept.worker-configuration). Unless that configuration
chooses Claude Code, the backend is pi. The backend never comes from the program the task session
runs on.

<a id="uses-main-session"></a>

**Main session** provides the [guidance](../../glossary.json#concept.main-session-guidance) a task
session starts with. The task-session guidance carries the same rules for working inside a task that
the main agent follows. The sections the other installed parts contribute follow that task-session
guidance. Distribution composes this guidance into `generated/guidance/task-session.md` of the
Concorde package that runs. In a source checkout, the build composes every part. In a project's
Framework copy, the installer composes the installed parts. When the composition is missing, the
start is refused with `session_failed`. For every task session it starts, Task sessions also
configures the [project MCP server](../../glossary.json#concept.project-mcp-server) without a
channel (`CONCORDE_CHANNEL=0`). The server is Distribution's host of the tools the installed parts
register.

Two Modules call this one, both from level 1's side. The Main session's guidance has the main agent
start task sessions. After its own checks, Tasks dispatches `concorde task session` here. When Tasks
closes a task, it has the task's task sessions ended here. A task session records:

- Its start.
- Its reports.
- Its transcript and figures once its task ends.

The main agent learns what a task session did from its report. The report is recorded in the
task record and delivered by SendMessage. While its task is open, the main agent finds a session
that ended without a report with `claude agents` and `claude logs`.
