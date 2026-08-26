---
id: feature.concorde.workflow.manage-feature-workspaces
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
canonical_spec: specs/concorde/features/001-concorde-workflow/subfeatures/004-manage-feature-workspaces/spec.md
---

# Feature Specification: Manage Feature Workspaces

**Created**: 2026-08-26
**Status**: Specified; existing realization has not been hardened into this sub-feature design
**Input**: Propose, create, select, and resolve one canonical top-level feature or immediate sub-feature workspace.

## Outcome

A maintainer can place or select exactly one valid feature-shaped lifecycle root, and every later
phase receives authoritative durable, temporal, ownership, parent, and sibling context for that root.

## Parent Context and Boundary

The parent owns why features are selected in the overall workflow. This child owns
`speckit.concorde.feature.create`, `speckit.concorde.feature.select`, and Feature Workspace Protocol
routing. It does not own the behavior of the phases that consume those paths. The parent component
diagram already covers command, adapter, control-state, and artifact interaction.

## User Scenarios & Testing

### User Story 1 - Create or select one lifecycle root (Priority: P1)

A maintainer reviews placement for a new feature or chooses an existing root, then continues normal
Spec Kit work without relying on branch naming or a second registry.

**Independent Test**: Create and select top-level and immediate-child fixtures, then resolve every
normal phase and inspect the returned Protocol v3 fields and paths.

**Acceptance Scenarios**:
1. **Given** one valid module or top-level parent, **When** creation is proposed, **Then** the exact
   root, durable pair, registration, ownership, relationship context, and source digest are shown.
2. **Given** the exact placement is approved, **When** creation completes, **Then** the root is
   registered bidirectionally where required, validates, and becomes selectable.
3. **Given** an existing root with a non-empty attempt, **When** selection omits explicit resume,
   **Then** the previous selection is preserved and a conflict is reported.

### Edge Cases

- Both or neither placement modes are supplied; a child is used as a parent; depth exceeds two.
- IDs, paths, ownership, canonical metadata, or parent registration conflict.
- A selected root is symlinked, stale, missing its durable pair, or has an unsafe path.

## Requirements

- **FR-001**: Creation MUST accept exactly one reviewed placement mode: providing module or top-level parent.
- **FR-002**: A sub-feature MUST inherit its parent's module and live directly beneath that parent's `subfeatures/` directory.
- **FR-003**: Creation MUST present exact changes and remain read-only until explicit approval.
- **FR-004**: Every created root MUST contain one canonical `spec.md` and adjacent durable `design.md` and be registered by its module or parent.
- **FR-005**: Selection MUST resolve exactly one valid root by stable ID or canonical path and persist only that root.
- **FR-006**: Protocol v3 MUST return selected kind, ID, module, durable/temporal paths, implementation state, nullable parent context, and bounded siblings.
- **FR-007**: Every phase MUST remain confined to the selected root; parent and sibling attempts MUST never be implicit inputs.
- **FR-008**: Invalid creation or selection MUST preserve prior maintained sources and selection state.

## Success Criteria

- **SC-001**: All creation fixtures propose the canonical root and correct registration without mutation.
- **SC-002**: All nine normal phases resolve correctly for top-level and child selections.
- **SC-003**: All invalid depth, ownership, path, identity, registration, and resume cases preserve prior state.
- **SC-004**: A child workspace result contains its parent and ordered siblings but no related attempt paths.

## Assumptions

- Exactly one standard `.specify/feature.json` pointer remains the selection authority.
