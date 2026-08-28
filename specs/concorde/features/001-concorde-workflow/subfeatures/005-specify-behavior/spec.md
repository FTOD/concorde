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
architecture_view: specs/concorde/architecture.json
evidence_status: partial
canonical_spec: specs/concorde/features/001-concorde-workflow/subfeatures/005-specify-behavior/spec.md
---

# Feature Specification: Specify Behavior

**Created**: 2026-08-26
**Revised**: 2026-08-28
**Status**: Specified and revised for the parent's three-tier feature document model; existing
realization has not been hardened into this sub-feature's `design.md`
**Input**: Route `speckit.specify`, `speckit.clarify`, and `speckit.checklist` through one selected
Concorde root, authoring `tldr.md` and `spec.md` together and seeding or preserving the feature
`design.md`.

## Outcome

A maintainer can define focused, testable behavior with a faithful TL;DR, resolve material
uncertainty, and record requirements-quality review while preserving the boundary between durable
intent, accepted realization, and temporal review state.

## Parent Context and Boundary

The parent owns shared workflow invariants, the document model, and aggregate outcomes. This child
owns specification, clarification, and requirements-quality review for the selected root, and is the
only writer of a feature's TL;DR. For a child selection, parent durable sources are aggregate
read-only context and sibling bodies are excluded. The parent core diagram and selected workspace
model are sufficient; no child diagram is needed.

## User Scenarios & Testing

### User Story 1 - Produce a ready specification with a faithful TL;DR (Priority: P1)

A maintainer describes the selected outcome, resolves only consequential ambiguity, and checks that
the resulting specification is understandable, testable, bounded, and free of implementation design,
and that its TL;DR lets a programmer or agent grasp the feature in minutes without saying anything
the specification does not.

**Independent Test**: Run all three phases for new and existing top-level and child roots and verify
durable and checklist writes, design-reference preservation, TL;DR shape and budget, and bounded
context reads.

**Acceptance Scenarios**:
1. **Given** a selected root, **When** specification is authored, **Then** only its canonical
   `tldr.md` and `spec.md` change and its existing `design.md` is preserved byte-for-byte.
2. **Given** a new canonical root, **When** specification runs, **Then** it authors a self-contained
   `tldr.md` in the parent's five-section shape within the reading budget, authors `spec.md`, seeds
   a `design.md` whose only content is the explicit not-yet-hardened state, and creates no
   `implementation.md`.
3. **Given** material ambiguity, **When** clarification completes, **Then** accepted answers are
   encoded into that same specification without creating a competing copy, and the TL;DR is
   updated wherever it summarized the changed behavior.
4. **Given** requirements review, **When** a checklist is produced, **Then** it lives beneath the
   selected root's `implementation/checklists/` directory and includes the TL;DR's shape, budget,
   and faithfulness to `spec.md`.
5. **Given** a TL;DR that states a rule, scope boundary, or criterion absent from `spec.md`, whose
   `Logic` rules do not cite the requirement they summarize, or that cannot be understood without
   opening `spec.md`, **When** the requirements-quality checklist is evaluated, **Then** the
   offending statement is named as a failing item.
6. **Given** the level at which the feature is specified, **When** specification needs architecture
   context, **Then** it reads that level's `module.md` and bounded view, and opens the level's
   `design.md` only when the maintainer asks for a recorded detail.

### Edge Cases

- A child repeats parent-owned vocabulary, invariants, dependencies, or aggregate requirements.
- A cross-component feature lacks either a core component diagram or a clear sufficiency rationale.
- A TL;DR restates the specification at length, exceeds its budget, omits a section, or defines
  behavior the specification does not.
- A phase attempts to write through parent or sibling context, to a feature `design.md`, or to a
  module `design.md`.
- The selected root still carries a legacy `implementation.md` or has no `tldr.md`.

## Requirements

- **FR-001**: All three phases MUST resolve the selected workspace before artifact access.
- **FR-002**: Specification and clarification MUST write only the selected canonical `tldr.md` and
  `spec.md`.
- **FR-003**: Existing durable `design.md` content MUST remain byte-identical during these phases.
- **FR-004**: Requirements-quality checklists MUST live only in the selected temporal checklist
  directory.
- **FR-005**: A child specification MUST own one focused outcome and MUST NOT duplicate parent-owned
  aggregate facts.
- **FR-006**: Cross-component specifications MUST declare one text-backed core architecture diagram
  or record why prose and the bounded view suffice.
- **FR-007**: Clarification MUST prioritize consequential scope, security, and user-outcome choices,
  encode accepted answers durably in `spec.md`, and update the TL;DR wherever it summarized the
  changed behavior.
- **FR-008**: For a new root, specification MUST author `tldr.md` and `spec.md` and seed a
  `design.md` holding only the explicit not-yet-hardened state, and MUST NOT create an
  `implementation.md`; the design reference's substantive content is written by hardening.
- **FR-009**: These phases MUST use the level's `module.md` as bounded architecture context and MUST
  NOT treat the level's `design.md` as an implicit input or write to it.
- **FR-010**: The authored TL;DR MUST be self-contained (understood without opening any other
  document), MUST have exactly the parent's five sections in order, MUST link the feature's
  declared core diagram (or the parent's core view, the level view, or an inline sketch) from its
  structure section, MUST cite a `spec.md` requirement ID for every rule stated in its `Logic`
  section, MUST stay within the TL;DR reading budget, and MUST NOT state a requirement, scope
  boundary, or success criterion absent from `spec.md`.

## Success Criteria

- **SC-001**: Every phase-routing test writes only within the selected root's authorized paths.
- **SC-002**: Every completed quality checklist has all mandatory items resolved and no clarification
  markers remain.
- **SC-003**: Parent and child review samples contain no duplicated normative requirement.
- **SC-004**: All existing feature `design.md` files and all module `design.md` files remain
  byte-identical after specification and clarification.
- **SC-005**: Every newly seeded root contains `tldr.md`, `spec.md`, and a placeholder `design.md`
  and no `implementation.md`.
- **SC-006**: Every TL;DR in the acceptance fixtures passes the parent's shape and budget checks and
  cites an existing requirement ID for each rule in its `Logic` section.

## Assumptions

- Spec Kit supplies the normal phase procedure and active templates; Concorde supplies path and
  architecture context, including resolved templates for the TL;DR and for the placeholder
  `design.md`.
