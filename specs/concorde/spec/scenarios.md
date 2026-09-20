# Spec scenarios

These precise specifications belong directly to the [Spec Module](module.md).
Subject headings organize the Module's obligations; they do not create separate owners or contexts.

## Terminology

| Term                                              | Meaning / definition                             |
| ------------------------------------------------- | ------------------------------------------------ |
| [Module](../module.md#terminology)                | Defined in Concorde Framework.                   |
| [Spec](../module.md#terminology)                  | Defined in Concorde Framework.                   |
| [Registry](../module.md#terminology)              | Defined in Concorde Framework.                   |
| [Context](../module.md#terminology)               | Defined in Concorde Framework.                   |
| [Snapshot](../module.md#terminology)              | Defined in Concorde Framework.                   |
| [Protocol binding](values.md#terminology)         | Defined in Identities and versions.              |
| [Ownership](registry.md#terminology)              | Defined in Registry.                             |
| [Composition](registry.md#terminology)            | Defined in Registry.                             |
| [Use](registry.md#terminology)                    | Defined in Registry.                             |
| [Reference](registry.md#terminology)              | Defined in Registry.                             |
| [Implementation binding](registry.md#terminology) | Defined in Registry.                             |
| [Document unit](values.md#terminology)            | Defined in Identities and versions.              |
| [Document role](values.md#terminology)            | Defined in Identities and versions.              |
| [Entity](../module.md#terminology)                | Defined in Concorde Framework.                   |
| [Requirement](../module.md#terminology)           | Defined in Concorde Framework.                   |
| [Scenario](../module.md#terminology)              | Defined in Concorde Framework.                   |
| [Structural validation](structure.md#terminology) | Defined in What structural validation tells you. |
| [Semantic completeness](structure.md#terminology) | Defined in What structural validation tells you. |
| [Initialization](initialize.md#terminology)       | Defined in Project initialization.               |
| [Initial proposal](initialize.md#terminology)     | Defined in Project initialization.               |
| [Issue](../module.md#terminology)                 | Defined in Concorde Framework.                   |
| [Spec context](../harness/context.md#terminology) | Defined in What information a worker receives.   |

## Spec

### scenario.spec.admit-inventory — Admitting a consistent Module inventory

- GIVEN an explicit registry with Module identities, at most one structural parent per Module, directed uses, entity listing entries and document ownership and references
- AND a shared provider is outside its consumers' structural ownership, even when those consumers have different parents or occupy different hierarchy levels
- AND a Protocol binding that matches the installed Protocol assets
- WHEN the repository is constructed
- THEN it admits immutable Module descriptors, file-ownership and reverse-user indexes without requiring sibling placement
- AND the provider retains its declared identity and parent, and uses alone add no documents or implementation permissions to a consumer
- AND it never reads a listed file's contents or a collaborator's Spec body to do so

### scenario.spec.reject-inconsistent-inventory — Rejecting a structurally inconsistent inventory

- GIVEN a registry with an unresolved parent or use, a composition cycle, a duplicate entry owner within one Module, a shared provider structurally owned by one of its consumers, or a listing entry that is a control or generated path, an existing path of the wrong kind, a registered Spec document or a directory containing one
- WHEN the repository is constructed
- THEN admission fails before any Agent runs
- AND no partial repository is returned

### scenario.spec.shared-file — A file shared by several Modules

- GIVEN two Modules each declare an entity whose listing entry binds the same implementation file, as an exact file or as a directory prefix that covers it
- WHEN the repository is admitted
- THEN both Modules keep their own entry in their own entity listing
- AND the reverse index reports every Module whose entries cover the file, so a change to it can be assessed against each of their contracts
- BUT within one Module the file belongs to exactly one of its entities, the one whose most specific entry covers it

### scenario.spec.external-reference — A Module references vendored material it does not own

- GIVEN a Module registration whose `references` include an entry of kind `external` naming the vendored documentation or source of a library, service or tool the Module uses
- WHEN the repository is admitted and the Module's external references are resolved
- THEN the entry enters no Spec context and no implementation file listing, its readable files are expanded with the ordinary exclusions plus media and archive suffixes, it is identified by one digest over those files, and validation reports an entry that does not exist as an error
- AND several Modules may reference the same material
- BUT an entry that is or contains a registered Spec document, that overlaps the Module's own file listing, or that is declared twice is rejected, and an external reference is never pending

### scenario.spec.directory-entry — A directory prefix binds a whole directory

- GIVEN an entity whose listing entry ends with `/` and names a directory this Module alone owns
- WHEN the repository resolves that Module's implementation files
- THEN every existing regular file below the directory is bound, excluding the Framework's skipped directories, dot-prefixed names, symlinks and skipped suffixes
- AND a file created below that directory later needs no new declaration
- BUT a more specific entry of the same Module still owns the file it names

## Registry

### scenario.spec.select-module — Selecting a Module's complete context

- GIVEN a registered Module identity
- WHEN a caller selects it
- THEN the repository returns that Module's complete descriptor including its owned documents and explicit references
- AND resolving its context includes only the full documents selected by those declarations, with original ownership retained

### scenario.spec.select-scenario-focus — Selecting through a scenario focus

- GIVEN a registered scenario identity that belongs to a Module
- WHEN a caller selects the Module with that scenario as focus
- THEN the repository returns the same complete Module descriptor as an unfocused selection
- AND the focus narrows attention only, never the returned file set

### scenario.spec.reject-foreign-focus — Rejecting a focus that is not the target's own

- GIVEN a scenario identity that belongs to a different Module than the one being selected
- WHEN a caller selects the target with that focus
- THEN selection fails with an invalid-focus error
- AND no descriptor is returned

### scenario.spec.query-files — Resolving a stable ID to its complete file set

- GIVEN a registered Module identity or a registered scenario identity
- WHEN a caller queries its Spec file set
- THEN the query returns the owning Module's complete resolved document context, deduplicated and sorted by canonical path
- BUT it neither follows uses, parentage nor entity listing entries, and it never reads the returned files' contents

## Registry values and selection

### scenario.spec.reject-unsupported-profile — Rejecting an unsupported configuration profile

- GIVEN a project configuration whose profile_version is not 15, or whose Protocol binding does not match the Protocol copy the installer placed under `.concorde/protocol/`, or whose copy differs from the installed package's Protocol
- WHEN the repository is constructed
- THEN construction fails with unsupported_profile or protocol_mismatch
- BUT a matching Profile 15 configuration with a current Protocol binding admits normally

### scenario.spec.task-control-values — Admit bounded task metadata without granting authority

- GIVEN a task-scope-feedback or task-identity-constraints value using the [task metadata shapes](contracts.md#values-task-authoring-transport-values)
- WHEN the Typed values interface validates it
- THEN a valid version-1 value is returned without rewriting its data
- AND unknown fields, malformed digests, other reason values, blank or duplicate reserved IDs, wrong types and unsupported versions raise TypedDataError with a code and field
- AND repeated validation of unchanged input returns the same data without project reads, writes or lifecycle effects
- BUT structural admission does not establish current task identity, complete history or phase authorization

## Spec structure and validation

### scenario.spec.validate-success — A conforming Spec state validates successfully

- GIVEN a registry and documents that satisfy every structural rule
- WHEN the validator runs
- THEN it returns success with no error findings and a source digest for the assessed state
- BUT success is not represented as proof that every promise is semantically complete

### scenario.spec.validate-structural-errors — Reporting structural errors, not semantics

- GIVEN a Module missing a required reading-entry section or its metadata companion, an unresolved scenario/requirement/entity identity collision, an entity entry union that disagrees with the registry, or a missing local dependency promise
- WHEN the validator runs
- THEN it returns invalid with one rule-identified, remediable finding per problem
- AND it does not attempt to judge whether the underlying behavior is correct

### scenario.spec.validate-pending-warning — A created entry still marked pending

- GIVEN an entity lists an exact file or a directory prefix as both present in files and in pending
- AND that file or directory now exists on disk
- WHEN the validator runs
- THEN it reports a warning, not an error
- BUT a declared entry whose file or directory is missing and not marked pending is still an error

### scenario.spec.validate-architecture-mismatch — Scoped diagram nodes must name declared entities

- GIVEN a Module's Relationships subsection flowchart names an undeclared entity, or an edge has no label
- WHEN the validator runs
- THEN it reports an architecture finding identifying the mismatched or unlabeled elements
- AND it requires every depicted node to name a declared local entity, while permitting scoped omission of inventory nodes

### scenario.spec.link-anchors — ID-shaped link fragments must resolve to their definition

- GIVEN a registered document with a local link whose fragment has the shape of a scenario, requirement, entity or canonical contract identity
- WHEN the validator resolves that fragment
- THEN it reports a link finding when no definition anywhere carries that identity
- AND it reports a link finding when the link's own document differs from the document that defines the identity
- BUT a link that correctly addresses its defining document, or whose fragment is not ID-shaped, passes without a finding

### scenario.spec.verification-declarations — Verification declarations live with the tests

- GIVEN the Python and TypeScript test files listed by every Module's entities
- WHEN the validator scans them for scenario verification declarations, Python decorators and TypeScript comments alike
- THEN a declared scenario ID that no registered Module defines is reported as an error
- AND a declaring file that its scenario's owning Module does not list is reported as a warning
- AND a scenario that no declaration names is reported as a warning against its defining document, unless its Module binds no implementation entry at all
- AND a listed Python file the validator cannot read for its declarations is reported as an error
- AND a malformed declaration, including a TypeScript comment that no test follows, is reported as an error
- BUT no Spec document lists tests; the declarations live only with the code

### scenario.spec.reader-parts — Read purpose, usage and design before detailed cases

- GIVEN a module-role entry with Purpose, Terminology, Usage, Design and Relationships and implementation-role companions for precise definitions
- AND paired companion documents that cover their own topics without repeating the entry layout
- WHEN structural validation runs
- THEN it accepts the complete source pairs and nonempty required reading explanations
- BUT it does not claim that those explanations are semantically complete or implemented

### scenario.spec.reader-parts-invalid — Reject malformed reader-oriented structure

- GIVEN an old enclosing-parts entry, missing metadata, missing or duplicate required sections, wrong heading levels or order, empty required explanations or an unresolved meaning anchor
- WHEN structural validation runs
- THEN it reports a remediable Module-structure error for each detected problem
- AND headings inside code fences do not satisfy required structure

### scenario.spec.internal-contract-context — Internal obligations retain ordinary identity

- GIVEN a Module defines an internal design requirement and verification scenario in an implementation-role companion
- AND a listed test declares that scenario's stable ID
- WHEN definitions, scenario context and verification coverage are resolved
- THEN the internal definitions retain the same Module ownership and identity rules as external definitions
- AND the scenario resolves the complete owned/direct-reference context, including both source members of every selected document unit
- AND the test declaration contributes coverage without creating another Spec kind or granting code access

### scenario.spec.document-roles — Separate explanation and precise definitions without filtering context

- GIVEN explicitly registered schema-2 document units with module or implementation roles
- WHEN the repository admits the units and resolves their Module context
- THEN the entry and explanatory topics contain no formal requirements, scenarios or canonical structured contracts
- AND those precise definitions are admitted only in implementation-role companions owned directly by the Module
- AND both roles contribute their complete reading and metadata members to Module and scenario queries
- BUT missing or unknown roles, version-1 metadata, an implementation-role module.md, or the retired concorde.publication extension fail admission without automatic migration

### scenario.spec.reference-resolution — Resolve only the selecting Module's references

- GIVEN A references Module B and one B-owned document while B references C
- WHEN A's context is resolved
- THEN each B-owned document appears once with every direct inclusion reason and original owner
- AND no C-owned document appears unless A also directly references it
- AND a scenario query for a B-owned definition resolves B's complete context, including its C reference

### scenario.spec.reference-invalid — Reject invalid ownership or reference identities

- GIVEN a duplicate owner, wrong-kind or missing reference, unsafe alias, or binding whose definition is absent from the resolved context
- WHEN the registry is validated
- THEN the validator reports the affected document, Module and declaration without silently adding files
- AND no conforming context or interface agreement is claimed

The maintenance-only `scripts/development/check-spec-v5.py` audits the authored registry without
constructing the runtime repository. It checks ownership, references, binding/example shape,
links, reading-subset structure, definition/diagram grammar, entity/file/dependency consistency and manifest
digests; `--base REVISION` also checks stable Requirement/Scenario/Entity ownership against Git.
It is independent documentation evidence, not a lifecycle check or a semantic-completeness claim.

## Project initialization

### scenario.spec.propose-initialization — Proposing an initial project structure

- GIVEN an uninitialized project, a name and a supported operation configuration
- WHEN the developer requests action propose
- THEN the operation returns a typed concorde-project-proposal with a null base_digest, every file's before_digest null, and an honest Module stub
- AND no project file changes yet

### scenario.spec.apply-initialization — Applying an accepted proposal

- GIVEN a previously returned proposal whose destinations are still absent and whose Protocol binding is current
- WHEN the developer requests action apply with that exact proposal
- THEN the operation validates the complete resulting registry and documents and commits every file in one transaction
- AND it creates nothing that exists only because Concorde is installed: the Protocol copy, and the Issue directory defaults are the installer's outputs
- AND the response reports status applied with the applied paths

### scenario.spec.reject-already-initialized — Rejecting an already-configured project

- GIVEN a project whose configuration already exists
- WHEN initialization is requested
- THEN the operation fails with already_initialized
- AND no existing file is overwritten

### scenario.spec.reject-stale-or-invalid-proposal — Rejecting a stale, invalid or out-of-bound proposal

- GIVEN a proposal whose identity, registry/Protocol binding or destination set is invalid, out of bound, or whose preconditions changed since it was proposed
- WHEN the developer requests action apply
- THEN the operation fails with invalid_proposal, permission_denied or stale_proposal as appropriate
- AND it does not apply a partial file set

### scenario.spec.rollback-on-failure — Restoring original bytes on failure

- GIVEN an accepted proposal is being applied
- WHEN a filesystem or transaction failure occurs after some files were staged
- THEN the operation restores the original bytes and cannot report applied
- BUT a failure during that recovery itself is reported as a failure, never as a successful rollback
