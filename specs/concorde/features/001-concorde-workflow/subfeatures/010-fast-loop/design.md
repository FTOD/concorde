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

**Revised**: 2026-08-31 — admit explicit logic-preserving pure renames and align architecture
evidence with Constitution 3.0.0

**Status**: Draft

**Input**: User description: "Add a `fast-loop` command for small modifications. The normal workflow
is specify → plan → tasks → implementation → accept-impl; fast-loop directly modifies code and the
related documentation without planning, tasks, implementation, or acceptance."

## Outcome

A maintainer can explicitly invoke `speckit.fast-loop` for a small, well-bounded modification and
receive one directly reconciled change to code, tests, and related maintained documentation without
creating an attempt or running the planning, task-generation, implementation, or implementation-
delivery commands. Changes that are not safely small are rejected before mutation and redirected
to the full workflow.

## Parent Boundary

The parent [Concorde Workflow](../../design.md) owns the aggregate lifecycle, durable document model,
selection rules, shared safety invariants, and command inventory. This child owns only the alternate
direct-edit path that begins from an existing selected anchor feature and may reconcile other related
existing features. It does not redefine ordinary specification, planning, execution, validation, or
delivery behavior.

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

A maintainer describes a small modification from an existing, already-realized anchor feature and
asks the fast-loop command to make it. The command identifies every related existing feature whose
behavior or accepted realization is affected, updates the code, proportional tests, and all related
maintained feature, contract, architecture-detail, or user-facing documents needed to keep the
repository truthful, runs the relevant checks, and reports the resulting diff and evidence without
creating an attempt.

**Why this priority**: Removing ceremony only has value if the complete small change is still coherent
and verifiable when the command returns.

**Independent Test**: Select an anchor feature with an accepted realization, request a small behavior
correction that also affects a related existing feature and an inter-module contract format, run the
command, and verify the code, tests, every affected feature's durable documents, the contract source,
and user-facing documentation agree while no `attempt/` or lifecycle artifact was created and module
responsibilities and dependencies remain unchanged.

**Acceptance Scenarios**:

1. **Given** a valid selected anchor and an affected set of one or more existing features, each with
   an accepted implementation and no active attempt, **When** the maintainer requests an eligible
   small correction, **Then** the command directly applies the code, test, and related documentation
   edits and reports passing targeted evidence.
2. **Given** an eligible change that alters observable behavior in multiple related features,
   **When** the loop completes, **Then** every affected feature's `design.md`, `abstract.md`, and
   `implementation.md` describe the resulting behavior and realization consistently without a
   planning or delivery artifact.
3. **Given** an eligible implementation-only correction that leaves required behavior unchanged,
   **When** the loop completes, **Then** behavioral authority remains unchanged while the accepted
   implementation reference, tests, and affected user-facing documentation are reconciled.
4. **Given** an otherwise eligible change that edits an inter-module contract or maintained
   architecture view, **When** code, documentation, and deterministic checks are complete, **Then**
   the command reports the exact architecture-source diff and hashes as validated evidence and may
   complete without separate post-edit human review under constitution A.V.
5. **Given** an explicit old-to-new name mapping that changes no implementation logic, behavioral or
   data semantics, permissions, failure handling, responsibility, or dependency direction, **When**
   every affected accepted authority can be reconciled under the existing compatibility/migration
   policy, **Then** the command applies the rename directly across all affected roots and proves the
   stale old-name inventory is empty across maintained sources, including rewritten reflection
   entries whose stable `R-NNN` identifiers remain unchanged and valid.

---

### User Story 2 - Escalate work that is not small (Priority: P1)

A maintainer receives a clear, non-mutating explanation when the requested work would cross the fast
boundary, together with the full workflow stage from which to continue.

**Why this priority**: A faster path must not silently become a way around module-boundary review,
active-attempt state, the first accepted realization, or project-level user compatibility policy.

**Independent Test**: Exercise the command with no valid anchor, a placeholder implementation or
active attempt in any affected feature, a new feature, changed module responsibility, changed module
dependency direction, changed whole-project user compatibility or migration policy, and ambiguous
scope; verify each is rejected before any file changes and the response recommends the normal
workflow. Separately verify that a bounded cross-feature change, inter-module contract-format change,
and explicit pure rename that follows existing policy remain eligible when all affected authorities
are reconciled.

**Acceptance Scenarios**:

1. **Given** no valid existing anchor, a placeholder accepted implementation, or an active attempt in
   any affected feature, **When** fast-loop is invoked, **Then** it makes no mutation and identifies
   the blocking condition.
2. **Given** a request that creates or restructures a feature or module, changes a module's
   responsibility or dependency direction, or changes the project's compatibility or migration
   policy for users of the whole project, **When** eligibility is evaluated, **Then** it is rejected
   before mutation and redirected to specify → plan → tasks → implement → accept; an explicit pure
   rename is not such a policy change when it follows the existing policy and changes no logic or
   semantics.
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
passing report names the anchor, affected feature set, changed files, and checks, while the failing
run never claims completion or accepted evidence.

**Acceptance Scenarios**:

1. **Given** all required edits and checks pass, **When** the command finishes, **Then** it reports
   the anchor and every affected feature, changed files, behavioral and documentation impact, tests
   and validations run, and any unrelated pre-existing changes left untouched.
2. **Given** a required check fails, **When** the command cannot repair the failure within the same
   bounded loop, **Then** it does not claim success, does not describe unverified realization as
   accepted, and reports the exact remaining failure and safe next action.

### Edge Cases

- The anchor has an accepted realization, but a related affected feature still has the
  no-accepted-realization placeholder or an active attempt.
- A stale or malformed selection resolves outside the canonical hierarchy.
- An `attempt/` contains only checklists from specification versus substantive planning or execution
  artifacts; both count as active workflow state for fast-loop safety.
- The change initially looks local but a failing test reveals another affected feature or contract;
  the agent expands the affected set and reconciles it before continuing.
- Related prose exists in both feature documents and general user-facing guides.
- A requested rename omits part of the old-to-new mapping, changes executable branching or data
  meaning, leaves a partial old token or duplicate identity, or conflicts with an append-only source.
- The worktree contains unrelated edits, untracked files, or an overlapping edit made by the user.
- The requested change is documentation-only but changes module responsibility, dependency
  direction, or a whole-project user compatibility promise.
- Validation cannot run because a required local tool or dependency is unavailable.

## Requirements

### Functional Requirements

- **FR-001**: Concorde MUST expose one user-visible `speckit.fast-loop` command with equivalent intent,
  arguments, target disclosure, and failure behavior in every supported coding-agent integration.
- **FR-002**: The command MUST require a concrete change description and resolve at least one existing
  canonical feature as its anchor through the Feature Workspace Protocol before reading or writing
  feature-scoped artifacts. The selected anchor is a navigation entry, not an assertion that exactly
  one feature owns the change.
- **FR-003**: Before mutation, the command MUST identify every existing feature whose behavior or
  accepted realization the request can affect. A request is eligible only when every affected
  feature has a non-placeholder accepted implementation and no active `attempt/`.
- **FR-004**: The command MUST reject before mutation any request that creates or restructures a
  feature or module, changes a module responsibility or dependency direction, changes the project's
  compatibility or migration policy for users of the whole project, or remains materially ambiguous
  after bounded inspection. A cross-feature behavioral effect, inter-module contract change, or
  maintained diagram update is not independently disqualifying when the change is otherwise small,
  every related authority is reconciled, and module responsibilities and dependencies stay stable.
  An explicit pure naming migration that satisfies FR-017 follows rather than changes existing
  compatibility/migration policy and is not independently disqualifying.
- **FR-005**: Eligibility preflight MUST inspect the anchor's selection and attempt state, discover the
  affected feature set from bounded module, contract, implementation, test, and documentation
  evidence, deliberately read each affected feature's durable authority and accepted realization,
  verify every affected attempt state, and inspect the existing worktree diff. It MUST NOT load an
  unrelated feature body or any feature's attempt implicitly.
- **FR-006**: An eligible invocation MUST directly edit the implementation and proportional tests,
  plus every related maintained document necessary to keep the completed repository truthful, in
  one command execution.
- **FR-007**: For every affected feature whose required behavior changes, the command MUST update its
  `design.md` and keep `abstract.md` faithful; when its realization changes, it MUST update its
  `implementation.md` to describe the verified current realization. It MUST leave a durable
  behavioral document byte-for-byte unchanged when that feature's behavior did not change.
- **FR-008**: The command MUST update every directly related feature source, inter-module contract,
  maintained diagram, module reference, and user-facing guide necessary to describe an eligible
  completed change truthfully. Such edits MUST preserve module responsibilities and dependency
  direction and MUST exclude unrelated feature and architecture sources.
- **FR-009**: The command MUST NOT create or use `attempt/`, `plan.md`, `tasks.md`, acceptance
  proposals, or task checklists, and MUST NOT invoke the plan, tasks, implement, converge, or
  implementation-delivery workflows as hidden substeps.
- **FR-010**: The command MUST preserve unrelated pre-existing worktree changes and MUST stop before
  writing when overlapping ownership cannot be established safely.
- **FR-011**: The command MUST run tests and deterministic validation in proportion to every changed
  source, including every affected feature, contract, architecture source, and user document.
- **FR-012**: The command MUST claim completion only when code, tests, and maintained documentation
  agree and all required checks pass. If repair cannot finish inside the same bounded loop, it MUST
  report failure and MUST NOT present unverified realization as accepted.
- **FR-013**: The completion report MUST name the anchor and every affected feature, summarize
  eligibility, list changed files, distinguish each feature's behavioral from realization-only
  and referential-only documentation changes, identify every check run and its result, disclose
  unrelated pre-existing changes preserved, report architecture evidence as `not_applicable` or
  `validated`, and state that no attempt or delivery operation was used. For a pure rename it MUST
  also report the old-to-new mapping, stale-name inventory, and every rewritten reflection entry ID.
- **FR-015**: Compatibility and migration eligibility MUST be evaluated only against durable
  project-level promises made to users of the whole project. Internal module contracts, data formats,
  and coordinated feature behavior MAY change in fast-loop when FR-003 through FR-012 remain
  satisfied; feature or module sources MUST NOT invent a separate compatibility or migration policy.
  A pure naming migration MAY replace project-visible names only when it follows the existing policy
  for aliases, deprecation, and migration rather than inventing or weakening that policy.
- **FR-016**: When an eligible invocation edits an inter-module contract, maintained architecture
  diagram, or other architecture authority, the command MUST report the exact validated diff and
  source hashes with architecture evidence state `validated`. Under constitution A.V it MUST NOT
  require a separate post-edit human review for an otherwise eligible fast loop.
- **FR-017**: A pure naming migration MUST require an explicit complete old-to-new mapping and MUST
  change only identifiers, labels, paths, and their references. It MUST preserve implementation
  logic, behavioral and data semantics, permissions, failure handling, module responsibilities, and
  dependency direction; reconcile every bounded affected authority; and deterministically reject
  stale old names, partial replacements, unauthorized aliases, or duplicate identities. The project
  reflection log is maintained docs/specs and MUST be rewritten when its text or references match the
  mapping, while preserving exact unique `R-NNN` identifiers, required structure, maintainer
  decisions, occurrence identity, and problem meaning. Only version-control history is inherently
  outside the maintained-source inventory.
- **FR-014**: An ineligible or blocked response MUST be actionable: it MUST identify the failed
  eligibility rule, make no fast-loop mutation, and direct the maintainer to the normal workflow at
  the earliest applicable stage.

### Scope

**In scope**: direct corrections and small enhancements beginning from one existing anchor and
affecting one or more related existing features; proportional code and test changes; direct
reconciliation of every affected feature's durable trio; bounded inter-module contract-format and
architecture-detail updates that preserve module responsibilities and dependencies; explicit pure
naming migrations across bounded authorities; related user documentation; preflight eligibility,
worktree safety, targeted validation, and a truthful report.

**Out of scope**: new feature roots; a first accepted realization; active attempts in any affected
feature; module or feature restructuring; changed module responsibility or dependency direction;
changes to project-level user compatibility or migration policy other than an explicit pure rename
that follows that policy; unrelated feature or architecture sources; and any hidden use of planning,
tasks, implementation, convergence, or acceptance.

### Key Entities

- **Fast-loop request**: The maintainer's concrete small-change description plus an existing selected
  anchor from which bounded impact discovery begins.
- **Affected feature set**: Every existing canonical feature whose required behavior or accepted
  realization changes, each with an accepted baseline and no active attempt.
- **Eligibility decision**: The pre-mutation result that records whether the request stays inside the
  fast boundary and, when it does not, the earliest normal workflow stage to use.
- **Direct change set**: The code, tests, affected feature documents, related contract and
  architecture detail, and user-facing docs edited by one eligible invocation, excluding unrelated
  worktree changes.
- **Pure naming migration**: An explicit old-to-new mapping applied exhaustively across bounded
  affected authorities with implementation logic and all non-name semantics preserved.
- **Evidence report**: The command's final account of target, scope, files, checks, outcomes, and
  preserved pre-existing work.

## Success Criteria

### Measurable Outcomes

- **SC-001**: In 100% of eligible acceptance fixtures, one command completes the code, proportional
  tests, and required documentation updates with no `attempt/`, plan, task list, or acceptance
  proposal created.
- **SC-002**: In 100% of ineligible fixtures, the command changes zero files and names both the failed
  eligibility rule and the earliest normal workflow stage to use.
- **SC-003**: In all eligible behavior-change fixtures, every affected feature's abstract,
  specification, accepted realization, code, contract/architecture detail, and executable evidence
  agree after the command; in realization-only fixtures, unaffected behavioral documents remain
  byte-identical.
- **SC-004**: In all dirty-worktree fixtures, unrelated pre-existing edits are byte-identical after
  the command, and ambiguous overlapping edits cause a pre-mutation stop.
- **SC-005**: Every successful invocation reports the selected anchor and complete affected feature
  set, every changed file, every required check and result, and explicit confirmation that no attempt
  or delivery operation ran.
- **SC-007**: Eligible fixtures that span two existing features or change an inter-module contract
  format complete directly with all related authorities reconciled; fixtures that change module
  responsibility, dependency direction, or whole-project user compatibility/migration policy make
  zero fast-loop edits and redirect to the full workflow unless the request is a pure rename that
  follows the existing policy.
- **SC-008**: Every eligible fixture that edits maintained architecture sources reports exact
  validated paths, hashes, and diff and completes without a separate post-edit human review or any
  attempt/implementation-delivery artifact.
- **SC-009**: Every eligible pure-rename fixture changes all and only mapped names and references,
  reports every affected authority as referential-only, preserves implementation logic and
  non-name semantics, preserves every rewritten reflection `R-NNN` identifier and valid log shape,
  and produces a zero-result maintained-source stale-name/alias/duplicate inventory.
- **SC-006**: The installed Codex and slash-command surfaces pass equivalent contract scenarios for
  eligible completion, ineligible escalation, target disclosure, and failure reporting.

## Assumptions

- “Small” is determined by ownership and architectural risk, not solely by line count or the number
  of affected feature roots. A coordinated change remains eligible when its affected set is bounded,
  all related authorities can be reconciled in one loop, and module responsibilities, dependencies,
  and project-level user compatibility/migration policy remain stable. Replacing names under that
  existing policy is referential change, not new policy, when FR-017 holds.
- Invoking `speckit.fast-loop` with a concrete change description is the maintainer's explicit
  authorization for the bounded direct edits described here, including related feature and
  inter-module contract sources; it is not approval to change a module responsibility, dependency,
  or whole-project user compatibility/migration policy.
- Fast-loop operates only when every affected feature already has an accepted realization. Creating
  a first accepted implementation remains part of the full workflow.
- Existing targeted test and validation commands are available from the repository; unavailable
  required tooling makes the run incomplete rather than silently successful.
- Direct documentation reconciliation is ordinary maintained-source authoring, not acceptance
  compaction. The command is responsible for keeping every edited authority truthful in the same
  loop.

## Dependencies

- The parent `feature.concorde.workflow` document model, selection rules, and safety invariants.
- Feature Workspace Protocol v9 or its compatible successor for canonical selection, durable paths,
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
- **Observable textual outcome**: one safe small change across a bounded set of existing related
  features, including a logic-preserving pure rename, can be completed directly without attempt
  ceremony, while module-boundary and project-policy changes are redirected before mutation.
- **Parent refinement**: internal child of the project-level workflow feature.
- **Representative scenarios**: the existing current-level `feature-work` scenario covers the
  normal/full-flow contrast and `direct-authoring` covers an eligible small direct change; the
  acceptance scenarios above specialize both without inventing new level-view identifiers.
- **Core feature diagram**: none; the parent core view is sufficient and linked above.
- **Supplemental diagrams**: none.
- **Contracts**: provides `contract.concorde.workflow`; requires
  `contract.concorde.spec-kit-platform`.
- **Level views**: the project module's level view remains authoritative; fast-loop may reconcile
  contract or architecture detail but cannot change module responsibilities or dependencies.
- **Evidence status**: `unknown` until command-surface, fixture, and end-to-end evidence exists.

## Terminology

| Term | Meaning | Relationships |
|---|---|---|
| `Fast-loop request` | The maintainer's explicit small-change description and selected anchor used to begin bounded impact discovery. | `evaluated by` → `Eligibility decision`; `discovers` → `Affected feature set` |
| `Affected feature set` | Every accepted feature whose behavior, realization, or related authority must change together. | `contains` → `Feature`; `bounds` → `Direct change set` |
| `Eligibility decision` | The pre-mutation result that either permits the direct loop or names the normal workflow stage required. | `classifies` → `Fast-loop request` |
| `Direct change set` | The bounded code, tests, feature documents, contracts, architecture detail, and guides edited by one eligible invocation. | `implements` → `Fast-loop request`; `reported by` → `Evidence report` |
| `Pure naming migration` | An explicit old-to-new mapping that changes names across bounded authorities while preserving logic and non-name semantics. | `is a` → `Direct change set` |
| `Evidence report` | The final account of scope, files, checks, outcomes, preserved work, and architecture evidence. | `describes` → `Direct change set`; `contains` → `Finding` |
