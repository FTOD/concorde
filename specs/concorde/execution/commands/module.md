# Commands

## Purpose

Commands is Execution's framework for deterministic runs on a bound workspace. These runs are the
[execution commands](../../glossary.json#concept.execution-command). Commands holds their catalog,
assembled from the commands the installed parts register. Commands delegates each command to the
[Module](../../glossary.json#concept.module) that provides it. In Concorde,
[Method](../../method/module.md) registers the three commands of its way of working:

- Validation's `task-validation`
- Delivery's `delivery`
- Scaffold's `scaffold`

An execution command launches no worker. Yet it is a run like an Operation. The
[Execution runner](../../glossary.json#concept.execution-runner) runs it in the workspace of the
worktree it starts in, under the [workspace lock](../../glossary.json#concept.workspace-lock).
The runner records its [run result](../../glossary.json#concept.run-result) in the
[run store](../../glossary.json#concept.run-store). This lets a workflow take the command as a step.
The recorded run result also lets the task level read the result later. Work that needs a model is
not an execution command. It is an [Operation](../../glossary.json#concept.operation).

Commands provides no command of its own. Commands never does any of these things:

- chooses the next run
- asks the developer anything
- reads a [task record](../../glossary.json#concept.task-record)

Whoever works the workspace, directly or through a [workflow](../../workflows/module.md), decides
what runs. The other `concorde` commands are not execution commands, even those of Execution.
`run` starts an Operation. `workflow` starts a
[workflow step](../../glossary.json#concept.workflow-step). Each of the rest is registered by its
owner, one of these parts:

- Coordination
- the Spec tooling
- Issues
- the Kernel
- Distribution

## Core concepts

Commands rests on one idea, a deterministic step that is nonetheless a run. It also rests on the
catalog that lists every such step the installed parts register.

### Execution commands

<a id="concept.execution-command"></a>

Whoever works a workspace runs an
**[execution command](../../glossary.json#concept.execution-command)** inside it by name, without
`run`. An execution command exists because some steps of the work need no model. Yet these steps
must be handled like any run in these ways:

- taken
- recorded
- awaited

A workflow takes Method's `task-validation` or `scaffold` as a step. The task level waits for each
command and reads its evidence and [error chain](../../glossary.json#concept.error-chain).
Running them with the same runner as Operations gives them all of that without the
[Operation catalog](../../glossary.json#concept.operation-catalog) or any worker machinery.

### The command catalog

The **command catalog** lists the execution commands the installed parts register. It gives these
details for each command:

- its providing Module
- what it writes
- its output

A part adds a command by registering its definition. Two parts registering the same name is an
installation error. The catalog refuses it when it loads, naming both parts. The
commands of Concorde's own way of working, with their providers, are
[Method's](../../method/module.md#the-operations-and-commands-it-provides).

## Overview

### Its place in the levels of work

Commands is the deterministic half of level 4 of the
[levels of work](../../module.md#the-levels-of-work), beside Operations, its AI half. Both are
runs. The task level or a workflow starts one and waits for its recorded result. Being
deterministic does not make every program an execution command. A service such as
[Check execution](../checks/module.md) is called by a step and answers it. An execution command is
itself the run, with these things:

- a workspace
- a lock
- a result

So Method's `task-validation` is an execution command whose step calls Check execution, as an
Operation's step does.

```d2
commands: Commands {
  command: Execution command
  table: Command table {
    "src/concorde/execution/commands/"
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

Every execution command is a `concorde` command of its own. Distribution composes the `concorde`
command from the [part registrations](../../glossary.json#concept.part-registration) alone.
So the part that provides an execution command also names it among the commands of its part
registration. Its entry hands the command line to the [Execution runner](../runner.md).
If no registration names a command the catalog lists, it is no `concorde` command. In Concorde,
Method's registration names these commands:

- `task-validation`
- `delivery`
- `scaffold`

```text
concorde <command> [--modules <id>[,<id>…]] [--input <run-id>]… [--detach] [--wait <seconds>] [command arguments]
```

The following arguments are the [Execution runner](../runner.md)'s:

- `--modules`
- `--input`
- `--detach`
- `--wait`

Every execution command accepts them like every run. Each command adds its own arguments, such
as Delivery's `--adoption`. For a command as for an Operation, though no worker is launched, the
runner also keeps the following:

- the run identity
- the [run progress file](../../glossary.json#concept.run-progress-file)
- the workspace lock
- the result

Every execution command needs a bound workspace. In a worktree without a binding, the command
is refused with `binding_required`. In that worktree, the command changes nothing. Its run result
has these fields:

- `kind` `command`
- no `worker`
- no `worker_runs`

When the run result is not `ok`, its error link has the level `command`. `concorde run` naming an
execution command is a command-line error that names the command to use. How a task usually ends
with Method's `task-validation` and `delivery` is Method's
([Method](../../method/module.md)).

## How it is built

### The command table

<a id="realization.commands.catalog"></a>

The **Command table** realization, `src/concorde/execution/commands/catalog.py`, holds the
command catalog. This catalog has the same shape as the [Operation catalog](../operations/module.md).
The part that provides a command registers the command's definition when the part's code loads.
The catalog holds each definition with the providing Module the definition names and with that
part. The catalog handles these errors:

- A definition naming no providing Module is refused with `invalid_definition`.
- A second definition under a registered name is refused, naming both parts.
- A command no installed part registers is a command-line error that names it. No run begins.

The providers' own code lives with their Modules.

### What a provider declares

Each execution command's steps live with the Module that provides it. A provider's definition
declares these things:

- the command's name
- its steps
- the contract of its output
- the arguments of its own
- its own admission of the run's Modules

In Method's commands, that admission checks the run's Modules against the workspace's
[Specs](../../glossary.json#concept.spec), except where the command diagnoses those Specs itself.
`task-validation` diagnoses them itself, so it begins even when those Specs cannot be loaded. The runner performs these actions:

- parses those arguments with its own
- refuses a run without a binding
- admits the inputs
- runs the definition's admission and steps
- checks the output against its contract
- wraps the output in the run result

The provider's own steps check what an admitted input must be, such as Scaffold's one survey.

## What Commands relies on

<a id="uses-execution"></a>

**Execution**'s runner runs every execution command. The runner performs these actions:

- reads the [workspace binding](../../glossary.json#concept.workspace-binding)
- holds the workspace lock
- admits the inputs
- runs the definition's admission and steps in order
- writes the run result

Commands relies on the runner looking a command up in this catalog by name. Commands also relies
on the runner refusing every command unbound. A command reads what it needs of its workspace from
the run context the runner fills.
