---
id: feature.concorde.workflow.initialize-architecture
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
canonical_spec: specs/concorde/features/001-concorde-workflow/subfeatures/001-initialize-architecture/spec.md
---

# Feature Specification: Initialize Architecture

**Created**: 2026-08-26
**Status**: Specified; existing realization has not been hardened into this sub-feature design
**Input**: Establish a minimal Concorde root through `speckit.concorde.init` without overwriting maintained intent.

## Outcome

A maintainer can review and explicitly approve a minimal root module package before later workflow
steps depend on architectural ownership.

## Parent Context and Boundary

Feature 001 owns the overall lifecycle and shared artifact authority. This child owns only root
initialization: proposal, approval, safe application, and idempotent re-entry. Installation is out of
scope. The parent core diagram and root bounded module view sufficiently show the participating
maintainer, command surface, runtime, and maintained sources; no child diagram is needed.

## User Scenarios & Testing

### User Story 1 - Establish the root safely (Priority: P1)

A maintainer reviews the proposed root responsibility, boundaries, contracts, paths, and conflicts
before deciding whether to create it.

**Independent Test**: Run proposal and approved application in an empty supported project, then rerun
the operation and compare maintained bytes.

**Acceptance Scenarios**:
1. **Given** an uninitialized project, **When** proposal mode runs, **Then** it reports the exact root
   artifacts, source basis, and conflicts without mutation.
2. **Given** that exact proposal is approved and still current, **When** apply runs, **Then** all root
   artifacts appear together and validate.
3. **Given** the same initialized hierarchy, **When** initialization is repeated, **Then** it reports
   unchanged and does not rewrite sources.

### Edge Cases

- Existing content conflicts with one proposed path.
- A proposal escapes the project, is malformed, or becomes stale before application.
- Promotion is interrupted after staging but before completion.

## Requirements

### Functional Requirements

- **FR-001**: Initialization MUST first return a reviewable proposal containing root responsibility,
  boundary, contracts, child summaries, paths, source digest, and conflicts.
- **FR-002**: Proposal mode MUST be read-only and silence MUST NOT count as approval.
- **FR-003**: Application MUST accept only the explicitly reviewed project-contained proposal.
- **FR-004**: Application MUST create the configuration, root module, root view, and approved initial
  contracts as one failure-safe change.
- **FR-005**: Conflicting existing content, unsafe paths, malformed proposals, and stale state MUST
  leave existing maintained sources unchanged and produce actionable findings.
- **FR-006**: Repeating initialization against the same accepted hierarchy MUST be idempotent.

## Success Criteria

- **SC-001**: Every proposal-only test produces zero filesystem changes.
- **SC-002**: Every approved clean initialization produces a deterministically valid root hierarchy.
- **SC-003**: Every seeded conflict or stale proposal preserves all pre-existing maintained bytes.
- **SC-004**: Repeating initialization against unchanged sources returns unchanged in all fixtures.

## Assumptions

- Concorde and a compatible Spec Kit host are already installed.
- The maintainer supplies a project root they are authorized to initialize.
