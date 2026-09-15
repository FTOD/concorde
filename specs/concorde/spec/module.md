# Spec

## Purpose

Spec supplies explicit project identities, complete contract-context queries, structural
validation and honest initialization to developers and Framework tools. It admits and pins the
independent Spec Protocol rather than deciding the project's intended software behavior.

## Usage

Use this Module when a tool needs to identify a Module, resolve its complete Spec context,
validate authored documents or initialize a project. Construct a `SpecRepository` from an explicitly
configured project whose installed Protocol matches its accepted binding. Select a Module ID, or
query a scenario to select its sole owner's context. Use `spec_context` for sources and provenance;
implementation listing queries are separate and do not implicitly read source contents.

A registry records ownership, composition, dependencies and reading references as distinct facts.
A document has one owner; a file may realize several Modules. Usage explains correct
use, and Design explains design; both remain in every selected full document.
Reconstruct the repository after changes. Invalid identities, paths, references or bindings reject
admission rather than returning a partial result. `validate_repository` is read-only; its success
establishes structural checks only. For a new project, propose then apply `concorde-init`; existing
configuration is not overwritten. Read [queries](registry.md), [values](values.md),
[validation](structure.md) and [initialization](initialize.md) for exact inputs and outcomes.

## Design

<a id="entity.spec.registry"></a><a id="entity.spec.protocol-binding"></a><a id="entity.spec.repository-api"></a><a id="entity.spec.validator"></a><a id="entity.spec.init-capability"></a><a id="entity.spec.spec-model"></a><a id="entity.spec.typed-values"></a><a id="entity.spec.file-transactions"></a><a id="entity.spec.protocol-text"></a><a id="entity.spec.protocol-assets"></a>

Registry admission first establishes explicit identities and relationship indexes. Document
parsing then resolves owned definitions, while a separate one-level union resolves context with
source digests and inclusion reasons. Keeping those operations distinct realizes the external
promise that reading a provider definition neither acquires ownership nor adds its implementation.
Entity bindings and the reverse file index independently identify affected implementation users.

The reading content and associated metadata are validated as document structure, not used as context filters. Definitions
are still parsed across the owner's whole collection, including internal constraints and scenarios.
Initialization uses a before-digest file transaction and validates its complete proposed overlay;
structural validation and test-declared coverage remain evidence rather than semantic proof.
Shared typed-value and transaction realizations have their own exact entity entries below.

Registry metadata and the Protocol binding are admitted before source bodies. The SpecRepository API resolves complete document units: reading Markdown plus associated metadata, each with its own byte digest and source role. The Validator checks their structure and consistency without proving semantic completeness. The Spec model keeps ownership and reference selection distinct from implementation access.

Initialization capability creates an honest paired draft through File transactions, which preserves original bytes if applying a proposal fails. Typed values centralize canonical encoding, safe paths and offline schema evaluation. Protocol text is the independently authored standard; Protocol assets packages it with the Framework profile for exact, verified installation.

## Relationships

The registry separates semantic Module identities from implementation-file ownership: Modules register documents and entities, entities bind listing entries that are exact files or directory prefixes, and a file may be bound by several Modules while belonging to one entity within each, the owner of its most specific entry. Admission creates immutable selection records and reverse indexes from exact declarations; overlay bytes support candidate inspection without writes. Selection never walks a dependency to read another Module's body. The Spec model's own package entry points, the Validator and the Initialization capability are three ways of using the same admitted Registry and Protocol binding; the Protocol assets entity packages the authored Protocol text for runtime distribution without becoming a second authority over its meaning.

```mermaid
flowchart TB
    accTitle: Spec entities and relationships
    accDescr: A pinned Protocol binding and the explicit Registry are admitted together. The SpecRepository API, the Validator and the Initialization capability are interfaces realized by the Spec model program, which depends on the shared Typed values and File transactions programs and verifies the freshness of the packaged Protocol assets, themselves built from the authored Protocol text.
    registry["Registry"]
    binding["Protocol binding"]
    repositoryApi["SpecRepository API"]
    validator["Validator"]
    initCapability["Initialization capability"]
    specModel["Spec model"]
    typedValues["Typed values"]
    fileTransactions["File transactions"]
    protocolText["Protocol text"]
    protocolAssets["Protocol assets"]
    binding -->|is admitted together with| registry
    repositoryApi -->|admits| registry
    repositoryApi -->|admits| binding
    validator -->|checks| registry
    initCapability -->|creates| registry
    repositoryApi -->|realized by| specModel
    validator -->|realized by| specModel
    initCapability -->|realized by| specModel
    specModel -->|depends on| typedValues
    specModel -->|depends on| fileTransactions
    specModel -->|verifies freshness of| protocolAssets
    protocolAssets -->|packages| protocolText
```

## Requirements

### req.spec.no-body-read — Metadata resolution does not read collaborator bodies

Resolving a Module's identity, ownership or file listing SHALL NOT read a collaborator Module's
Spec body or a listed file's contents.

### req.spec.one-owner-per-module — One owning entity per bound file

Within one Module, a bound implementation file SHALL belong to exactly one entity, the owner of the
most specific entry that covers it.

### req.spec.directory-entry — Directory prefix binds every file below it

A listing entry that ends with `/` SHALL bind every regular file below that directory.

### req.spec.directory-no-spec-document — No Spec document inside a listed directory

A listed directory SHALL NOT contain a registered Spec document.

### req.spec.sibling-sharing — Shared providers stay siblings of their consumers

A Module used by more than one consumer SHALL share the same structural parent as its consumers.

### req.spec.no-structural-proof — Structural checks are not semantic proof

Structural validation SHALL NOT be represented as proof of semantic completeness.

## Scenarios

The registered companion documents [registry](registry.md), [values](values.md), [structure](structure.md) and [initialize](initialize.md) define most scenarios; this section introduces the Module's core admission behavior.

### scenario.spec.admit-inventory — Admitting a consistent Module inventory

- GIVEN an explicit registry with Module identities, one structural parent per Module, directed uses, entity listing entries and document ownership and references
- AND a Protocol binding that matches the installed Protocol assets
- WHEN the repository is constructed
- THEN it admits immutable Module descriptors, file-ownership and reverse-user indexes
- AND it never reads a listed file's contents or a collaborator's Spec body to do so

### scenario.spec.reject-inconsistent-inventory — Rejecting a structurally inconsistent inventory

- GIVEN a registry with an unresolved parent or use, a composition cycle, a duplicate entry owner within one Module, a non-sibling shared provider, or a listing entry that is a control or generated path, an existing path of the wrong kind, a registered Spec document or a directory containing one
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

## Unresolved information

`spec_files` and `spec_context` now resolve Module and scenario queries through unique document
ownership and explicit one-level references. The retired `spec_pair` is not a Protocol 5 query.
Initialization emits the paired reading/metadata Module stub, Profile 14/schema 5 and owner metadata.
`model.py` retains the compatibility `ProposalFile` record alongside `Finding` and `ToolResult`.

The runtime admits Profile 14/schema 5, validates canonical definitions and participant bindings,
and records exact source bytes, ownership, declarations and inclusion provenance. Structural
validation and passing tests do not establish semantic completeness.
