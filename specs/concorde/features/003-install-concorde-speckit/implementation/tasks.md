---

description: "Dependency-ordered implementation tasks for installing Concorde through Spec Kit"
---

# Tasks: Deliver Concorde through Spec Kit

**Input**: Durable Feature 003 specification/contracts and temporal design under `implementation/`

**Tests**: Required because package presence and matching prompt text do not prove installed behavior,
composition precedence, rollback, or user-source preservation.

**Organization**: Tasks follow the four installation user stories. Feature 001 is authoritative for
workspace and command semantics; these tasks package, materialize, execute, and maintain that handoff.

## Phase 1: Setup and Distribution Baseline

**Purpose**: Record the current append-only defect and protect existing release behavior.

- [X] T001 Record the revised Feature 003 requirement/evidence matrix and current append-only gap in `specs/concorde/features/003-install-concorde-speckit/implementation/validation.md`
- [X] T002 [P] Verify release, Python, Node, generated-output, and environment ignore coverage in `.gitignore` and `docsite/.gitignore`
- [X] T003 [P] Capture current manifest, release, bundle lifecycle, and command-registration baselines in `specs/concorde/features/003-install-concorde-speckit/implementation/validation.md`

---

## Phase 2: Foundational Package and Command-Surface Contracts

**Purpose**: Bind package content and normal-command replacement to the exact Feature 001 handoff.

**Critical gate**: If Spec Kit 0.16.4 public command replacement cannot route before legacy path
selection, stop and require an upstream-supported host version; do not patch managed core scripts.

- [X] T004 [P] Add exact three-template/nine-replacement/five-command manifest assertions in `tests/concorde/contract/test_manifests.py`
- [X] T005 [P] Add archive allowlist, handoff-digest, installed-relative dependency, and reproducibility assertions in `tests/concorde/contract/test_release_artifacts.py`
- [X] T006 [P] Add installed winner, provenance, bootstrap-order, and receipt contract tests in `tests/concorde/contract/test_installed_command_surfaces.py`
- [X] T007 Create the shared installed command-surface fixture and receipt model in `tests/concorde/support/installed_command_surface.py`
- [X] T008 Convert all nine preset command entries to authoritative `replace` strategy in `presets/concorde-core/preset.yml`
- [X] T009 Replace the nine late routing addenda with complete Spec Kit 0.16.4-compatible command sources in `presets/concorde-core/commands/`
- [X] T010 Preserve the three architecture template entries as append-only guidance in `presets/concorde-core/templates/`
- [X] T011 Package all five command definitions, launchers, workspace adapter, schemas, and runtime files in `extensions/concorde/extension.yml`
- [X] T012 Bind release metadata and catalogs to the Feature 001 handoff and fourteen-surface inventory in `scripts/release/build-components.py` and `scripts/release/verify-release.py`

**Checkpoint**: Maintained package sources contain one reviewable, version-locked command inventory.

---

## Phase 3: User Story 1 - Inspect Concorde Before Installation (Priority: P1) 🎯 MVP

**Goal**: Build independently identifiable release units and show the exact trusted component plan
and role boundaries before any project mutation.

**Independent Test**: Build twice, inspect all catalogs/archives, preview by catalog ID, and verify
exact pins, compatibility, trust, integration inheritance, template/command strategies, and byte
reproducibility.

### Tests for User Story 1

- [X] T013 [P] [US1] Extend package identity, cardinality, strategy, and role contract tests in `tests/concorde/contract/test_manifests.py`
- [X] T014 [P] [US1] Add two-build byte equality and catalog/archive parity tests in `tests/concorde/contract/test_release_artifacts.py`
- [X] T015 [P] [US1] Add catalog, directory, manifest, archive, and expanded-plan parity tests in `tests/concorde/integration/test_bundle_lifecycle.py`

### Implementation for User Story 1

- [X] T016 [US1] Build deterministic preset, extension, bundle, and catalog outputs from explicit allowlists in `scripts/release/build-components.py`
- [X] T017 [US1] Verify versions, URLs, compatibility, member lists, and digests without contacting `--base-url` in `scripts/release/verify-release.py`
- [X] T018 [US1] Align bundle, preset, and extension role/inspection guidance in `bundles/concorde-starter/README.md`, `presets/concorde-core/README.md`, and `extensions/concorde/README.md`
- [X] T019 [US1] Align checked-in bundle, preset, and extension catalogs with generated release metadata in `catalogs/bundles.json`, `catalogs/presets.json`, and `catalogs/extensions.json`

**Checkpoint**: US1 provides a reproducible, inspectable plan with no project mutation.

---

## Phase 4: User Story 2 - Install Concorde into a New or Existing Project (Priority: P1)

**Goal**: Install the exact accepted bundle through native Spec Kit lifecycle into supported clean or
existing projects with correct provenance and no separate installer.

**Independent Test**: Install the same built release by all approved source forms into initialized
and uninitialized projects, compare the accepted plan and records, repeat three times, and seed all
pre-mutation compatibility/trust failures.

### Tests for User Story 2

- [X] T020 [P] [US2] Add initialized/uninitialized and four-source-form install parity tests in `tests/concorde/integration/test_bundle_lifecycle.py`
- [X] T021 [P] [US2] Add unsupported-host, trust, missing-component, digest, and collision refusal tests in `tests/concorde/integration/test_bundle_lifecycle.py`
- [X] T022 [P] [US2] Add three-install idempotency and project-source hash tests in `tests/concorde/integration/test_bundle_lifecycle.py`

### Implementation for User Story 2

- [X] T023 [US2] Complete bundle pins, compatibility, integration inheritance, and native lifecycle declarations in `bundles/concorde-starter/bundle.yml`
- [X] T024 [US2] Complete preset and extension manifest compatibility, content, and ownership declarations in `presets/concorde-core/preset.yml` and `extensions/concorde/extension.yml`
- [X] T025 [US2] Harden local catalog serving and checkout-isolated target setup in `tests/concorde/support/catalog_server.py` and `tests/concorde/support/specify_project.py`
- [X] T026 [US2] Implement plan/install comparison, provenance, idempotency, and pre-mutation failure assertions in `tests/concorde/integration/test_bundle_lifecycle.py`

**Checkpoint**: US2 installs exactly the accepted components through Spec Kit-native lifecycle.

---

## Phase 5: User Story 3 - Verify the Installed Workflow, Not Just Files (Priority: P1)

**Goal**: Execute the actual fourteen installed winners in checkout-isolated skills and slash-command
projects and prove the Feature 001 durable/temporal behavior.

**Independent Test**: Resolve every registered winner, execute its installed bootstrap and scenario,
verify nine normal phase paths plus five Concorde command results, then remove required archive
members and prove clean acceptance fails without checkout fallback.

### Tests for User Story 3

- [X] T027 [P] [US3] Add fourteen-surface source/materialized provenance and bootstrap execution tests in `tests/concorde/contract/test_installed_command_surfaces.py`
- [X] T028 [P] [US3] Add durable/temporal normal-phase matrix and zero-root-alias tests in `tests/concorde/integration/test_clean_phase_matrix.py`
- [X] T029 [P] [US3] Add five-command installed-runtime and missing-member negative tests in `tests/concorde/acceptance/test_installed_codex_workflow.py`
- [X] T030 [P] [US3] Add equivalent slash-command presentation and result tests in `tests/concorde/acceptance/test_installed_slash_workflow.py`

### Implementation for User Story 3

- [X] T031 [US3] Implement winning-layer discovery, presentation provenance, and executable receipts in `tests/concorde/support/installed_command_surface.py`
- [X] T032 [US3] Ensure every normal replacement resolves the Feature 001 workspace before path-sensitive work in `presets/concorde-core/commands/`
- [X] T033 [US3] Ensure all extension command/runtime paths resolve from installed package content in `extensions/concorde/commands/` and `extensions/concorde/scripts/`
- [X] T034 [US3] Implement checkout path sanitization and file-access auditing in `tests/concorde/support/specify_project.py`
- [X] T035 [US3] Execute the complete nested lifecycle through installed Codex skills in `tests/concorde/acceptance/test_installed_codex_workflow.py`
- [X] T036 [US3] Execute equivalent lifecycle and Concorde operations through one slash integration in `tests/concorde/acceptance/test_installed_slash_workflow.py`
- [X] T037 [US3] Bind every installed receipt to package and Feature 001 handoff digests in `tests/concorde/contract/test_installed_command_surfaces.py`

**Checkpoint**: US3 proves installed behavior, not repository-local text or runtime invocation alone.

---

## Phase 6: User Story 4 - Update or Remove Concorde Safely (Priority: P3)

**Goal**: Preview/apply compatible updates and remove Concorde while respecting Spec Kit's persistent
registration behavior, restoring lower winners on removal, preserving shared components, and leaving
project-authored sources byte-identical.

**Independent Test**: Stack a lower preset, then disable, reprioritize, update, fail an update, and
remove Concorde; disable/priority preserve registered winners, update/removal materialize the expected
layer for all nine commands, and user/shared state remains intact.

### Tests for User Story 4

- [X] T038 [P] [US4] Add nine-command enable/disable/priority/remove host-lifecycle matrix tests in `tests/concorde/integration/test_command_recomposition.py`
- [X] T039 [P] [US4] Add compatible update, rollback, shared-component, local-modification, and residual-state tests in `tests/concorde/integration/test_bundle_lifecycle.py`
- [X] T040 [P] [US4] Add before/after `.concorde/`, `specs/`, `docs/`, and unrelated-agent hash assertions in `tests/concorde/integration/test_bundle_lifecycle.py` and `tests/concorde/support/specify_project.py`

### Implementation for User Story 4

- [X] T041 [US4] Complete lower-layer restoration and stale-artifact detection in `tests/concorde/support/installed_command_surface.py`
- [X] T042 [US4] Complete update/remove ownership and rollback assertions in `tests/concorde/integration/test_bundle_lifecycle.py`
- [X] T043 [US4] Implement the full command recomposition fixture and transitions in `tests/concorde/integration/test_command_recomposition.py`
- [X] T044 [US4] Align update, removal, rollback, and shared-component guidance in `bundles/concorde-starter/README.md` and `specs/concorde/features/003-install-concorde-speckit/contracts/bundle-distribution.md`

**Checkpoint**: US4 follows the host registration lifecycle, restores every lower winner on removal,
and preserves every user/shared source under test.

---

## Phase 7: Diagrams, Documentation, Self-Application, and Evidence

**Purpose**: Keep the installed component model understandable and record only evidence actually run.

- [X] T045 [P] Align textual ownership and invocation explanations in `specs/concorde/features/003-install-concorde-speckit/spec.md`, `specs/concorde/features/003-install-concorde-speckit/contracts/ecosystem-explanation.md`, and `specs/concorde/features/003-install-concorde-speckit/contracts/installed-command-surfaces.md`
- [X] T046 [P] Align static package/command composition with the textual contracts in `specs/concorde/features/003-install-concorde-speckit/diagrams/spec-kit-component-model.json`
- [X] T047 [P] Align release/install/use/recomposition order with the textual contracts in `specs/concorde/features/003-install-concorde-speckit/diagrams/starter-installation-flow.json`
- [X] T048 Validate both Feature 003 diagrams with all Archify showcase checks and deliver fresh provenance-bearing outputs to `generated/architecture/concorde-spec-kit-component-model.html` and `generated/architecture/concorde-starter-installation-flow.html`
- [X] T049 Verify automatic feature-page embedding, route inventory, and freshness for both diagrams in `docsite/tests/integration/production-build.test.ts`
- [X] T050 Run the full Python suite, two-build release verification, clean-target matrices, Concorde self-validation, Archify checks, Docusaurus `npm run check`, and `git diff --check`, then record exact results in `specs/concorde/features/003-install-concorde-speckit/implementation/validation.md`
- [X] T051 Reconcile automated evidence while leaving SC-001 and SC-007 human pilots partial in `specs/concorde/features/003-install-concorde-speckit/spec.md`, `specs/concorde/modules/distribution/features/001-package-starter-bundle/spec.md`, and `specs/concorde/modules/spec-kit-integration/features/001-compose-starter-workflow/spec.md`

---

## Dependencies & Execution Order

- Setup has no dependency; Foundational depends on Setup and blocks all stories.
- US1 inspection depends on Foundation and supplies artifacts/catalogs for US2.
- US2 installation depends on US1's accepted release plan.
- US3 verification depends on US2's installed target and Feature 001's handoff.
- US4 lifecycle safety depends on a verified US3 command inventory.
- Diagram/evidence work depends on the completed automated story checkpoints.

## Parallel Opportunities

- T002/T003, T004–T006, T013–T015, T020–T022, T027–T030, T038–T040, and T045–T047
  operate on independent tests or sources.
- Release metadata tests and installed-surface harness development can proceed in parallel after the
  Feature 001 handoff is frozen.

## Parallel Example: User Story 3

```text
Task T027: installed winner/receipt contracts
Task T028: normal phase path matrix
Task T029: Codex installed runtime and negative archive fixtures
Task T030: slash-command parity fixture
```

## Implementation Strategy

### MVP First

1. Complete Setup and Foundational.
2. Complete US1 reproducible build and exact preview.
3. Stop and validate package identity before project mutation.

### Incremental Delivery

1. Add US2 native installation and provenance.
2. Add US3 executable checkout-isolated command proof.
3. Add US4 recomposition, update, and safe removal.
4. Reconcile diagrams/docs and record automated versus human evidence honestly.

## Notes

- `dist/` archives/catalogs and generated HTML are reproducible outputs, not maintained intent.
- `.agents/` and root `.specify/` are self-hosting inputs and may not satisfy product acceptance.
- Human setup/comprehension outcomes remain pending until real participants complete the protocols.
