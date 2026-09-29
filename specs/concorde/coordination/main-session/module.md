# Main session

## Purpose

Main session is the top of Concorde's levels of work, level 1: the guidance that makes an ordinary
Claude Code or pi session in a project's primary worktree act as Concorde's
[main agent](../../glossary.json#concept.main-agent): discuss work with the developer, split it into
[tasks](../../glossary.json#concept.task), hand every task to a
[task session](../../glossary.json#concept.task-session) and answer it, keep each task's
[decision log](../../glossary.json#concept.decision-log), decide ordinary questions itself while
escalating only major ones, merge delivered tasks, and handle
[Issues](../../glossary.json#concept.issue). The method of working inside a task is part of this
guidance too, as the task-session guidance: the task level is the main agent's own work, which it
always delegates, and a task session starts with that method in the guidance it is given. It is
advice to a model, not enforcement — Concorde places no permission limits on the
main agent, and nothing here constrains the developer. In pi it adds a
[run view](../../glossary.json#concept.run-view), an extension that starts
[Operations](../../glossary.json#concept.operation) and
[execution commands](../../glossary.json#concept.execution-command) in the
background and shows their progress and that of every task session's round. Distribution renders and installs this
[Module](../../glossary.json#concept.module)'s content.

## Usage

<a id="concept.main-session-guidance"></a>

**What the main agent is told.** The installed guidance tells the Claude Code or pi session opened
in a Concorde project's primary worktree that it is the main agent, and gives it a working method:

- **Discuss first.** Agree the direction with the developer before changing anything.
- **Split into tasks.** Turn agreed work into [tasks](../../glossary.json#concept.task),
  opened with `concorde task`. Run tasks in parallel only across worktrees whose Modules and shared
  files do not overlap; run the rest one after another
  ([requirements](requirements.md#req.main-session.parallel-by-worktree)).
- **Hand every task to a task session.** Never work inside a task worktree: start one
  [task session](../../glossary.json#concept.task-session) per task with
  `concorde task session <task>`, even for a single task, and stay in the primary worktree, where
  the main agent discusses, opens and closes tasks, starts and answers task sessions, runs
  [unbound](../../glossary.json#concept.unbound-run) Operations, merges, reports, inspects Issues
  and changes the worker configuration. Before starting the session, record the task's brief in its
  decision log: the developer's decisions the task carries out, the workflow and mode when one
  applies, and what is left to the session; the session reads it first. A task session runs on the
  main agent's own program. In Claude Code the command names the main agent's session with
  `--main`, and the [session reports](../../glossary.json#concept.session-report) back with
  SendMessage; ending the task, by its merge or its close, stops its Claude Code task sessions and
  removes them from Claude's session list, keeping their transcripts in the task's
  [trace](../../glossary.json#concept.trace), so the main agent never removes them itself. In pi
  the main agent uses the `concorde_task_session` tool: each
  [session round](../../glossary.json#concept.session-round) ends with a report that wakes the main
  agent that started the task session, which starts the next round with the tool's `answer`. The task session changes Specs and
  code in the task worktree directly or by running
  [Operations](../../glossary.json#concept.operation) with `concorde run <operation> …` and the
  [execution commands](../../glossary.json#concept.execution-command) `concorde task-validation`
  and `concorde delivery`, reading each [run result](../../glossary.json#concept.run-result), and
  runs every `concorde` command that works on the task's workspace with the worktree's own copy;
  the commands that open, merge and close tasks and start task sessions run from the primary
  worktree. None of these names the task: the task worktree's
  [workspace binding](../../glossary.json#concept.workspace-binding), which `concorde task open`
  wrote, tells every run which goal, Modules, branch and base it works on, and one workspace runs
  one of them at a time (`workspace_busy` otherwise); in Claude Code a task session starts them in
  background Bash, and since a pi round ends only with its report, a pi task session runs them in
  the foreground within the round (see [Task sessions](../task-session/module.md)).
- **Make only approved small changes in the primary worktree.** A very small change, such as a
  typo, a one-line fix or a wording correction, may be made by the main agent directly in the
  primary worktree, but only after it said what it would change and why the change is small and the
  developer approved that specific change
  ([requirements](requirements.md#req.main-session.small-change)). Besides it, the primary
  worktree sees only housekeeping that regenerates derived files, such as the registry mirror, and
  the commit of the worker configuration alone.
- **Ask the developer from the main session only.** A task never asks the developer in place: a
  task session gathers every decision it needs and escalates them together to the main agent,
  which decides those its authority covers, puts the rest to the developer at once, and answers
  the session once with every answer
  ([requirements](requirements.md#req.main-session.batched-decisions)).
- **Keep the decision log.** Record every non-`ok` result of the task's runs and every
  unsupervised choice, with its reason, in the task's
  [decision log](../../glossary.json#concept.decision-log), including
  the decisions and problems of a workflow's report, which nothing else writes there.
- **Merge delivered work.** Merge, without asking the developer's authorization, a task branch
  that `delivery` committed, from the primary worktree with `concorde task merge`, never with
  `git merge`: it holds the [merge lock](../../glossary.json#concept.merge-lock) so merges of
  several main sessions never interleave, runs `concorde spec-validation` on the primary branch, or
  exactly the `--check` commands given, undoes a merge whose checks fail and closes the task.
  Retry a `merge_busy`, and a `workspace_busy` once the task's run ended; have the task's session
  resolve a conflict by merging the primary branch into its task branch and delivering again, the
  only merge a task session makes; handle a
  failed check as new work, never by discarding someone's change. Finish a merge that a
  `merge_incomplete` refusal names before anything else, with `concorde task merge <task> --resume`,
  or `--abort` when the merge commit is no longer the primary branch's head, and leave a
  `merge_diverged` primary branch to the developer. Act on every warning of `task merge` and
  `task close`: each names a decision log nobody wrote in, or a Claude Code task session whose
  transcript the close could not keep or that it could not remove, with the command that removes
  it by hand.
- **Report.** Close each piece of work with a short summary for the developer: what was merged,
  what was decided on the developer's behalf, and what is still open.
- **Use the project's terms.** Every session of the project starts with all the terms of its
  worktree's glossary: in Claude Code the Concorde block of `CLAUDE.md` imports the glossary file,
  which Claude Code loads at launch, and in pi Concorde's extension adds the terms, read afresh, to
  the system prompt of every prompt, in main and task sessions alike. The guidance tells the main
  agent and every task session to use each term exactly as defined, with the developer and in task
  goals, decision logs, escalations, commit messages and Specs; never to coin a synonym; and to
  raise a missing or no longer fitting definition instead of working around it, changing the
  glossary through a task. A SessionStart hook could not carry the terms: Claude Code cuts a hook's
  output at 10,000 characters, while a project's glossary is usually longer.

A representative flow, agreeing a payments retry limit, with who works where at each stage:

```d2 illustrative
direction: down
developer: Developer {
  ask: ask for a retry limit
  read: read the report
}
primary: Main agent in the primary worktree {
  agree: agree the limit with the developer
  open: "open a task for module.payments,\nrecord its brief"
  merge: merge the delivered task
  report: report the exponential back-off it chose
}
task: Task session in the task worktree {
  work: run specify, implement, test
  review: run code_review
  deliver: run task-validation, delivery
}
developer.ask -> primary.agree
primary.agree -> primary.open
primary.open -> task.work: start a task session
task.work -> task.review: read each run result
task.review -> task.deliver
task.deliver -> primary.merge: report the delivery
primary.merge -> primary.report
primary.report -> developer.read
```

<a id="concept.run-view"></a>

**The [run view](../../glossary.json#concept.run-view) in pi.** In Claude Code the main agent runs
its unbound Operations in background Bash and is woken when they exit, and a task session does the
same with the runs of its task. In pi the installed extension gives the same with more to watch. The `concorde_run`
tool takes an Operation or an execution command (`task-validation`, `delivery`, `scaffold`), the
task and further arguments, and starts `concorde run <operation> … --detach` or
`concorde <command> … --detach` in the task's worktree, found through the
[task record](../../glossary.json#concept.task-record), since a pi session cannot move into the task
worktree itself: the task worktree's own `concorde` runs there and reads its workspace binding, so
the command line never names the task. The runner then runs as a process of its own and writes
its output to `host.out` in the run's own [trace node](../../glossary.json#concept.trace-node); a
failure before any run exists, such as a malformed command line, comes back to the tool directly
with its error. Without a task it starts an
[unbound](../../glossary.json#concept.unbound-run) Operation in the session's own worktree; an
execution command without a task starts there too, and Execution refuses it with `binding_required`
in a worktree without a binding, a run refused at once whose result the tool returns (see below). A
task without a worktree is refused before anything starts. The tool returns at once with the run
identity. The extension follows every run of the project, Operation or recorded command, whoever
started it: the `concorde_run` tool, a command the main agent ran with bash, or another session,
a pi task session's included. It looks in the primary worktree's
[run store](../../glossary.json#concept.run-store), the workspace folders of the current tasks,
where every task worktree's binding records its runs, and `.concorde/unbound/`, for every run still
running when the session starts and every run started since, even one
that ended between two looks; a run that had already ended when the session started is only listed
by `/concorde` ([requirements](requirements.md#req.main-session.pi-run-follow)). It follows each
through its [run progress file](../../glossary.json#concept.run-progress-file) there and through
the [progress file](../../glossary.json#concept.progress-file) of the worker an
Operation launched, which lies in the run's own node; an execution command has no worker.
It shows each run as an external job in pi-subagents' FleetView — its workspace (or `unbound`) and
name, its step, the worker's round and latest tool call, and on its end `completed`, `stopped` or
`failed` for a result of `ok`, `blocked` or `failed`, with the result's summary; a run whose runner
process ended without finishing is shown `failed`. Runs are filed under the session's file, or
its identity when it is not persisted, the name pi-subagents gives the session. The session
**owns** only the runs its own `concorde_run` started and the rounds of the task sessions started
for it (see [Owners](#owners)), and only what it owns wakes it or is its **background work**: a
`bg_wait` call without an id waits for its own runs and rounds still running (with an id it matches
only subagent runs), and a main session run with `pi -p` waits for them before it exits, as
pi-subagents drains the work of every `pi -p` session. A run or round it only follows, started with
bash, by a task session or by another main session, is shown but never wakes it and is never its
work, so a `pi -p` session never waits for another session's runs. When a run the session owns
ends, the extension sends the main agent a message naming the run, its workspace and name, the
result's status and summary and the run result's file, followed, for a result that carries an
[error chain](../../glossary.json#concept.error-chain), by that whole chain as indented text: while the main agent is in a turn the message is steered into
that turn after its current tool calls, and otherwise it starts the next turn. A run that has
already finished when `concorde_run` finds it, such as one refused at once, is answered in the
tool's own result instead, and no message follows. `/concorde` lists the recent runs of both kinds.
The view only launches and observes: the
[Execution runner](../../glossary.json#concept.execution-runner) runs and records every run, so
closing pi never stops or changes one. Without pi-subagents the tool, the wake and `/concorde` still
work.

How the run view carries one run from its start, or from its discovery, to the message that wakes
the main agent:

```d2 illustrative
direction: down
tool: "concorde_run: an Operation or execution command, with or without a task"
worktree: "Find the task worktree through the task record"
refused: "Refused before anything starts, naming the task"
launch: "Start the worktree's own concorde with --detach\n(the session's own worktree without a task)"
elsewhere: "A run still running when the session started,\nor started since with bash or by another session"
store: "Find the run in the primary worktree's run store"
done: "Answered in the tool's own result; no message follows"
follow: "Follow its run progress file and, for an Operation,\nits worker's progress file"
fleet: "Show it in FleetView: workspace or unbound, name, step,\nworker round and latest tool call"
ended: "The run ends, or its runner is lost"
owned: "Owned by this session?" {shape: diamond}
shown: "Shown ended; nobody here is woken"
wake: "Message the main agent: status, summary, result file, error chain"
steer: "Steered into the current turn\nafter its tool calls"
next: "Starts the next turn"
tool -> worktree: with a task
tool -> launch: without a task
worktree -> refused: no worktree
worktree -> launch: worktree found
launch -> done: already finished, such as refused at once
launch -> follow: still running
elsewhere -> store
store -> follow
follow -> fleet: with pi-subagents
follow -> ended
ended -> owned
owned -> wake: "yes: started by its concorde_run"
owned -> shown: no
wake -> steer: in a turn
wake -> next: between turns
```

The view follows pi task sessions the same way. The `concorde_task_session` tool starts a task
session, answers it (`answer`, which starts the next round) or stops its running round (`stop`), by
running `concorde task session` from the primary worktree, and returns at once. Like `concorde_run`,
it takes an optional text argument (`answer`, `model`, or `concorde_run`'s `task`) that is empty or
only whitespace as absent, since a model may fill an optional field it means to leave out that way.
A start names the session with `--main`, so the task session's [trace node](../../glossary.json#concept.trace-node)
names it as the owner of every round of that task session. The extension reads each pi session's
status file `status.json` in the session's node `.concorde/tasks/<task>/sessions/<session>/` and
shows every running round as an external job — its task, round and the session's latest tool call —
and when a round the session owns ends it wakes the main agent with the outcome recorded in the
round's node `rounds/<n>/`: the report's summary, decisions and open points, the
[delivery commit](../../glossary.json#concept.delivery-commit), the numbers of the escalations to
read with `concorde task show`, or the failed round's error chain rendered. The round of another
main session's task session is shown and never wakes it; when the session answers such a session,
the tool's result names the owner, which alone will be woken. A main session that starts again finds
the running rounds from their status files. In a pi task
session itself, where `CONCORDE_TASK_SESSION` is set, the extension only adds the project's terms to
every prompt and marks the commands the session starts as started from pi; it starts, follows and
reports no runs or rounds.

<a id="owners"></a>

**Owners.** Several Claude Code and pi main sessions may work on one project at the same time,
and each sees every run and round of it, but a run or a
[session round](../../glossary.json#concept.session-round) wakes only its **owner**, and it has
never more than one:

| Work | Owner | How the owner is woken |
| --- | --- | --- |
| A run a main session starts in Claude Code, in background Bash | that session | Claude Code's own notification when the command ends |
| A run a pi main session starts with `concorde_run` | that session | the run view's message |
| Every round of a pi task session, whoever answered it | the main session its session's node names as its `main`, the one that started it | the run view's message |
| What a Claude Code task session reports | the session its `--main` names | the task session's SendMessage |
| A run a task session starts in its worktree | that task session, no main session | the task session's own wait; its owner hears of it in the task session's report |
| A run started by a command run by hand, a round of a pi task session started without `--main` | no main session | nobody is woken |

The owner is recorded where the owner's side keeps it, never by Execution, which knows nothing of
main sessions: a pi main session keeps the runs its `concorde_run` started, and each end it has
been given, as custom entries of its own session file, so a resumed session keeps owning its runs,
is given once the end of one that ended while it was closed, and is never given an end twice; the
owner of a task session's rounds is the `main` its session's trace node records. A main session that
does not own a run or round sees its state without being woken: a pi main session in its run view
and `/concorde`; a Claude Code main session, to which nothing is pushed, when it asks with
`concorde task show <task>`, which lists the task workspace's runs with their status and the
task's sessions with their owner and, for pi, each round's outcome
([requirements](requirements.md#req.main-session.single-owner)).

**Escalation policy.** A result that is not `ok`,
or a refused `concorde` command, carries an [error chain](../../glossary.json#concept.error-chain);
the guidance tells the main agent to read it in full, since the origin says what went wrong and each
link says why that level could not handle it. The main agent decides ordinary design uncertainty
itself — naming, internal structure, task order, a clarified re-run, splitting a task — and records
and reports the choice. It asks the developer first only for a decision with major impact: changing
what a Module promises to its users or the project's direction, contradicting an earlier developer
decision, discarding work or data, doing something an ordinary revert cannot undo, touching security
or credentials, or needing more resources than the developer set; in doubt it records its reasoning
and asks. A task never asks the developer in place: a task session escalates every decision it needs
together, and the main agent answers them together, asking the developer at once about all those
it may not decide. An escalation is never a summary: `concorde task escalate` adds its own link, with the
reason it may not decide, on top of the chain, records it in the task and prints it rendered for the
developer; a decision of major impact that no error carries is escalated as that link alone. The decision log and the escalation both belong to a task, so they cover the runs of a
task. An [unbound run](../../glossary.json#concept.unbound-run) belongs to none: when one is not
`ok`, the guidance tells the main agent to show the developer its whole chain as rendered, on the
command's standard error or in the pi run view's message, and, when the failure leads to work, to
open a task for that work and escalate there with the run's result file,
`--error-file .concorde/unbound/<run-id>/result.json`, since `--run` names only runs of the task's own
workspace ([requirements](requirements.md#req.main-session.unbound-failure)).

**[Worker](../../glossary.json#concept.worker) models.** Every worker runs only on what the
worktree's [worker configuration](../../glossary.json#concept.worker-configuration), the tracked
`.concorde/workers.json`, enables and chooses per [worker
id](../../glossary.json#concept.worker-id), never on the developer's own pi or Claude Code settings;
it runs on pi, whatever program the main agent runs on, unless the file chooses Claude Code for
it. No worker runs without the file, which the installer does not write: the guidance tells the
main agent, when the project has none, to ask the developer which models workers may use and which
is the default, and to write the file with its required enabled models and a default model and
commit it alone on the primary branch before any Operation runs
([requirements](requirements.md#req.main-session.worker-configuration-first)). It describes the
enabled models, each with an optional level of its own, the refusals of a model that is not
enabled and of a worker without a model, and which level a worker takes. The guidance tells the
main agent to change the file only when the developer asks, by editing the JSON directly and
preserving unrelated entries, adding every model it names to the enabled models; there is no
editor. It chooses Claude Code for a worker by setting that entry's
`backend` to `claude`; the chosen program must be installed when a worker launches, not when the
file is edited. A change meant for future tasks is committed alone directly on the primary branch,
the one change the main agent makes in the primary worktree, never while a merge is unfinished; a
task may change its own copy, which reaches the primary branch when the task merges
([requirements](requirements.md#req.main-session.model-change-method)). The separate
`scripts/available_models.py --backend pi|claude [--json]` supplies optional suggestions without
Git or inference API calls. Discovery does not gate custom/offline configuration or impose an extra
question flow when the developer already chose a model.

**Questions without a task.** The guidance
tells the main agent that `understand`, `survey`, `spec_review`, `spec_panel` and `code_review`
(with `--base`) also run [unbound](../../glossary.json#concept.unbound-run), in a worktree without a
workspace binding such as the primary worktree, on the Modules `--modules` names. Such a run works
on an [unbound checkout](../../glossary.json#concept.unbound-checkout) of that worktree's `HEAD`, so
a task merged there meanwhile does not disturb it and uncommitted changes are not examined; its
result has `workspace` null and names the examined commit as `commit`, an `--input` of such a run
must be unbound too, and they change no
[Spec](../../glossary.json#concept.spec) or code, since an unbound run launches only reading
workers. It uses them for a question or a review that does not justify a task, such as understanding
a Module before a change is agreed. In pi `concorde_run` takes the task as optional for them.

**Workflows.** For a task that follows a known procedure the guidance tells the main agent to have
its [workflow](../../glossary.json#concept.workflow) run instead of sequencing the runs by hand:
open the task and name in its brief the workflow, its Module and its
[mode](../../glossary.json#concept.workflow-mode); the task session starts the workflow inside the
task worktree, since like every run it works on the workspace of the worktree it starts in and
never names the task. In Claude Code the task session runs the installed `/concorde-<name>`
workflow; in pi it starts the installed script through pi-subagents with the task worktree as
working directory. The main agent asks the developer which mode to use unless the developer
already said; interactive suits a developer who wants to settle the decision points, no-ask one
who wants the result later. A task session runs the workflow in the mode its brief names, and in
interactive mode when the brief names none
([requirements](requirements.md#req.main-session.task-session-workflow)). When the workflow ends
`awaiting_decision`, the session escalates every pending
[decision point](../../glossary.json#concept.decision-point) at once, with the
[workflow result](../../glossary.json#concept.workflow-result) as `--error-file`, whose chain names
each point with its options and recommendation; the main agent decides those its authority covers,
puts the rest to the developer at once and answers the session with every answer, and the session
starts the same workflow again with its `answers` keyed by each step's base key, its
[step key](../../glossary.json#concept.step-key) without a restart label or answer digest, each key
holding every answer given for that step so far, not only the newest
([Workflows](../../execution/workflows/module.md) defines the arguments). The session reads the
workflow result from the file Workflows saves in the workflow's node beside the workspace's
[workflow record](../../glossary.json#concept.workflow-record), in the task's workspace folder, and
treats it like a
run result: it copies the result's decisions and problems into the task's decision log, since
Workflows keeps its record apart from the task and in no-ask mode those are decisions taken
without the developer, gives the decisions in its own report and escalates a result that is not
`ok` with the report as `--error-file` and a decision of major impact with its own link alone. The
main agent reads every problem's chain and merges a delivered task. The guidance names the
[brownfield workflow](../../glossary.json#concept.brownfield-workflow) as the way to describe a
project whose code came before its Specs, right after installation and initialization, and
nowhere else, in a task opened for the root Module, or for a created Module to split further.

### Issues

The main agent decides whether a concrete problem deserves an
[Issue](../../glossary.json#concept.issue), typically when the current task will not fix
it. A worker finding or an Operation error is input to that decision; neither records an Issue
automatically. The guidance tells the main agent to inspect `concorde issues list` and
`show <id>` first, including closed matches, then create or append a report through the
bookkeeping command. It keeps the receipt for follow-up; repeating a creation command would
create another Issue. Inspecting Issues is explicit, with no automatic notification to sessions.

Run every writing command (`report`, `close`, `reopen`) in a task worktree, through the task
session working that task, which the main agent tells so in the task's brief or its answer, and
pass that task's identity to `report --task`. If no task exists, open one for the owning Module, or the root Module
when the owner is unknown. `--task` supplies provenance, not routing; the working directory or
explicit root selects the Issue files. The command still accepts reports without a task; this
workflow is a rule of the guidance. Read-only `list`, `show` and `check` may run in either
worktree and describe its local records. The main agent works through the store's command rather
than editing report contents or flipping `status` in a file.

An Issue stays open while a task investigates or fixes it. Solve it by ordinary Operations on its
current owning Module, then `close --reason resolved` on that task's branch with a note and the
fix's evidence before delivery, so the closure merges with the fix. Other closing reasons are
`duplicate` (naming another open Issue) and `not-actionable`; recurrence uses `reopen`, preserving
history. Each disposition needs evidence whose meaning the main agent checks itself. Appending a
report to an open Issue uses the revision from `show`; closing and reopening read their own
current revisions. On `stale_issue`, read the record again before deciding to retry. See the
Issues [lifecycle](../../issues/module.md#lifecycle) for the complete state model.

Before ending a task without merging it, preserve follow-up information for every Issue worth
keeping. Either record it through the command in a subsequent task, keeping its earlier identity
and branch as references in the report, or append a handoff to the current task's decision log:
Issue identity, branch and commit when available, what remains to be done, and durable locations
of the report and evidence. Preserve uncommitted material needed for the handoff before allowing
worktree removal. Tasks keeps the branch and decision log after closing; committed Issue changes
survive there, but the primary branch's list still shows only what has been merged. A log entry
is a handoff, not a published Issue or an automatic transfer.

If Git reports a conflict in an Issue record, the task session resolves it in the task worktree
while merging the primary branch into it, as the main agent's answer tells it. Preserve accepted reports unchanged and document how competing
dispositions are reconciled, retaining their evidence. Do not concatenate incompatible closes or
invent a reopening just to satisfy the state rules. Run `concorde issues check` explicitly on the
resolved records before `task-validation` and `delivery`; structural Spec validation alone does not
run the store check. If the meaning of a competing decision cannot be settled within the task's
scope, escalate it under the ordinary escalation policy.

### Develop installs

In a [develop install](../../glossary.json#concept.develop-install), where the developer also
changes the Concorde the project runs, the installed skill and `CLAUDE.md` block end with
[Dogfooding](../../dogfooding/module.md)'s own section: watch Concorde's runs, never change Concorde
from the project, and report [Concorde defects](../../glossary.json#concept.concorde-defect) to the
[Concorde repository](../../glossary.json#concept.concorde-repository). Everything above holds
unchanged; a normal install carries no such section.

### Spec queries

The main agent may configure the Spec MCP server for
its own session, to ask which Modules exist, what a Module's context is, or what grant a
[task type](../../glossary.json#concept.task-type) gives. The server answers from the Specs of the
worktree it is rooted in — the primary worktree for the main agent — and workers never receive it.

## Design

The guidance is instructions, not a program, because the main agent's work is judgment. Everything
that must hold regardless of judgment is enforced elsewhere — workers by the Harness, Operations by
their own checks, readiness by `task-validation` and `delivery` — so an agent that ignores the
guidance wastes effort but cannot widen a worker's boundary.

### Its place in the levels of work

The main session is level 1 of Concorde's [levels of work](../../module.md#the-levels-of-work), the
top of Coordination. Nothing in Concorde calls it: the developer talks to it, and the installed
skill and `CLAUDE.md` block are Concorde's only way to reach a session at all. It calls only
downward. At level 2 it opens a task and delegates it to a task session; from inside the task,
the task session starts workflows (level 3) and runs (level 4), Operations and execution
commands, in the task worktree; the main agent itself starts only unbound runs, in the primary
worktree, and it reaches workers (level 5) only through an Operation, touching Workers otherwise
only to watch a run and to edit the worker configuration. What comes back up is structured: run results, workflow results, and task-session reports
and escalations, each failure carrying its
[error chain](../../glossary.json#concept.error-chain). The chain ends here: the main agent
decides what the escalation policy lets it decide, records and reports it, and otherwise adds its
own `main-agent` link and asks the developer, the chain's last receiver.

What the main agent reaches, down the levels. Workers appear only under Operations, because an
Operation is the only way the main agent reaches one:

```d2 illustrative
mainsession: Main session
tasks: Tasks
tasksession: Task sessions
workflows: Workflows
runs: "Runs: Operations and execution commands"
workers: Workers
mainsession -> tasks: opens, merges, closes
mainsession -> tasksession: delegates a task to
mainsession -> runs: starts unbound
tasksession -> tasks: records rounds in
tasksession -> workflows: starts in its task worktree
tasksession -> runs: starts in its task worktree
workflows -> runs: runs one at a time
runs -> workers: an Operation launches
```

The main agent never changes the primary worktree's Specs or code beyond a small change the
developer approved: its view there is the whole project, so nothing would bound or evidence a
change made directly, and the primary worktree must stay clean to merge; the developer's approval
of the specific change stands in for that evidence where a task would cost more than the change.
Inside a task worktree a direct change is bounded by the task and evidenced by `task-validation`
and `delivery`, so task sessions may change Specs and code there themselves. Every `concorde` command that works on a task's workspace runs with the
worktree's own copy, because only the branch's copy knows the Specs, Protocol and checks the task
changes, and only that worktree's binding names the task's workspace. The main agent hands every
task, even a single one, to a task session, so that it stays free to talk with the developer and to
answer every session while tasks run, and every task runs under a boundary; a task session's writes
are confined to its task by the
[session boundary](../../glossary.json#concept.session-boundary), which
[Task sessions](../task-session/module.md) obtains from the Harness, while the main agent stays
unrestricted and alone merges; merging needs no authorization because `delivery` only commits what
it found ready, and a merge is ordinary, revertible Git. The escalation policy balances the same
way: deciding ordinary questions keeps work moving, recording and reporting them keeps them
reviewable, and reserving major-impact ones protects decisions only the developer may make.
Gathering a task's decisions into one escalation, and the developer's answers into one reply,
keeps the developer's attention in one place, the main session, and asks for it once per round
rather than once per question.

<a id="uses-tasks"></a>

**Tasks** provides the [task](../../glossary.json#concept.task) — its branch, its worktree bound as
a workspace, and its record — and the [decision log](../../glossary.json#concept.decision-log): the
workspace of level 2, which a task session works. `concorde task show` lists the task's runs, deliveries and the holder of its
[workspace lock](../../glossary.json#concept.workspace-lock), read from what Execution recorded, so
the main agent learns a task's progress from one command. Each task's own worktree is what keeps
parallel tasks from mixing changes; opening, merging and closing tasks are the main agent's
responsibility, and the log is written by the main agent and the task's session alike. The guidance
relies on `concorde task merge` holding the merge lock and undoing a merge whose checks fail, and
tells the main agent to retry a `merge_busy`, to have the task's session resolve a conflict in the
task worktree, and to
treat a failed check as new work rather than discard a change. It also relies on Tasks refusing
every task command with `merge_incomplete` after a merge was interrupted, and tells the main agent
to finish that merge first with `--resume` or `--abort` rather than to work around the refusal:
checking the merge again is the default, since the recorded checks decide as they would have, and
only a primary branch changed by hand after the merge goes to the developer. A task session has no
authority to finish a merge, so its guidance sends such a refusal to the main agent.

<a id="uses-task-session"></a>

**Task sessions** starts the task sessions the main agent delegates tasks to and, in pi, runs and
records their [session rounds](../../glossary.json#concept.session-round), whose
progress files and recorded outcomes the run view reads. It applies to every task. The guidance
relies on a task session never merging its task into the primary branch or closing it and on every
round ending with an outcome its round's node records. A task session's report or
escalation is its result travelling up to level 1: the main agent answers the escalations, all at
once, or asks for more, with the next round's answer, reads a failed round's error chain like any other, and
merges a delivered task itself.

<a id="uses-workflows"></a>

**Workflows** provides the [workflows](../../glossary.json#concept.workflow) the main agent names
in a task's brief, their modes and the
[workflow result](../../glossary.json#concept.workflow-result) read when one ends. The guidance
relies on a workflow never opening, merging or closing a task and on its result keeping every
run's chain whole, so that a workflow's end is handled like a run's: an `awaiting_decision` result
makes the task session escalate every pending decision point at once, and the main agent answers
them all before the session starts the same workflow again with the answers. Workflows never
writes the decision log, so the guidance makes the task session copy a report's decisions and
problems there.

<a id="uses-tracing"></a>

**Tracing** lays out where the run view finds what it shows: the runs in the current tasks'
workspace folders and in `.concorde/unbound/`, each a [trace node](../../glossary.json#concept.trace-node)
with its workers inside it, the nodes of task-session rounds, and the run locks under
`.concorde/locks/runs/`. The run view relies on the [layout](../../tracing/contracts.md#layout)
and the [locks](../../tracing/contracts.md#locks), and on a runner removing its run lock file as it
exits. For a whole task's history with its cost, the guidance points the main agent to
`concorde trace show <task>`.

<a id="uses-execution"></a>

**Execution** runs the work a task session starts in its task worktree: `concorde run` for an
Operation and the [execution commands](../../glossary.json#concept.execution-command)
`concorde task-validation`, `concorde delivery` and `concorde scaffold`, each reading the
worktree's [workspace binding](../../glossary.json#concept.workspace-binding), and
the Operations that run [unbound](../../glossary.json#concept.unbound-run) in the
primary worktree. Each run returns a [run result](../../glossary.json#concept.run-result)
the main agent can read without inspecting a worker, and none starts the next one: that choice is
the agent's that started it. Every non-`ok` result of a task's runs is recorded in the decision log, and its
chain is read in full before deciding or escalating. The run view relies on each running run keeping its
[run progress file](../../glossary.json#concept.run-progress-file) current in its trace node in
the primary worktree's run store, whose workspace folders every task worktree's binding names, and
on each runner holding its [run lock](../../glossary.json#concept.run-lock) under
`.concorde/locks/runs/` for as long as it runs.

<a id="uses-operations"></a>

**Operations** provides the [Operation](../../glossary.json#concept.operation)
catalog: which Operations exist, what each takes and which may run unbound. The guidance names
them, and the task session chooses which to run for a task's next step.

<a id="uses-commands"></a>

**Commands** provides the catalog of
[execution commands](../../glossary.json#concept.execution-command), the
deterministic runs `task-validation`, `delivery` and `scaffold` that a task session starts by name
in its task worktree. The guidance names them apart from the Operations, since they launch no worker
and a caller starts them without `run`.

### Beside the levels

Two providers serve the main agent without being a level below it.

<a id="uses-issues"></a>

**Issues** provides durable [Issue](../../glossary.json#concept.issue) records and the
bookkeeping command for [reports](../../issues/interface.md#contract.issues.report) and
[receipts](../../issues/interface.md#contract.issues.receipt). The guidance relies on
status following dispositions and
[revisions](../../glossary.json#concept.issue-revision) detecting concurrent writes. It tells
the main agent to inspect before recording, make every Issue write in a task, preserve unmerged
observations for follow-up, and merge closure with the fix. The command records these decisions;
the main agent remains responsible for their evidence and for resolving conflicting decisions.

<a id="uses-spec-mcp"></a>

The **Spec MCP server**, a child of Spec tooling, answers read-only queries about Modules, context
and grants from the worktree it is rooted in. The main agent configures it for its own session only
when it wants to ask such questions; workers never receive it. Since a server rooted in the primary
worktree knows only the primary branch's Specs, the guidance tells the main agent that a question
about a task's Specs needs a server, or a `concorde` command, rooted in that task's worktree.

### Inside

How this Module is built: the guidance on one side, and the pi extension on the other.

```d2
mainsession: Main session {
  sources: Guidance sources {
    "prompts/main-session/"
  }
  guidance: Main-session guidance
  view: pi run view {
    "pi_extension.ts"
    "pi_runs.ts"
  }
  sources -> guidance: authors
}
```

<a id="realization.main-session.guidance"></a>

The **guidance sources** live under `prompts/main-session/` (`skill.md`, installed as the project
skill `.claude/skills/concorde/SKILL.md`; `claude-md.md`, installed into the project's `CLAUDE.md`;
`task-session.md` and `task-session-pi.md`, the first prompts `concorde task session` gives a
Claude Code and a pi task session, which share `common/task-session.md`; and
`common/in-task.md`, the rules for working inside a task that the skill and the task-session
guidance share) and are rendered by Distribution's build into `generated/main-session/`. Their
tests, under `tests/concorde/main_session/`, check that the rendered guidance states every rule the
[scenarios](scenarios.md) describe; what the main agent then does is judgment no deterministic test
observes. The skill is also installed for pi as `.pi/skills/concorde/SKILL.md`.

<a id="realization.main-session.pi-run-view"></a>

The **pi run view** is `src/concorde/main_session/pi_extension.ts`, installed as
`.pi/extensions/concorde/index.ts`, with the pure reading of progress files in `pi_runs.ts` beside
it. It also sets `CONCORDE_CLIENT=pi` for every command the session starts, which tells Concorde
that the main session is pi, so that `concorde task session` starts pi task sessions; which
backend a worker runs on is not affected, since Workers takes it from the worktree's worker
configuration. It tells an execution command from an Operation by name and starts the first as
`concorde <command>`, the second as `concorde run <operation>`, both with `--detach`, and reads the
announced run. It finds a worker's progress file in the run's own node, `workers/<worker run>/`,
never by a process identifier, which runners in different PID namespaces, such as sandboxed shells,
share. It tells whether a runner still lives by its [run lock](../../glossary.json#concept.run-lock)
`.concorde/locks/runs/<run-id>.lock`: a missing file means the runner has exited, and an existing
one is held exactly when the kernel's lock table `/proc/locks` names its inode, whichever PID
namespace holds it; only where the kernel shows no lock table does it fall back to the recorded
process identifier. A run still marked running without a result whose run lock nobody holds is
shown `failed`. It looks for runs it does not follow yet on every refresh, except while
`concorde_run` is still waiting for a run it started to be announced, which that tool then answers,
so that no run is reported twice. `pi_runs.ts` also reads the status files of task-session
sessions and the nodes of their rounds. The
tests run `pi_runs.ts` under Node against progress files; the extension itself needs a pi session
and is exercised in one.

The pi extension is the only part of this Module that is code meeting other Modules directly. It
observes what they record and starts their commands, and the records it reads stay theirs:

```d2
view: pi run view
round: Task sessions / Session round
wprogress: Workers / Progress file
rprogress: Execution / Run progress file
view -> round: follows
view -> wprogress: reads
view -> rprogress: reads
```

<a id="uses-workers"></a>

**Workers** keeps each worker run's [progress file](../../glossary.json#concept.progress-file). The
run view relies on it recording the phase, round and latest tool call, and the Operation run that
launched the worker, and on it being an observation only: the
[run record](../../glossary.json#concept.run-record), not the progress file, is the evidence, so the
view shows but never judges a run from it. Workers also owns the
[worker configuration](../../glossary.json#concept.worker-configuration), which the guidance tells
the main agent to edit directly; the guidance relies on Workers validating the whole file when a
worker launches and reporting a malformed one with `config_invalid`. The separate discovery helper
supplies suggestions without proving API access or gating edits.

### Who relies on it

Three Modules consume what this one authors. [Distribution](../../distribution/module.md) renders
the guidance sources and installs the rendered guidance and the pi extension into a project;
[Dogfooding](../../dogfooding/module.md) appends its own section to the guidance in a develop
install and changes nothing else; and [Task sessions](../task-session/module.md) gives a task
session the rendered task-session guidance as its first prompt, so every task follows the method
this Module sets.
