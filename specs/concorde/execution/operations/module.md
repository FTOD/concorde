# Operations

## Purpose

Operations is Execution's framework for bounded AI work in a workspace. It holds the
[Operation catalog](../../glossary.json#concept.operation-catalog), assembled from the
[Operation](../../glossary.json#concept.operation) definitions the installed parts register, and
hands the [Execution runner](../../glossary.json#concept.execution-runner) each definition it names.
Every Operation combines host steps, service calls and one or more AI workers to complete one job,
and ends with one [run result](../../glossary.json#concept.run-result) that keeps what the host
steps established apart from what a worker claims. Work that needs no model is not an Operation: it
is an [execution command](../../glossary.json#concept.execution-command), registered with
[Commands](../commands/module.md).

Operations provides no Operation of its own. In Concorde, [Method](../../method/module.md) registers
every Operation, with the steps that compute each worker's grant from the Specs and launch the
worker through the [worker harness](../../worker-harness/module.md); a project that installs the
execution part without Method runs only the Operations some other part registers. Operations never
chooses the next Operation, runs one Operation from another, asks the developer anything or changes
a [Spec](../../glossary.json#concept.spec) on its own initiative: whoever works the workspace,
directly or through a [workflow](../../workflows/module.md), orders the runs. How a run is started,
recorded, locked and reported is the runner's, which runs an Operation's steps like any other
definition's.

## Core concepts

<a id="concept.operation"></a>

An **Operation** hides the internal execution of one AI job from its caller. Method's `implement`,
for example, prepares a grant and brief, delegates code changes to a worker through the worker
harness, and uses [check results](../../glossary.json#concept.check-result) to check the changes and drive bounded repair rounds; the caller
receives one run result without managing those rounds. An Operation exists because a model's answer
must be checked by a program before anyone above relies on it, so the catalog holds exactly the jobs
that involve a model; deterministic jobs are execution commands.

An Operation's **definition** is what the part that provides it registers: its name, its providing
[Module](../../glossary.json#concept.module), the [task type](../../glossary.json#concept.task-type)
of its workers, the [worker ids](../../glossary.json#concept.worker-id) of every worker it may
launch, its steps, its arguments, whether it may run [unbound](../../glossary.json#concept.unbound-run),
whether it may change the workspace, the runtime paths an unbound run's checkout links, and the
contract of its output. The worker ids are stable names, such as `spec_panel`'s `reviewer2` or
`chair`: the same id keys the [worker configuration](../../glossary.json#concept.worker-configuration),
names the worker in its [run record](../../glossary.json#concept.run-record) and labels the run's evidence, so each worker may have its own
backend, model and level.

<a id="concept.operation-catalog"></a>

The **Operation catalog** lists the definitions of the installed parts, one per name, with each
one's providing Module, task type, worker ids, whether it may run unbound, whether it may change the
workspace and its output contract. Two parts registering the same name is an installation error the
catalog refuses when it loads, naming both. The catalog of Concorde's own Operations, with their
providers, is [Method's](../../method/module.md#the-operations-and-commands-it-provides).

## Overview

### Where Operations sits

Operations is called only through the runner: by the task level with `concorde run`, or by a
[workflow](../../workflows/module.md) step that runs the same command detached. The runner reads the
[workspace binding](../../glossary.json#concept.workspace-binding), holds the
[workspace lock](../../glossary.json#concept.workspace-lock) and writes the result; an Operation's
steps call only downward, into the worker harness and services such as Check execution, through the
parts their provider depends on. Nothing below calls back up: a worker never runs an Operation, and
a service call returns to the step that made it.

```d2 illustrative
provider: "Providing part\n(in Concorde, Method)" {
  definition: Operation definition
}
operations: Operations {
  catalog: Operation catalog
}
runner: Execution runner
harness: Worker harness
checks: Check execution
provider.definition -> operations.catalog: registered in
runner -> operations.catalog: looks up
runner -> provider.definition: runs the steps of
provider.definition -> harness: "launches workers through"
provider.definition -> checks: "runs checks through"
```

### Claims and evidence

A worker-backed run's result carries the worker's own
[worker result](../../glossary.json#concept.worker-result) unchanged in `worker`, beside the evidence
the run's steps produced, so the caller reads the claim as a claim and the evidence as fact. The
framework keeps that separation for every Operation: the runner and every step place nothing a
worker said in the result's summary or host evidence
([req.execution.claims-apart](../requirements.md#req.execution.claims-apart)), and a worker's link
in the [error chain](../../glossary.json#concept.error-chain) keeps the level `worker`.

## Running an Operation

Whoever works a workspace runs an Operation inside it:

```text
concorde run <operation> [--modules <id>[,<id>…]] [--input <run-id>]… [--detach] [operation arguments]
```

The run works on the workspace whose binding lies in the worktree it starts in; `--modules`,
`--input`, `--detach`, the run identity, the
[run progress file](../../glossary.json#concept.run-progress-file), the workspace lock and the
result are the [Execution runner](../runner.md)'s, the same for every run. Each definition adds its
own arguments, such as `--goal` for Method's `understand`. No Operation needs the developer's
consent. How Concorde's task level uses its Operations, and in which order, is Method's
([Method](../../method/module.md)).

## How it is built

Between the caller, which has the workspace's goal, and a worker, which has only a narrow brief, an
Operation's host steps launch the worker, audit what it changed, run checks themselves, and turn the
outcome into a result whose facts they produced. A worker's answer is a proposal until those steps
have checked it, and the run result keeps the two apart. Deterministic work, which needs no such
check, is left to execution commands. The framework fixes only that shape: the catalog, the
definition and what every Operation owes the runner. What a worker is given, under which grant and
how its round is validated is the providing part's, so that the execution part needs neither the
Spec tooling nor the worker harness to run, and a project may register Operations of its own.

<a id="realization.operations.catalog"></a>

The **Catalog** realization (`catalog.py`) holds the catalog: the definitions registered with it,
each with the providing Module its definition names and the part that registered it, and the
refusal with `invalid_definition` of a definition that names no providing Module or of an Operation
that declares no worker id, and with `duplicate_definition` of a second definition under a
registered name. It also gives the command catalog of [Commands](../commands/module.md) its shape. Every
Operation's own code, such as the prompt and brief helpers of Method's worker-backed providers
(`src/concorde/method/prompts.py`), lives with the part that registers it, and its behaviour is
specified by that part, for Method's by [Method](../../method/module.md#the-standard-worker-sequence)
and its children.

<a id="realization.operations.tests"></a>

The **Operations tests**, under `tests/concorde/operations/`, register stand-in definitions and run
them through the runner in a real task worktree, show the catalog refusing a second definition of
one name, and show that the first step Method puts in every Operation checks all its workers
against the [model map](../../glossary.json#concept.model-map) before any of the provider's own steps; Method's worker-backed scenarios are
verified with the runner's tests.

### What Operations relies on

<a id="uses-execution"></a>

**Execution**'s runner runs every Operation: it reads the workspace binding, holds the workspace
lock, admits the inputs, runs the definition's admission and steps in order and writes the run
result. An Operation relies on it for everything about the run that is not the job itself, and
knows nothing of tasks; what it needs of its workspace, such as the goal a worker is briefed with or
the base a review compares against, it reads from the run context the runner fills from the
binding.
