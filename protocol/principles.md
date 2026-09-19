# Spec Protocol principles

Concorde Spec Protocol 10.0.0 defines Module specifications, their complete content and the subset
intended for human reading. It applies to project Specs, including those of software implementing
this Protocol. The standard's own chapters need not describe themselves as software Modules.

## Requirement language

**MUST** is required for conformance; **MUST NOT** is prohibited. **SHOULD** is recommended and may
be departed from for an explained reason. **MAY** permits a choice. Examples prescribe neither
project names nor business behavior.

### P1. A Module has one complete specification and a readable subset

A **Module** is one cohesive software responsibility, not necessarily a package, directory, service
or process. Its realization may span or share physical units or be supplied entirely by children.
Its purpose, behavior, concepts and relationships establish its boundary; file bindings locate its
realization and do not establish that boundary.

Let `Content(M)` be the complete specification content owned by Module M and `Reading(M)` its
human-readable content. **Reading(M) is a subset of Content(M)**. The Protocol defines membership
and completeness of both, not a docsite's layout. Reading is not an independently maintained
summary, a weaker contract or whatever a renderer chooses to retain.

Reading content MUST explain:

- **Purpose:** responsibility, intended consumers, scope and relevant non-goals.
- **Terminology:** the concepts needed to understand this document, introduced before detailed use.
  Give each term one canonical Terminology definition; elsewhere link directly to that table and
  MAY repeat or faithfully restate its meaning with explicit source attribution for reading convenience.
  This is a reader aid, not an entity inventory or file-binding declaration.
- **Usage:** when and how to use the Module, concepts and prerequisites, actual entry points,
  inputs, results, effects, errors and applicable repeat, cancellation and compatibility behavior.
  Start with a coherent explanation rather than asking readers to assemble instructions from formal
  statements. A logical responsibility MUST NOT invent an executable interface to fill a template.
- **Design:** responsibility decomposition, collaborations, significant control/data flow and state,
  internal invariants, constraints, choices and how they support the guarantees. Intended design
  is not proof that existing code conforms. A diagram or inventory is not a design explanation.
- **Relationships:** what the participating entities mean, how they collaborate, and the distinction
  between structural composition and operation use. Explain conditions and reactions that arrows
  cannot express. A scoped diagram is not required to reproduce the entire entity inventory.
- **Precise obligations:** Module requirements, concrete scenarios, interface definitions and the
  local duties and relied-upon guarantees of collaborators. Infrequent failures, concurrency,
  security and compatibility promises remain readable even when they are not on the initial path.

Identity, ownership, registration, implementation bindings and pending markers are machine
metadata, not mandatory reading. Their mechanical records MUST NOT be mixed into the reading
body. Metadata MUST refer to readable meaning rather than become the only place an essential
responsibility or obligation is stated. This distinction is about information, not syntax:
interface schemas and examples can be reading content; a file listing written as a Markdown table
is still implementation metadata. A publisher MAY expose metadata as an auxiliary inspection view.

The complete Module specification has two explicit document roles, both within Reading(M):

- **Module Specs** (`module`): the reading entry and explanatory topic documents. The entry follows
  **Purpose, Terminology, Usage, Design, Relationships**. Topics explain concepts, correct use, collaborations,
  significant design and important guarantees. Together these explanations MUST establish a usable
  mental model without requiring readers to reconstruct it from formal definitions. They MUST NOT
  become empty link indexes or independently maintained summaries.
- **Implementation Specs** (`implementation`): the precise normative requirements, scenarios and
  interface contracts that implementations must satisfy, including external behavior and internal
  constraints. They are not implementation source, temporary plans or descriptions of incidental code.

Formal requirement and scenario definitions MUST occur only in implementation-role document units.
The entry and module-role topics MUST NOT define them. Canonical structured interface contracts
MUST also be defined in implementation-role units; explanation, usage examples and links to those
contracts belong in Module Specs. Define each precise obligation once. Explanations retain important
meaning and link to its exact definition rather than duplicating a second formal contract.

The intended reader understands general software concepts but does not know the project's
implementation, internal type names, execution library or migration history. Explanatory reading
MUST let that reader explain the problem, when to use the Module, a normal interaction, its result,
important stopping conditions and why the design works. Purpose uses ordinary verbs before internal
names. Usage presents a representative normal path before exceptional recovery. Illustrative examples
SHOULD make abstract distinctions concrete; they explain existing promises, not invent new ones.

Role separation is about meaning, not just heading syntax. Exact private APIs, wire fields, byte
algorithms, persistence layouts, internal limits and executable-node/state catalogs belong in
Implementation Specs even when written as ordinary prose without SHALL or scenario headings.
Module Specs retain architecture, design reasons, actual public entry points, and any limits or
hazards a consumer needs for correct use. They MUST NOT hide destructive defaults, security limits
or known unfulfilled guarantees behind detail links. A simple usage example is not an API inventory.

Design MUST connect a decision to the problem it solves and the guarantee it supports, not merely
list implementation calls in order. Conceptual diagrams SHOULD answer one reader question with
recognizable labels. They MUST be distinguished from exact executable diagrams; the latter belong
in implementation-role units and remain the single authority for execution topology. A concept view
must not become a competing executable model. Explain relevant collaborations locally, but do not
repeat generic permission, compatibility or completeness disclaimers on every path. Historical
migration records MUST be labeled with their baseline and kept apart from the default explanation
of current behavior; preserve any still-applicable obligations in the current specification.

Terminology tables MUST contain only concepts relevant to the page. A local definition uses familiar
language rather than another chain of unexplained terms. An imported term links directly to its
canonical document's Terminology table and identifies that source. Its row MAY repeat or faithfully
restate the definition so readers need not navigate away to understand the term. Such a restatement
MUST preserve the canonical meaning without adding, removing or changing its constraints; it is not
another authoritative definition. Changes to the canonical definition MUST include checking affected
restatements for consistency. An intermediate glossary, even one containing a restatement, is not the
canonical source. This permission applies only to terminology explanations, not duplicate formal
requirements, scenarios, interface contracts or schemas. Neither links nor restatements grant context:
required defining units must still be explicitly included.
Entity identities and realization bindings stay in metadata; Design and Relationships explain how
particular entities participate. A glossary neither duplicates those declarations nor replaces that
contextual explanation. Identical words with distinct meanings must be qualified explicitly.

Both roles belong directly to the same owning Module. A topic such as Registry is an explanation,
not a new owner, sub-Module or requirements container. Implementation Specs MAY be split into several
owned units and grouped by subject, but requirements and scenarios remain Module-owned. Roles
MUST be explicit metadata, never inferred from paths, headings, body syntax or publishing preferences.
Roles change neither complete context inclusion nor execution authority. There are no mandatory
usage/architecture wrappers or standalone entity-inventory chapters.

A **requirement** is one decidable Module-wide SHALL statement with a stable identity. A **scenario**
is one testable situation expressed through GIVEN, WHEN and THEN steps. A situation-specific
obligation belongs in its scenario, not in a second attached requirement. Both external behavior
and internal constraints are normative where prescribed. Define each obligation once and link to
it; editorial organization MUST NOT silently weaken, duplicate or contradict it.

**Entities** are named programs, records, concepts, interfaces, files, Modules or boundary actors.
Their identities and bindings are metadata; their meaning belongs in reading prose. **Relationships**
are directed edges with meaningful free-text labels, preferably verbs. An interface is an entity
whose behavior is specified by readable definitions and scenarios, not another Spec kind.

The Module model is recursive. A Module has at most one structural parent; composition is acyclic.
Using a provider does not acquire it as a child. A shared provider has one identity and MUST NOT
be owned by one of its consumers; dependencies may cross hierarchy levels. Module ownership,
execution composition and context references are independent relations. Missing or inapplicable facts MUST be stated honestly, not
invented from code, examples or template placeholders.

### P2. Implementation bindings are metadata, not reading or implicit code access

An entity MAY bind exact project-relative files or directory prefixes. A prefix binds every regular
file below it, including future files, under a tool's explicit deterministic exclusion rule. The
Module's implementation listing is the union of its entities' entries. It records realization,
not a promise omitted from reading content or permission to inspect the files.

Within a Module each entry belongs to one entity. When entries cover the same file, an exact entry
wins over a directory, and a longer directory prefix wins over a shorter one. Several Modules MAY
bind the same implementation; each retains its own identity and contract, and changes concern all
listing Modules. No document-unit member, generated output or project-control record may be bound
as implementation; a directory binding MUST NOT contain a document-unit member.

A pending marker names an intended entry that does not yet exist. A non-pending entry MUST exist.
Pending is intent, not evidence. File contents and external material remain separately authorized.

Tests are implementation files. A test names the scenario it verifies; reading content MUST NOT
list verifying tests or prescribe coverage declarations. A tool derives coverage from those test
annotations without executing them. Metadata may bind test files like other implementation files.
Missing coverage does not cancel a promise, and a declared test is not proof of fulfillment.

### P3. A Module resolves complete document units

Each Module MUST have a stable identity and a nonempty owned `documents` collection with exactly one
local `module.md` reading entry. Each registered **document unit** has one stable document identity,
one owner and two source members: reading Markdown and its associated metadata. Registering the
reading path registers the pair. Neither member is independently owned or included.

The Module separately declares `references`: another Module's whole owned collection, one document
unit by stable identity, or existing project-relative vendored external material pinned at a known
revision. References select knowledge, not ownership, composition, dependency, implementation or
permission. Only the selected Module's references expand, once. Referenced Modules' references,
Markdown links, neighbors and directory structure MUST NOT expand the context.

The complete Spec context is the deduplicated union of all owned and directly referenced units,
with **both source members available whole**. Reading content is a subset of this context, never a
replacement for it. External references and implementation contents remain outside Spec context.
A tool MUST provide all admitted sources and no sources outside its explicit grant, whatever file
delivery mechanism it chooses. A scenario query resolves its sole owner and then that owner's
complete context; it never trims to the scenario or selects the consumer that happened to read it.

The resolved reading subset MUST explain purpose, correct use, design and obligations without
undeclared reading or source code supplying missing meaning. For every child and direct dependency,
state responsibility, use conditions, canonical promises relied upon and local obligations/reactions.
Necessary provider definitions must be included through explicit references; use ordinary links,
not copies or transclusion as a substitute for inclusion. Attributed terminology restatements under
P1 aid reading but do not replace those complete defining units. Included entities keep their owner and do not join the consumer's local
entity inventory, diagram or implementation listing.

Record exact source-byte digests, member roles, document identity, owner and inclusion provenance,
and bind the selecting registration to the context identity. Changing metadata alone invalidates
dependent context and review evidence just as changing reading does. Identity links MUST continue
to reach canonical readable definitions after publication. Missing meaning remains an attributed
gap; a reader MUST NOT silently fetch more files to repair it.

### P4. Conformance covers content, reading, structure and consistency

A conformance claim identifies its Protocol version. Stable identities, unique unit ownership,
complete paired source inclusion, explicit document roles and definition placement, explicit
one-level references, consistent declarations, required reading structure, one statement per requirement and consistent file listings are structural
requirements. Complete and mutually consistent readable obligations, design and relationships,
including decidable requirements and an explanation usable without implementation knowledge, are
semantic requirements. Readability review checks the stated reader's questions, terminology,
normal-path order, concrete examples, causal design and visible safety limits. It is not a word-count
gate or a preference for shorter prose. A correctly named section or table cannot prove understanding.

Passing shape checks, headings, diagrams or coverage checks cannot establish semantic completeness
or implementation conformance. Reading must not hide necessary guarantees in metadata, while
metadata must not override prose or silently infer relationships absent from the registry.

The [Required format](format.md) defines representation, and templates provide starters, not proof.
A tool's configuration version, registry serialization, worker wire types, execution policy and
context delivery are separate agreements. Tools MUST preserve the content model and its reading
subset, identities, ownership, inclusion, relationships and obligations. The Protocol does not
prescribe docsite pages, sidebars, tabs, themes, folding or interaction behavior.
