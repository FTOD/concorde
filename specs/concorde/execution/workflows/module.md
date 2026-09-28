# Workflows

## Purpose

Workflows is level 3 of Concorde's [levels of work](../../module.md#the-levels-of-work), the top of
[Execution](../module.md): a workflow orders the runs of one bound workspace for a known procedure,
such as describing existing code in Specs, and handles their results and
[decision points](../../glossary.json#concept.decision-point). Each workflow's procedure is written
once and the build renders it into a Claude Code workflow and a pi-subagents workflow. Whoever works
a workspace, in Concorde the task level inside a task worktree, starts the workflow there; it runs
Operations and execution commands one at a time, records its steps in its own
[workflow record](../../glossary.json#concept.workflow-record) in the run store, and returns one
[workflow result](../../glossary.json#concept.workflow-result) with every step, decision,
[open question](../../glossary.json#concept.open-question) and problem, preserving each problem's
error chain. In interactive mode it stops where the developer must decide; in no-ask mode it follows
the procedure's continuation rules and reports the decisions at the end.

Workflows adds orchestration, not authority. It knows no task: it never opens, merges or closes one,
never reads or writes a [task record](../../glossary.json#concept.task-record) or a
[decision log](../../glossary.json#concept.decision-log), and every run it starts is an ordinary run
whoever works the workspace could have started itself.

## Usage

<a id="concept.workflow"></a>

A **workflow** is started in a bound [workspace](../../glossary.json#concept.workspace), never by a
worker or a run. In Concorde the task level starts it: the
[main agent](../../glossary.json#concept.main-agent) inside a task it has opened, or the
[task session](../../glossary.json#concept.task-session) the task was delegated to. It is level 3 of
the [levels of work](../../module.md#the-levels-of-work), directly above the runs: the workflow
determines which run comes next, while each run owns its workers, check calls and internal repair
rounds. A task says what work is isolated where; a workflow says how the runs in that workspace
proceed. For the [brownfield workflow](../../glossary.json#concept.brownfield-workflow), the main
agent opens a task from the primary worktree:

```text
concorde task open adopt --goal "describe the existing code in Specs" --modules module.shop
```

and then, inside the task worktree, runs the installed Claude Code workflow `/concorde-brownfield`
with the arguments `{"module": "module.shop", "mode": "no-ask"}`, or, in pi, the installed script
`.concorde/workflows/pi/brownfield.js` through pi-subagents with the task worktree as its working
directory and the same arguments. The arguments name no workspace: every command the workflow runs
starts in that worktree, whose [workspace binding](../../glossary.json#concept.workspace-binding)
names it. Every workflow takes `mode`, `answers`, `retry` and `restart`, plus its own arguments such
as `module`. `answers` maps a step's base key, such as `survey` or `describe:module.checkout`, to
the list of every answer the developer has given for that step so far, in the shape of
[answers](../../glossary.json#concept.answers); a relaunch passes all of them again, not only the
newest. `retry` lists the base keys to run again after a failure. `restart` maps a base key to a
short generation label, such as `{"scaffold": "2"}`, to run that step again whatever its outcome,
for instance after the workspace was reset by hand: the label becomes part of the
[step key](../../glossary.json#concept.step-key), so the step and every later step run once more,
and relaunching with the same label finds the restarted runs instead of starting them again, as
long as no rerun of an earlier step has superseded them. A worktree without a binding runs no
workflow: both workflow commands answer there with `binding_required`.

<a id="concept.workflow-mode"></a><a id="concept.decision-point"></a>

The **[workflow mode](../../glossary.json#concept.workflow-mode)** decides what happens at a
**decision point**, an item in a run's output that is the developer's to settle: every
[open question](../../glossary.json#concept.open-question), because only the developer knows what
behaviour is intended, and every [decision](../../glossary.json#concept.decision) of a survey that
the worker took rather than the developer, because how a project splits into Modules shapes all
later work. A code_to_spec decision, such as a concept's name, is ordinary: the workflow never stops
for it and reports it.

- **Interactive.** The developer is present, so the workflow ends right after any step that needs
  them: a step whose output has decision points its answers did not settle, with status
  `awaiting_decision` and each pending point with its options and recommendation; and any step that
  did not end `ok`, with that step's status. Whoever started it asks the developer, writes the
  answers or repairs what failed, and starts the same workflow again. Steps that finished return
  their recorded runs immediately, an answered or retried step runs again, and the workflow
  continues.
- **No-ask.** The workflow never stops for a decision point. It keeps each worker's decision, leaves
  each open question unanswered and unwritten as a promise, goes on past a
  [Module](../../glossary.json#concept.module) whose description did not end `ok`, and reports
  everything once the procedure has ended. It stops early only where the procedure cannot go on at
  all, such as a failed survey.

<a id="concept.workflow-step"></a><a id="concept.step-key"></a>

A **[workflow step](../../glossary.json#concept.workflow-step)** is one
[run](../../glossary.json#concept.run), of an [Operation](../../glossary.json#concept.operation) or
of an [execution command](../../glossary.json#concept.execution-command). The script asks for it by
a base **step key**:

```text
concorde workflow step --workflow <name> --mode <interactive|no-ask> --key <base key> [--answers <file>] [--retry] [--restart <label>] [--wait <seconds>] -- <operation or command> [arguments]
concorde workflow step --json '<step request>' [--wait <seconds>]
concorde workflow step --stdin
```

The step's key is the base key, followed by `#` and the generation label when `--restart` names one,
and with `--answers` by `@` and the first eight hexadecimal digits of the SHA-256 of the answers
list in canonical JSON (keys sorted, no whitespace), so a restarted or answered rerun is a new step
while the same label and answers find the same step again. Holding the workspace's **step lock**,
the lock on its workflow record that only the step and report commands take and that is distinct
from the [workspace lock](../../glossary.json#concept.workspace-lock) a run holds, the command looks
the key up among the **current steps** of the workspace's workflow record, those no later rerun has
superseded. When it is not there, it starts the run detached with the workspace's own `concorde`:
`concorde run <operation> … --detach` for an Operation and `concorde <command> … --detach` for an
execution command such as `task-validation`, `delivery` or `scaffold`. For an answered step it adds
`--answers` with the answers written next to the workflow record and `--input` naming the latest
`ok` run of the same base key, whose questions the answers settle; then it records the key and run.
It waits for the result at most `--wait` seconds (default 540). Asked again, it finds the recorded
run and only waits for it. `--retry` starts a new run for a key whose recorded run did not end `ok`.
`--json` takes the same request as one [step request](contracts.md#contract.workflows.step-request),
as the Claude Code [step agent](../../glossary.json#concept.step-agent) passes it, and `--stdin`
reads it from standard input and waits until the run has finished.

Starting a new run for a base key that already has a step, by `--retry`, with a new restart label
or with new answers, **supersedes** that earlier step and every step recorded after it: a
superseded step stays in the record but is never found again, so the procedure runs its later steps
anew on the changed workspace and nothing validated or delivered before the change is taken as
current. An answered step's `--input` is the latest `ok` run of its base key even when a rerun
superseded that run, since the answers still refer to its questions.

The command prints the [step outcome](contracts.md#contract.workflows.step) and exits with status 0
once the run has finished, 3 while it is still running, so a caller that must not block longer than
a few minutes simply asks again, 1 when the step is lost or refused or the command cannot work at
all, and 2 when the command line or request breaks the step request contract (`invalid_request`).
With `--stdin` it exits 0 whatever step outcome it printed, which the pi step agent passes on.
Before it starts a run, the command waits, within the same bound, until the workspace lock is free,
since a workspace runs one run at a time. When the bound ends while the lock is still held, it
starts and records nothing and prints an outcome with state `running`, no run and no error, exiting
with status 3; asking again waits for the lock again. A step is **lost** when its recorded run has
no result and no living runner. A step is **refused** when the runner rejected the command line or
the detached runner did not start: the step is then recorded without a run and with that error. A
step for another workflow than the workspace's, or a key recorded for another Operation or command,
is refused by the workflow record before anything is recorded or started, with a `step_rejected`
link over that refusal; if the record refuses a run already started, the link is `step_unrecorded`
and names the run. Such a step is in no record, so the script returns its outcome with the report.
Every lost or refused outcome carries an error link, and a lost step's link carries the end of its
runner's output.

<a id="concept.workflow-record"></a>

The **workflow record** of a workspace lies in the
[run store](../../glossary.json#concept.run-store) of the records directory its binding names, at
`runs/workflows/<workspace>/record.json`, beside the step lock, the answers passed to steps and the
saved reports. It names the workflow once, at its first step, and lists every step with its key, the
name of its Operation or command, its run or refusal, its mode and whether it was superseded, and
every report. A workspace runs at most one workflow. Only the step and report commands write the
record, and only while they hold the step lock. Whoever prepared the workspace finds it there by the
workspace's name, next to the workspace's runs.

### One procedure, two client workflows

A workflow's source is a procedure that the build adapts for the client, not a prompt asking a
model to invent the next steps. The adapters preserve the selection of Operations and commands and
their arguments, step order, branches, admitted results and decision points; they adapt only how a
step is invoked and awaited and how the final report is requested. The same procedure therefore
runs as a Claude Code workflow or a pi-subagents workflow, both starting Concorde's ordinary runs.

The platform's step agent is an adapter, not a Concorde worker: it relays a command and result,
while the run decides whether to launch AI workers. Converting a workflow does not expand Operations
into platform agents or expose Concorde's services to those agents. The two clients use the same run
command lines, the same workspace lock and the same recorded results. The current mechanism renders
authored JavaScript [workflow scripts](../../glossary.json#concept.workflow-script); it is not a
general converter for arbitrary platform workflows or free-form plans.

<a id="concept.step-agent"></a><a id="concept.workflow-script"></a>

A **workflow script** holds a workflow's procedure once, in plain JavaScript without asynchronous
helper functions, so that the same source runs in both clients. The build wraps it for each: for
Claude Code with a `meta` block and a step function whose **step agent** is a subagent that runs the
step command once, waiting at most 100 seconds, and returns the JSON it printed, while the step
function itself asks again as long as the run is still running and treats an outcome that names
another step or no real run as no answer. A model retypes the command, and a live
[headless run](../../glossary.json#concept.headless-run) showed one dropping a field of the request,
which the step command then refused as `invalid_request`; so the step function asks again after an
outcome that is no answer, three times in a row at most, since the same key never starts a run
twice. A step still without an answer is reported lost, and the script's result carries what its
agents relayed last as `relayed`, marked unverified, so that the step command's own refusal stays in
the error chain. For pi the step function's step agent is the installed command-runner agent
`concorde-step`, which runs `concorde workflow step --stdin` without a model, and the report goes
through its twin `concorde-report`, which runs `concorde workflow report --stdin`. Both read the
JSON object in the prompt pi-subagents hands them: a
[step request](contracts.md#contract.workflows.step-request) for the step, and a
[report request](contracts.md#contract.workflows.report-request) for the report, whose `lost` lists
the keys the `--lost` option would name. A step agent only relays; what counts is what the runs
recorded.

<a id="concept.workflow-result"></a>

The script ends by running `concorde workflow report [--lost <key>]`, which builds the **workflow
result** ([contract](contracts.md#contract.workflows.result)) from the workflow record and the
saved [run results](../../glossary.json#concept.run-result), never from what a step agent
relayed. Its status is, in this order of precedence:

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
[error chain](../../glossary.json#concept.error-chain) link, level `workflow`, whose causes
are the errors of the steps that stopped it, unchanged; for `awaiting_decision` its evidence names
every pending point. The report is saved beside the workflow record as `reports/<n>.json`, with a
Markdown rendering `reports/<n>.md`, and listed in the record; it is written into no decision log.
Decisions a no-ask workflow took without the developer belong in the decision log of whoever
started it, so the task level copies them from the rendering into the task's log itself. When a
step agent returned nothing, the script reports with `--lost <key>`: a key whose base key has a
current step keeps what that step's run shows, finished, still running or lost, since the record
wins, and any other is reported lost.
Anyone can run the report command in the workspace again at any time.

<a id="concept.brownfield-workflow"></a>

The **brownfield workflow** describes a project whose code came before its Specs, one Module and its
new children at a time. Its arguments add `module`, the Module to describe, usually the root.
Splitting a created child further is a new workspace running the workflow on that child, since a
workspace's step keys, `validate` and `delivery` included, belong to one procedure.

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

## Design

A workflow orchestrates runs from the client of whoever works the workspace. Each run completes one
job, an Operation by combining workers, services and host steps, an execution command
deterministically, and never starts another run. The workflow sees only their command lines and
results; it leaves worker prompts, grants, check calls, audits and repair loops inside the run. Each
workflow step is an ordinary run of the
[Execution runner](../../glossary.json#concept.execution-runner), so the workspace lock allows one
run at a time and every run is recorded, audited and reported exactly as if the task level had
started it.

### Its place in the levels of work

Workflows is level 3 of the [levels of work](../../module.md#the-levels-of-work). It is called from
the task level only: the main agent inside a task it has opened, or a task session inside the task
delegated to it, starts a workflow in the task worktree and may go on with other work while it runs
in its client's background. It calls only the level directly below: its commands start each step as
a run, and it never reaches a worker or a service, which only a run calls. What goes back up is one
workflow result, assembled from what the runs recorded, in which every run's error chain stays whole
under the workflow's own link. The task level is free to skip this level and start a run directly
whenever no workflow fits, and nothing a workflow does opens, merges or closes a task.

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

The script never runs a command itself; its step agents relay each step to the workflow commands,
which alone start runs, keep the workflow record and read the run results.

Workflows keeps its own record rather than writing into the task record, because the execution
core knows no task: a workflow runs in any bound workspace, and the facts it records, which steps
ran with which runs, are Execution's to keep, next to the runs they name. The task level reads the
record and the reports where they are. For the same reason the report is not appended to a
decision log: the log is the task level's, and it decides what to copy into it.

<a id="uses-execution"></a>

**Execution** runs every step. The step command starts the runner detached with the workspace's own
`concorde`, reads the announced run identity and waits for the saved
[run result](../../glossary.json#concept.run-result), which is the step's outcome. Workflows relies
on each run reading the same [workspace binding](../../glossary.json#concept.workspace-binding) as
the workflow, holding the [workspace lock](../../glossary.json#concept.workspace-lock) for its whole
life, writing exactly one result before releasing it and starting no other run, so the order of the
runs is the procedure's alone and each step, which waits for the lock before it starts its run,
finds the results of the earlier steps written; a result on disk does not mean the lock is free yet.
It
relies on a [detached run](../../glossary.json#concept.detached-run) being announced only once its
[run progress file](../../glossary.json#concept.run-progress-file) exists, and on the
[run store](../../glossary.json#concept.run-store) keeping every run's result and progress by its
identity, which is how a later call, or a relaunched workflow, finds a run it started before.
Workflows reads results and never changes them. A command line the runner rejects, such as an
unknown argument, and a detached runner that did not start make the step refused, with the runner's
message or `detach_failed` link as the cause; a run with no result and no living runner makes it
lost, with the end of the runner's output; a run that the runner refused, such as one for a
workspace that was busy after all, is an ordinary finished run whose result carries that refusal.

<a id="uses-operations"></a>

**Operations** names the jobs that involve a model. A workflow's steps name Operations from the
[Operation catalog](../../glossary.json#concept.operation-catalog), such as `survey`,
`code_to_spec` and `spec_review`, with their arguments; Workflows relies on each Operation
returning its output under its catalog entry's contract, which the runner checks before it saves
the result, and never starting another Operation. It never looks inside an Operation. From a
`spec_review` result it copies the output's `verdict` and its `modules`, each reviewed Module's
outcome with its findings, unchanged into the workflow result; it neither judges nor repairs them.

<a id="uses-commands"></a>

**Commands** names the deterministic runs. A step names an
[execution command](../../glossary.json#concept.execution-command) of its catalog, such
as `task-validation` or `scaffold`, by the command's own name, and the step command starts it as
`concorde <command>` instead of `concorde run`; Workflows relies on the catalog to tell the two
kinds apart and treats their results alike.

<a id="uses-validation"></a>

**Validation** provides the execution command `task-validation`. A workflow runs it before delivery;
the step outcome's `ready` is the
[readiness](../commands/validation/contracts.md#contract.validation.readiness)'s `ready`, and the
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
them from the run results by their [contracts](../operations/adoption/contracts.md) and passes
answers back through `--answers`; it never interprets what a decision means. It relies on those
contracts to tell a survey decision from a code_to_spec decision and an open question from a
settled one, since that is what makes a decision point; an output that does not follow them is the
run's failure and ends the step as its result says.

<a id="uses-scaffold"></a>

**Scaffold** provides the scaffold step between them. Its
[scaffold record](../commands/scaffold/contracts.md#contract.scaffold.record) names the Modules it
created, and the step outcome lists them with the `uses` the survey proposed among them; Workflows
relies on the record listing every Module the scaffold created, which the brownfield workflow then
describes one by one.

### Steps in the client

The procedure lives in the client's workflow runtime because both clients offer one and run it in
the background while the task level stays responsive. That runtime has no shell, so each step is
carried by a step agent. On Claude Code that agent is a model, whose Bash command ends after two
minutes unless it asks for more, while a run may take much longer. So a step starts a
[detached run](../../glossary.json#concept.detached-run) and each call waits at most 100
seconds, and the repetition is the script's, not the model's: a live headless run showed a step
agent that, handed a longer wait and told to repeat, let its command go to the background and
returned an invented outcome instead. Because a key maps to one recorded run, repeating a call or
relaunching the whole workflow never starts a run twice, and a relaunched interactive workflow
replays its finished steps at once.

The result is assembled by a deterministic command from what the runs recorded. A step agent might
drop or paraphrase what it relays; the report reads each saved run result itself. So the chain the
developer finally reads is the runs' own, with the workflow's link on top, whatever happened in
between.

One step over time, for a run that outlives the first call:

```d2 illustrative
shape: sequence_diagram
t: Task level
s: Workflow script
a: Step agent
c: Workflow commands
h: Execution runner
t -> s: start in the task worktree (mode, answers)
s -> a: step request for key "survey"
a -> c: concorde workflow step
c -> h: concorde run survey --detach
c -> a: exit 3: still running {style.stroke-dash: 3}
a -> s: outcome: running {style.stroke-dash: 3}
s -> a: ask again, same key
a -> c: concorde workflow step
c -> c: finds the recorded run, waits
h -> c: run result saved {style.stroke-dash: 3}
c -> a: step outcome {style.stroke-dash: 3}
a -> s: step outcome {style.stroke-dash: 3}
s -> c: concorde workflow report (relayed by a step agent)
c -> s: workflow result, built from the record {style.stroke-dash: 3}
s -> t: workflow result with its error chain {style.stroke-dash: 3}
```

### The brownfield procedure

Brownfield's procedure, as a step table:

| # | Step key | Run | Runs when | Ends the workflow when |
| --- | --- | --- | --- | --- |
| 1 | `survey` | Operation `survey --modules <module>` | always | not `ok`; interactive with decision points not answered |
| 2 | `scaffold` | execution command `scaffold --input <survey run>` | the survey is `ok` | not `ok` |
| 3 | `describe:<id>` | Operation `code_to_spec --modules <id>` | for each created Module, providers before the Modules that use them, then `<module>` | interactive, and either not `ok` or with open questions not answered |
| 4 | `spec_review` | Operation `spec_review --modules <module and created Modules>` | always after 3 | interactive and not `ok` |
| 5 | `validate` | execution command `task-validation` | always after 4 | not `ok`, or readiness not ready |
| 6 | `delivery` | execution command `delivery --adoption` | validation ready | — |
| 7 | — | `concorde workflow report` | always, last | — |

Created Modules are described providers first, by the `uses` the survey proposed among them, and
otherwise in the proposal's order, so that a worker describing a consumer reads its providers'
descriptions rather than their stubs. A `describe` step that did not end `ok` does not end a no-ask
workflow: the Module keeps its stub or partial description, task validation decides whether the
workspace can still be delivered, and the problem is reported. Spec review findings are reported,
not repaired, because repairing a [Spec](../../glossary.json#concept.spec) needs a decision.

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

The **[Workflow](../../glossary.json#concept.workflow) commands** realization holds the workflow
catalog (`catalog.py`: each workflow's name, description and script), the workflow record with its
step lock, answers and saved reports (`store.py`), the `concorde workflow step` and `report`
commands and the step outcome, step request and workflow result schemas.

<a id="realization.workflows.scripts"></a>

The **Workflow scripts** realization holds each workflow's procedure (`brownfield.js`), the Claude
Code and pi step adapters the build wraps it with, and the definitions of the pi command-runner
agents `concorde-step` and `concorde-report`.

<a id="realization.workflows.tests"></a>

The **Workflows tests**, under `tests/concorde/workflows/` with the existing-codebase fixture
`tests/concorde/support/brownfield_project.py`, run the step and report commands in a real bound
task worktree against stand-in run results, one step through a real detached `task-validation`
run, and run the rendered scripts with both adapters in a small JavaScript sandbox that stands in
for the client runtime, verifying the [requirements](requirements.md) and
[scenarios](scenarios.md).
