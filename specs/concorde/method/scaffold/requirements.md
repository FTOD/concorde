# Scaffold requirements

The obligations of [Scaffold](module.md). The shapes are in the [contracts](contracts.md). The
[scenarios](scenarios.md) show the obligations in concrete situations.

## Applying a proposal

### req.scaffold.children-created — Every proposed child is created

For every proposed child, the scaffold host SHALL create an entry whose realization binds the
paths the survey proposed for that child, less any vendored code inside them.

Each relation anchor the scaffold host writes names its Module by the identity after `module.`,
dots kept. Thus, distinct identities such as `module.a-b` and `module.a.b` never share an anchor,
in the parent's entry or in a child's.

### req.scaffold.children-uses — A new child uses what the survey found

The scaffold host SHALL give every created child exactly the `uses` the survey proposed for it.

### req.scaffold.contained — The parent contains its new children

The scaffold host SHALL add every created child to the parent's `contains`, with one explaining
paragraph per child at the end of the `Parts` section of the parent's entry.

When the parent's entry has no `Parts` section, the scaffold host adds one at the end of the entry
for these paragraphs and leaves the existing prose unchanged, as
[scenario.scaffold.no-parts-section](scenarios.md#scenario.scaffold.no-parts-section) shows.

### req.scaffold.registered — The registry records the new children

The scaffold host SHALL add a registry record for every created child.

### req.scaffold.vendored-external — Vendored code is never a Module

The scaffold host SHALL make every path the survey proposes as vendored third-party code an
external inclusion of the [Module](../../glossary.json#concept.module) that uses it, bound by no
Module, so that no worker describes or reviews it as the project's code.

### req.scaffold.vendored-bound-elsewhere — Vendored code another Module binds is refused

When a registered Module other than the surveyed Module binds a file of a vendored path, the
scaffold host SHALL end the run `blocked` with `stale_proposal` before writing anything.

Each such Module is a `proposal_mismatch` cause of its own that names the Module and the path, as
[scenario.scaffold.vendored-bound-elsewhere](scenarios.md#scenario.scaffold.vendored-bound-elsewhere)
shows. The scaffold changes no Module but the surveyed one and its new children, so it cannot take
the vendored path out of that Module.

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

The scaffold host SHALL check the proposal against the workspace again before writing and, when
the proposal no longer fits, end the run `blocked` with `stale_proposal`, every mismatch listed and
each a cause of its error.

A surveyed Module that the workspace removed or renamed is such a mismatch, also when it is the
only Module of the workspace's binding, as
[scenario.scaffold.surveyed-module-removed](scenarios.md#scenario.scaffold.surveyed-module-removed)
shows. When the workspace's [Specs](../../glossary.json#concept.spec) do not load, the scaffold
host ends the run `failed` with `specs_unloadable`, Spec core's error its cause, as
[scenario.scaffold.specs-unloadable](scenarios.md#scenario.scaffold.specs-unloadable) shows.

### req.scaffold.no-overwrite — The scaffold never replaces a file

When a file the scaffold would create exists, or a child's folder already exists, the scaffold host
SHALL end the run `blocked` with `stale_proposal`, naming the existing file or the folder of the
child that would hold it.

This holds even for a folder that holds no file the scaffold would create, since the scaffold
creates files only in folders it creates.

### req.scaffold.atomic — A scaffold is kept whole or not at all

The scaffold host SHALL write all its changes in one
[file transaction](../../glossary.json#concept.file-transaction) that is kept only when it adds no
structural error.

### req.scaffold.one-snapshot — A change is bound to the bytes it was computed from

The scaffold host SHALL derive the new content of every existing file it changes from the bytes its
recheck loaded and bind that change to the digest of those same bytes.

It binds every file it creates to the file's absence. Thus, a file changed after the recheck ends
the run `blocked` with `stale_proposal`, nothing of the scaffold kept and the change made to that
file preserved, as
[scenario.scaffold.concurrent-edit](scenarios.md#scenario.scaffold.concurrent-edit) shows.

### req.scaffold.write-failed — A failed write names what was not restored

When either condition holds, the scaffold host SHALL end the run `failed` with `write_failed`,
naming every file that still holds the scaffold's content:

- Its file transaction fails for a reason other than a file changed while it was written or a new
  structural error.
- Its file transaction cannot restore a file it wrote.

When every file was restored, a stale file stays `stale_proposal` and a new structural error stays
`scaffold_invalid`. When the transaction cannot restore a file, the run becomes `write_failed`,
whatever made the transaction fail, since the workspace is then not as before and the
[main agent](../../glossary.json#concept.main-agent) must repair it.

### req.scaffold.parent-narrowed — A child's paths leave the parent

The scaffold host SHALL narrow the parent's realizations so that every file they bound is bound by
exactly one of the parent and the created children, except in these cases:

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

The scaffold host SHALL state the survey's purpose in every entry it creates.

### req.scaffold.stub-unspecified — A scaffolded entry states what is unknown

In every entry it creates, the scaffold host SHALL say, in a section Not yet specified that follows
its Purpose, that the Module's core concepts, behaviour and design are not yet specified.

The section stands where the reading order of an entry puts the core concepts and the overview.
Thus, a reader meets the unknowns before the parts. A `Parts` section follows, which explains the
realization binding the child's code. Then a `Collaborations` section explains each proposed `uses`.

## The workflow handoff

### req.scaffold.step-output — The created Modules reach a workflow script

In the output of every `ok` scaffold run, the scaffold host SHALL put, under the
[step output convention](../../workflows/contracts.md#contract.workflows.step-output),
`data.created_modules`: every Module the run created, in its record's order, each with the `uses`
the survey proposed among the created Modules.

A [workflow script](../../glossary.json#concept.workflow-script) reads only what the convention
hands it, so this is how the [brownfield workflow](../../glossary.json#concept.brownfield-workflow)
orders its descriptions ([contracts](contracts.md)).
