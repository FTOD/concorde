# Spec Protocol principles

Concorde Spec Protocol 2.0.0 defines Module Specs, Implementation Specs and their organization.
These requirements apply to project specifications, including the specifications of software that
implements this Protocol. They do not require the Protocol text to describe itself as a Module.

## Requirement language

**MUST** states a requirement for conformance. **MUST NOT** states a prohibition. **SHOULD** states a
recommendation that may be departed from for an explained reason. **MAY** states an allowed choice.
Examples illustrate the rules; their names, paths and subject matter are not prescribed.

### P1. A Module describes a cohesive software responsibility

A **Module** provides observable capabilities, called **features**, through explicit **interfaces**.
Its **architecture** describes the internal domain that supports those promises: concepts,
submodules, responsibilities, relationships and operating behavior. Domain is a view within a
Module, not an additional kind of specification.

A Module Spec MUST describe its features, usage interfaces and internal architecture. Interfaces
MUST state their inputs, outputs, effects, errors and compatibility requirements, including retry
or idempotency behavior where applicable. Implementation detail cannot replace these promises.

The Module definition applies recursively to submodules. Each Module MUST have at most one
structural parent, and parent relationships MUST be acyclic. Composition and dependency are
distinct: using a capability does not give the consumer structural ownership of its provider.
A capability shared by several consumers has one identity and is a sibling of those consumers.

### P2. Implementation descriptions have explicit file bindings

An **Implementation Spec** describes one realization and its relationship to Module contracts. It MUST bind
a nonempty set of exact, project-relative implementation files and describe their responsibilities,
interfaces, dependencies, constraints and relevant verification.

Each implementation file in the specified software MUST have exactly one authoritative
Implementation Spec owner. One Implementation Spec MAY bind several files, and several Modules
MAY reference the same Implementation Spec. Reuse does not merge Module identities or create
another structural parent. A directory or source layout does not establish a Module boundary.

An Implementation Spec MUST preserve the distinction between promised software behavior and the
implementation choices that realize it. An implementation description or a code change does not
silently amend a Module contract.

### P3. A Module Spec is a complete contract context

Each Module MUST have a stable identity and an explicitly registered, nonempty Markdown collection
with exactly one local `module.md` reading entry. Its complete collection MUST explain the Module's
promises and architecture without requiring another Module's documents, Implementation Specs or
source code to supply missing meaning.

For every direct dependency and submodule, the containing or consuming Module MUST state the
provider's identity, responsibility, selection condition and relied-upon promises locally.
These statements describe the composition or dependency from that Module's own perspective.

Document membership MUST be explicit. A parent, dependency, implementation reference, hyperlink,
directory location or selected feature does not add or remove documents from the collection.
Explicitly shared Module documents belong to every collection that registers them. Sharing one
document does not include the other documents of any referring Module.

Selecting a Feature or Interface MUST resolve to its providing Module and use that Module's full
contract context. The included files are its registered Markdown collection and explicitly
declared authored diagram sources. Spec management's Spec and Context rules define the query
domain and deterministic mapping. Implementation references and mentions of other Modules do not
expand that file set implicitly.

An unspecified promise MUST remain identifiable as unspecified. An honest draft MAY describe known
facts and name unresolved questions; it cannot claim completeness for the unresolved behavior.

### P4. Conformance concerns both meaning and structure

A claim of conformance MUST identify the Protocol version it applies to. Stable identity, explicit
membership, consistent relationship declarations and unique file ownership are structural
requirements. Complete and mutually consistent behavioral promises are semantic requirements.

A document heading, diagram or correctly shaped metadata block does not establish semantic
completeness. Structural checks can establish particular invariants; they cannot establish that
every intended behavior has been specified or that an implementation fulfills its contract.

The Protocol defines the meaning to preserve. A tool's configuration version, serialized registry
version, execution policy or review procedure is a separate agreement. Tools that represent these
specifications MUST preserve their identities, memberships, relationship meanings and contracts.

The Required format chapter defines the mandatory representation of authored Spec documents.
The Protocol templates demonstrate starting layouts; filling them out does not replace the
semantic and structural requirements above.
