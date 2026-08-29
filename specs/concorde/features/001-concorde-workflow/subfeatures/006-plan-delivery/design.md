---
id: feature.concorde.workflow.plan-delivery
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
canonical_design: specs/concorde/features/001-concorde-workflow/subfeatures/006-plan-delivery/design.md
---

# Feature Design: Plan Delivery

**Created**: 2026-08-26
**Revised**: 2026-08-28
**Status**: Specified and revised for the parent's three-tier feature document model; existing
realization has not been hardened into this sub-feature's `implementation.md`
**Input**: Route `speckit.plan`, `speckit.tasks`, and `speckit.taskstoissues` through one temporal
attempt, planning from `design.md`, the accepted feature `implementation.md`, and the level's `module.md`.

## Outcome

A maintainer can turn the selected durable behavior and accepted realization baseline into one
bounded, dependency-ordered delivery attempt and, when requested, a faithful issue projection.

## Parent Context and Boundary

The parent owns workflow ordering, durable/temporal authority, and the document model. This child
owns planning, task generation, and task-to-issue conversion. It does not execute tasks or harden the
result. The parent component diagram and selected workspace paths sufficiently describe participants.

## User Scenarios & Testing

### User Story 1 - Prepare executable work (Priority: P1)

A maintainer reviews architecture and contracts, chooses an implementation approach, and receives an
ordered task list confined to the selected root's active attempt.

**Independent Test**: Plan top-level and child fixtures with and without a hardened baseline,
generate tasks, convert them to issues in a test sink, and compare paths, requirement coverage,
dependency order, and reference citations.

**Acceptance Scenarios**:
1. **Given** a selected root, **When** planning starts, **Then** it reads that root's `design.md` and
   `implementation.md`, uses the abstract only to orient, uses the level's `module.md` and bounded view as
   architecture context, and writes only beneath its `attempt/` directory.
2. **Given** a root whose `implementation.md` holds only the not-yet-hardened state, **When** planning
   starts, **Then** it treats the feature as having no accepted baseline rather than inventing one.
3. **Given** the plan needs a constraint or rationale recorded only in the level's `implementation.md`,
   **When** the planner consults it, **Then** the plan cites that reference and does not copy it into
   any durable document.
4. **Given** an approved plan, **When** tasks are generated, **Then** they cover behavior, architecture,
   contracts, validation, documentation freshness, and acceptance evidence where applicable.
5. **Given** a complete task list, **When** issue conversion is explicitly requested, **Then** issue
   order and dependencies preserve the task plan without changing durable sources.

### Edge Cases

- The accepted realization is unhardened, stale, or conflicts with the current specification.
- A constraint the plan depends on exists only in a module design reference.
- A planner treats the abstract as if it were the specification.
- Tasks omit architecture or validation work required by the selected change.
- Issue publication lacks external authorization or a configured target.

## Requirements

- **FR-001**: Planning MUST resolve the selected root and create or continue only its temporal
  attempt.
- **FR-002**: Planning MUST treat selected `design.md` as required behavior and the selected feature
  `implementation.md` as the accepted realization baseline, treating the not-yet-hardened placeholder as
  the absence of a baseline; the abstract MAY orient the planner but MUST NOT substitute for `design.md`.
- **FR-003**: Child planning MAY read parent durable aggregate context but MUST NOT read sibling or
  parent attempts implicitly.
- **FR-004**: Tasks MUST be dependency ordered, independently actionable, and traceable to
  requirements or acceptance outcomes.
- **FR-005**: Required architecture, contract, validation, diagram, documentation, and evidence work
  MUST appear explicitly in the plan and tasks.
- **FR-006**: Issue conversion MUST preserve task identity, order, dependencies, and scope and MUST
  require separate authority for external writes.
- **FR-007**: These phases MUST NOT update `abstract.md`, `design.md`, the feature `implementation.md`, any module
  `module.md` or `implementation.md`, or create root-level compatibility copies.
- **FR-008**: Planning MUST use the level's `module.md` as bounded architecture context and MAY
  consult that level's `implementation.md` only for a specific recorded detail, citing it in the plan.

## Success Criteria

- **SC-001**: All planning artifacts appear only beneath the selected root's `attempt/`
  directory.
- **SC-002**: Every buildable requirement in acceptance fixtures maps to at least one task.
- **SC-003**: Every converted issue set preserves all task dependencies and ordering constraints.
- **SC-004**: Parent, sibling, `abstract.md`, `design.md`, feature `implementation.md`, module summary, and module
  reference bytes remain unchanged throughout planning.
- **SC-005**: Every fixture plan that used a design reference cites it; no fixture plan reproduces
  reference content into a durable document.

## Assumptions

- External issue creation occurs only when the maintainer separately authorizes and configures it.
