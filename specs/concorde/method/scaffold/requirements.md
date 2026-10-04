# Scaffold requirements

The obligations of [Scaffold](module.md). The shapes are in the [contracts](contracts.md). The
[scenarios](scenarios.md) show the obligations in concrete situations.

## Applying a proposal

### req.scaffold.children-created — Every proposed child is created

For every proposed child, the scaffold host SHALL create an entry whose realization binds the
paths the survey proposed for that child, less any vendored code inside them.

### req.scaffold.children-uses — A new child uses what the survey found

The scaffold host SHALL give every created child exactly the `uses` the survey proposed for it.

### req.scaffold.contained — The parent contains its new children

The scaffold host SHALL add every created child to the parent's `contains`.

### req.scaffold.registered — The registry records the new children

The scaffold host SHALL add a registry record for every created child.

### req.scaffold.vendored-external — Vendored code is never a Module

The scaffold SHALL make every path the survey proposes as vendored third-party code an external
inclusion of the [Module](../../glossary.json#concept.module) that uses it, bound by no Module.

This way, no worker describes or reviews it as the project's code.

### req.scaffold.input — The scaffold applies one survey of its workspace

The scaffold host SHALL apply exactly one proposal, from an `ok` survey run admitted with `--input`.

Given any of these inputs, it ends the run `failed` with `invalid_request`, as
[scenario.scaffold.refused-input](scenarios.md#scenario.scaffold.refused-input) shows:

- No input.
- Several inputs.
- An input that is not a survey.

A run of another workspace, or an unbound one, never reaches the scaffold. As for every run, the
runner refuses it with `input_not_admissible` before the run begins.

### req.scaffold.checks-proposed-only — Proposed checks are never configured

The scaffold host SHALL NOT change the project configuration or any checks file.

A proposed check is a command a model chose after reading code. The developer configures the ones
they accept.

### req.scaffold.rechecked — The proposal is checked again before writing

The scaffold host SHALL do all of these before writing:

- Check the proposal against the workspace again.
- When the proposal no longer fits, end the run `blocked` with `stale_proposal`.
- In that case, list every mismatch as a cause of its error.

### req.scaffold.no-overwrite — The scaffold never replaces a file

The scaffold host SHALL end the run `blocked` with `stale_proposal`, naming the existing file or the
folder of the child that would hold it, when either of these holds:

- A file it would create exists.
- A child's folder already exists, even one that holds no file it would create.

A child's existing folder is refused too, since the scaffold creates files only in folders it
creates.

### req.scaffold.atomic — A scaffold is kept whole or not at all

The scaffold host SHALL write all its changes in one
[file transaction](../../glossary.json#concept.file-transaction) that is kept only when it adds no
structural error.

### req.scaffold.write-failed — A failed write names what was not restored

When either condition holds, the scaffold host SHALL end the run `failed` with `write_failed`,
naming every file that still holds the scaffold's content:

- Its file transaction fails for a reason other than a file changed while it was written or a new
  structural error.
- Its file transaction cannot restore a file it wrote.

When every file was restored, a stale file stays `stale_proposal` and a new structural error stays
`scaffold_invalid`. When the transaction cannot restore a file, the run becomes `write_failed`,
whatever made the transaction fail. The workspace is then not as before, and the
[main agent](../../glossary.json#concept.main-agent) must repair it.

### req.scaffold.parent-narrowed — A child's paths leave the parent

After a scaffold, every file the parent's realizations bound SHALL be bound by exactly one of the
parent and the created children, except in these cases:

- The proposal gave the file to several children.
- The proposal named the file as vendored code.
- The proposal named a directory holding the file as vendored code.

This holds for a realization the parent declares in any of its documents, not only its entry.

Vendored code is bound by no Module
([req.scaffold.vendored-external](#req.scaffold.vendored-external)).

A child's directory entry binds only what the exclusion rule admits. Thus, a dot file below it
that the parent bound exactly stays with the parent.

A parent directory entry that contains a child's entry is replaced by the entries below it that
no child took. When no child took anything inside it, a directory stays one entry.

### req.scaffold.stub-honest — A scaffolded entry states the survey's purpose

Every entry the scaffold creates SHALL state the survey's purpose.

### req.scaffold.stub-unspecified — A scaffolded entry states what is unknown

In a section Not yet specified that follows its Purpose, every entry the scaffold creates SHALL
say that the Module's core concepts, behaviour and design are not yet specified.

The section stands where the reading order of an entry puts the core concepts and the overview.
Thus, a reader meets the unknowns before the parts. A `Parts` section follows, which explains the
realization binding the child's code. Then a `Collaborations` section explains each proposed
`uses`.

## The workflow handoff

### req.scaffold.step-output — The created Modules reach a workflow script

Under the [step output convention](../../workflows/contracts.md#contract.workflows.step-output),
the output of every `ok` scaffold run SHALL carry `data.created_modules`: every Module the run
created, in its record's order, each with the `uses` the survey proposed among the created Modules.

A [workflow script](../../glossary.json#concept.workflow-script) reads only what the convention
hands it. This is how the [brownfield workflow](../../glossary.json#concept.brownfield-workflow)
orders its descriptions ([contracts](contracts.md)).

