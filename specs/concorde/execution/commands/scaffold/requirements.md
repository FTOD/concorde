# Scaffold requirements

The obligations of [Scaffold](module.md). The shapes are in the [contracts](contracts.md); the
[scenarios](scenarios.md) show the obligations in concrete situations.

## Applying a proposal

### req.scaffold.vendored-external — Vendored code is never a Module

The scaffold SHALL make every path the survey proposes as vendored third-party code an external inclusion of the [Module](../../../glossary.json#concept.module) that uses it, bound by no Module, so that no worker describes or reviews it as the project's code.

### req.scaffold.input — The scaffold applies one survey of its workspace

The scaffold host SHALL apply exactly one proposal, from an `ok` survey run admitted with `--input`, refusing no input, several inputs or an input that is not a survey with `invalid_request`.

A run of another workspace, or an unbound one, never reaches the scaffold: the runner refuses it
before the run begins with `input_not_admissible`, as for every run.

### req.scaffold.checks-proposed-only — Proposed checks are never configured

The scaffold host SHALL NOT change the project configuration.

A proposed check is a command a model chose after reading code; the developer configures the ones
they accept.

### req.scaffold.rechecked — The proposal is checked again before writing

The scaffold host SHALL check the proposal against the workspace again before writing, ending the run `blocked` with `stale_proposal` and every mismatch listed when it no longer fits or a file it would create exists.

### req.scaffold.atomic — A scaffold is kept whole or not at all

The scaffold host SHALL write all its changes in one [file transaction](../../../glossary.json#concept.file-transaction) that is kept only when it adds no structural error.

### req.scaffold.parent-narrowed — A child's paths leave the parent

After a scaffold, every file the parent's realizations bound SHALL be bound by exactly one of the parent and the created children, unless the proposal gave it to several children.

A child's directory entry binds only what the exclusion rule admits, so a dot file below it that
the parent bound exactly stays with the parent.

A parent directory entry that contains a child's entry is replaced by the entries below it that no
child took, a directory staying one entry when no child took anything inside it.

### req.scaffold.stub-honest — A scaffolded entry states what is unknown

Every entry the scaffold creates SHALL state the survey's purpose and say in its Usage and Design sections that the Module's behaviour and design are not yet specified.
