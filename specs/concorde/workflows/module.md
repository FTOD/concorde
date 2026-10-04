# Workflows

## Purpose

Workflows is the workflow [part](../glossary.json#concept.part). It is level 3 of Concorde's
[levels of work](../module.md#the-levels-of-work), directly above the runs of
[Execution](../execution/module.md). A workflow orders the runs of one bound workspace for a known
procedure, such as describing existing code in Specs. It handles their results and the
[decision points](../glossary.json#concept.decision-point) their outputs declare. The part that
owns each workflow's procedure writes it once. The build renders it into a Claude Code workflow.
Whoever works a workspace starts the workflow there. In Concorde, this is the task level inside a
task worktree. The workflow runs Operations and execution commands one at a time. It records its
steps in its own [workflow record](../glossary.json#concept.workflow-record). This is the
[trace node](../glossary.json#concept.trace-node) of the workflow in the workspace folder.
The runs of its steps are nested inside it. The workflow returns one
[workflow result](../glossary.json#concept.workflow-result) with every item of these kinds:

- Step.
- Decision.
- Decision point.
- Deviation.
- Note.
- Problem, with its error chain preserved.

In interactive mode, the workflow stops where a decision is needed so that whoever started it can
have the decision settled. In no-ask mode, it follows the procedure's continuation rules. It
reports the decisions at the end.

A step is only ever a Concorde run, so the workflow part depends on the execution part and the
kernel alone. It knows no particular Operation or command. Under Workflows'
[step output convention](contracts.md#contract.workflows.step-output), a run declares in its
output what it wants a workflow to know:

- Its decision points.
- Its decisions.
- Its deviations.
- Its notes.
- The values its script reads.

The procedure determines these details:

- Which steps it runs.
- In which order it runs them.
- Which step is its last.

In Concorde the procedures and the Operations that fill the convention are
[Method](../method/module.md)'s, such as its
[brownfield workflow](../glossary.json#concept.brownfield-workflow).

Workflows adds orchestration, not authority. It knows no task. It never does any of these things:

- Open a task.
- Merge a task.
- Close a task.
- Read or write a [task record](../glossary.json#concept.task-record).
- Read or write a [decision log](../glossary.json#concept.decision-log).

Every run it starts is an ordinary run whoever works the workspace could have started itself.

## Core concepts

A workflow is a procedure over runs. It does these things:

- Asks for each run as a step named by a key.
- Stops at the decision points its mode tells it to.
- Ends with a result built from what the runs recorded.

It builds on these Execution concepts:

- [run](../glossary.json#concept.run).
- [run result](../glossary.json#concept.run-result).
- [workspace lock](../glossary.json#concept.workspace-lock).

### Workflows and their modes

<a id="concept.workflow"></a>

A **[workflow](../glossary.json#concept.workflow)** is started in a bound
[workspace](../glossary.json#concept.workspace), never by a worker or a run. In Concorde the task
level starts it, in the mode the task's brief names. This is the
[task session](../glossary.json#concept.task-session) the
[main agent](../glossary.json#concept.main-agent) delegated the task to. The workflow is level 3 of
the [levels of work](../module.md#the-levels-of-work), directly above the runs. The workflow
determines which run comes next. Each run owns these things:

- Its workers.
- Its check calls.
- Its internal repair rounds.

A task says what work is isolated where. A workflow says how the runs in that workspace proceed.

<a id="concept.workflow-mode"></a><a id="concept.decision-point"></a>

The **[workflow mode](../glossary.json#concept.workflow-mode)** decides what happens at a
**decision point**. Under the [step output convention](contracts.md#contract.workflows.step-output),
a run's output declares this item as not the run's to settle. The item is to be settled above the
task. It is one of two kinds:

- A decision of kind `decision`, a choice the run took or proposes.
- An item of kind `question`, an [open question](../glossary.json#concept.open-question) the run
  could not settle.

The producing Operation's own rule determines which of its items are decision points.
Its [Spec](../glossary.json#concept.spec) states that rule. Method's survey, for instance,
declares every decision it took itself because how a project splits into
[Modules](../glossary.json#concept.module) shapes all later work. It also declares every open
question. A `code_to_spec` decision such as a concept's name is ordinary. It is only reported among
the run's decisions. The workflow never stops for it. Workflows interprets no point. It only counts
those an answer has not settled. Workflows does not say who settles a point. In Concorde, the
[main agent](../glossary.json#concept.main-agent) settles those its authority covers. It puts to
the developer those with a major impact, as its guidance's decision policy says.
Workflows counts an answer the same whoever gave it.

- **Interactive.** The decision points are to be settled before the workflow goes on.
  For this reason, when a step's output has decision points its answers did not settle, the workflow
  ends right after that step. It ends with status `awaiting_decision` and each pending point with
  its options and recommendation. When any step did not end `ok`, the workflow ends right after
  that step with that step's status.

  Whoever started the workflow has every pending point settled at once. In Concorde, a task session
  escalates them all together to the main agent, never by asking in place. The main agent decides
  those its authority covers. It puts the rest to the developer. Then whoever started the workflow
  writes the answers or repairs what failed. Whoever started the workflow starts the same workflow
  again. Steps that finished
  return their recorded runs immediately. An answered or retried step runs again. The workflow
  continues.
- **No-ask.** The workflow never stops for a decision point. It keeps each run's decision.
  It leaves each question unanswered and unwritten as a promise. When a step did not end `ok`, the
  workflow goes past it if its procedure lets it, such as one description among several.
  Once the procedure ends, the workflow reports everything. It stops early only where its procedure
  cannot go on at all, such as a failed survey in the brownfield workflow. The procedure says where
  this applies.

### Steps and their keys

<a id="concept.workflow-step"></a><a id="concept.step-key"></a>

A **[workflow step](../glossary.json#concept.workflow-step)** is one
[run](../glossary.json#concept.run), of an [Operation](../glossary.json#concept.operation) or
of an [execution command](../glossary.json#concept.execution-command). The script asks for it by
a base **[step key](../glossary.json#concept.step-key)**, such as the brownfield workflow's
`survey` or `describe:module.checkout`. For a key it has seen before, `concorde workflow step`
returns the recorded run. Otherwise, the command starts the step's run. The step's key starts with
the base key. When a restart names a generation label, the key appends `#` and that label.
With answers, the key appends `@` and a digest of those answers. Thus, a restarted or answered rerun
is a new step. The same label and answers find the same step again.
[The step command](#the-step-command) gives the exact rule.

For a base key that already has a step, a new run starts through any of these means:

- `--retry`.
- A new restart label.
- New answers.

Starting that new run **supersedes** the earlier step and every step recorded after it.
A superseded step stays in the record but is never found again. For this reason, the procedure runs
its later steps anew on the changed workspace. For the same reason, nothing validated or delivered
before the change is taken as current. Even when a rerun superseded the run, an answered step's `--input` is the latest
`ok` run of its base key. This is because the answers still refer to that run's questions.
When that base key has no `ok` run, the answered step has no input.

### The record and the result

<a id="concept.workflow-record"></a>

The **[workflow record](../glossary.json#concept.workflow-record)** of a workspace is the
`trace.json` of the workflow's [trace node](../glossary.json#concept.trace-node).
That node is `workflow/` of the workspace folder its binding names.
The record sits beside these items:

- The answers passed to steps (`answers/`).
- The saved reports (`reports/`).
- The step nodes (`steps/`).

The record names the workflow once, at its first step.
For a workflow whose first step was lost before anything was recorded, the record names the
workflow at its first report instead.
The record carries the mode of the latest recorded step.
Its content lists every report and every step.
For each step, it lists these details:

- Its key.
- The name of its Operation or command.
- Its run (none yet while the step is starting) or refusal.
- Its mode.
- Its node.
- Whether it was superseded.

Each step records its own mode, so a relaunch may change the mode.
The script stops by its own mode.
The report judges pending points by the latest recorded step's mode.
Each step's node records when the step started.
Once a step or report command saw the step's run end, the step's node records when the step ended
and how.
The run's own node lies inside the step's node.
A workspace runs at most one workflow.
Only the step and report commands write the record and the step nodes.
They write only while they hold the workflow lock.
Whoever prepared the workspace finds the workflow in the workspace folder, next to the runs
started directly.
A task's [trace](../glossary.json#concept.trace) holds the workflow.

<a id="concept.workflow-result"></a>

The script ends by running `concorde workflow report --workflow <name> --mode <mode> [--lost <key>]`.
That command builds the **[workflow result](../glossary.json#concept.workflow-result)**
([contract](contracts.md#contract.workflows.result)) from the workflow record and the saved
[run results](../glossary.json#concept.run-result).
It never builds the result from what a step agent relayed.
The report cannot see where the procedure stopped, only what was recorded.
For that reason, the step it judges is the **latest current step** in recorded order.
The result's status follows this order of precedence:

- For a report taken before the end, the status is `running` when either condition holds:
  - Any current step's run is still running.
  - A step still starting may yet get its run.
- When the script reported a key lost whose base key has no current step, the status is `failed`,
  with the code `step_lost`.
- When any of these cases applies to the latest current step, the status is `failed`:
  - It ended `failed`.
  - It was refused.
  - It was lost.
- When the latest current step ended `blocked` or its output declared it blocking, the status is
  `blocked`.
  One example is a task validation that found the workspace not ready.
- When both conditions hold, the status is `awaiting_decision`:
  - The latest recorded step ran in interactive mode.
  - The latest current step's output has decision points its answers did not settle.
- Even if earlier steps reported problems the procedure could go past, the status is `ok`
  when both conditions hold:
  - The latest current step is the procedure's last step, which the workflow names, such as
    `delivery` in the brownfield workflow.
  - The latest current step ended `ok`.
- Otherwise, the status is `failed` with the code `incomplete`.
  This includes either case:
  - The recorded steps end before the procedure's last step, such as a report taken after a
    script ended early.
  - No installed part registers the workflow.

From the current steps, every result lists every item of these kinds that the runs declared:

- Decision.
- Decision point.
- Deviation.
- Note.

The result lists the items as the runs declared them, with each item's step and run.
Examples are a review's verdict or the checks a survey proposed for the developer to configure.
Every result also lists each current step that did not end `ok` as a problem with its error chain unchanged.
Superseded steps are listed apart, with their runs.
They contribute nothing else.
When the status is not `ok`, `error` is the workflow's own
[error chain](../glossary.json#concept.error-chain) link, level `workflow`.
That link's causes are the errors of the steps that stopped the workflow, unchanged.
For `awaiting_decision`, the link's evidence names every pending point.
The report is saved in the workflow's node as `reports/<n>.json`, with a Markdown rendering
`reports/<n>.md`.
The report is listed in the record.
It is written into no decision log.
Decisions a no-ask workflow took without the developer belong in the decision log of whoever
started it.
For that reason, the task level copies them from the rendering into the task's log itself.
When a step agent returned nothing, the script reports with `--lost <key>`.
For a key whose base key has a current step, the record wins, so the key keeps what that step's
run shows:

- Finished.
- Still running.
- Lost.

Any other key is reported lost.
A workspace whose first step was lost before anything was recorded has no record.
In that case, the report builds its result from these inputs:

- `--workflow`.
- `--mode`.
- The lost key.

The report then creates the workflow's node to save the result in
([req.workflows.lost-first](requirements.md#req.workflows.lost-first)).
Anyone can run the report command in the workspace again at any time.

### Scripts and step agents

<a id="concept.step-agent"></a><a id="concept.workflow-script"></a>

A **[workflow script](../glossary.json#concept.workflow-script)** holds a workflow's procedure
once, in plain JavaScript without asynchronous helper functions.
The script is kept apart from the step adapter.
The part that owns a procedure contributes its script.
The owning part registers these details with Workflows' catalog:

- The workflow's name.
- The workflow's description.
- The workflow's last step.

[Contributing a workflow](contracts.md#contributing-a-workflow) defines that contribution with the
functions the script calls and the result it returns.
The script reads from each step outcome the `data` its runs handed it, such as the Modules a
scaffold created.
Workflows never reads those values.
The build wraps the script with these items:

- A `meta` block.
- The constant `WORKFLOW`, its name.
- The constant `LAST_STEP`, the last step its owner registered.
- The Claude Code step adapter, Workflows' own.

The adapter's step function's **[step agent](../glossary.json#concept.step-agent)** is a subagent
that calls the tool `workflow_step` once with the step request.
The workflow part registers that tool with the
[project MCP server](../glossary.json#concept.project-mcp-server).
The step agent waits at most 100 seconds.
It returns the step outcome the tool answered.
As long as the run is still running, the step function itself asks again.
It makes up to 200 calls for one step as a guard against a run that never ends.
Once an outcome names the step's run, the step function leaves `retry` out.
The step function treats an outcome as no answer in either case:

- The outcome names another step key.
- The outcome names a finished or lost step without a well-formed run.

The server runs the step command as a process of its own, as
[Steps in Claude Code](#steps-in-claude-code) explains.
A model copies the request.
A live headless run showed a model dropping a field of the request.
The step command then refused that request as `invalid_request`.
For that reason, after an outcome that is no answer, the step function asks again, three times
in a row at most.
It can ask again because the same key never starts a run twice.
A step still without an answer is reported lost.
The script's result carries what its agents relayed last as `relayed`, marked unverified.
It does so to keep the step command's own refusal in the error chain.
The report is relayed the same way, by one more such subagent.
A step agent only relays.
What counts is what the runs recorded.

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
workflow -> step: runs
workflow -> mode: runs in
step -> key: is named by
record -> step: lists
agent -> step: relays
script -> workflow: defines
workflow -> result: ends with
mode -> point: decides what happens at
```

## Overview

Two pictures show Workflows:

- Its place between the task level and the runs.
- How one step is carried from the script to a run and back.
[Method](../method/brownfield.md) shows the procedure of its brownfield workflow.

### Its place in the levels of work

A workflow orchestrates runs from the Claude Code session of whoever works the workspace.
Each run completes one job.
For an Operation, a run completes its job by combining these participants:

- Workers.
- Services.
- Host steps.

An execution command completes its job deterministically.
A run never starts another run.
The workflow sees only the runs' command lines and results.
It leaves these details inside the run:

- Worker prompts.
- Grants.
- Check calls.
- Audits.
- Repair loops.

Each workflow step is an ordinary run of the
[Execution runner](../glossary.json#concept.execution-runner).
For that reason, the workspace lock allows one run at a time.
For the same reason, every run receives this treatment exactly as if the task level had started it:

- It is recorded.
- It is audited.
- It is reported.

Workflows is level 3 of the [levels of work](../module.md#the-levels-of-work).
It is called from the task level only.
The task session a task was delegated to starts a workflow in the task worktree.
While the workflow runs in Claude Code's background, the task session may go on with other work.
Workflows calls only the level directly below.
Its commands start each step as a run.
Workflows never reaches a worker or a service, which only a run calls.
What goes back up is one workflow result, assembled from what the runs recorded.
In that result, every run's error chain stays whole under the workflow's own link.
Whenever no workflow fits, the task level is free to skip this level and start a run directly.
Nothing a workflow does performs any of these actions:

- Opens a task.
- Merges a task.
- Closes a task.

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

The script never runs a command itself.
Its step agents relay each step to the workflow commands through the `workflow_step` tool.
The workflow part registers that tool with the project MCP server.
The workflow commands alone perform these actions:

- Start runs.
- Keep the workflow record.
- Read the run results.
### One step, from the script to a run and back

A step passes through four participants below the task level:

- The script asks for a key.
- A step agent relays it once through the `workflow_step` tool of the project MCP server.
  The server runs the step command as a process of the server.
  The server waits at most 100 seconds.
- When the key is not yet recorded, and only then, the workflow commands start the run.
  Otherwise, the workflow commands wait for the recorded run.
- The Execution runner runs the run. The Execution runner saves its result.

While the run still runs, the script asks again with the same key. That request only waits again,
so a run that outlives many calls is still started once. The report at the end is built from the
record, not from what the agents relayed.

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
  relay: "Call the workflow_step\ntool once,\nwaiting at most 100 s,\nrelay what it answered"
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

The build renders each registered workflow as a Claude Code workflow.
[Distribution](../distribution/module.md) installs it in a project as
`.claude/workflows/concorde-<name>.js`. Claude Code offers it as the command `/concorde-<name>`.
Whoever works a workspace starts the workflow inside the bound worktree, with the workflow's
arguments as one JSON object. In Concorde, the task session starts it in its task worktree.
For `/concorde-brownfield`, one such object is `{"module": "module.shop", "mode": "no-ask"}`.
The arguments name no workspace, since every step runs in the workspace the worktree's binding
names. The workflow then runs its steps one after another. It ends with its report: the
[workflow result](../glossary.json#concept.workflow-result). The workflow result is saved in the
workflow's node as `workflow/reports/<n>.json` of the workspace folder. The workflow returns the
workflow result's status and summary. The `workflow_report` tool reads the workflow result again
at any time. [Running the brownfield
workflow](../method/brownfield.md#running-the-brownfield-workflow) follows one such workflow through
a project.

### A workflow's arguments

Every workflow takes these arguments:

- `mode`.
- `answers`.
- `retry`.
- `restart`.

Every workflow also takes its own arguments, such as `module`.
`answers` maps a step's base key, such as `survey` or `describe:module.checkout`, to the list of
every answer given for that step so far. The main agent or the developer gives those answers in
the shape of answers. A relaunch passes all of them again, not only the newest.
`retry` lists the base keys to run again after a failure.
`restart` maps a base key to a short generation label, such as `{"scaffold": "2"}`, to run that
step again whatever its outcome. For instance, this applies after the workspace was reset by
hand. The label becomes part of the [step key](../glossary.json#concept.step-key), so the step
and every later step run once more. As long as no rerun of an earlier step has superseded them,
relaunching with the same label finds the restarted runs instead of starting them again.

### The step command

```text
concorde workflow step --workflow <name> --mode <interactive|no-ask> --key <base key> [--answers <file>] [--retry] [--restart <label>] [--wait <seconds>] -- <operation or command> [arguments]
concorde workflow step --json '<step request>' [--wait <seconds>]
```

The step's key starts with the base key. When `--restart` names a generation label, `#` and that
label follow the base key. With `--answers`, `@` and a short digest of the answers follow
([req.workflows.answers-new-key](requirements.md#req.workflows.answers-new-key)). So a restarted or
answered rerun is a new step. The same label and answers find the same step again. The workspace's
**workflow lock** is `locks/workflows/<workspace>.lock` of the binding's `.concorde`. Only the step
and report commands take it. It is distinct from the
[workspace lock](../glossary.json#concept.workspace-lock) a run holds. While holding the workflow
lock, the command looks the key up among the **current steps** of the workspace's workflow record.
The current steps are those no later rerun has superseded. When the key is not there, the command
records the step as **starting**, with no run yet. The step's node is `steps/<n>-<key>/`
([the folder's exact name](contracts.md#contract.workflows.workflow-trace)). When the key is not there, the command then starts the run detached with the workspace's own
`concorde`. It places the run's node inside the
step's with `--trace-at <step node>/run`. It uses `concorde run <operation> … --detach` for an
Operation. It uses `concorde <command> … --detach` for an execution command, such as:

- `task-validation`
- `delivery`
- `scaffold`

The command tells the two kinds apart by Execution's catalogs of the installed parts' definitions.
For an answered step, it adds `--answers` with the answers written next to the workflow record.
It also adds `--input` naming the latest `ok` run of the same base key, whose decision points the
answers settle. When that base key has none, it adds no `--input`. Once the run is announced, the
command writes the run into the step. For a run that did not start, it writes the refusal instead.
It waits for the result at most `--wait` seconds (default 540). Asked again, it finds the recorded
run and only waits for it. `--retry` starts a new run for a key whose recorded run did not end
`ok`. `--json` takes the same request as one
[step request](contracts.md#contract.workflows.step-request), as the
[step agent](../glossary.json#concept.step-agent) passes it.

When a later call finds a step still starting, its step command ended between recording the step
and writing its run. The command was killed meanwhile or could not write the record
(`step_unrecorded`). That call adopts the run whose node lies in the step's node. It writes the
run into the step. The call waits as it waits for the workspace lock below when both conditions
hold:

- No run lies in the step's node.
- A run of the workspace holds the workspace lock or waits in the lobby for it.

This is because that run may be the step's. Otherwise the step's run never started. In that case,
the call ends the step's node lost. It starts the run anew under the same key. The new attempt
supersedes the starting one
([req.workflows.key-idempotent](requirements.md#req.workflows.key-idempotent)).

The command prints the [step outcome](contracts.md#contract.workflows.step). Its exit status
follows these rules:

- Once the run finishes, the command exits with status 0.
- While the run still runs, the command exits with status 3.
- When the step is lost or refused or the command cannot work at all, the command exits with
  status 1.
- When the command line or request breaks the step request contract, the command exits with
  status 2 (`invalid_request`).

So a caller that must not block longer than a few minutes simply asks again. Before it starts a run, the command waits, within the same bound, until
the workspace lock is free. This is because a workspace runs one run at a time. It waits without
holding the workflow lock. It then takes the workflow lock again and looks the key up again. When
the bound ends while the workspace lock is still held, the command starts and records nothing.
It prints an outcome with these details:

- State `running`.
- No run.
- No error.

The command exits with status 3. Asking again waits for the workspace lock again. The command also
waits for the workflow lock itself only within the bound. When the bound ends while another step or report command still holds that lock, the command
returns the same outcome. Only the launch of a run may outlast
the bound, by at most 90 seconds
([req.workflows.bounded-wait](requirements.md#req.workflows.bounded-wait)). When its recorded run
has no result and no living runner, a step is **lost**. When the runner rejects the command line
or the detached runner does not start, a step is **refused**. This includes a launcher that could
not be run or gave no answer within 90 seconds. The command then records the step without a run
and with that error. Before anything is recorded or started, the workflow record refuses either
of these cases with a `step_rejected` link over the refusal:

- A step for another workflow than the workspace's.
- A key recorded for another Operation or command.

If the record cannot record a run already started, the link is `step_unrecorded`. The link names
the run. The record leaves the step starting for the next call to adopt. A `step_rejected` step
is in no record. A `step_unrecorded` step is recorded without its run. So the script returns the
step's outcome with the report, as
[the script's result](contracts.md#contributing-a-workflow) requires.

<a id="retired-workspace"></a>

**A retired workspace.** Whoever retires a workspace, as closing a task does, holds the workflow
lock throughout these actions:

- Removing its worktree with the binding.
- Moving the workspace folder away.
- Removing the workflow lock file.

So the step and report commands write nothing into a workspace folder until both conditions hold:

- They hold the workflow lock.
- They have read the binding again.

They never take a lock file that was removed or replaced while they waited for it. Once they hold
the lock, the binding must still be the one they read when they started. Otherwise the command
refuses the step with a `workspace_retired` link. Its cause is a `Workflows (workflow lock)` link.
That cause says what the command found:

- `lock_removed`
- `binding_gone`
- `binding_untrusted`
- `binding_changed`

Nothing is started or recorded, because the workspace folder may already lie in the history, which
nothing writes. The outcome alone carries the refusal, with state `refused`. The script returns
the outcome with the report. When a step's run started and ended before retirement, the command refuses the step the same way
upon ending its node. The refusal names the run.
The run's own records went with the folder. In a retired workspace, the report command is refused
with a `component` link `workspace_retired`.

The workflow lock is a leaf. Neither command waits for another lock while holding it
([req.workflows.workflow-lock-leaf](requirements.md#req.workflows.workflow-lock-leaf)). This is
why a step waits for the workspace lock without holding the workflow lock. Therefore a close
holding the workspace lock always gets the workflow lock soon. When it merges, that close also
holds the [merge lock](../glossary.json#concept.merge-lock). Nothing waits in a circle. When a step
holds the workflow lock before the close does, the step finishes its writes before the folder
moves. When a step waits for the workflow lock until after the close, the step is refused.
Every lost or refused outcome carries an error link. A lost step's link carries the end of its
runner's output.

## How it is built

### One procedure, rendered as a Claude Code workflow

A workflow's source is a procedure that the build wraps with a step adapter. It is not a prompt
asking a model to invent the next steps. The adapter preserves:

- The selection of Operations and commands and their arguments.
- The step order.
- The branches.
- The admitted results.
- The decision points.

The adapter decides only these details:

- How a step is invoked.
- How a step is awaited.
- How the final report is requested.

The procedure therefore runs as a Claude Code workflow that starts Concorde's ordinary runs.
Workflows are rendered for Claude Code alone because the task level that starts them runs on
Claude Code. Workers run on pi or Claude Code. Workers never start a workflow.

The step agent is an adapter, not a Concorde worker. It relays a command and result. The run
decides whether to launch AI workers. Rendering a workflow does not expand Operations into Claude
Code agents. It does not expose Concorde's services to those agents. The workflow uses the same
items as runs started directly:

- The run command lines.
- The workspace lock.
- The recorded results.

The current mechanism renders authored JavaScript workflow scripts. It is not a general converter
for arbitrary platform workflows or free-form plans.

### Steps in Claude Code

The procedure lives in Claude Code's workflow runtime because that runtime runs the procedure in the
background while the task level stays responsive. That runtime has no shell, so a step agent carries
each step. That agent is a model. Every tool call by that model is meant to end within two minutes.
Unless it asks for more, a Bash call ends within that time. A run may take much longer. So a step
starts a [detached run](../glossary.json#concept.detached-run). Each call waits at most 100 seconds.
The repetition is the script's, not the model's. The reason is that a live headless run showed a
step agent that was handed a longer wait and told to repeat. That agent let its command go to the
background and returned an invented outcome instead. Because a key maps to one recorded run,
repeating a call or relaunching the whole workflow never starts a run twice. For the same reason, a
relaunched interactive workflow replays its finished steps at once.

<a id="steps-through-the-server"></a>

The detached run must also outlive the relay that started it. A step agent's own Bash does not let
it. A step may run for many minutes while each relay is one short turn. A run anchored in a relaying
agent's call lives only as long as that call. An end-to-end run on 2026-09-30 lost its survey step
this way, `step_lost` over `host_ended` with nothing in the runner's output. The worker was still
reading at that time. This happened because a sandboxed Bash call's PID namespace ends with the
call. Consequently, the namespace takes every process the call started with it
([Execution](../execution/module.md#detached-namespace)). So a step agent does not run the step
command with Bash. It calls the tool `workflow_step` with the step request as an object. The
workflow part registers that tool with the
[project MCP server](../glossary.json#concept.project-mcp-server). The server is a process of the
session beside its tools. The server runs the step command of the session's worktree. It uses the fresh process with which
it answers each call ([Distribution](../distribution/module.md)). The run
the server starts lives until it ends, whatever becomes of:

- The calls that asked for the run.
- The session.
- The server.

Later calls for the same key only wait for the run. The request travels as an object, with nothing
quoted for a shell. The report is still relayed with Bash. `concorde workflow report` starts no run.
It returns at once.

The rejected alternative anchored the run in a step agent's background Bash call. That call lives
until its command ends. The alternative would have used these steps:

- Each step's first relay would have started the step command with `run_in_background` to live as
  long as the run.
- The relay would then have asked for the outcome with a second, foreground call that only waits.
- When a later relay found the step unrecorded and no anchor alive, it would have had to start the
  anchor again.

The alternative was rejected for these reasons:

- It asks a small relay model for a two-command choreography around a background command. A live
  run saw a relay turn that very kind of instruction into an invented outcome.
- Claude Code ends a background command after at most two hours. When the session is stopped,
  Claude Code ends the session's background commands. Those endings take the run down with the
  commands.
- When its anchor ends, Claude Code wakes each step agent again. That is a turn for nothing.

The server path has none of these limits. The price is that the session's server starts a workflow's
runs rather than the session's own shell, as
[Task sessions](../coordination/task-session/module.md#workflow-runs-through-the-server) states.

The result is assembled by a deterministic command from what the runs recorded. A step agent might
drop or paraphrase what it relays. The report reads each saved run result itself. So, whatever happened in between, the chain the developer finally reads is the runs' own.
Whatever happened in between, the workflow's link is on top.

### Why Workflows keeps its own record

Workflows keeps its own record rather than writing into the task record, because nothing below the
task level knows a task. A workflow runs in any bound workspace. The facts it records are which
steps ran with which runs. Those facts are the workflow's to keep, around the runs they name. A
step nests its run because it gives the run its place before the run starts.
[Tracing](../kernel/tracing/module.md) requires this of every parent. So a workflow's trace holds
its runs without any run knowing it is a step. The task level reads the
record and the reports where they are. For the same reason the report is not appended to a
decision log. The log is the task level's. The task level decides what to copy into it.

### Inside

How Workflows is built:

```d2
workflows: Workflows {
  commands: Workflow commands {
    "src/concorde/workflows/__init__.py"
    "src/concorde/workflows/catalog.py"
    "src/concorde/workflows/cli.py"
    "src/concorde/workflows/output.py"
    "src/concorde/workflows/step.py"
    "src/concorde/workflows/report.py"
    "src/concorde/workflows/store.py"
    "src/concorde/workflows/tools.py"
  }
  scripts: Workflow scripts {
    "src/concorde/workflows/scripts/"
  }
  scripts -> commands: runs steps through
}
```

<a id="realization.workflows.commands"></a>

The **[Workflow](../glossary.json#concept.workflow) commands** realization holds:

- The workflow catalog and its rendering (`catalog.py`). When the procedure-owning part's code
  loads, that part registers these catalog details for each workflow:
  - Its name.
  - Its description.
  - Its script.
  - Its last step.
- The step output convention (`output.py`).
- The workflow record (`store.py`), with:
  - Its workflow lock.
  - Its answers.
  - Its saved reports.
  - Its step nodes.
- The `concorde workflow step` and `report` commands, which the workflow part registers with the
  `concorde` command.
- The schemas for:
  - The step outcome.
  - The step request.
  - The workflow result.
- The code of the `workflow_step` and `workflow_report` tools (`tools.py`).
- The workflow part's [part registration](../glossary.json#concept.part-registration)
  (`registration.json`), which names:
  - The command.
  - The tools.
  - The build's `renders` entry that renders every registered workflow.
  - The permission rules the workflows' step agents need.

Distribution loads every installed part's registering modules first. So the procedures the parts
contribute are registered when any of these reads the catalog:

- A step.
- A report.
- The build.

<a id="realization.workflows.scripts"></a>

The **Workflow scripts** realization holds the Claude Code step adapter (`claude.js`) the build
wraps every procedure with. It holds no procedure. Method's
[brownfield workflow](../glossary.json#concept.brownfield-workflow) script lies in Method's package,
beside the module that registers it.

<a id="realization.workflows.tests"></a>

The **Workflows tests** are under `tests/concorde/workflows/`. They use the existing-codebase fixture
`tests/concorde/support/brownfield_project.py`. The tests verify the [requirements](requirements.md)
and [scenarios](scenarios.md) through these actions:

- They run the step and report commands in a real bound task worktree against stand-in run results.
- They run one step through a real detached `task-validation` run.
- They start one run inside a PID namespace of its own to show that the run dies with that namespace.
- They run the rendered script in a small JavaScript sandbox that stands in for Claude Code's
  workflow runtime.

<a id="realization.workflows.guidance"></a>

The **Workflows guidance** is the part's sections of the
[main-session guidance](../glossary.json#concept.main-session-guidance). These sections are kept in
`prompts/guidance/workflows/`. They are registered under `guidance` in the part's registration. Wherever
the part is installed, [Distribution](../distribution/module.md#guidance-composition) composes
these sections after Coordination's working method. The sections are these:

- The project skill's and the task-session prompt's "Workflows". They cover the workflows' modes,
  their reports and the `workflow_report` and `workflow_step` tools.
- The `CLAUDE.md` block's sentence on workflows.

Each section says what happens where a part it mentions is not installed.

## What Workflows relies on

<a id="uses-tracing"></a>

**Tracing** gives the workflow and each step the shape of a
[trace node](../glossary.json#concept.trace-node). It gives the workflow lock its file under
`locks/workflows/`. The step and report commands write the workflow's and the steps' nodes through
Tracing's library. They create each step's node before starting its run inside it. This is how
Tracing nests a run below its step. Workflows relies on the
[node contract](../kernel/tracing/contracts.md#contract.tracing.node) and the
[locks](../kernel/tracing/contracts.md#locks).

<a id="uses-execution"></a>

**Execution** runs every step. The step command starts the runner detached with the workspace's own
`concorde`. With `--trace-at`, the run's node lies inside the step's node. Once the run enters its
workspace, the runner [records it](../execution/requirements.md#req.execution.trace-node) inside the step's node.
The step command reads the run identity the command
[announces only once the run exists](../execution/requirements.md#req.execution.detached-announced).
It waits for the saved [run result](../glossary.json#concept.run-result), which is the step's
outcome. Workflows relies on each run doing the following:

- Reading the same [workspace binding](../glossary.json#concept.workspace-binding) as the workflow.
- Holding the [workspace lock](../glossary.json#concept.workspace-lock) for its whole life.
- Writing exactly one result before releasing the workspace lock.
- Starting no other run.

These properties ensure that the order of the runs is the procedure's alone. Each step waits for
the lock before it starts its run. Because of these properties, each step finds the results of the
earlier steps written. A result on disk does not mean the lock is free yet.
Workflows relies on a [detached run](../glossary.json#concept.detached-run) being announced only
once its [run progress file](../glossary.json#concept.run-progress-file) exists. It also relies on
the [run store](../glossary.json#concept.run-store) keeping every run's result and progress by its
identity. This is how a later call, or a relaunched workflow, finds a run it started before.
Workflows reads results and never changes them. It relies on whoever retires a workspace holding
the workflow lock throughout these actions, as [A retired workspace](#retired-workspace) describes:

- Removing the binding.
- Moving the workspace folder.
- Removing the lock file.

The task level retires a workspace when it closes a task. When the runner rejects a command line,
such as an unknown argument, the step is refused. Its cause is the runner's message. When a detached
runner did not start, the step is refused with the `detach_failed` link as the cause.
A `detach_failed` runner
[has been ended](../execution/requirements.md#req.execution.detach-failed-ends-runner) and
[left nothing behind](../execution/requirements.md#req.execution.detach-failed-leaves-nothing).
Therefore, no run of a refused step starts later. For the same reason, a retry starts afresh.
When a run has no result and no living runner, the step is lost, with the end of the runner's
output. Once nobody [holds the run lock](../execution/requirements.md#req.execution.run-lock-held), the
[run lock](../glossary.json#concept.run-lock) tells that the run has no living runner. A run that
the runner refused, such as one for a workspace that was busy after all, is an ordinary finished
run. Its result carries that refusal.

<a id="uses-kernel"></a>

The **Kernel** gives every step the workspace it runs in. The step and report commands read the
[workspace binding](../glossary.json#concept.workspace-binding) of the worktree they start in, as
the [binding contract](../kernel/contracts.md#contract.kernel.workspace-binding) defines it.
They find there the workspace folder of the workflow's node and the `.concorde` of its locks.
When the binding breaks its contract or names another root, Workflows relies on the binding being
refused rather than trusted. Workflows also relies on whoever holds the
[workspace lock](../glossary.json#concept.workspace-lock) doing one thing at a time in the
workspace. This is why a step waits for that lock before it starts its run.

<a id="uses-commands"></a>

**Operations** and **Commands** name what a step may run. A step names an
[Operation](../glossary.json#concept.operation) of the
[Operation catalog](../glossary.json#concept.operation-catalog), started as `concorde run`.
Alternatively, it names an [execution command](../glossary.json#concept.execution-command) of the
command catalog, started as `concorde <command>`. Both catalogs list the definitions the installed
parts register. Workflows relies on them only to tell the two kinds apart. It treats their results
alike. It never looks inside an Operation or command. What it reads of a finished run's output is
the `workflow` object of the [step output convention](contracts.md#contract.workflows.step-output).
When a run's output declares nothing there, the run simply has none of the following:

- A decision point.
- A decision.
- A deviation.
- A note.

Answers reach a run through `--answers`. A run that declares decision points takes answers through
this option.
What an answer means is the run's.

<a id="uses-distribution"></a>

**Distribution** composes the [project MCP server](../glossary.json#concept.project-mcp-server)
from the [part registrations](../glossary.json#concept.part-registration) of the installed parts.
The workflow part registers its tools `workflow_step` and `workflow_report` there. It registers
its `workflow` commands with the `concorde` command. Its `registration.json` follows Distribution's
[part registration contract](../distribution/contracts.md#contract.distribution.part-registration).
The registration's `renders` entry has the build render every registered workflow. Its `install`
permissions let the workflows' step agents run without a prompt per step.
Workflows relies on the server running each call of its tools as a separate process of the current Concorde.
The process runs outside the calling session's Bash so that the run a step starts outlives the
relay. Workflows also relies on the server returning the tool's answer or refusal unchanged.
It relies on nothing else of the server. The tools' exact shapes are in the
[contracts](contracts.md#mcp-tools).
