# Spec requirements

These are the Module-wide obligations of the [Spec core](module.md)
[Module](../../glossary.json#concept.module). The headings group them by subject. Each requirement
belongs to the Module as a whole.

## Independence

### req.spec.no-owner-imports — Spec core depends on no other Module

Spec core SHALL NOT import code of any other Concorde Module, the Kernel's included.

Other Modules' schemas, policies and file locations reach Spec core only as call arguments or,
for a type of the spec part's own Modules, through its typed value registration.

The utilities Spec core shares in kind with the Kernel are its own copy: typed values, file
transactions, schema checking and digests.

These copies follow the formats the
[Kernel's contracts](../../kernel/contracts.md#typed-values) define.

## Loading

### req.spec.registered-only — Documents come from declarations only

The loader SHALL treat as documents only the reading paths listed in some Module's `owns`, each
together with its exact `.json` companion.

None of the following adds a document:

- A Markdown file found on disk.
- A Markdown link.
- A directory neighbour.

### req.spec.no-writes — Loading and queries never write

The following activities SHALL NOT write any project file:

- Constructing a repository.
- Querying it.
- Computing a grant.
- Validating a project.

### req.spec.snapshot-reconstruct — A repository is a snapshot

A repository SHALL answer every query from the sources as they were when it was constructed.

A caller that needs to see a change constructs a new repository.
Replacement bytes handed to the constructor for the registry or for documents stay in memory.
These bytes are never written.

### req.spec.deterministic-order — Same input, same answer

Repeated queries against the same repository SHALL return equal results in the same order.

### req.spec.no-implementation-read — Boundary sets never read code

The following activities SHALL NOT read the contents of implementation files:

- Loading the Specs.
- Computing [boundary sets](../../glossary.json#concept.boundary-set).
- Computing grants.
- Computing impact indexes.

Listing a directory to expand its entries is allowed. Only paths are used.
The `covered-by` index and validation's coverage scan are the exception.
They parse bound test files for their verification declarations.
Neither feeds a boundary set or a grant.

### req.spec.no-partial-repository — No partial repository

When the project has a problem that makes a boundary untrustworthy, the loader SHALL NOT return a
repository for use by consumers.

These problems are listed in the [interface definitions](contracts.md#loading-failures). The
validator opens the repository so that the same problems become findings instead.

### req.spec.protocol-binding — Only the accepted Protocol is admitted

The loader SHALL admit a project only when all these conditions hold:

- Its configuration binds exactly the
  [Protocol copy](../../glossary.json#concept.protocol-copy) under `.concorde/protocol/`.
- That copy's assets match their recorded digests.
- The copy's manifest equals the Protocol manifest of the running Concorde package.

## Checks

### req.spec.every-check — Every Protocol check is evaluated

Validation SHALL evaluate every check listed in the Protocol's Checks chapter.

### req.spec.check-finding-identity — A violation carries its check's identity and strictness

Validation SHALL report each violation of a Protocol check as a finding with that check's rule
identity and the strictness the Checks chapter gives it.

### req.spec.all-findings — One run reports everything it can

After a finding, Validation SHALL continue and report every further violation that the remaining
readable declarations and test files allow it to establish.

When a test file cannot be parsed, it is reported, and the other bound test files are still scanned.

### req.spec.status-from-errors — Only errors make a result invalid

Exactly when at least one finding has strictness error, the validation status SHALL be `invalid`.

### req.spec.no-structural-proof — Structural checks are not semantic proof

A validation result SHALL NOT be represented as proof that a
[Spec](../../glossary.json#concept.spec) is semantically sufficient or that an implementation
conforms to it.

The result carries an explicit marker saying semantic completeness is not proven.

### req.spec.link-fragments — Links to definitions resolve

Validation SHALL report as an error every link in Spec reading whose fragment has the form of a
requirement, scenario, realization or contract identity and does not name a definition in the
linked document.

A link whose fragment is a concept identity is a term link.
The Protocol's `CHK.term.link` checks it against the project glossary instead.

### req.spec.fixed-registry — The registry has one place

Spec core SHALL read the registry only from `.concorde/specs.json`.

No current profile has a field naming a registry.
A configuration that still names a registry is refused.


### req.spec.digest-per-assessment — Every result names what it assessed

Every validation result SHALL carry a digest of the exact inputs it assessed:

- The configuration.
- The registry.
- The document members.
- The glossary.
- The [Protocol binding](../../glossary.json#concept.protocol-binding).

The digest covers only those inputs. It excludes the following:

- The files that Modules bind.
- The list of version-controlled files.
- The contents of the tests scanned for verification declarations.

Since the digest excludes them, findings about bindings, unbound files and scenario coverage can
change while the digest stays the same.

## Registry mirror

### req.spec.registry-mirror-only — Regeneration changes only mirrored fields

Regenerating the registry SHALL rewrite only the mirrored fields of the Modules it already records,
leaving each record's identity and entry path and the set of recorded Modules unchanged.

The mirrored fields are every field of the entry's `module` block: `title`, `owns`, `contains`,
`uses`, `includes` and `participates`, and `glossary` in the one block that declares it.

### req.spec.registry-check-read-only — Checking the mirror never writes

Checking the registry mirror SHALL report every record whose mirrored fields differ from its entry
without writing any file.

## Boundary sets and indexes

### req.spec.one-level-selection — Context selection is one level deep

[Spec context](../../glossary.json#concept.spec-context) selection SHALL follow only the selected
Module's own `owns`, `contains`, `uses` and `includes` declarations and never the relations of the
Modules and documents they select.

Sharing a bound file with another Module adds nothing to either Module's Spec context.

### req.spec.term-selection — A context holds the definitions its documents use

A Module's Spec context SHALL hold exactly the glossary entries of the following concepts, closed
over concepts those entries' definitions link and their `narrows`, `supersedes` and `relates` target:

- The concepts the Module owns.
- The concepts the documents it selects link or relate to.
- The concepts its `relies_on` names.

The closure stays inside the glossary.
The closure adds definitions, never a document.

### req.spec.both-members — Documents are selected whole

Every boundary set that contains a document SHALL contain both its reading member and its metadata
member.

### req.spec.write-sets-own-only — Write sets hold only the Module's own files

A Module's Spec scope and implementation scope SHALL contain only the following:

- The documents it owns.
- The project glossary.
- The files its own realizations cover.

Of the glossary, only the entries the Module owns and new entries naming it as owner are the
Module's to change.

The grant that makes the file writable names the Modules whose entries it covers.
A harness can therefore hold the change to those entries.

A provider's documents therefore appear in a consumer's Spec context but never in the consumer's
Spec scope.

### req.spec.one-realization-per-file — The longest entry decides

Within one Module, a bound file SHALL belong to the realization whose covering entry is the longest.

### req.spec.directory-entry — A directory entry binds the files below it

An entry ending with `/` SHALL bind every regular file below that directory except those the
implementation exclusion rule skips.

The exclusion rule is part of the [interface definitions](contracts.md#implementation-exclusions).

### req.spec.scenario-query-owner — A scenario selects its owner's whole context

A query by scenario identity SHALL return exactly the Spec context of the Module that owns the
scenario.

### req.spec.indexes-derived — Impact indexes come from declarations alone

Every [impact index](../../glossary.json#concept.impact-index) SHALL be computed from the loaded
declarations and realization entries alone.

No index reads implementation file contents, test results or recorded evidence. No index query
changes a boundary set. The one exception is `covered-by`, which reads the
[verification declarations](../../glossary.json#concept.verification-declaration) of bound test
sources as [req.spec.coverage-from-tests](#req.spec.coverage-from-tests) says. It reads them
without importing, compiling or running the test sources.

## Grants

### req.spec.grant-task-type-levels — A task type fixes every level

A grant SHALL give each boundary set of each bound Module, and ProjectImplementation, exactly the
access level that the Protocol's [task-type](../../glossary.json#concept.task-type) table assigns
to the grant's task type.

The levels are serialized as `names`, `ro` and `rw`. The table is repeated in the
[interface definitions](contracts.md#grants).

### req.spec.grant-highest-level — The highest level wins

When a path falls into several boundary sets of one or more bound Modules, the grant SHALL give it
the highest level any of those sets assigns, ordered none, `names`, `ro`, `rw`.

### req.spec.grant-deny-omitted — Denied paths are absent

A grant SHALL list only paths whose level is `names`, `ro` or `rw`.

Every path the list does not cover, directly or below a directory entry, is denied.

### req.spec.grant-no-widening — Nothing else widens a grant

A grant SHALL contain no path outside the boundary sets of its bound Modules and, for the task
types that assign them, ProjectImplementation and ProjectSpecification.

None of the following adds anything:

- Task material.
- Shared files.
- Impact indexes.
- The task's history.

### req.spec.grant-installed-read-only — An installed file is never writable

A grant SHALL give an exact entry for a file that the installation record `.concorde/install.json`
lists as the installer's own at most the level `ro`.

The cap applies after the highest level is chosen.
It therefore overrides an `rw` that an implementation scope would give.
A file the installer only amends is the project's.
Such a file keeps its level.
A directory entry covering an installed file is the `CHK.binds.installed` error.
Only validation reports this error.

### req.spec.grant-shared-write — Shared files need every binder

When a grant would make writable a file that a Module outside the grant's Modules also binds,
computing the grant SHALL fail.

The failure names every such file and Module.
The caller can therefore bind the task to them or split the work.

### req.spec.grant-one-worktree — One worktree answers

A grant SHALL be computed only from the following sources of the worktree named as its root:

- The configuration.
- The registry.
- The documents.
- The realization entries.

### req.spec.grant-deterministic — Same Specs, same grant

Computing a grant twice from unchanged sources SHALL return equal values with entries sorted by
path.

### req.spec.context-identity-changes — The context identity tracks its sources

The [context identity](../../glossary.json#concept.context-identity) SHALL change in any of these
cases:

- A byte of a selected document member changes.
- A byte of a selected glossary entry changes.
- A byte of a selecting declaration changes.
- A byte of a document's owner changes.
- A byte of pinned external material changes.
- For a `review-architecture` grant, a byte of any file of ProjectSpecification changes.

The context identity covers no implementation file contents.
A worker's writes to implementation files therefore never change it.
A task that writes Specs changes the context identity with its own writes to the Module's documents
or glossary entries.
An identity computed after those writes therefore differs from the one frozen before.

## Coverage

### req.spec.coverage-from-tests — Coverage comes from the tests

Scenario coverage SHALL be read only from
[verification declarations](../../glossary.json#concept.verification-declaration) in bound test
sources, without any of these actions:

- Importing the tests.
- Compiling the tests.
- Running the tests.

## Typed values

### req.spec.typed-closed — Typed values are closed and exactly versioned

Checking a [typed value](../../glossary.json#concept.typed-value) SHALL reject any of the following:

- An unknown type.
- A schema version other than the registered one.
- Any field of the value itself other than `type_id`, `schema_version` and `data`.
- Any `data` its registered schema refuses as JSON Schema would, including a missing required field
  and a field an object closed by `additionalProperties: false` does not name.

When a type's schema uses a keyword that checking its values would not evaluate, registering the
type SHALL fail.

### req.spec.typed-offline — Typed values are checked offline

Checking a typed value or a contract schema SHALL use no network access and no schema outside
those registered or defined in the checked schema itself.

### req.spec.typed-registration-unique — One registration per type

When a type's identity is already registered with a different version or schema, registering the
type SHALL fail.

Registering the identical version and schema again is accepted.
This registration changes nothing.
An owner's code may therefore be loaded twice.

## File transactions

### req.spec.transaction-all-or-nothing — A transaction applies completely or not at all

A [file transaction](../../glossary.json#concept.file-transaction) SHALL either write every listed
file with its new content or, when a write or its final check fails while the process runs, leave every
listed file with its original bytes.

The guarantee covers only failures the process observes as an exception.
If any of the following happens part-way, the process leaves the files in the state listed below:

- The process is killed.
- The process stops because of a signal or a keyboard interrupt.
- The process loses its machine.

In those cases, the files have this state:

- Each listed file the process already replaced holds the new content.
- Every other listed file holds its original bytes.
- `.concorde-write-` temporary files may remain beside them.

Every file is replaced by a rename.
No listed file therefore ever holds part of each.

### req.spec.transaction-restore-reported — A failed restore is named

When a file transaction fails and the operating system refuses to restore a file it wrote,
the transaction SHALL fail with a `system_error` with these properties:

- It names every file the transaction could not restore.
- It carries the first failure and each refused restore as causes.
- It states that those files still hold the new content.
- It states that every other written file was restored.

### req.spec.transaction-system-errors — Refused writes are Spec errors

A file transaction SHALL report an operating-system error from one of its writes as a `SpecError`
with these properties:

- Its code is `system_error`.
- It names the file.
- Its cause is the `system_error` record of the operating system's error.

An exception raised by the caller's final check is the caller's own.
Once every written file is restored, that exception propagates unchanged.

### req.spec.transaction-digest-bound — Stale input stops a transaction

When any listed file's current bytes do not match the digest the transaction expects to replace,
a file transaction SHALL refuse to write.

A file expected to be absent has a null digest.
Such a file must still be absent.

## Initialization

### req.spec.init-allowed-files — Initialization writes only its own files

Applying an initial proposal SHALL write only the following:

- `.concorde/config.json`.
- `.concorde/specs.json`.
- The members of the documents the proposed registry registers.
- The glossary the proposed root Module declares.

### req.spec.init-no-overwrite — Initialization never overwrites

Applying an initial proposal SHALL NOT replace a file that already exists.

### req.spec.init-explicit-envelope — Apply checks shape, integrity and freshness

Applying SHALL accept an initial proposal only when all these conditions hold:

- The proposal is a complete typed value of the proposal type in exactly the shape propose returns.
- The proposal comes with a proposal digest that is the digest of that value.
- The proposal's source digest is the project's current one.

These checks establish the proposal's shape, its integrity and its freshness. They do not
establish that propose produced the proposal, since any caller can compute the proposal digest.
An applied proposal is also held to the following:

- The allowed files.
- The rule that nothing is overwritten.
- A project that validates.

### req.spec.init-validated — The result must validate

Applying SHALL keep the written files only if the resulting project validates without errors.

### req.spec.init-honest-stub — The first Spec invents nothing

Rather than invent concepts, requirements, scenarios or relations, the initial Module stub SHALL
state the following as not yet specified:

- The project's purpose.
- The project's behaviour.
- The project's architecture.

### req.spec.init-binds-existing-files — Existing files are bound at once

The initial Module stub SHALL bind every existing project file that version control tracks or does
not ignore, apart from the files below, so that the new project validates without errors:

- Document members.
- Control records.
- Generated outputs.

The binding is one realization of the root Module, Existing project files.
The realization locates files. It promises nothing about them.

### req.spec.init-installation-apart — Concorde's own files are bound apart

The initial Module stub SHALL bind the files the installer's receipt names outside `.concorde/`,
other than the files it lists as amended, in a realization of their own, Concorde installation,
and not among the existing project files.

The installer's skill and workflows configure the agents, not the project.
The project's `.gitignore` and `CLAUDE.md`, which the installer only amends, stay the project's files.

### req.spec.installation-follows-record — The installation realization follows the receipt

Binding the installation of an initialized project SHALL add, as an exact entry of its Concorde
installation realization, every file the installer's receipt names outside `.concorde/`, other than
the amended ones, that exists and that no realization binds by its exact path, and remove from
that realization every entry that no longer exists, writing nothing else.

Installation binding never unbinds an existing file.
Installation binding never adds a directory entry.
Therefore, `CHK.binds.installed` keeps holding.
Without such a realization and with files to bind, installation binding creates the realization
in the root Module with its explaining paragraph in the root entry, as initialization does.

The metadata member and, only when the realization is created, the entry are written in one
[file transaction](../../glossary.json#concept.file-transaction).

When any of these conditions holds, installation binding leaves a project unchanged:

- The project has no configuration.
- The project's registry cannot be read.
- The project's metadata cannot be read.

A realization whose every entry is gone is left for validation to report.

### req.spec.init-no-installer-files — Installer outputs are not initialization outputs

Initialization SHALL NOT create files that exist only because Concorde is installed, such as the
Protocol copy under `.concorde/protocol/`.

## Protocol assets

### req.spec.protocol-assets-projected — The bundle carries only the Protocol

Every Protocol asset recorded in the tracked manifest SHALL be rendered only from the Protocol
text.

Concorde's own conventions are not part of the bundle.
The Modules that own them define them. Rendering the bundle is Distribution's build step.

### req.spec.protocol-assets-digest — Each asset records its digest

The tracked manifest SHALL record for every Protocol asset the digest of its rendered bytes.

Distribution's `protocol-manifest` command recomputes the digests.
