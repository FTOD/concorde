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
canonical_design: specs/concorde/features/001-concorde-workflow/subfeatures/004-manage-feature-workspaces/design.md
---

# Feature Design: Manage Feature Workspaces

**Created**: 2026-08-26
**Revised**: 2026-08-28
**Status**: Specified and revised for the parent's three-tier feature document model; existing
realization has not been hardened into this sub-feature's `implementation.md`
**Input**: Resolve, validate, and route the standard Spec Kit selection of one canonical top-level
feature or immediate sub-feature workspace whose durable trio is `abstract.md`, `design.md`, and
`implementation.md`.

## Outcome

Every normal Spec Kit phase receives authoritative durable, temporal, ownership, parent, and sibling
context for exactly one valid feature-shaped lifecycle root, selected through the standard Spec Kit
pointer rather than a Concorde command.

## Parent Context and Boundary

The parent owns why features are selected in the overall workflow and the document model every root
must satisfy. This child owns Feature Workspace Protocol resolution and routing of the standard Spec
Kit selection, together with the deterministic placement rules a selected root must satisfy.
Creating a root is the normal `speckit.specify` phase with `SPECIFY_FEATURE_DIRECTORY` set to the
canonical path, and selecting a root is the standard `.specify/feature.json` `feature_directory`
record; this child adds no creation or selection command and no second selection store. It does not
own the behavior of the phases that consume the resolved paths. The parent component diagram already
covers command, adapter, control-state, and artifact interaction.

## User Scenarios & Testing

### User Story 1 - Work inside one selected lifecycle root (Priority: P1)

A maintainer creates a feature root through `speckit.specify` at its canonical path or points the
standard Spec Kit selection at an existing root, then continues normal Spec Kit work without relying
on branch naming, a Concorde selection command, or a second registry.

**Independent Test**: Select top-level and immediate-child fixtures through `.specify/feature.json`,
then resolve every normal phase and inspect the returned protocol fields and paths, including
legacy-name and missing-abstract fixtures.

**Acceptance Scenarios**:
1. **Given** `SPECIFY_FEATURE_DIRECTORY` names a canonical unused root beneath a module's `features/`
   or a top-level parent's `subfeatures/`, **When** `speckit.specify` runs, **Then** the root
   contains `abstract.md`, `design.md`, and a `implementation.md` holding only the not-yet-hardened state,
   contains no `implementation.md`, and `.specify/feature.json` records that root.
2. **Given** a selected root whose spec front matter (`id`, `module`, and `parent_feature` for a
   sub-feature) agrees with its module or parent registration, **When** any normal phase runs,
   **Then** the adapter returns the selected kind, ID, module, durable paths naming `abstract.md`,
   `design.md`, and `implementation.md`, temporal paths, `attempt_state`, and bounded relationship
   context for that root.
3. **Given** a selected root with a non-empty `attempt/` attempt, **When** a phase resolves
   the workspace, **Then** the attempt is reported through `attempt_state: active` and is
   never replaced or removed silently.
4. **Given** a selected root with former `tldr.md`/`spec.md` files or an `implementation/` directory,
   **When** a phase
   resolves the workspace or `speckit.concorde.validate` runs, **Then** the root is reported invalid
   with a rename remediation and no maintained source or selection state changes.
5. **Given** a selected root that is unregistered, misplaced, or missing any file of its durable
   trio, **When** a phase resolves the workspace or `speckit.concorde.validate` runs, **Then**
   actionable findings are returned and no maintained source or selection state changes.

### Edge Cases

- The selected root sits at a third containment level, names a child as its parent, or disagrees
  with its parent's module.
- IDs, paths, ownership, canonical metadata, or parent registration conflict.
- A selected root is symlinked, stale, missing part of its durable trio, or has an unsafe path.
- A root has a legacy filename, no `abstract.md`, or an alias or symlink standing in for a canonical name.
- No feature is selected, or the selection points outside the configured specification package.

## Requirements

- **FR-001**: The selection authority MUST be the standard Spec Kit `.specify/feature.json`
  `feature_directory` record, written by `speckit.specify` or set through
  `SPECIFY_FEATURE_DIRECTORY`; no Concorde creation or selection command and no second selection
  store exists.
- **FR-002**: A sub-feature MUST inherit its parent's module and live directly beneath that parent's
  `subfeatures/` directory; a top-level feature MUST live directly beneath its module's `features/`
  directory.
- **FR-003**: A valid root MUST contain one canonical `design.md` with adjacent durable `abstract.md` and
  `implementation.md` and MUST be registered by its module or parent; for a new root the specify addendum
  seeds that trio.
- **FR-004**: Resolution MUST accept exactly one valid root and MUST reject unsafe, symlinked,
  unregistered, misplaced, or third-level paths without changing selection state.
- **FR-005**: The Feature Workspace Protocol MUST return selected kind, ID, module, durable paths
  naming `abstract.md`, `design.md`, and `implementation.md`, temporal paths, attempt state, nullable
  parent context whose durable trio uses the same names, and bounded siblings.
- **FR-006**: Every phase MUST remain confined to the selected root; parent and sibling attempts
  MUST never be implicit inputs.
- **FR-007**: A non-empty `attempt/` attempt MUST be reported as `attempt_state:
  active` and MUST never be replaced, archived as a second authority, or removed by resolution.
- **FR-008**: Registration, canonical path, two-level containment, and identity rules MUST be
  enforced deterministically by `speckit.concorde.validate`, and invalid roots MUST preserve prior
  maintained sources and selection state.
- **FR-009**: A root containing legacy `tldr.md`/`spec.md` files or an `implementation/` attempt
  directory MUST be rejected with migration guidance; a root without `abstract.md` MUST receive an
  authoring remediation, and no alias or symlink may satisfy a canonical name.

## Success Criteria

- **SC-001**: All canonical top-level and child fixtures resolve without mutation, and all
  unregistered, misplaced, or unsafe fixtures produce actionable findings.
- **SC-002**: All nine normal phases resolve correctly for top-level and child selections and receive
  `abstract.md` as the orientation path and `implementation.md` as the accepted-realization path.
- **SC-003**: All invalid depth, ownership, path, identity, registration, legacy-name,
  duplicate-name, and missing-abstract cases preserve prior state.
- **SC-004**: A child workspace result contains its parent and ordered siblings but no related
  attempt paths.

## Assumptions

- Exactly one standard `.specify/feature.json` pointer remains the selection authority.
- The constitution (v2.0.0, principle A.III) no longer requires one providing module per feature, so
  reviewed placement is expressed in spec front matter and feature lists and enforced by validation
  rather than by a dedicated creation command.
- Adding the abstract path and renaming the accepted-realization path in the protocol follow the
  protocol's own compatibility rules; whether that is a new major protocol version is decided by
  the implementation plan.
