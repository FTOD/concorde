---
id: feature.concorde.workflow.harden-design
kind: feature
module: module.concorde
parent_feature: feature.concorde.workflow
refines: []
subfeatures: []
scenarios:
  - scenario-concorde-review-implement-and-reconcile
contracts:
  provided:
    - contract.concorde.workflow
  required:
    - contract.concorde.spec-kit-platform
architecture_view: specs/concorde/architecture.json
evidence_status: partial
canonical_spec: specs/concorde/features/001-concorde-workflow/subfeatures/009-harden-design/spec.md
---

# Feature Specification: Harden Design

**Created**: 2026-08-26
**Status**: Specified; existing realization has not been hardened into this sub-feature design
**Input**: Review and compact a completed attempt through `speckit.concorde.feature.harden`.

## Outcome

A maintainer can explicitly accept the durable realization of one completed feature or sub-feature
milestone and atomically remove exactly that milestone's temporal attempt.

## Parent Context and Boundary

The parent owns the durable/temporal authority model and lifecycle placement of hardening. This child
owns eligibility, candidate design synthesis, exact review, approval binding, failure-safe apply, and
result reporting. It does not execute incomplete work or change behavior requirements. The parent
diagram already depicts the agent/runtime approval split and artifact transition.

## User Scenarios & Testing

### User Story 1 - Accept one completed realization (Priority: P1)

A maintainer reviews the proposed final design and exact cleanup manifest, then explicitly approves
or rejects compaction of the selected attempt.

**Independent Test**: Exercise eligible, incomplete, malformed, stale, unsafe, interrupted, parent,
and child attempts while snapshotting all related roots.

**Acceptance Scenarios**:
1. **Given** incomplete tasks or unresolved checklist items, **When** hardening is proposed, **Then** it
   is ineligible and changes nothing.
2. **Given** an eligible attempt, **When** proposal mode completes, **Then** the maintainer sees the
   candidate design, exact whole-attempt removal target, source digest, and retained authorities.
3. **Given** that exact current proposal is approved, **When** apply completes, **Then** the selected
   design matches the reviewed candidate and only the selected attempt is absent.
4. **Given** a stale or interrupted apply, **When** the operation fails, **Then** the previous design
   and complete attempt remain recoverable.

### Edge Cases

- No recognizable task exists; task or checklist Markdown is malformed.
- Proposal paths escape the selected root or use symlinks.
- Parent, child, sibling, selection, or source digest changes after review.

## Requirements

- **FR-001**: Eligibility MUST require at least one recognizable task, every task complete, and every existing checklist item complete and well formed.
- **FR-002**: Proposal mode MUST be read-only and return the runtime-resolved candidate location, task/checklist summaries, selected target, cleanup target, and source digest.
- **FR-003**: The candidate design MUST concisely capture accepted collaboration, flows, decisions, evidence, and limitations without copying the temporal task log.
- **FR-004**: Apply MUST require explicit approval of the exact unchanged proposal.
- **FR-005**: Apply MUST accept only the selected root's `design.md` and complete `implementation/` directory as mutation targets.
- **FR-006**: Design replacement and attempt removal MUST complete atomically or restore both prior states.
- **FR-007**: Child hardening MUST preserve parent and siblings; parent hardening MUST preserve every child root.
- **FR-008**: A success result MUST report prior/resulting design digests, removed artifacts, selected feature, and retained authorities.

## Success Criteria

- **SC-001**: Every incomplete, malformed, unsafe, or stale fixture produces zero durable or temporal changes.
- **SC-002**: Every approved fixture leaves a design byte-identical to the reviewed candidate and removes exactly one attempt.
- **SC-003**: Every injected interruption restores both the prior design and complete attempt.
- **SC-004**: All parent, child, and sibling roots outside the selected mutation targets remain byte-identical.

## Assumptions

- Requirements changes occur through specification review, not through hardening.
