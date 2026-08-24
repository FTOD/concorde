---

description: "Dependency-ordered implementation tasks for the Concorde core workflow"
---

# Tasks: Complete the Concorde Core Workflow

**Input**: Durable behavior from `../spec.md`, accepted realization from `../design.md`, durable contracts and diagrams at the feature root, and the current temporal attempt in `implementation/`

**Tests**: Required because this feature changes workspace authority, mutation safety, architecture validation, hardening, and installed command semantics.

**Organization**: Tasks implement the current plan's delta from the accepted design. They are grouped by the five user stories in priority order and leave `../design.md` unchanged except through the explicitly approved hardening operation exercised by User Story 5.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it targets different files and has no dependency on an incomplete task
- **[Story]**: Maps the task to `US1` through `US5` from `../spec.md`
- Every task names exact maintained-source, implementation, test, or evidence paths

## Phase 1: Setup and Baseline

**Purpose**: Establish the current-attempt boundary, protect durable design, and verify the mandatory core diagram role before implementation begins.

- [X] T001 Verify that `specs/concorde/features/001-concorde-starter-workflow/spec.md` declares exactly one `role: core` diagram and that `specs/concorde/features/001-concorde-starter-workflow/diagrams/core-workflow-components.json` uses Archify `architecture` as the stable component-interaction view rather than a sequence or workflow view
- [X] T002 Record the current Feature 001 requirement, accepted-design digest, and evidence baseline in `specs/concorde/features/001-concorde-starter-workflow/implementation/validation.md`
- [X] T003 [P] Verify that the active checklist exists only at `specs/concorde/features/001-concorde-starter-workflow/implementation/checklists/requirements.md` and remove any root checklist compatibility path from `specs/concorde/features/001-concorde-starter-workflow/checklists/`
- [X] T004 [P] Capture the focused Python, Archify, docsite, source-immutability, and generated-output baseline in `specs/concorde/features/001-concorde-starter-workflow/implementation/validation.md`

**Checkpoint**: The accepted design digest is recorded, temporal review state is confined to `implementation/`, and the core diagram has the required role and type.

---

## Phase 2: Foundational Workflow Contracts and Services

**Purpose**: Freeze the distribution-neutral workspace, command, and hardening handoff used by every story and by Feature 003.

**Critical gate**: Feature 001 may prove source and self-hosting semantics, but Feature 003 alone may claim release-installed materialization.

- [X] T005 [P] Extend durable-root, temporal-attempt, checklist, selection, and no-alias contract coverage in `tests/concorde/contract/test_feature_workspace_contract.py`
- [X] T006 [P] Add nine-phase, six-command, hardening-proposal, result-envelope, and distribution-handoff assertions in `tests/concorde/contract/test_agent_commands.py`
- [X] T007 [P] Add selected-root, phase-path, lifecycle-state, proposal-digest, checklist-path, and confinement unit coverage in `tests/concorde/unit/test_feature_workspace.py`
- [X] T008 [P] Add stable success/failure envelope assertions for create, select, harden, context, init, and validate in `tests/concorde/contract/test_structured_results.py`
- [X] T009 Implement the immutable durable/temporal workspace path model and lifecycle state in `extensions/concorde/runtime/concorde/feature_workspace.py`
- [X] T010 Implement installed-relative, read-only phase-path resolution with checklist routing in `extensions/concorde/scripts/python/workspace.py`
- [X] T011 Align self-hosting path resolution with root `spec.md` and `design.md` plus temporal `implementation/` paths in `.specify/scripts/bash/common.sh`, `.specify/scripts/bash/setup-plan.sh`, `.specify/scripts/bash/setup-tasks.sh`, and `.specify/scripts/bash/check-prerequisites.sh`
- [X] T012 Align all six canonical command contracts with portable extension commands in `specs/concorde/features/001-concorde-starter-workflow/contracts/agent-commands.md` and `extensions/concorde/commands/`
- [X] T013 Finalize the versioned workspace and hardening representations in `specs/concorde/features/001-concorde-starter-workflow/contracts/feature-workspace.schema.json` and `specs/concorde/features/001-concorde-starter-workflow/contracts/examples/`
- [X] T014 Reconcile workspace ownership and path semantics in `specs/concorde/modules/spec-kit-integration/contracts/feature-workspace/contract.md` and `specs/concorde/modules/spec-kit-integration/features/002-manage-feature-workspace/spec.md`

**Checkpoint**: One selected feature resolves one safe, versioned durable/temporal path set and one distribution-neutral six-command contract.

---

## Phase 3: User Story 1 - Establish and Navigate the Architecture Hierarchy (Priority: P1) 🎯 MVP

**Goal**: Propose a root hierarchy safely and navigate exactly one architectural level at a time.

**Independent Test**: Initialize a three-level fixture, request root then child context, and verify that each response contains only the current module, immediate children, current-level features, their I/O contracts, permitted externals, and stable deeper navigation references.

### Tests for User Story 1

- [X] T015 [P] [US1] Add review-first initialization, explicit approval, rollback, and source-preservation cases in `tests/concorde/integration/test_initialize.py`
- [X] T016 [P] [US1] Add root-to-child three-level bounded-context and navigation assertions in `tests/concorde/integration/test_context.py`
- [X] T017 [P] [US1] Add responsibility, boundary, current-module, child-I/O, permitted-external, and one-level visibility cases in `tests/concorde/unit/test_rules.py`

### Implementation for User Story 1

- [X] T018 [US1] Complete module, contract, feature, scenario, and navigation projections in `extensions/concorde/runtime/concorde/projection.py`
- [X] T019 [US1] Refine root and child bounded context around stable module and feature identities in `extensions/concorde/runtime/concorde/context.py`
- [X] T020 [US1] Enforce module prose, explicit boundary sets, hierarchy acyclicity, and one-level view completeness in `extensions/concorde/runtime/concorde/validation/hierarchy.py`

**Checkpoint**: US1 passes independently without exposing grandchildren or mutating architecture before approval.

---

## Phase 4: User Story 2 - Place and Specify a Feature at the Right Level (Priority: P1)

**Goal**: Review, create, and select one nested feature workspace under the correct provider while retaining one canonical specification and durable design.

**Independent Test**: Place single-module and cross-child behaviors, approve their exact proposals, select each workspace, and prove nearest-common-parent ownership, atomic state, durable root files, temporal attempt paths, and zero aliases.

### Tests for User Story 2

- [X] T021 [P] [US2] Add numbering, safe-path, collision, provider, nearest-common-parent, and proposal-digest cases in `tests/concorde/unit/test_feature_workspace.py`
- [X] T022 [P] [US2] Add read-only proposal, atomic create/select, resume, conflict, stale-proposal, and idempotent reselection cases in `tests/concorde/integration/test_feature_workspace.py`
- [X] T023 [P] [US2] Add durable `spec.md` and `design.md`, temporal checklist/plan/task, and zero-root-alias matrix coverage in `tests/concorde/integration/test_implementation_workspace.py`
- [X] T024 [P] [US2] Prove normal lifecycle path composition against a nested feature in `tests/concorde/acceptance/test_preset_workflow.py`

### Implementation for User Story 2

- [X] T025 [US2] Complete reviewed placement, numbering, digest binding, safe path resolution, workspace creation, and atomic selection in `extensions/concorde/runtime/concorde/feature_workspace.py`
- [X] T026 [US2] Complete `feature create` and `feature select` dispatch, diagnostics, and exit semantics in `extensions/concorde/runtime/concorde/cli.py`
- [X] T027 [P] [US2] Complete portable create and select orchestration in `extensions/concorde/commands/speckit.concorde.feature.create.md` and `extensions/concorde/commands/speckit.concorde.feature.select.md`
- [X] T028 [US2] Ensure created feature workspaces receive durable `spec.md` and `design.md` plus one temporal `implementation/` attempt through `extensions/concorde/runtime/concorde/feature_workspace.py`
- [X] T029 [US2] Register create/select command and runtime dependencies without distribution-specific presentation assumptions in `extensions/concorde/extension.yml`

**Checkpoint**: US2 creates and selects nested features without a second registry, specification, design authority, or lifecycle.

---

## Phase 5: User Story 3 - Review Architecture Before Approving the Plan (Priority: P2)

**Goal**: Produce a deterministic readiness result for ownership, refinements, child participation, contracts, dependency direction, scenario traces, views, diagrams, and expected evidence.

**Independent Test**: A cross-boundary fixture remains not ready until its provider, adjacent refinements, governing contracts, ordered interactions, affected view, feature-diagram decision, and evidence expectation exist; it then passes without changing Spec Kit plan authority.

### Tests for User Story 3

- [X] T030 [P] [US3] Add architecture-readiness fail-then-pass integration fixtures in `tests/concorde/integration/test_architecture_readiness.py`
- [X] T031 [P] [US3] Add standard/custom representation, schema/example conformance, and unsupported-format findings in `tests/concorde/unit/test_contract_validation.py`
- [X] T032 [P] [US3] Add core-diagram sufficiency, single-core cardinality, Archify type, scenario, and contract-trace cases in `tests/concorde/integration/test_validation.py`

### Implementation for User Story 3

- [X] T033 [US3] Complete digest-bound architecture-readiness projection and actionable findings in `extensions/concorde/runtime/concorde/readiness.py`
- [X] T034 [P] [US3] Complete deterministic JSON, TOML, constrained-YAML, schema, grammar, and unsupported-format handling in `extensions/concorde/runtime/concorde/validation/contracts.py`
- [X] T035 [P] [US3] Complete ordered scenario participant, boundary-crossing, and governing-contract validation in `extensions/concorde/runtime/concorde/validation/scenarios.py`
- [X] T036 [US3] Integrate readiness and feature-diagram review with bounded context and validation in `extensions/concorde/runtime/concorde/context.py` and `extensions/concorde/runtime/concorde/validate.py`

**Checkpoint**: US3 returns deterministic gaps and blocks only architecture-ready claims, not the normal planning phase itself.

---

## Phase 6: User Story 5 - Harden a Completed Milestone into Durable Design (Priority: P2)

**Goal**: Propose and explicitly approve compaction of a task-complete attempt into permanent design while removing only the selected feature's temporal workspace.

**Independent Test**: An incomplete fixture remains byte-identical; a complete fixture yields a digest-bound proposal; approved apply updates `design.md` and removes only `implementation/`; stale, unsafe, or failed commits restore the previous state.

### Tests for User Story 5

- [X] T037 [P] [US5] Add incomplete, malformed, empty-task, unresolved-checklist, and no-attempt eligibility refusals in `tests/concorde/integration/test_feature_hardening.py`
- [X] T038 [P] [US5] Add proposal digest, candidate completeness, exact removal set, symlink, traversal, and stale-input refusal cases in `tests/concorde/integration/test_feature_hardening.py`
- [X] T039 [P] [US5] Add approved atomic apply, whole-attempt removal, injected-failure rollback, and retained-source hash cases in `tests/concorde/integration/test_feature_hardening.py`
- [X] T040 [P] [US5] Add portable hardening command/result contract assertions in `tests/concorde/contract/test_agent_commands.py` and `tests/concorde/contract/test_structured_results.py`

### Implementation for User Story 5

- [X] T041 [US5] Implement canonical task parsing, checklist resolution, candidate validation, source digesting, and confinement checks in `extensions/concorde/runtime/concorde/feature_hardening.py`
- [X] T042 [US5] Implement read-only proposal and explicitly approved staged apply with recoverable rollback in `extensions/concorde/runtime/concorde/feature_hardening.py`
- [X] T043 [US5] Add `feature harden` CLI dispatch, deterministic diagnostics, and result envelope handling in `extensions/concorde/runtime/concorde/cli.py`
- [X] T044 [P] [US5] Implement agent-assisted candidate assembly and explicit approval instructions in `extensions/concorde/commands/speckit.concorde.feature.harden.md`
- [X] T045 [US5] Register the hardening command, launcher dependencies, and runtime files in `extensions/concorde/extension.yml`
- [X] T046 [US5] Align self-hosting hardening guidance and the permanent design template in `.agents/skills/speckit-concorde-feature-harden/SKILL.md` and `.specify/templates/design-template.md`

**Checkpoint**: US5 changes durable design only through approved hardening and removes no path outside the selected `implementation/` directory.

---

## Phase 7: User Story 4 - Implement, Reconcile, and Validate with Bounded Context (Priority: P3)

**Goal**: Return the smallest sufficient active-feature context and deterministically reconcile durable intent/design, temporal work, implementation/test evidence, and generated projections.

**Independent Test**: The active feature exposes only relevant durable and temporal artifacts plus adjacent architecture; invalid layout, missing/disagreeing evidence, contract mismatch, and stale projections return stable findings over three unchanged runs.

### Tests for User Story 4

- [X] T047 [P] [US4] Add exact active-feature spec, design, implementation, checklist, contract, diagram, refinement, and exclusion assertions in `tests/concorde/integration/test_context.py`
- [X] T048 [P] [US4] Add layout, selected-attempt, evidence, custom conformance, and delegated-freshness fixtures in `tests/concorde/integration/test_validation.py`
- [X] T049 [P] [US4] Add three-run determinism, cross-presentation semantics, and source-immutability acceptance cases in `tests/concorde/acceptance/test_core_workflow.py`

### Implementation for User Story 4

- [X] T050 [US4] Discover durable designs and diagrams, temporal attempts, checklists, and safe evidence receipts in `extensions/concorde/runtime/concorde/repository.py`
- [X] T051 [US4] Project exact active-feature artifacts, contract bodies, adjacent refinements, diagram metadata, and evidence in `extensions/concorde/runtime/concorde/context.py`
- [X] T052 [P] [US4] Enforce durable-root, temporal-attempt, selected-state, checklist, and no-alias layout rules in `extensions/concorde/runtime/concorde/validation/layout.py`
- [X] T053 [P] [US4] Complete missing, verified, unknown, stale, and disagreeing evidence-reference rules in `extensions/concorde/runtime/concorde/validation/evidence.py`
- [X] T054 [P] [US4] Complete delegated Archify and docsite provenance/freshness normalization in `extensions/concorde/runtime/concorde/validation/freshness.py`
- [X] T055 [US4] Coordinate focused validators in stable rule and finding order in `extensions/concorde/runtime/concorde/validate.py`
- [X] T056 [US4] Reconcile bounded-context and validation command behavior with `specs/concorde/features/001-concorde-starter-workflow/contracts/architecture-sources.md` and `specs/concorde/features/001-concorde-starter-workflow/contracts/agent-commands.md`

**Checkpoint**: US4 is bounded, read-only, repeatable, and explicit about unknown or disagreeing evidence.

---

## Phase 8: Diagrams, Self-Application, Distribution Handoff, and Quality Gates

**Purpose**: Complete the core diagram lifecycle, prove self-application, and publish an exact handoff without claiming Feature 003's release evidence.

- [X] T057 [P] Align the core component responsibilities, normal phase path, Concorde operation path, hardening path, scenario IDs, and governing contracts in `specs/concorde/features/001-concorde-starter-workflow/spec.md` and `specs/concorde/features/001-concorde-starter-workflow/contracts/architecture-sources.md`
- [X] T058 [P] Maintain the stable component-interaction source and scenario/contract traceability in `specs/concorde/features/001-concorde-starter-workflow/diagrams/core-workflow-components.json` without encoding generated HTML as intent
- [X] T059 Validate the Feature 001 core diagram with all Archify showcase checks and deliver fresh provenance-bearing output to `generated/architecture/concorde-core-workflow-components.html`
- [X] T060 Record truthful light/dark, containment, and browser perceptual-review status in `generated/architecture/concorde-core-workflow-components.visual-check.json` and `specs/concorde/features/001-concorde-starter-workflow/implementation/validation.md`
- [X] T061 Verify declaration-driven canonical feature-page embedding, standalone delivery links, provenance, and freshness in `docsite/tests/integration/production-build.test.ts`
- [X] T062 [P] Align diagram-role, durable-design, temporal-checklist, and hardening guidance in `presets/concorde-core/templates/`, `.specify/templates/`, and `.agents/skills/`
- [X] T063 Publish the exact Feature Workspace Protocol digest, nine-phase matrix, six-command inventory, and runtime allowlist handoff in `specs/concorde/features/003-install-concorde-speckit/contracts/installed-command-surfaces.md`
- [X] T064 Run the complete Python suite, Concorde self-validation, schema/example checks, Archify validation, Docusaurus `npm run check`, and `git diff --check`, then record exact automated evidence in `specs/concorde/features/001-concorde-starter-workflow/implementation/validation.md`
- [X] T065 Reconcile automated versus human evidence without inferring SC-001, SC-007, SC-008, or SC-011 outcomes in `specs/concorde/features/001-concorde-starter-workflow/spec.md` and `specs/concorde/features/001-concorde-starter-workflow/implementation/validation.md`

**Checkpoint**: Every deterministic gate passes, the core diagram is fresh and automatically published, and pending human evidence remains explicitly pending.

---

## Dependencies and Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Starts immediately and freezes the accepted-design and diagram baseline.
- **Foundation (Phase 2)**: Depends on Setup and blocks every user story.
- **US1 and US2 (Phases 3-4)**: Depend only on Foundation and may proceed in parallel.
- **US3 (Phase 5)**: Depends on Foundation and the stable provider/workspace identities from US2.
- **US5 (Phase 6)**: Depends on the workspace protocol from Foundation and complete attempt semantics from US2; it does not depend on US4 validation internals.
- **US4 (Phase 7)**: Integrates US1 navigation, US2 selection, US3 readiness, and US5 durable/temporal lifecycle state.
- **Quality gates (Phase 8)**: Depend on every desired story checkpoint; T063 is the explicit Feature 003 handoff.

### User Story Dependency Graph

```text
Setup -> Foundation -> US1 --------------------|
                    -> US2 -> US3 ------------|-> US4 -> Quality gates
                           -> US5 -------------|
```

### Parallel Opportunities

- T003-T004, T005-T008, T015-T017, T021-T024, T030-T032, T037-T040, T047-T049, and T057-T058 target independent files or fixtures.
- After Foundation, US1 hierarchy work and US2 workspace work may proceed in parallel.
- Within US5, eligibility, digest/confinement, rollback, and command-contract tests may be authored in parallel before runtime implementation.

## Parallel Example: User Story 5

```text
Task T037: hardening eligibility cases in tests/concorde/integration/test_feature_hardening.py
Task T038: proposal digest and confinement cases in tests/concorde/integration/test_feature_hardening.py
Task T039: approved apply and rollback cases in tests/concorde/integration/test_feature_hardening.py
Task T040: command/result contract cases in tests/concorde/contract/
```

## Implementation Strategy

### MVP First

1. Complete Setup and Foundation.
2. Complete US1 and prove root-to-child bounded navigation.
3. Stop and validate the hierarchy before adding placement, readiness, or hardening behavior.

### Incremental Delivery

1. Add US2 nested placement, selection, and durable/temporal routing.
2. Add US3 readiness and contract conformance without replacing plan authority.
3. Add US5 explicit hardening with rollback and unchanged-source evidence.
4. Add US4 bounded reconciliation across durable and temporal sources.
5. Validate and publish the core diagram, self-apply the workflow, and hand exact semantics to Feature 003.

## Notes

- `../design.md` is the immutable accepted baseline for this attempt; normal plan/tasks/implement work must not edit it directly.
- Generated HTML is refreshed through Archify and never edited as maintained intent.
- Feature 003 alone proves release-installed command winners and checkout isolation.
- Human pilot, approval, and browser outcomes remain pending until real evidence exists.
