---
id: feature.concorde.workflow.execute-and-reconcile
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
canonical_design: specs/concorde/features/001-concorde-workflow/subfeatures/007-execute-and-reconcile/design.md
---

# Feature Design: Execute and Reconcile

**Created**: 2026-08-26
**Revised**: 2026-08-28
**Status**: Specified and revised for the parent's three-tier feature document model; existing
realization has not been hardened into this sub-feature's `implementation.md`
**Input**: Route `speckit.implement`, `speckit.analyze`, and `speckit.converge` through the selected
attempt, keeping every discovery inside it until hardening.

## Outcome

A coding agent can execute the approved task list, report cross-artifact inconsistencies without
mutation, and append only genuine remaining work while staying inside bounded selected context and
recording what it learns where hardening can later find it.

## Parent Context and Boundary

The parent owns lifecycle authority, review boundaries, and the document model. This child owns task
execution, non-destructive consistency analysis, and convergence of discovered remaining work. It
does not own architecture validation or hardening. The parent core diagram and selected workspace
model are sufficient; no child diagram is needed.

## User Scenarios & Testing

### User Story 1 - Deliver and reconcile one attempt (Priority: P1)

A maintainer asks the coding agent to execute all ready tasks, verify outcomes, analyze remaining
gaps, and make the task list honestly reflect unfinished work.

**Independent Test**: Run execution, analysis, and convergence against complete, incomplete, and
inconsistent top-level and child attempts while snapshotting unrelated roots, module summaries, and
module references.

**Acceptance Scenarios**:
1. **Given** a ready task list, **When** implementation runs, **Then** tasks execute in dependency
   order against the feature `implementation.md` baseline, relevant checks run, and completion state
   reflects evidence rather than intent.
2. **Given** complete abstract, specification, accepted realization, plan, and task artifacts, **When**
   analysis runs, **Then** it reports high-signal inconsistencies and coverage gaps — including any
   statement in the abstract that the specification does not support — without modifying files.
3. **Given** verified remaining work, **When** convergence runs, **Then** only new dependency-ordered
   tasks are appended to the selected attempt without duplicating completed work.
4. **Given** a design decision, alternative, or implementation detail discovered during execution,
   **When** the agent records it, **Then** it is written inside the selected attempt, and no
   `abstract.md`, `design.md`, feature `implementation.md`, `module.md`, or module `design.md` changes.

### Edge Cases

- A required artifact is absent, malformed, or belongs to another selected root.
- Tests disagree with maintained intent or cannot establish evidence.
- The abstract and the specification disagree on a behavior a task implements.
- Convergence finds no genuine remaining work.
- Execution learns something that would belong in a module `design.md` before any hardening.

## Requirements

- **FR-001**: All three phases MUST resolve and remain within the selected lifecycle root.
- **FR-002**: Implementation MUST honor task dependencies, MUST read the feature `implementation.md` as its
  accepted baseline, and MUST update completion only after proportionate verification.
- **FR-003**: Implementation context MUST exclude implicit parent and sibling attempts, unrelated
  deeper architecture, and any module `design.md` not deliberately opened and cited.
- **FR-004**: Analysis MUST be strictly read-only and prioritize specification, accepted realization,
  plan, task, and constitution inconsistencies, and MUST report any disagreement between `abstract.md`
  and `design.md` naming the prevailing requirement.
- **FR-005**: Analysis MUST distinguish absent evidence, disagreement, ambiguity, duplication, and
  coverage gaps.
- **FR-006**: Convergence MUST append only verified remaining work, preserve completed tasks, and
  avoid duplicates.
- **FR-007**: None of these phases may update `abstract.md`, `design.md`, the feature `implementation.md`, any
  module `module.md` or `implementation.md`, or remove the temporal attempt.
- **FR-008**: Rationale, alternatives, and implementation detail discovered during execution MUST be
  recorded within the selected attempt so that hardening can carry the durable parts into the
  feature `implementation.md` and the level's `implementation.md`.

## Success Criteria

- **SC-001**: All execution fixtures preserve unrelated feature, parent, and sibling roots, every
  `abstract.md` and `design.md`, and every module summary and reference byte-for-byte.
- **SC-002**: Analysis reports all seeded critical conflicts, including every seeded abstract/specification
  disagreement, and makes zero filesystem changes.
- **SC-003**: Convergence appends every seeded remaining task once and no already-completed task.
- **SC-004**: No task is marked complete in acceptance fixtures without corresponding verification
  evidence.

## Assumptions

- The task list is the execution index, while durable behavior and accepted realization remain
  higher authorities.
