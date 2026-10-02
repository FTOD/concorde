# Workflows

## Purpose

Workflows is level 3 of Concorde's [levels of work](../module.md#the-levels-of-work), the top of
[Execution](../execution/module.md): a workflow orders the runs of one bound workspace for a known procedure,
such as describing existing code in Specs, and handles their results and
[decision points](../glossary.json#concept.decision-point). Each workflow's procedure is written
once and the build renders it into a Claude Code workflow. Whoever works
a workspace, in Concorde the task level inside a task worktree, starts the workflow there; it runs
Operations and execution commands one at a time, records its steps in its own
[workflow record](../glossary.json#concept.workflow-record), the
[trace node](../glossary.json#concept.trace-node) of the workflow in the workspace folder, with
the runs of its steps nested inside it, and returns one
[workflow result](../glossary.json#concept.workflow-result) with every step, decision,
[open question](../glossary.json#concept.open-question) and problem, preserving each problem's
error chain. In interactive mode it stops where a decision is needed, so that whoever started it
can have it settled; in no-ask mode it follows
the procedure's continuation rules and reports the decisions at the end.

Workflows adds orchestration, not authority. It knows no task: it never opens, merges or closes one,
never reads or writes a [task record](../glossary.json#concept.task-record) or a
[decision log](../glossary.json#concept.decision-log), and every run it starts is an ordinary run
whoever works the workspace could have started itself.

## Core concepts

A workflow is a procedure over runs: it asks for each run as a step named by a key, stops at the
decision points its mode tells it to, and ends with a result built from what the runs recorded. It
builds on Execution's [run](../glossary.json#concept.run),
[run result](../glossary.json#concept.run-result) and
[workspace lock](../glossary.json#concept.workspace-lock).

### Workflows and their modes

<a id="concept.workflow"></a>

A **[workflow](../glossary.json#concept.workflow)** is started in a bound
[workspace](../glossary.json#concept.workspace), never by a worker or a run. In Concorde the task
level starts it: the [task session](../glossary.json#concept.task-session) the
[main agent](../glossary.json#concept.main-agent) delegated the task to, in the mode the task's
brief names. It is level 3 of the [levels of work](../module.md#the-levels-of-work), directly
above the runs: the workflow determines which run comes next, while each run owns its workers,
check calls and internal repair rounds. A task says what work is isolated where; a workflow says how
the runs in that workspace proceed.

<a id="concept.workflow-mode"></a><a id="concept.decision-point"></a>

The **[workflow mode](../glossary.json#concept.workflow-mode)** decides what happens at a
**decision point**, an item in a run's output that is not the worker's to settle but is settled
above the task: every [open question](../glossary.json#concept.open-question), because the
worker could not tell what behaviour is intended, and every decision of a survey that
the worker took itself rather than following an answer, because how a project splits into Modules
shapes all later work. A code_to_spec decision, such as a concept's name, is ordinary: the workflow
never stops for it and reports it. Workflows does not say who settles a point: in Concorde the
[main agent](../glossary.json#concept.main-agent) settles those its authority covers and puts to
the developer those with a major impact, as its guidance's decision policy says, and Workflows
counts an answer the same whoever gave it.

- **Interactive.** The decision points are to be settled before the workflow goes on, so it ends
  right after any step that needs them: a step whose output has decision points its answers did
  not settle, with status `awaiting_decision` and each pending point with its options and
  recommendation; and any step that did not end `ok`, with that step's status. Whoever started it
  has every pending point settled at once, in Concorde by a task session that escalates them all
  together to the main agent, which decides those its authority covers and puts the rest to the
  developer, never by asking in place; then it writes the answers or repairs what failed, and
  starts the same workflow again. Steps that finished return
  their recorded runs immediately, an answered or retried step runs again, and the workflow
  continues.
- **No-ask.** The workflow never stops for a decision point. It keeps each worker's decision, leaves
  each open question unanswered and unwritten as a promise, goes on past a
  [Module](../glossary.json#concept.module) whose description did not end `ok`, and reports
  everything once the procedure has ended. It stops early only where the procedure cannot go on at
  all, such as a failed survey.

### Steps and their keys

<a id="concept.workflow-step"></a><a id="concept.step-key"></a>

A **[workflow step](../glossary.json#concept.workflow-step)** is one
[run](../glossary.json#concept.run), of an [Operation](../glossary.json#concept.operation) or
of an [execution command](../glossary.json#concept.execution-command). The script asks for it by
a base **[step key](../glossary.json#concept.step-key)**, such as `survey` or
`describe:module.checkout`, and `concorde workflow step` starts its run or, for a key it has seen
before, returns the recorded run. The step's key is the base key, followed by `#` and the generation
label when a restart names one, and with answers by `@` and a digest of those answers, so a
restarted or answered rerun is a new step while the same label and answers find the same step
again. [The step command](#the-step-command) gives the exact rule.

Starting a new run for a base key that already has a step, by `--retry`, with a new restart label
or with new answers, **supersedes** that earlier step and every step recorded after it: a
superseded step stays in the record but is never found again, so the procedure runs its later steps
anew on the changed workspace and nothing validated or delivered before the change is taken as
current. An answered step's `--input` is the latest `ok` run of its base key even when a rerun
superseded that run, since the answers still refer to its questions.

### The record and the result

<a id="concept.workflow-record"></a>

The **[workflow record](../glossary.json#concept.workflow-record)** of a workspace is the
`trace.json` of the workflow's [trace node](../glossary.json#concept.trace-node), `workflow/` of
the workspace folder its binding names, beside the answers passed to steps (`answers/`), the saved
reports (`reports/`) and the step nodes (`steps/`). It names the workflow and its mode once, at its
first step, and its content lists every step with its key, the name of its Operation or command,
its run or refusal, its mode, its node and whether it was superseded, and every report. Each step's
node records when the step started and, once a step or report command saw its run end, when it
ended and how; the run's own node lies inside it. A workspace runs at most one workflow. Only the
step and report commands write the record and the step nodes, and only while they hold the workflow
lock. Whoever prepared the workspace finds the workflow in the workspace folder, next to the runs
started directly, and a task's [trace](../glossary.json#concept.trace) holds it.

<a id="concept.workflow-result"></a>

The script ends by running `concorde workflow report [--lost <key>]`, which builds the **[workflow
result](../glossary.json#concept.workflow-result)** ([contract](contracts.md#contract.workflows.result))
from the workflow record and the saved [run results](../glossary.json#concept.run-result), never
from what a step agent relayed. Its status is, in this order of precedence:

- `running` when a current step's run is still running, for a report taken before the end;
- `failed` when the procedure stopped at a step that ended `failed`, was refused or was lost;
- `blocked` when it stopped at a step that ended `blocked`, or at a task validation that was not
  ready;
- `awaiting_decision` when an interactive run ended at decision points;
- `ok` when the procedure's last step, `delivery` in the brownfield workflow, ended `ok`, even if
  earlier steps reported problems the procedure could go past;
- `failed`, with the code `incomplete`, when the recorded steps end before the procedure's last
  step without any of the stops above, such as a report taken after a script ended early.

Every result lists, from the current steps, every decision and open question as the run reported
it, with its step and run; every deviation; every Spec review's verdict and findings; the checks
the survey proposed, for the developer to configure the ones they accept; and each step that did
not end `ok` as a problem with its error chain unchanged. Superseded steps are listed apart, with
their runs, and contribute nothing else. When the status is not `ok`, `error` is the workflow's own
[error chain](../glossary.json#concept.error-chain) link, level `workflow`, whose causes
are the errors of the steps that stopped it, unchanged; for `awaiting_decision` its evidence names
every pending point. The report is saved in the workflow's node as `reports/<n>.json`, with a
Markdown rendering `reports/<n>.md`, and listed in the record; it is written into no decision log.
Decisions a no-ask workflow took without the developer belong in the decision log of whoever
started it, so the task level copies them from the rendering into the task's log itself. When a
step agent returned nothing, the script reports with `--lost <key>`: a key whose base key has a
current step keeps what that step's run shows, finished, still running or lost, since the record
wins, and any other is reported lost.
Anyone can run the report command in the workspace again at any time.

### Scripts and step agents

<a id="concept.step-agent"></a><a id="concept.workflow-script"></a>

A **[workflow script](../glossary.json#concept.workflow-script)** holds a workflow's procedure
once, in plain JavaScript without asynchronous helper functions, kept apart from the step adapter.
The build wraps it with a `meta` block and the Claude Code step adapter, whose step function's
**[step agent](../glossary.json#concept.step-agent)** is a subagent that calls the
[project MCP server](../glossary.json#concept.project-mcp-server)'s tool `workflow_step` once
with the step request, waiting at most 100 seconds, and returns the step outcome it answered, while
the step function itself asks again as long as the run is still running and treats an outcome that
names another step or no real run as no answer. The server runs the step command as a process of its
own, as [Steps in Claude Code](#steps-in-claude-code) explains. A model copies
the request, and a live headless run showed one dropping a field of it,
which the step command then refused as `invalid_request`; so the step function asks again after an
outcome that is no answer, three times in a row at most, since the same key never starts a run
twice. A step still without an answer is reported lost, and the script's result carries what its
agents relayed last as `relayed`, marked unverified, so that the step command's own refusal stays in
the error chain. The report is relayed the same way, by one more such subagent. A step agent only
relays; what counts is what the runs recorded.

The terms relate as follows:

```d2
workflow: Workflow
mode: Workflow mode
point: Decision point
step: Workflow step
key: Step key
record: Workflow record
agent: Step agent
script: Workflow script
result: Workflow result
brownfield: Brownfield workflow
workflow -> step: runs
workflow -> mode: runs in
step -> key: is named by
record -> step: lists
agent -> step: relays
script -> workflow: defines
workflow -> result: ends with
mode -> point: decides what happens at
brownfield -> workflow: is a
```

## Overview

Three pictures show Workflows: its place between the task level and the runs, how one step is
carried from the script to a run and back, and the brownfield procedure.

### Its place in the levels of work

A workflow orchestrates runs from the Claude Code session of whoever works the workspace. Each run
completes one job, an Operation by combining workers, services and host steps, an execution command
deterministically, and never starts another run. The workflow sees only their command lines and
results; it leaves worker prompts, grants, check calls, audits and repair loops inside the run. Each
workflow step is an ordinary run of the
[Execution runner](../glossary.json#concept.execution-runner), so the workspace lock allows one
run at a time and every run is recorded, audited and reported exactly as if the task level had
started it.

Workflows is level 3 of the [levels of work](../module.md#the-levels-of-work). It is called from
the task level only: the task session a task was delegated to starts a workflow in the task worktree
and may go on with other work while it runs in Claude Code's background. It calls only the level
directly below: its commands start each step as a run, and it never reaches a worker or a service,
which only a run calls. What goes back up is one workflow result, assembled from what the runs
recorded, in which every run's error chain stays whole under the workflow's own link. The task level
is free to skip this level and start a run directly whenever no workflow fits, and nothing a
workflow does opens, merges or closes a task.

```d2
workflows: Workflows {
  scripts: Workflow scripts
  commands: Workflow commands
  record: Workflow record
  scripts -> commands: runs steps through
  commands -> record: records steps in
}
execution: Execution
workflows.commands -> execution: starts runs through
```

The script never runs a command itself; its step agents relay each step, through the project MCP
server, to the workflow commands, which alone start runs, keep the workflow record and read the run
results.

### One step, from the script to a run and back

A step passes through four participants below the task level. The script asks for a key; a step
agent relays it once, through the project MCP server's `workflow_step`, which runs the step command
as a process of the server, waiting at most 100 seconds; the workflow commands start the
run only when the key is not yet recorded and otherwise wait for the recorded one; the Execution
runner runs it and saves its result. While the run is still running the script asks again with the
same key, which only waits again, so a run that outlives many calls is still started once. The
report at the end is built from the record, not from what the agents relayed.

```d2 illustrative
grid-columns: 5
horizontal-gap: 60
task: "Task level" {
  grid-columns: 1
  vertical-gap: 40
  start: "Start the workflow\nin the task worktree\n(mode, answers)"
  g1: "" {style.opacity: 0}
  g2: "" {style.opacity: 0}
  g3: "" {style.opacity: 0}
  g4: "" {style.opacity: 0}
  receive: "Receive the workflow\nresult with its\nerror chain"
}
script: "Workflow script" {
  grid-columns: 1
  vertical-gap: 40
  g0: "" {style.opacity: 0}
  request: "Ask for the step\nwith key \"survey\""
  g1: "" {style.opacity: 0}
  again: "Still running?\nAsk again, same key"
  next: "Finished: go on to\nthe next step, or\nask for the report"
  g2: "" {style.opacity: 0}
}
agent: "Step agent" {
  grid-columns: 1
  vertical-gap: 40
  g0: "" {style.opacity: 0}
  relay: "Call workflow_step of the\nproject MCP server once,\nwaiting at most 100 s,\nrelay what it answered"
  g1: "" {style.opacity: 0}
  g2: "" {style.opacity: 0}
  g3: "" {style.opacity: 0}
  g4: "" {style.opacity: 0}
}
commands: "Workflow commands" {
  grid-columns: 1
  vertical-gap: 40
  g0: "" {style.opacity: 0}
  lookup: "Look the key up among\nthe current steps; if it is\nnot recorded, start the run\ndetached and record it"
  g1: "" {style.opacity: 0}
  wait: "Wait for the saved\nrun result (exit 3\nwhile still running)"
  g2: "" {style.opacity: 0}
  report: "workflow report: build\nthe workflow result\nfrom the record"
}
runner: "Execution runner" {
  grid-columns: 1
  vertical-gap: 40
  g0: "" {style.opacity: 0}
  g1: "" {style.opacity: 0}
  run: "concorde run survey\n--detach"
  saved: "Run result saved\nin the run store"
  g2: "" {style.opacity: 0}
  g3: "" {style.opacity: 0}
}
task.start -> script.request
script.request -> agent.relay
agent.relay -> commands.lookup
commands.lookup -> commands.wait
commands.lookup -> runner.run: "not recorded:\nstarts"
runner.run -> runner.saved
runner.saved -> commands.wait: "read by"
commands.wait -> agent.relay: "step outcome" {style.stroke-dash: 3}
agent.relay -> script.again: "running" {style.stroke-dash: 3}
agent.relay -> script.next: "finished" {style.stroke-dash: 3}
script.again -> agent.relay
script.next -> commands.report: "through one more\nstep agent"
commands.report -> task.receive: "via the script" {style.stroke-dash: 3}
```

## Using a workflow

### A workflow's arguments

Every workflow takes `mode`, `answers`, `retry` and `restart`, plus its own arguments such
as `module`. `answers` maps a step's base key, such as `survey` or `describe:module.checkout`, to
the list of every answer given for that step so far, by the main agent or the developer, in the shape of
answers; a relaunch passes all of them again, not only the
newest. `retry` lists the base keys to run again after a failure. `restart` maps a base key to a
short generation label, such as `{"scaffold": "2"}`, to run that step again whatever its outcome,
for instance after the workspace was reset by hand: the label becomes part of the
[step key](../glossary.json#concept.step-key), so the step and every later step run once more,
and relaunching with the same label finds the restarted runs instead of starting them again, as
long as no rerun of an earlier step has superseded them.

### The step command

```text
concorde workflow step --workflow <name> --mode <interactive|no-ask> --key <base key> [--answers <file>] [--retry] [--restart <label>] [--wait <seconds>] -- <operation or command> [arguments]
concorde workflow step --json '<step request>' [--wait <seconds>]
```

The step's key is the base key, followed by `#` and the generation label when `--restart` names one,
and with `--answers` by `@` and the first eight hexadecimal digits of the SHA-256 of the answers
list in canonical JSON (keys sorted, no whitespace), so a restarted or answered rerun is a new step
while the same label and answers find the same step again. Holding the workspace's **workflow lock**,
`locks/workflows/<workspace>.lock` of the binding's `.concorde`, which only the step and report
commands take and which is distinct from the [workspace lock](../glossary.json#concept.workspace-lock)
a run holds, the command looks
the key up among the **current steps** of the workspace's workflow record, those no later rerun has
superseded. When it is not there, it creates the step's node `steps/<n>-<key>/`, `<n>` counting every
step the workflow recorded from 1 and the key written with every character other than a lower-case
letter, digit, `.` or `-` as `_`, and starts the run detached with the workspace's own `concorde`,
placing the run's node inside the step's with `--trace-at <step node>/run`:
`concorde run <operation> … --detach` for an Operation and `concorde <command> … --detach` for an
execution command such as `task-validation`, `delivery` or `scaffold`. For an answered step it adds
`--answers` with the answers written next to the workflow record and `--input` naming the latest
`ok` run of the same base key, whose questions the answers settle; then it records the key and run
in the workflow's node and writes the step's node.
It waits for the result at most `--wait` seconds (default 540). Asked again, it finds the recorded
run and only waits for it. `--retry` starts a new run for a key whose recorded run did not end `ok`.
`--json` takes the same request as one [step request](contracts.md#contract.workflows.step-request),
as the [step agent](../glossary.json#concept.step-agent) passes it.

The command prints the [step outcome](contracts.md#contract.workflows.step) and exits with status 0
once the run has finished, 3 while it is still running, so a caller that must not block longer than
a few minutes simply asks again, 1 when the step is lost or refused or the command cannot work at
all, and 2 when the command line or request breaks the step request contract (`invalid_request`).
Before it starts a run, the command waits, within the same bound, until the workspace lock is free,
since a workspace runs one run at a time. It waits without holding the workflow lock, then takes it
again and looks the key up again. When the bound ends while the lock is still held, it
starts and records nothing and prints an outcome with state `running`, no run and no error, exiting
with status 3; asking again waits for the lock again. A step is **lost** when its recorded run has
no result and no living runner. A step is **refused** when the runner rejected the command line or
the detached runner did not start: the step is then recorded without a run and with that error. A
step for another workflow than the workspace's, or a key recorded for another Operation or command,
is refused by the workflow record before anything is recorded or started, with a `step_rejected`
link over that refusal; if the record refuses a run already started, the link is `step_unrecorded`
and names the run. Such a step is in no record, so the script returns its outcome with the report.

<a id="retired-workspace"></a>

**A retired workspace.** Whoever retires a workspace, as closing a task does, removes its worktree
with the binding, moves the workspace folder away and removes the workflow lock file, holding the
workflow lock all the while. So the step and report commands write nothing into a workspace folder
until they hold the workflow lock and have read the binding again: they never take a lock file that
was removed or replaced while they waited for it, and once they hold the lock, the binding must
still be the one they read when they started. Otherwise the step is refused with a
`workspace_retired` link, whose cause, a `Workflows (workflow lock)` link, says what the command
found: `lock_removed`, `binding_gone`, `binding_untrusted` or `binding_changed`. Nothing is started
or recorded, for the workspace folder may already lie in the history, which nothing writes: the
outcome alone carries the refusal, with state `refused`, and the script returns it with the report.
A step whose run had started and ended before the workspace was retired is refused the same way when
it comes to end the step's node, naming the run, whose own records went with the folder. The report
command in a retired workspace is refused with a `component` link `workspace_retired`.

The workflow lock is a leaf: neither command waits for another lock while holding it, which is why a
step waits for the workspace lock without it. A close holding the workspace lock, and the [merge lock](../glossary.json#concept.merge-lock)
when it merges, therefore always gets the workflow lock soon, and nothing waits in a circle: a step
that holds the workflow lock before the close does finishes its writes before the folder moves, and
one that waits for it until after the close is refused.
Every lost or refused outcome carries an error link, and a lost step's link carries the end of its
runner's output.

## How it is built

### One procedure, rendered as a Claude Code workflow

A workflow's source is a procedure that the build wraps with a step adapter, not a prompt asking a
model to invent the next steps. The adapter preserves the selection of Operations and commands and
their arguments, step order, branches, admitted results and decision points; it decides only how a
step is invoked and awaited and how the final report is requested. The procedure therefore runs as
a Claude Code workflow that starts Concorde's ordinary runs. Workflows are rendered for Claude Code
alone because the task level that starts them runs on Claude Code; workers, which run on pi or
Claude Code, never start a workflow.

The step agent is an adapter, not a Concorde worker: it relays a command and result, while the run
decides whether to launch AI workers. Rendering a workflow does not expand Operations into Claude
Code agents or expose Concorde's services to those agents. The workflow uses the same run command
lines, the same workspace lock and the same recorded results as runs started directly. The current
mechanism renders authored JavaScript workflow scripts; it is not a general converter for arbitrary
platform workflows or free-form plans.

### Steps in Claude Code

The procedure lives in Claude Code's workflow runtime because it runs the procedure in the
background while the task level stays responsive. That runtime has no shell, so each step is
carried by a step agent. That agent is a model, whose every tool call is meant to end within two
minutes, as a Bash call does unless it asks for more, while a run may take much longer. So a step starts a
[detached run](../glossary.json#concept.detached-run) and each call waits at most 100
seconds, and the repetition is the script's, not the model's: a live headless run showed a step
agent that, handed a longer wait and told to repeat, let its command go to the background and
returned an invented outcome instead. Because a key maps to one recorded run, repeating a call or
relaunching the whole workflow never starts a run twice, and a relaunched interactive workflow
replays its finished steps at once.

<a id="steps-through-the-server"></a>

The detached run must also outlive the relay that started it, and a step agent's own Bash does not
let it. A step may run for many minutes while each relay is one short turn, and a run anchored in a
relaying agent's call lives only as long as that call: an end-to-end run on 2026-09-30 lost its
survey step this way, `step_lost` over `host_ended` with nothing in the runner's output, while the
worker was still reading, because a sandboxed Bash call's PID namespace ends with the call and
takes every process it started with it ([Execution](../execution/module.md#detached-namespace)). So a step
agent does not run the step command with Bash: it calls the
[project MCP server](../glossary.json#concept.project-mcp-server)'s tool `workflow_step` with the
step request as an object, and the server, a process of the session beside its tools, runs the step
command of the session's worktree, through the fresh process with which it answers each call
([Current code](../coordination/main-session/module.md#current-code)). The run it starts lives
until it ends, whatever becomes of the calls that asked for it, of the session or of the server;
later calls for the same key only wait for it. The request travels as an object, with nothing quoted for a
shell. The report is still relayed with Bash: `concorde workflow report` starts no run and returns
at once.

The rejected alternative anchored the run in a step agent's background Bash call, which lives until
its command ends: each step's first relay would have started the step command with
`run_in_background` to live as long as the run, then asked for the outcome with a second,
foreground call that only waits, and a later relay that found the step unrecorded and no anchor
alive would have had to start the anchor again. It was rejected because it asks a small relay model
for a two-command choreography around a background command, the very kind of instruction a live run
had seen a relay turn into an invented outcome; because Claude Code ends a background command after
at most two hours and ends a session's background commands when the session is stopped, taking the
run down with them; and because Claude Code wakes each step agent again when its anchor ends, a turn
for nothing. The server path has none of these limits, at the price that a workflow's runs are
started by the session's server rather than by the session's own shell, as
[Task sessions](../coordination/task-session/module.md#workflow-runs-through-the-server)
states.

The result is assembled by a deterministic command from what the runs recorded. A step agent might
drop or paraphrase what it relays; the report reads each saved run result itself. So the chain the
developer finally reads is the runs' own, with the workflow's link on top, whatever happened in
between.

### Why Workflows keeps its own record

Workflows keeps its own record rather than writing into the task record, because the execution
core knows no task: a workflow runs in any bound workspace, and the facts it records, which steps
ran with which runs, are Execution's to keep, around the runs they name. A step nests its run
because it gives the run its place before the run starts, as [Tracing](../kernel/tracing/module.md)
requires of every parent, so a workflow's trace holds its runs without any run knowing it is a
step. The task level reads the
record and the reports where they are. For the same reason the report is not appended to a
decision log: the log is the task level's, and it decides what to copy into it.

### Inside

How Workflows is built:

```d2
workflows: Workflows {
  commands: Workflow commands {
    "src/concorde/workflows/__init__.py"
    "src/concorde/workflows/catalog.py"
    "src/concorde/workflows/cli.py"
    "src/concorde/workflows/step.py"
    "src/concorde/workflows/report.py"
    "src/concorde/workflows/store.py"
  }
  scripts: Workflow scripts {
    "src/concorde/workflows/scripts/"
  }
  scripts -> commands: runs steps through
}
```

<a id="realization.workflows.commands"></a>

The **[Workflow](../glossary.json#concept.workflow) commands** realization holds the workflow
catalog (`catalog.py`: each workflow's name, description and script), the workflow record with its
workflow lock, answers, saved reports and step nodes (`store.py`), the `concorde workflow step` and `report`
commands and the step outcome, step request and workflow result schemas.

<a id="realization.workflows.scripts"></a>

The **Workflow scripts** realization holds each workflow's procedure (`brownfield.js`) and the Claude
Code step adapter (`claude.js`) the build wraps it with.

<a id="realization.workflows.tests"></a>

The **Workflows tests**, under `tests/concorde/workflows/` with the existing-codebase fixture
`tests/concorde/support/brownfield_project.py`, run the step and report commands in a real bound
task worktree against stand-in run results, one step through a real detached `task-validation`
run, one started inside a PID namespace of its own to show that it dies with it, and run the
rendered script in a small JavaScript sandbox that stands in for Claude Code's
workflow runtime, verifying the [requirements](requirements.md) and
[scenarios](scenarios.md).

## What Workflows relies on

<a id="uses-tracing"></a>

**Tracing** gives the workflow and each step the shape of a
[trace node](../glossary.json#concept.trace-node) and the workflow lock its file under
`locks/workflows/`: the step and report commands write the workflow's and the steps' nodes through
Tracing's library and create each step's node before starting its run inside it, which is how
Tracing nests a run below its step. Workflows relies on the
[node contract](../kernel/tracing/contracts.md#contract.tracing.node) and the
[locks](../kernel/tracing/contracts.md#locks).

<a id="uses-execution"></a>

**Execution** runs every step. The step command starts the runner detached with the workspace's own
`concorde`, reads the announced run identity and waits for the saved
[run result](../glossary.json#concept.run-result), which is the step's outcome. Workflows relies
on each run reading the same [workspace binding](../glossary.json#concept.workspace-binding) as
the workflow, holding the [workspace lock](../glossary.json#concept.workspace-lock) for its whole
life, writing exactly one result before releasing it and starting no other run, so the order of the
runs is the procedure's alone and each step, which waits for the lock before it starts its run,
finds the results of the earlier steps written; a result on disk does not mean the lock is free yet.
It relies on a [detached run](../glossary.json#concept.detached-run) being announced only once
its [run progress file](../glossary.json#concept.run-progress-file) exists, and on the
[run store](../glossary.json#concept.run-store) keeping every run's result and progress by its
identity, which is how a later call, or a relaunched workflow, finds a run it started before.
Workflows reads results and never changes them. It relies on whoever retires a workspace, as the task level
does when it closes a task, holding the workflow lock while it removes the binding, moves the
workspace folder and removes the lock file, as [A retired workspace](#retired-workspace) describes. A command line the runner rejects, such as an
unknown argument, and a detached runner that did not start make the step refused, with the runner's
message or `detach_failed` link as the cause; a run with no result and no living runner makes it
lost, with the end of the runner's output; a run that the runner refused, such as one for a
workspace that was busy after all, is an ordinary finished run whose result carries that refusal.

<a id="uses-main-session"></a>

**Main session** provides the [project MCP server](../glossary.json#concept.project-mcp-server),
whose `workflow_step` tool the Claude Code step agents call. Workflows relies on it running the
step command of the session's worktree as a process of the server, so that the run outlives the
relay, and answering with the step outcome that command printed, or with its refusal unchanged; it
relies on nothing else of the server.

<a id="uses-operations"></a>

**Operations** names the jobs that involve a model. A workflow's steps name Operations from the
[Operation catalog](../glossary.json#concept.operation-catalog), such as `survey`,
`code_to_spec` and `spec_review`, with their arguments; Workflows relies on each Operation
returning its output under its catalog entry's contract, which the runner checks before it saves
the result, and never starting another Operation. It never looks inside an Operation. From a
`spec_review` result it copies the output's `verdict` and its `modules`, each reviewed Module's
outcome with its findings, unchanged into the workflow result; it neither judges nor repairs them.

<a id="uses-commands"></a>

**Commands** names the deterministic runs. A step names an
[execution command](../glossary.json#concept.execution-command) of its catalog, such
as `task-validation` or `scaffold`, by the command's own name, and the step command starts it as
`concorde <command>` instead of `concorde run`; Workflows relies on the catalog to tell the two
kinds apart and treats their results alike.

<a id="uses-validation"></a>

**Validation** provides the execution command `task-validation`. A workflow runs it before delivery;
the step outcome's `ready` is the
[readiness](../method/validation/contracts.md#contract.validation.readiness)'s `ready`, and the
procedure delivers only when it is true. Workflows relies on the readiness saying whether the
workspace is ready and never decides readiness itself.

<a id="uses-delivery"></a>

**Delivery** provides the execution command `delivery`, a workflow's last step, which decides the
readiness again and commits the workspace. The brownfield workflow passes `--adoption`, because an
adoption describes code that already exists and adds no test, so a scenario it writes need not
have a new verifying test to be delivered. Workflows relies on delivery refusing a workspace that is
not ready rather than committing it, and leaves the merge to the task level.

<a id="uses-adoption"></a>

**Adoption** provides the survey and code_to_spec steps and defines the decisions, open
questions, answers and deviations that the brownfield workflow counts and reports. Workflows reads
them from the run results by their [contracts](../method/adoption/contracts.md) and passes
answers back through `--answers`; it never interprets what a decision means. It relies on those
contracts to tell a survey decision from a code_to_spec decision and an open question from a
settled one, since that is what makes a decision point; an output that does not follow them is the
run's failure and ends the step as its result says.

<a id="uses-scaffold"></a>

**Scaffold** provides the scaffold step between them. Its
[scaffold record](../method/scaffold/contracts.md#contract.scaffold.record) names the Modules it
created, and the step outcome lists them with the `uses` the survey proposed among them; Workflows
relies on the record listing every Module the scaffold created, which the brownfield workflow then
describes one by one.
