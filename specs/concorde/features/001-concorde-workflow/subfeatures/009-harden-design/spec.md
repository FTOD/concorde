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
**Revised**: 2026-08-28
**Status**: Specified and revised for the parent's three-tier feature document model; existing
realization has not been hardened into this sub-feature's `design.md`
**Input**: Review and compact a completed attempt through `speckit.concorde.feature.harden` into the
selected root's `design.md`, optionally amending the level's module `design.md` in the same
approval.

## Outcome

A maintainer can explicitly accept the durable realization of one completed feature or sub-feature
milestone into its feature `design.md`, carry the rationale developed during the attempt into the
level's module `design.md` when the proposal includes it, and atomically remove exactly that
milestone's temporal attempt.

## Parent Context and Boundary

The parent owns the durable/temporal authority model, the document model, and the lifecycle
placement of hardening. This child owns eligibility, candidate synthesis, exact review, approval
binding, failure-safe apply, and result reporting. It does not execute incomplete work, change
behavior requirements, or touch the TL;DR or specification. The stable ID and title are retained;
the hardened feature artifact is the feature `design.md`. The parent diagram already depicts the
agent/runtime approval split and the artifact transition.

## User Scenarios & Testing

### User Story 1 - Accept one completed realization (Priority: P1)

A maintainer reviews the proposed feature `design.md`, any proposed module `design.md` amendment, and
the exact cleanup manifest, then explicitly approves or rejects compaction of the selected attempt.

**Independent Test**: Exercise eligible, incomplete, malformed, stale, unsafe, interrupted, first-time,
repeat, parent, and child attempts, with and without a module-reference amendment, while
snapshotting all related roots, TL;DRs, specifications, module summaries, and module references.

**Acceptance Scenarios**:
1. **Given** incomplete tasks or unresolved checklist items, **When** hardening is proposed, **Then**
   it is ineligible and changes nothing.
2. **Given** an eligible attempt, **When** proposal mode completes, **Then** the maintainer sees the
   candidate feature `design.md`, any candidate module `design.md` amendment, the exact whole-attempt
   removal target, the source digest, and the retained authorities.
3. **Given** that exact current proposal is approved, **When** apply completes, **Then** the selected
   feature `design.md` matches the reviewed candidate, the level's module `design.md` matches the
   reviewed amendment when one was proposed, only the selected attempt is absent, and `tldr.md` and
   `spec.md` are byte-identical.
4. **Given** a first hardening of a root whose `design.md` holds only the not-yet-hardened state,
   **When** apply completes, **Then** the feature `design.md` is written in full; **Given** a later
   hardening, **Then** it is completed and updated rather than duplicated.
5. **Given** a stale or interrupted apply, **When** the operation fails, **Then** the previous feature
   `design.md`, the previous module `design.md`, and the complete attempt remain recoverable.

### Edge Cases

- No recognizable task exists; task or checklist Markdown is malformed.
- Proposal paths escape the selected root or use symlinks.
- The proposal names a `module.md`, a `tldr.md`, a `spec.md`, a module `design.md` at a level other
  than the one at which the feature is specified, or a legacy `implementation.md`.
- Parent, child, sibling, selection, or source digest changes after review.

## Requirements

- **FR-001**: Eligibility MUST require at least one recognizable task, every task complete, and
  every existing checklist item complete and well formed.
- **FR-002**: Proposal mode MUST be read-only and return the runtime-resolved candidate location,
  task/checklist summaries, selected target, optional module-reference amendment target, cleanup
  target, and source digest.
- **FR-003**: The candidate feature `design.md` MUST capture accepted collaboration, flows,
  decisions, evidence, limitations, and the implementation detail a coder needs under the parent's
  six fixed sections, without copying the temporal task log.
- **FR-004**: Apply MUST require explicit approval of the exact unchanged proposal.
- **FR-005**: Apply MUST accept only the selected root's `design.md`, its complete `implementation/`
  directory, and — when the proposal includes it — the module `design.md` of the level at which the
  feature is specified as mutation targets, and MUST reject any `module.md`, `tldr.md`, `spec.md`,
  any other level's `design.md`, and any `implementation.md`.
- **FR-006**: Realization replacement, reference amendment, and attempt removal MUST complete
  atomically or restore every prior state.
- **FR-007**: Child hardening MUST preserve parent and siblings; parent hardening MUST preserve every
  child root.
- **FR-008**: A success result MUST report prior/resulting feature `design.md` digests,
  prior/resulting module `design.md` digests when amended, removed artifacts, selected feature, and
  retained authorities.
- **FR-009**: A candidate module `design.md` amendment MUST contain only implementation detail and
  rationale developed during the attempt, organized under the reference's stable headings, and MUST
  NOT restate or alter facts owned by `module.md`, contracts, or the level view.
- **FR-010**: Hardening MUST write the feature `design.md` in full on the first accepted milestone
  and complete or update it on later ones, never leaving the not-yet-hardened placeholder beside
  accepted content.

## Success Criteria

- **SC-001**: Every incomplete, malformed, unsafe, or stale fixture produces zero durable or temporal
  changes.
- **SC-002**: Every approved fixture leaves a feature `design.md` byte-identical to the reviewed
  candidate, a module `design.md` byte-identical to the reviewed amendment when one was proposed,
  and removes exactly one attempt.
- **SC-003**: Every injected interruption restores the prior feature `design.md`, the prior module
  `design.md`, and the complete attempt.
- **SC-004**: All parent, child, and sibling roots, every `tldr.md` and `spec.md`, and every
  `module.md` outside the selected mutation targets remain byte-identical.

## Assumptions

- Requirements changes occur through specification review, not through hardening; the TL;DR is
  never refreshed by hardening.
- The level at which the feature is specified is the level whose module `design.md` a hardening
  proposal may amend; a feature realized across several modules records lower-level detail in those
  modules' references through their own features' hardening.
