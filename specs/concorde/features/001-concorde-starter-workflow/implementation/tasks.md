---

description: "Dependency-ordered implementation tasks for the Concorde core workflow"
---

# Tasks: Complete the Concorde Core Workflow

**Input**: Durable intent in `spec.md` and `contracts/`; temporal design in `implementation/`

**Tests**: Required because this feature changes path authority, mutation safety, architecture
validation, and installed command semantics.

**Organization**: Tasks are grouped by the four user stories and are independently testable at each
checkpoint. Existing behavior must be re-verified against the revised contracts before a task is
marked complete.

## Phase 1: Setup and Baseline

**Purpose**: Protect the dirty worktree and establish the current implementation/evidence baseline.

- [X] T001 Record the revised Feature 001 requirement and evidence matrix in `specs/concorde/features/001-concorde-starter-workflow/implementation/validation.md`
- [X] T002 [P] Verify Python, Node, generated-output, and environment ignore coverage in `.gitignore` and `docsite/.gitignore`
- [X] T003 [P] Capture the current core-workflow test and self-validation baseline in `specs/concorde/features/001-concorde-starter-workflow/implementation/validation.md`

---

## Phase 2: Foundational Workflow Contracts and Services

**Purpose**: Freeze the semantic handoff used by every user story and by Feature 003.

**Critical gate**: Feature 001 may validate source/self-hosting behavior, but only Feature 003 may
claim release-installed command materialization.

- [X] T004 [P] Extend Feature Workspace Protocol contract tests for every durable and temporal path in `tests/concorde/contract/test_feature_workspace_contract.py`
- [X] T005 [P] Add five-command intent, result-envelope, and distribution-handoff assertions in `tests/concorde/contract/test_agent_commands.py`
- [X] T006 [P] Add selected-root, phase-path, lifecycle-state, proposal-digest, and no-alias unit tests in `tests/concorde/unit/test_feature_workspace.py`
- [X] T007 Implement the complete immutable workspace path and lifecycle model in `extensions/concorde/runtime/concorde/feature_workspace.py`
- [X] T008 Implement the installed-relative, read-only phase-path adapter in `extensions/concorde/scripts/python/workspace.py`
- [X] T009 Align self-hosting path resolution with the Feature Workspace Protocol in `.specify/scripts/bash/common.sh`, `.specify/scripts/bash/setup-plan.sh`, `.specify/scripts/bash/setup-tasks.sh`, and `.specify/scripts/bash/check-prerequisites.sh`
- [X] T010 Align the five canonical extension command definitions with `contracts/agent-commands.md` in `extensions/concorde/commands/`
- [X] T011 Publish the versioned nine-phase/five-command semantic handoff in `specs/concorde/features/001-concorde-starter-workflow/contracts/agent-commands.md` and `specs/concorde/features/001-concorde-starter-workflow/contracts/feature-workspace.schema.json`

**Checkpoint**: One selected feature returns one complete, safe, versioned durable/temporal path set.

---

## Phase 3: User Story 1 - Establish and Navigate the Architecture Hierarchy (Priority: P1) 🎯 MVP

**Goal**: Propose a root hierarchy safely and navigate exactly one architectural level at a time.

**Independent Test**: Initialize a three-level fixture, request root then child context, and verify
that each response contains only the current module, immediate children, current-level features,
their I/O contracts, permitted externals, and stable deeper navigation references.

### Tests for User Story 1

- [X] T012 [P] [US1] Extend review-first initialization and rollback tests in `tests/concorde/integration/test_initialize.py`
- [X] T013 [P] [US1] Add root-then-child three-level bounded-context assertions in `tests/concorde/integration/test_context.py`
- [X] T014 [P] [US1] Add responsibility, boundary, current-module, child-I/O, external, and one-level view rule fixtures in `tests/concorde/unit/test_rules.py`

### Implementation for User Story 1

- [X] T015 [US1] Complete module, contract, feature, scenario, and navigation projections in `extensions/concorde/runtime/concorde/projection.py`
- [X] T016 [US1] Refactor bounded root/child context around explicit stable identities in `extensions/concorde/runtime/concorde/context.py`
- [X] T017 [US1] Enforce module prose and one-level view completeness in `extensions/concorde/runtime/concorde/validation/hierarchy.py`

**Checkpoint**: US1 passes independently without exposing grandchildren or overwriting architecture.

---

## Phase 4: User Story 2 - Place and Specify a Feature at the Right Level (Priority: P1)

**Goal**: Review, create, and select one nested feature under the correct provider while retaining the
normal Spec Kit lifecycle and one canonical `spec.md`.

**Independent Test**: Place a single-module feature and a cross-child feature, approve the exact
proposal, select each workspace, and prove correct nearest-common-parent ownership, atomic state, and
the durable/temporal path split.

### Tests for User Story 2

- [X] T018 [P] [US2] Add number allocation, safe path, collision, digest, provider, and nearest-common-parent tests in `tests/concorde/unit/test_feature_workspace.py`
- [X] T019 [P] [US2] Add read-only proposal plus atomic select/resume/conflict/idempotency tests in `tests/concorde/integration/test_feature_workspace.py`
- [X] T020 [P] [US2] Prove composed nested artifact materialization and the installed nine-phase path matrix with zero root temporal copies in `tests/concorde/acceptance/test_preset_workflow.py` and `tests/concorde/integration/test_clean_phase_matrix.py`

### Implementation for User Story 2

- [X] T021 [US2] Complete reviewed feature placement, numbering, source-digest-bound proposal, safe path resolution, and atomic selection in `extensions/concorde/runtime/concorde/feature_workspace.py`
- [X] T022 [US2] Complete `feature create` and `feature select` CLI dispatch and exit semantics in `extensions/concorde/runtime/concorde/cli.py`
- [X] T023 [P] [US2] Complete portable create/select command orchestration in `extensions/concorde/commands/speckit.concorde.feature.create.md` and `extensions/concorde/commands/speckit.concorde.feature.select.md`
- [X] T024 [US2] Register all five commands and every required workspace/runtime file in `extensions/concorde/extension.yml`
- [X] T025 [US2] Align the Spec Kit Integration workspace refinement and module contract evidence in `specs/concorde/modules/spec-kit-integration/features/002-manage-feature-workspace/spec.md` and `specs/concorde/modules/spec-kit-integration/contracts/feature-workspace/contract.md`

**Checkpoint**: US2 creates/selects nested features without a second registry, spec, or lifecycle.

---

## Phase 5: User Story 3 - Review Architecture Before Approving the Plan (Priority: P2)

**Goal**: Produce a deterministic readiness result for ownership, refinements, child participation,
boundary contracts, dependency direction, scenario trace, affected view, and expected evidence.

**Independent Test**: A cross-boundary fixture is not architecture-ready until its provider,
refinement, governing contract, ordered scenario interaction, view, and evidence expectation exist;
the same fixture then passes without changing Spec Kit plan authority.

### Tests for User Story 3

- [X] T026 [P] [US3] Add readiness fail-then-pass integration fixtures in `tests/concorde/integration/test_architecture_readiness.py`
- [X] T027 [P] [US3] Add standard/custom representation and schema/example conformance tests in `tests/concorde/unit/test_contract_validation.py`

### Implementation for User Story 3

- [X] T028 [US3] Complete digest-bound architecture-readiness projection and findings in `extensions/concorde/runtime/concorde/readiness.py`
- [X] T029 [P] [US3] Complete deterministic representation adapters and contract conformance rules in `extensions/concorde/runtime/concorde/validation/contracts.py`
- [X] T030 [P] [US3] Complete ordered scenario participant, crossing, and governing-contract rules in `extensions/concorde/runtime/concorde/validation/scenarios.py`
- [X] T031 [US3] Integrate readiness with context and validation without replacing Spec Kit planning in `extensions/concorde/runtime/concorde/context.py` and `extensions/concorde/runtime/concorde/validate.py`

**Checkpoint**: US3 blocks only architecture-ready claims and returns actionable deterministic gaps.

---

## Phase 6: User Story 4 - Implement, Reconcile, and Validate with Bounded Context (Priority: P3)

**Goal**: Return the smallest sufficient active-feature context and deterministically reconcile
durable intent, temporal design, implementation/test evidence, and generated projections.

**Independent Test**: An active feature exposes only relevant durable/temporal artifacts and adjacent
architecture; invalid layout, missing/disagreeing evidence, contract mismatch, and stale projection
fixtures return stable findings over three unchanged runs.

### Tests for User Story 4

- [X] T032 [P] [US4] Add exact active-feature artifact, contract, diagram, refinement, and exclusion tests in `tests/concorde/integration/test_context.py`
- [X] T033 [P] [US4] Add layout, evidence, custom conformance, and delegated-freshness fixtures in `tests/concorde/integration/test_validation.py`
- [X] T034 [P] [US4] Add three-run determinism, cross-presentation semantics, and source-immutability acceptance in `tests/concorde/acceptance/test_core_workflow.py`

### Implementation for User Story 4

- [X] T035 [US4] Discover durable feature diagrams, temporal artifacts, and safe evidence receipts in `extensions/concorde/runtime/concorde/repository.py`
- [X] T036 [US4] Project exact active-feature artifacts, contract bodies, adjacent refinements, and evidence in `extensions/concorde/runtime/concorde/context.py`
- [X] T037 [P] [US4] Complete workspace layout and selected-attempt rules in `extensions/concorde/runtime/concorde/validation/layout.py`
- [X] T038 [P] [US4] Complete evidence-reference and disagreement rules in `extensions/concorde/runtime/concorde/validation/evidence.py`
- [X] T039 [P] [US4] Complete delegated Archify/docsite freshness normalization in `extensions/concorde/runtime/concorde/validation/freshness.py`
- [X] T040 [US4] Coordinate focused validators in stable rule order in `extensions/concorde/runtime/concorde/validate.py`

**Checkpoint**: US4 is bounded, read-only, repeatable, and explicit about unknown/disagreeing evidence.

---

## Phase 7: Polish, Diagrams, Self-Application, and Cross-Feature Handoff

**Purpose**: Reconcile durable architecture and produce honest automated evidence.

- [X] T041 [P] Align the core-workflow textual scenario and governing contracts in `specs/concorde/features/001-concorde-starter-workflow/spec.md` and `specs/concorde/features/001-concorde-starter-workflow/contracts/architecture-sources.md`
- [X] T042 [P] Align component invocation and ordered scenario traces in `specs/concorde/features/001-concorde-starter-workflow/diagrams/core-workflow-scenarios.json` and `specs/concorde/architecture.json`
- [X] T043 Validate the Feature 001 diagram with all Archify showcase checks and deliver a fresh provenance-bearing projection to `generated/architecture/concorde-core-workflow-scenarios.html`
- [X] T044 Verify automatic canonical feature-page embedding and freshness for the Feature 001 diagram in `docsite/tests/integration/production-build.test.ts`
- [X] T045 [P] Align diagram evaluation and durable/temporal workflow guidance in `presets/concorde-core/templates/`, `.specify/templates/`, and `.agents/skills/`
- [X] T046 Publish the Feature 001 handoff digest/inventory for Feature 003 and verify matching references in `specs/concorde/features/003-install-concorde-speckit/contracts/installed-command-surfaces.md`
- [X] T047 Run the complete Python suite, Concorde self-validation, Archify checks, Docusaurus `npm run check`, and `git diff --check`, then record exact automated evidence in `specs/concorde/features/001-concorde-starter-workflow/implementation/validation.md`
- [X] T048 Reconcile automated statuses while leaving SC-001, SC-007, and human approval partial in `specs/concorde/features/001-concorde-starter-workflow/spec.md` and `specs/concorde/modules/spec-kit-integration/features/002-manage-feature-workspace/spec.md`

---

## Dependencies & Execution Order

- Setup has no dependency; Foundational depends on Setup and blocks all stories.
- US1 and US2 depend only on Foundational and are independently testable.
- US3 consumes workspace/provider identities established by Foundational and US2.
- US4 integrates US1 navigation, US2 selection, and US3 readiness/conformance.
- Polish depends on all automated story checkpoints; Feature 003 consumes T046.

## Parallel Opportunities

- T002/T003, T004–T006, T012–T014, T018–T020, T026/T027, T029/T030, T032–T034,
  T037–T039, T041/T042, and T045 affect different files or isolated fixtures.
- After Foundational, US1 hierarchy work and US2 workspace work can proceed independently.

## Parallel Example: User Story 2

```text
Task T018: unit placement/path cases in tests/concorde/unit/test_feature_workspace.py
Task T019: lifecycle integration cases in tests/concorde/integration/test_feature_workspace.py
Task T020: end-to-end normal lifecycle in tests/concorde/acceptance/test_core_workflow.py
```

## Implementation Strategy

### MVP First

1. Complete Setup and Foundational.
2. Complete US1 and prove root→child bounded navigation.
3. Stop and validate before adding placement and reconciliation behavior.

### Incremental Delivery

1. Add US2 nested placement/selection and one normal lifecycle.
2. Add US3 readiness/conformance without changing plan authority.
3. Add US4 bounded reconciliation.
4. Self-apply, validate the diagram, and publish the handoff consumed by Feature 003.

## Notes

- Generated HTML is refreshed by Archify and never edited as maintained intent.
- Feature 003 alone proves release-installed command winners and checkout isolation.
- Human pilot and approval outcomes remain pending until real evidence exists.
