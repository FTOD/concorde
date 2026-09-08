---
audience: shared
---

# Concorde Spec Protocol

Concorde Spec Protocol 1.2.0 is the specification standard within Concorde Framework. It defines the
organization, meaning and file format of Concorde Specs. The Framework includes this Protocol and
software that applies it: installable Skills, automatic validation, bounded agent workflows and
developer tools. Concorde's own Specs follow the same Protocol as consumer projects.

P1–P4 define the Concorde Spec Protocol. The separately authored Framework execution profile below contains
P5–P10: requirements on the software that uses these Specs. Packaging, version binding, model
processes and context injection are Framework mechanisms, not definitions of the Spec model.

## Spec organization and meaning

### P1. Business scope and implementation structure are separate dimensions

A project MUST distinguish Domain scopes from its Service/Module component structure.
These are the Domain/Service/Module modeling categories, separate from the Protocol's document
organization and file-format categories.

An **Ontology** defines the entities in a Domain, their types and meanings, and their named,
directed relationships. A Domain MUST explain its Ontology, including relevant external entities
and the relationships that cross its boundary. Group entities by meaningful type; a flat vocabulary
list without relationships is insufficient. Ontology here does not require a separate formal
ontology language. Physical Spec files describe entities; a file is not itself a Domain, Service
or Module merely because it describes one.

| Concept | Meaning | Primary specification obligations |
|---|---|---|
| Domain | A scope within which a business or problem-space vocabulary, rules, and system behavior are explained. | Define significant entities, their relationships and responsibilities, interaction triggers, invariants, state transitions, completion, failure, and retry semantics where applicable. Explain how the system operates within this scope, including relevant features. |
| Service | A self-contained capability with a clearly specified interaction boundary. | Describe consumer-facing features and their usage, then define complete boundary contracts: entry points, configuration, runtime inputs, results, effects, errors, compatibility, and applicable retry/idempotency behavior. |
| Module | A cohesive implementation responsibility exposed through an explicit API. | Define provided and required APIs, including signatures, types, preconditions, results, state/effect obligations, and failure behavior. Function calls are valid interactions. |

A Service's boundary can use an executable, a file exchange, HTTP, or another explicitly defined
or versioned standard format. Deployment topology is a separate declared property. A Module's
Spec MUST describe its interface rather than its algorithms or private implementation.

Domain MUST NOT be treated as a third component kind in one universal Domain/Service/Module
containment tree. The model MUST distinguish at least:

- Domain scope nesting: one Domain narrows a broader Domain's problem space.
- Component composition: a Service or Module is composed using other Services or Modules.
- Scope participation: a Service or Module participates in a Domain with a stated role.
- Behavioral relationships: entities call, produce, consume, constrain, or otherwise interact
  using named relationships with explicit direction and meaning.

Scope nesting and structural containment MUST be acyclic. They MUST NOT determine each other's
parent relationships. Scope participation MAY overlap: a shared Service or Module can participate
in multiple Domains without acquiring duplicate component identities or implementations. Each
Domain explains the role relevant to its own scope. Participation does not automatically grant
context access or mutation authority.

Every Domain and Service that routes work toward another target MUST state that target's stable ID,
local responsibility, relationship and selection condition in its own Spec. This routing view does
not substitute for the downstream target's complete Spec. It lets a main coordinator decide where
work belongs without reading a Module Spec or relying on registry metadata as hidden business
authority.

For every direct component `participates_in` relationship in the registry, the corresponding Domain
collection MUST contain exactly one machine-readable `concorde-participants` entry with the
component's stable target ID and kind, its Domain-local responsibility, the condition for selecting
it, and the nonempty promises that Domain relies on. A broader Domain MAY repeat a participant from
a nested Domain when it needs that participant locally, but the repeated declaration does not grant
the participant's Spec or code. Deterministic validation MUST reject missing, duplicate, unknown,
kind-mismatched or unrelated declarations. Before Domain planning or task generation, context
solving MUST report a missing direct declaration as a concrete Domain Spec gap and an inconsistent
declaration as conflicting.

Business entities such as Account, Transfer, and Daily Limit MUST have meaningful definitions
and responsibility assignments where they matter. They do not each require a separate Domain,
Service, or Module Spec. A Domain is responsible for explaining, for example, who checks a Daily
Limit, when a Transfer is allowed, what completion means, and which failures permit retry.

### P2. Features and APIs describe the appropriate consumer view

A Service Spec MUST explain its consumer-facing features: what a consumer can accomplish, how
the Service is used, and the associated promises and failures. Its boundary schemas MUST make
those promises executable and unambiguous.

A Module Spec MUST describe its APIs directly. Concorde MUST NOT require authors to wrap each
Module API in an artificial Feature document. Interface signatures and usage examples in a Spec
are permitted contract content; they do not authorize reading implementation source.

A Domain Spec MUST emphasize operating principles and collaborations. It MAY describe features
observable within its scope, including behavior that spans multiple Services or Modules.

Features and APIs used for selection, traceability, or lifecycle work MUST have stable identities
independent of document paths. A Feature or API belongs to its providing Spec target. Neither its
identity nor its filename creates an independent permission boundary. Concorde MUST NOT require a
separate Feature file or one Feature per Markdown file.

### P3. Every resolved Spec context is a self-contained document closure

Every Domain, Service, and Module MUST have a stable Spec target identity and an explicitly
registered, nonempty collection of Markdown documents. A physical document MAY be referenced by
one target or shared by several targets. Each document MUST declare one globally unique stable
document ID, the exact nonempty set of referencing target IDs, and whether its content is
`main_visible`. The registry remains the deterministic resolution index and MUST contain the same
memberships. Directory traversal, links, scope/component relationships, and another referencing
entity's remaining documents MUST NOT implicitly add context.

Every Domain MUST register exactly one target-local main document named `ontology.md`. It MUST
reference only that Domain and be `main_visible`. The filename identifies the main document only
within the explicit registered collection; no directory scan or collection ordering selects it.
Service and Module filenames and other Domain document filenames remain unrestricted.

The main document MUST define the Domain's scope and Ontology in an `Ontology` section: entity
types, meanings, responsibilities, internal relationships and relevant relationships with entities
outside the Domain. It MUST introduce an architecture overview that shows this boundary and those
relationships. Register that overview with `kind: architecture` and `recipe: system-overview` in
this Domain's diagram declarations. The view is associated with the main Spec; Framework publication supplies its rendering and
embedding behavior. Additional diagrams and topic documents remain
allowed. The main Spec is the Domain's canonical reading entry.

A main document is a human reading entry, not a replacement for the complete Spec context. Its
existence and declaration can be checked structurally; the presence of an Ontology heading or a
diagram does not prove that the Domain's meaning is complete. An initialized stub MUST explicitly
identify unknown business facts and may diagram only the known project-authoring boundary.

The resolved context for one target is the ordered union of its registered documents. Documents
referenced only by that target appear under `Target Spec`; documents referenced by several targets
appear once under `Shared Specs`. This one-hop document inclusion is not recursive entity-context
expansion. The complete resolved context MUST explain the target without requiring an undisclosed
parent, ancestor, child, collaborator, or related entity Spec.

Project knowledge SHOULD avoid unnecessary duplication. Exact shared truth—such as a vocabulary,
schema, invariant, state transition or common completion rule—SHOULD have one canonical shared
document when several targets rely on it. Target-local perspective remains local: a consumer still
explains when and why it uses a capability and how it handles results and failures, while the
provider explains what it offers. Natural-language similarity alone does not prove that two
perspectives are duplicate.

A shared document has collective authority and no implicit unique owner. A single-target author MAY
read it but MUST NOT change it. Changing shared truth requires a coordinated topology application in
which every candidate referencing target receives a separate context and returns identical proposed
bytes. Document identity, membership and `main_visible` changes follow the same reviewed, atomic
path. Any shared change intentionally changes the context identity of every referencing target.

#### Guidance for readable Spec collections

Prefer a main page that establishes an overall understanding of the Domain: what it concerns,
which entities matter, and how they collaborate. Detailed explanations usually fit best in the
relevant child Domain, Service, Module or topic Spec. Refer to those explanations where useful,
and include enough detail locally to make the actual collaborations and relied-upon promises clear.

Choose detail according to the subject and the reader's needs. A Domain need not be presented as
a black box, and no fixed hierarchy of abstraction levels is required. Internal structure and
cross-domain behavior can belong on the main page when they help explain how the Domain works.
Using or implementing a protocol does not by itself mean that its entire vocabulary or document
format needs to be restated in the surrounding Domain's overview.

Prefer a clear source for detailed definitions and explain their local use when referring to
them. A brief explanation of an unfamiliar term can help readers without reproducing the full
definition or making the main page a catalog of all concepts used by the project. Self-containment
is assessed across the complete registered context, not by repeating every fact on every page.
Human navigation links help readers find detail; required worker context still follows explicit
document membership rather than link traversal.

These are authoring recommendations, not additional validation gates. Different page organization,
an expanded Domain view or a different amount of detail is not by itself a conformance failure or
a blocking review finding. The existing requirements for meaningful contracts, explicit context
and sufficient information for the affected task continue to apply.

### P4. Concorde Spec Protocol conformance and Framework application

A project's Specs MUST follow one explicitly accepted Concorde Spec Protocol revision consistently. The
Protocol defines their modeling categories, document organization and required meaning. It does
not define a Domain by a runtime package, installation directory, model client or context-injection
mechanism. Those mechanisms belong to Concorde Framework's implementation contracts.

Project-specific rules MAY supplement the Concorde Spec Protocol but MUST NOT weaken its obligations.
Concorde Framework's own Specs MUST follow the same Protocol as the projects that use it. Its
own Domain and component decomposition is one application of the Protocol, not a mandatory
architecture for other projects. A valid structural check establishes format and consistency only;
semantic sufficiency remains relative to the intended task and requires explicit review.

@include prompts/protocol/framework-profile.md
