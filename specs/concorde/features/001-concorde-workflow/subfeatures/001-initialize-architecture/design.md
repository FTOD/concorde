---
id: feature.concorde.workflow.initialize-architecture
kind: feature
module: module.concorde
parent_feature: feature.concorde.workflow
refines: []
subfeatures: []
scenarios:
  - feature-work
contracts:
  provided:
    - contract.concorde.workflow
  required:
    - contract.concorde.spec-kit-platform
evidence_status: partial
canonical_design: specs/concorde/features/001-concorde-workflow/subfeatures/001-initialize-architecture/design.md
---

# Feature Design: Initialize Architecture

**Created**: 2026-08-26
**Revised**: 2026-08-29
**Status**: Specified and revised for the parent's three-tier feature document model; existing
realization has not been accepted into this sub-feature's `implementation.md`
**Input**: Establish a minimal Concorde root through `speckit.concorde.init` without overwriting
maintained intent, seeding the root module summary and its design reference together while making
the Skills → Scripts → Workspace Files interaction model explicit.

## Outcome

A maintainer can review and explicitly approve a minimal root module package — summary, design
reference, level view, and initial contracts — before later workflow steps depend on architectural
ownership, while an already configured hierarchy is reported as unchanged instead of receiving a
blank starter proposal.

## Parent Context and Boundary

Feature 001 owns the overall lifecycle, the document model, and shared artifact authority. This child
owns only root initialization: proposal, approval, safe application, idempotent re-entry, and the
first writing of the root `module.md` summary and `design.md` reference. Installation is out of
scope, and so is migrating an existing package that predates the reference. The parent core diagram
and root bounded module view sufficiently show the participating maintainer, command surface,
runtime, and maintained sources; no child diagram is needed.

## User Scenarios & Testing

### User Story 1 - Establish the root safely (Priority: P1)

A maintainer reviews the proposed root responsibility, boundaries, contracts, paths, and conflicts
before deciding whether to create it, and receives a root whose summary can be read in minutes.

**Independent Test**: Run proposal and approved application in an empty supported project, verify the
seeded summary and reference against the parent's shape and reading-budget checks, then rerun the
operation and compare maintained bytes.

**Acceptance Scenarios**:
1. **Given** an uninitialized project, **When** proposal mode runs, **Then** it reports the exact root
   artifacts — including `module.md`, `design.md`, and the level view — their source basis, the
   Skills/Scripts/Workspace-Files interaction model, and conflicts without mutation.
2. **Given** that exact proposal is approved and still current, **When** apply runs, **Then** all root
   artifacts appear together and validate.
3. **Given** an approved application, **When** it completes, **Then** the root `module.md` has the
   summary shape the parent requires (responsibility, boundary, structure diagram reference,
   feature/contract/submodule inventory tables, representative scenario) within the reading budget,
   and the adjacent `design.md` exists, is reachable from the summary, and states that no product
   implementation detail has
   been recorded yet.
4. **Given** the same initialized hierarchy, **When** initialization is repeated, **Then** it reports
   unchanged, returns the configured root paths, children, features, and contracts, and does not
   propose or rewrite starter sources.

### Edge Cases

- Existing content conflicts with one proposed path.
- The target already has a `module.md` without a `design.md`, or the reverse.
- The target has `.concorde/config.json` but its configured root package is incomplete or unreadable.
- A proposal escapes the project, is malformed, or becomes stale before application.
- Promotion is interrupted after staging but before completion.

## Requirements

### Functional Requirements

- **FR-001**: Initialization MUST first return a reviewable proposal containing root responsibility,
  boundary, contracts, child summaries, every proposed path (summary, design reference, level view,
  configuration, initial contracts), source digest, conflicts, and the Skills/Scripts/Workspace-Files
  interaction model.
- **FR-002**: Proposal mode MUST be read-only and silence MUST NOT count as approval.
- **FR-003**: Application MUST accept only the explicitly reviewed project-contained proposal.
- **FR-004**: Application MUST create the configuration, root `module.md` summary, root `design.md`
  reference, root view with `meta.legend.mode` set to `hidden`, and approved initial contracts as one
  failure-safe change.
- **FR-005**: Conflicting existing content, unsafe paths, malformed proposals, and stale state MUST
  leave existing maintained sources unchanged and produce actionable findings.
- **FR-006**: Repeating initialization against the same accepted hierarchy MUST be idempotent.
- **FR-007**: The seeded `module.md` MUST satisfy the parent's summary shape and reading budget on
  creation, and the seeded `design.md` MUST be reachable from it and MAY state only that no product
  implementation detail has
  been recorded yet.
- **FR-008**: A target that already holds a summary without a reference, or a reference without a
  summary, MUST be reported as a conflict with a remediation rather than silently completed.
- **FR-009**: When a configured root package already exists, proposal mode MUST return `unchanged`
  with its root paths, children, features, contracts, and interaction model; it MUST NOT compare the
  package to the starter template, infer replacement product modules, or emit an overwrite proposal.
- **FR-010**: The seed MUST explain that Skills are the maintainer-facing interface, Scripts perform
  deterministic operations, and Workspace Files preserve durable, temporal, and generated state,
  while making clear that these workflow roles are not default product modules.

## Success Criteria

- **SC-001**: Every proposal-only test produces zero filesystem changes.
- **SC-002**: Every approved clean initialization produces a deterministically valid root hierarchy
  whose summary passes the parent's shape and reading-budget checks, whose reference is reachable,
  and whose seed view explicitly hides its legend.
- **SC-003**: Every seeded conflict, partial package, or stale proposal preserves all pre-existing
  maintained bytes.
- **SC-004**: Repeating initialization against unchanged sources returns unchanged in all fixtures.
- **SC-005**: A valid configured hierarchy that has evolved beyond the starter text still returns
  unchanged with its current registration, while an incomplete configured hierarchy returns one
  actionable conflict and creates no files.

## Assumptions

- Concorde and a compatible Spec Kit host are already installed.
- The maintainer supplies a project root they are authorized to initialize.
- Adding a `design.md` to a module that predates it is migration work owned by the parent, not an
  initialization behavior.
