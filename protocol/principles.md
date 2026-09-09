# Spec Protocol principles

Concorde Spec Protocol 3.0.0 defines Module Specs and their organization. These requirements apply
to project specifications, including the specifications of software that implements this
Protocol. They do not require the Protocol text to describe itself as a Module.

## Requirement language

**MUST** states a requirement for conformance. **MUST NOT** states a prohibition. **SHOULD** states a
recommendation that may be departed from for an explained reason. **MAY** states an allowed choice.
Examples illustrate the rules; their names, paths and subject matter are not prescribed.

### P1. A Module describes a cohesive software responsibility in four parts

A **Module** is a cohesive software responsibility. Its Spec MUST contain four parts:

1. **Purpose**: a concise plain-prose statement of what the Module is for and for whom.
2. **Scenarios**: the situations in which the Module is used and how it must react, each written
   as a sequence of GIVEN, WHEN and THEN steps, with **requirements** stated as SHALL sentences
   attached to one scenario or to the Module as a whole.
3. **Entities**: the things the Module consists of. An entity may be a submodule, a program, a
   file, a record, a concept, an interface at the Module boundary or an external actor.
4. **Relationships**: how the entities relate. There is no predefined vocabulary; each
   relationship is a directed edge with a free-text label, which SHOULD be a verb such as
   "uses", "downloads", "saves" or "loads".

Purpose and scenarios form the Module's **functional spec**: they state what the Module promises.
Entities and relationships form its **architecture spec**: they state how the Module is built.
Implementation detail cannot replace either. An interface is an entity whose behavior is given by
scenarios; inputs, outputs, effects, errors, compatibility and repeated-invocation behavior are
scenario steps and requirements, not a separate kind of declaration.

The Module definition applies recursively to submodules. Each Module MUST have at most one
structural parent, and parent relationships MUST be acyclic. Composition and dependency are
distinct: using a capability does not give the consumer structural ownership of its provider.
A capability shared by several consumers has one identity and is a sibling of those consumers.

### P2. Implementation files are Module metadata

An entity MAY bind a set of exact, project-relative implementation files. The Module's
**implementation files** are the union of its entities' files. Binding a file records which
files realize the Module; it does not make those files part of the Spec and does not let the code
supply a promise the Spec omits.

Within one Module each file belongs to exactly one entity. Several Modules MAY list the same file
when one realization serves several contracts; that file then has several using Modules and a
change to it concerns all of them. Reuse does not merge Module identities or create another
structural parent. A directory or source layout does not establish a Module boundary.

A declared file MAY be pending: intended but not yet created. A pending declaration describes an
intended output, not evidence that the file exists. A file that is declared without a pending
marker MUST exist.

The files a Module lists, together with their pending status, form that Module's
**implementation context**; Spec management defines how it is resolved and keeps it separate from
the Module's Spec context.

### P3. A Module Spec is a complete contract context

Each Module MUST have a stable identity and an explicitly registered, nonempty Markdown collection
with exactly one local `module.md` reading entry. Its complete collection MUST explain the Module's
purpose, scenarios, entities and relationships without requiring another Module's documents or
source code to supply missing meaning.

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

An unspecified promise MUST remain identifiable as unspecified. An honest draft MAY describe known
facts and name unresolved questions; it cannot claim completeness for the unresolved behavior.

### P4. Conformance concerns both meaning and structure

A claim of conformance MUST identify the Protocol version it applies to. Stable identity, explicit
membership, consistent relationship declarations, the four mandatory parts and consistent file
listings are structural requirements. Complete and mutually consistent scenarios, requirements
and relationships are semantic requirements.

A document heading, diagram or correctly shaped metadata block does not establish semantic
completeness. Structural checks can establish particular invariants; they cannot establish that
every intended behavior has been specified or that an implementation fulfills its contract.

The Protocol defines the meaning to preserve. A tool's configuration version, serialized registry
version, execution policy or review procedure is a separate agreement. Tools that represent these
specifications MUST preserve their identities, memberships, relationship meanings and contracts.

The Required format chapter defines the mandatory representation of authored Spec documents.
The Protocol templates demonstrate starting layouts; filling them out does not replace the
semantic and structural requirements above.
