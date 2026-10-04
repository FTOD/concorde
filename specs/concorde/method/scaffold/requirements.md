# Scaffold requirements

The obligations of [Scaffold](module.md). The shapes are in the [contracts](contracts.md); the
[scenarios](scenarios.md) show the obligations in concrete situations.

## Applying a proposal

### req.scaffold.children-created — Every proposed child is created

For every proposed child, the scaffold host SHALL create an entry whose realization binds the paths the survey proposed for that child, less any vendored code inside them.

### req.scaffold.children-uses — A new child uses what the survey found

The scaffold host SHALL give every created child exactly the `uses` the survey proposed for it.

### req.scaffold.contained — The parent contains its new children

The scaffold host SHALL add every created child to the parent's `contains`.

### req.scaffold.registered — The registry records the new children

The scaffold host SHALL add a registry record for every created child.

### req.scaffold.vendored-external — Vendored code is never a Module

The scaffold SHALL make every path the survey proposes as vendored third-party code an external inclusion of the [Module](../../glossary.json#concept.module) that uses it, bound by no Module, so that no worker describes or reviews it as the project's code.

### req.scaffold.input — The scaffold applies one survey of its workspace

The scaffold host SHALL apply exactly one proposal, from an `ok` survey run admitted with `--input`.

Given no input, several inputs or an input that is not a survey, it ends the run `failed` with
`invalid_request`, as
[scenario.scaffold.refused-input](scenarios.md#scenario.scaffold.refused-input) shows. A run of
another workspace, or an unbound one, never reaches the scaffold: the runner refuses it before the
run begins with `input_not_admissible`, as for every run.

### req.scaffold.checks-proposed-only — Proposed checks are never configured

The scaffold host SHALL NOT change the project configuration or any checks file.

A proposed check is a command a model chose after reading code; the developer configures the ones
they accept.

### req.scaffold.rechecked — The proposal is checked again before writing

The scaffold host SHALL check the proposal against the workspace again before writing, ending the run `blocked` with `stale_proposal` and every mismatch listed when it no longer fits.

### req.scaffold.no-overwrite — The scaffold never replaces a file

The scaffold host SHALL end the run `blocked` with `stale_proposal`, naming the existing file or the folder of the child that would hold it, when a file it would create exists or a child's folder already exists, even one that holds no file it would create, since the scaffold creates files only in folders it creates.

### req.scaffold.atomic — A scaffold is kept whole or not at all

The scaffold host SHALL write all its changes in one [file transaction](../../glossary.json#concept.file-transaction) that is kept only when it adds no structural error.

### req.scaffold.parent-narrowed — A child's paths leave the parent

After a scaffold, every file the parent's realizations bound SHALL be bound by exactly one of the parent and the created children, unless the proposal gave it to several children or named it, or a directory holding it, as vendored code.

Vendored code is bound by no Module
([req.scaffold.vendored-external](#req.scaffold.vendored-external)).

A child's directory entry binds only what the exclusion rule admits, so a dot file below it that
the parent bound exactly stays with the parent.

A parent directory entry that contains a child's entry is replaced by the entries below it that no
child took, a directory staying one entry when no child took anything inside it.

### req.scaffold.stub-honest — A scaffolded entry states the survey's purpose

Every entry the scaffold creates SHALL state the survey's purpose.

### req.scaffold.stub-unspecified — A scaffolded entry states what is unknown

Every entry the scaffold creates SHALL say, in a section Not yet specified that follows its Purpose, that the Module's core concepts, behaviour and design are not yet specified.

The section stands where the reading order of an entry puts the core concepts and the overview, so
a reader meets the unknowns before the parts. A `Parts` section follows, which explains the
realization binding the child's code, and then a `Collaborations` section, which explains each
proposed `uses`.

## The workflow handoff

### req.scaffold.step-output — The created Modules reach a workflow script

The output of every `ok` scaffold run SHALL carry, under the [step output convention](../../workflows/contracts.md#contract.workflows.step-output), `data.created_modules`: every Module it created, in its record's order, each with the `uses` the survey proposed among the created Modules.

A [workflow script](../../glossary.json#concept.workflow-script) reads only what the convention hands it, so this is how the
[brownfield workflow](../../glossary.json#concept.brownfield-workflow) orders its descriptions
([contracts](contracts.md)).

