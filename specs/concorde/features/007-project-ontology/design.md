---
id: feature.concorde.define-project-ontology
kind: feature
module: module.concorde
canonical_design: specs/concorde/features/007-project-ontology/design.md
evidence_status: partial
subfeatures: []
contracts:
  provided:
    - contract.concorde.ontology
  required: []
diagrams:
  - source: specs/concorde/features/007-project-ontology/diagrams/concorde-ontology-model.json
    role: core
    kind: architecture
    output: generated/architecture/concorde-ontology-model.html
    scenarios:
      - US1
      - US2
      - US3
---

# Feature Design: Define Project Ontology

**Feature Branch**: `007-project-ontology`

**Created**: 2026-08-31

**Status**: Draft

**Input**: User description: "Define a consistent Concorde ontology at every architecture and feature level, inherit terminology from ancestor levels, and show concept relationships with Archify."

## Core Component Diagram and Supplemental Scenario Views

- **Core decision**: `diagrams/concorde-ontology-model.json` is the core Archify architecture source. It explains how specification roots, modules, features, sub-features, local terminology, concepts, relationships, and attempt workspaces fit together.
- **Supplemental decisions**: No dynamic view is needed; inheritance and concept relationships are stable structural facts.
- **Generated view**: `generated/architecture/concorde-ontology-model.html`

The diagram supplements the definitions and requirements below. This text remains authoritative when a visual and a definition differ.

## Terminology

| Term | Meaning | Relationships |
|---|---|---|
| `Terminology table` | The local ontology declaration in a level's `design.md`; it defines concepts introduced at that level and does not repeat unchanged ancestor definitions. | `defines` → `Concept`; `inherits from` → `Terminology table` |
| `Concept` | A project entity or idea with one meaning and a qualified identity anchored at the level that defines it. | `named by` → `Preferred term`; `participates in` → `Relationship` |
| `Preferred term` | The canonical word or expression that names one concept at its defining level. | `names` → `Concept` |
| `Relationship` | A typed, directed semantic connection from one concept to another concept. | `connects` → `Concept` |
| `Terminology inheritance` | The rule that makes ancestor concepts available to a descendant without copying their table rows. | `exposes` → `Concept`; `traverses` → `Inheritance chain` |
| `Inheritance chain` | The ordered ancestor levels whose terminology is available to the current level. | `contains` → `Terminology table` |
| `Qualified concept identity` | The defining level's stable ID combined with the normalized preferred term, used to distinguish branch-local concepts that share a surface word. | `identifies` → `Concept`; `belongs to` → `Level` |
| `Level` | A specification root module, architecture/module, feature, or immediate sub-feature at which a design is maintained. | `owns` → `Terminology table`; `participates in` → `Inheritance chain` |
| `Ontology view` | A maintained Archify architecture source and generated delivery that visualize important concepts and typed relationships while remaining subordinate to textual definitions. | `visualizes` → `Concept`; `visualizes` → `Relationship` |

## User Scenarios & Testing

### User Story 1 - Define a Level's Vocabulary (Priority: P1)

As a maintainer, I can open any architecture or feature `design.md` and find the important terms introduced at that level, their precise meanings, and their relationships to other concepts, so I can understand the design without guessing what its language means.

**Why this priority**: A visible, bounded terminology table is the minimum useful ontology and immediately improves every design review.

**Independent Test**: Select any maintained module, feature, or sub-feature design, locate its terminology table, and verify that every important locally introduced concept has one unambiguous definition and relationship description.

**Acceptance Scenarios**:

1. **Given** a level introduces a concept not defined by an ancestor, **When** its design is reviewed, **Then** the concept appears once in the level's terminology table with a meaning and relationships.
2. **Given** a design uses several expressions for one concept, **When** the terminology table is read, **Then** one preferred term is identified and any accepted alias is explicit.
3. **Given** a level introduces no new concepts, **When** its design is reviewed, **Then** the required terminology section explicitly states that it relies only on inherited terminology rather than silently omitting the section.

---

### User Story 2 - Reuse Ancestor Terminology Consistently (Priority: P2)

As a maintainer working at a lower level, I can use terminology defined by ancestor architecture and feature levels without restating it, while automated checks prevent incompatible redefinitions and broken relationship references.

**Why this priority**: Inheritance keeps documents concise, and consistency checks prevent the same word from acquiring incompatible meanings across the project.

**Independent Test**: Define a term at an ancestor, use it unchanged in a descendant, and verify that the descendant passes without copying the row; then add a conflicting descendant definition and verify that validation reports both definitions and the inheritance path.

**Acceptance Scenarios**:

1. **Given** a term is defined by an ancestor level, **When** a descendant uses the term with the inherited meaning, **Then** no duplicate local row is required.
2. **Given** a descendant defines an inherited preferred term with an incompatible meaning, **When** the project is validated, **Then** validation fails and identifies the conflicting levels.
3. **Given** a relationship names another concept, **When** the project is validated, **Then** the named concept resolves locally or through the permitted ancestor chain.
4. **Given** two separate branches use the same word for different concepts, **When** neither definition is inherited by the other, **Then** validation permits the branch-local meanings and the project-wide ontology exposes their distinct qualified identities.

---

### User Story 3 - Explore Concept Relationships (Priority: P3)

As a maintainer or coding agent, I can inspect a maintained Archify view of Concorde's ontology and follow the textual source for each relationship, so I understand not only what entities mean but how they contain, provide, refine, inherit from, and own one another.

**Why this priority**: Definitions establish vocabulary, while relationships make the vocabulary a usable ontology and reveal inconsistent mental models.

**Independent Test**: Open the delivered ontology view, trace each displayed relationship to the terminology and design text, and verify that every important textual relationship is represented without making the diagram a second behavioral authority.

**Acceptance Scenarios**:

1. **Given** the project ontology defines related entities, **When** the ontology view is opened, **Then** the entities and typed relationships are visible and searchable.
2. **Given** a relationship changes in maintained text, **When** project validation runs, **Then** a stale generated ontology view is rejected until it is regenerated from the maintained source.
3. **Given** a lower level introduces a materially new concept relationship, **When** the level is documented, **Then** it declares a level-owned Archify view or explicitly links to an ancestor view that already explains the relationship.

### Edge Cases

- A term differs only by capitalization, punctuation, pluralization, or surrounding code formatting.
- A preferred expression contains multiple words or a domain abbreviation.
- A relationship references a term defined later in the same table.
- An inherited term is intentionally specialized; the specialization must receive its own qualified preferred term and state its relationship to the broader term.
- A feature inherits from both its providing module hierarchy and an immediate parent feature.
- A moved or renamed level changes the qualification path but not the concept's intended meaning.
- A table is structurally valid but omits a concept that is central to the level's responsibilities or outcomes.
- An Archify source is valid but contradicts its textual terminology or relationship descriptions.

## Requirements

### Functional Requirements

- **FR-001**: Every maintained architecture/module, feature, and sub-feature `design.md` MUST contain a `## Terminology` section.
- **FR-002**: The terminology section MUST contain a table with the columns `Term`, `Meaning`, and `Relationships`, or an explicit statement that the level introduces no local terminology and inherits all terms from its ancestors.
- **FR-003**: Each table MUST include every important concept or expression introduced by the current level and MUST exclude unchanged inherited terms.
- **FR-004**: Each row MUST identify one preferred term or expression and give a non-circular meaning that is sufficient for a reader familiar with ancestor levels.
- **FR-005**: Each row MUST state the concept's important typed relationships using preferred terms that resolve in the current level or its permitted ancestor chain; `None` is allowed only when no relationship is material.
- **FR-006**: Accepted aliases MUST be declared in the preferred term's row and MUST NOT create a second concept identity.
- **FR-007**: A module level MUST inherit terminology from its ancestor modules and the specification root; a top-level feature MUST additionally inherit from its providing module hierarchy; a sub-feature MUST additionally inherit from its immediate parent feature.
- **FR-008**: A descendant MUST be able to use an inherited term directly without copying its terminology row.
- **FR-009**: A descendant MUST NOT redefine an inherited preferred term incompatibly. A narrower concept MUST use a distinct qualified term and declare its specialization relationship.
- **FR-010**: Separate branches MAY define different branch-local meanings for the same surface word when neither definition is inherited by the other; project-wide presentations MUST qualify those concept identities by defining level.
- **FR-011**: Project validation MUST report missing or malformed terminology sections, duplicate local preferred terms, incompatible inherited redefinitions, invalid aliases, and relationship references that do not resolve through the permitted inheritance chain.
- **FR-012**: Workflow guidance and templates that create or revise a `design.md` MUST require maintainers and coding agents to update the current level's terminology and relationships as part of the same change.
- **FR-013**: The project MUST maintain a text-backed Archify architecture view that shows the core Concorde ontology entities and their typed relationships.
- **FR-014**: A level that introduces a materially new relationship not already explained by an applicable ancestor view MUST declare a level-owned Archify view; otherwise it MUST identify the applicable inherited view.
- **FR-015**: Maintained ontology diagram sources MUST use hidden generic legends, pass showcase validation, remain aligned with the textual ontology, and be regenerated before a stale delivery can be accepted.
- **FR-016**: Generated project documentation MUST render each level's terminology table and declared ontology view without becoming an alternative source of ontology truth.
- **FR-017**: Concorde's existing maintained architecture and feature designs MUST be migrated to the terminology-section contract before this feature is considered complete.
- **FR-018**: The project-wide ontology MUST define Concorde's own core concepts, including specification root, module, feature, sub-feature, design, implementation, attempt, durable artifact, temporal artifact, generated projection, contract, diagram, concept, relationship, and terminology inheritance.

### Key Entities

- **Level**: One node in the maintained specification hierarchy: the specification root, an architecture/module level, a feature, or an immediate sub-feature.
- **Term**: The preferred word or expression used to name one concept within a defining level.
- **Concept**: A project entity or idea with one meaning and a qualified identity anchored at its defining level.
- **Meaning**: The non-circular explanation that distinguishes a concept from related concepts.
- **Alias**: An explicitly accepted alternate expression for an existing concept; it does not create another concept.
- **Relationship**: A typed, directed semantic connection between two concepts, expressed with a predicate such as `contains`, `provides`, `refines`, `inherits`, or `owns`.
- **Terminology Table**: The local ontology declaration in a level's `design.md`; it introduces new concepts and does not copy unchanged ancestor declarations.
- **Inheritance Chain**: The ordered set of levels whose terminology is available to the current level.
- **Ontology View**: A maintained Archify architecture source and generated delivery that visualize concepts and relationships while remaining subordinate to textual definitions.

## Success Criteria

### Measurable Outcomes

- **SC-001**: 100% of maintained module, feature, and sub-feature `design.md` files satisfy the terminology-section contract in project validation.
- **SC-002**: 100% of relationship references in terminology tables resolve to a local or inherited concept, with zero incompatible inherited redefinitions.
- **SC-003**: A maintainer can identify the defining level, meaning, and important relationships for any term used by a sampled design in under 3 minutes without reading descendant or sibling designs.
- **SC-004**: The core Concorde ontology view passes all showcase composition checks with zero errors and zero warnings, and its desktop visual evidence is reviewed truthfully.
- **SC-005**: Every workflow entry point that authors or revises a design includes an ontology update check, demonstrated by automated guidance tests.
- **SC-006**: All pre-existing Concorde design levels are migrated and the complete validation suite passes without ontology warnings.

## Assumptions

- Readers at a level already understand the maintained designs and terminology of its ancestors, as stated by the user.
- Ontology authority remains in maintained Markdown; Archify sources explain relationships and generated HTML is disposable.
- "Important" means a concept necessary to understand the level's responsibilities, boundaries, outcomes, invariants, contracts, states, or artifact roles; incidental implementation identifiers do not require rows.
- The local-only table model is preferred over repeating inherited rows because duplication would create drift.
- Qualified concept identity consists of the defining level's stable ID plus the normalized preferred term, allowing unrelated branches to reuse surface words safely.
- Existing Concorde stable IDs and hierarchy remain authoritative; this feature clarifies their ontology rather than renaming the architecture.

## Concorde Architecture Alignment

- **Stable feature ID**: `feature.concorde.define-project-ontology`
- **Providing module**: `module.concorde`
- **Decomposition decision**: Keep the feature atomic because terminology tables, inheritance checks, relationship views, and project migration form one consistency contract.
- **Authority split**: This design defines observable ontology behavior. `implementation.md` will record an accepted realization only after explicit implementation delivery.
- **Observable textual outcome**: Every level exposes a local terminology table, inherits ancestor concepts consistently, and makes important concept relationships inspectable.
- **Parent refinement**: This is a project-level feature because it applies across every Concorde module and feature hierarchy.
- **Core feature diagram**: `diagrams/concorde-ontology-model.json` (`role: core`, Archify `architecture`).
- **Supplemental diagrams**: None.
- **Legend policy**: The maintained source sets `meta.legend.mode` to `hidden`.
- **Contracts**: Provides `contract.concorde.ontology`; no additional external boundary contract is required.
- **Level views**: The feature supplements, and does not redefine, the providing module's maintained level view.
- **Evidence status**: `partial` until the workflow, validation, migration, and generated view are implemented and verified.
