---

description: "Dependency-ordered implementation tasks for installing Concorde through Spec Kit"
---

# Tasks: Deliver Concorde through Spec Kit

**Input**: Durable behavior from `../spec.md`, accepted realization from `../design.md`, feature contracts and diagrams at the root, and the current temporal attempt in `implementation/`

**Tests**: Required because package presence and matching prompt text do not prove installed behavior, command precedence, temporal checklist routing, hardening, rollback, or user-source preservation.

**Organization**: Tasks implement the current plan's distribution delta from the accepted design. Feature 001 owns workspace and command semantics; Feature 003 packages four preset template layers, nine normal command replacements, six Concorde-specific commands, and their clean-project lifecycle without editing `../design.md`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it targets different files and has no dependency on an incomplete task
- **[Story]**: Maps the task to `US1` through `US4` from `../spec.md`
- Every task names exact maintained-source, package, test, generated-evidence, or validation paths

## Phase 1: Setup and Distribution Baseline

**Purpose**: Freeze the Feature 001 handoff, protect durable design, and verify the mandatory core diagram role before package changes begin.

- [X] T001 Verify that `specs/concorde/features/003-install-concorde-speckit/spec.md` declares exactly one `role: core` diagram and that `specs/concorde/features/003-install-concorde-speckit/diagrams/spec-kit-component-model.json` uses Archify `architecture`, while `diagrams/starter-installation-flow.json` remains `role: supplemental` workflow
- [X] T002 Record the accepted-design digest, Feature Workspace Protocol handoff, four-template/nine-replacement/six-command inventory, and current evidence baseline in `specs/concorde/features/003-install-concorde-speckit/implementation/validation.md`
- [X] T003 [P] Verify that Feature 003 review state exists only at `specs/concorde/features/003-install-concorde-speckit/implementation/checklists/requirements.md` with no root `checklists/` copy or symlink
- [X] T004 [P] Capture current manifest, release, catalog, bundle lifecycle, clean phase matrix, installed command, diagram, and docsite baseline results in `specs/concorde/features/003-install-concorde-speckit/implementation/validation.md`

**Checkpoint**: The accepted design is unchanged, temporal review state is confined, and the core/supplemental diagram roles are valid.

---

## Phase 2: Foundational Package and Command-Surface Contracts

**Purpose**: Bind distributable package content and normal-command replacement to the exact Feature 001 handoff before user-facing installation work.

**Critical gate**: If Spec Kit 0.16.4 cannot replace normal commands before path-sensitive work, stop with an actionable compatibility failure rather than patching managed core scripts.

- [X] T005 [P] Add exact four-template, nine-replacement, six-command, strategy, version, and compatibility assertions in `tests/concorde/contract/test_manifests.py`
- [X] T006 [P] Add archive allowlist, Feature 001 handoff digest, installed-relative dependency, no-self-hosting-input, and reproducibility assertions in `tests/concorde/contract/test_release_artifacts.py`
- [X] T007 [P] Add fifteen-surface winner, source package, provenance, bootstrap order, path matrix, and receipt assertions in `tests/concorde/contract/test_installed_command_surfaces.py`
- [X] T008 [P] Add package role, core/supplemental view, authority boundary, and clean-project explanation assertions in `tests/concorde/contract/test_ecosystem_explanation.py`
- [X] T009 Extend the shared installed command-surface inventory and executable receipt model in `tests/concorde/support/installed_command_surface.py`
- [X] T010 Declare four preset template layers and authoritative `replace` strategy for all nine normal commands in `presets/concorde-core/preset.yml`
- [X] T011 Maintain complete Spec Kit 0.16.4-compatible normal command sources with pre-path workspace resolution in `presets/concorde-core/commands/`
- [X] T012 Maintain the three inherited architecture guidance layers plus the permanent design template in `presets/concorde-core/templates/`
- [X] T013 Package all six Concorde commands, launchers, workspace adapter, schemas, and runtime files in `extensions/concorde/extension.yml`
- [X] T014 Bind build metadata, catalogs, ZIP allowlists, handoff digest, and fifteen-surface inventory in `scripts/release/build-components.py` and `scripts/release/verify-release.py`

**Checkpoint**: Maintained package sources define one reviewable, version-locked four-template/fifteen-surface inventory with no checkout-local dependency.

---

## Phase 3: User Story 1 - Inspect Concorde Before Installation (Priority: P1) 🎯 MVP

**Goal**: Build independently identifiable release units and show the exact trusted component plan, role boundaries, template strategies, command winners, and compatibility before mutation.

**Independent Test**: Build twice, inspect catalogs and archives, preview by catalog ID, and verify exact pins, trust, compatibility, integration inheritance, four template layers, fifteen command surfaces, source URLs, and byte reproducibility.

### Tests for User Story 1

- [X] T015 [P] [US1] Add package identity, cardinality, template/command strategy, compatibility, and role tests in `tests/concorde/contract/test_manifests.py`
- [X] T016 [P] [US1] Add two-build byte equality, catalog/archive parity, offline base-URL serialization, and member allowlist tests in `tests/concorde/contract/test_release_artifacts.py`
- [X] T017 [P] [US1] Add catalog, directory, manifest, archive, expanded-plan, and trusted-source parity tests in `tests/concorde/integration/test_bundle_lifecycle.py`

### Implementation for User Story 1

- [X] T018 [US1] Build deterministic preset, extension, bundle, and catalog outputs from explicit source allowlists in `scripts/release/build-components.py`
- [X] T019 [US1] Verify versions, URLs, compatibility, member lists, handoff digests, and archive digests without contacting `--base-url` in `scripts/release/verify-release.py`
- [X] T020 [US1] Reconcile bundle, preset, extension, template, normal-command, and Concorde-command inspection guidance in `bundles/concorde-starter/README.md`, `presets/concorde-core/README.md`, and `extensions/concorde/README.md`
- [X] T021 [US1] Reconcile package-role and trust semantics in `specs/concorde/features/003-install-concorde-speckit/contracts/bundle-distribution.md` and `specs/concorde/features/003-install-concorde-speckit/contracts/ecosystem-explanation.md`
- [X] T022 [US1] Align checked-in bundle, preset, and extension catalogs with generated release metadata in `catalogs/bundles.json`, `catalogs/presets.json`, and `catalogs/extensions.json`
- [X] T023 [US1] Run the two-build preview/inspection checkpoint and record exact package identities, strategies, URLs, and digests in `specs/concorde/features/003-install-concorde-speckit/implementation/validation.md`

**Checkpoint**: US1 yields a reproducible, inspectable, trusted installation plan without mutating a project.

---

## Phase 4: User Story 2 - Install Concorde into a New or Existing Project (Priority: P1)

**Goal**: Install the exact accepted bundle through Spec Kit's native lifecycle into supported initialized or uninitialized projects with correct provenance and no separate installer.

**Independent Test**: Install the same release from every supported source form into initialized and uninitialized projects, compare accepted plans and records, repeat three times, and seed every pre-mutation compatibility, trust, digest, missing-component, and collision failure.

### Tests for User Story 2

- [X] T024 [P] [US2] Add initialized/uninitialized and catalog/directory/manifest/archive install parity tests in `tests/concorde/integration/test_bundle_lifecycle.py`
- [X] T025 [P] [US2] Add unsupported-host, untrusted-source, missing-component, digest, command-collision, and partial-materialization refusal tests in `tests/concorde/integration/test_bundle_lifecycle.py`
- [X] T026 [P] [US2] Add three-install idempotency plus `.concorde/`, `specs/`, `docs/`, and unrelated-agent source hash tests in `tests/concorde/integration/test_bundle_lifecycle.py`

### Implementation for User Story 2

- [X] T027 [US2] Finalize bundle pins, compatibility, integration inheritance, and native lifecycle declarations in `bundles/concorde-starter/bundle.yml`
- [X] T028 [US2] Finalize preset and extension compatibility, content ownership, composition, and command materialization declarations in `presets/concorde-core/preset.yml` and `extensions/concorde/extension.yml`
- [X] T029 [US2] Harden local catalog serving and checkout-isolated target setup in `tests/concorde/support/catalog_server.py` and `tests/concorde/support/specify_project.py`
- [X] T030 [US2] Implement accepted-plan comparison, provenance, idempotency, source-preservation, and pre-mutation failure assertions in `tests/concorde/integration/test_bundle_lifecycle.py`
- [X] T031 [US2] Align install, compatibility, trust, ownership, idempotency, and failure semantics in `specs/concorde/features/003-install-concorde-speckit/contracts/bundle-distribution.md`
- [X] T032 [US2] Run the installation checkpoint for every source form and record target paths, package records, provenance, repeatability, and unchanged-source hashes in `specs/concorde/features/003-install-concorde-speckit/implementation/validation.md`

**Checkpoint**: US2 installs exactly the accepted bundle, preset, and extension through native Spec Kit lifecycle with no false success or user-source mutation.

---

## Phase 5: User Story 3 - Verify the Installed Workflow, Not Just Files (Priority: P1)

**Goal**: Execute the actual fifteen installed winners in checkout-isolated skills and slash-command projects and prove durable specification/design, temporal checklist/implementation, and hardening behavior.

**Independent Test**: Resolve every winner, execute its installed bootstrap and scenario, verify nine normal phase paths plus six Concorde command results, exercise hardening eligibility, and prove missing archive members fail without checkout fallback.

### Tests for User Story 3

- [X] T033 [P] [US3] Add fifteen-surface source/materialized provenance, winner hash, bootstrap order, and execution receipt tests in `tests/concorde/contract/test_installed_command_surfaces.py`
- [X] T034 [P] [US3] Add durable root spec/design, temporal checklist/plan/task, and zero-root-alias assertions for all nine normal phases in `tests/concorde/integration/test_clean_phase_matrix.py`
- [X] T035 [P] [US3] Add six-command installed runtime, hardening eligibility, and missing-member negative cases in `tests/concorde/acceptance/test_installed_codex_workflow.py`
- [X] T036 [P] [US3] Add equivalent slash-command presentation, path, hardening, and result-envelope cases in `tests/concorde/acceptance/test_installed_slash_workflow.py`
- [X] T037 [P] [US3] Add installed design-template materialization and no-checkout-fallback assertions in `tests/concorde/integration/test_preset_composition.py`

### Implementation for User Story 3

- [X] T038 [US3] Implement winning-layer discovery, package provenance, command presentation identity, and executable receipts in `tests/concorde/support/installed_command_surface.py`
- [X] T039 [US3] Ensure specification/clarification use durable intent while generated review checklists and all delivery phases resolve temporal paths in `presets/concorde-core/commands/`
- [X] T040 [US3] Ensure all normal planning and implementation commands read root `design.md` as immutable accepted baseline in `presets/concorde-core/commands/`
- [X] T041 [US3] Ensure all six extension commands and runtime dependencies resolve only from installed package content in `extensions/concorde/commands/`, `extensions/concorde/scripts/`, and `extensions/concorde/runtime/concorde/`
- [X] T042 [US3] Implement checkout-path sanitization and filesystem access auditing in `tests/concorde/support/specify_project.py`
- [X] T043 [US3] Execute the complete nested lifecycle and hardening eligibility through installed Codex skills in `tests/concorde/acceptance/test_installed_codex_workflow.py`
- [X] T044 [US3] Execute equivalent lifecycle and Concorde operations through one slash-command integration in `tests/concorde/acceptance/test_installed_slash_workflow.py`
- [X] T045 [US3] Bind every installed receipt to its package digest and Feature 001 handoff digest in `tests/concorde/contract/test_installed_command_surfaces.py`
- [X] T046 [US3] Reconcile the observable durable/temporal path matrix, command inventory, presentation parity, and missing-member failures in `specs/concorde/features/003-install-concorde-speckit/contracts/installed-command-surfaces.md`
- [X] T047 [US3] Run the clean Codex and slash-command checkpoints three times and record phase paths, checklist location, command results, hardening eligibility, receipts, and checkout isolation in `specs/concorde/features/003-install-concorde-speckit/implementation/validation.md`

**Checkpoint**: US3 proves actual installed behavior for all fifteen surfaces, including permanent design and temporal checklist/hardening semantics, without reading the Concorde checkout.

---

## Phase 6: User Story 4 - Update or Remove Concorde Safely (Priority: P3)

**Goal**: Preview/apply compatible updates and remove Concorde while respecting persistent registration, restoring lower winners, preserving shared components, and retaining project-authored sources byte-for-byte.

**Independent Test**: Stack a lower preset, then disable, reprioritize, update, fail an update, and remove Concorde; verify registered-winner semantics for all nine normal commands and unchanged user/shared state.

### Tests for User Story 4

- [X] T048 [P] [US4] Add nine-command enable, disable, priority, update, and removal host-lifecycle matrix tests in `tests/concorde/integration/test_command_recomposition.py`
- [X] T049 [P] [US4] Add compatible update, injected rollback, shared-component, local-modification, residual-state, and hardening-command ownership tests in `tests/concorde/integration/test_bundle_lifecycle.py`
- [X] T050 [P] [US4] Add before/after `.concorde/`, `specs/`, `docs/`, configuration, and unrelated-agent hash assertions in `tests/concorde/integration/test_bundle_lifecycle.py` and `tests/concorde/support/specify_project.py`

### Implementation for User Story 4

- [X] T051 [US4] Complete lower-layer restoration, winning hash comparison, and stale-artifact detection in `tests/concorde/support/installed_command_surface.py`
- [X] T052 [US4] Complete update/remove ownership, shared-component retention, rollback, and residual-state assertions in `tests/concorde/integration/test_bundle_lifecycle.py`
- [X] T053 [US4] Implement the complete nine-command recomposition fixture and Spec Kit 0.16.4 transitions in `tests/concorde/integration/test_command_recomposition.py`
- [X] T054 [US4] Reconcile update, disable, priority, removal, rollback, and source-preservation guidance in `bundles/concorde-starter/README.md` and `specs/concorde/features/003-install-concorde-speckit/contracts/bundle-distribution.md`
- [X] T055 [US4] Run the lifecycle checkpoint and record winner hashes, rollback state, retained shared components, residual diagnostics, and unchanged user-source hashes in `specs/concorde/features/003-install-concorde-speckit/implementation/validation.md`

**Checkpoint**: US4 follows host registration semantics, restores every expected lower winner, and preserves all project-authored and shared state under test.

---

## Phase 7: Diagrams, Documentation, Release Rebuild, and Final Evidence

**Purpose**: Complete both diagram lifecycles, rebuild release metadata, self-apply the distribution, and report automated versus human evidence truthfully.

- [X] T056 [P] Align package roles, stable component interactions, install/recomposition order, command inventory, scenarios, and governing contracts in `specs/concorde/features/003-install-concorde-speckit/spec.md`, `specs/concorde/features/003-install-concorde-speckit/contracts/ecosystem-explanation.md`, and `specs/concorde/features/003-install-concorde-speckit/contracts/installed-command-surfaces.md`
- [X] T057 [P] Maintain the single core package/component interaction source with complete scenario and contract traceability in `specs/concorde/features/003-install-concorde-speckit/diagrams/spec-kit-component-model.json`
- [X] T058 [P] Maintain the supplemental release/install/use/recomposition workflow source with complete scenario and contract traceability in `specs/concorde/features/003-install-concorde-speckit/diagrams/starter-installation-flow.json`
- [X] T059 Validate both Feature 003 sources with all Archify showcase checks and deliver fresh provenance-bearing outputs to `generated/architecture/concorde-spec-kit-component-model.html` and `generated/architecture/concorde-starter-installation-flow.html`
- [X] T060 Record truthful light/dark, containment, and browser perceptual-review status in `generated/architecture/concorde-spec-kit-component-model.visual-check.json`, `generated/architecture/concorde-starter-installation-flow.visual-check.json`, and `specs/concorde/features/003-install-concorde-speckit/implementation/validation.md`
- [X] T061 Verify declaration-driven canonical feature-page embedding, standalone links, provenance, route inventory, and freshness for both diagrams in `docsite/tests/integration/production-build.test.ts`
- [X] T062 Rebuild release archives and catalogs, verify four templates and fifteen surfaces from built artifacts, and record new digests in `specs/concorde/features/003-install-concorde-speckit/implementation/validation.md`
- [X] T063 Run the full Python suite, two-build release verification, clean-target matrices, Concorde self-validation, Archify checks, Docusaurus `npm run check`, and `git diff --check`, then record exact automated results in `specs/concorde/features/003-install-concorde-speckit/implementation/validation.md`
- [ ] T064 Conduct the SC-001 installation and SC-007 ecosystem-role pilots with first-time maintainers and record participants, timings, responses, and unmet thresholds in `specs/concorde/features/003-install-concorde-speckit/implementation/validation.md`
- [X] T065 Reconcile automated, browser, and human evidence without inferring pending outcomes in `specs/concorde/features/003-install-concorde-speckit/spec.md`, `specs/concorde/modules/distribution/features/001-package-starter-bundle/spec.md`, and `specs/concorde/modules/spec-kit-integration/features/001-compose-starter-workflow/spec.md`

**Checkpoint**: Built archives contain the exact reviewed workflow, both diagrams are fresh and embedded, deterministic gates pass, and human evidence remains honest.

---

## Dependencies and Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Starts immediately and freezes handoff and diagram roles.
- **Foundation (Phase 2)**: Depends on Setup and blocks all user stories.
- **US1 (Phase 3)**: Depends on Foundation and supplies reproducible artifacts/catalogs for installation.
- **US2 (Phase 4)**: Depends on US1's accepted release plan.
- **US3 (Phase 5)**: Depends on US2's installed target and Feature 001's exact handoff.
- **US4 (Phase 6)**: Depends on US3's verified command inventory.
- **Quality gates (Phase 7)**: Depend on every desired story checkpoint.

### User Story Dependency Graph

```text
Setup -> Foundation -> US1 inspect -> US2 install -> US3 execute -> US4 maintain -> Quality gates
```

### Parallel Opportunities

- T003-T004, T005-T008, T015-T017, T024-T026, T033-T037, T048-T050, and T056-T058 target independent files or fixtures.
- Release metadata tests and installed-surface harness work may proceed in parallel after the Feature 001 handoff is frozen.
- Codex, slash-command, phase-matrix, and design-template acceptance cases may be authored in parallel before the shared installed harness is finalized.

## Parallel Example: User Story 3

```text
Task T033: installed winner and receipt contracts in tests/concorde/contract/test_installed_command_surfaces.py
Task T034: durable/temporal phase matrix in tests/concorde/integration/test_clean_phase_matrix.py
Task T035: installed Codex and hardening cases in tests/concorde/acceptance/test_installed_codex_workflow.py
Task T036: slash-command parity cases in tests/concorde/acceptance/test_installed_slash_workflow.py
Task T037: design-template composition cases in tests/concorde/integration/test_preset_composition.py
```

## Implementation Strategy

### MVP First

1. Complete Setup and Foundation.
2. Complete US1 reproducible build and exact preview.
3. Stop and validate package identity, compatibility, trust, and composition before project mutation.

### Incremental Delivery

1. Add US2 native installation, provenance, idempotency, and refusal safety.
2. Add US3 executable checkout-isolated proof for all fifteen surfaces and the complete durable/temporal matrix.
3. Add US4 recomposition, compatible update, rollback, and safe removal.
4. Reconcile both diagrams, rebuild release units, and complete automated and human evidence gates.

## Notes

- `../design.md` is the immutable accepted baseline for this attempt.
- `dist/` archives/catalogs and generated diagram HTML are reproducible outputs, not maintained intent.
- `.agents/` and root `.specify/` are self-hosting inputs and may not satisfy product acceptance.
- Human setup/comprehension and browser perceptual outcomes remain pending until directly observed.
