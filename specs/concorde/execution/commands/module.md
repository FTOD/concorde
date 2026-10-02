# Commands

## Purpose

Commands is Execution's framework for the deterministic runs on a bound workspace, the
[execution commands](../../glossary.json#concept.execution-command): it holds their catalog,
assembled from the commands the installed parts register, and delegates each to the
[Module](../../glossary.json#concept.module) that provides it. In Concorde,
[Method](../../method/module.md) registers the three of its way of working: Validation's
`task-validation`, Delivery's `delivery` and Scaffold's `scaffold`. An execution command launches no
worker, yet it is a run like an Operation: the
[Execution runner](../../glossary.json#concept.execution-runner) runs it in the workspace of the
worktree it starts in, under the [workspace lock](../../glossary.json#concept.workspace-lock), and
records its [run result](../../glossary.json#concept.run-result) in the
[run store](../../glossary.json#concept.run-store), so that a workflow can take it as a step and the
task level can read it later. Work that needs a model is not an execution command: it is an
[Operation](../../glossary.json#concept.operation).

Commands provides no command of its own, never chooses the next run, asks the developer anything or
reads a [task record](../../glossary.json#concept.task-record): whoever works the workspace,
directly or through a [workflow](../../workflows/module.md), decides what runs. The other `concorde`
commands are not execution commands, even those of Execution: `run` starts an Operation, `workflow`
a [workflow step](../../glossary.json#concept.workflow-step), and the rest are registered by
Coordination, the Spec tooling, Issues, the Kernel or Distribution, each by its owner.

## Core concepts

Commands rests on one idea, a deterministic step that is nonetheless a run, and on the catalog that
lists every such step the installed parts register.

### Execution commands

<a id="concept.execution-command"></a>

Whoever works a workspace runs an
**[execution command](../../glossary.json#concept.execution-command)** inside it by name, without
`run`. An execution command exists because some steps of the work need no model, yet must be taken,
recorded and awaited like any run: a workflow takes Method's `task-validation` or `scaffold` as a
step, and the task level waits for each command and reads its evidence and
[error chain](../../glossary.json#concept.error-chain). Running them with the same runner as
Operations gives them all of that without the
[Operation catalog](../../glossary.json#concept.operation-catalog) or any worker machinery.

### The command catalog

The **command catalog** lists the execution commands the installed parts register, each with its
providing Module, what it writes and its output. A part adds a command by registering its
definition; two parts registering the same name is an installation error the catalog refuses when it
loads, naming both. The commands of Concorde's own way of working, with their providers, are
[Method's](../../method/module.md#the-operations-and-commands-it-provides).

## Overview

### Its place in the levels of work

Commands is the deterministic half of level 4 of the
[levels of work](../../module.md#the-levels-of-work), beside Operations, its AI half. Both are runs:
the task level or a workflow starts one and waits for its recorded result. Being deterministic does
not make every program an execution command: a service such as
[Check execution](../checks/module.md) is called by a step and answers it, while an execution
command is itself the run, with a workspace, a lock and a result. So Method's `task-validation` is
an execution command whose step calls Check execution, as an Operation's step does.

```d2
commands: Commands {
  command: Execution command
  table: Command table {
    "src/concorde/commands/"
  }
  table -> command: lists
}
```

```d2 illustrative
direction: right
provider: "Providing part\n(in Concorde, Method)" {
  definition: "Command definitions:\ntask-validation, delivery, scaffold"
}
commands: Commands {
  catalog: Command catalog
}
runner: Execution runner
provider.definition -> commands.catalog: registered in
runner -> commands.catalog: looks up by name
runner -> provider.definition: runs the steps of
```

## Running an execution command

Every execution command is a `concorde` command of its own, which Execution registers with
Distribution's `concorde` command for each command in the catalog:

```text
concorde <command> [--modules <id>[,<id>…]] [--input <run-id>]… [--detach] [--wait <seconds>] [command arguments]
```

`--modules`, `--input`, `--detach` and `--wait` are the [Execution runner](../runner.md)'s, and
every execution command accepts them like every run; each command adds its own arguments, such as
Delivery's `--adoption`. The run identity, the
[run progress file](../../glossary.json#concept.run-progress-file), the workspace lock and the
result are the runner's too: it keeps them for a command as for an Operation, though no worker is
launched. Every execution command needs a bound workspace: in a worktree without a binding it is
refused with `binding_required` and changes nothing. Its run result has `kind` `command`, no
`worker` and no `worker_runs`, and when it is not `ok` its error link has the level `command`.
`concorde run` naming an execution command is a command-line error that names the command to use.
How a task usually ends with Method's `task-validation` and `delivery` is Method's
([Method](../../method/module.md)).

## How it is built

### The command table

<a id="realization.commands.catalog"></a>

The **Command table** realization, `src/concorde/commands/catalog.py`, maps each command's name to
the definition its provider declares and imports that definition only when the command runs, so
running one command loads only the code its provider needs. A definition that cannot be imported is
a command-line error that names why, and no run begins. The providers' own code lives with their
Modules.

### What a provider declares

Each execution command's steps live with the Module that provides it. A provider's definition
declares the command's name, its steps, the contract of its output, the arguments of its own, and
whether its run may begin when the worktree's Specs cannot be loaded, as `task-validation`'s may
because it diagnoses those Specs itself. The runner parses those arguments with its own, refuses a
run without a binding, admits the inputs, runs the definition's admission and steps, checks the
output against its contract and wraps it in the run result. What an admitted input must be, such as
Scaffold's one survey, the provider's own steps check.

## What Commands relies on

<a id="uses-execution"></a>

**Execution**'s runner runs every execution command: it reads the
[workspace binding](../../glossary.json#concept.workspace-binding), holds the workspace lock, admits
the inputs, runs the definition's admission and steps in order and writes the run result. Commands
relies on it looking a command up in this catalog by name and refusing every command unbound; what a
command needs of its workspace it reads from the run context the runner fills.
