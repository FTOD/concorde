---
id: feature.concorde.workflow.fast-loop
kind: feature
module: module.concorde
parent_feature: feature.concorde.workflow
refines: []
scenarios:
  - feature-work
  - direct-authoring
contracts:
  provided:
    - contract.concorde.workflow
  required:
    - contract.concorde.spec-kit-platform
diagrams: []
evidence_status: unknown
canonical_design: specs/concorde/features/001-concorde-workflow/subfeatures/010-fast-loop/design.md
---

# Feature Design: Fast Loop

**Read first**: [abstract.md](abstract.md) — the self-contained abstract of this feature. **Accepted
realization**: [implementation.md](implementation.md) — consulted when changing the command or fixing
a bug.

**Created**: 2026-08-29

**Status**: Draft

**Input**: User description: "Add a `fast-loop` command for small modifications. The normal workflow
is specify → plan → tasks → implementation → accept-impl; fast-loop directly modifies code and the
related documentation without planning, tasks, implementation, or acceptance."

## Outcome

A maintainer can explicitly invoke `speckit.fast-loop` for a small, well-bounded modification and
receive one directly reconciled change to code, tests, and related maintained documentation without
creating an attempt or running the planning, task-generation, implementation, or implementation-
acceptance commands. Changes that are not safely small are rejected before mutation and redirected
to the full workflow.

## Parent Boundary

The parent [Concorde Workflow](../../design.md) owns the aggregate lifecycle, durable document model,
selection rules, shared safety invariants, and command inventory. This child owns only the alternate
direct-edit path for an existing selected feature. It does not redefine ordinary specification,
planning, execution, validation, or acceptance behavior.

## Core Component Diagram and Supplemental Scenario Views

- **Core decision**: No child-owned diagram is needed. The parent's maintained core architecture
  view, `../../diagrams/concorde-workflow-components.json`, already shows the maintainer, coding-agent
  command surfaces, selected-workspace adapter, durable feature documents, code and evidence. The
  Functionality, requirements, and scenarios below state the fast-loop eligibility and direct-edit
  behavior completely.
- **Supplemental decisions**: None. The two short ordered flows in the acceptance scenarios do not
  need a separate dynamic view.
- **Generated view**: `generated/architecture/concorde-workflow-components.html` (parent-owned).

## User Scenarios & Testing

### User Story 1 - Complete a small change directly (Priority: P1)

A maintainer describes a small modification against one selected, already-realized feature and asks
the fast-loop command to make it. The command updates the code, proportional tests, and every related
maintained feature or user-facing document needed to keep the repository truthful, runs the relevant
checks, and reports the resulting diff and evidence without creating an attempt.

**Why this priority**: Removing ceremony only has value if the complete small change is still coherent
and verifiable when the command returns.

**Independent Test**: Select a feature with an accepted realization, request a local behavior
correction covered by that feature, run the command, and verify the code, tests, affected durable
feature documents, and user-facing documentation agree while no `attempt/` or lifecycle artifact was
created.

**Acceptance Scenarios**:

1. **Given** one valid selected feature with an accepted implementation and no active attempt,
   **When** the maintainer requests an eligible local correction, **Then** the command directly
   applies the code, test, and related documentation edits and reports passing targeted evidence.
2. **Given** an eligible change that alters observable feature behavior, **When** the loop completes,
   **Then** the selected feature's `design.md`, `abstract.md`, and `implementation.md` describe the
   resulting behavior and realization consistently without a planning or acceptance artifact.
3. **Given** an eligible implementation-only correction that leaves required behavior unchanged,
   **When** the loop completes, **Then** behavioral authority remains unchanged while the accepted
   implementation reference, tests, and affected user-facing documentation are reconciled.

---

### User Story 2 - Escalate work that is not small (Priority: P1)

A maintainer receives a clear, non-mutating explanation when the requested work would cross the fast
boundary, together with the full workflow stage from which to continue.

**Why this priority**: A faster path must not silently become a way around architectural ownership,
contract review, active-attempt state, or the first accepted realization.

**Independent Test**: Exercise the command with an unselected target, placeholder implementation,
active attempt, architecture change, contract change, new feature, multi-feature behavior change,
and ambiguous scope; verify each is rejected before any file changes and the response recommends the
normal workflow.

**Acceptance Scenarios**:

1. **Given** no single valid selected feature, a placeholder accepted implementation, or an active
   attempt, **When** fast-loop is invoked, **Then** it makes no mutation and identifies the blocking
   condition.
2. **Given** a request that creates or restructures a feature or module, changes a boundary contract
   or architecture view, changes compatibility, or needs coordinated behavior across feature roots,
   **When** eligibility is evaluated, **Then** it is rejected before mutation and redirected to
   specify → plan → tasks → implement → accept.
3. **Given** pre-existing worktree changes overlap files the command would edit and safe ownership of
   the edits cannot be established, **When** preflight runs, **Then** the command preserves those
   changes and stops with an actionable explanation.

---

### User Story 3 - Finish with truthful evidence (Priority: P2)

A maintainer can distinguish a completed fast loop from a partial or failed one using a concise
report of scope, files, checks, and remaining concerns.

**Why this priority**: Direct editing is trustworthy only when success means the maintained docs,
implementation, and executable evidence agree.

**Independent Test**: Run one passing and one deliberately failing eligible change and verify the
passing report names the selected feature, changed files, and checks, while the failing run never
claims completion or accepted evidence.

**Acceptance Scenarios**:

1. **Given** all required edits and checks pass, **When** the command finishes, **Then** it reports
   the selected feature, changed files, behavioral and documentation impact, tests and validations
   run, and any unrelated pre-existing changes left untouched.
2. **Given** a required check fails, **When** the command cannot repair the failure within the same
   bounded loop, **Then** it does not claim success, does not describe unverified realization as
   accepted, and reports the exact remaining failure and safe next action.

### Edge Cases

- The selected feature exists but its `implementation.md` is still the no-accepted-realization
  placeholder.
- A stale or malformed selection resolves outside the canonical hierarchy.
- An `attempt/` contains only checklists from specification versus substantive planning or execution
  artifacts; both count as active workflow state for fast-loop safety.
- The change initially looks local but a failing test reveals a cross-feature or contract impact.
- Related prose exists in both feature documents and general user-facing guides.
- The worktree contains unrelated edits, untracked files, or an overlapping edit made by the user.
- The requested change is documentation-only but changes normative behavior or a boundary promise.
- Validation cannot run because a required local tool or dependency is unavailable.

## Requirements

### Functional Requirements

- **FR-001**: Concorde MUST expose one user-visible `speckit.fast-loop` command with equivalent intent,
  arguments, target disclosure, and failure behavior in every supported coding-agent integration.
- **FR-002**: The command MUST require a concrete change description and resolve exactly one existing
  canonical selected feature through the Feature Workspace Protocol before reading or writing
  feature-scoped artifacts.
- **FR-003**: A request is eligible only when the selected feature already has a non-placeholder
  accepted implementation, has no active `attempt/`, and the requested result remains within that
  feature's existing outcome and ownership.
- **FR-004**: The command MUST reject before mutation any request that creates or restructures a
  feature or module, changes module responsibility or dependency direction, changes a boundary
  contract or maintained architecture diagram, changes compatibility or migration policy, spans
  behavioral authority across feature roots, or remains materially ambiguous after bounded
  inspection.
- **FR-005**: Eligibility preflight MUST inspect current selection and attempt state, the selected
  feature's behavioral authority and accepted realization, bounded module context, relevant code and
  tests, and the existing worktree diff without loading sibling bodies or attempts implicitly.
- **FR-006**: An eligible invocation MUST directly edit the implementation and proportional tests,
  plus every related maintained document necessary to keep the completed repository truthful, in
  one command execution.
- **FR-007**: When required behavior changes within the existing feature boundary, the command MUST
  update the selected feature's `design.md` and keep `abstract.md` faithful; when realization changes,
  it MUST update `implementation.md` to describe the verified current realization. It MUST leave a
  durable behavioral document byte-for-byte unchanged when that behavior did not change.
- **FR-008**: The command MAY update non-architectural user-facing guides that directly describe the
  changed behavior, but MUST NOT edit a module summary, module design reference, boundary contract,
  maintained architecture diagram, parent or sibling feature body, or unrelated feature source.
- **FR-009**: The command MUST NOT create or use `attempt/`, `plan.md`, `tasks.md`, acceptance
  proposals, or task checklists, and MUST NOT invoke the plan, tasks, implement, converge, or
  implementation-acceptance workflows as hidden substeps.
- **FR-010**: The command MUST preserve unrelated pre-existing worktree changes and MUST stop before
  writing when overlapping ownership cannot be established safely.
- **FR-011**: The command MUST run tests and deterministic validation in proportion to every changed
  source, including selected feature and documentation checks when durable documentation changed.
- **FR-012**: The command MUST claim completion only when code, tests, and maintained documentation
  agree and all required checks pass. If repair cannot finish inside the same bounded loop, it MUST
  report failure and MUST NOT present unverified realization as accepted.
- **FR-013**: The completion report MUST name the selected feature, summarize eligibility, list
  changed files, distinguish behavioral from realization-only documentation changes, identify every
  check run and its result, disclose unrelated pre-existing changes preserved, and state that no
  attempt or acceptance operation was used.
- **FR-014**: An ineligible or blocked response MUST be actionable: it MUST identify the failed
  eligibility rule, make no fast-loop mutation, and direct the maintainer to the normal workflow at
  the earliest applicable stage.

### Scope

**In scope**: direct corrections and small enhancements wholly contained by one existing selected
feature; proportional code and test changes; direct reconciliation of that feature's durable trio
when affected; related non-architectural user documentation; preflight eligibility, worktree safety,
targeted validation, and a truthful completion report.

**Out of scope**: new feature roots; a first accepted realization; active attempts; module or feature
restructuring; module summaries or design references; architecture views; boundary contracts;
cross-feature behavioral changes; compatibility or migration changes; dependency or distribution
changes; and any hidden use of planning, tasks, implementation, convergence, or acceptance.

### Key Entities

- **Fast-loop request**: The maintainer's concrete small-change description plus the selected feature
  against which eligibility is evaluated.
- **Eligibility decision**: The pre-mutation result that records whether the request stays inside the
  fast boundary and, when it does not, the earliest normal workflow stage to use.
- **Direct change set**: The code, tests, selected feature documents, and related user-facing docs
  edited by one eligible invocation, excluding unrelated worktree changes.
- **Evidence report**: The command's final account of target, scope, files, checks, outcomes, and
  preserved pre-existing work.

## Success Criteria

### Measurable Outcomes

- **SC-001**: In 100% of eligible acceptance fixtures, one command completes the code, proportional
  tests, and required documentation updates with no `attempt/`, plan, task list, or acceptance
  proposal created.
- **SC-002**: In 100% of ineligible fixtures, the command changes zero files and names both the failed
  eligibility rule and the earliest normal workflow stage to use.
- **SC-003**: In all eligible behavior-change fixtures, the selected feature's abstract,
  specification, accepted realization, code, and executable evidence agree after the command; in
  realization-only fixtures, the behavioral documents remain byte-identical.
- **SC-004**: In all dirty-worktree fixtures, unrelated pre-existing edits are byte-identical after
  the command, and ambiguous overlapping edits cause a pre-mutation stop.
- **SC-005**: Every successful invocation reports one selected feature, every changed file, every
  required check and result, and explicit confirmation that no attempt or acceptance operation ran.
- **SC-006**: The installed Codex and slash-command surfaces pass equivalent contract scenarios for
  eligible completion, ineligible escalation, target disclosure, and failure reporting.

## Assumptions

- “Small” is determined by ownership and risk, not solely by line count: a change is fast-loop
  eligible only when it remains inside one existing feature's current behavior and architecture.
- Invoking `speckit.fast-loop` with a concrete change description is the maintainer's explicit
  authorization for the bounded direct edits described here; it is not approval for an architecture
  or contract change.
- Fast-loop operates only on a feature that already has an accepted realization. Creating the first
  accepted implementation remains part of the full workflow.
- Existing targeted test and validation commands are available from the repository; unavailable
  required tooling makes the run incomplete rather than silently successful.
- Direct documentation reconciliation is ordinary maintained-source authoring, not acceptance
  compaction. The command is responsible for keeping every edited authority truthful in the same
  loop.

## Dependencies

- The parent `feature.concorde.workflow` document model, selection rules, and safety invariants.
- Feature Workspace Protocol v8 or its compatible successor for canonical selection, durable paths,
  parent context, bounded siblings, and attempt state.
- `contract.concorde.spec-kit-platform` for equivalent installed command presentation.
- Existing project-specific test and deterministic validation surfaces.

## Concorde Architecture Alignment

- **Stable feature ID**: `feature.concorde.workflow.fast-loop`
- **Providing module**: `module.concorde`
- **Decomposition decision**: atomic immediate sub-feature; it cannot own children.
- **Feature containment**: immediate child of `feature.concorde.workflow`, inheriting the parent's
  module and shared workflow/document invariants.
- **Authority split**: the parent owns aggregate lifecycle order and safety; this child owns fast-loop
  eligibility, direct reconciliation, escalation, and evidence reporting.
- **Observable textual outcome**: one safe small change can be completed directly without attempt
  ceremony, while ineligible work is redirected before mutation.
- **Parent refinement**: internal child of the project-level workflow feature.
- **Representative scenarios**: the existing current-level `feature-work` scenario covers the
  normal/full-flow contrast and `direct-authoring` covers an eligible small direct change; the
  acceptance scenarios above specialize both without inventing new level-view identifiers.
- **Core feature diagram**: none; the parent core view is sufficient and linked above.
- **Supplemental diagrams**: none.
- **Contracts**: provides `contract.concorde.workflow`; requires
  `contract.concorde.spec-kit-platform`.
- **Level views**: the project module's level view remains authoritative; fast-loop does not change
  architecture.
- **Evidence status**: `unknown` until command-surface, fixture, and end-to-end evidence exists.
