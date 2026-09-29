# Commands

## Purpose

Commands names the deterministic runs Concorde offers on a bound workspace, the
[execution commands](../../glossary.json#concept.execution-command): it holds their catalog and
delegates each to the [Module](../../glossary.json#concept.module) that provides it: Validation's
`task-validation`, Delivery's `delivery` and Scaffold's `scaffold`. An execution command launches no
worker, yet it is a run like an Operation: the
[Execution runner](../../glossary.json#concept.execution-runner) runs it in the workspace of the
worktree it starts in, under the [workspace lock](../../glossary.json#concept.workspace-lock), and
records its [run result](../../glossary.json#concept.run-result) in the
[run store](../../glossary.json#concept.run-store), so that a workflow can take it as a step and the
task level can read it later. Work that needs a model is not an execution command: it is an
[Operation](../../glossary.json#concept.operation).

Commands never chooses the next run, asks the developer anything or reads a
[task record](../../glossary.json#concept.task-record): whoever works the workspace, directly or
through a [workflow](../workflows/module.md), decides what runs. The other `concorde` commands are
not execution commands, even those of Execution: `run` starts an Operation, `workflow` a
[workflow step](../../glossary.json#concept.workflow-step), and the rest belong to Coordination, Spec tooling, Issues or Distribution, as the
table of subcommands of the
command-line interface shows.

## Core concepts

Commands rests on one idea, a deterministic step that is nonetheless a run, and on the fixed catalog
that lists every such step.

### Execution commands

<a id="concept.execution-command"></a>

Whoever works a workspace runs an
**[execution command](../../glossary.json#concept.execution-command)** inside it by name, without
`run`. An execution command exists because some steps of the work need
no model, yet must be taken, recorded and awaited like any run: a workflow takes `task-validation`
or `scaffold` as a step, and the task level waits for each command and reads its evidence and
[error chain](../../glossary.json#concept.error-chain). Running them with the
same runner as Operations gives them all of that without the
[Operation catalog](../../glossary.json#concept.operation-catalog) or any worker machinery.

### The command catalog

The **command catalog** is the fixed table, in
Concorde's code, of the execution commands and their providers. A project cannot extend it: a new
execution command is a change to Concorde, a new row and a definition in its providing Module. The
catalog of this version:

| Command | Provider | Writes | Output |
| --- | --- | --- | --- |
| `task-validation` | [Validation](validation/module.md) | nothing in the workspace | a [readiness](validation/contracts.md#contract.validation.readiness) |
| `delivery` | [Delivery](delivery/module.md) | one [delivery commit](../../glossary.json#concept.delivery-commit) on the bound branch | the [delivery commit](delivery/contracts.md#contract.delivery.output) |
| `scaffold` | [Scaffold](scaffold/module.md) | the new child Modules' Specs, the parent's entry and the registry | a [scaffold record](scaffold/contracts.md#contract.scaffold.record) |

For a project whose code came before its Specs, `scaffold` sits between the Operations `survey` and
`code_to_spec`, usually run by the [brownfield workflow](../workflows/module.md).

## Overview

Two pictures show Commands: its place beside Operations among the runs, and the two execution
commands that usually end a task.

### Its place in the levels of work

Commands is the deterministic half of level 4 of the
[levels of work](../../module.md#the-levels-of-work), beside Operations, its AI half. Both are runs:
the task level or a workflow starts one and waits for its recorded result. Being deterministic does
not make every program an execution command: a service such as
[Check execution](../checks/module.md) is called by a step and answers it, while an execution
command is itself the run, with a workspace, a lock and a result. So `task-validation` is an
execution command whose step calls Check execution, as an Operation's step does.

```d2
commands: Commands {
  command: Execution command
  table: Command table {
    "src/concorde/commands/"
  }
  validation: Validation
  delivery: Delivery
  scaffold: Scaffold
  table -> command: lists
}
```

### A task's last two runs

A task usually ends with two execution commands. In a task worktree bound to the workspace
`severity` on the branch `concorde/severity`, once its changes are made:

```text
concorde task-validation
concorde delivery
```

`task-validation` is the preview: it decides the workspace's
[readiness](validation/contracts.md#contract.validation.readiness) and writes nothing. When the
workspace is ready its run result has status `ok` and a readiness with `ready` true; otherwise it
is `blocked` and names every blocking finding at once, to repair before trying again. `delivery`
then decides the readiness again itself rather than trusting the preview and, when it is ready,
creates the [delivery commit](../../glossary.json#concept.delivery-commit)
`concorde: deliver severity` on `concorde/severity` and returns that commit as its output. Both
runs are recorded in the [run store](../../glossary.json#concept.run-store).

```d2 illustrative
direction: right
work: "Changes made\nin the task worktree"
validate: "concorde task-validation\npreview, writes nothing"
repair: "Repair every\nblocking finding"
deliver: "concorde delivery\ndecides the readiness again"
commit: "Delivery commit\nconcorde: deliver severity"
work -> validate
validate -> deliver: "ok, ready"
validate -> repair: "blocked" {style.stroke-dash: 3}
repair -> validate
deliver -> commit: ready
```

## Running an execution command

The execution commands and their arguments:

```text
concorde task-validation [--modules <id>[,<id>…]] [--input <run-id>]… [--detach]
concorde delivery        [--adoption] [--detach]
concorde scaffold        --input <survey run> [--detach]
```

`--modules`, `--input` and `--detach` are the [Execution runner](../runner.md)'s, and every
execution command accepts them like every run, even where a line above leaves them out; each command
adds its own arguments, such as `--adoption`. The run identity, the
[run progress file](../../glossary.json#concept.run-progress-file), the workspace lock and the
result are the runner's too: it keeps them for a command as for an Operation, though no worker is
launched. Every execution command needs a bound workspace: in a worktree without a binding it is
refused with `binding_required` and changes nothing. Its run result has `kind` `command`, no
`worker` and no `worker_runs`, and when it is not `ok` its error link has the level `command`.
`concorde run` naming an execution command is a command-line error that names the command to use.

## How it is built

### The command table

<a id="realization.commands.catalog"></a>

The **Command table** realization, `src/concorde/commands/catalog.py`, maps each command's name to
the definition its provider declares and imports that definition only when the command runs, so
running one command loads only the code its provider needs. A definition that cannot be imported is
a command-line error that names why, and no run begins. The providers' own code lives with their
Modules.

### The providers

Each execution command's steps live with the Module that provides it. A provider's definition
declares the command's name, its steps, the contract of its output, the arguments of its own, such
as Delivery's `--adoption`, and whether its run may begin when the worktree's Specs cannot be
loaded, as `task-validation`'s may because it diagnoses those Specs itself. The runner parses those
arguments with its own, refuses a run without a binding, admits the inputs, runs the steps, checks
the output against its contract and wraps it in the run result. What an admitted input must be,
such as Scaffold's one survey, the provider's own steps check.

<a id="contains-validation"></a>

**Validation** provides `task-validation`, which decides whether the bound workspace is ready to
deliver and binds that readiness to the inputs it examined. It writes nothing in the workspace.

<a id="contains-delivery"></a>

**Delivery** provides `delivery`, the only run that commits: it decides the readiness again with
Validation's steps and commits the workspace's changes on the bound branch. Its
delivery commits are the only record of a delivery.

<a id="contains-scaffold"></a>

**Scaffold** provides `scaffold`, which applies one
[decomposition proposal](../../glossary.json#concept.decomposition-proposal) of an `ok`
survey run and creates the proposed child Modules as stubs
whose entries state the survey's purpose and say plainly that their behaviour and design are not
yet specified. Adding Modules is a project-level change a worker may never make, so deterministic
code makes it from the proposal a worker only suggested.

## What Commands relies on

<a id="uses-execution"></a>

**Execution**'s runner runs every execution command: it reads the
[workspace binding](../../glossary.json#concept.workspace-binding), holds the workspace lock, admits
the Modules and inputs, runs the steps in order and writes the run result. Commands relies on it
looking a command up in this catalog by name and refusing every command unbound; what a command
needs of its workspace it reads from the run context the runner fills.
