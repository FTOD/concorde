---
id: feature.concorde.explore-alignment
kind: feature
module: module.concorde
refines: []
subfeatures: []
scenarios: []
contracts:
  provided:
    - contract.concorde.alignment-explorer
  required:
    - contract.understand-anything.knowledge-graph
diagrams:
  - source: specs/concorde/features/006-alignment-explorer/diagrams/alignment-explorer-components.json
    role: core
    kind: architecture
    scenarios:
      - scenario.alignment-explorer.explore-architecture
      - scenario.alignment-explorer.inspect-alignment
      - scenario.alignment-explorer.expose-unknowns
    output: generated/architecture/alignment-explorer-components.html
evidence_status: unknown
canonical_design: specs/concorde/features/006-alignment-explorer/design.md
---

# Feature Design: Alignment Explorer

**Read first**: [abstract.md](abstract.md) — the self-contained overview. **Shared project ontology**:
[docs/ontology.md](../../../../docs/ontology.md) — the project-wide authority for Concorde and UA
terminology and their relationship. **Accepted realization**: [implementation.md](implementation.md)
— currently a placeholder.

**Created**: 2026-08-31

**Status**: Draft

**Input**: Use [Understand Anything](https://github.com/Egonex-AI/Understand-Anything) as a second
viewing channel for developers: an interactive architecture browser and Concorde
specification–implementation consistency visualization engine. Its command must be
`/concorde-explore` or `speckit-concorde-explore`, not bare `/explore`. Maintain a complete-enough
definition of Concorde terminology, UA terminology, and their relationship in the shared
`docs/ontology.md`; adapter representation mappings are only the rendering profile within that
broader ontology. Changes to existing specifications, documentation, and code are allowed.

## Outcome

A developer can invoke the canonical `speckit.concorde.explore` intent through the platform's
`/concorde-explore` or `$speckit-concorde-explore` presentation, move from Concorde's module and
feature hierarchy into the implementation graph, and inspect whether required intent, accepted
realization, executable reality, and evidence agree. The experience preserves Concorde's source
authority and vocabulary while using Understand Anything as a read-only interactive projection, and
it distinguishes verified agreement, partial evidence, unknown state, and actual disagreement
without guessing.

## Core Component Diagram and Supplemental Scenario Views

- **Core decision**: [alignment-explorer-components.json](diagrams/alignment-explorer-components.json)
  shows the stable participants: maintained Concorde sources, the shared project ontology, code and
  tests, the deterministic validator, the Understand Anything graph input, the disposable alignment
  projection, the `speckit.concorde.explore` command surface, and the developer. Maintained sources
  own intent, code and tests own executable reality, and the projection owns neither.
- **Supplemental decisions**: None. Architecture browsing and alignment inspection are focus views in
  the core component map; their required behavior is fully stated below and does not require a dynamic
  diagram.
- **Generated view**: `generated/architecture/alignment-explorer-components.html`

## User Scenarios & Testing

### User Story 1 - Explore the architecture (Priority: P1)

As a developer, I invoke `/concorde-explore` or `$speckit-concorde-explore` and browse the project
from its Concorde root through modules, features, contracts, scenarios, and linked implementation
elements so that I can orient myself without reading the entire repository.

**Why this priority**: A useful second viewing channel must first make the existing architecture
quickly navigable while preserving its meaning and provenance.

**Independent Test**: Build the projection for a valid project, invoke the supported explore command,
locate a named feature from the root, follow it to one implementation element, and return to the exact
maintained source from which the feature description came.

**Acceptance Scenarios**:

1. **Given** a validated Concorde hierarchy and a current implementation graph, **when** a developer
   invokes `/concorde-explore` or `$speckit-concorde-explore`, **then** the root view exposes modules,
   features, contracts, scenarios, and their relationships using Concorde labels and stable
   identities.
2. **Given** a selected feature node, **when** the developer follows an implementation relationship,
   **then** the explorer shows the corresponding code or test element and preserves links to the
   canonical specification and implementation sources.
3. **Given** a developer searches by a stable ID, source path, or human-readable name, **when** one or
   more matching entities exist, **then** every result identifies its Concorde kind, adapter
   representation type, source provenance, and current evidence state.

---

### User Story 2 - Inspect specification–implementation alignment (Priority: P2)

As a reviewer, I switch to the alignment view and inspect whether a feature's required behavior,
accepted realization, implementation elements, and executable evidence are connected and current so
that I can focus review on gaps and conflicts.

**Why this priority**: Alignment is the differentiated value of the integration, but it is trustworthy
only after the architectural entities and their provenance can be navigated.

**Independent Test**: Use a fixture containing one verified relationship, one partial relationship,
one unknown relationship, and one contradiction; confirm that the explore command displays four
distinct states, their basis, and their provenance without presenting any non-verified state as
agreement.

**Acceptance Scenarios**:

1. **Given** a feature with specification, accepted realization, implementation links, and passing
   deterministic evidence, **when** the reviewer selects it, **then** the explorer may show `verified`
   and identifies the evidence and source revisions that justify that state.
2. **Given** a feature with implementation links but missing or incomplete evidence, **when** it is
   inspected, **then** the explorer shows `partial` or `unknown`, names the missing coverage, and does
   not imply correctness.
3. **Given** a deterministic finding that the maintained sources and executable reality conflict,
   **when** the affected entity is inspected, **then** the explorer shows `disagrees`, the exact
   finding, and links to both sides of the conflict.
4. **Given** source revisions newer than the projection inputs, **when** the explore command is invoked,
   **then** it marks the projection stale and does not reuse an earlier `verified` presentation as
   current fact.

---

### User Story 3 - Audit the ontology relationship model (Priority: P3)

As a Concorde maintainer, I inspect how Concorde entities and relationships are represented through
the Understand Anything adapter so that upstream schema changes or ambiguous terms cannot silently
alter the meaning of the architecture.

**Why this priority**: The integration must remain evolvable after the initial browsing and alignment
flows work.

**Independent Test**: Enumerate the pinned upstream node and edge registries, compare them with
`docs/ontology.md`, and introduce an undefined Concorde term, relationship, or changed upstream type;
confirm that the projection reports the drift and refuses to assign a misleading meaning.

**Acceptance Scenarios**:

1. **Given** the pinned upstream registry of 27 node types, **when** the ontology is checked, **then**
   every type appears exactly once in its upstream category and its permitted Concorde treatment is
   explicit.
2. **Given** a Concorde feature whose adapter representation type is Understand Anything `concept`,
   **when** it is viewed, **then** the interface labels it as a Concorde Feature and exposes `concept`
   only as adapter representation metadata.
3. **Given** a new, removed, or semantically changed upstream type, **when** a projection is requested,
   **then** the mismatch is reported as ontology drift and no automatic synonym is invented.

### Edge Cases

- A Concorde stable entity exists but has no implementation path or graph node.
- An implementation node matches multiple Concorde entities by name but none by stable identity or
  explicit source mapping.
- A source path is renamed while the stable Concorde ID remains unchanged.
- An `implementation.md` placeholder exists, so no accepted realization is available.
- An active `attempt/` proposes work that is not durable intent and must not be presented as accepted.
- The Understand Anything graph is absent, invalid, generated from a different commit, or contains
  dropped/auto-corrected nodes.
- A node uses an overloaded term such as `module`, `concept`, `source`, `page`, or `instance_of` whose
  upstream meaning differs by graph kind.
- A generated projection is present but its Concorde source digest, implementation revision, ontology
  version, or upstream schema pin is stale.
- A valid project has no tests for an implementation element; absence of evidence remains visible and
  does not become disagreement by itself.
- A user follows a graph node to a source artifact that is excluded, moved, or no longer readable.
- An agent integration materializes bare `/explore`, two conflicting explore commands, or a command
  whose behavior differs from the canonical `speckit.concorde.explore` intent.

## Requirements

### Functional Requirements

- **FR-001**: Concorde MUST expose the canonical intent `speckit.concorde.explore` as a read-only
  second viewing channel alongside its canonical Markdown and documentation views. Skill-style
  integrations MUST present it as `$speckit-concorde-explore`; slash-command integrations MAY present
  it as `/concorde-explore`. Concorde MUST NOT expose bare `/explore` as the public command or a
  compatibility alias, replace canonical sources, or make generated graph state authoritative.
- **FR-002**: Invoking `/concorde-explore` or `$speckit-concorde-explore` MUST support navigation from
  the project-level module through modules, features, immediate sub-features, contracts, scenarios,
  and their linked implementation elements.
- **FR-003**: Developers MUST be able to search and filter by Concorde kind, stable ID, source path,
  human-readable name, architectural level, adapter representation type, and evidence state.
- **FR-004**: Every projected Concorde entity MUST preserve its stable ID when one exists, canonical
  source path, specifying module or feature context, authority class, lifecycle class, and ontology
  version.
- **FR-005**: Every displayed specification–implementation relationship MUST link to the contributing
  specification, accepted realization when one exists, implementation element, evidence, and source
  revisions, or explicitly identify which contribution is absent.
- **FR-006**: Alignment state MUST use Concorde's existing evidence vocabulary: `unknown`, `partial`,
  `verified`, and `disagrees`; `verified` MUST require positive deterministic evidence, and no other
  state may be presented as agreement.
- **FR-007**: The project MUST maintain [docs/ontology.md](../../../../docs/ontology.md) as its shared
  terminology and relationship authority. It MUST separately define Concorde classes, artifacts,
  relations, authority/lifecycle rules and invariants; the pinned UA graph classes, 27 node types, 38
  edge types, metadata, graph kinds and aliases; and the identity, representation, correlation,
  realization, evidence, disagreement, provenance, and rendering relationships between them.
- **FR-008**: The project ontology MUST account for all 27 node types and 38 edge types defined by the
  pinned Understand Anything registry, preserve their upstream categories and graph-kind-sensitive
  semantics, and treat the adapter representation profile as rendering behavior rather than semantic
  equivalence with Concorde kinds.
- **FR-009**: The projection MUST retain the Concorde kind independently of the chosen Understand
  Anything node type and MUST label the entity by its Concorde kind in the explore command's output.
- **FR-010**: Ambiguous name-only matches MAY be shown as candidates but MUST remain `unknown` until an
  explicit identity, path, contract, accepted-realization, or evidence link resolves the correlation.
- **FR-011**: Concorde validation findings and executable test evidence used for alignment MUST be
  derived deterministically; semantic summaries or model-generated suggestions MUST NOT establish a
  `verified` or `disagrees` state by themselves.
- **FR-012**: Every projection MUST record the Concorde source digest, implementation revision,
  ontology source and version, upstream repository and revision, graph version, and analysis time used
  to build it.
- **FR-013**: The explore command MUST visibly report stale, missing, invalid, or incompatible inputs
  and MUST prevent stale `verified` states from appearing current.
- **FR-014**: If the implementation graph is unavailable, the explore command MUST still expose the
  Concorde hierarchy when possible, mark implementation coverage `absent`, and report alignment as
  `unknown` rather than failing silently.
- **FR-015**: A user MUST be able to inspect why any state was assigned, including coverage, relevant
  findings, evidence references, mapping basis, and links back to source artifacts.
- **FR-016**: Unknown upstream node or edge types, category changes, alias changes that affect meaning,
  and unsupported graph kinds MUST produce explicit ontology-drift diagnostics rather than silent
  coercion or deletion.
- **FR-017**: Generated graph, alignment, search, and user-interface artifacts MUST be reproducible
  disposable read models and MUST never write back into maintained Concorde sources, code, tests, or
  accepted realization.
- **FR-018**: The maintained ontology, contract schemas and examples, feature requirements, user-facing
  labels, and deterministic tests MUST evolve together whenever the mapping or bundle representation
  changes.
- **FR-019**: Concorde source discovery, digesting, validation, bounded context, link checking, and
  publication MUST treat `docs/ontology.md` as the shared maintained project ontology and MUST report
  its absence, invalid structure, stale version, broken references, or inconsistent use by features,
  contracts, schemas, examples, tests, and projections.

### Key Entities

- **Concorde Entity**: A module, feature, sub-feature, contract, scenario, requirement, or source
  artifact with its canonical meaning, identity, authority, lifecycle, and hierarchy context.
- **Implementation Entity**: A code, configuration, document, service, data, or test element represented
  by the implementation knowledge graph and anchored to a source revision.
- **Adapter Representation Node**: An Understand Anything node whose `type` is one of the pinned 27
  values. Its type lets the adapter validate, filter, lay out, and render the node; it does not
  establish a Concorde kind.
- **Ontology Relationship Model**: The versioned definitions of the Concorde and pinned UA
  vocabularies plus explicit identity, representation, correlation, realization, evidence,
  disagreement, provenance, and drift relationships between them.
- **Adapter Representation Profile**: The subordinate rendering rules that choose UA node/edge types
  for Concorde subjects while keeping canonical Concorde kinds and relations separately.
- **Alignment Record**: A correlation among a Concorde subject, specification sources, accepted
  realization, implementation nodes, evidence nodes, findings, coverage, revisions, and one evidence
  state.
- **Projection Provenance**: The source digest, implementation commit, upstream/schema pin, graph
  version, ontology version, and analysis time that make freshness and reproduction testable.
- **Ontology Drift Finding**: An explicit incompatibility between the pinned mapping and an upstream
  or Concorde vocabulary/schema change.
- **Explore Command**: The stable `speckit.concorde.explore` intent and its equivalent
  `/concorde-explore` or `$speckit-concorde-explore` platform presentation; it is an agent command
  surface, not the identity of a browser route.

## Success Criteria

### Measurable Outcomes

- **SC-001**: For a valid project, 100% of registered modules, features, contracts, and referenced
  scenarios are present in the explore command's output or appear in an explicit exclusion/error
  inventory.
- **SC-002**: In usability checks, at least 90% of developers can move from the project root to a named
  feature, one linked implementation element, and the canonical source in under two minutes without
  repository-wide text search.
- **SC-003**: 100% of displayed alignment records expose their evidence state, coverage, mapping basis,
  source provenance, and freshness inputs.
- **SC-004**: Automated fixtures demonstrate zero cases in which `unknown`, `partial`, stale, missing,
  or model-suggested correlations are presented as `verified`.
- **SC-005**: Rebuilding from identical canonicalized inputs produces byte-identical semantic graph and
  alignment content after excluding explicitly non-semantic generation-time fields.
- **SC-006**: For graphs containing up to 10,000 nodes, at least 95% of search, filter, select, and
  adjacent-node navigation actions present their result within one second in the supported developer
  environment.
- **SC-007**: A registry check accounts for all 27 pinned upstream node types and fails on every
  unmapped addition, removal, or category change.
- **SC-008**: In reviewer exercises containing known mismatches, at least 90% of participants can locate
  the disagreeing source pair and its supporting finding within three minutes.
- **SC-009**: Changing only `docs/ontology.md` changes the maintained-source digest, triggers ontology,
  contract, schema/example, reference, and projection consistency checks, and appears in every
  declared developer-facing projection that links the ontology.
- **SC-010**: Every supported agent integration exposes exactly one presentation of
  `speckit.concorde.explore`, uses `/concorde-explore` or `$speckit-concorde-explore` as appropriate,
  and contains zero callable bare `/explore` aliases.

## Assumptions

- The first release consumes Understand Anything's `codebase` graph as the implementation view. Its
  `knowledge` and `design` graph kinds remain valid upstream inputs but do not establish Concorde
  architecture or alignment unless a later reviewed ontology version adds an explicit mapping.
- The upstream compatibility baseline is commit
  [`ba450c43425f3de6d43daf76526950ad8ca93536`](https://github.com/Egonex-AI/Understand-Anything/tree/ba450c43425f3de6d43daf76526950ad8ca93536),
  whose core registry defines 27 node types and 38 edge types. The implementation plan may advance the
  pin only with an ontology and compatibility review.
- Existing Concorde source authority remains unchanged: maintained Markdown and contracts own intent,
  code owns executable behavior, tests own executable evidence, and generated projections own none of
  those facts.
- Access to `speckit.concorde.explore` follows the host project's existing access boundary; this
  feature introduces no separate user, role, or authorization model.
- `speckit.concorde.explore` is the stable command intent. `/concorde-explore` and
  `$speckit-concorde-explore` are platform presentations of that intent; bare `/explore` is not a
  supported alias.
- An active `attempt/` may be shown as proposed context only when clearly separated from durable intent;
  it never counts as accepted realization or positive alignment evidence.
- The feature stays atomic because architecture browsing and alignment inspection share one ontology,
  projection, route, and freshness model; splitting them would duplicate the core trust boundary.

## Concorde Architecture Alignment

- **Stable feature ID**: `feature.concorde.explore-alignment`
- **Specifying module**: `module.concorde`, because the outcome combines maintained workspace sources,
  deterministic validation, executable reality, and a read-only viewing projection across multiple
  immediate modules.
- **Decomposition decision**: Atomic; no sub-features are introduced.
- **Observable textual outcome**: `speckit.concorde.explore`, presented as `/concorde-explore` or
  `$speckit-concorde-explore`, provides architecture navigation and evidence-qualified
  specification–implementation alignment without becoming a source of truth.
- **Parent refinement**: None; this is a project-level feature.
- **Representative scenarios**: The three user journeys are prose-only at the root level; the
  feature-owned core diagram supplies matching focus views without redefining the root module's
  maintained level-view scenarios.
- **Core feature diagram**: The declared component view shows all stable participants and its text
  counterpart is the Outcome, requirements, and scenarios above.
- **Contracts**: The feature provides `contract.concorde.alignment-explorer` and requires
  `contract.understand-anything.knowledge-graph`.
- **Shared requested authority**: `docs/ontology.md` owns project-wide terminology and relationship
  semantics incorporated by FR-007 and FR-018; this `design.md` remains the feature's behavioral
  authority and contract schemas remain serialization authorities.
- **Bootstrap gap**: Profile 4 does not yet treat `docs/ontology.md` as a maintained architectural
  input to source digest, validation, or bounded context. FR-019 must be implemented and verified
  before this feature can be accepted; publication as an ordinary project guide alone does not close
  that gap.
- **Evidence status**: `unknown`; no implementation realization or behavioral evidence has been
  accepted for this feature.

## Terminology

| Term | Meaning | Relationships |
|---|---|---|
| `Concorde entity` | A module, feature, contract, scenario, requirement, or source artifact with canonical project meaning and identity. | `correlates with` → `Implementation entity`; `participates in` → `Ontology relationship model` |
| `Implementation entity` | A code, configuration, document, service, data, design, or test element anchored to an implementation revision. | `correlates with` → `Concorde entity`; `participates in` → `Alignment record` |
| `Ontology relationship model` | The versioned Concorde and pinned-UA vocabularies plus explicit identity, representation, correlation, realization, evidence, provenance, and drift relationships. | `governs` → `Alignment record`; `governs` → `Adapter representation profile` |
| `Adapter representation profile` | The subordinate rules choosing UA node and edge types for Concorde subjects without replacing canonical project kinds and relations. | `represents` → `Concorde entity`; `governed by` → `Ontology relationship model` |
| `Alignment record` | The evidence-qualified correlation among a Concorde subject, specification, accepted realization, implementation nodes, findings, coverage, and revisions. | `correlates` → `Concorde entity`; `correlates` → `Implementation entity`; `carries` → `Projection provenance` |
| `Projection provenance` | The source digest, implementation revision, upstream/schema pin, ontology version, and analysis time needed for freshness and reproduction. | `qualifies` → `Alignment record`; `detects` → `Ontology drift finding` |
| `Ontology drift finding` | A deterministic incompatibility between a pinned mapping and an upstream or Concorde vocabulary/schema change. | `is a` → `Finding`; `concerns` → `Ontology relationship model` |
