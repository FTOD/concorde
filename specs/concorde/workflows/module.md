# Workflows

## Purpose

Workflows presets tasks that follow a known procedure. A workflow is a preset task: the main agent
opens a task as usual and starts a workflow in it, and the workflow runs that task's Operations in a
fixed order, one at a time, then returns one workflow result with every step, every decision taken,
every open question and every problem, each problem with its Operation's error chain unchanged. In
interactive mode a workflow ends at the first point that needs the developer, so the main agent can
ask right away and start it again with the answers; in no-ask mode it takes those decisions itself,
keeps going and reports them all at the end. Workflows adds determinism to the order of work, not
authority: it never opens, merges or closes a task, never runs two Operations at once, and every
Operation it runs is an ordinary run the main agent could have started itself.

## Terminology

| Term | Definition |
| --- | --- |
| Workflow | A preset task: a named, fixed procedure of Operation runs in one task, written once as a client workflow script, that the main agent starts in a task it opened and that ends with one workflow result. |
| Workflow mode | Whether a workflow run is interactive, ending at the first decision point so the developer can decide, or no-ask, taking every decision itself and reporting it at the end. |
| Decision point | A decision or open question in an Operation's output that the workflow treats as the developer's to settle: every open question, and every decision of a survey. |
| Workflow step | One Operation run of a workflow, named by a step key and started and awaited through `concorde workflow step`, which returns the recorded run for a key it has seen before. |
| Step key | The name of a workflow step within its task, made of the name the script gives it and, when answers are passed, a digest of those answers. |
| Step agent | The client-side runner of a workflow step: on Claude Code a small subagent that runs `concorde workflow step` until the run has finished, on pi a command-runner agent that runs it once. |
| Workflow script | The JavaScript source of one workflow's procedure, rendered by the build into a Claude Code workflow and a pi-subagents workflow script. |
| Workflow result | The envelope `concorde workflow report` assembles from the task record and the saved Operation results: status, steps, decisions, open questions, deviations, pending decision points, problems and the error chain. |
| Brownfield workflow | The workflow that describes a project whose code came before its Specs: survey, scaffold, code_to_spec per Module, spec review, validation and delivery. |
| [Main agent](../vocabulary.md#concept.concorde.main-agent) | |
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
Operation. Workflows lives beside Tasks rather than above Operations: a task says what work is
isolated where, and a workflow says in which order that task's Operations run. For the brownfield
workflow, from the primary worktree:

```text
concorde task open adopt --goal "describe the existing code in Specs" --modules module.shop
```

and then, in Claude Code, the installed workflow `/concorde-brownfield` with the arguments
`{"task": "adopt", "module": "module.shop", "mode": "no-ask"}`, or in pi the installed script
`.concorde/workflows/pi/brownfield.js` through pi-subagents with the same arguments. The main agent
stays in the primary worktree while the workflow runs. Every workflow takes `task`, `mode`,
`answers` and `retry`, plus its own arguments such as `module`. `answers` maps a step's base key,
such as `survey` or `describe:module.checkout`, to the list of every answer the developer has given
for that step so far, in the shape of
[answers](../operations/adoption/module.md#concept.adoption.answers); a relaunch passes all of them
again, not only the newest. `retry` lists the base keys to run again after a failure.

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
concorde workflow step --task <task-id> --workflow <name> --mode <interactive|no-ask> --key <base key> [--answers <file>] [--retry] [--wait <seconds>] -- <operation> [operation arguments]
concorde workflow step --json '<step request>' [--wait <seconds>]
concorde workflow step --stdin
```

The step's key is the base key, or with `--answers` the base key followed by `@` and the first eight
hexadecimal digits of the SHA-256 of the answers list in canonical JSON (keys sorted, no
whitespace), so an answered rerun is a new step while the same answers find the same step again.
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

<a id="concept.workflows.step-agent"></a><a id="concept.workflows.script"></a>

A **workflow script** holds a workflow's procedure once, in plain JavaScript without asynchronous
helper functions, so that the same source runs in both clients. The build wraps it for each: for
Claude Code with a `meta` block and a step function whose **step agent** is a subagent that runs the
step command, runs it again while it exits with 3, and returns the JSON it printed; for pi with a
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

A workflow orders Operations but is not one: an Operation is one host process that never starts
another, and the one place that sees several Operations is the main agent. A workflow is the main
agent's own procedure, written down once, run by its client and returning to it. Each step is an
ordinary `concorde run`, so the task's lock allows one Operation at a time and every run is recorded,
audited and reported exactly as if the main agent had started it.

The procedure lives in the client's workflow runtime because both clients offer one and run it in
the background while the main agent stays responsive. That runtime has no shell, so each step is
carried by a step agent. On Claude Code that agent is a model, and a Bash command there ends after
ten minutes, while an Operation may take longer. So a step starts a [detached
run](../operations/module.md#concept.operations.detached-run) and waits at most nine minutes per
call, and the step agent repeats the same call. Because a key maps to one recorded run, repeating a
call or relaunching the whole workflow never starts an Operation twice, and a relaunched interactive
workflow replays its finished steps at once.

The result is assembled by a deterministic command from what the hosts recorded. A step agent might
drop or paraphrase what it relays; the report reads each saved Operation result itself. So the chain
the developer finally reads is the hosts' own, with the workflow's link on top, whatever happened in
between.

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
records and stand-in Operation results, one step through a real detached run, and run the rendered scripts with both adapters in a
small JavaScript sandbox that stands in for the client runtime, verifying the
[requirements](requirements.md) and [scenarios](scenarios.md).

## Relationships

```d2
workflows: Workflows
tasks: Tasks
operations: Operations
adoption: Adoption
workflows -> tasks
workflows -> operations
workflows -> adoption
```

<a id="uses-tasks"></a>

**Tasks** resolves a task to its worktree and state, and keeps the workflow's part of the task
record: the workflow's name, each step key with its Operation, run and mode, and each report. It
refuses a closed task, and Workflows relies on it to keep one Operation running per task. The
report appends to the task's decision log through it.

<a id="uses-operations"></a>

**Operations** runs every step: `concorde run --detach` starts the host, and the saved [Operation
result](../operations/module.md#concept.operations.result) is the step's outcome. Workflows reads
results and never changes them; an unknown Operation or a refused command line is refused by
`concorde run` and reported as the step's error.

<a id="uses-adoption"></a>

**Adoption** defines the decisions, open questions, answers and deviations that the brownfield
workflow counts and reports. Workflows reads them from the Operation results by their
[contracts](../operations/adoption/contracts.md) and passes answers back through `--answers`; it
never interprets what a decision means.
