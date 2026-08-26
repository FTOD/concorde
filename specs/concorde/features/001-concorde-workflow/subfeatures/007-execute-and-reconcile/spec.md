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
canonical_spec: specs/concorde/features/001-concorde-workflow/subfeatures/007-execute-and-reconcile/spec.md
---

# Feature Specification: Execute and Reconcile

**Created**: 2026-08-26
**Status**: Specified; existing realization has not been hardened into this sub-feature design
**Input**: Route `speckit.implement`, `speckit.analyze`, and `speckit.converge` through the selected attempt.

## Outcome

A coding agent can execute the approved task list, report cross-artifact inconsistencies without
mutation, and append only genuine remaining work while staying inside bounded selected context.

## Parent Context and Boundary

The parent owns lifecycle authority and review boundaries. This child owns task execution,
non-destructive consistency analysis, and convergence of discovered remaining work. It does not own
architecture validation or durable design hardening. The parent core diagram and selected workspace
model are sufficient; no child diagram is needed.

## User Scenarios & Testing

### User Story 1 - Deliver and reconcile one attempt (Priority: P1)

A maintainer asks the coding agent to execute all ready tasks, verify outcomes, analyze remaining
gaps, and make the task list honestly reflect unfinished work.

**Independent Test**: Run execution, analysis, and convergence against complete, incomplete, and
inconsistent top-level and child attempts while snapshotting unrelated roots.

**Acceptance Scenarios**:
1. **Given** a ready task list, **When** implementation runs, **Then** tasks execute in dependency order,
   relevant checks run, and completion state reflects evidence rather than intent.
2. **Given** complete spec, design, plan, and task artifacts, **When** analysis runs, **Then** it reports
   high-signal inconsistencies and coverage gaps without modifying files.
3. **Given** verified remaining work, **When** convergence runs, **Then** only new dependency-ordered
   tasks are appended to the selected attempt without duplicating completed work.

### Edge Cases

- A required artifact is absent, malformed, or belongs to another selected root.
- Tests disagree with maintained intent or cannot establish evidence.
- Convergence finds no genuine remaining work.

## Requirements

- **FR-001**: All three phases MUST resolve and remain within the selected lifecycle root.
- **FR-002**: Implementation MUST honor task dependencies and update completion only after proportionate verification.
- **FR-003**: Implementation context MUST exclude implicit parent and sibling attempts and unrelated deeper architecture.
- **FR-004**: Analysis MUST be strictly read-only and prioritize specification, design, plan, task, and constitution inconsistencies.
- **FR-005**: Analysis MUST distinguish absent evidence, disagreement, ambiguity, duplication, and coverage gaps.
- **FR-006**: Convergence MUST append only verified remaining work, preserve completed tasks, and avoid duplicates.
- **FR-007**: None of these phases may update durable `design.md` or remove the temporal attempt.

## Success Criteria

- **SC-001**: All execution fixtures preserve unrelated feature, parent, and sibling roots byte-for-byte.
- **SC-002**: Analysis reports all seeded critical conflicts and makes zero filesystem changes.
- **SC-003**: Convergence appends every seeded remaining task once and no already-completed task.
- **SC-004**: No task is marked complete in acceptance fixtures without corresponding verification evidence.

## Assumptions

- The task list is the execution index, while durable behavior and design remain higher authorities.
