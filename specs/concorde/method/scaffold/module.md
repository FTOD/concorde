# Scaffold

## Purpose

Scaffold creates the child Modules a survey proposed. It provides the
[execution command](../../glossary.json#concept.execution-command) `concorde scaffold`. It takes
one [decomposition proposal](../../glossary.json#concept.decomposition-proposal) from an `ok`
survey of the same [workspace](../../glossary.json#concept.workspace). It then does these:

- Writes each proposed child as a stub [Module](../../glossary.json#concept.module) that says plainly
  what is not specified yet.
- Narrows the parent's realizations to what no child took.
- Adds the children to the parent's `contains` and to the
  [registry](../../glossary.json#concept.registry).
- Returns a record of exactly what it wrote.

For a project whose code came before its Specs, it is the step between Adoption's two Operations,
`survey` and `code_to_spec`. The task level or the [brownfield workflow](../brownfield.md) runs it.
Scaffold launches no worker. The proposal, not Scaffold, decides which Modules to create.
Scaffold never does any of these:

- Describes a Module beyond the survey's purpose.
- Configures a check.
- Changes code.

## Overview

A survey's worker reads the code and proposes the children. Scaffold applies that proposal by fixed
rules, in one [file transaction](../../glossary.json#concept.file-transaction). `code_to_spec`
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

One scaffold changes the bindings as follows:

- Each child takes the paths the survey proposed for it.
- The parent keeps every path no child took.

So no file is bound twice. [Narrowing the parent](#narrowing-the-parent) gives the rule.

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

After a survey of the Module to split, usually the root, ends `ok`, the task level runs the command
in a task worktree. It runs the command before `code_to_spec` describes the new Modules:

```text
concorde scaffold --input <survey run> [--detach]
```

It is an execution command. The [Execution runner](../../execution/runner.md) runs it in the
workspace whose [binding](../../glossary.json#concept.workspace-binding) lies in the worktree it
starts in. The runner records it in the [run store](../../glossary.json#concept.run-store), so that
a workflow takes it as a step. Its result records exactly what it wrote. In a worktree without a
binding, the runner refuses it with `binding_required`. In that case, it writes nothing. It admits
exactly one input, an `ok` survey of the same workspace. Before the first step, the runner refuses a
survey of another workspace, or an unbound one.

## What it writes

For each proposed child, it writes an entry `module.md` and its metadata. It writes them in a folder
named after the child's identity, next to the parent's entry. The entry follows the recommended
reading order. It invents nothing:

- Its `Purpose` states the survey's purpose.
- Its section `Not yet specified` says that the child's core concepts, behaviour and design are not
  specified yet.
- Its `Parts` section explains a realization binding the paths the survey proposed for the child.
- Its `Collaborations` section explains each proposed `uses`.

The scaffold changes the parent and registry as follows:

- Adds the children to the parent's `contains` with one explaining paragraph each at the end of the
  parent's `Parts` section. Each paragraph repeats the child's purpose from the survey.
- Removes the children's paths from the parent's realization entries.
- Adds the registry records.

Vendored code leaves the parent's realizations too. It never becomes a Module. It becomes an
`includes` of kind `external` of the Module that uses it. That Module reads it. Nobody describes or
reviews it as the project's code, as the Protocol treats pinned third-party material. The scaffold
never configures the proposed checks. A check is a command the host later runs. Before use, the
developer must accept a command a model chose after reading code nobody vouched for. So the checks
stay a proposal the workflow reports. Everything is written in one file transaction. If validation
finds no new error, and only then, Scaffold keeps the transaction.

## Results and errors

The [run result](../../glossary.json#concept.run-result), of kind `command` with no worker,
carries the **scaffold record** ([contract](contracts.md#contract.scaffold.record)). The record
contains these:

- The Modules created with their entries.
- The vendored paths made external inclusions.
- The parent's realization entries before and after.
- Every file written.

When any of these conditions holds, the run is `blocked` with `stale_proposal`:

- The proposal no longer fits the worktree. A child's folder that already exists is such a mismatch.
- A file it would create exists.
- A file changed while it was written.

When any of these conditions holds, the run is `failed`:

- The input is not one survey.
- The Specs cannot be loaded.
- The files would add a structural error.

The [error chain](../../glossary.json#concept.error-chain) names every mismatch or finding as a
cause. When the file transaction fails for another reason, such as the operating system refusing a
write, the run is `failed` with `write_failed`. When the transaction cannot restore a file it wrote,
the run also has this status and code. In either case, the result names every file that still holds
the scaffold's content, to be removed or restored by hand. It says every other file is as before.

A stale proposal is `blocked` because what follows is the
[main agent](../../glossary.json#concept.main-agent)'s decision: survey again, or undo the change
to the worktree. A structural error is `failed` because the scaffold writes by fixed rules. It cannot
repair a proposal whose Spec does not validate. In that case, survey again with a goal naming the
problem, or report an [Issue](../../glossary.json#concept.issue) against the scaffold. Every code of
the scaffold's own steps is in the [error table](contracts.md#errors). A refusal before the first
step is the [runner's](../../execution/runner.md#errors).

## Why a deterministic command

Adding Modules is the project-level step the Protocol reserves for the registry and the parent's
`contains`, which no worker's write set includes. So a survey worker only proposes the children.
This deterministic command applies the proposal. Anyone can check what it wrote against the
proposal. Because no model is involved, it is an execution command rather than an
[Operation](../../glossary.json#concept.operation).

## Narrowing the parent

Scaffold writes where it can decide by rules alone. A child's folder is the parent entry's folder
plus the child identity's last segment. The parent keeps every path its realizations covered when
both of these conditions hold:

- No child took the path.
- The proposal did not name the path as vendored code.

This applies whichever of its documents declares the realization. The metadata of each is rewritten
in the same file transaction.
When a directory entry of the parent contains a child's entry, entries below it that no child took
replace it. When no child took anything inside a directory, the directory stays one entry. A file
is listed exactly. These are left out, as a directory entry never bound them:

- A directory that would bind no file, such as an empty one or one holding only skipped files.
- A symbolic link.

Conversely, when a child's directory entry does not bind a file, that file stays with the parent.
Such a file can be a dot file the parent binds exactly because its own directory entry skips it.
Unless the proposal deliberately gives one path to several children, no path is bound by both
parent and child. For example, a parent bound to `src/`, holding `src/checkout/`, `src/inventory/`
and `src/db.py`, whose children take `src/checkout/` and `src/inventory/`, is left bound to
`src/db.py`.

Vendored code is taken out by the same rule, from the parent and from a child's directory entry
alike. It is then bound by no Module. For example, a child bound to `src/checkout/` that holds
vendored `src/checkout/payment.py` binds the rest of the directory. When the proposal names the
child as that file's user, the child includes the vendored file as external material.

## The Scaffold command

<a id="realization.scaffold.command"></a>

The **Scaffold command** realization, `src/concorde/method/scaffold/`, declares the `SCAFFOLD`
execution command. The command launches no worker:

| # | Step | Actor | Stops the run when |
| --- | --- | --- | --- |
| 1 | Admit exactly one `ok` survey of the same workspace as input | host | none or several, not a survey, or a survey output that breaks its contract (`failed`, `invalid_request`) |
| 2 | Validate the worktree as a baseline and check the proposal against it again | host, Spec core | the Specs cannot be loaded (`failed`, `specs_unloadable`); the proposal no longer fits, such as a child's folder that already exists (`blocked`, `stale_proposal`) |
| 3 | Compute every file change: child entries, parent entry, the metadata of every parent document declaring a realization, registry | host | a target file already exists (`blocked`, `stale_proposal`) |
| 4 | Apply them as one file transaction, kept only if validation finds no new error | host, Spec core | a new error (`failed`, `scaffold_invalid`), nothing kept; a file changed while it was written (`blocked`, `stale_proposal`), nothing kept; a write the operating system refused or a file it could not restore (`failed`, `write_failed`), naming every file not restored |
| 5 | Return the run result with the scaffold record | host | — |

Its tests, under `tests/concorde/scaffold/`, run a survey and the scaffold in a bound task worktree
of a small existing codebase. They use a fake worker to verify the
[requirements](requirements.md) and [scenarios](scenarios.md).

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

**Execution**'s runner runs the command. It does these:

- Reads the workspace binding.
- Holds the [workspace lock](../../glossary.json#concept.workspace-lock).
- Admits the `--input` run only when it ended `ok` in the same workspace.
- Wraps the scaffold record in the [run result](../../glossary.json#concept.run-result).

Scaffold relies on it refusing another workspace's survey, or an unbound one, before the first
step. So it only checks that its one input is a survey.

<a id="uses-commands"></a>

**Commands**, Execution's execution-command framework, is what `scaffold` plugs into. Method
registers its definition there. This is how the runner finds this Module's definition by the
command's name.

<a id="uses-adoption"></a>

**Adoption** defines these:

- The [decomposition proposal](../adoption/contracts.md#contract.adoption.decomposition) a survey
  returns.
- The [checks of a proposal against a worktree](../adoption/requirements.md#req.adoption.proposal-checked)
  that the survey applies.
- In its shared records, the code of the rule, stated in
  [Narrowing the parent](#narrowing-the-parent), that narrows realization entries around children's
  paths and vendored code.

Since the worktree can change after the survey, Scaffold applies the same checks again before
writing. It relies on a proposal that passes them naming only paths the parent binds and identities
nobody registered. It computes the parent's and the children's entries again with the same rule,
from the worktree as it is then. It does not take the survey's `remaining_entries`.

<a id="uses-spec"></a>

**Spec core** does these, always on the workspace:

- Runs the [structural checks](../../glossary.json#concept.structural-check).
- Regenerates the [registry](../../glossary.json#concept.registry) mirror.
- Applies its own copy of a [file transaction](../../glossary.json#concept.file-transaction).

Scaffold relies on its checks as the definition of a valid
[Spec](../../glossary.json#concept.spec). It adds none of its own. When a Spec cannot be loaded,
the run ends `failed`.

<a id="uses-workflows"></a>

**Workflows** defines the
[step output convention](../../workflows/contracts.md#contract.workflows.step-output), the
`workflow` object of a run's output. Through it, every `ok` scaffold run hands a
[workflow script](../../glossary.json#concept.workflow-script) the Modules it created as
`data.created_modules` ([req.scaffold.step-output](requirements.md#req.scaffold.step-output)).
The run declares no [decision point](../../glossary.json#concept.decision-point), decision,
deviation or note there. Scaffold builds that object with Workflows' `step_output` helper. The
helper checks it against the convention. Scaffold knows no workflow. What `created_modules` holds
is Scaffold's. The envelope around it is Workflows'.
