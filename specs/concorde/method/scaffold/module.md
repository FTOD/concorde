# Scaffold

## Purpose

Scaffold creates the child Modules a survey proposed. It provides the
[execution command](../../glossary.json#concept.execution-command) `concorde scaffold`: given
one [decomposition proposal](../../glossary.json#concept.decomposition-proposal) from an `ok`
survey of the same [workspace](../../glossary.json#concept.workspace), it writes each proposed
child as a stub [Module](../../glossary.json#concept.module) that says plainly what is not
specified yet, narrows the parent's realizations to what no child took, adds the children to the
parent's `contains` and to the [registry](../../glossary.json#concept.registry), and returns a
record of exactly what it wrote. It is the step between Adoption's two Operations, `survey` and
`code_to_spec`, for a project whose code came before its Specs; the task level or the
[brownfield workflow](../brownfield.md) runs it. Scaffold launches no worker, never decides
which Modules to create — the proposal does — and never describes a Module beyond the survey's
purpose, configures a check or changes code.

## Overview

A survey's worker reads the code and proposes the children; Scaffold applies that proposal by fixed
rules, in one [file transaction](../../glossary.json#concept.file-transaction); `code_to_spec`
then describes each new Module. The checks the survey proposed stay a proposal the developer
decides on:

```d2 illustrative
direction: right
survey: "survey\nAdoption, one worker"
proposal: "Decomposition proposal:\nchildren, their paths and uses,\nvendored code, checks" {shape: page}
scaffold: "concorde scaffold\nno worker"
written: "One file transaction:\nchild stubs, parent narrowed,\ncontains, registry" {shape: page}
describe: "code_to_spec\ndescribes each child"
checks: "Proposed checks,\nleft for the developer" {shape: page}
survey -> proposal -> scaffold -> written -> describe
proposal -> checks: never configured
```

What one scaffold does to the bindings: each child takes the paths the survey proposed for it, and
the parent keeps every path no child took, so no file is bound twice. [Narrowing the
parent](#narrowing-the-parent) gives the rule.

```d2 illustrative
direction: right
before: "Before: the parent binds src/" {
  checkout: "src/checkout/"
  inventory: "src/inventory/"
  db: "src/db.py"
}
after: "After: the parent binds src/db.py\nand contains two children" {
  checkout: "Checkout:\nbinds src/checkout/"
  inventory: "Inventory:\nbinds src/inventory/"
}
before -> after: "children take their paths;\nthe parent keeps the rest"
```

## Running the command

The task level runs the command in a task worktree after a survey of the Module to split, usually
the root, has ended `ok`, and before `code_to_spec` describes the new Modules:

```text
concorde scaffold --input <survey run> [--detach]
```

It is an execution command: the [Execution runner](../../execution/runner.md) runs it in the workspace whose
[binding](../../glossary.json#concept.workspace-binding) lies in the worktree it starts in and
records it in the [run store](../../glossary.json#concept.run-store), so that a workflow takes it
as a step and its result records exactly what it wrote. In a worktree without a binding it is
refused with `binding_required` and writes nothing. It admits exactly one input, an `ok` survey of
the same workspace; the runner refuses a survey of another workspace, or an unbound one, before the
first step.

## What it writes

For each proposed child it writes an entry `module.md` and its metadata in a folder named after the
child's identity, next to the parent's entry. The entry follows the recommended reading order and
invents nothing: its Purpose states the survey's purpose; a section Not yet specified says that the
child's core concepts, behaviour and design are not specified yet; its Parts section explains a
realization binding the paths the survey proposed for the child; and its Collaborations section
explains each proposed `uses`. The scaffold adds the children to the parent's `contains` with one
explaining paragraph each at the end of the parent's Parts section, which repeats the child's
purpose from the survey, removes the children's paths from the parent's realization entries and adds
the registry records.

Vendored code leaves the parent's realizations too, but never becomes a Module: it becomes an
`includes` of kind `external` of the Module that uses it, which that Module reads and nobody
describes or reviews as the project's code, as the Protocol treats pinned third-party material. The
scaffold never configures the proposed checks: a check is a command the host later runs, and a
command a model chose after reading code nobody vouched for must be accepted by the developer first,
so the checks stay a proposal the workflow reports. Everything is written in one file transaction
that is kept only if validation finds no new error.

## Results and errors

The [run result](../../glossary.json#concept.run-result), of kind `command` with no worker,
carries the **scaffold record** ([contract](contracts.md#contract.scaffold.record)): the Modules
created with their entries, the vendored paths made external inclusions, the parent's realization
entries before and after, and every file written. The run is `blocked` with `stale_proposal` when
the proposal no longer fits the worktree (a child's folder that already exists is such a mismatch),
a file it would create exists or a file changed while it was written, and `failed` when the input is
not one survey, the Specs cannot be loaded or the files would add a structural error; the
[error chain](../../glossary.json#concept.error-chain) names every mismatch or finding as a cause.
A stale proposal is `blocked` because what follows is the
[main agent](../../glossary.json#concept.main-agent)'s decision: survey again, or undo the change
to the worktree. A structural error is `failed` because the scaffold writes by fixed rules and cannot
repair a proposal whose Spec does not validate: survey again with a goal naming the problem, or
report an [Issue](../../glossary.json#concept.issue) against the scaffold. Every code of the
scaffold's own steps is in the [error table](contracts.md#errors); a refusal before the first step
is the [runner's](../../execution/runner.md#errors).

## Why a deterministic command

Adding Modules is the project-level step the Protocol reserves for the registry and the parent's
`contains`, which no worker's write set includes. So a survey worker only proposes the children, and
this deterministic command applies the proposal: anyone can check what it wrote against the
proposal, and it is an execution command rather than an
[Operation](../../glossary.json#concept.operation) because no model is involved.

## Narrowing the parent

Scaffold writes where it can decide by rules alone. A child's folder is the parent entry's folder
plus the child identity's last segment. The parent keeps every path its realizations covered that no
child took and the proposal did not name as vendored code. A directory entry of the parent that
contains a child's entry is replaced by the entries below it that no child took: a directory stays
one entry when no child took anything inside it, and a file is listed exactly. A directory that
would bind no file, such as an empty one or one holding only skipped files, and a symbolic link are
left out, as a directory entry never bound them. Conversely a file a child's directory entry does
not bind, such as a dot file the parent binds exactly because its own directory entry skips it,
stays with the parent. So no path is bound by both parent and child unless the proposal
deliberately gives one path to several children. For example, a parent bound to `src/`, holding
`src/checkout/`, `src/inventory/` and `src/db.py`, whose children take `src/checkout/` and
`src/inventory/`, is left bound to `src/db.py`.

Vendored code is taken out by the same rule, from the parent and from a child's directory entry
alike, and then bound by no Module: a child bound to `src/checkout/` that holds vendored
`src/checkout/payment.py` binds the rest of the directory, and includes the vendored file as
external material when the proposal names it as that file's user.

## The Scaffold command

<a id="realization.scaffold.command"></a>

The **Scaffold command** realization, `src/concorde/method/scaffold/`, declares the `SCAFFOLD` execution
command, which launches no worker:

| # | Step | Actor | Stops the run when |
| --- | --- | --- | --- |
| 1 | Admit exactly one `ok` survey of the same workspace as input | host | none or several, not a survey, or a survey output that breaks its contract (`failed`, `invalid_request`) |
| 2 | Validate the worktree as a baseline and check the proposal against it again | host, Spec core | the Specs cannot be loaded (`failed`, `specs_unloadable`); the proposal no longer fits, such as a child's folder that already exists (`blocked`, `stale_proposal`) |
| 3 | Compute every file change: child entries, parent entry and realization, registry | host | a target file already exists (`blocked`, `stale_proposal`) |
| 4 | Apply them as one file transaction, kept only if validation finds no new error | host, Spec core | a new error (`failed`, `scaffold_invalid`), nothing kept; a file changed while it was written (`blocked`, `stale_proposal`), nothing kept |
| 5 | Return the run result with the scaffold record | host | — |

Its tests, under `tests/concorde/scaffold/`, run a survey and the scaffold in a bound task worktree
of a small existing codebase with a fake worker, verifying the [requirements](requirements.md) and
[scenarios](scenarios.md).

```d2
scaffold: Scaffold {
  command: Scaffold command {
    "src/concorde/method/scaffold/"
    "tests/concorde/scaffold/"
  }
}
```

## The Modules it relies on

<a id="uses-execution"></a>

**Execution**'s runner runs the command: it reads the workspace binding, holds the
[workspace lock](../../glossary.json#concept.workspace-lock), admits the `--input` run only when
it ended `ok` in the same workspace, and wraps the scaffold record in the
[run result](../../glossary.json#concept.run-result). Scaffold relies on it refusing another
workspace's survey, or an unbound one, before the first step, so it only checks that its one input
is a survey.

<a id="uses-commands"></a>

**Commands**, Execution's execution-command framework, is what `scaffold` plugs into: Method
registers its definition there, which is how the runner finds this Module's definition by the
command's name.

<a id="uses-adoption"></a>

**Adoption** defines the
[decomposition proposal](../adoption/contracts.md#contract.adoption.decomposition) a
survey returns, the
[checks of a proposal against a worktree](../adoption/requirements.md#req.adoption.proposal-checked)
that the survey applies, and, in its shared records, the code of the rule, stated in
[Narrowing the parent](#narrowing-the-parent), that narrows realization entries around children's
paths and vendored code. Scaffold applies the same checks again before writing, since the worktree
may have changed since the survey, and relies on a proposal that passes them naming only paths the
parent binds and identities nobody registered. It computes the parent's and the children's entries again with the same rule, from the
worktree as it is then, rather than taking the survey's `remaining_entries`.

<a id="uses-spec"></a>

**Spec core** runs the [structural checks](../../glossary.json#concept.structural-check),
regenerates the [registry](../../glossary.json#concept.registry) mirror and applies its own copy of a
[file transaction](../../glossary.json#concept.file-transaction), always on the workspace.
Scaffold relies on its checks as the definition of a valid
[Spec](../../glossary.json#concept.spec) and adds none of its own; a Spec that cannot be loaded
ends the run `failed`.

<a id="uses-workflows"></a>

**Workflows** defines the
[step output convention](../../workflows/contracts.md#contract.workflows.step-output), the
`workflow` object of a run's output, through which every `ok` scaffold run hands a
[workflow script](../../glossary.json#concept.workflow-script) the Modules it created as
`data.created_modules` ([req.scaffold.step-output](requirements.md#req.scaffold.step-output)); it
declares no [decision point](../../glossary.json#concept.decision-point), decision, deviation or note there. Scaffold builds that object with Workflows' `step_output`
helper, which checks it against the convention, and knows no workflow: what `created_modules` holds
is Scaffold's, the envelope around it Workflows'.
