---
id: feature.concorde.workflow
kind: feature
module: module.concorde
refines: []
subfeatures:
  - feature.concorde.workflow.initialize-architecture
  - feature.concorde.workflow.retrieve-bounded-context
  - feature.concorde.workflow.answer-workflow-questions
  - feature.concorde.workflow.manage-feature-workspaces
  - feature.concorde.workflow.specify-behavior
  - feature.concorde.workflow.plan-delivery
  - feature.concorde.workflow.execute-and-reconcile
  - feature.concorde.workflow.validate-architecture
  - feature.concorde.workflow.harden-design
scenarios:
  - scenario-concorde-establish-and-place-feature
  - scenario-concorde-review-implement-and-reconcile
contracts:
  provided:
    - contract.concorde.workflow
  required:
    - contract.concorde.spec-kit-platform
architecture_view: specs/concorde/architecture.json
diagrams:
  - source: specs/concorde/features/001-concorde-workflow/diagrams/concorde-workflow-components.json
    role: core
    kind: architecture
    scenarios:
      - scenario-concorde-establish-and-place-feature
      - scenario-concorde-review-implement-and-reconcile
    output: generated/architecture/concorde-workflow-components.html
evidence_status: partial
canonical_spec: specs/concorde/features/001-concorde-workflow/spec.md
---

# Feature Specification: Concorde Workflow

**Created**: 2026-08-19

**Revised**: 2026-08-26

**Status**: Decomposed into first-class workflow-step sub-features; automated implementation evidence
exists, while human comprehension and browser review remain pending

**Input**: User description: "Keep Feature 001 as the simple specification of the complete Concorde
workflow and decompose each important command or related command set into one immediate sub-feature."

## Outcome

A maintainer can move one correlated change from architectural placement through specification,
planning, implementation, validation, and accepted durable design while every command respects one
selected feature root, bounded architectural context, explicit human authority, and reproducible
source ownership.

## Workflow Boundary

Concorde surrounds the normal Spec Kit lifecycle with architectural controls; it does not replace
Spec Kit's specification, clarification, planning, task, implementation, analysis, convergence, or
issue-conversion procedures. The parent feature owns the end-to-end order, shared concepts,
cross-step invariants, and command inventory. Each immediate sub-feature owns the observable behavior
of one cohesive workflow step and does not restate this aggregate contract.

Installation, bundle management, update, and removal belong to
`feature.concorde.install-with-spec-kit`. Publication of the read-only project documentation belongs
to `feature.concorde.publish-project-docsite`.

## Decomposition

| Order | Sub-feature | Owned command surface |
|---:|---|---|
| 1 | `feature.concorde.workflow.initialize-architecture` | `speckit.concorde.init` |
| 2 | `feature.concorde.workflow.retrieve-bounded-context` | `speckit.concorde.context` |
| 3 | `feature.concorde.workflow.answer-workflow-questions` | `speckit.concorde.ask` |
| 4 | `feature.concorde.workflow.manage-feature-workspaces` | `speckit.concorde.feature.create`, `speckit.concorde.feature.select`, and Feature Workspace Protocol routing |
| 5 | `feature.concorde.workflow.specify-behavior` | `speckit.specify`, `speckit.clarify`, `speckit.checklist` |
| 6 | `feature.concorde.workflow.plan-delivery` | `speckit.plan`, `speckit.tasks`, `speckit.taskstoissues` |
| 7 | `feature.concorde.workflow.execute-and-reconcile` | `speckit.implement`, `speckit.analyze`, `speckit.converge` |
| 8 | `feature.concorde.workflow.validate-architecture` | `speckit.concorde.validate` |
| 9 | `feature.concorde.workflow.harden-design` | `speckit.concorde.feature.harden` |

The decomposition follows maintainer outcomes rather than implementation packages. Commands are
grouped only when they operate on the same selected artifacts as one recognizable workflow step.
The children inherit `module.concorde`, cannot own children, and remain distinct from adjacent-module
feature refinement.

## Shared Vocabulary and Invariants

- A **module** owns one responsibility, its current-level features, boundary contracts, and a view of
  itself plus immediate children.
- A **feature root** is either a top-level feature or one immediate sub-feature. It owns durable
  `spec.md` and `design.md` documents and at most one temporal `implementation/` attempt.
- A **selection** identifies exactly one canonical feature root. All lifecycle phases use the paths
  returned for that selected root.
- **Bounded context** exposes one architectural level. Parent and sibling feature relationships are
  concise navigation context, not permission to load their implementation attempts.
- `spec.md` owns required behavior; `design.md` owns the accepted realization; `implementation/`
  owns one temporary attempt. Generated pages and reports are projections, not maintained intent.
- Human approval is required before architecture creation or design hardening mutates maintained
  intent. Read-only questions, context retrieval, analysis, and validation do not grant approval.
- Feature containment and adjacent-module feature refinement are separate relationships with
  separate validation and documentation labels.

## End-to-End Workflow

| Stage | Maintainer outcome | Operation |
|---:|---|---|
| 1 | Establish or review the root module package and its boundary. | `speckit.concorde.init` |
| 2 | Inspect exactly one module or feature relationship level and choose ownership. | `speckit.concorde.context` |
| Any | Ask a source-grounded, read-only workflow question. | `speckit.concorde.ask` |
| 3 | Propose and approve a canonical top-level feature or immediate sub-feature, or select an existing root. | `speckit.concorde.feature.create` / `speckit.concorde.feature.select` |
| 4 | Define behavior, resolve material uncertainty, and review requirements quality. | `speckit.specify` / `speckit.clarify` / `speckit.checklist` |
| 5 | Plan one implementation attempt, order its work, and optionally project tasks into issues. | `speckit.plan` / `speckit.tasks` / `speckit.taskstoissues` |
| 6 | Execute tasks, analyze artifact consistency, and append only genuine remaining work. | `speckit.implement` / `speckit.analyze` / `speckit.converge` |
| 7 | Deterministically validate maintained architecture and evidence references. | `speckit.concorde.validate` |
| 8 | Review and explicitly compact a completed attempt into durable accepted design. | `speckit.concorde.feature.harden` |

Validation may be invoked after any maintained structural change, not only at stage 7. Context and
the question surface may be used whenever a maintainer needs to navigate or understand the workflow.

## Cross-Sub-feature Relationships

Initialization must precede operations that depend on an existing Concorde hierarchy. Workspace
management establishes the selected root consumed by all normal Spec Kit phases. Specification is
the durable behavioral input to planning; planning creates the temporal artifacts consumed by
execution; validation may challenge any maintained structural claim; hardening is eligible only
after execution work and review state are complete. A later attempt begins again from the durable
specification and the last accepted design.

## Core Component Diagram

The maintained parent diagram at
`diagrams/concorde-workflow-components.json` remains the one core component view because it shows the
shared invocation layers and artifact authorities used across all nine children. The child specs use
that parent view plus the bounded module view; they do not duplicate it unless a future child-specific
scenario introduces a materially different component question.

## User Scenarios & Testing

### User Story 1 - Complete a governed change (Priority: P1)

A maintainer establishes architectural ownership, selects the right feature root, specifies and
plans the change, directs implementation, validates maintained sources, and accepts the resulting
design without losing the distinction between intent, attempt, and evidence.

**Independent Test**: Complete the lifecycle for one top-level feature and one sub-feature and verify
that every phase uses only the selected root's authoritative paths.

**Acceptance Scenarios**:

1. **Given** an initialized project, **When** a maintainer completes all ordered stages, **Then** the
   result has one canonical specification, one accepted design, no hardened temporal attempt, and a
   valid maintained hierarchy.
2. **Given** an immediate sub-feature is selected, **When** normal phases run, **Then** parent durable
   context is read-only and sibling bodies and attempts are not implicitly loaded.

### User Story 2 - Stop safely at a review boundary (Priority: P1)

A maintainer can inspect any proposal, question answer, context result, analysis report, or validation
finding before authorizing a mutation.

**Independent Test**: Exercise every review-only mode against a snapshot and verify maintained
sources are byte-identical afterward.

**Acceptance Scenarios**:

1. **Given** a creation or hardening proposal, **When** approval is withheld, **Then** no maintained
   source or selection state changes.
2. **Given** missing or conflicting evidence, **When** validation or analysis runs, **Then** the result
   reports disagreement or uncertainty rather than rewriting intent.

### User Story 3 - Resume from durable authority (Priority: P2)

A maintainer starts a later delivery attempt from the current specification and accepted design
without depending on a previous temporal task log.

**Independent Test**: Harden one attempt, begin another, and verify the new attempt resolves the same
durable root without root-level compatibility copies.

**Acceptance Scenarios**:

1. **Given** a hardened feature, **When** planning starts again, **Then** a fresh `implementation/`
   workspace is created beneath that feature root and the durable pair remains authoritative.

### Edge Cases

- A command receives an unknown, ambiguous, unsafe, or stale module/feature target.
- A proposed sub-feature uses a child as its parent or attempts a third containment level.
- A phase finds an existing non-empty attempt without explicit resume authority.
- A contract, refinement, scenario, diagram, or parent registration is missing or contradictory.
- The maintained source digest changes between proposal review and approved application.
- Generated evidence disagrees with maintained intent or cannot be reproduced.

## Requirements

### Functional Requirements

- **FR-001**: Concorde MUST preserve the ordered workflow and command ownership declared in the
  Decomposition and End-to-End Workflow sections.
- **FR-002**: Every command MUST operate on one explicit or selected canonical target and MUST reject
  ambiguous, unsafe, or structurally invalid targets.
- **FR-003**: All normal Spec Kit phases MUST use the selected Feature Workspace Protocol paths and
  MUST NOT derive competing root-level plan, task, or checklist paths.
- **FR-004**: The workflow MUST support exactly two feature-containment levels while keeping
  containment independent from adjacent-module refinement.
- **FR-005**: Parent specifications MUST own aggregate outcomes, shared invariants, ordering, and
  decomposition; child specifications MUST own focused workflow-step behavior.
- **FR-006**: Every lifecycle root MUST independently own one durable `spec.md`, one durable
  `design.md`, optional durable contracts and diagrams, and at most one temporal `implementation/`.
- **FR-007**: Bounded operations MUST disclose their target, source basis, status, and complete
  findings without silently expanding unrelated deeper content.
- **FR-008**: Proposal-only, question, context, analysis, and validation operations MUST be read-only.
- **FR-009**: Mutations of maintained architectural intent or accepted design MUST require explicit
  approval of the presented proposal and MUST fail safely if reviewed inputs become stale.
- **FR-010**: Missing or conflicting implementation evidence MUST be represented as unknown or
  disagreement, never as inferred agreement.
- **FR-011**: Installed Codex and slash-command presentations MUST preserve equivalent command intent,
  arguments, path authority, review boundaries, and failure behavior.
- **FR-012**: Generated diagrams, documentation, indexes, manifests, and reports MUST remain
  reproducible projections of maintained sources and MUST exclude temporal attempts.
- **FR-013**: A feature-owned diagram MUST supplement text, declare its role, live under the owning
  lifecycle root's `diagrams/`, and never silently define behavior or contracts.
- **FR-014**: The workflow MUST remain usable in an installed project without depending on this
  repository's source-tree paths.
- **FR-015**: Deterministic operations MUST return stable structured statuses and actionable findings
  suitable for both human review and automated tests.

### Scope

**In scope**: root initialization; bounded context; workflow questions; feature creation and
selection; selected-root routing for all nine normal Spec Kit phases; architecture validation;
feature hardening; the shared authority and containment model connecting those operations.

**Out of scope**: installation and bundle lifecycle; documentation-site publication mechanics;
application-specific implementation quality; a third feature-containment level; a second feature
lifecycle or registry.

### Key Entities

- **Module**: One architectural responsibility with current-level features, contracts, children, and
  a one-level view.
- **Feature root**: A top-level feature or immediate sub-feature with its own durable and temporal
  artifact boundaries.
- **Selection**: The canonical pointer to exactly one feature root.
- **Workspace result**: Versioned paths and bounded relationship context for the selected root.
- **Implementation attempt**: Temporary plan, tasks, checklists, research, models, guidance, and
  evidence for one delivery cycle.
- **Proposal**: A reviewable, source-bound description of a permitted maintained mutation.
- **Finding**: A deterministic rule result identifying severity, location, explanation, and remedy.

## Success Criteria

### Measurable Outcomes

- **SC-001**: All 16 installed command surfaces map to exactly one sub-feature and appear once in the
  aggregate workflow inventory.
- **SC-002**: In all lifecycle routing tests, every phase reads or writes only the selected top-level
  feature or immediate sub-feature paths returned by the workspace result.
- **SC-003**: In all approval-gated fixtures, withholding approval or changing reviewed sources causes
  zero maintained-intent mutations.
- **SC-004**: Repeated validation of unchanged sources produces byte-equivalent ordered findings.
- **SC-005**: All seeded invalid hierarchy, containment, refinement, contract, scenario, path, and
  selection cases produce actionable findings.
- **SC-006**: Every generated parent page lists its immediate sub-features once in authored order, and
  every child page exposes parent and sibling navigation without publishing temporal attempts.
- **SC-007**: At least 90% of first-time maintainers can identify the command for each workflow stage
  and distinguish specification, accepted design, implementation attempt, and generated evidence
  after no more than five minutes with the parent feature.
- **SC-008**: A completed approved hardening leaves the reviewed `design.md`, removes exactly the
  selected attempt, and preserves parent, sibling, and child authorities not named by the proposal.

## Assumptions

- Spec Kit remains authoritative for its nine normal lifecycle procedures.
- Concorde is already installed and the project has a supported Spec Kit version.
- Parent context and sibling summaries are sufficient for ordinary child work; deeper sources are
  opened only by deliberate navigation.
- Human comprehension metrics require separate pilot evidence and are not implied by automated tests.

## Dependencies

- `contract.concorde.workflow` and `contract.concorde.spec-kit-platform`.
- The maintained `module.concorde` hierarchy, contracts, and bounded architecture view.
- The installation and documentation-publication features for distribution and generated-site
  behavior outside this workflow's boundary.
