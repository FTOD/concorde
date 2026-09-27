# Scaffold

## Purpose

Scaffold creates the child Modules a survey proposed. It provides the execution command
`concorde scaffold`: given one decomposition proposal from an `ok`
[survey](../../operations/adoption/module.md#concept.adoption.survey) of the same workspace, it
writes each proposed child as an honest stub Module, narrows the parent's realizations to what no
child took, adds the children to the parent's `contains` and to the registry, and returns a record
of exactly what it wrote. It is the step between Adoption's two Operations, `survey` and
`code_to_spec`, for a project whose code came before its Specs; the task level or the
[brownfield workflow](../../workflows/module.md) runs it. Scaffold launches no worker, never
decides which Modules to create — the proposal does — and never describes a Module beyond the
survey's purpose, configures a check or changes code.

## Terminology

| Term | Definition |
| --- | --- |
| Scaffold record | The output of a scaffold: the Modules and documents it created, the vendored paths it made external inclusions, and the parent's realization entries before and after. |
| [Execution command](../module.md#concept.commands.execution-command) | |
| [Workspace](../../module.md#concept.execution.workspace) | |
| [Run result](../../module.md#concept.execution.run-result) | |
| [Survey](../../operations/adoption/module.md#concept.adoption.survey) | |
| [Decomposition proposal](../../operations/adoption/module.md#concept.adoption.decomposition) | |
| [Module](../../../vocabulary.md#concept.concorde.module) | |
| [Worker](../../../vocabulary.md#concept.concorde.worker) | |
| [Error chain](../../../vocabulary.md#concept.concorde.error-chain) | |
| [File transaction](../../../spec-tooling/spec/module.md#concept.spec.file-transaction) | |
| [Registry](../../../spec-tooling/spec/module.md#concept.spec.registry) | |

## Usage

The task level runs the command in a task worktree after a survey of the Module to split, usually
the root, has ended `ok`, and before `code_to_spec` describes the new Modules:

```text
concorde scaffold --input <survey run> [--detach]
```

It is an [execution command](../module.md#concept.commands.execution-command): the
[Execution runner](../../runner.md) runs it in the workspace whose
[binding](../../module.md#concept.execution.workspace-binding) lies in the worktree it starts in and
records it in the run store, so that a workflow takes it as a step and its result records exactly
what it wrote. In a worktree without a binding it is refused with `binding_required` and writes
nothing. It admits exactly one input, an `ok` survey of the same workspace; the runner refuses a
survey of another workspace, or an unbound one, before the first step.

<a id="concept.scaffold.record"></a>

For each proposed child it writes an entry `module.md` and its metadata in a folder named after the
child's identity, next to the parent's entry, stating the survey's purpose, a realization binding
the proposed entries, and the proposed `uses`, with every other section saying honestly that it is
not specified yet. It adds the children to the parent's `contains` with one explaining paragraph
each, removes the children's paths from the parent's realizations and adds the registry records.
Vendored code leaves the parent's realizations too, but never becomes a Module: it becomes an
`includes` of kind `external` of the Module that uses it, which that Module reads and nobody
describes or reviews as the project's code, as the Protocol treats pinned third-party material. It
never configures the proposed checks: a check is a command the host later runs, and a command a
model chose after reading code nobody vouched for must be accepted by the developer first, so the
checks stay a proposal the workflow reports. Everything is written in one
[file transaction](../../../spec-tooling/spec/module.md#concept.spec.file-transaction) that is kept
only if validation finds no new error.

The [run result](../../module.md#concept.execution.run-result), of kind `command` with no worker,
carries the **scaffold record** ([contract](contracts.md#contract.scaffold.record)). It is `blocked`
with `stale_proposal` when the proposal no longer fits the worktree, and `failed` when the input is
not one survey or the files would add a structural error; the error chain names every mismatch or
finding as a cause. Every code is in the [error table](contracts.md#errors).

## Design

Adding Modules is the project-level step the Protocol reserves for the registry and the parent's
`contains`, which no worker's write set includes. So a survey worker only proposes the children,
and this deterministic command applies the proposal: anyone can check what it wrote against the
proposal, and it is an execution command rather than an Operation because no model is involved.

Scaffold writes where it can decide by rules alone. A child's folder is the parent entry's folder
plus the child identity's last segment. The parent keeps every path its realizations covered that no
child took. A directory entry of the parent that contains a child's entry is replaced by the entries
below it that no child took: a directory stays one entry when no child took anything inside it, and
a file is listed exactly. A directory that would bind no file, such as an empty one or one holding
only skipped files, and a symbolic link are left out, as a directory entry never bound them.
Conversely a file a child's directory entry does not bind, such as a dot file the parent binds
exactly because its own directory entry skips it, stays with the parent. So no path is bound by
both parent and child unless the proposal deliberately gives one path to several children.

<a id="realization.scaffold.command"></a>

The **Scaffold command** realization, `src/concorde/scaffold/`, declares the `SCAFFOLD` execution
command, which launches no worker:

| # | Step | Actor | Stops the run when |
| --- | --- | --- | --- |
| 1 | Admit exactly one `ok` survey of the same workspace as input | host | none or several, or not a survey (`failed`, `invalid_request`) |
| 2 | Validate the worktree as a baseline and check the proposal against it again | host, Spec core | the proposal no longer fits (`blocked`, `stale_proposal`) |
| 3 | Compute every file change: child entries, parent entry and realization, registry | host | a target file already exists (`blocked`, `stale_proposal`) |
| 4 | Apply them as one file transaction, kept only if validation finds no new error | host, Spec core | a new error (`failed`, `scaffold_invalid`), nothing kept |
| 5 | Return the run result with the scaffold record | host | — |

Its tests, under `tests/concorde/scaffold/`, run a survey and the scaffold in a bound task worktree
of a small existing codebase with a fake worker, verifying the [requirements](requirements.md) and
[scenarios](scenarios.md).

```d2
scaffold: Scaffold {
  command: Scaffold command {
    "src/concorde/scaffold/"
    "tests/concorde/scaffold/"
  }
  record: Scaffold record
  command -> record: produces
}
```

### Outside

<a id="uses-execution"></a>

**Execution**'s runner runs the command: it reads the workspace binding, holds the workspace lock,
admits the `--input` run only when it ended `ok` in the same workspace, and wraps the scaffold
record in the [run result](../../module.md#concept.execution.run-result). Scaffold relies on it
refusing another workspace's survey, or an unbound one, before the first step, so it only checks
that its one input is a survey.

<a id="uses-commands"></a>

**Commands** lists `scaffold` in its catalog, which is how the runner finds this Module's
definition by the command's name.

<a id="uses-adoption"></a>

**Adoption** defines the [decomposition proposal](../../operations/adoption/contracts.md#contract.adoption.decomposition)
a survey returns, and the checks of a proposal against a worktree that the survey applies too.
Scaffold applies the same checks again before writing, since the worktree may have changed since
the survey, and relies on a proposal that passes them naming only paths the parent binds and
identities nobody registered.

<a id="uses-spec"></a>

**Spec core** runs the [structural checks](../../../spec-tooling/spec/module.md#concept.spec.structural-check),
regenerates the [registry](../../../spec-tooling/spec/module.md#concept.spec.registry) mirror and
applies the [file transaction](../../../spec-tooling/spec/module.md#concept.spec.file-transaction),
always on the workspace. Scaffold relies on its checks as the definition of a valid Spec and adds
none of its own; a Spec that cannot be loaded ends the run `failed`.
