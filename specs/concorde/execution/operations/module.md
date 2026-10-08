# Operations

## Purpose

Operations is Execution's framework for bounded AI work in a workspace. It holds the
[Operation catalog](../../glossary.json#concept.operation-catalog). The catalog is assembled from
the [Operation](../../glossary.json#concept.operation) definitions the installed parts register.
Operations hands the [Execution runner](../../glossary.json#concept.execution-runner) each definition
it names. To complete one job, every Operation combines these elements:

- host steps
- service calls
- one or more AI workers

Every Operation ends with one [run result](../../glossary.json#concept.run-result). The result keeps
what the host steps established apart from what a worker claims. Work that needs no model is not an
Operation. It is an [execution command](../../glossary.json#concept.execution-command), registered
with [Commands](../commands/module.md).

Operations provides no Operation of its own. In Concorde, [Method](../../method/module.md)
registers every Operation. Each registration includes the steps that compute each worker's grant
from the Specs and launch the worker through the
[worker harness](../../worker-harness/module.md). A project that installs the execution part without
Method runs only the Operations some other part registers. Operations never does any of these things:

- chooses the next Operation
- runs one Operation from another
- asks the developer anything
- changes a [Spec](../../glossary.json#concept.spec) on its own initiative

Whoever works the workspace, directly or through a [workflow](../../workflows/module.md), orders
the runs. The runner handles these aspects of a run:

- how it is started
- how it is recorded
- how it is locked
- how it is reported

The runner runs an Operation's steps like any other definition's.

## Core concepts

<a id="concept.operation"></a>

An **Operation** hides the internal execution of one AI job from its caller. Method's `implement`,
for example, performs these steps:

- prepares a grant and brief
- delegates code changes to a worker through the worker harness
- uses [check results](../../glossary.json#concept.check-result) to check the changes and drive
  bounded repair rounds

The caller receives one run result without managing those rounds. Before anyone above relies on a
model's answer, a program must check it. This is why an Operation exists. The catalog therefore
holds exactly the jobs that involve a model. Deterministic jobs are execution commands.

An Operation's **definition** is what the part that provides it registers. The definition holds
these details:

- its name
- its providing [Module](../../glossary.json#concept.module)
- the [task type](../../glossary.json#concept.task-type) of its workers, or none when each run
  names it
- the [worker ids](../../glossary.json#concept.worker-id) of every worker it may launch
- its steps
- its arguments
- whether it may run [unbound](../../glossary.json#concept.unbound-run)
- whether it may change the workspace
- the runtime paths an unbound run's checkout links
- the contract of its output

[Registering a definition](registration.md) gives the exact fields of a definition and how a part
registers it. The worker ids are stable names, such as `spec_panel`'s `reviewer2` or `chair`. The
same id serves these purposes:

- keys the [worker configuration](../../glossary.json#concept.worker-configuration)
- names the worker in its [run record](../../glossary.json#concept.run-record)
- labels the run's evidence

Each worker may therefore have its own settings:

- backend
- model
- level

<a id="concept.operation-catalog"></a>

The **Operation catalog** lists the definitions of the installed parts, one per name. For each
definition, the catalog lists these details:

- its providing Module
- its task type, or that each run names it
- its worker ids
- whether it may run unbound
- whether it may change the workspace
- its output contract

Two parts registering the same name is an installation error. The catalog refuses it when it
loads, naming both parts. Only the same part may register its definition again, unchanged, which
changes nothing ([req.operations.unique-names](requirements.md#req.operations.unique-names)). The
catalog of Concorde's own Operations, with their providers, is
[Method's](../../method/module.md#the-operations-and-commands-it-provides).

## Overview

### Where Operations sits

Operations is called only through the runner. The task level calls it with `concorde run`, or a
[workflow](../../workflows/module.md) step runs the same command detached. The runner performs these
steps:

- reads the [workspace binding](../../glossary.json#concept.workspace-binding)
- holds the [workspace lock](../../glossary.json#concept.workspace-lock)
- writes the result

An Operation's steps call only downward, into the worker harness and services such as Check
execution, through the parts their provider depends on. Nothing below calls back up. A worker
never runs an Operation. A service call returns to the step that made it.

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
the run's steps produced. The caller therefore reads the claim as a claim and the evidence as fact.
The framework keeps that separation for every Operation. The runner and every step place nothing a
worker said in the result's summary or host evidence
([req.execution.claims-apart](../requirements.md#req.execution.claims-apart)). A worker's link in
the [error chain](../../glossary.json#concept.error-chain) keeps the level `worker`.

## Registering an Operation

A part registers each of its Operations when its code loads. The module that registers them is
among the `loads` of the part's [part registration](../../glossary.json#concept.part-registration).
This example registers an Operation `ask` of a part `asking`:

```python
from concorde.execution.context import Continue, Provider
from concorde.execution.operations.catalog import OPERATIONS


def ask(context):
    # Launch the worker through the worker harness, then check its answer.
    return Continue(output={"answer": "..."})


OPERATIONS.register(
    "asking",
    Provider(
        name="ask",
        task_type="understand",
        writes=False,
        steps=(ask,),
        workers=("worker",),
        module="module.asking",
    ),
)
```

After that, `concorde run ask` runs `ask`'s steps. The catalog refuses a definition without a
providing Module or without a worker id. [Registering a definition](registration.md) gives every
field, every refusal and the lookups.

## Running an Operation

Whoever works a workspace runs an Operation inside it:

```text
concorde run <operation> [--modules <id>[,<id>…]] [--input <run-id>]… [--detach] [operation arguments]
```

The run works on the workspace whose binding lies in the worktree it starts in. The
[Execution runner](../runner.md) handles these aspects, the same for every run:

- `--modules`
- `--input`
- `--detach`
- the run identity
- the [run progress file](../../glossary.json#concept.run-progress-file)
- the workspace lock
- the result

Each definition adds its own arguments, such as `--goal` for Method's `understand`. No Operation
needs the developer's consent. Method determines how Concorde's task level uses its Operations,
and in which order ([Method](../../method/module.md)).

## How it is built

The caller has the workspace's goal. A worker has only a narrow brief. Between the caller and the
worker, an Operation's host steps perform these actions:

- launch the worker
- audit what it changed
- run checks themselves
- turn the outcome into a result whose facts they produced

Until those steps check it, a worker's answer is a proposal. The run result keeps the proposal and
the checked facts apart. Deterministic work, which needs no such check, is left to execution
commands. The framework fixes only these aspects of that shape:

- the catalog
- the definition
- what every Operation owes the runner

The providing part determines these aspects:

- what a worker is given
- under which grant
- how its round is validated

The execution part therefore needs neither the Spec tooling nor the worker harness to run. A
project may therefore register Operations of its own.

<a id="realization.operations.catalog"></a>

The **Catalog** realization (`catalog.py`) holds the catalog of definitions registered with it.
Each definition has the providing Module its definition names and the part that registered it.
The realization refuses these cases
([Registering](registration.md#registering)):

- a definition that names no providing Module, with `invalid_definition`
- an Operation that declares no worker id or an empty one, with `invalid_definition`
- an execution command that does not require a binding, with `invalid_definition`
- a second definition under a registered name, with `duplicate_definition`, unless the same part
  registers an equal definition again

It also gives the command catalog of [Commands](../commands/module.md) its shape. Every Operation's
own code lives with the part that registers it. Examples include the prompt and brief helpers of
Method's worker-backed providers (`src/concorde/method/prompts.py`). The registering part specifies
the Operation's behaviour. For Method's Operations, [Method](../../method/module.md#the-standard-worker-sequence)
and its children specify that behaviour.

<a id="realization.operations.tests"></a>

The **Operations tests**, under `tests/concorde/operations/`, exercise the catalogs at their seam
with the runner. They register stand-in definitions and run them in a real task worktree.

### What Operations relies on

<a id="uses-execution"></a>

**Execution**'s runner runs every Operation. The runner performs these actions
([Runner](../runner.md#runner)):

- reads the workspace binding
- holds the workspace lock
- admits the inputs
- runs the definition's admission and steps in order
- writes the run result

What the runner takes from a definition is
[What a definition gives the runner](../runner.md#what-a-definition-gives-the-runner). The runner
wraps every Operation's output in the
[run result contract](../contracts.md#contract.execution.run-result). Every Operation's result
follows these Execution requirements in particular:

- [req.execution.claims-apart](../requirements.md#req.execution.claims-apart)
- [req.execution.error-when-not-ok](../requirements.md#req.execution.error-when-not-ok)
- [req.execution.reasons](../requirements.md#req.execution.reasons)
- [req.execution.error-detail](../requirements.md#req.execution.error-detail)

An Operation relies on the runner for everything about the run that is not the job itself. The
Operation knows nothing of tasks. The Operation reads what it needs of its workspace from the run
context the runner fills from the binding. Examples include the goal a worker is briefed with or
the base a review compares against.
