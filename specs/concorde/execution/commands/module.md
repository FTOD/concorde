# Commands

## Purpose

Commands is how deterministic work on a bound workspace is run and recorded. It holds the catalog of
[execution commands](../../glossary.json#concept.execution-command) and delegates each to the
[Module](../../glossary.json#concept.module) that provides it: Validation's `task-validation`,
Delivery's `delivery` and Scaffold's `scaffold`. An execution command launches no worker, yet it is
a run like an Operation: the [Execution runner](../../glossary.json#concept.execution-runner) runs
it in the workspace of the worktree it starts in, under the
[workspace lock](../../glossary.json#concept.workspace-lock), and records its
[run result](../../glossary.json#concept.run-result) in the
[run store](../../glossary.json#concept.run-store), so that a workflow can take it as a step and a
later run can cite it. Work that needs a model is not an execution command: it is an
[Operation](../../glossary.json#concept.operation).

Commands never chooses the next run, asks the developer anything or reads a
[task record](../../glossary.json#concept.task-record): whoever works the workspace, directly or
through a [workflow](../workflows/module.md), decides what runs. The other `concorde` commands are
not execution commands, even those of Execution: `run` starts an Operation, `workflow` a
[workflow step](../../glossary.json#concept.workflow-step), `configure-workers` changes the worker
configuration, and the rest belong to Coordination, Spec tooling, Issues or Distribution, as
[Distribution's command table](../../glossary.json#concept.command-line-interface) shows.

## Usage

<a id="concept.execution-command"></a>

Whoever works a workspace runs an **execution command** inside it by name, without `run`:

```text
concorde task-validation [--modules <id>[,<id>…]] [--input <run-id>]… [--detach]
concorde delivery        [--adoption] [--detach]
concorde scaffold        --input <survey run> [--detach]
```

`--modules`, `--input`, `--detach`, the run identity, the
[progress file](../../glossary.json#concept.progress-file), the workspace lock and the result are
the [Execution runner](../runner.md)'s, the same for every run; each command adds its own arguments.
Every execution command needs a bound workspace: in a worktree without a binding it is refused with
`binding_required` and changes nothing. Its run result has `kind` `command`, no `worker` and no
`worker_runs`, and when it is not `ok` its error link has the level `command`. `concorde run` naming
an execution command is a command-line error that names the command to use.

<a id="concept.command-catalog"></a>

The **[command catalog](../../glossary.json#concept.command-catalog)** of this version:

| Command | Provider | Writes | Output |
| --- | --- | --- | --- |
| `task-validation` | [Validation](validation/module.md) | nothing in the workspace | a [readiness](validation/contracts.md#contract.validation.readiness) |
| `delivery` | [Delivery](delivery/module.md) | one [delivery commit](../../glossary.json#concept.delivery-commit) on the bound branch | the [delivery commit](delivery/contracts.md#contract.delivery.output) |
| `scaffold` | [Scaffold](scaffold/module.md) | the new child Modules' Specs, the parent's entry and the registry | a [scaffold record](scaffold/contracts.md#contract.scaffold.record) |

A task usually ends with `task-validation` as a preview and `delivery`, which decides the readiness
again itself. For a project whose code came before its Specs, `scaffold` sits between the
Operations `survey` and `code_to_spec`, usually run by the
[brownfield workflow](../workflows/module.md).

## Design

An execution command exists because some steps of the work need no model, yet must be taken, cited
and awaited like any run: a workflow takes `task-validation` or `scaffold` as a step, Delivery cites
the runs that led to it, and the task level reads each command's evidence and
[error chain](../../glossary.json#concept.error-chain). Running them with the same runner as
Operations gives them all of that without the
[Operation catalog](../../glossary.json#concept.operation-catalog) or any worker machinery.

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
  catalog: Command catalog
  command: Execution command
  table: Command table {
    "src/concorde/commands/"
  }
  validation: Validation
  delivery: Delivery
  scaffold: Scaffold
  catalog -> command: lists
  table -> catalog: realizes
}
```

<a id="realization.commands.catalog"></a>

The **Command table** realization, `src/concorde/commands/catalog.py`, maps each command's name to
the definition its provider declares and imports that definition only when the command runs. The
providers' own code lives with their Modules.

### The providers

Each execution command's steps live with the Module that provides it. A provider supplies its steps
and the contract of its output; the runner runs those steps, checks the output against its contract
and wraps it in the run result.

<a id="contains-validation"></a>

**Validation** provides `task-validation`, which decides whether the bound workspace is ready to
deliver and binds that readiness to the inputs it examined. It writes nothing in the workspace.

<a id="contains-delivery"></a>

**Delivery** provides `delivery`, the only run that commits: it decides the readiness again with
Validation's steps and commits the workspace's changes with their evidence on the bound branch. Its
delivery commits are the only record of a delivery.

<a id="contains-scaffold"></a>

**Scaffold** provides `scaffold`, which applies one
[decomposition proposal](../../glossary.json#concept.decomposition-proposal) of an `ok`
[survey](../../glossary.json#concept.survey) run and creates the proposed child Modules as honest
stubs. Adding Modules is a project-level change a worker may never make, so deterministic code makes
it from the proposal a worker only suggested.

### What Commands relies on

<a id="uses-execution"></a>

**Execution**'s runner runs every execution command: it reads the
[workspace binding](../../glossary.json#concept.workspace-binding), holds the workspace lock, admits
the Modules and inputs, runs the steps in order and writes the run result. Commands relies on it
looking a command up in this catalog by name and refusing every command unbound; what a command
needs of its workspace it reads from the run context the runner fills.
