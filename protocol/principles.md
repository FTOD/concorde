# Spec Protocol principles

Concorde Spec Protocol 4.0.0 defines Module Specs and their organization. These requirements apply
to project specifications, including the specifications of software that implements this
Protocol. They do not require the Protocol text to describe itself as a Module.

## Requirement language

**MUST** states a requirement for conformance. **MUST NOT** states a prohibition. **SHOULD** states a
recommendation that may be departed from for an explained reason. **MAY** states an allowed choice.
Examples illustrate the rules; their names, paths and subject matter are not prescribed.

### P1. A Module describes a cohesive software responsibility in four parts

A **Module** is a cohesive software responsibility. Its Spec MUST contain four parts:

1. **Purpose**: a concise plain-prose statement of what the Module is for and for whom.
2. **Requirements**: what the Module as a whole must guarantee. Each requirement is one SHALL
   statement with its own stable identity; it expresses exactly one behavior and can be judged
   true or false against the Module.
3. **Scenarios**: the concrete situations in which the Module is used and how it must react, each
   written as a sequence of GIVEN, WHEN and THEN steps. A scenario is the unit that tests verify.
4. **Ontology**: the things that exist in the Module's world and how they relate. Its
   **entities** may be submodules, programs, files, records, concepts, interfaces at the Module
   boundary or external actors. Its **relationships** are directed edges between entities, each
   with a free-text label, which SHOULD be a verb such as "uses", "downloads", "saves" or "loads".

Purpose, requirements and scenarios form the Module's **functional spec**: they state what the
Module promises. The Ontology forms its **architecture spec**: it states how the Module is built.
The word ontology is used in its plain sense, the Module's account of what exists in its domain
and how those things stand to one another. It asks for no formal ontology language, and it is not
limited to business concepts: a program or a file the Module consists of belongs to its Ontology
as much as a business record or an external actor does.

Requirements and scenarios differ in granularity and in owner. A requirement is a coarse promise
about the Module and belongs to the Module alone. A scenario is one specific, testable situation;
whatever it must additionally guarantee is written into its own steps and prose rather than
attached as a separate requirement. Implementation detail cannot replace either part. An interface
is an entity whose behavior is given by scenarios; inputs, outputs, effects, errors, compatibility
and repeated-invocation behavior are scenario steps, not a separate kind of declaration.

The Module definition applies recursively to submodules. Each Module MUST have at most one
structural parent, and parent relationships MUST be acyclic. Composition and dependency are
distinct: using a capability does not give the consumer structural ownership of its provider.
A capability shared by several consumers has one identity and is a sibling of those consumers.

### P2. Implementation files are Module metadata

An entity MAY bind project-relative implementation files, each listing entry naming either an
exact file or a directory prefix. A directory prefix binds every regular file below it, including
files created later. The Module's **implementation files** are the union of what its entities'
entries bind. Binding files records which files realize the Module; it does not make those files
part of the Spec and does not let the code supply a promise the Spec omits.

Within one Module each file belongs to exactly one entity: when several entries of the same
Module cover a file, the most specific entry owns it, an exact file before a directory and a
longer directory before a shorter one. Several Modules MAY list the same file or directory when
one realization serves several contracts; that file then has several using Modules and a change
to it concerns all of them. Reuse does not merge Module identities or create another structural
parent. Listing a directory does not by itself establish a Module boundary; the Module's declared
purpose, requirements, scenarios and entities do.

A declared entry MAY be pending: intended but not yet created. A pending declaration describes an
intended output, not evidence that the file or directory exists. An entry that is declared without
a pending marker MUST exist.

Tests are implementation files like any other. A test declares which scenario it verifies by that
scenario's identity; a Spec never lists tests. A tool derives each scenario's verifying tests from
those declarations. That derived coverage is evidence about the tests, not part of the contract,
and a scenario without a declared test remains a promise the Module makes.

The files a Module lists, together with their pending status, form that Module's
**implementation context**; Spec management defines how it is resolved and keeps it separate from
the Module's Spec context.

### P3. A Module Spec is a complete contract context

Each Module MUST have a stable identity and an explicitly registered, nonempty Markdown collection
with exactly one local `module.md` reading entry. Its complete collection MUST explain the Module's
purpose, requirements, scenarios, entities and relationships without requiring another Module's
documents or source code to supply missing meaning.

For every direct dependency and submodule, the containing or consuming Module MUST state the
provider's identity, responsibility, selection condition and relied-upon promises locally.
These statements describe the composition or dependency from that Module's own perspective.

Document membership MUST be explicit. A parent, dependency, file binding, hyperlink, directory
location or selected scenario does not add or remove documents from the collection. Explicitly
shared Module documents belong to every collection that registers them. Sharing one document does
not include the other documents of any referring Module.

Selecting a scenario MUST resolve to its providing Module and use that Module's full contract
context. The included files are its registered Markdown collection. Spec management's Spec and
Context rules define the query domain and deterministic mapping. File bindings and mentions of
other Modules do not expand that file set implicitly.

Every scenario, requirement and entity is addressable: its identity is the anchor of its
definition, so a plain Markdown link to the defining document with the identity as fragment
reaches it. Such a link is navigation; it selects no context and changes no membership.

An unspecified promise MUST remain identifiable as unspecified. An honest draft MAY describe known
facts and name unresolved questions; it cannot claim completeness for the unresolved behavior.

### P4. Conformance concerns both meaning and structure

A claim of conformance MUST identify the Protocol version it applies to. Stable identity, explicit
membership, consistent relationship declarations, the four mandatory parts, one statement per
requirement and consistent file listings are structural requirements. Complete and mutually
consistent requirements, scenarios and relationships, and requirements that can each be judged
true or false, are semantic requirements.

A document heading, diagram or correctly shaped metadata block does not establish semantic
completeness. Structural checks can establish particular invariants; they cannot establish that
every intended behavior has been specified or that an implementation fulfills its contract.

The Protocol defines the meaning to preserve. A tool's configuration version, serialized registry
version, execution policy or review procedure is a separate agreement. Tools that represent these
specifications MUST preserve their identities, memberships, relationship meanings and contracts.

The Required format chapter defines the mandatory representation of authored Spec documents.
The Protocol templates demonstrate starting layouts; filling them out does not replace the
semantic and structural requirements above.
