---

description: "Refactoring tasks for the Concorde core workflow"
---

# Tasks: Complete the Concorde Core Workflow

**Input**: Durable intent in `spec.md` and `contracts/`; temporal design in `implementation/`

**Tests**: Required. This is a behavioral refactor of an installed workflow, so contract, unit,
integration, and clean-install acceptance tests precede the corresponding implementation changes.

**Organization**: Tasks are grouped by user story. Existing `init`, `context`, and `validate`
behavior is preserved while shared path, context, and validation responsibilities are separated.

## Phase 1: Setup and Refactoring Baseline

**Purpose**: Lock current behavior and prepare one evidence record for this attempt.

- [X] T001 Record baseline commands, capability gaps, and Feature 001-only evidence headings in `specs/concorde/features/001-concorde-starter-workflow/implementation/validation.md`
- [X] T002 [P] Verify Python/Node ignore coverage and add only missing critical patterns to `.gitignore` and `docsite/.gitignore`
- [X] T003 [P] Add nested feature-root, selection-state, and source-hash fixture helpers in `tests/concorde/support/feature_workspace.py`

---

## Phase 2: Foundational Workspace and Composition Services

**Purpose**: Establish the portable path/selection boundary and prove supported Spec Kit command composition before story work depends on it.

**Critical gate**: Failure of the clean-install public composition test stops implementation; managed Spec Kit core scripts must not be patched as the product mechanism.

- [X] T004 [P] Add Feature Workspace Protocol example, safe-path, status, and derived-path contract tests in `tests/concorde/contract/test_feature_workspace_contract.py`
- [X] T005 [P] Add safe root resolution, phase routing, lifecycle, atomic selection, and no-alias unit tests in `tests/concorde/unit/test_feature_workspace.py`
- [X] T006 Implement immutable workspace path/state models and safe selection persistence in `extensions/concorde/runtime/concorde/feature_workspace.py`
- [X] T007 Implement the portable JSON phase-path adapter in `extensions/concorde/scripts/python/workspace.py`
- [X] T008 Add public preset command compositions for specify, clarify, checklist, plan, tasks, implement, analyze, converge, and task-to-issue routing in `presets/concorde-core/preset.yml` and `presets/concorde-core/commands/`
- [X] T009 Add clean unmodified-Spec-Kit Codex/slash composition coverage in `tests/concorde/acceptance/test_workspace_composition.py`
- [X] T010 Make self-hosting setup/check scripts consistently implement the same path contract in `.specify/scripts/bash/common.sh`, `.specify/scripts/bash/setup-plan.sh`, `.specify/scripts/bash/setup-tasks.sh`, and `.specify/scripts/bash/check-prerequisites.sh`

**Checkpoint**: One selected feature root yields durable and temporal paths through an installable public composition boundary.

---

## Phase 3: User Story 1 - Establish and Navigate the Architecture Hierarchy (Priority: P1) 🎯 MVP

**Goal**: Preserve review-first initialization and return an explicit one-level hierarchy at root and child levels.

**Independent Test**: Initialize a three-level fixture, request root then child context, and prove only the current module and immediate children appear at each step.

### Tests for User Story 1

- [X] T011 [P] [US1] Extend initialization tests for responsibility, boundary, explicit I/O, and unchanged proposal/apply semantics in `tests/concorde/integration/test_initialize.py`
- [X] T012 [P] [US1] Add three-level root-then-child context and ordered scenario-interaction assertions in `tests/concorde/integration/test_context.py`
- [X] T013 [P] [US1] Add module prose, explicit child identity, and current-level view rule fixtures in `tests/concorde/unit/test_rules.py`

### Implementation for User Story 1

- [X] T014 [US1] Extract reusable module, contract, and scenario projections into `extensions/concorde/runtime/concorde/projection.py`
- [X] T015 [US1] Refactor bounded hierarchy navigation and interaction output around the projection service in `extensions/concorde/runtime/concorde/context.py`
- [X] T016 [US1] Enforce module prose, child identities, and one-level view completeness in `extensions/concorde/runtime/concorde/validation/hierarchy.py`

**Checkpoint**: US1 works independently with initialization safety and stronger bounded navigation.

---

## Phase 4: User Story 2 - Place and Specify a Feature at the Right Level (Priority: P1)

**Goal**: Propose, approve, create, and select one nested canonical feature workspace without a second Spec Kit lifecycle.

**Independent Test**: Place cross-child behavior on the nearest common parent, approve the digest-bound proposal, select it, and run the normal lifecycle with one root `spec.md` and temporal plan/tasks.

### Tests for User Story 2

- [X] T017 [P] [US2] Add proposal, allocation, collision, digest, and nearest-common-parent unit tests in `tests/concorde/unit/test_feature_workspace.py`
- [X] T018 [P] [US2] Add create, select, rollback, idempotency, and resume integration tests in `tests/concorde/integration/test_feature_workspace.py`
- [X] T019 [P] [US2] Extend command contract tests from three to five portable command surfaces in `tests/concorde/contract/test_agent_commands.py`

### Implementation for User Story 2

- [X] T020 [US2] Implement reviewed placement, numbering, nearest-common-parent checks, apply, and selection in `extensions/concorde/runtime/concorde/feature_workspace.py`
- [X] T021 [US2] Add `feature create` and `feature select` CLI dispatch with normative envelopes in `extensions/concorde/runtime/concorde/cli.py`
- [X] T022 [P] [US2] Add portable create/select commands in `extensions/concorde/commands/speckit.concorde.feature.create.md` and `extensions/concorde/commands/speckit.concorde.feature.select.md`
- [X] T023 [US2] Register five commands and workspace scripts in `extensions/concorde/extension.yml`
- [X] T024 [US2] Add an end-to-end nested lifecycle acceptance test with no root compatibility files in `tests/concorde/acceptance/test_core_workflow.py`

**Checkpoint**: US2 creates/selects a nested feature and hands the same root to every normal Spec Kit phase.

---

## Phase 5: User Story 3 - Review Architecture Before Approving the Plan (Priority: P2)

**Goal**: Produce a deterministic readiness result naming missing ownership, refinement, boundary, view, dependency, and evidence decisions.

**Independent Test**: A cross-boundary fixture is incomplete without its contract and trace, then becomes ready after durable sources are supplied.

### Tests for User Story 3

- [X] T025 [P] [US3] Add readiness fail-then-pass fixtures for ownership, refinements, crossings, dependency direction, views, and evidence in `tests/concorde/integration/test_architecture_readiness.py`
- [X] T026 [P] [US3] Add standard/custom contract completeness and supported conformance tests in `tests/concorde/unit/test_contract_validation.py`

### Implementation for User Story 3

- [X] T027 [US3] Implement digest-bound architecture-readiness projection and findings in `extensions/concorde/runtime/concorde/readiness.py`
- [X] T028 [US3] Implement standard/custom representation checks and deterministic adapters in `extensions/concorde/runtime/concorde/validation/contracts.py`
- [X] T029 [US3] Implement scenario participant, interaction, and governing-contract rules in `extensions/concorde/runtime/concorde/validation/scenarios.py`
- [X] T030 [US3] Integrate readiness without replacing Spec Kit plan authority in `extensions/concorde/runtime/concorde/context.py` and `extensions/concorde/runtime/concorde/validate.py`

**Checkpoint**: US3 blocks architecture-ready claims until durable boundary information is reviewable.

---

## Phase 6: User Story 4 - Implement, Reconcile, and Validate with Bounded Context (Priority: P3)

**Goal**: Give implementation agents the smallest sufficient feature context and report source/evidence/projection disagreement deterministically.

**Independent Test**: An active-feature fixture exposes only relevant artifacts while broken refinement, missing evidence, disagreement, and stale projection findings repeat byte-for-byte.

### Tests for User Story 4

- [X] T031 [P] [US4] Add exact active-feature artifact, refinement, contract, and evidence inclusion/exclusion tests in `tests/concorde/integration/test_context.py`
- [X] T032 [P] [US4] Add layout, evidence-state, digest-disagreement, and delegated-freshness tests in `tests/concorde/integration/test_validation.py`
- [X] T033 [P] [US4] Add three-run cross-presentation determinism and source-immutability coverage in `tests/concorde/acceptance/test_core_workflow.py`

### Implementation for User Story 4

- [X] T034 [US4] Discover active implementation artifacts and safe auxiliary receipts without promoting them to durable entities in `extensions/concorde/runtime/concorde/repository.py`
- [X] T035 [US4] Add exact workspace, contract body, adjacent refinement, and evidence projections in `extensions/concorde/runtime/concorde/context.py`
- [X] T036 [P] [US4] Implement durable/temporal layout and selection rules in `extensions/concorde/runtime/concorde/validation/layout.py`
- [X] T037 [P] [US4] Implement evidence-reference and disagreement rules in `extensions/concorde/runtime/concorde/validation/evidence.py`
- [X] T038 [P] [US4] Implement Archify/docsite provenance freshness normalization in `extensions/concorde/runtime/concorde/validation/freshness.py`
- [X] T039 [US4] Refactor validation coordination into focused, stably ordered rule modules in `extensions/concorde/runtime/concorde/validate.py`

**Checkpoint**: US4 reconciliation is bounded, read-only, actionable, and repeatable.

---

## Phase 7: Polish, Self-Application, and Cross-Feature Compatibility

**Purpose**: Apply the refactored workflow to Concorde and record evidence without fabricating human outcomes.

- [X] T040 [P] Update stable scenario/contract traces for the five-command workflow in `specs/concorde/architecture.json`, `specs/concorde/module.md`, and `specs/concorde/modules/spec-kit-integration/module.md`
- [X] T041 [P] Synchronize command counts, catalogs, and Feature 003 compatibility references in `scripts/release/build-components.py`, `catalogs/extensions.json`, and `specs/concorde/features/003-install-concorde-speckit/`
- [X] T042 Regenerate release catalogs and architecture/documentation projections using their owning build commands in `catalogs/`, `generated/architecture/`, and `docsite/build/`
- [X] T043 Run Python tests, self-validation, Archify freshness, Docusaurus `npm run check`, and `git diff --check`, then record results and pending human protocols in `specs/concorde/features/001-concorde-starter-workflow/implementation/validation.md`
- [X] T044 Reconcile automated evidence while leaving SC-001, SC-007, and human approval partial in `specs/concorde/features/001-concorde-starter-workflow/spec.md` and `specs/concorde/modules/spec-kit-integration/features/002-manage-feature-workspace/spec.md`

---

## Dependencies & Execution Order

- Setup has no dependency; Foundational depends on Setup and blocks every story.
- US1 and US2 depend only on Foundational and remain independently testable.
- US3 uses workspace identity from US2; US4 integrates US1 navigation, US2 selection, and US3 rules.
- Polish depends on all automated story checkpoints.

## Parallel Opportunities

- T002/T003, T004/T005, T011–T013, T017–T019, T025/T026, T031–T033, T036–T038, and T040/T041 affect different files.

## Implementation Strategy

1. Characterize behavior with tests before each extraction.
2. Complete Setup and Foundational, then validate US1 as the preserved MVP.
3. Complete US2 for the first end-to-end nested lifecycle.
4. Add US3 readiness and US4 reconciliation incrementally.
5. Run self-application only after focused story checks pass.

## Notes

- Generated outputs are refreshed only by Archify, release, or Documentation owners.
- Human SC-001/SC-007 pilots and reviewer approval stay pending without real evidence.
- Existing dirty-worktree changes are preserved; implementation edits only named files.
