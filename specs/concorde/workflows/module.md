# Workflows

## Purpose

Workflows is the third of Concorde's five levels, the upper of the two program levels, directly
above Operations. Each workflow describes a task's procedure once and the build renders it into a
Claude Code workflow and a pi-subagents workflow. The main agent opens a task and starts the
workflow in its client; the workflow orders that task's Operation runs, one at a time, and handles
their results and decision points. It returns one workflow result with every step, decision, open
question and problem, preserving each problem's Operation error chain. In interactive mode it stops where the developer must decide; in no-ask
mode it follows the procedure's continuation rules and reports the decisions at the end.
Workflows adds orchestration, not authority: it never opens, merges or closes a task, and every
Operation it runs is an ordinary run the main agent could have started itself.

## Terminology

| Term | Definition |
| --- | --- |
| Workflow | A named procedure that orders Operation runs and handles their results and decision points within one task, written once and rendered for Claude Code and pi. |
| Workflow mode | Whether a workflow run is interactive, ending at the first decision point so the developer can decide, or no-ask, taking every decision itself and reporting it at the end. |
| Decision point | A decision or open question in an Operation's output that the workflow treats as the developer's to settle: every open question, and every decision of a survey. |
| Workflow step | One Operation run of a workflow, named by a step key and started and awaited through `concorde workflow step`, which returns the recorded run for a key it has seen before. |
| Step key | The name of a workflow step within its task, made of the name the script gives it and, when answers are passed, a digest of those answers. |
| Step agent | The client-side runner of a workflow step: on Claude Code a small subagent that runs `concorde workflow step` until the run has finished, on pi a command-runner agent that runs it once. |
| Workflow script | The JavaScript source of one workflow's procedure, rendered by the build into a Claude Code workflow and a pi-subagents workflow script. |
| Workflow result | The envelope `concorde workflow report` assembles from the task record and the saved Operation results: status, steps, decisions, open questions, deviations, pending decision points, problems and the error chain. |
| Brownfield workflow | The workflow that describes a project whose code came before its Specs: survey, scaffold, code_to_spec per Module, spec review, validation and delivery. |
| [Main agent](../vocabulary.md#concept.concorde.main-agent) | |
| [Worker](../vocabulary.md#concept.concorde.worker) | |
| [Tool](../vocabulary.md#concept.concorde.tool) | |
| [Developer](../vocabulary.md#concept.concorde.developer) | |
| [Error chain](../vocabulary.md#concept.concorde.error-chain) | |
| [Task](../tasks/module.md#concept.tasks.task) | |
| [Task record](../tasks/module.md#concept.tasks.task-record) | |
| [Decision log](../tasks/module.md#concept.tasks.decision-log) | |
| [Operation](../operations/module.md#concept.operations.operation) | |
| [Operation result](../operations/module.md#concept.operations.result) | |
| [Detached run](../operations/module.md#concept.operations.detached-run) | |
| [Decision](../operations/adoption/module.md#concept.adoption.decision) | |
| [Open question](../operations/adoption/module.md#concept.adoption.open-question) | |
| [Answers](../operations/adoption/module.md#concept.adoption.answers) | |

Read Workflow and Workflow mode first. A workflow is made of workflow steps; the step agent and the
step key are how a client script runs a step safely; the workflow result is what the main agent reads.

## Usage

<a id="concept.workflows.workflow"></a>

A **workflow** is started by the main agent in a task it has opened, never by a worker or an
Operation. It is level 3 of the [five levels](../module.md#the-five-levels), directly above
Operations: the Workflow determines which Operation runs next, while each Operation owns its worker
jobs, Tool calls and internal repair rounds. Tasks has a separate role: a task says what work is
isolated where, and a workflow says how that task's Operations proceed. For the brownfield workflow, from the primary worktree:

```text
concorde task open adopt --goal "describe the existing code in Specs" --modules module.shop
```

and then, in Claude Code, the installed workflow `/concorde-brownfield` with the arguments
`{"task": "adopt", "module": "module.shop", "mode": "no-ask"}`, or in pi the installed script
`.concorde/workflows/pi/brownfield.js` through pi-subagents with the same arguments. The main agent
stays in the primary worktree while the workflow runs. Every workflow takes `task`, `mode`,
`answers`, `retry` and `restart`, plus its own arguments such as `module`. `answers` maps a step's base key,
such as `survey` or `describe:module.checkout`, to the list of every answer the developer has given
for that step so far, in the shape of
[answers](../operations/adoption/module.md#concept.adoption.answers); a relaunch passes all of them
again, not only the newest. `retry` lists the base keys to run again after a failure. `restart`
maps a base key to a short generation label, such as `{"scaffold": "2"}`, to run that step again
whatever its outcome, for instance after the task worktree was reset by hand: the label becomes
part of the step key, so the step and every later step run once more, and relaunching with the
same label finds the restarted runs instead of starting them again.

<a id="concept.workflows.mode"></a><a id="concept.workflows.decision-point"></a>

The **workflow mode** decides what happens at a **decision point**, an item in an Operation's output
that is the developer's to settle: every [open
question](../operations/adoption/module.md#concept.adoption.open-question), because only the
developer knows what behaviour is intended, and every
[decision](../operations/adoption/module.md#concept.adoption.decision) of a survey that the worker
took rather than the developer, because how a project splits into Modules shapes all later work. A
code_to_spec decision, such as a concept's name, is ordinary: the workflow never stops for it and
reports it.

- **Interactive.** The developer is present, so the workflow ends right after any step that needs
  them: a step whose output has decision points its answers did not settle, with status
  `awaiting_decision` and each pending point with its options and recommendation; and any step that
  did not end `ok`, with that step's status. The main agent asks the developer, writes the answers
  or repairs what failed, and starts the same workflow again. Steps that finished return their
  recorded runs immediately, an answered or retried step runs again, and the workflow continues.
- **No-ask.** The workflow never stops for a decision point. It keeps each worker's decision, leaves
  each open question unanswered and unwritten as a promise, goes on past a Module whose description
  did not end `ok`, and reports everything once the procedure has ended. It stops early only where
  the procedure cannot go on at all, such as a failed survey.

<a id="concept.workflows.step"></a><a id="concept.workflows.step-key"></a>

A **workflow step** is one Operation run. The script asks for it by a base **step key**:

```text
concorde workflow step --task <task-id> --workflow <name> --mode <interactive|no-ask> --key <base key> [--answers <file>] [--retry] [--restart <label>] [--wait <seconds>] -- <operation> [operation arguments]
concorde workflow step --json '<step request>' [--wait <seconds>]
concorde workflow step --stdin
```

The step's key is the base key, followed by `#` and the generation label when `--restart` names
one, and with `--answers` by `@` and the first eight hexadecimal digits of the SHA-256 of the
answers list in canonical JSON (keys sorted, no whitespace), so a restarted or answered rerun is a
new step while the same label and answers find the same step again.
Holding the task's step lock, the command looks the key up among the task's current steps. When it
is not there, it starts `concorde run <operation> --task <task-id> --detach` with the task
worktree's own `concorde`, adding `--answers` with the answers written next to the task record and,
for an answered step, `--input` naming the latest run of the same base key, whose questions the
answers settle; then it records the key and run. It waits for the result at most `--wait` seconds
(default 540). Asked again, it finds the recorded run and only waits for it. `--retry` starts a new
run for a key whose recorded run did not end `ok`. `--json` takes the same request as one
[step request](contracts.md#contract.workflows.step-request), as the Claude Code step agent passes
it, and `--stdin` reads it from standard input and waits until the run has finished.

Starting a new run for a base key that already has a step, by `--retry` or with new answers,
**supersedes** that earlier step and every step recorded after it: a superseded step stays in the
record but is never found again, so the procedure runs its later steps anew on the changed worktree and
nothing validated or delivered before the change is taken as current.

The command prints the [step outcome](contracts.md#contract.workflows.step) and exits with status 0
once the run has finished, 3 while it is still running, so a caller that must not block longer than
a few minutes simply asks again, and 1 when the step is lost or refused. Before it starts a run,
the command waits, within the same bound, until no other run of the task is still running, since a
task runs one Operation at a time. An answered step's `--input` is the latest `ok` run of its base
key even when a rerun superseded that run, since the answers still refer to its questions. A step is **lost** when its
recorded run has no result and no living host. A step is **refused** when `concorde run` rejected
the command line or the detached host did not start: the step is then recorded without a run and
with that error. A step for another workflow than the task's, a key recorded for another Operation
or a closed task is refused by Tasks before anything is recorded or started, with a `step_rejected`
link over the Tasks refusal; if Tasks refuses to record a run already started, the link is
`step_unrecorded` and names the run. Such a step is in no record, so the script returns its outcome
with the report. Every lost or refused outcome carries an error link, and a lost step's link
carries the end of its host's output.

### One procedure, two client workflows

A workflow's source is a procedure that the build adapts for the client, not a prompt asking a
model to invent the next steps. The adapters preserve Operation selection and arguments, step
order, branches, admitted results and decision points; they adapt only how a step is invoked and
awaited and how the final report is requested. The same procedure therefore runs as a Claude Code
workflow or a pi-subagents workflow, both invoking Concorde's ordinary Operations.

The platform's step agent is an adapter, not a Concorde worker: it relays a command and result,
while the Operation decides whether to launch AI workers. Converting a Workflow does not expand
Operations into platform agents or expose host Tools to those agents. The two clients use the same
Operation interfaces, task locks and recorded results. The current mechanism renders authored
JavaScript workflow scripts; it is not a general converter for arbitrary platform workflows or
free-form plans.

<a id="concept.workflows.step-agent"></a><a id="concept.workflows.script"></a>

A **workflow script** holds a workflow's procedure once, in plain JavaScript without asynchronous
helper functions, so that the same source runs in both clients. The build wraps it for each: for
Claude Code with a `meta` block and a step function whose **step agent** is a subagent that runs the
step command once, waiting at most 100 seconds, and returns the JSON it printed, while the step
function itself asks again as long as the run is still running and treats an outcome that names
another step or no real run as no answer. A model retypes the command, and a live headless run
showed one dropping a field of the request, which the step command then refused as
`invalid_request`; so the step function asks again after an outcome that is no answer, three
times in a row at most, since the same key never starts a run twice. A step still without an
answer is reported lost, and the script's result carries what its agents relayed last as
`relayed`, marked unverified, so that the step command's own refusal stays in the error chain;
for pi with a
step function whose step agent is the installed command-runner agent `concorde-step`, which runs
`concorde workflow step --stdin` without a model, and a report through its twin `concorde-report`,
which runs `concorde workflow report --stdin`. Both read the JSON object in the prompt pi-subagents
hands them. A step agent only relays; what counts is what the host recorded.

<a id="concept.workflows.result"></a>

The script ends by running `concorde workflow report --task <task-id>`, which builds the **workflow
result** ([contract](contracts.md#contract.workflows.result)) from the task record and the saved
Operation results, never from what a step agent relayed. Its status is, in this order of
precedence:

- `running` when a current step's run is still running, for a report taken before the end;
- `failed` when the procedure stopped at a step that ended `failed`, was refused or was lost;
- `blocked` when it stopped at a step that ended `blocked`, or at a validation that was not ready;
- `awaiting_decision` when an interactive run ended at decision points;
- `ok` when the procedure's last step, `delivery` in the brownfield workflow, ended `ok`, even if
  earlier steps reported problems the procedure could go past.

Every result lists, from the current steps, every decision and open question as the Operation
reported it, with its step and run; every deviation; every Spec review's verdict and findings; the
checks the survey proposed, for the developer to configure the ones they accept; and each step that
did not end `ok` as a problem with its error chain unchanged. Superseded steps are listed apart,
with their runs, and contribute nothing else. When the status is not `ok`, `error` is the workflow's
own [error chain](../vocabulary.md#concept.concorde.error-chain) link, level `workflow`, whose causes
are the errors of the steps that stopped it, unchanged; for `awaiting_decision` its evidence names
every pending point. The report also appends the result, rendered, to the task's [decision
log](../tasks/module.md#concept.tasks.decision-log) under a heading with its time, and saves it at
`.concorde/tasks/<task-id>.workflow.json`. When a step agent returned nothing, the script reports
with `--lost <key>`: a key whose current step has a finished run keeps that run's outcome, since
the record wins, and any other is reported lost. The main agent can always run the report command
itself.

<a id="concept.workflows.brownfield"></a>

The **brownfield workflow** describes a project whose code came before its Specs, one Module and its
new children at a time. Its arguments add `module`, the Module to describe, usually the root.
Splitting a created child further is a new task running the workflow on that child, since a task's
step keys, `validate` and `delivery` included, belong to one procedure.

```d2
workflow: Workflow
mode: Workflow mode
point: Decision point
step: Workflow step
key: Step key
agent: Step agent
script: Workflow script
result: Workflow result
brownfield: Brownfield workflow
workflow -> step: runs
workflow -> mode: runs in
step -> key: is named by
agent -> step: runs
script -> workflow: defines
workflow -> result: ends with
mode -> point: decides what happens at
brownfield -> workflow: is a
```

## Design

A workflow orchestrates Operations from the main agent's client. Each Operation completes one job
by combining workers, Tools and host logic and never starts another Operation. The Workflow sees
only its public inputs and results; it leaves worker prompts, grants, Tool calls, audits and
repair loops inside the Operation. A deterministic Operation remains an Operation because it owns
a whole job and its result, even when it launches no worker. Each workflow step is an ordinary
`concorde run`, so the task's lock allows one Operation at a time and every run is recorded,
audited and reported exactly as if the main agent had started it.

### Its place in the five levels

Workflows is level 3 of the [five levels](../module.md#the-five-levels). It is called from the
task level only: the main agent starts a workflow for a task it has opened, and may stay in the
primary worktree while the workflow runs in its client's background, or a task session starts one
inside the task delegated to it. It calls only the level
directly below: its commands start each step as an Operation run, and it never reaches a worker or
a Tool, which only an Operation host calls. What goes back up is one workflow result, assembled
from what the hosts recorded, in which every Operation's error chain stays whole under the
workflow's own link. The task level is free to skip this level and run an Operation directly
whenever no workflow fits, and nothing a workflow does opens, merges or closes a task: those stay
with the main agent.

```d2
main: Main session
workflows: Workflows {
  scripts: Workflow scripts
  commands: Workflow commands
  scripts -> commands: runs steps through
}
operations: Operations
workers: Workers
tasksession: Task sessions
main -> workflows
main -> operations
tasksession -> workflows
tasksession -> operations
workflows.commands -> operations: starts runs through
operations -> workers
```

The script never runs a command itself; its step agents relay each step to the Workflow commands,
which alone start Operation runs and read their results. Whoever plays the task level, the main
session or a task session, reaches Operations both through a workflow and directly, and only
Operations reaches Workers.

<a id="uses-operations"></a>

**Operations** runs every step: `concorde run --detach` starts the host, and the saved [Operation
result](../operations/module.md#concept.operations.result) is the step's outcome. Workflows relies
on each run being an ordinary run of that task, under the task's lock, recorded by its host and
answered by exactly one result, and on no Operation starting another, so the order of the runs is
the procedure's alone. Workflows reads results and never changes them; an unknown Operation or a
refused command line is refused by `concorde run` and reported as the step's error, a host that
did not start makes the step refused, and a run with no result and no living host makes it lost,
each with its error link in the workflow result.

<a id="uses-tasks"></a>

**Tasks** resolves a task to its worktree and state, and keeps the workflow's part of the task
record: the workflow's name, each step key with its Operation, run and mode, and each report. It
refuses a closed task, and Workflows relies on it to keep one Operation running per task. The
report appends to the task's decision log through it. A step Tasks refuses to record is refused
with a `step_rejected` link over the Tasks refusal before anything starts, or reported with
`step_unrecorded` naming the run when the run had already started.

### Steps in the client

The procedure lives in the client's workflow runtime because both clients offer one and run it in
the background while the main agent stays responsive. That runtime has no shell, so each step is
carried by a step agent. On Claude Code that agent is a model, whose Bash command ends after two
minutes unless it asks for more, while an Operation may take much longer. So a step starts a
[detached run](../operations/module.md#concept.operations.detached-run) and each call waits at
most 100 seconds, and the repetition is the script's, not the model's: a live headless run showed
a step agent that, handed a longer wait and told to repeat, let its command go to the background
and returned an invented outcome instead. Because a key maps to one recorded run, repeating a call
or relaunching the whole workflow never starts an Operation twice, and a relaunched interactive
workflow replays its finished steps at once.

The result is assembled by a deterministic command from what the hosts recorded. A step agent might
drop or paraphrase what it relays; the report reads each saved Operation result itself. So the chain
the developer finally reads is the hosts' own, with the workflow's link on top, whatever happened in
between.

One step over time, for a run that outlives the first call:

```d2 illustrative
shape: sequence_diagram
m: Main agent
s: Workflow script
a: Step agent
c: Workflow commands
h: Operation host
m -> s: start for the task (mode, answers)
s -> a: step request for key "survey"
a -> c: concorde workflow step
c -> h: concorde run survey --task --detach
c -> a: exit 3: still running {style.stroke-dash: 3}
a -> s: outcome: running {style.stroke-dash: 3}
s -> a: ask again, same key
a -> c: concorde workflow step
c -> c: finds the recorded run, waits
h -> c: Operation result saved {style.stroke-dash: 3}
c -> a: step outcome {style.stroke-dash: 3}
a -> s: step outcome {style.stroke-dash: 3}
s -> c: concorde workflow report (relayed by a step agent)
c -> s: workflow result, built from the record {style.stroke-dash: 3}
s -> m: workflow result with its error chain {style.stroke-dash: 3}
```

### The brownfield procedure

Brownfield's procedure, as a step table:

| # | Step key | Operation | Runs when | Ends the workflow when |
| --- | --- | --- | --- | --- |
| 1 | `survey` | `survey --modules <module>` | always | not `ok`; interactive with decision points not answered |
| 2 | `scaffold` | `scaffold --input <survey run>` | the survey is `ok` | not `ok` |
| 3 | `describe:<id>` | `code_to_spec --modules <id>` | for each created Module, providers before the Modules that use them, then `<module>` | interactive with open questions not answered, or not `ok` |
| 4 | `spec_review` | `spec_review --modules <module and created Modules>` | always after 3 | interactive and not `ok` |
| 5 | `validate` | `validate` | always after 4 | not `ok`, or readiness not ready |
| 6 | `delivery` | `delivery` | validation ready | — |
| 7 | — | `concorde workflow report` | always, last | — |

Created Modules are described providers first, by the `uses` the survey proposed among them, and
otherwise in the proposal's order, so that a worker describing a consumer reads its providers'
descriptions rather than their stubs. A `describe` step that did not end `ok` does not end a
no-ask workflow: the Module keeps its stub or partial description, validation decides whether the
task can still be delivered, and the problem is reported. Spec review findings are reported, not
repaired, because repairing a Spec needs a decision.

<a id="uses-adoption"></a>

**Adoption** provides the survey, scaffold and code_to_spec steps and defines the decisions, open
questions, answers and deviations that the brownfield workflow counts and reports. Workflows reads
them from the Operation results by their [contracts](../operations/adoption/contracts.md) and
passes answers back through `--answers`; it never interprets what a decision means. It relies on
those contracts to tell a survey decision from a code_to_spec decision and an open question from
a settled one, since that is what makes a decision point; an output that does not follow them is
the Operation's failure and ends the step as its result says.

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
  }
  scripts: Workflow scripts {
    "src/concorde/workflows/scripts/"
  }
  scripts -> commands: runs steps through
}
```

<a id="realization.workflows.commands"></a>

The **Workflow commands** realization holds the workflow catalog (`catalog.py`: each workflow's
name, description and script), the `concorde workflow step` and `report` commands and the step
outcome and workflow result schemas.

<a id="realization.workflows.scripts"></a>

The **Workflow scripts** realization holds each workflow's procedure (`brownfield.js`), the Claude
Code and pi step adapters the build wraps it with, and the definitions of the pi command-runner
agents `concorde-step` and `concorde-report`.

<a id="realization.workflows.tests"></a>

The **Workflows tests**, under `tests/concorde/workflows/` with the existing-codebase fixture
`tests/concorde/support/brownfield_project.py`, run the step and report commands against real task
records and stand-in Operation results, one step through a real detached run, and run the rendered
scripts with both adapters in a small JavaScript sandbox that stands in for the client runtime,
verifying the [requirements](requirements.md) and [scenarios](scenarios.md).
