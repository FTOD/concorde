# Spec requirements

The Module-wide obligations of the [Spec tooling](module.md) Module. The headings group them by
subject; each requirement belongs to the Module as a whole.

## Independence

### req.spec.no-owner-imports — Spec tooling depends on no other Module

Spec tooling SHALL NOT import code of any other Concorde Module.

Schemas, policies and file locations that other Modules own reach Spec tooling only through its
registration interface or as arguments of a call.

## Loading

### req.spec.registered-only — Documents come from declarations only

The loader SHALL treat as documents only the reading paths listed in some Module's `owns`, each
together with its exact `.json` companion.

A Markdown file found on disk, a Markdown link or a directory neighbour never adds a document.

### req.spec.no-writes — Loading and queries never write

Constructing a repository, querying it and validating a project SHALL NOT write any project file.

### req.spec.snapshot-reconstruct — A repository is a snapshot

A repository SHALL answer every query from the sources as they were when it was constructed.

A caller that needs to see a change constructs a new repository. Replacement bytes handed to the
constructor for the registry or for documents stay in memory and are never written.

### req.spec.deterministic-order — Same input, same answer

Repeated queries against the same repository SHALL return equal results in the same order.

### req.spec.no-implementation-read — Boundary sets never read code

Loading the Specs and computing boundary sets and impact indexes SHALL NOT read the contents of
implementation files.

Listing a directory to expand its entries is allowed; only paths are used. Validation's coverage
scan, which parses bound test files, is a separate step.

### req.spec.no-partial-repository — No partial repository

The loader SHALL NOT return a repository for use by consumers when the project has a problem that
makes a boundary untrustworthy.

These problems are listed in the [interface definitions](contracts.md#loading-failures). The
validator opens the repository so that the same problems become findings instead.

### req.spec.protocol-binding — Only the accepted Protocol is admitted

The loader SHALL admit a project only when its configuration binds exactly the Protocol copy under
`.concorde/protocol/`, that copy's assets match their recorded digests, and the copy's manifest
equals the Protocol manifest of the running Concorde package.

## Checks

### req.spec.every-check — Every Protocol check is evaluated

Validation SHALL evaluate every check listed in the Protocol's Checks chapter and report each
violation as a finding whose rule identity is that check's identity and whose severity is the
severity the chapter gives it.

### req.spec.all-findings — One run reports everything it can

Validation SHALL continue after a finding and report every further violation that the remaining
readable declarations and test files allow it to establish.

A test file that cannot be parsed is reported, and the other bound test files are still scanned.

### req.spec.status-from-errors — Only errors make a result invalid

The validation status SHALL be `invalid` exactly when at least one finding has severity error.

### req.spec.no-structural-proof — Structural checks are not semantic proof

A validation result SHALL NOT be represented as proof that a Spec is semantically sufficient or
that an implementation conforms to it.

The result carries an explicit marker saying semantic completeness is not proven.

### req.spec.link-fragments — Links to definitions resolve

Validation SHALL report as an error every link in Spec reading whose fragment has the form of a
node identity and does not name a definition in the linked document.

### req.spec.check-inputs — Configured check inputs exist and are safe

Validation SHALL report as an error every configured-check input that is missing, is not a
canonical project-relative path, or is reached through a symbolic link.

### req.spec.digest-per-assessment — Every result names what it assessed

Every validation result SHALL carry a digest of the exact configuration, registry, document members,
Protocol binding and configured-check input states it assessed.

## Registry mirror

### req.spec.registry-mirror-only — Regeneration changes only mirrored fields

Regenerating the registry SHALL rewrite only the mirrored fields of the Modules it already records,
leaving each record's identity and entry path and the set of recorded Modules unchanged.

The mirrored fields are every field of the entry's `module` block: `title`, `owns`, `contains`,
`uses`, `includes` and `participates`.

### req.spec.registry-check-read-only — Checking the mirror never writes

Checking the registry mirror SHALL report every record whose mirrored fields differ from its entry
without writing any file.

## Boundary sets and indexes

### req.spec.one-level-selection — Context selection is one level deep

Spec context selection SHALL follow only the selected Module's own `owns`, `contains`, `uses` and
`includes` declarations and never the relations of the Modules and documents they select.

Sharing a bound file with another Module adds nothing to either Module's Spec context.

### req.spec.both-members — Documents are selected whole

Every boundary set that contains a document SHALL contain both its reading member and its metadata
member.

### req.spec.write-sets-own-only — Write sets hold only the Module's own files

A Module's Spec scope and implementation scope SHALL contain only the documents it owns and the
files its own realizations cover.

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

Every impact index SHALL be computed from the loaded declarations and realization entries alone.

No index reads implementation file contents, test results or recorded evidence, and no index
query changes a boundary set.

## Coverage

### req.spec.coverage-from-tests — Coverage comes from the tests

Scenario coverage SHALL be read only from verification declarations in bound test sources, without
importing, compiling or running the tests.

## Typed values

### req.spec.typed-closed — Typed values are closed and exactly versioned

Checking a typed value SHALL reject an unknown type, a schema version other than the registered
one, a missing required field and any field its schema does not declare.

### req.spec.typed-offline — Typed values are checked offline

Checking a typed value or a contract schema SHALL use no network access and no schema outside
those registered or defined in the checked schema itself.

### req.spec.typed-registration-unique — One registration per type

Registering a type SHALL fail when its identity is already registered with a different version or
schema.

Registering the identical version and schema again is accepted and changes nothing, so an owner's
code may be loaded twice.

## File transactions

### req.spec.transaction-all-or-nothing — A transaction applies completely or not at all

A file transaction SHALL either write every listed file with its new content or leave every listed
file with its original bytes.

### req.spec.transaction-digest-bound — Stale input stops a transaction

A file transaction SHALL refuse to write when any listed file's current bytes do not match the
digest the transaction expects to replace.

A file expected to be absent has a null digest and must still be absent.

## Initialization

### req.spec.init-allowed-files — Initialization writes only its own files

Applying an initial proposal SHALL write only `.concorde/config.json`, `.concorde/specs.json` and
the members of the documents the proposed registry registers.

### req.spec.init-no-overwrite — Initialization never overwrites

Applying an initial proposal SHALL NOT replace a file that already exists.

### req.spec.init-explicit-envelope — Apply accepts only the exact proposal

Applying SHALL accept an initial proposal only as the complete typed value that propose returned.

### req.spec.init-apply-uses-proposal-configuration — The proposal carries the configuration

Applying SHALL write the configuration bytes contained in the proposal rather than any
configuration supplied with the apply request.

### req.spec.init-validated — The result must validate

Applying SHALL keep the written files only if the resulting project validates without errors.

### req.spec.init-honest-stub — The first Spec invents nothing

The initial Module stub SHALL state the project's purpose, behaviour and architecture as not yet
specified rather than invent concepts, requirements, scenarios or relations.

### req.spec.init-binds-existing-files — Existing files are bound at once

The initial Module stub SHALL bind every existing project file that version control tracks or
does not ignore, apart from document members, control records and generated outputs, so that the
new project validates without errors.

The binding is one realization of the root Module, Existing project files. It locates files and
promises nothing about them.

### req.spec.init-no-installer-files — Installer outputs are not initialization outputs

Initialization SHALL NOT create files that exist only because Concorde is installed, such as the
Protocol copy under `.concorde/protocol/`.

## Protocol assets

### req.spec.protocol-assets-projected — The bundle carries only the Protocol

Every Protocol asset recorded in the tracked manifest SHALL be rendered only from the Protocol text
and carry the digest of its rendered bytes.

Concorde's own conventions are not part of the bundle; they are defined by the Modules that own
them. Rendering the bundle and recomputing the digests is Distribution's build step.
