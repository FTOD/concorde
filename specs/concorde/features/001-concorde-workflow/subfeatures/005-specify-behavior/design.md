---
id: feature.concorde.workflow.specify-behavior
kind: feature
module: module.concorde
parent_feature: feature.concorde.workflow
refines: []
subfeatures: []
scenarios:
  - scenario-concorde-establish-and-place-feature
contracts:
  provided:
    - contract.concorde.workflow
  required:
    - contract.concorde.spec-kit-platform
evidence_status: partial
canonical_design: specs/concorde/features/001-concorde-workflow/subfeatures/005-specify-behavior/design.md
---

# Feature Design: Specify Behavior

**Created**: 2026-08-26
**Revised**: 2026-08-28
**Status**: Specified and revised for the parent's three-tier feature document model; existing
realization has not been accepted into this sub-feature's `implementation.md`
**Input**: Route `speckit.specify`, `speckit.clarify`, and `speckit.checklist` through one selected
Concorde root, authoring `abstract.md` and `design.md` together and seeding or preserving the feature
`implementation.md`.

## Outcome

A maintainer can define focused, testable behavior with a faithful abstract, resolve material
uncertainty, and record requirements-quality review while preserving the boundary between durable
intent, accepted realization, and temporal review state.

## Parent Context and Boundary

The parent owns shared workflow invariants, the document model, and aggregate outcomes. This child
owns specification, clarification, and requirements-quality review for the selected root, and is the
only writer of a feature's abstract. For a child selection, parent durable sources are aggregate
read-only context and sibling bodies are excluded. The parent core diagram and selected workspace
model are sufficient; no child diagram is needed.

## User Scenarios & Testing

### User Story 1 - Produce a ready specification with a faithful abstract (Priority: P1)

A maintainer describes the selected outcome, resolves only consequential ambiguity, and checks that
the resulting specification is understandable, testable, bounded, and free of implementation design,
and that its abstract lets a programmer or agent grasp the feature in minutes without saying anything
the specification does not.

**Independent Test**: Run all three phases for new and existing top-level and child roots and verify
durable and checklist writes, design-reference preservation, abstract shape and budget, and bounded
context reads.

**Acceptance Scenarios**:
1. **Given** a selected root, **When** specification is authored, **Then** only its canonical
   `abstract.md` and `design.md` change and its existing `implementation.md` is preserved byte-for-byte.
2. **Given** a new canonical root, **When** specification runs, **Then** it authors a self-contained
   `abstract.md` in the parent's five-section shape within the reading budget, authors `design.md`, seeds
   a `implementation.md` whose only content is the explicit not-yet-accepted state, and creates no
   `implementation.md`.
3. **Given** material ambiguity, **When** clarification completes, **Then** accepted answers are
   encoded into that same specification without creating a competing copy, and the abstract is
   updated wherever it summarized the changed behavior.
4. **Given** requirements review, **When** a checklist is produced, **Then** it lives beneath the
   selected root's `attempt/checklists/` directory and includes the abstract's shape, budget,
   and faithfulness to `design.md`.
5. **Given** a abstract that states a rule, scope boundary, or criterion absent from `design.md`, whose
   `Logic` rules do not cite the requirement they summarize, or that cannot be understood without
   opening `design.md`, **When** the requirements-quality checklist is evaluated, **Then** the
   offending statement is named as a failing item.
6. **Given** the level at which the feature is specified, **When** specification needs architecture
   context, **Then** it reads that level's `module.md` and bounded view, and opens the level's
   `design.md` only when the maintainer asks for a recorded detail.

### Edge Cases

- A child repeats parent-owned vocabulary, invariants, dependencies, or aggregate requirements.
- A cross-component feature lacks either a core component diagram or a clear sufficiency rationale.
- A abstract restates the specification at length, exceeds its budget, omits a section, or defines
  behavior the specification does not.
- A phase attempts to write through parent or sibling context, to a feature `implementation.md`, or to a
  module `design.md`.
- The selected root carries a legacy filename or has no `abstract.md`.

## Requirements

- **FR-001**: All three phases MUST resolve the selected workspace before artifact access.
- **FR-002**: Specification and clarification MUST write only the selected canonical `abstract.md` and
  `design.md`.
- **FR-003**: Existing durable `implementation.md` content MUST remain byte-identical during these phases.
- **FR-004**: Requirements-quality checklists MUST live only in the selected temporal checklist
  directory.
- **FR-005**: A child specification MUST own one focused outcome and MUST NOT duplicate parent-owned
  aggregate facts.
- **FR-006**: Cross-component specifications MUST declare one text-backed core architecture diagram
  or record why prose and the bounded view suffice.
- **FR-007**: Clarification MUST prioritize consequential scope, security, and user-outcome choices,
  encode accepted answers durably in `design.md`, and update the abstract wherever it summarized the
  changed behavior.
- **FR-008**: For a new root, specification MUST author `abstract.md` and `design.md` and seed a
  `implementation.md` holding only the explicit not-yet-accepted state; substantive implementation
  content is written by acceptance.
- **FR-009**: These phases MUST use the level's `module.md` as bounded architecture context and MUST
  NOT treat the level's `design.md` as an implicit input or write to it.
- **FR-010**: The authored abstract MUST be self-contained (understood without opening any other
  document), MUST have exactly the parent's five sections in order, MUST link the feature's
  declared core diagram (or the parent's core view, the level view, or an inline sketch) from its
  structure section, MUST cite a `design.md` requirement ID for every rule stated in its `Logic`
  section, MUST stay within the abstract reading budget, and MUST NOT state a requirement, scope
  boundary, or success criterion absent from `design.md`.

## Success Criteria

- **SC-001**: Every phase-routing test writes only within the selected root's authorized paths.
- **SC-002**: Every completed quality checklist has all mandatory items resolved and no clarification
  markers remain.
- **SC-003**: Parent and child review samples contain no duplicated normative requirement.
- **SC-004**: All existing feature `implementation.md` files and all module `design.md` files remain
  byte-identical after specification and clarification.
- **SC-005**: Every newly seeded root contains `abstract.md`, `design.md`, and a placeholder `implementation.md`
  with no legacy filename.
- **SC-006**: Every abstract in the acceptance fixtures passes the parent's shape and budget checks and
  cites an existing requirement ID for each rule in its `Logic` section.

## Assumptions

- Spec Kit supplies the normal phase procedure and active templates; Concorde supplies path and
  architecture context, including resolved templates for the abstract and for the placeholder
  `implementation.md`.
