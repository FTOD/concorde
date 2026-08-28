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
**Revised**: 2026-08-27
**Status**: Specified and revised for the parent's document model; existing realization has not been
hardened into this sub-feature's `implementation.md`
**Input**: Route `speckit.specify`, `speckit.clarify`, and `speckit.checklist` through one selected
Concorde root, seeding and preserving `implementation.md` rather than a feature-level `design.md`.

## Outcome

A maintainer can define focused, testable behavior, resolve material uncertainty, and record
requirements-quality review while preserving the boundary between durable intent, accepted
realization, and temporal review state.

## Parent Context and Boundary

The parent owns shared workflow invariants, the document model, and aggregate outcomes. This child
owns specification, clarification, and requirements-quality review for the selected root. For a
child selection, parent durable sources are aggregate read-only context and sibling bodies are
excluded. The parent core diagram and selected workspace model are sufficient; no child diagram is
needed.

## User Scenarios & Testing

### User Story 1 - Produce a ready specification (Priority: P1)

A maintainer describes the selected outcome, resolves only consequential ambiguity, and checks that
the resulting specification is understandable, testable, bounded, and free of implementation design.

**Independent Test**: Run all three phases for new and existing top-level and child roots and verify
durable and checklist writes, accepted-realization preservation, and bounded context reads.

**Acceptance Scenarios**:
1. **Given** a selected root, **When** specification is authored, **Then** only its canonical `spec.md`
   changes and its existing `implementation.md` is preserved byte-for-byte.
2. **Given** a new canonical root, **When** specification runs, **Then** it seeds `spec.md` and an
   `implementation.md` whose only content is the explicit not-yet-hardened state, and creates no
   `design.md` at that root.
3. **Given** material ambiguity, **When** clarification completes, **Then** accepted answers are
   encoded into that same specification without creating a competing copy.
4. **Given** requirements review, **When** a checklist is produced, **Then** it lives beneath the
   selected root's `implementation/checklists/` directory.
5. **Given** the level at which the feature is specified, **When** specification needs architecture
   context, **Then** it reads that level's `module.md` and bounded view, and opens the level's
   `design.md` only when the maintainer asks for a recorded detail.

### Edge Cases

- A child repeats parent-owned vocabulary, invariants, dependencies, or aggregate requirements.
- A cross-component feature lacks either a core component diagram or a clear sufficiency rationale.
- A phase attempts to write through parent or sibling context, to a feature-root `design.md`, or to
  a module `design.md`.
- The selected root still carries a legacy `design.md`.

## Requirements

- **FR-001**: All three phases MUST resolve the selected workspace before artifact access.
- **FR-002**: Specification and clarification MUST write only the selected canonical `spec.md`.
- **FR-003**: Existing durable `implementation.md` content MUST remain byte-identical during these
  phases.
- **FR-004**: Requirements-quality checklists MUST live only in the selected temporal checklist
  directory.
- **FR-005**: A child specification MUST own one focused outcome and MUST NOT duplicate parent-owned
  aggregate facts.
- **FR-006**: Cross-component specifications MUST declare one text-backed core architecture diagram
  or record why prose and the bounded view suffice.
- **FR-007**: Clarification MUST prioritize consequential scope, security, and user-outcome choices
  and encode accepted answers durably.
- **FR-008**: For a new root, specification MUST seed `implementation.md` holding only the explicit
  not-yet-hardened state and MUST NOT create a `design.md` at a feature root; its substantive
  content is written by hardening.
- **FR-009**: These phases MUST use the level's `module.md` as bounded architecture context and MUST
  NOT treat the level's `design.md` as an implicit input or write to it.

## Success Criteria

- **SC-001**: Every phase-routing test writes only within the selected root's authorized paths.
- **SC-002**: Every completed quality checklist has all mandatory items resolved and no clarification
  markers remain.
- **SC-003**: Parent and child review samples contain no duplicated normative requirement.
- **SC-004**: All existing `implementation.md` files and all module `design.md` files remain
  byte-identical after specification and clarification.
- **SC-005**: Every newly seeded root contains `spec.md` and a placeholder `implementation.md` and
  no `design.md`.

## Assumptions

- Spec Kit supplies the normal phase procedure and active templates; Concorde supplies path and
  architecture context, including a resolved template for the placeholder `implementation.md`.
