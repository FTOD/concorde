# Spec Protocol principles

Concorde Spec Protocol 6.0.0 defines Module Specs and their organization. These requirements apply
to project specifications, including the specifications of software that implements this Protocol.
They do not require the Protocol text to describe itself as a Module.

## Requirement language

**MUST** states a requirement for conformance. **MUST NOT** states a prohibition. **SHOULD** states
a recommendation that may be departed from for an explained reason. **MAY** states an allowed
choice. Examples illustrate the rules; their names, paths and subject matter are not prescribed.

### P1. A Module describes one responsibility for its consumers and its implementers

A **Module** is a cohesive software responsibility. It is a unit of specification, not a unit of
implementation: a Module need not correspond to a package, directory, process, service or other
physical unit. Its realization may be spread across several such units, shared with other Modules,
or supplied entirely by its children. The Module's boundary is established by its purpose,
requirements, scenarios and entities; its file bindings record where that responsibility is realized
and do not define it.

A Module's Spec MUST contain two reader-oriented parts:

1. **Usage & Contract** explains how to use the Module and what a consumer can rely on. It MUST
   explain its purpose, intended consumers and scope, when to use it, the concepts needed to use
   it, prerequisites and entry points, inputs, results, effects, errors and applicable repeat,
   cancellation and compatibility behavior. Start with coherent usage prose, not a catalog of
   formal statements that the reader must assemble into instructions. Requirements and concrete
   scenarios make the promises precise; they do not replace the usage explanation.
2. **Architecture & Realization** explains how the Module fulfills those promises. It MUST
   explain the design, responsibility decomposition, collaborations, relevant control/data flow
   and state, internal invariants and constraints, and realization through entity file bindings
   or children. Explain significant design choices and how they support the external guarantees;
   an entity inventory and a diagram alone are not an architecture explanation. This part is
   normative where it prescribes a constraint, not merely commentary on current source code.

The dividing question is whether a fact is needed to use or depend on the Module, or to implement
and maintain it. A consumer may be a person, another Module or external software; "external" is
relative to this Module, not a requirement for a public API, command or physical package. A logical
or composite responsibility MUST NOT invent an executable interface just to populate a template.
Internal security or concurrency constraints remain binding, while their consumer-visible effects
belong in Usage & Contract. A missing or inapplicable behavior MUST be stated honestly rather than
invented. A Spec describes intended design, not proof that its realization already conforms.

Purpose, requirements, scenarios, entities and relationships remain information elements within
these two parts, not competing top-level reading structures. A **requirement** is one decidable
SHALL statement with its own stable identity, expressing one Module-wide obligation. A **scenario**
is a concrete sequence of GIVEN, WHEN and THEN steps and is the unit tests verify. Requirements
and scenarios MAY specify internal constraints in Architecture & Realization as well as external
behavior in Usage & Contract. Define each obligation once in the appropriate part and link to it
from its realization or verification discussion; neither part may silently redefine the other.

**Entities** are the things in the Module's world: submodules, programs, files, records, concepts,
boundary interfaces or external actors. **Relationships** are directed edges between entities with
free-text labels, which SHOULD be verbs such as "uses", "saves" or "loads". The internal entity
inventory records identities and implementation bindings; explain consumer-facing concepts and
interface meaning in the external part without making a second canonical definition. Ontology
may be a useful modeling technique, but is not the name or the entirety of the architecture part.

Requirements and scenarios differ in granularity and in owner. A requirement is a coarse promise
about the Module and belongs to the Module alone. A scenario is one specific, testable situation;
whatever it must additionally guarantee is written into its own steps and prose rather than attached
as a separate requirement. Implementation detail cannot replace either part. An interface is an
entity whose behavior is given by scenarios; inputs, outputs, effects, errors, compatibility and
repeated-invocation behavior are specified through a canonical interface definition and its related
scenarios, not a second kind of Spec.

The Module definition applies recursively to submodules. Each Module MUST have at most one
structural parent, and parent relationships MUST be acyclic. Composition and dependency are
distinct: using a capability does not give the consumer structural ownership of its provider. A
capability shared by several consumers has one identity and is a sibling of those consumers.

### P2. Implementation files are Module metadata

An entity MAY bind project-relative implementation files, each listing entry naming either an exact
file or a directory prefix. A directory prefix binds every regular file below it, including files
created later. The Module's **implementation files** are the union of what its entities' entries
bind. Binding files records which files realize the Module; it does not make those files part of the
Spec and does not let the code supply a promise the Spec omits.

Within one Module each file belongs to exactly one entity: when several entries of the same Module
cover a file, the most specific entry owns it, an exact file before a directory and a longer
directory before a shorter one. Several Modules MAY list the same file or directory when one
realization serves several contracts; that file then has several using Modules and a change to it
concerns all of them. Reuse does not merge Module identities or create another structural parent.
Listing a directory does not by itself establish a Module boundary; the Module's declared purpose,
requirements, scenarios and entities do.

A declared entry MAY be pending: intended but not yet created. A pending declaration describes an
intended output, not evidence that the file or directory exists. An entry that is declared without a
pending marker MUST exist.

Tests are implementation files like any other. A test declares which scenario it verifies by that
scenario's identity; a Spec never lists tests. A tool derives each scenario's verifying tests from
those declarations. That derived coverage is evidence about the tests, not part of the contract, and
a scenario without a declared test remains a promise the Module makes.

The files a Module lists, together with their pending status, form that Module's **implementation
context**; Spec management defines how it is resolved and keeps it separate from the Module's Spec
context.


### P3. A Module resolves a complete contract context

Each Module MUST have a stable identity and a nonempty `documents` collection that it owns, with
exactly one local `module.md` reading entry. Every physical Spec document MUST have exactly one
owning Module. Ownership of a requirement, scenario, entity or interface definition follows its
defining document and remains unchanged when another Module reads it.

Each Module MUST independently declare `references` in its registration record: what the Module
reads but does not own. A reference selects either another Module's entire owned document
collection or one registered document by stable identity, or it names **external** reference
material: a project-relative file or directory prefix holding vendored documentation or source of
a library, service or tool the Module relies on, pinned at a known revision. References determine
context inclusion, not ownership, composition, dependency, implementation file binding or
permission. An external reference is never included in the Spec context and supplies no promise
the Spec omits: it is neither a Spec document nor an implementation file, it is never pending,
and a tool that gives an agent knowledge of external capabilities takes that knowledge from these
declarations rather than from an undeclared network or dependency installation. Only the selected Module's references are expanded, once:
referenced Modules' references and Markdown links MUST NOT be followed. The complete context is the
deduplicated union of full owned and directly referenced documents. That context is the reader's
visibility scope: a tool makes all of it available and nothing outside it, and how the tool delivers
it is the tool's choice rather than part of this Protocol.

That resolved context MUST explain both reader-oriented parts: the selected Module's purpose,
correct use and guarantees, and the design that realizes them, with requirements, scenarios,
entities and relationships, without undeclared reading or source code supplying missing meaning. For each
dependency and child the local contract states responsibility, selection conditions, which canonical
guarantees it relies on and its own obligations or reactions. It SHOULD link to included provider
definitions instead of copying them. Shared interfaces MAY be ordinary documents owned by one Module
and referenced by many; they do not require a new Spec kind or Module.

A scenario query MUST first resolve its unique owning Module, then return that Module's complete
context. Context resolution MUST be deterministic and record identities, inclusion provenance and
exact byte digests. Referenced definitions do not become local entities or requirements, and do not
add provider implementation files or diagram nodes to the consumer.

All prose references use ordinary Markdown links. Publishing renders them as links, never content
inclusion; only registered Module references select Agent context. Every requirement, scenario,
entity and structured contract has its stable identity as its definition anchor.

A missing required definition is a gap. A reader MUST NOT silently fetch more files to repair it. An
honest draft identifies unresolved meaning and does not claim completeness for it.

### P4. Conformance concerns both meaning and structure

A claim of conformance MUST identify the Protocol version it applies to. Stable identity, unique
document ownership, explicit one-level references, consistent relationship declarations, the two
mandatory reader-oriented parts, one statement per requirement and consistent file listings are structural
requirements. Complete and mutually consistent requirements, scenarios and relationships, and
requirements that can each be judged true or false, are semantic requirements.

A document heading, diagram or correctly shaped metadata block does not establish semantic
completeness. Structural checks can establish particular invariants; they cannot establish that
every intended behavior has been specified or that an implementation fulfills its contract.

The Protocol defines the meaning to preserve. A tool's configuration version, serialized registry
version, execution policy, context delivery mechanism or review procedure is a separate agreement.
Tools that represent these specifications MUST preserve their identities, ownership, context
inclusion, relationship meanings and contracts.

The Required format chapter defines the mandatory representation of authored Spec documents. The
Protocol templates demonstrate starting layouts; filling them out does not replace the semantic and
structural requirements above.
